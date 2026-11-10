"""Synthetic stored records for projection/UI QA only. Never runs a target."""
import hashlib
import time
from pathlib import Path

from app.common import packed, uid
from app.storage.db import one
from app.storage.files import write_private
from boundary.contracts import ActionEnvelope, BrowserArguments, BrowserObservation, HttpArguments, Observation, UploadArguments, UploadObservation, canonical


async def attach_observation(app, run_id: str, kind="HTTP_EXCHANGE"):
    async with app.state.db.transaction() as conn:
        run = await one(conn, "SELECT * FROM runs WHERE run_id=?", (run_id,))
        snapshot, boot, action, evidence = uid(), uid(), uid(), uid()
        await conn.execute("UPDATE runs SET tool_execution_mode='LAB',process_status='COMPLETED',queue_status='FINISHED',"
                           "finished_at=?,target_snapshot_id=?,worker_boot_id=? WHERE run_id=?", (time.time(), snapshot, boot, run_id))
        if kind == "BROWSER_PROBE":
            args = BrowserArguments(account_alias="requester-a", fixture="inert-v1", nonce=uid())
            tool, source, cls, template = "browser_probe", "worker_browser", BrowserObservation, "/notifications/preview"
        elif kind == "UPLOAD_EXCHANGE":
            args = UploadArguments(relative_path=f"/api/requests/{uid()}/attachments", fixture="inert-v1", nonce=uid())
            tool, source, cls, template = "upload_fixture", "worker_upload", UploadObservation, "/api/requests/{id}/attachments"
        else:
            args = HttpArguments(method="GET", relative_path="/api/attachments/sample", account_alias="requester-a")
            tool, source, cls, template = "http_request", "worker_http", Observation, "/api/attachments/{id}"
        now = time.time()
        envelope = ActionEnvelope(run_id=run_id, action_id=action, action_seq=1, program_id=run["program_id"],
                                  scope_version_id=run["scope_version_id"], authorization_epoch=run["authorization_epoch"],
                                  target_snapshot_id=snapshot, tool_name=tool, validated_arguments=args,
                                  allowed_rules=[{"path_template": template, "methods": [args.method]}], issued_at=now,
                                  expires_at=now+5, network_remaining=40, artifact_remaining=16777216)
        envelope_json = canonical(envelope.model_dump(mode="json"))
        envelope_hash = hashlib.sha256(envelope_json).hexdigest()
        body = '{"private_note":"INTERNAL_NOTE","api_key":"secret-only-fixture","condition":"PRIVATE_EVALUATOR_LABEL","dom_excerpt":"PRIVATE_DOM"}'
        obs = cls(run_id=run_id, action_id=action, action_seq=1, envelope_hash=envelope_hash, target_snapshot_id=snapshot,
                  boot_id=boot, status="OK", http_status=200, actor_alias=args.account_alias, method=args.method,
                  relative_path=args.relative_path, body=body, body_sha256=hashlib.sha256(body.encode()).hexdigest(),
                  request_attempts=2, responses_received=2, captured_at=now)
        data = canonical(obs.model_dump(mode="json"))
        path = app.state.config.data_dir / "evidence" / run_id / (evidence + ".json")
        write_private(app.state.config.data_dir, path, data, 2 * 1048576)
        await conn.execute("INSERT INTO actions VALUES (?,?,?,1,?,?,NULL,'ALLOW','SYNTHETIC_QA_RECORD',?,?)",
                           (action, run_id, tool, packed(args.model_dump(mode="json")), args.account_alias, now, now))
        await conn.execute("INSERT INTO handoff_actions VALUES (?,?,1,?,?,'RECEIVED',?,?)",
                           (action, run_id, envelope_json.decode(), envelope_hash, packed(obs.model_dump(mode="json")), now+5))
        provenance = {"source": source, "mode": "lab_tools", "run_id": run_id, "action_id": action,
                      "evidence_id": evidence, "worker_boot_id": boot, "envelope_hash": envelope_hash, "snapshot_id": snapshot}
        await conn.execute("INSERT INTO evidence(evidence_id,run_id,action_id,kind,captured_at,artifact_path,sha256,actor_alias,target_alias,summary,provenance_json) "
                           "VALUES (?,?,?,?,?,?,?,?,?,?,?)", (evidence, run_id, action, kind, now, str(path.relative_to(app.state.config.data_dir)),
                            hashlib.sha256(data).hexdigest(), args.account_alias, "portal", "PRIVATE_SUMMARY_WITH_SECRET", packed(provenance)))
        verified = {"verdict": "INCONCLUSIVE", "reasoning": "Rekaman sintetis QA; tidak ada pengujian target.",
                    "supporting_evidence_ids": [], "contradicting_evidence_ids": []}
        await conn.execute("INSERT INTO assessments(run_id,claim_id,verdict,raw_model_json,system_verified_json,reviewer_note) "
                           "VALUES (?,?,'INCONCLUSIVE',?,?,?)", (run_id, run["primary_claim_id"], '{"private":"PRIVATE_MODEL"}', packed(verified), "INTERNAL_NOTE"))
        return {"run_id": run_id, "evidence_id": evidence, "action_id": action, "path": path}
