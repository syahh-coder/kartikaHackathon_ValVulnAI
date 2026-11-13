import asyncio
import json
import time
from pathlib import Path

from fastapi import APIRouter, Depends, Request, UploadFile
from fastapi.responses import Response

from app.auth import Principal, member, owned, principal
from app.common import AppError, audit, digest, packed, rate_limit, uid
from app.policy.targets import validate_scope
from app.schemas import MessageInput, ScopeDraft, SnapshotInput
from app.storage.db import all_rows, one
from app.storage.quota import check_storage
from app.storage.files import write_private

router = APIRouter()


async def bindings_for(conn, program_id: str) -> dict[str, dict]:
    rows = await all_rows(conn, "SELECT * FROM target_bindings WHERE program_id=?", (program_id,))
    return {r["asset_alias"]: {**dict(r), "profile": json.loads(r["profile_json"])} for r in rows}


@router.get("/api/programs")
async def programs(request: Request, user: Principal = Depends(principal)):
    async with request.app.state.db.connect() as conn:
        rows = await all_rows(conn, "SELECT p.program_id,p.display_name,p.active_scope_version_id,m.role "
                                   "FROM programs p JOIN memberships m USING(program_id) "
                                   "WHERE m.user_id=? AND m.enabled=1 AND p.enabled=1", (user.user_id,))
    return [dict(r) for r in rows]


@router.get("/api/programs/{program_id}/guidelines")
async def guidelines(program_id: str, request: Request, user: Principal = Depends(principal)):
    async with request.app.state.db.connect() as conn:
        await member(conn, user, program_id)
        row = await one(conn, "SELECT s.* FROM scope_versions s JOIN programs p "
                             "ON p.active_scope_version_id=s.scope_version_id WHERE p.program_id=?", (program_id,))
    if not row:
        return {"state": "NOT_CONFIGURED", "scope_version_id": None}
    return {"scope_version_id": row["scope_version_id"], "version": row["version"],
            "source_text": row["source_text"], "rules": json.loads(row["rules_json"]), "state": row["state"]}


@router.post("/api/programs/{program_id}/scope-drafts", status_code=201)
async def scope_draft(program_id: str, body: ScopeDraft, request: Request, user: Principal = Depends(principal)):
    async with request.app.state.db.transaction() as conn:
        await member(conn, user, program_id, admin=True)
        validate_scope(body, await bindings_for(conn, program_id))
        version = (await one(conn, "SELECT coalesce(max(version),0)+1 n FROM scope_versions WHERE program_id=?", (program_id,)))[0]
        scope_id = uid()
        await conn.execute("INSERT INTO scope_versions(scope_version_id,program_id,version,state,rules_json,source_text,source_hash) "
                           "VALUES (?,?,?,'DRAFT',?,?,?)", (scope_id, program_id, version, packed(body.model_dump()),
                                                           body.source_text, digest(body.source_text)))
        await audit(conn, user.user_id, "SCOPE_DRAFT", {"scope_version_id": scope_id})
    return {"scope_version_id": scope_id, "version": version, "state": "DRAFT"}


@router.get("/api/programs/{program_id}/scope-drafts")
async def scope_drafts(program_id: str, request: Request, user: Principal = Depends(principal)):
    async with request.app.state.db.connect() as conn:
        await member(conn, user, program_id, admin=True)
        rows = await all_rows(conn, "SELECT scope_version_id,version,source_text,rules_json FROM scope_versions "
                              "WHERE program_id=? AND state='DRAFT' ORDER BY version DESC LIMIT 20", (program_id,))
    return [dict(r) for r in rows]


