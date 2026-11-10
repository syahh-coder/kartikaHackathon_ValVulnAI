"""Manual business record review. Never plans or dispatches target actions."""
import asyncio
import json
import time
from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response
from pydantic import Field

from app.auth import Principal, owned, principal
from app.agent.business_evidence_workflow import Binding, UntrustedClaim, WorkflowPacket, build as build_workflow
from app.common import AppError, audit, digest, packed, rate_limit, uid
from app.schemas import Claim, DTO, ScopeDraft
from app.storage.db import all_rows, one
from app.storage.files import write_private
from app.storage.quota import check_storage
from boundary.business_trace import RULES_VERSION, TraceRecord, audit as audit_trace
from boundary.business_types import decode_json

router = APIRouter()
MAX_RECORD_BYTES = 131072
REVIEW_VERSION = "manual-business-record-v1"


class NoteInput(DTO):
    reviewer_note: str = Field(min_length=1, max_length=2000)


async def record_access(conn, review_id: str, user: Principal, admin: bool = False):
    row = await one(conn, "SELECT * FROM business_record_reviews WHERE review_id=?", (review_id,))
    if not row:
        raise AppError(404, "NOT_FOUND", "Objek tidak ditemukan.")
    report, role = await owned(conn, "reports", "report_id", row["report_id"], user)
    if admin and role != "PROGRAM_ADMIN":
        raise AppError(404, "NOT_FOUND", "Objek tidak ditemukan.")
    if role != "PROGRAM_ADMIN" and row["publication_status"] != "PUBLISHED":
        raise AppError(404, "NOT_FOUND", "Objek tidak ditemukan.")
    return row, report, role


def projection(row, role: str) -> dict:
    provenance = json.loads(row["provenance_json"])
    output = {"review_id": row["review_id"], "report_revision_id": row["report_revision_id"],
              "report_revision_number": provenance["report_revision_number"],
              "mode": "MANUAL_RECORD_REVIEW", "vulnerability_verdict": None,
              "ground_truth": None, "summary": row["hunter_summary"]}
    if role == "PROGRAM_ADMIN":
        output.update({key: row[key] for key in (
            "record_sha256", "byte_size", "imported_at", "review_status", "reviewer_note",
            "reviewed_at", "publication_status", "scope_version_id")})
        output["result"] = json.loads(row["result_json"])
        output["provenance"] = provenance
    return output


async def record_bytes(config, row) -> bytes:
    root = config.data_dir.resolve()
    expected = Path("evidence") / "manual-business" / (row["review_id"]+".json")
    if row["record_path"] != str(expected):
        raise AppError(409, "RECORD_INTEGRITY", "Rekaman memerlukan pemeriksaan storage.")
    path = root / expected
    for parent in (path, *path.parents):
        if parent == root:
            break
        if parent.is_symlink():
            raise AppError(409, "RECORD_INTEGRITY", "Rekaman memerlukan pemeriksaan storage.")
    def read():
        with path.open("rb") as stream:
            return stream.read(MAX_RECORD_BYTES+1)
    try:
        raw = await asyncio.to_thread(read)
    except OSError:
        raise AppError(409, "RECORD_INTEGRITY", "Rekaman tidak tersedia atau berubah.") from None
    if len(raw) != row["byte_size"] or digest(raw) != row["record_sha256"]:
        raise AppError(409, "RECORD_INTEGRITY", "Rekaman tidak tersedia atau berubah.")
    return raw


@router.get("/api/reports/{report_id}/business-records")
async def list_records(report_id: str, request: Request, user: Principal = Depends(principal)):
    async with request.app.state.db.connect() as conn:
        _, role = await owned(conn, "reports", "report_id", report_id, user)
        rows = await all_rows(conn, "SELECT * FROM business_record_reviews WHERE report_id=? "
                              "AND (?='PROGRAM_ADMIN' OR publication_status='PUBLISHED') ORDER BY imported_at DESC LIMIT 20",
                              (report_id, role))
    return [projection(row, role) for row in rows]


