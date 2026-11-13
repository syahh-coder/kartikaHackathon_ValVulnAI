"""One explicit live triage through a running app, its normal API and shared ledger."""
import argparse
import asyncio
import json
import time
from pathlib import Path
from urllib.parse import urlsplit
from uuid import uuid4

import httpx


async def smoke(args):
    url = urlsplit(args.origin)
    if (url.scheme != "http" or url.hostname not in {"127.0.0.1", "localhost"} or not url.port or
            url.username or url.password or url.path or url.query or url.fragment):
        raise ValueError("EXACT_LOOPBACK_APP_ORIGIN_REQUIRED")
    result = {"provider": args.provider, "live_verified": False, "target_requests": 0, "automatic_fallback": False}

    async def checked(response, expected=200):
        if response.status_code != expected:
            raise ValueError("APP_HTTP_" + str(response.status_code))
        return response.json()

    async with httpx.AsyncClient(base_url=args.origin, headers={"Origin": args.origin},
                                 trust_env=False, follow_redirects=False, timeout=10) as client:
        readiness = await checked(await client.get("/api/readiness"))
        if (readiness["triage_mode"] != "live" or readiness["triage_provider"] != args.provider or
                readiness["text_provider"] != "CONFIGURED_NOT_VERIFIED"):
            return result | {"status": "CONFIGURATION_REQUIRED", "provider_requests": 0}
        csrf = await checked(await client.get("/api/auth/csrf"))
        login = await checked(await client.post("/api/auth/login", headers={"X-CSRF-Token": csrf["csrf_token"]},
            json={"login_name": args.username, "password": args.password_file.read_text(encoding="utf-8").strip()}))
        client.headers["X-CSRF-Token"] = login["csrf_token"]
        programs = await checked(await client.get("/api/programs"))
        if not programs:
            raise ValueError("PROGRAM_MEMBERSHIP_REQUIRED")
        conversation = await checked(await client.post(f"/api/programs/{programs[0]['program_id']}/conversations"), 201)
        cid = conversation["conversation_id"]
        draft = await checked(await client.post(f"/api/conversations/{cid}/messages", json={
            "title": "Smoke AI teks - data sintetis",
            "body": "Klaim penghapusan lampiran lintas pemilik. ID objek dan kontrol belum dilengkapi. Identifikasi informasi yang kurang; jangan menguji target.",
            "expected_draft_version": 0}), 201)
        triage = await checked(await client.post(f"/api/conversations/{cid}/triages",
            headers={"Idempotency-Key": "smoke-" + str(uuid4())},
            json={"expected_draft_version": draft["draft_version"]}), 202)
        deadline = time.monotonic() + 75
        while triage["status"] in {"PENDING", "RUNNING"} and time.monotonic() < deadline:
            await asyncio.sleep(0.2)
            triage = await checked(await client.get(f"/api/triages/{triage['triage_id']}"))
        if triage["status"] in {"PENDING", "RUNNING"}:
            await checked(await client.post(f"/api/triages/{triage['triage_id']}/cancel"))
            triage = await checked(await client.get(f"/api/triages/{triage['triage_id']}"))
        conversation = await checked(await client.get(f"/api/conversations/{cid}"))
        if conversation["run_ids"]:
            raise ValueError("UNEXPECTED_TARGET_RUN")
        return result | {"status": triage["status"], "error_code": triage["error_code"],
                         "triage_id": triage["triage_id"], "live_verified": triage["status"] == "SUCCEEDED",
                         "attempts": [{"status": a["status"], "cost_status": a["cost_status"],
                                       "reserved_idr": a["reserved_idr"], "actual_idr": a["actual_idr"]}
                                      for a in triage["attempts"]]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", help="Explicitly send a live request via the app ledger")
    parser.add_argument("--provider", choices=["openrouter", "azure"], default="openrouter")
    parser.add_argument("--origin", default="http://127.0.0.1:8000")
    parser.add_argument("--username", default="hunter-a")
    parser.add_argument("--password-file", type=Path, default=Path(".local-data/demo-password.txt"))
    args = parser.parse_args(argv)
    if not args.execute:
        print(json.dumps({"status": "LIVE_TEST_DEFERRED", "provider_requests": 0, "live_verified": False}))
        return 2
    try:
        result = asyncio.run(smoke(args))
    except (ValueError, OSError, KeyError, httpx.HTTPError):
        result = {"status": "SMOKE_FAILED_OR_OUTCOME_UNKNOWN", "live_verified": False,
                  "action": "Inspect app triage and shared ledger before any retry."}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["live_verified"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
