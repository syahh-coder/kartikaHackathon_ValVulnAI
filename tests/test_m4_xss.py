"""Product workflow tests with a simulated browser transport; Docker smoke proves Chromium."""
import asyncio
import base64
import hashlib
import json
import time
from contextlib import asynccontextmanager

import pytest

from app.agent.verifier import AssessmentProposal, validate_assessment
from app.agent.xss import verify
from app.common import AppError, uid
from app.m2_operator import execute
from app.storage.db import one
from boundary.browser import BrowserCapture, MarkerEvent
from boundary.contracts import BrowserObservation, canonical
from test_browser_contracts import PNG
from test_m3_bac import runtime, start


CLAIM = {"asset_alias": "portal", "path": "/notifications/preview", "method": "GET", "category": "XSS",
         "account_aliases": ["requester-a", "requester-b"], "primary_claim": "Fixture marker mengeksekusi JavaScript pada pratinjau"}


class SimulatedBrowser:
    def __init__(self, condition="vulnerable", failure=False, waiting=False):
        self.condition, self.failure, self.waiting = condition, failure, waiting
        self.calls = 0
        self.started = asyncio.Event()

    async def execute(self, envelope, fingerprint, boot):
        self.calls += 1
        args = envelope.validated_arguments
        if self.waiting and self.calls == 2:
            self.started.set()
            await asyncio.Event().wait()
        marker = args.fixture == "marker-v1" and self.condition == "vulnerable"
        capture = BrowserCapture(fixture=args.fixture, nonce=args.nonce, browser_version="simulated-unit-only",
            js_control=True, initial_storage_empty=True, payload_visible_as_text=not marker, screenshot_base64=PNG,
            screenshot_sha256=hashlib.sha256(base64.b64decode(PNG)).hexdigest(),
            marker_events=[MarkerEvent(nonce=args.nonce, origin="http://lab:8001", path=args.relative_path, frame="main")] if marker else [])
        body = capture.model_dump_json()
        fail = self.failure and self.calls == 2
        return BrowserObservation(run_id=envelope.run_id, action_id=envelope.action_id, action_seq=envelope.action_seq,
            envelope_hash=fingerprint, target_snapshot_id=envelope.target_snapshot_id, boot_id=boot,
            status="FAILED" if fail else "OK", error_code="BROWSER_TIMEOUT" if fail else None, http_status=200,
            actor_alias=args.account_alias, method=args.method, relative_path=args.relative_path, body=body,
            body_sha256=hashlib.sha256(body.encode()).hexdigest(), request_attempts=2, responses_received=2, captured_at=time.time())


@asynccontextmanager
async def browser_runtime(env, tmp_path, monkeypatch, **kwargs):
    app, p, a, b, admin = env
    tool = SimulatedBrowser(**kwargs)
    async with runtime(env, tmp_path, monkeypatch, tool_factory=lambda _: tool) as (_, worker, handoff):
        await execute("register_browser", {}, app.state.db, app.state.config, handoff)
        yield tool, worker


@pytest.mark.parametrize("condition,verdict", [("vulnerable", "CONFIRMED"), ("fixed", "REFUTED")])
async def test_xss_product_review_publication_and_forgery(env, tmp_path, monkeypatch, condition, verdict):
    app, p, a, b, admin = env
    async with browser_runtime(env, tmp_path, monkeypatch, condition=condition) as (tool, worker):
        _, rid = await start(a, p, CLAIM)
        await app.state.workflow.tick()
        private = (await admin.get(f"/api/runs/{rid}")).json()
        assert private["process_status"] == "COMPLETED", private
        assert private["validation_kind"] == "XSS"
        assessment = private["assessment"]["system_verified"]
        assert assessment["verdict"] == verdict
        assert private["counters"]["target_requests"] == 8
        assert private["counters"]["browser_actions"] == 20
        assert private["counters"]["model_calls"] == 1
        assert tool.calls == 4 and len(private["evidence"]) == 4
        assert {e["kind"] for e in private["evidence"]} == {"BROWSER_PROBE"}
        assert (await a.get(f"/api/runs/{rid}/export")).json()["assessment"] is None
        assert (await b.get(f"/api/runs/{rid}/export")).status_code == 404
        eid = private["evidence"][0]["evidence_id"]
        assert (await a.get(f"/api/evidence/{eid}")).status_code == 404
        assert (await admin.get(f"/api/evidence/{eid}")).status_code == 200
        assert (await admin.post(f"/api/runs/{rid}/publish")).status_code == 409
        assert (await a.post(f"/api/runs/{rid}/review", json={"reviewer_note": "x"})).status_code == 403
        note = "private <img src=x onerror=alert(1)>"
        assert (await admin.post(f"/api/runs/{rid}/review", json={"reviewer_note": note})).status_code == 200
        assert (await admin.post(f"/api/runs/{rid}/publish")).status_code == 200
        public = (await a.get(f"/api/runs/{rid}/export")).json()
        assert public["assessment"]["verdict"] == verdict
        summary = public["assessment"]["summary"]
        assert "browser lab aktual" in summary and "fixture" in summary and "dua akun" in summary
        for secret in (note, "screenshot_base64", "requester-a", "raw_model", "evidence_id", "pemilik kehilangan"):
            assert secret not in json.dumps(public)
        assert (await admin.get(f"/api/runs/{rid}")).json()["assessment"]["raw_model"] == private["assessment"]["raw_model"]
        assert (await admin.post(f"/api/runs/{rid}/review", json={"reviewer_note": "Ulang", "analyst_override": "INCONCLUSIVE"})).status_code == 200
        assert (await a.get(f"/api/runs/{rid}")).json()["assessment"] is None
        # Mutate one binding at a time, including internally consistent forged capture hashes.
        async with app.state.db.transaction() as conn:
            row = await one(conn, "SELECT * FROM handoff_actions WHERE run_id=? AND action_seq=2", (rid,))
            original = json.loads(row["observation_json"])
            for field, value in (("run_id", uid()), ("boot_id", uid()), ("actor_alias", "requester-b"),
                                 ("target_snapshot_id", uid()), ("action_seq", 1), ("truncated", True), ("request_attempts", 1), ("captured_at", 0)):
                await conn.execute("SAVEPOINT tamper")
                doc = original | {field: value}
                await conn.execute("UPDATE handoff_actions SET observation_json=? WHERE action_id=?", (json.dumps(doc), row["action_id"]))
                await conn.execute("UPDATE evidence SET sha256=? WHERE action_id=?", (hashlib.sha256(canonical(doc)).hexdigest(), row["action_id"]))
                assert (await verify(conn, rid))["verdict"] == "INCONCLUSIVE", field
                await conn.execute("ROLLBACK TO tamper"); await conn.execute("RELEASE tamper")
            for sql, params in (
                ("UPDATE actions SET arguments_json='{}' WHERE action_id=?", (row["action_id"],)),
                ("UPDATE evidence SET provenance_json='{}' WHERE action_id=?", (row["action_id"],)),
                ("UPDATE evidence SET sha256=? WHERE action_id=?", ("0"*64, row["action_id"])),
                ("DELETE FROM evidence WHERE action_id=?", (row["action_id"],))):
                await conn.execute("SAVEPOINT tamper")
                await conn.execute(sql, params)
                assert (await verify(conn, rid))["verdict"] == "INCONCLUSIVE"
                await conn.execute("ROLLBACK TO tamper"); await conn.execute("RELEASE tamper")
            doc = dict(original); cap = json.loads(doc["body"]); cap["nonce"] = uid()
            for event in cap["marker_events"]: event["nonce"] = cap["nonce"]
            doc["body"] = json.dumps(cap); doc["body_sha256"] = hashlib.sha256(doc["body"].encode()).hexdigest()
            await conn.execute("UPDATE handoff_actions SET observation_json=? WHERE action_id=?", (json.dumps(doc), row["action_id"]))
            await conn.execute("UPDATE evidence SET sha256=? WHERE action_id=?", (hashlib.sha256(canonical(doc)).hexdigest(), row["action_id"]))
            assert (await verify(conn, rid))["verdict"] == "INCONCLUSIVE"
            with pytest.raises(AppError, match="Dampak/kontrol"):
                await validate_assessment(conn, rid, AssessmentProposal(claim_id=private["assessment"]["claim_id"], **assessment))