@router.post("/api/reports/{report_id}/revisions/{revision_id}/business-records", status_code=201)
async def import_record(report_id: str, revision_id: str, request: Request, user: Principal = Depends(principal)):
    # Authorize before parsing and again inside the write transaction.
    async with request.app.state.db.connect() as conn:
        _, role = await owned(conn, "reports", "report_id", report_id, user)
        if role != "PROGRAM_ADMIN":
            raise AppError(403, "ROLE_DENIED", "Impor rekaman memerlukan admin program.")
    async with request.form(max_files=1, max_fields=0, max_part_size=MAX_RECORD_BYTES+1) as form:
        values = list(form.multi_items())
        if len(values) != 1 or values[0][0] != "file" or not hasattr(values[0][1], "read"):
            raise AppError(422, "RECORD_FIELDS", "Unggah satu file JSON tanpa field tambahan.")
        raw = await values[0][1].read(MAX_RECORD_BYTES+1)
    if len(raw) > MAX_RECORD_BYTES:
        raise AppError(413, "RECORD_LIMIT", "Rekaman maksimal 128 KiB.")
    try:
        value = TraceRecord.model_validate(decode_json(raw, MAX_RECORD_BYTES))
    except (ValueError, RecursionError):
        raise AppError(422, "RECORD_SCHEMA", "Rekaman JSON tidak sesuai format kontrol alur bisnis.") from None
    result = audit_trace(value.model_dump(mode="json"))
    config = request.app.state.config
    review_id, now = uid(), time.time()
    path = config.data_dir / "evidence" / "manual-business" / (review_id+".json")
    async with request.app.state.db.transaction() as conn:
        report, role = await owned(conn, "reports", "report_id", report_id, user)
        if role != "PROGRAM_ADMIN":
            raise AppError(403, "ROLE_DENIED", "Impor rekaman memerlukan admin program.")
        revision = await one(conn, "SELECT * FROM report_revisions WHERE revision_id=? AND report_id=?", (revision_id, report_id))
        if not revision:
            raise AppError(404, "NOT_FOUND", "Revisi tidak ditemukan.")
        claim = Claim.model_validate_json(revision["claim_json"])
        if claim.category != "BUSINESS_LOGIC" or claim.claim_count != 1:
            raise AppError(409, "BUSINESS_CLAIM_REQUIRED", "Gunakan snapshot dengan satu klaim business logic.")
        scope = await one(conn, "SELECT s.* FROM scope_versions s JOIN programs p "
                          "ON p.active_scope_version_id=s.scope_version_id WHERE p.program_id=?", (report["program_id"],))
        if not scope:
            raise AppError(409, "BUSINESS_RULES_REQUIRED", "Admin perlu mengaktifkan versi aturan bisnis terlebih dahulu.")
        rules = ScopeDraft.model_validate_json(scope["rules_json"])
        if (rules.business_rules_version != RULES_VERSION or not rules.business_rules.strip()
                or any(phase.trace.rules_version != rules.business_rules_version for phase in value.phases)):
            raise AppError(409, "BUSINESS_RULES_MISMATCH", "Versi aturan aktif harus sesuai format rekaman bisnis yang didukung.")
        previous = await one(conn, "SELECT * FROM business_record_reviews WHERE report_revision_id=? AND record_sha256=?",
                             (revision_id, digest(raw)))
        if previous:
            await record_bytes(config, previous)
            return projection(previous, role)
        if (await one(conn, "SELECT count(*) FROM business_record_reviews WHERE report_id=?", (report_id,)))[0] >= 20:
            raise AppError(409, "RECORD_COUNT_LIMIT", "Maksimal 20 rekaman per laporan.")
        await rate_limit(conn, "business-import:"+user.user_id, 5, 60)
        await asyncio.to_thread(check_storage, config, len(raw))
        provenance = {"source": "ADMIN_UPLOADED_UNATTESTED_RECORD", "review_version": REVIEW_VERSION,
                      "review_id": review_id, "report_id": report_id, "report_revision_id": revision_id,
                      "report_revision_number": revision["revision_number"],
                      "report_content_hash": revision["content_hash"], "scope_version_id": scope["scope_version_id"],
                      "business_rules_version": rules.business_rules_version,
                      "business_rules_sha256": digest(rules.business_rules), "record_sha256": digest(raw),
                      "imported_by": user.user_id, "target_requests": 0, "model_calls": 0,
                      "binding": "uploaded record attached to report; target/actor authenticity not established"}
        await asyncio.to_thread(write_private, config.data_dir, path, raw, MAX_RECORD_BYTES)
        try:
            await conn.execute("INSERT INTO business_record_reviews(review_id,report_id,report_revision_id,scope_version_id,"
                               "imported_by,imported_at,record_path,record_sha256,byte_size,result_json,provenance_json) "
                               "VALUES (?,?,?,?,?,?,?,?,?,?,?)", (review_id, report_id, revision_id, scope["scope_version_id"],
                               user.user_id, now, str(path.relative_to(config.data_dir)), digest(raw), len(raw), packed(result), packed(provenance)))
            await audit(conn, user.user_id, "BUSINESS_RECORD_IMPORTED", {"review_id": review_id, "record_sha256": digest(raw),
                        "report_revision_id": revision_id, "consistency_status": result["status"]})
        except BaseException:
            await asyncio.to_thread(path.unlink, missing_ok=True)
            raise
        row = await one(conn, "SELECT * FROM business_record_reviews WHERE review_id=?", (review_id,))
        return projection(row, role)


