import asyncio
import hashlib
import json
import re
import time

from fastapi import APIRouter, Depends, Header, Request

from app.auth import Principal, owned, principal
from app.common import AppError, audit, packed
from app.schemas import Claim, RunInput, ReviewInput
from app.storage.db import one, all_rows

router = APIRouter()


async def validation_kind(conn, run):
    revision = await one(conn, "SELECT claim_json FROM report_revisions WHERE revision_id=?", (run["report_revision_id"],))
    return Claim.model_validate_json(revision[0]).category


async def run_projection(conn, run, role: str):
    output = {k: run[k] for k in (
        "run_id", "report_revision_id", "scope_version_id", "process_status", "queue_status", "scope_decision",
        "capability_decision", "execution_mode", "tool_execution_mode", "model_id", "inference_provider", "error_code", "created_at", "finished_at")}
    output["counters"] = json.loads(run["counters_json"])
    output["validation_kind"] = await validation_kind(conn, run)
    assessment = await one(conn, "SELECT * FROM assessments WHERE run_id=?", (run["run_id"],))
    output["assessment"] = None
    if assessment:
        if role == "PROGRAM_ADMIN":
            output["assessment"] = {"claim_id": assessment["claim_id"], "raw_model": json.loads(assessment["raw_model_json"]),
                                    "system_verified": json.loads(assessment["system_verified_json"]),
                                    "review_status": assessment["review_status"], "publication_status": assessment["publication_status"],
                                    "analyst_override": assessment["analyst_override"], "reviewer_note": assessment["reviewer_note"],
                                    "reviewed_by": assessment["reviewed_by"], "reviewed_at": assessment["reviewed_at"]}
        elif assessment["publication_status"] == "PUBLISHED":
            output["assessment"] = {"verdict": assessment["analyst_override"] or assessment["verdict"],
                                    "summary": assessment["hunter_summary"], "review_status": "REVIEWED"}
        else:
            output["assessment"] = {"verdict": "INCONCLUSIVE", "summary": "Simulasi tanpa pengujian target."} if run["execution_mode"]=="mock" and run["tool_execution_mode"]=="NONE" else None
    output["awaiting_review"] = bool(assessment and assessment["publication_status"] != "PUBLISHED" and run["tool_execution_mode"] == "LAB")
    if role == "PROGRAM_ADMIN":
        output["requested_by"] = run["requested_by"]
        output["target_id"] = run["target_id"]
        rows = await all_rows(conn, "SELECT evidence_id,action_id,kind,summary,sha256 FROM evidence WHERE run_id=? ORDER BY captured_at", (run["run_id"],))
        output["evidence"] = [dict(r) for r in rows]
    return output


@router.post("/api/runs/{run_id}/review")
async def review(run_id: str, body: ReviewInput, request: Request, user: Principal = Depends(principal)):
    async with request.app.state.db.transaction() as conn:
        _, role = await owned(conn, "runs", "run_id", run_id, user)
        if role != "PROGRAM_ADMIN":
            raise AppError(403, "ROLE_DENIED", "Review memerlukan admin program.")
        assessment = await one(conn, "SELECT * FROM assessments WHERE run_id=?", (run_id,))
        if not assessment:
            raise AppError(409, "ASSESSMENT_REQUIRED", "Assessment belum tersedia.")
        await audit(conn, user.user_id, "ASSESSMENT_REVIEW", {"previous_override": assessment["analyst_override"],
                         "previous_note": assessment["reviewer_note"], "override": body.analyst_override, "note": body.reviewer_note}, run_id)
        await conn.execute("UPDATE assessments SET review_status='REVIEWED',analyst_override=?,reviewer_note=?,reviewed_by=?,reviewed_at=?,"
                           "publication_status='PRIVATE',hunter_summary=NULL WHERE run_id=?",
                           (body.analyst_override, body.reviewer_note, user.user_id, time.time(), run_id))
    return {"review_status": "REVIEWED", "publication_status": "PRIVATE"}