@pytest.mark.parametrize("change,status", [({"path": "/not-allowed"}, "OUT_OF_SCOPE"),
    ({"path": None}, "NEEDS_INFO"), ({"method": "DELETE"}, "OUT_OF_SCOPE"),
    ({"control_path": "/notifications/preview"}, "UNSUPPORTED"), ({"claim_count": 2}, "NEEDS_INFO")])
async def test_xss_gate_no_transport(env, tmp_path, monkeypatch, change, status):
    app, p, a, b, admin = env
    async with browser_runtime(env, tmp_path, monkeypatch) as (tool, _):
        _, rid = await start(a, p, CLAIM | change)
        await app.state.workflow.tick()
        result = (await a.get(f"/api/runs/{rid}")).json()
        assert result["process_status"] == status
        assert tool.calls == 0 and result["counters"]["target_requests"] == 0


async def test_xss_timeout_is_failure_without_refutation(env, tmp_path, monkeypatch):
    app, p, a, b, admin = env
    async with browser_runtime(env, tmp_path, monkeypatch, failure=True) as (tool, _):
        _, rid = await start(a, p, CLAIM)
        await app.state.workflow.tick()
        result = (await admin.get(f"/api/runs/{rid}")).json()
        assert result["process_status"] == "FAILED" and result["error_code"] == "BROWSER_TIMEOUT"
        assert result["assessment"] is None and len(result["evidence"]) == 2 and tool.calls == 2


@pytest.mark.parametrize("stop", ["cancel", "scope", "membership"])
async def test_xss_stop_preserves_trace_and_prevents_next_account(env, tmp_path, monkeypatch, stop):
    app, p, a, b, admin = env
    async with browser_runtime(env, tmp_path, monkeypatch, waiting=True) as (tool, worker):
        _, rid = await start(a, p, CLAIM)
        task = asyncio.create_task(app.state.workflow.tick())
        try:
            await asyncio.wait_for(tool.started.wait(), 15)
            if stop == "cancel":
                assert (await a.post(f"/api/runs/{rid}/cancel")).status_code == 200
            else:
                async with app.state.db.transaction() as conn:
                    if stop == "scope":
                        await conn.execute("UPDATE programs SET authorization_epoch=authorization_epoch+1 WHERE program_id=?", (p,))
                    else:
                        await conn.execute("UPDATE memberships SET enabled=0 WHERE user_id=(SELECT owner_user_id FROM runs WHERE run_id=?) AND program_id=?", (rid,p))
            await asyncio.wait_for(task, 5)
            result = (await admin.get(f"/api/runs/{rid}")).json()
            assert result["process_status"] == ("CANCELLED" if stop == "cancel" else "FAILED")
            assert result["assessment"] is None and len(result["evidence"]) == 1
            assert tool.calls == 2
            async with app.state.db.connect() as conn:
                assert (await one(conn, "SELECT dirty FROM target_bindings WHERE target_id='portal-lab'"))[0]
        finally:
            if not task.done():
                task.cancel()
                await asyncio.gather(task, return_exceptions=True)