@router.get("/api/business-records/{review_id}/record")
async def original_record(review_id: str, request: Request, user: Principal = Depends(principal)):
    async with request.app.state.db.connect() as conn:
        row, _, _ = await record_access(conn, review_id, user, admin=True)
    raw = await record_bytes(request.app.state.config, row)
    return Response(raw, media_type="application/json", headers={"Content-Disposition": 'attachment; filename="business-record.json"'})


@router.get("/api/business-records/{review_id}/workflow", response_model=WorkflowPacket)
async def evidence_workflow(review_id: str, request: Request, user: Principal = Depends(principal)):
    async with request.app.state.db.connect() as conn:
        await conn.execute("BEGIN")
        row, report, _ = await record_access(conn, review_id, user, admin=True)
        revision = await one(conn, "SELECT * FROM report_revisions WHERE revision_id=? AND report_id=?",
                             (row["report_revision_id"], report["report_id"]))
        scope = await one(conn, "SELECT * FROM scope_versions WHERE scope_version_id=? AND program_id=?",
                          (row["scope_version_id"], report["program_id"]))
        current = await one(conn, "SELECT revision_id FROM report_revisions WHERE report_id=? ORDER BY revision_number DESC LIMIT 1",
                            (report["report_id"],))
        program = await one(conn, "SELECT active_scope_version_id FROM programs WHERE program_id=?", (report["program_id"],))
        raw = await record_bytes(request.app.state.config, row)
    try:
        value = TraceRecord.model_validate(decode_json(raw, MAX_RECORD_BYTES))
        result = audit_trace(value.model_dump(mode="json"))
        provenance = json.loads(row["provenance_json"])
        rules = ScopeDraft.model_validate_json(scope["rules_json"])
        claim = Claim.model_validate_json(revision["claim_json"])
        if (packed(result) != packed(json.loads(row["result_json"])) or
                provenance["source"] != "ADMIN_UPLOADED_UNATTESTED_RECORD" or
                provenance["review_version"] != REVIEW_VERSION or
                provenance["review_id"] != row["review_id"] or
                provenance["report_id"] != report["report_id"] or
                provenance["report_revision_id"] != revision["revision_id"] or
                provenance["report_revision_number"] != revision["revision_number"] or
                provenance["report_content_hash"] != revision["content_hash"] or
                provenance["scope_version_id"] != scope["scope_version_id"] or
                provenance["business_rules_version"] != rules.business_rules_version or
                provenance["business_rules_sha256"] != digest(rules.business_rules) or
                provenance["record_sha256"] != digest(raw)):
            raise ValueError("WORKFLOW_BINDING_INVALID")
        binding = Binding(review_id=row["review_id"], report_id=report["report_id"],
                          report_revision_id=revision["revision_id"], report_revision_number=revision["revision_number"],
                          report_content_hash=revision["content_hash"], scope_version_id=scope["scope_version_id"],
                          business_rules_version=rules.business_rules_version, business_rules_sha256=digest(rules.business_rules),
                          record_sha256=digest(raw), is_current_report_revision=current["revision_id"] == revision["revision_id"],
                          is_current_scope=program["active_scope_version_id"] == scope["scope_version_id"])
        return build_workflow(binding=binding,
                              claim=UntrustedClaim(primary_claim=claim.primary_claim, asset_alias=claim.asset_alias,
                                                   path=claim.path, category=claim.category, claim_count=claim.claim_count),
                              business_rules=rules.business_rules, result=result)
    except (ValueError, KeyError, TypeError, RecursionError):
        raise AppError(409, "WORKFLOW_BINDING_INVALID", "Rekaman atau binding konteks tidak cocok; perlu ditinjau admin.") from None


