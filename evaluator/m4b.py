"""Explicit local XSS product smoke. Resets synthetic lab, never provider calls or startup work."""
import asyncio
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import time
from uuid import uuid4

from boundary.browser import BrowserCapture
from evaluator.m2 import cli, operator, reset
from evaluator.m3 import checked, login
from evaluator.m4 import browser_processes, lab_log

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / "artifacts/m4b"
CLAIM = {"asset_alias": "portal", "path": "/notifications/preview", "method": "GET", "category": "XSS",
         "account_aliases": ["requester-a", "requester-b"],
         "primary_claim": "Fixture marker dapat mengeksekusi JavaScript pada pratinjau notifikasi"}


async def start(client, program, title="Development M4b", claim=None):
    c = checked(await client.post(f"/api/programs/{program}/conversations"), 201)
    cid = c["conversation_id"]
    checked(await client.post(f"/api/conversations/{cid}/messages", json={"body": "DEVELOPMENT: fixture tetap; bukan dataset/GT.",
        "title": title+" "+str(uuid4()), "expected_draft_version": 0}), 201)
    snapshot = checked(await client.post(f"/api/conversations/{cid}/reports", json={"expected_draft_version": 1, "claim": claim or CLAIM}), 201)
    payload = {"report_revision_id": snapshot["report_revision_id"], "execution_mode": "mock", "tool_execution_mode": "LAB"}
    headers = {"Idempotency-Key": str(uuid4())}
    path = f"/api/reports/{snapshot['report_id']}/runs"
    first = checked(await client.post(path, json=payload, headers=headers), 202)
    repeated = checked(await client.post(path, json=payload, headers=headers), 202)
    assert first["run_id"] == repeated["run_id"]
    return cid, first["run_id"]


async def terminal(client, rid):
    deadline = time.monotonic()+190
    while time.monotonic() < deadline:
        result = checked(await client.get(f"/api/runs/{rid}"))
        if result["queue_status"] not in {"QUEUED", "LEASED"}:
            return result
        await asyncio.sleep(.5)
    raise RuntimeError("PRODUCT_RUN_DID_NOT_TERMINATE")