@router.post("/api/programs/{program_id}/scope-drafts/{scope_id}/activate")
async def activate_scope(program_id: str, scope_id: str, request: Request, user: Principal = Depends(principal)):
    async with request.app.state.db.transaction() as conn:
        await member(conn, user, program_id, admin=True)
        row = await one(conn, "SELECT * FROM scope_versions WHERE scope_version_id=? AND program_id=?", (scope_id, program_id))
        if not row:
            raise AppError(404, "NOT_FOUND", "Draf tidak ditemukan.")
        if row["state"] != "DRAFT":
            raise AppError(409, "SCOPE_CONFLICT", "Hanya draf dapat diaktifkan.")
        validate_scope(ScopeDraft.model_validate_json(row["rules_json"]), await bindings_for(conn, program_id))
        await conn.execute("UPDATE scope_versions SET state='RETIRED' WHERE program_id=? AND state='ACTIVE'", (program_id,))
        await conn.execute("UPDATE scope_versions SET state='ACTIVE',activated_by=?,activated_at=? WHERE scope_version_id=?",
                           (user.user_id, time.time(), scope_id))
        await conn.execute("UPDATE programs SET active_scope_version_id=?,authorization_epoch=authorization_epoch+1 WHERE program_id=?",
                           (scope_id, program_id))
        pending = await all_rows(conn, "SELECT run_id FROM runs WHERE program_id=? AND queue_status IN ('QUEUED','LEASED')", (program_id,))
        for run in pending:
            await request.app.state.workflow._stop(conn, run["run_id"], "CANCELLED", "SCOPE_REVOKED")
        await conn.execute("UPDATE ledger SET status='RELEASED' WHERE status='RESERVED' AND provider_attempt_id IS NULL AND run_id IN "
                           "(SELECT run_id FROM runs WHERE program_id=? AND error_code='SCOPE_REVOKED')", (program_id,))
        await audit(conn, user.user_id, "SCOPE_ACTIVATED", {"scope_version_id": scope_id})
    return {"scope_version_id": scope_id, "state": "ACTIVE"}


@router.post("/api/programs/{program_id}/conversations", status_code=201)
async def new_conversation(program_id: str, request: Request, user: Principal = Depends(principal)):
    conversation_id = uid()
    async with request.app.state.db.transaction() as conn:
        await member(conn, user, program_id)
        await conn.execute("INSERT INTO conversations(conversation_id,program_id,owner_user_id,created_at) VALUES (?,?,?,?)",
                           (conversation_id, program_id, user.user_id, time.time()))
    return {"conversation_id": conversation_id, "draft_version": 0}


@router.get("/api/programs/{program_id}/conversations")
async def conversations(program_id: str, request: Request, user: Principal = Depends(principal)):
    async with request.app.state.db.connect() as conn:
        role = await member(conn, user, program_id)
        rows = await all_rows(conn, "SELECT conversation_id,draft_title,draft_version,owner_user_id FROM conversations "
                              "WHERE program_id=? AND (?='PROGRAM_ADMIN' OR owner_user_id=?) ORDER BY created_at DESC LIMIT 100",
                              (program_id, role, user.user_id))
    return [dict(r) for r in rows]


@router.get("/api/conversations/{conversation_id}")
async def conversation(conversation_id: str, request: Request, user: Principal = Depends(principal)):
    async with request.app.state.db.connect() as conn:
        row, _ = await owned(conn, "conversations", "conversation_id", conversation_id, user)
        messages = await all_rows(conn, "SELECT message_id,kind,body,created_at FROM messages WHERE conversation_id=? ORDER BY created_at", (conversation_id,))
        attachment = await one(conn, "SELECT attachment_id,original_name,byte_size FROM attachments WHERE conversation_id=?", (conversation_id,))
        report = await one(conn, "SELECT report_id FROM reports WHERE conversation_id=?", (conversation_id,))
        runs = await all_rows(conn, "SELECT run_id FROM runs WHERE report_id=? ORDER BY created_at DESC", (report[0],)) if report else []
        revision = await one(conn, "SELECT claim_json,revision_id FROM report_revisions WHERE report_id=? ORDER BY revision_number DESC LIMIT 1", (report[0],)) if report else None
        triage = await one(conn, "SELECT triage_id FROM text_triages WHERE conversation_id=? ORDER BY created_at DESC LIMIT 1", (conversation_id,))
    return {**dict(row), "messages": [dict(m) for m in messages], "attachment": dict(attachment) if attachment else None,
            "report_id": report[0] if report else None, "run_ids": [r[0] for r in runs], "latest_claim": json.loads(revision[0]) if revision else None,
            "latest_report_revision_id": revision["revision_id"] if revision else None,
            "latest_triage_id": triage[0] if triage else None}


