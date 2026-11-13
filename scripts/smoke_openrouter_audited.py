"""One explicit free-model triage smoke through the real API and existing ledger."""
import argparse
import asyncio
import json
import sqlite3
import time
from pathlib import Path
from uuid import uuid4

import httpx

from app.config import Settings
from app.main import create_app
from app.storage import db as storage_db


async def smoke(args):
    config = Settings().model_copy(update={"dispatcher_enabled": False, "triage_retry_enabled": False})
    proof = json.loads(Path(args.preflight).read_text(encoding="utf-8"))
    if (config.triage_provider != "openrouter" or config.triage_mode != "live"
            or proof.get("model") != config.triage_model or proof.get("key", {}).get("http_status") != 200
            or not config.triage_model.endswith(":free")
            or proof.get("models", {}).get("model", {}).get("pricing") != {"prompt": "0", "completion": "0"}
            or config.triage_prompt_usd_per_million != 0 or config.triage_completion_usd_per_million != 0):
        raise RuntimeError("VERIFIED_FREE_PROFILE_REQUIRED")
    if not config.db_path.is_file():
        raise RuntimeError("EXISTING_LEDGER_REQUIRED")
    with sqlite3.connect(config.db_path) as conn:
        versions = {r[0] for r in conn.execute("SELECT version FROM schema_versions")}
        expected = {p.name for p in Path(storage_db.__file__).with_name("migrations").glob("*.sql")}
        if expected != versions:
            raise RuntimeError("SCHEMA_REVIEW_REQUIRED")
        if (conn.execute("SELECT count(*) FROM runs WHERE queue_status IN ('QUEUED','LEASED')").fetchone()[0]
                or conn.execute("SELECT count(*) FROM text_triages WHERE status IN ('PENDING','RUNNING')").fetchone()[0]
                or conn.execute("SELECT count(*) FROM evaluation_jobs WHERE status='DISPATCHED'").fetchone()[0]):
            raise RuntimeError("ACTIVE_WORK_REQUIRES_REVIEW")
        counts_before = {t: conn.execute("SELECT count(*) FROM " + t).fetchone()[0]
                         for t in ("runs", "actions", "evidence", "assessments", "ledger", "provider_attempts")}
        old_ledger = {r[0]: r for r in conn.execute("SELECT * FROM ledger")}
    password = Path(args.password_file).read_text(encoding="utf-8").strip()
    app = create_app(config)
    started = time.monotonic()
    result = {"mode": "live", "provider": "openrouter", "requested_model": config.triage_model,
              "live_verified": False, "counts_before": counts_before, "retry_enabled": False}

    async def checked(response, expected=200):
        data = response.json()
        if response.status_code != expected:
            error = data.get("error", {})
            raise RuntimeError(error.get("code", "HTTP_" + str(response.status_code)))
        return data

    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url=config.public_origin,
                                     headers={"Origin": config.public_origin}) as client:
            csrf = await checked(await client.get("/api/auth/csrf"))
            login = await checked(await client.post("/api/auth/login", headers={"X-CSRF-Token": csrf["csrf_token"]},
                                                    json={"login_name": "hunter-a", "password": password}))
            del password
            client.headers["X-CSRF-Token"] = login["csrf_token"]
            programs = await checked(await client.get("/api/programs"))
            conversation = await checked(await client.post(f"/api/programs/{programs[0]['program_id']}/conversations"), 201)
            cid = conversation["conversation_id"]
            draft = await checked(await client.post(f"/api/conversations/{cid}/messages", json={
                "title": "Smoke koneksi OpenRouter - data sintetis",
                "body": "Laporan sintetis mengklaim penghapusan lampiran lintas pemilik. ID objek dan kontrol belum dilengkapi. Tolong identifikasi informasi yang kurang; tidak meminta pengujian target.",
                "expected_draft_version": 0}), 201)
            triage = await checked(await client.post(f"/api/conversations/{cid}/triages",
                headers={"Idempotency-Key": "audited-smoke-" + str(uuid4())},
                json={"expected_draft_version": draft["draft_version"]}), 202)
            result["triage_id"] = triage["triage_id"]
            deadline = time.monotonic() + config.triage_timeout_seconds + 8
            while triage["status"] in {"PENDING", "RUNNING"} and time.monotonic() < deadline:
                await asyncio.sleep(0.2)
                triage = await checked(await client.get(f"/api/triages/{triage['triage_id']}"))
            if triage["status"] in {"PENDING", "RUNNING"}:
                await client.post(f"/api/triages/{triage['triage_id']}/cancel")
                triage = await checked(await client.get(f"/api/triages/{triage['triage_id']}"))
            result.update(status=triage["status"], error_code=triage["error_code"], attempts=triage["attempts"],
                          suggestion=triage["suggestion"], live_verified=triage["status"] == "SUCCEEDED")
    with sqlite3.connect(config.db_path) as conn:
        counts_after = {t: conn.execute("SELECT count(*) FROM " + t).fetchone()[0] for t in counts_before}
        rows = {r[0]: r for r in conn.execute("SELECT * FROM ledger")}
        result["existing_ledger_unchanged"] = all(rows.get(k) == v for k, v in old_ledger.items())
        result["counts_after"] = counts_after
        result["no_target_work_created"] = all(counts_before[t] == counts_after[t] for t in ("runs", "actions", "evidence", "assessments"))
    result["elapsed_seconds"] = round(time.monotonic() - started, 2)
    Path(args.output).write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "suggestion"}, indent=2))
    return 0 if result["live_verified"] and result["existing_ledger_unchanged"] and result["no_target_work_created"] else 2


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--preflight", required=True)
    parser.add_argument("--password-file", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        raise SystemExit(asyncio.run(smoke(args)))
    except Exception as exc:
        # Never print raw provider responses, environment, passwords, or trace locals.
        print(json.dumps({"status": "SMOKE_FAILED", "error_type": type(exc).__name__,
                          "error_code": str(exc) if isinstance(exc, RuntimeError) else "LOCAL_ERROR", "live_verified": False}))
        raise SystemExit(2)


if __name__ == "__main__":
    main()
