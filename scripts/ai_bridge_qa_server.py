"""Disposable MOCK extraction server for browser QA; no cloud/target HTTP."""
import argparse
import asyncio
import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread

import httpx
import uvicorn

from app.agent.text_triage import MockTriageTransport
from app.config import Settings
from app.main import create_app
from app.operator import seed
from app.providers.triage_contracts import TriageSuggestion, ValidationFields
from scripts.r2_ui_qa_server import counts


class QAExtraction(MockTriageTransport):
    calls = 0

    async def dispatch(self, call_id, prompt):
        self.calls += 1
        source = json.loads(prompt)["report"]["text"]
        path = "/outside/item" if "QA_OOS" in source else "/api/attachments/victim"
        reply = await super().dispatch(call_id, prompt)
        suggestion = TriageSuggestion(primary_claim='<img src=x onerror="window.qaInjected=true"> Klaim QA.',
            category="BAC", subtype="BAC-08", missing_information=[], scope_suggestion="IN_SCOPE",
            capability_suggestion="AVAILABLE", reason="MOCK ekstraksi untuk QA tombol dan konfirmasi.",
            validation_fields=ValidationFields(asset_alias="portal", path=path, control_path="/api/attachments/control",
                                              account_aliases=["requester-a", "requester-b"], claim_count=1))
        reply.result.text = reply.redacted_response = suggestion.model_dump_json()
        return reply


async def setup(app, program, password):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url=app.state.config.public_origin,
                                 headers={"Origin": app.state.config.public_origin}) as client:
        csrf = (await client.get("/api/auth/csrf")).json()["csrf_token"]
        login = await client.post("/api/auth/login", json={"login_name": "admin", "password": password},
                                  headers={"X-CSRF-Token": csrf})
        client.headers["X-CSRF-Token"] = login.json()["csrf_token"]
        draft = await client.post(f"/api/programs/{program}/scope-drafts", json={
            "source_text": "Program sintetis QA sambungan AI.", "in_scope_rules": [{"asset_alias": "portal",
                "path_template": "/api/attachments/{id}", "methods": ["GET", "DELETE"], "capabilities": ["BAC"]}]})
        assert draft.status_code == 201
        response = await client.post(f"/api/programs/{program}/scope-drafts/{draft.json()['scope_version_id']}/activate")
        assert response.status_code == 200


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, required=True)
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        raise ValueError("Invalid QA port")
    password = json.loads(sys.stdin.readline())["password"]
    with TemporaryDirectory(prefix="valvuln-ai-bridge-") as temporary:
        app = create_app(Settings(_env_file=None, data_dir=Path(temporary), dispatcher_enabled=False,
                                  min_free_bytes=0, public_origin=f"http://127.0.0.1:{args.port}"))
        program = asyncio.run(seed(app.state.db, password))
        asyncio.run(setup(app, program, password))
        transport = QAExtraction()
        app.state.text_triage.transport = transport
        async def deny(*args, **kwargs):
            raise AssertionError("QA forbids real provider and target HTTP")
        httpx.AsyncHTTPTransport.handle_async_request = deny
        server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=args.port, log_level="warning", access_log=False))
        def control():
            for line in sys.stdin:
                if line.strip() == "stop": break
            server.should_exit = True
        Thread(target=control, daemon=True).start()
        server.run()
        final = asyncio.run(counts(app.state.db))
    print("QA_FINAL " + json.dumps({"counts": final, "mock_dispatches": transport.calls,
        "real_provider_requests": 0, "target_requests": 0, "temporary_storage_removed": True}), flush=True)


if __name__ == "__main__":
    main()