@router.post("/api/conversations/{conversation_id}/messages", status_code=201)
async def message(conversation_id: str, body: MessageInput, request: Request, user: Principal = Depends(principal)):
    async with request.app.state.db.transaction() as conn:
        row, _ = await owned(conn, "conversations", "conversation_id", conversation_id, user, owner_only=True)
        if row["draft_version"] != body.expected_draft_version:
            raise AppError(409, "DRAFT_STALE", "Muat ulang versi draf terbaru.")
        attachment = await one(conn, "SELECT extracted_text FROM attachments WHERE conversation_id=?", (conversation_id,))
        new_body = (row["draft_body"] + "\n" + body.body).strip()
        if len(new_body) + len(attachment[0] if attachment else "") > 32_000:
            raise AppError(413, "TEXT_LIMIT", "Gabungan laporan dan lampiran maksimal 32.000 karakter.")
        await rate_limit(conn, "chat:"+user.user_id, 10, 60)
        message_id = uid()
        await conn.execute("INSERT INTO messages VALUES (?,?,?,'USER',?,?)",
                           (message_id, conversation_id, user.user_id, body.body, time.time()))
        await conn.execute("UPDATE conversations SET draft_body=?,draft_title=?,draft_version=draft_version+1 WHERE conversation_id=?",
                           (new_body, body.title, conversation_id))
    return {"message_id": message_id, "draft_version": body.expected_draft_version+1}


def decode_upload(filename: str, content: bytes) -> tuple[str, str]:
    if (not filename or len(filename)>200 or any(c in filename for c in ("/", "\\", ":", "\x00")) or
            any(ord(c)<32 for c in filename) or filename in {".", ".."}):
        raise AppError(422, "FILENAME_DENIED", "Nama file tidak sah.")
    suffix = Path(filename).suffix.lower()
    if suffix not in {".txt", ".md"}:
        raise AppError(415, "FORMAT_DENIED", "Gunakan file TXT/MD UTF-8.")
    if len(content)>131072:
        raise AppError(413, "UPLOAD_LIMIT", "File maksimal 128 KiB.")
    try:
        text = content.decode("utf-8-sig", errors="strict")
    except UnicodeDecodeError as exc:
        raise AppError(415, "UTF8_REQUIRED", "File harus UTF-8.") from exc
    if "\x00" in text:
        raise AppError(415, "TEXT_REQUIRED", "File harus teks UTF-8 tanpa NUL.")
    return text, "text/plain" if suffix==".txt" else "text/markdown"


@router.post("/api/conversations/{conversation_id}/attachments", status_code=201)
async def upload(conversation_id: str, request: Request, user: Principal = Depends(principal)):
    # Parse manually to reject injected purpose/owner fields and extra files.
    async with request.form(max_files=1, max_fields=0, max_part_size=131073) as form:
        values = list(form.multi_items())
        if len(values)!=1 or values[0][0]!="file" or not hasattr(values[0][1], "read"):
            raise AppError(422, "UPLOAD_FIELDS", "Satu field file diperlukan.")
        file: UploadFile = values[0][1]
        raw = await file.read(131073)
        text, detected = decode_upload(file.filename or "", raw)
        attachment_id, storage_key = uid(), uid()+".txt"
        directory = request.app.state.config.data_dir / "uploads"
        path = directory / storage_key
        async with request.app.state.db.transaction() as conn:
            row, _ = await owned(conn, "conversations", "conversation_id", conversation_id, user, owner_only=True)
            if len(text)+len(row["draft_body"])>32_000:
                raise AppError(413, "TEXT_LIMIT", "Gabungan laporan maksimal 32.000 karakter.")
            if await one(conn, "SELECT 1 FROM attachments WHERE conversation_id=?", (conversation_id,)):
                raise AppError(409, "ATTACHMENT_EXISTS", "Satu lampiran per draf.")
            await rate_limit(conn, "upload:"+user.user_id, 5, 60)
            await asyncio.to_thread(check_storage, request.app.state.config, len(raw))
            await asyncio.to_thread(write_private, request.app.state.config.data_dir, path, raw, 131072)
            try:
                await conn.execute("INSERT INTO attachments VALUES (?,?,?,?,?,?,?,?,?,?,'PARSED',?)",
                                   (attachment_id, row["program_id"], row["owner_user_id"], conversation_id,
                                    "REPORT", storage_key, file.filename, detected, len(raw), digest(raw), text))
                await conn.execute("UPDATE conversations SET draft_version=draft_version+1 WHERE conversation_id=?", (conversation_id,))
            except BaseException:
                await asyncio.to_thread(path.unlink, missing_ok=True)
                raise
    return {"attachment_id": attachment_id, "byte_size": len(raw), "draft_version": row["draft_version"]+1}