async def verify(cancel_only=False, cancel_account="hunter-b"):
    DIRECTORY.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    result = {"status": "RUNNING", "model": "mock; no live inference", "tool": "actual Docker Chromium", "results": []}
    clients = [await login(name) for name in ("hunter-a", "hunter-b", "admin")]
    a, b, admin = clients
    cancel_client = {"hunter-a": a, "hunter-b": b, "admin": admin}[cancel_account]
    active = None
    try:
        p = checked(await a.get("/api/programs"))[0]["program_id"]
        await asyncio.to_thread(operator, "register_browser")
        for condition, verdict in ([] if cancel_only else [("vulnerable", "CONFIRMED"), ("fixed", "REFUTED")]):
            await asyncio.to_thread(reset, "fixed", xss_condition=condition)
            cid, active = await start(a, p)
            public = await terminal(a, active)
            private = checked(await admin.get(f"/api/runs/{active}"))
            assert private["process_status"] == "COMPLETED", private["error_code"]
            assert private["assessment"]["system_verified"]["verdict"] == verdict
            assert private["validation_kind"] == "XSS" and public["assessment"] is None and public["awaiting_review"]
            assert private["counters"]["target_requests"] == 8 and private["counters"]["browser_actions"] == 20
            assert private["counters"]["model_calls"] == 1 and len(private["evidence"]) == 4
            assert (await b.get(f"/api/runs/{active}/export")).status_code == 404
            captures = []
            nonces = []
            for e in private["evidence"]:
                eid = e["evidence_id"]
                assert (await a.get(f"/api/evidence/{eid}")).status_code == 404
                obs = checked(await admin.get(f"/api/evidence/{eid}"))["observation"]
                cap = BrowserCapture.model_validate_json(obs["body"])
                assert cap.initial_storage_empty and cap.js_control and cap.sandbox_requested and cap.screenshot_base64
                assert obs["request_attempts"] == 2 and obs["responses_received"] == 2
                assert len(cap.marker_events) == (1 if condition == "vulnerable" and cap.fixture == "marker-v1" else 0)
                nonces.append(str(cap.nonce))
                captures.append({"evidence_id": eid, "fixture": cap.fixture, "marker_events": len(cap.marker_events), "screenshot_sha256": cap.screenshot_sha256})
            assert len(set(nonces)) == 4
            assert (await admin.post(f"/api/runs/{active}/publish")).status_code == 409
            checked(await admin.post(f"/api/runs/{active}/review", json={"reviewer_note": "Private development inspection <img src=x>"}))
            checked(await admin.post(f"/api/runs/{active}/publish"))
            exported = checked(await a.get(f"/api/runs/{active}/export"))
            assert exported["assessment"]["verdict"] == verdict
            text = json.dumps(exported)
            for secret in nonces+["Private development", "<img", "screenshot_base64", "raw_model", "requester-a", "evidence_id"]:
                assert secret not in text
            assert "browser lab aktual" in exported["assessment"]["summary"]
            assert not await asyncio.to_thread(browser_processes)
            log = await asyncio.to_thread(lab_log)
            assert sum(row[2] for row in log) == 8
            assert {row[1] for row in log} == {"/api/auth/login", "/notifications/preview"}
            result["results"].append({"condition": condition, "conversation_id": cid, "run_id": active, "verdict": verdict,
                "requests": 8, "evidence": captures, "review_publication_export_idempotency": "PASS", "private_capture_denied_to_hunter": True})
            active = None
            print(json.dumps({"phase": condition, "status": "PASS", "verdict": verdict}), flush=True)
        # Actual product cancel on first delayed browser action: no operator run bypass.
        await asyncio.to_thread(reset, "fixed", xss_condition="fixed")
        await asyncio.to_thread(cli, "lab", "lab.maintenance", "arm-browser-delay")
        _, active = await start(cancel_client, p, "Development M4b cancel")
        for _ in range(80):
            state = await asyncio.to_thread(cli, "lab", "lab.maintenance", "inspect")
            if state["browser_delay_started"]:
                break
            await asyncio.sleep(.1)
        else:
            raise RuntimeError("DELAYED_BROWSER_ACTION_NOT_OBSERVED")
        checked(await cancel_client.post(f"/api/runs/{active}/cancel"))
        stopped = await terminal(cancel_client, active)
        assert stopped["process_status"] == "CANCELLED" and stopped["assessment"] is None
        await asyncio.sleep(8.5)  # Let the already-entered server handler quiesce before reset.
        private = checked(await admin.get(f"/api/runs/{active}"))
        assert not private["evidence"] and not await asyncio.to_thread(browser_processes)
        log = await asyncio.to_thread(lab_log)
        result["cancel_actual_log"] = log
        assert sum(row[2] for row in log) == 2
        assert {row[1] for row in log} == {"/api/auth/login", "/notifications/preview"}
        readiness = checked(await admin.get("/api/readiness"))
        assert readiness["lab"] == "OPERATOR_CHECK_REQUIRED"
        result["results"].append({"cancel_run_id": active, "actual_requests": 2, "no_followup_actions": True,
            "assessment": None, "retained_evidence": 0, "dirty_gate": True, "browser_processes_after_cancel": 0})
        active = None
        await asyncio.to_thread(reset, "fixed", xss_condition="fixed")
        result.update(status="PASS", readiness=checked(await admin.get("/api/readiness")))
    except BaseException:
        result["status"] = "FAILED"
        result["active_run_id"] = active
        if active:
            await admin.post(f"/api/runs/{active}/cancel")
        raise
    finally:
        encoded = json.dumps(result, indent=2)
        name = "cancel" if cancel_only else "api"
        (DIRECTORY/f"{name}-{stamp}.json").write_text(encoded, encoding="utf-8")
        (DIRECTORY/f"{name}-verification.json").write_text(encoded, encoding="utf-8")
        for client in clients:
            await client.aclose()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cancel-only", action="store_true", help="Only rerun cancellation; preserve successful condition phases and start quotas")
    parser.add_argument("--cancel-account", choices=["hunter-a", "hunter-b", "admin"], default="hunter-b")
    args = parser.parse_args()
    asyncio.run(verify(args.cancel_only, args.cancel_account))
