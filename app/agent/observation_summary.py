"""Read-only observation projection, with no inference or target execution."""
import asyncio
import hashlib
import json
import os
from pathlib import Path
from uuid import UUID

from app.common import AppError
from app.storage.db import all_rows, one
from boundary.contracts import ActionEnvelope, canonical, observation_from
from boundary.files import safe_path

KINDS = {"HTTP_EXCHANGE": ("http_request", "worker_http", "HTTP"),
         "BROWSER_PROBE": ("browser_probe", "worker_browser", "Browser"),
         "UPLOAD_EXCHANGE": ("upload_fixture", "worker_upload", "Upload")}


def read_observation(data_dir: Path, run_id: str, evidence_id: str, expected_hash: str) -> dict:
    UUID(run_id)
    UUID(evidence_id)
    root = data_dir / "evidence" / run_id
    if (not root.resolve().is_relative_to(data_dir.resolve()) or
            (data_dir / "evidence").is_symlink() or root.is_symlink()):
        raise ValueError("Unsafe evidence path")
    path = safe_path(root, evidence_id + ".json")
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    with os.fdopen(descriptor, "rb") as stream:
        raw = stream.read(2 * 1048576 + 1)
    if len(raw) > 2 * 1048576 or hashlib.sha256(raw).hexdigest() != expected_hash:
        raise ValueError("Evidence integrity mismatch")
    return json.loads(raw)