@router.post("/api/business-records/{review_id}/review")
async def review_record(review_id: str, body: NoteInput, request: Request, user: Principal = Depends(principal)):
    if not body.reviewer_note.strip():
        raise AppError(422, "REVIEW_NOTE_REQUIRED", "Tulis catatan review.")
    async with request.app.state.db.transaction() as conn:
        row, _, _ = await record_access(conn, review_id, user, admin=True)
        await record_bytes(request.app.state.config, row)
        await audit(conn, user.user_id, "BUSINESS_RECORD_REVIEWED", {"review_id": review_id,
                    "previous_note": row["reviewer_note"], "note": body.reviewer_note})
        await conn.execute("UPDATE business_record_reviews SET review_status='REVIEWED',reviewer_note=?,reviewed_by=?,reviewed_at=?,"
                           "publication_status='PRIVATE',hunter_summary=NULL WHERE review_id=?",
                           (body.reviewer_note, user.user_id, time.time(), review_id))
    return {"review_status": "REVIEWED", "publication_status": "PRIVATE"}


@router.post("/api/business-records/{review_id}/publish")
async def publish_record(review_id: str, request: Request, user: Principal = Depends(principal)):
    async with request.app.state.db.transaction() as conn:
        row, _, _ = await record_access(conn, review_id, user, admin=True)
        if row["review_status"] != "REVIEWED":
            raise AppError(409, "REVIEW_REQUIRED", "Tinjau rekaman sebelum membagikan ringkasan.")
        await record_bytes(request.app.state.config, row)
        status = json.loads(row["result_json"])["status"]
        labels = {"CONSISTENT": "konsisten", "INCONSISTENT": "memiliki ketidaksesuaian", "INCOMPLETE": "belum lengkap"}
        summary = ("Rekaman unggahan telah ditinjau admin. Rekaman " + labels.get(status, "tidak dapat diperiksa") +
                   ". Ini pemeriksaan konsistensi rekaman, bukan pengujian langsung target atau keputusan kerentanan. Keaslian sumber dan izin aktor belum dibuktikan.")
        await conn.execute("UPDATE business_record_reviews SET publication_status='PUBLISHED',hunter_summary=? WHERE review_id=?", (summary, review_id))
        await audit(conn, user.user_id, "BUSINESS_RECORD_PUBLISHED", {"review_id": review_id, "projection": REVIEW_VERSION})
    return {"publication_status": "PUBLISHED"}
