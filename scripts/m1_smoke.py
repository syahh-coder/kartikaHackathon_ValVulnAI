"""Explicit local operator smoke check. Uses only the loopback app and Docker CLI.

No model provider or lab request. Creates synthetic records, optionally seeds demo
accounts and restarts only this Compose app. Never deletes data/volumes.
"""
import argparse
import asyncio
import hashlib
import json
import os
from pathlib import Path
import secrets
import subprocess
import time

import httpx

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = "http://127.0.0.1:8000"
RULE = {"asset_alias": "portal", "path_template": "/api/attachments/{id}",
        "methods": ["GET", "DELETE"], "capabilities": ["BAC"]}


def docker(*args, env=None):
    result = subprocess.run(["docker", "compose", *args], cwd=ROOT, env=env, capture_output=True, text=True)
    if result.returncode:
        # Do not print process args/environment or provider/account credentials.
        raise RuntimeError("Docker operation failed; inspect docker compose logs app locally")
    return result.stdout


def summary():
    # Only aggregate counts/digests leave the container, never session/password/report values.
    code = """import sqlite3,json,hashlib
c=sqlite3.connect('/data/valvuln.sqlite3')
tables=['users','sessions','memberships','programs','scope_versions','conversations','messages','reports','report_revisions','runs','actions','evidence','assessments','ledger','provider_attempts']
output={}
for table in tables:
 rows=c.execute('SELECT * FROM '+table+' ORDER BY rowid').fetchall()
 output[table]={'count':len(rows),'sha256':hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest()}
print(json.dumps(output))"""
    return json.loads(docker("exec", "-T", "app", "python", "-c", code))


def checked(response, status=200):
    if response.status_code != status:
        raise RuntimeError(f"Local smoke failed: HTTP {response.status_code}, expected {status}")
    return response.json()


async def login(name, password):
    client = httpx.AsyncClient(base_url=ORIGIN, trust_env=False, follow_redirects=False,
                               timeout=10, headers={"Origin": ORIGIN})
    token = checked(await client.get("/api/auth/csrf"))["csrf_token"]
    data = checked(await client.post("/api/auth/login", json={"login_name": name, "password": password},
                                     headers={"X-CSRF-Token": token}))
    client.headers["X-CSRF-Token"] = data["csrf_token"]
    return client


async def wait_ready():
    async with httpx.AsyncClient(base_url=ORIGIN, trust_env=False, timeout=2) as client:
        for _ in range(100):
            try:
                if (await client.get("/api/health")).status_code==200:
                    return
            except httpx.TransportError:
                pass
            await asyncio.sleep(0.2)
    raise RuntimeError("App did not become healthy within startup deadline")


async def main(args):
    await wait_ready()
    private = ROOT / ".local-data" / "demo-password.txt"
    password = os.environ.get("VALVULN_SEED_PASSWORD")
    if not password and private.exists():
        password = private.read_text(encoding="utf-8").strip()
    if args.seed:
        if not password:
            private.parent.mkdir(parents=True, exist_ok=True)
            password = secrets.token_urlsafe(24)
            private.write_text(password, encoding="utf-8")
            private.chmod(0o600)
        docker("exec", "-T", "-e", "VALVULN_SEED_PASSWORD", "app", "python", "-m", "app.operator",
               env={**os.environ, "VALVULN_SEED_PASSWORD": password})
    if not password:
        raise RuntimeError("Use --seed first, or supply VALVULN_SEED_PASSWORD for the operator-seeded accounts")
    clients = []
    try:
        for name in ("admin", "hunter-a", "hunter-b"):
            clients.append(await login(name, password))
        admin, hunter, other = clients
        program = checked(await admin.get("/api/programs"))[0]["program_id"]
        guideline = checked(await admin.get(f"/api/programs/{program}/guidelines"))
        if guideline["state"] == "NOT_CONFIGURED":
            draft = checked(await admin.post(f"/api/programs/{program}/scope-drafts", json={
                "source_text": "SIMULASI M1. Profil awal lampiran; bukan bukti portal sudah tersedia.", "in_scope_rules": [RULE]}), 201)
            checked(await admin.post(f"/api/programs/{program}/scope-drafts/{draft['scope_version_id']}/activate"))
        cid = checked(await hunter.post(f"/api/programs/{program}/conversations"), 201)["conversation_id"]
        checked(await hunter.post(f"/api/conversations/{cid}/messages", json={
            "body": "SIMULASI smoke M1: klaim BAC lampiran sintetis; tidak dieksekusi ke target.", "expected_draft_version": 0}), 201)
        report = checked(await hunter.post(f"/api/conversations/{cid}/reports", json={"expected_draft_version": 1,
            "claim": {"asset_alias": "portal", "path": "/api/attachments/sample", "method": "DELETE", "category": "BAC",
                      "account_aliases": ["requester-a", "requester-b"], "primary_claim": "Klaim utama sintetis"}}), 201)
        rid, revision = report["report_id"], report["report_revision_id"]
        request = {"report_revision_id": revision, "execution_mode": "mock"}
        key = secrets.token_hex(12)
        started = await asyncio.gather(*[hunter.post(f"/api/reports/{rid}/runs", json=request, headers={"Idempotency-Key": key}) for _ in range(5)])
        runs = [checked(r, 202) for r in started]
        assert len({r["run_id"] for r in runs})==1
        run_id = runs[0]["run_id"]
        for _ in range(100):
            result = checked(await hunter.get(f"/api/runs/{run_id}"))
            if result["queue_status"] == "FINISHED":
                break
            await asyncio.sleep(0.1)
        assert result["process_status"]=="COMPLETED", result["process_status"]
        assert result["assessment"]["verdict"]=="INCONCLUSIVE" and result["counters"]["target_requests"]==0
        assert "raw_model" not in json.dumps(result) and result["inference_provider"]=="mock"
        assert (await other.get(f"/api/reports/{rid}")).status_code==404
        assert (await other.get(f"/api/runs/{run_id}/export")).status_code==404
        before = summary()
        if args.restart_check:
            docker("restart", "app")
            await wait_ready()
            assert before == summary(), "Restart altered persistent records or dispatched work"
            assert checked(await hunter.get(f"/api/runs/{run_id}")) == result
        if args.stop_start_check:
            docker("stop", "app")
            docker("up", "-d", "--build")
            await wait_ready()
            assert before==summary(), "Stop/start altered persistent records or dispatched work"
            assert checked(await hunter.get(f"/api/runs/{run_id}"))==result
        print(json.dumps({"status": "PASS", "mode": "mock", "verdict": "INCONCLUSIVE", "target_requests": 0,
                          "idempotency": "PASS (5 concurrent requests)", "cross_hunter_access": "404",
                          "restart_persistence": "PASS" if args.restart_check else "NOT_RUN",
                          "stop_start_persistence": "PASS" if args.stop_start_check else "NOT_RUN",
                          "tables_verified": len(before), "live_provider_called": False}, indent=2))
    finally:
        for client in clients:
            await client.aclose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", action="store_true", help="Explicit seed; never replaces existing passwords")
    parser.add_argument("--restart-check", action="store_true", help="Restart app and compare persistent records")
    parser.add_argument("--stop-start-check", action="store_true", help="Stop app, rebuild/up, compare persistent records")
    asyncio.run(main(parser.parse_args()))