@router.get("/api/attachments/{attachment_id}")
async def attachment(attachment_id: str, request: Request, user: Principal = Depends(principal)):
    async with request.app.state.db.connect() as conn:
        row, _ = await owned(conn, "attachments", "attachment_id", attachment_id, user)
    return Response(row["extracted_text"], media_type="text/plain",
                    headers={"Content-Disposition": 'attachment; filename="report.txt"', "X-Content-Type-Options": "nosniff"})


@router.post("/api/conversations/{conversation_id}/reports", status_code=201)
async def snapshot(conversation_id: str, body: SnapshotInput, request: Request, user: Principal = Depends(principal)):
    async with request.app.state.db.transaction() as conn:
        convo, _ = await owned(conn, "conversations", "conversation_id", conversation_id, user, owner_only=True)
        if convo["draft_version"] != body.expected_draft_version:
            raise AppError(409, "DRAFT_STALE", "Versi draf sudah berubah.")
        source_triage = None
        if body.source_triage_id:
            from app.agent.validation_draft import current_source
            source_triage = await current_source(conn, user, body.source_triage_id, conversation_id)
        attachment = await one(conn, "SELECT * FROM attachments WHERE conversation_id=?", (conversation_id,))
        if not convo["draft_body"].strip() and not attachment:
            raise AppError(422, "REPORT_EMPTY", "Isi laporan diperlukan.")
        report = await one(conn, "SELECT report_id FROM reports WHERE conversation_id=?", (conversation_id,))
        report_id = report[0] if report else uid()
        if not report:
            await conn.execute("INSERT INTO reports VALUES (?,?,?,?)", (report_id, convo["program_id"], convo["owner_user_id"], conversation_id))
        source_hash = digest(packed({"body": convo["draft_body"], "title": convo["draft_title"],
                                    "attachment": attachment["sha256"] if attachment else None, "claim": body.claim.model_dump()}))
        previous = await one(conn, "SELECT * FROM report_revisions WHERE report_id=? AND draft_version=?", (report_id, convo["draft_version"]))
        if previous:
            if previous["content_hash"] != source_hash:
                raise AppError(409, "SNAPSHOT_CONFLICT", "Buat revisi draf baru untuk mengubah klaim snapshot.")
            if source_triage:
                from app.agent.validation_draft import record_confirmation
                await record_confirmation(conn, user, source_triage, previous["revision_id"], body.claim)
            return {"report_id": report_id, "report_revision_id": previous["revision_id"]}
        revision_id = uid()
        version = (await one(conn, "SELECT coalesce(max(revision_number),0)+1 FROM report_revisions WHERE report_id=?", (report_id,)))[0]
        await conn.execute("INSERT INTO report_revisions VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                           (revision_id, report_id, version, convo["draft_version"], convo["draft_title"], convo["draft_body"],
                            attachment["attachment_id"] if attachment else None, attachment["extracted_text"] if attachment else "",
                            source_hash, packed(body.claim.model_dump()), time.time()))
        if source_triage:
            from app.agent.validation_draft import record_confirmation
            await record_confirmation(conn, user, source_triage, revision_id, body.claim)
    return {"report_id": report_id, "report_revision_id": revision_id}


@router.get("/api/programs/{program_id}/reports")
async def reports(program_id: str, request: Request, user: Principal = Depends(principal)):
    async with request.app.state.db.connect() as conn:
        role = await member(conn, user, program_id)
        rows = await all_rows(conn, "SELECT report_id,conversation_id,owner_user_id FROM reports WHERE program_id=? "
                                   "AND (?='PROGRAM_ADMIN' OR owner_user_id=?)", (program_id, role, user.user_id))
    return [dict(r) for r in rows]


@router.get("/api/reports/{report_id}")
async def report(report_id: str, request: Request, user: Principal = Depends(principal)):
    async with request.app.state.db.connect() as conn:
        row, _ = await owned(conn, "reports", "report_id", report_id, user)
        revisions = await all_rows(conn, "SELECT revision_id,revision_number,title,body,attachment_text,content_hash,submitted_at "
                                       "FROM report_revisions WHERE report_id=? ORDER BY revision_number", (report_id,))
    return {**dict(row), "revisions": [dict(r) for r in revisions]}
