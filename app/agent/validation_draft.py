"""AI-to-claim handoff. Preparing a draft never queues or executes target work."""
import json
import re

from app.auth import owned
from app.common import AppError, audit, digest, packed
from app.policy.targets import check_action, gate
from app.providers.triage_contracts import SCHEMA_VERSION, TriageSuggestion
from app.schemas import Claim
from app.storage.db import all_rows, one

SUBTYPES = {"BAC-08": ("BAC", "DELETE"), "XSS-08": ("XSS", "GET"), "UP-04": ("UPLOAD", "GET")}


async def current_source(conn, user, triage_id, conversation_id=None):
    row = await one(conn, "SELECT * FROM text_triages WHERE triage_id=?", (triage_id,))
    if not row:
        raise AppError(404, "NOT_FOUND", "Saran tidak ditemukan.")
    convo, _ = await owned(conn, "conversations", "conversation_id", row["conversation_id"], user, owner_only=True)
    if conversation_id is not None and row["conversation_id"] != conversation_id:
        raise AppError(409, "TRIAGE_CONTEXT_MISMATCH", "Saran berasal dari laporan berbeda.")
    program = await one(conn, "SELECT * FROM programs WHERE program_id=?", (row["program_id"],))
    if (not program["enabled"] or program["active_scope_version_id"] != row["scope_version_id"] or
            program["authorization_epoch"] != row["authorization_epoch"]):
        raise AppError(409, "TRIAGE_STALE", "Scope berubah. Minta saran untuk konteks terbaru.")
    if convo["draft_version"] != row["draft_version"]:
        raise AppError(409, "TRIAGE_STALE", "Draf berubah. Minta saran untuk versi terbaru.")
    if row["status"] != "SUCCEEDED" or not row["output_json"]:
        raise AppError(409, "TRIAGE_NOT_READY", "Saran belum berhasil; belum dapat dipakai sebagai draf klaim.")
    if row["schema_version"] != SCHEMA_VERSION:
        raise AppError(409, "TRIAGE_SCHEMA_OUTDATED", "Saran lama tersimpan. Minta saran baru untuk menyiapkan klaim.")
    return row


def claim_from(row):
    suggestion = TriageSuggestion.model_validate_json(row["output_json"])
    category, method = SUBTYPES.get(suggestion.subtype, ("OTHER", "GET"))
    fields = suggestion.validation_fields
    claim = Claim(category=category, method=method, primary_claim=suggestion.primary_claim,
                  **(fields.model_dump() if fields else {}))
    return suggestion, claim


async def prepare(conn, user, triage_id):
    row = await current_source(conn, user, triage_id)
    suggestion, claim = claim_from(row)
    scope = await one(conn, "SELECT rules_json FROM scope_versions WHERE scope_version_id=? AND state='ACTIVE'",
                      (row["scope_version_id"],))
    scope_rules = json.loads(scope[0]) if scope else None
    rows = await all_rows(conn, "SELECT * FROM target_bindings WHERE program_id=?", (row["program_id"],))
    bindings = {r["asset_alias"]: {**dict(r), "profile": json.loads(r["profile_json"])} for r in rows}
    scope_decision, capability, status, _ = gate(claim, scope_rules, bindings)
    missing = list(suggestion.missing_information)
    source = json.loads(row["input_json"])["report"]
    report = "\n".join(source.get(k, "") for k in ("title", "text", "attachment_text"))
    # An extracted identifier must occur as a token in the submitted report.
    # AI suggestions cannot silently introduce another object, actor or asset.
    for name, values in (("asset_alias", [claim.asset_alias]), ("path", [claim.path]),
                         ("control_path", [claim.control_path]), ("account_aliases", claim.account_aliases)):
        for value in values:
            if value and not re.search(r"(?<![A-Za-z0-9_/-])" + re.escape(value) + r"(?![A-Za-z0-9_/-])", report):
                missing.append(f"Konfirmasi {name}: nilai ekstraksi tidak ditemukan persis pada laporan.")
    if suggestion.subtype not in SUBTYPES:
        capability, status = "UNSUPPORTED", "UNSUPPORTED"
    elif status == "SCOPE_CHECKED":
        from app.agent.lab_validation import validator_for
        try:
            for args in validator_for(claim).plan(claim):
                check_action(claim, scope_rules, bindings[claim.asset_alias], method=args.method,
                             path=args.relative_path, account_alias=args.account_alias)
        except AppError as exc:
            status = exc.code if exc.code in {"UNSUPPORTED", "NEEDS_INFO"} else "POLICY_BLOCKED"
            missing.append(exc.message)
    if not claim.asset_alias or not claim.path or len(set(claim.account_aliases)) != 2:
        missing.append("Lengkapi alias aset, path dan dua alias akun uji pada formulir konfirmasi.")
    if status == "SCOPE_CHECKED" and missing:
        status = "NEEDS_INFO"
    return {"source_triage_id": triage_id, "conversation_id": row["conversation_id"],
            "expected_draft_version": row["draft_version"], "scope_version_id": row["scope_version_id"],
            "input_hash": row["input_hash"], "schema_version": row["schema_version"], "mode": row["mode"],
            "claim": claim.model_dump(), "scope_decision": scope_decision, "capability_decision": capability,
            "policy_status": status, "missing_information": list(dict.fromkeys(missing)),
            "requires_confirmation": True, "target_execution_allowed": False,
            "model_dispatch_allowed": False, "worker_checked_on_start": True, "verdict": None}


async def record_confirmation(conn, user, row, revision_id, claim):
    # The original suggestion remains immutable. Edits are explicit user input,
    # bound to the new report revision and rechecked by Workflow on run creation.
    previous = await one(conn, "SELECT 1 FROM audit_events WHERE event_type='AI_CLAIM_CONFIRMED' "
                         "AND json_extract(details_json,'$.report_revision_id')=? "
                         "AND json_extract(details_json,'$.source_triage_id')=?", (revision_id, row["triage_id"]))
    if previous:
        return
    config = json.loads(row["config_json"])
    await audit(conn, user.user_id, "AI_CLAIM_CONFIRMED", {
        "source_triage_id": row["triage_id"], "report_revision_id": revision_id,
        "conversation_id": row["conversation_id"], "draft_version": row["draft_version"],
        "scope_version_id": row["scope_version_id"], "authorization_epoch": row["authorization_epoch"],
        "input_hash": row["input_hash"], "suggestion_hash": digest(row["output_json"]),
        "confirmed_claim_hash": digest(packed(claim.model_dump())), "mode": row["mode"],
        "provider": config["provider"], "requested_model": config["requested_model"]})