@router.post("/api/runs/{run_id}/publish")
async def publish(run_id: str, request: Request, user: Principal = Depends(principal)):
    async with request.app.state.db.transaction() as conn:
        run, role = await owned(conn, "runs", "run_id", run_id, user)
        if role != "PROGRAM_ADMIN":
            raise AppError(403, "ROLE_DENIED", "Publikasi memerlukan admin program.")
        assessment = await one(conn, "SELECT * FROM assessments WHERE run_id=?", (run_id,))
        if not assessment or assessment["review_status"] != "REVIEWED":
            raise AppError(409, "REVIEW_REQUIRED", "Tinjau hasil sebelum publikasi.")
        verdict = assessment["analyst_override"] or assessment["verdict"]
        # Only application-owned text is public. Free-form analyst/model/target text stays private.
        summaries = {"CONFIRMED": "Dampak klaim utama terkonfirmasi pada pengujian lab ini.",
                     "REFUTED": "Klaim utama disangkal oleh kontrol pada pengujian lab ini.",
                     "INCONCLUSIVE": "Bukti belum cukup untuk memutuskan klaim utama."}
        prefix = "Keputusan analis. " if assessment["analyst_override"] else "Hasil verifier. "
        category = await validation_kind(conn, run)
        tool = "upload dan browser lab aktual" if category == "UPLOAD" else "browser lab aktual" if category == "XSS" else "HTTP lab aktual"
        mode = f"Planner mock; {tool}, bukan model live." if run["tool_execution_mode"]=="LAB" else "Simulasi tanpa pengujian target."
        proof = ""
        verified = json.loads(assessment["system_verified_json"])
        if run["tool_execution_mode"] == "LAB" and category == "XSS" and verified.get("verdict") in {"CONFIRMED", "REFUTED"}:
            proof = (" Bukti tersanitasi. Kontrol: JavaScript aktif, penyimpanan awal kosong dan teks inert tampil tanpa callback "
                     "pada konteks browser baru di dua akun uji.")
            proof += (" Uji fixture marker: callback terikat nonce pada frame utama pratinjau teramati di kedua akun."
                      if verified["verdict"] == "CONFIRMED" else
                      " Uji fixture marker: tampil sebagai teks tanpa callback di kedua akun.")
            proof += " Terbatas pada fixture pratinjau ini; payload lain, persistensi dan eksfiltrasi belum diuji."
        elif run["tool_execution_mode"] == "LAB" and category == "UPLOAD" and verified.get("verdict") in {"CONFIRMED", "REFUTED"}:
            proof = (" Bukti tersanitasi: dua upload fixture teks tetap, pembaca terpisah yang ditugaskan, konteks browser baru, JavaScript aktif, kontrol nama inert dan label aman.")
            proof += (" Marker pada nama lampiran dieksekusi pada frame utama daftar." if verified["verdict"] == "CONFIRMED" else " Nama fixture tampil sebagai teks tanpa callback pada daftar.")
            proof += " Terbatas pada metadata nama fixture; isi aktif, penimpaan dan payload lain belum diuji oleh run ini."
        elif run["tool_execution_mode"] == "LAB" and category == "BAC" and verified.get("verdict") in {"CONFIRMED", "REFUTED"}:
            # Publish a fixed, de-identified account/object trace; never copy free-form
            # controls, body text, paths, identities or credentials into this projection.
            proof = (" Bukti tersanitasi. Kontrol: pemilik dapat membaca objek laporan sebelum aksi; "
                     "akun penguji tidak dapat membacanya. Akun penguji dapat membaca dan menghapus "
                     "objek kontrol miliknya sendiri; pembacaan setelahnya ditolak.")
            proof += (" Uji lintas akun: penghapusan objek laporan berhasil dan pemilik kehilangan akses setelah aksi."
                      if verified["verdict"] == "CONFIRMED" else
                      " Uji lintas akun: penghapusan ditolak dan objek laporan tetap dapat dibaca pemilik.")
        await conn.execute("UPDATE assessments SET publication_status='PUBLISHED',hunter_summary=? WHERE run_id=?",
                           (prefix+summaries[verdict]+" "+mode+proof, run_id))
        await audit(conn, user.user_id, "ASSESSMENT_PUBLISHED", {"verdict": verdict, "projection": "fixed-text-v1"}, run_id)
    return {"publication_status": "PUBLISHED"}


@router.post("/api/reports/{report_id}/runs", status_code=202)
async def new_run(report_id: str, body: RunInput, request: Request, user: Principal = Depends(principal),
                  idempotency_key: str = Header(default="")):
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", idempotency_key):
        raise AppError(422, "IDEMPOTENCY_REQUIRED", "Gunakan Idempotency-Key 1-128 karakter yang sah.")
    async with request.app.state.db.transaction() as conn:
        report, role = await owned(conn, "reports", "report_id", report_id, user)
        run_id = await request.app.state.workflow.create_run(conn, user, report, body, idempotency_key)
        run = await one(conn, "SELECT * FROM runs WHERE run_id=?", (run_id,))
        return await run_projection(conn, run, role)


@router.get("/api/runs/{run_id}")
@router.get("/api/runs/{run_id}/export")
async def get_run(run_id: str, request: Request, user: Principal = Depends(principal)):
    async with request.app.state.db.connect() as conn:
        run, role = await owned(conn, "runs", "run_id", run_id, user)
        return await run_projection(conn, run, role)


@router.get("/api/runs/{run_id}/observations-summary")
async def observations_summary(run_id: str, request: Request, user: Principal = Depends(principal)):
    from app.agent.observation_summary import build
    async with request.app.state.db.connect() as conn:
        run, role = await owned(conn, "runs", "run_id", run_id, user)
        return await build(conn, run, role, request.app.state.config.data_dir)


@router.post("/api/runs/{run_id}/cancel")
async def cancel(run_id: str, request: Request, user: Principal = Depends(principal)):
    async with request.app.state.db.transaction() as conn:
        run, role = await owned(conn, "runs", "run_id", run_id, user)
        await request.app.state.workflow.cancel(conn, run)
        updated = await one(conn, "SELECT * FROM runs WHERE run_id=?", (run_id,))
        return await run_projection(conn, updated, role)


@router.get("/api/evidence/{evidence_id}")
async def evidence(evidence_id: str, request: Request, user: Principal = Depends(principal)):
    async with request.app.state.db.connect() as conn:
        row = await one(conn, "SELECT * FROM evidence WHERE evidence_id=?", (evidence_id,))
        if not row:
            raise AppError(404, "NOT_FOUND", "Objek tidak ditemukan.")
        _, role = await owned(conn, "runs", "run_id", row["run_id"], user)
        if role != "PROGRAM_ADMIN":
            raise AppError(404, "NOT_FOUND", "Objek tidak ditemukan.")
    output = {k: row[k] for k in ("evidence_id", "run_id", "action_id", "kind", "captured_at", "sha256", "summary")}
    if row["kind"] in {"HTTP_EXCHANGE", "BROWSER_PROBE"}:
        from boundary.contracts import canonical
        from boundary.files import read_json
        root = request.app.state.config.data_dir / "evidence" / row["run_id"]
        document = await asyncio.to_thread(read_json, root, evidence_id+".json", 2*1048576)
        if hashlib.sha256(canonical(document)).hexdigest() != row["sha256"]:
            raise AppError(409, "EVIDENCE_INTEGRITY", "Hash evidence tidak cocok.")
        output["observation"] = document  # JSON only; browser must render textContent.
    return output
