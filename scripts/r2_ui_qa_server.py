"""Disposable R2 QA app. Synthetic stored observations, no worker/provider network."""
import argparse
import asyncio
import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread

import httpx
import uvicorn
from fastapi import Depends, Request

from app.auth import Principal, member, principal
from app.common import packed
from app.config import Settings
from app.main import create_app
from app.operator import seed
from app.providers.triage_contracts import TriageSuggestion
from app.agent.text_triage import MockTriageTransport
from app.storage.db import one
from scripts.r2_qa_fixtures import attach_observation


class QATransport(MockTriageTransport):
    def __init__(self):
        self.calls = 0

    async def dispatch(self, call_id, prompt):
        self.calls += 1
        if "R2_WAIT" in prompt:
            await asyncio.Event().wait()
        reply = await super().dispatch(call_id, prompt)
        result = TriageSuggestion.model_validate_json(reply.result.text)
        result.primary_claim = '<img src=x onerror="window.r2Injected=true"> Klaim sintetis QA.'
        result.reason = "MOCK QA; bukan inferensi model nyata."
        reply.result.text = result.model_dump_json()
        return reply


async def setup(app, program, password):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url=app.state.config.public_origin,
                                 headers={"Origin": app.state.config.public_origin}) as client:
        async def login(name):
            csrf = (await client.get("/api/auth/csrf")).json()["csrf_token"]
            response = await client.post("/api/auth/login", json={"login_name": name, "password": password}, headers={"X-CSRF-Token": csrf})
            assert response.status_code == 200
            client.headers["X-CSRF-Token"] = response.json()["csrf_token"]
        await login("admin")
        scope = {"source_text": "Guideline sintetis QA R2.", "in_scope_rules": [{"asset_alias": "portal", "path_template": "/api/attachments/{id}", "methods": ["GET", "DELETE"], "capabilities": ["BAC"]}]}
        scope_id = (await client.post(f"/api/programs/{program}/scope-drafts", json=scope)).json()["scope_version_id"]
        await client.post(f"/api/programs/{program}/scope-drafts/{scope_id}/activate")
        await login("hunter-a")
        cid = (await client.post(f"/api/programs/{program}/conversations")).json()["conversation_id"]
        await client.post(f"/api/conversations/{cid}/messages", json={"body": "Klaim sintetis untuk QA tampilan; tidak ada pengujian target.", "title": "R2 Observasi sintetis", "expected_draft_version": 0})
        report = (await client.post(f"/api/conversations/{cid}/reports", json={"expected_draft_version": 1, "claim": {"asset_alias": "portal", "path": "/api/attachments/sample", "method": "DELETE", "category": "BAC", "account_aliases": ["requester-a", "requester-b"], "primary_claim": "Klaim sintetis"}})).json()
        run = (await client.post(f"/api/reports/{report['report_id']}/runs", json={"report_revision_id": report["report_revision_id"]}, headers={"Idempotency-Key": "r2-qa-record"})).json()
        await attach_observation(app, run["run_id"])


async def counts(db):
    async with db.connect() as conn:
        return {t: (await one(conn, f"SELECT count(*) FROM {t}"))[0] for t in
                ("runs", "actions", "handoff_actions", "evidence", "assessments", "ledger", "provider_attempts", "text_triages")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, required=True)
    port = parser.parse_args().port
    if not 1024 <= port <= 65535:
        raise ValueError("Invalid QA loopback port")
    password = json.loads(sys.stdin.readline())["password"]
    with TemporaryDirectory(prefix="valvuln-r2-ui-") as temporary:
        config = Settings(data_dir=Path(temporary), public_origin=f"http://127.0.0.1:{port}", dispatcher_enabled=False,
                          min_free_bytes=0, _env_file=None)
        app = create_app(config)
        program = asyncio.run(seed(app.state.db, password))
        asyncio.run(setup(app, program, password))
        transport = QATransport()
        app.state.text_triage.transport = transport
        baseline = asyncio.run(counts(app.state.db))
        def deny(*args, **kwargs):
            raise AssertionError("QA forbids real provider/target HTTP")
        async def deny_async(*args, **kwargs):
            deny()
        httpx.AsyncHTTPTransport.handle_async_request = deny_async
        httpx.HTTPTransport.handle_request = deny

        @app.post("/qa/configuration")
        async def qa_configuration(request: Request, user: Principal = Depends(principal)):
            async with app.state.db.connect() as conn:
                await member(conn, user, program, admin=True)
            body = await request.json()
            assert body["mode"] in {"mock", "live"}
            config.triage_mode = body["mode"]  # No key: live must fail before dispatch.
            return {"mode": config.triage_mode}

        server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning", access_log=False))
        def control():
            for line in sys.stdin:
                if line.strip() == "stop":
                    break
            server.should_exit = True
        Thread(target=control, daemon=True).start()
        server.run()
        final = asyncio.run(counts(app.state.db))
    print("QA_FINAL " + json.dumps({"baseline": baseline, "counts": final, "mock_dispatches": transport.calls,
                                     "real_provider_requests": 0, "target_requests": 0, "temporary_storage_removed": True}), flush=True)


if __name__ == "__main__":
    main()
