"""Explicit operator smoke through the product API. Resets synthetic lab only."""
import asyncio
import json
from pathlib import Path
import time
from uuid import uuid4

import httpx

from evaluator.m2 import cli, compose, operator, reset

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = "http://127.0.0.1:8000"


def checked(response, expected=200):
    if response.status_code != expected:
        raise RuntimeError(f"HTTP {response.status_code}: {response.json().get('error_code', 'unexpected')}")
    return response.json()


async def login(name):
    # Seeded local demo only. Never include passwords/cookies in artifacts.
    password = (ROOT/".local-data/demo-password.txt").read_text().strip()
    client = httpx.AsyncClient(base_url=ORIGIN, trust_env=False, headers={"Origin": ORIGIN}, timeout=15)
    token = checked(await client.get("/api/auth/csrf"))["csrf_token"]
    data = checked(await client.post("/api/auth/login", json={"login_name": name, "password": password}, headers={"X-CSRF-Token": token}))
    client.headers["X-CSRF-Token"] = data["csrf_token"]
    return client


def access_count():
    return json.loads(compose("exec", "-T", "--user", "10001:10001", "lab", "python", "-c",
        "import sqlite3,json; c=sqlite3.connect('/data/lab.sqlite3'); print(json.dumps(c.execute('SELECT count(*) FROM access_log').fetchone()[0]))"))


def claim_for(snapshot):
    return {"asset_alias": "portal", "method": "DELETE", "category": "BAC", "account_aliases": ["requester-a", "requester-b"],
            "path": "/api/attachments/"+snapshot["objects"]["requester-b"]["attachment_id"],
            "control_path": "/api/attachments/"+snapshot["objects"]["requester-a"]["attachment_id"],
            "primary_claim": "Akun penguji dapat menghapus lampiran milik akun lain."}


async def start(client, program, claim):
    conversation = checked(await client.post(f"/api/programs/{program}/conversations"), 201)
    cid = conversation["conversation_id"]
    checked(await client.post(f"/api/conversations/{cid}/messages", json={"body": "DEVELOPMENT M3. " + claim["primary_claim"],
        "title": "Development API M3", "expected_draft_version": 0}), 201)
    checked(await client.post(f"/api/conversations/{cid}/attachments", files={"file": ("development.md", b"Synthetic development report; no benchmark label.", "text/markdown")}), 201)
    snapshot = checked(await client.post(f"/api/conversations/{cid}/reports", json={"expected_draft_version": 2, "claim": claim}), 201)
    payload = {"report_revision_id": snapshot["report_revision_id"], "execution_mode": "mock", "tool_execution_mode": "LAB"}
    key = str(uuid4())
    response = checked(await client.post(f"/api/reports/{snapshot['report_id']}/runs", json=payload, headers={"Idempotency-Key": key}), 202)
    repeated = checked(await client.post(f"/api/reports/{snapshot['report_id']}/runs", json=payload, headers={"Idempotency-Key": key}), 202)
    assert response["run_id"] == repeated["run_id"]
    return response["run_id"]


async def terminal(client, run_id):
    for _ in range(120):
        result = checked(await client.get(f"/api/runs/{run_id}"))
        if result["queue_status"] not in {"QUEUED", "LEASED"}:
            return result
        await asyncio.sleep(.25)
    raise RuntimeError("Run did not terminate")