async def build(conn, run, role: str, data_dir: Path) -> dict:
    revision = await one(conn, "SELECT * FROM report_revisions WHERE revision_id=? AND report_id=?",
                         (run["report_revision_id"], run["report_id"]))
    report = await one(conn, "SELECT * FROM reports WHERE report_id=?", (run["report_id"],))
    convo = await one(conn, "SELECT * FROM conversations WHERE conversation_id=?", (report["conversation_id"],))
    program = await one(conn, "SELECT * FROM programs WHERE program_id=?", (run["program_id"],))
    latest = await one(conn, "SELECT revision_id FROM report_revisions WHERE report_id=? ORDER BY revision_number DESC LIMIT 1",
                       (run["report_id"],))
    current = (latest[0] == run["report_revision_id"] and convo["draft_version"] == revision["draft_version"] and
               program["active_scope_version_id"] == run["scope_version_id"] and
               program["authorization_epoch"] == run["authorization_epoch"])
    result = {"schema_version": "observations-summary-v1", "origin": "APPLICATION_STRUCTURED_PROJECTION",
              "label": "Ringkasan observasi terstruktur — dibuat aplikasi, bukan AI",
              "run_id": run["run_id"], "report_revision_id": run["report_revision_id"], "is_current": current,
              "execution_mode": run["execution_mode"], "tool_execution_mode": run["tool_execution_mode"],
              "status": "NO_EVIDENCE", "summary": "Belum ada observasi target tersimpan untuk diringkas.",
              "observations": [], "verdict": None, "target_execution_allowed": False, "model_dispatch_allowed": False}
    if run["tool_execution_mode"] != "LAB":
        return result | {"status": "NO_TARGET_EVIDENCE", "summary": "Simulasi plumbing; tidak ada bukti pengujian target."}
    if role != "PROGRAM_ADMIN":
        assessment = await one(conn, "SELECT publication_status,review_status,hunter_summary FROM assessments WHERE run_id=?", (run["run_id"],))
        if assessment and assessment["publication_status"] == "PUBLISHED" and assessment["review_status"] == "REVIEWED":
            return result | {"status": "PUBLISHED", "summary": assessment["hunter_summary"], "label": "Ringkasan yang dibagikan admin"}
        return result | {"status": "AWAITING_PUBLICATION", "summary": "Observasi internal hanya untuk admin. Ringkasan menunggu review dan publikasi."}
    rows = await all_rows(conn, "SELECT e.*,a.tool_name,a.arguments_json,a.policy_result,h.status handoff_status,"
                          "h.action_seq,h.envelope_json,h.envelope_hash,h.observation_json "
                          "FROM evidence e LEFT JOIN actions a USING(action_id,run_id) "
                          "LEFT JOIN handoff_actions h USING(action_id,run_id) WHERE e.run_id=? ORDER BY h.action_seq LIMIT 41",
                          (run["run_id"],))
    if not rows:
        return result
    facts = []
    try:
        if len(rows) > 40 or not revision or report["program_id"] != run["program_id"] or report["owner_user_id"] != run["owner_user_id"]:
            raise ValueError("Invalid run binding")
        sequences = set()
        for row in rows:
            tool, source, label = KINDS[row["kind"]]
            envelope = ActionEnvelope.model_validate_json(row["envelope_json"])
            envelope.authorize(now=envelope.issued_at)
            document = await asyncio.to_thread(read_observation, data_dir, run["run_id"], row["evidence_id"], row["sha256"])
            obs = observation_from(document)
            args = envelope.validated_arguments
            provenance = json.loads(row["provenance_json"])
            expected_path = Path("evidence") / run["run_id"] / (row["evidence_id"] + ".json")
            if (row["tool_name"] != tool or envelope.tool_name != tool or row["policy_result"] != "ALLOW" or
                    row["handoff_status"] != "RECEIVED" or row["action_seq"] in sequences or
                    Path(row["artifact_path"]) != expected_path or row["target_alias"] != "portal" or
                    str(envelope.run_id) != run["run_id"] or str(envelope.action_id) != row["action_id"] or
                    str(envelope.program_id) != run["program_id"] or envelope.target_id != run["target_id"] or
                    str(envelope.scope_version_id) != run["scope_version_id"] or
                    envelope.authorization_epoch != run["authorization_epoch"] or
                    str(envelope.target_snapshot_id) != run["target_snapshot_id"] or
                    hashlib.sha256(canonical(envelope.model_dump(mode="json"))).hexdigest() != row["envelope_hash"] or
                    str(obs.run_id) != run["run_id"] or str(obs.action_id) != row["action_id"] or
                    obs.action_seq != envelope.action_seq or obs.action_seq != row["action_seq"] or
                    obs.envelope_hash != row["envelope_hash"] or str(obs.target_snapshot_id) != run["target_snapshot_id"] or
                    str(obs.boot_id) != run["worker_boot_id"] or obs.actor_alias != row["actor_alias"] or
                    (obs.method, obs.relative_path, obs.actor_alias) != (args.method, args.relative_path, args.account_alias) or
                    json.loads(row["arguments_json"]) != args.model_dump(mode="json") or
                    document != json.loads(row["observation_json"]) or
                    provenance != {"source": source, "mode": "lab_tools", "run_id": run["run_id"],
                                   "action_id": row["action_id"], "evidence_id": row["evidence_id"],
                                   "worker_boot_id": run["worker_boot_id"], "envelope_hash": row["envelope_hash"],
                                   "snapshot_id": run["target_snapshot_id"]}):
                raise ValueError("Evidence binding mismatch")
            sequences.add(row["action_seq"])
            # Only enums and numbers. No body, URL/path, identity, notes, screenshots or evaluator labels.
            facts.append({"evidence_id": row["evidence_id"], "action_seq": obs.action_seq, "tool": label,
                          "method": obs.method, "status": obs.status, "http_status": obs.http_status,
                          "request_attempts": obs.request_attempts, "responses_received": obs.responses_received,
                          "truncated": obs.truncated})
    except (ValueError, TypeError, KeyError, OSError, RecursionError):
        raise AppError(409, "EVIDENCE_BINDING_INVALID", "Ringkasan tidak tersedia: integritas atau binding observasi perlu ditinjau admin.") from None
    return result | {"status": "AVAILABLE", "summary": f"{len(facts)} observasi tersimpan terikat pada run ini. Status HTTP dan kelengkapan respons bukan verdict kerentanan.",
                     "binding": {"report_id": run["report_id"], "report_revision_id": run["report_revision_id"],
                                 "report_revision_number": revision["revision_number"], "report_content_hash": revision["content_hash"],
                                 "scope_version_id": run["scope_version_id"], "target_snapshot_id": run["target_snapshot_id"]},
                     "observations": facts}