async def verify_api():
    clients = [await login(n) for n in ("hunter-a", "hunter-b", "admin")]
    a, b, admin = clients
    results = []
    try:
        p = checked(await a.get("/api/programs"))[0]["program_id"]
        await asyncio.to_thread(operator, "configure_scope")
        for condition, verdict in (("vulnerable", "CONFIRMED"), ("fixed", "REFUTED")):
            snapshot = await asyncio.to_thread(reset, condition)
            run_id = await start(a, p, claim_for(snapshot))
            public = await terminal(a, run_id)
            private = checked(await admin.get(f"/api/runs/{run_id}"))
            assert private["process_status"] == "COMPLETED", private["error_code"]
            assert private["assessment"]["system_verified"]["verdict"] == verdict
            assert public["assessment"] is None and public["awaiting_review"]
            assert private["counters"]["target_requests"] == 14 and len(private["evidence"]) == 7
            assert (await b.get(f"/api/runs/{run_id}/export")).status_code == 404
            eid = private["evidence"][0]["evidence_id"]
            assert (await a.get(f"/api/evidence/{eid}")).status_code == 404
            checked(await admin.get(f"/api/evidence/{eid}"))
            checked(await admin.post(f"/api/runs/{run_id}/review", json={"reviewer_note": "Operator inspected development controls; private note."}))
            checked(await admin.post(f"/api/runs/{run_id}/publish"))
            exported = checked(await a.get(f"/api/runs/{run_id}/export"))
            assert exported["assessment"]["verdict"] == verdict
            assert all(k not in exported for k in ("evidence", "target_id", "requested_by"))
            state = await asyncio.to_thread(cli, "lab", "lab.maintenance", "inspect")
            victim = snapshot["objects"]["requester-b"]["attachment_id"]
            assert next(x["deleted"] for x in state["attachments"] if x["id"] == victim) == (condition == "vulnerable")
            results.append({"condition": condition, "run_id": run_id, "verdict": verdict, "requests": 14, "evidence": 7,
                            "projection_review_export": "PASS", "idempotency": "PASS"})
        snapshot = await asyncio.to_thread(reset, "fixed")
        baseline = await asyncio.to_thread(access_count)
        for change, status in (({"asset_alias": "unregistered"}, "OUT_OF_SCOPE"), ({"path": None}, "NEEDS_INFO")):
            run_id = await start(admin, p, claim_for(snapshot) | change)
            result = await terminal(admin, run_id)
            assert result["process_status"] == status and result["counters"]["target_requests"] == 0
        assert await asyncio.to_thread(access_count) == baseline
        results.append({"out_of_scope_unknown_zero_actual_lab_requests": "PASS"})
        # Delay response after a committed control DELETE; cancel must close I/O,
        # retain trace, block the target and never continue to the victim DELETE.
        snapshot = await asyncio.to_thread(reset, "vulnerable", arm_delay=True)
        run_id = await start(b, p, claim_for(snapshot))
        control = snapshot["objects"]["requester-a"]["attachment_id"]
        for _ in range(60):
            state = await asyncio.to_thread(cli, "lab", "lab.maintenance", "inspect")
            if next(x["deleted"] for x in state["attachments"] if x["id"] == control): break
            await asyncio.sleep(.1)
        else: raise RuntimeError("Delayed mutation not observed")
        checked(await b.post(f"/api/runs/{run_id}/cancel"))
        result = await terminal(b, run_id)
        assert result["process_status"] == "CANCELLED" and result["assessment"] is None
        await asyncio.sleep(8.5)
        state = await asyncio.to_thread(cli, "lab", "lab.maintenance", "inspect")
        victim = snapshot["objects"]["requester-b"]["attachment_id"]
        assert not next(x["deleted"] for x in state["attachments"] if x["id"] == victim)
        private = checked(await admin.get(f"/api/runs/{run_id}"))
        assert len(private["evidence"]) == 3
        results.append({"cancel_run_id": run_id, "cancel_after_mutation": "PASS", "retained_evidence": 3, "no_further_victim_delete": True})
        await asyncio.to_thread(reset, "fixed")
        readiness = checked(await a.get("/api/readiness"))
        assert readiness["worker"] == "IDLE" and readiness["lab"] == "OPERATOR_VERIFIED"
        directory = ROOT/"artifacts/m3"
        directory.mkdir(parents=True, exist_ok=True)
        output = {"status": "PASS", "model": "mock", "tool": "HTTP lab actual", "results": results, "readiness": readiness}
        (directory/"api-verification.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
        print(json.dumps(output, indent=2))
    finally:
        for client in clients:
            await client.aclose()


if __name__ == "__main__":
    asyncio.run(verify_api())
