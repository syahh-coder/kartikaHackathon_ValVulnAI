import asyncio
from contextlib import asynccontextmanager
import hashlib
import json

import httpx
import pytest

from app.agent.bac import verify
from app.common import uid
from app.storage.db import one
from app.transport import Handoff
from boundary.contracts import canonical
from lab.main import create_app
from lab.maintenance import reset
from worker.http_tool import HttpTool
from worker.service import Worker
from conftest import activate, report_for

KEY = b"12345678901234567890123456789012"
ACCOUNTS = {a: {"password": "synthetic-m3-only"} for a in ("requester-a", "requester-b")}


@asynccontextmanager
async def runtime(env, tmp_path, monkeypatch, condition="vulnerable", tool_factory=None):
    app, p, a, b, admin = env
    await activate(admin, p)
    snapshot = await reset(tmp_path/"lab.db", ACCOUNTS, condition)
    lab = create_app(tmp_path/"lab.db")
    inbox, outbox = tmp_path/"inbox", tmp_path/"outbox"
    inbox.mkdir(); outbox.mkdir()
    keyfile = tmp_path/"key"
    keyfile.write_text(KEY.hex())
    app.state.config.transport_key_file = keyfile
    handoff = Handoff(app.state.db, app.state.config, inbox, outbox, KEY)
    monkeypatch.setattr("app.transport.Handoff", lambda *args, **kwargs: handoff)
    async with lab.router.lifespan_context(lab):
        tool = HttpTool(ACCOUNTS, httpx.ASGITransport(app=lab))
        if tool_factory:
            tool = tool_factory(tool)
        worker = Worker(inbox, outbox, KEY, ACCOUNTS, tool)
        worker.state.update(snapshot_id=snapshot["snapshot_id"], dirty=False)
        worker.heartbeat()
        async with app.state.db.transaction() as conn:
            await conn.execute("UPDATE target_bindings SET ready=1,snapshot_id=?", (snapshot["snapshot_id"],))
        task = asyncio.create_task(worker.run())
        try:
            paths = {a: "/api/attachments/"+v["attachment_id"] for a, v in snapshot["objects"].items()}
            claim = {"asset_alias": "portal", "path": paths["requester-b"], "control_path": paths["requester-a"],
                     "account_aliases": ["requester-a", "requester-b"], "method": "DELETE", "category": "BAC",
                     "primary_claim": "Akun penguji menghapus lampiran milik akun lain"}
            yield claim, worker, handoff
        finally:
            worker.stop = True
            await task


async def start(a, p, claim):
    cid, rid, rev = await report_for(a, p, claim)
    response = await a.post(f"/api/reports/{rid}/runs", json={"report_revision_id": rev, "tool_execution_mode": "LAB"},
                            headers={"Idempotency-Key": uid()})
    assert response.status_code == 202, response.text
    return cid, response.json()["run_id"]


@pytest.mark.parametrize("condition,verdict", [("vulnerable", "CONFIRMED"), ("fixed", "REFUTED")])
async def test_end_to_end_evidence_and_role_projection(env, tmp_path, monkeypatch, condition, verdict):
    app, p, a, b, admin = env
    async with runtime(env, tmp_path, monkeypatch, condition) as (claim, worker, handoff):
        cid, rid = await start(a, p, claim)
        await app.state.workflow.tick()
        private = (await admin.get(f"/api/runs/{rid}")).json()
        assert private["process_status"] == "COMPLETED", private
        assert private["assessment"]["system_verified"]["verdict"] == verdict
        assert private["counters"]["target_requests"] == 14
        assert private["counters"]["model_calls"] == 1
        assert len(private["evidence"]) == 7
        assert (await a.get(f"/api/runs/{rid}/export")).json()["assessment"] is None
        assert (await b.get(f"/api/runs/{rid}")).status_code == 404
        assert (await b.get(f"/api/runs/{rid}/export")).status_code == 404
        eid = private["evidence"][0]["evidence_id"]
        assert (await a.get(f"/api/evidence/{eid}")).status_code == 404
        observation = (await admin.get(f"/api/evidence/{eid}")).json()["observation"]
        assert observation["actor_alias"] == "requester-b"
        assert (await a.post(f"/api/runs/{rid}/review", json={"reviewer_note": "no"})).status_code == 403
        assert (await admin.post(f"/api/runs/{rid}/publish")).status_code == 409
        raw = private["assessment"]["raw_model"]
        assert (await admin.post(f"/api/runs/{rid}/review", json={"reviewer_note": "internal-cookie-secret <img src=x>"})).status_code == 200
        assert (await admin.post(f"/api/runs/{rid}/publish")).status_code == 200
        public = (await a.get(f"/api/runs/{rid}/export")).json()
        assert public["assessment"]["verdict"] == verdict
        assert "Bukti tersanitasi. Kontrol:" in public["assessment"]["summary"]
        assert ("pemilik kehilangan akses setelah aksi" if condition == "vulnerable" else
                "objek laporan tetap dapat dibaca pemilik") in public["assessment"]["summary"]
        for secret in ("internal-cookie-secret", "requester-b", "evidence", "raw_model", "target_id"):
            assert secret not in json.dumps(public)
        assert (await admin.get(f"/api/runs/{rid}")).json()["assessment"]["raw_model"] == raw
        assert (await a.get(f"/api/conversations/{cid}")).json()["run_ids"] == [rid]
        # Re-review withdraws publication without changing the raw result.
        assert (await admin.post(f"/api/runs/{rid}/review", json={"reviewer_note": "Perlu pemeriksaan ulang", "analyst_override": "INCONCLUSIVE"})).status_code == 200
        assert (await a.get(f"/api/runs/{rid}/export")).json()["assessment"] is None
        assert (await admin.post(f"/api/runs/{rid}/publish")).status_code == 200
        assert (await a.get(f"/api/runs/{rid}/export")).json()["assessment"]["verdict"] == "INCONCLUSIVE"
        assert (await admin.get(f"/api/runs/{rid}")).json()["assessment"]["raw_model"] == raw
        # A missing/wrong identity or truncated trace cannot sustain a verdict.
        async with app.state.db.transaction() as conn:
            row = await one(conn, "SELECT action_id,observation_json FROM handoff_actions WHERE run_id=? AND action_seq=1", (rid,))
            doc = json.loads(row[1]); doc["truncated"] = True
            await conn.execute("UPDATE handoff_actions SET observation_json=? WHERE action_id=?", (json.dumps(doc), row[0]))
            assert (await verify(conn, rid))["verdict"] == "INCONCLUSIVE"


async def test_unrelated_object_body_does_not_prove_impact(env, tmp_path, monkeypatch):
    app, p, a, b, admin = env
    async with runtime(env, tmp_path, monkeypatch) as (claim, worker, handoff):
        _, rid = await start(a, p, claim)
        await app.state.workflow.tick()
        async with app.state.db.transaction() as conn:
            row = await one(conn, "SELECT action_id,observation_json FROM handoff_actions WHERE run_id=? AND action_seq=6", (rid,))
            doc = json.loads(row[1])
            doc["body"] = json.dumps({"attachment_id": "unrelated-object", "deleted": True})
            doc["body_sha256"] = hashlib.sha256(doc["body"].encode()).hexdigest()
            await conn.execute("UPDATE handoff_actions SET observation_json=? WHERE action_id=?", (json.dumps(doc), row[0]))
            await conn.execute("UPDATE evidence SET sha256=? WHERE action_id=?", (hashlib.sha256(canonical(doc)).hexdigest(), row[0]))
            assert (await verify(conn, rid))["verdict"] == "INCONCLUSIVE"


async def test_worker_timeout_preserves_trace_without_refutation(env, tmp_path, monkeypatch):
    app, p, a, b, admin = env
    class TimeoutTool:
        def __init__(self, real): self.real = real; self.calls = 0
        async def execute(self, *args):
            self.calls += 1
            observation = await self.real.execute(*args)
            if self.calls == 2:
                observation = observation.model_copy(update={"status": "FAILED", "error_code": "NETWORK_TIMEOUT", "http_status": None})
            return observation
    async with runtime(env, tmp_path, monkeypatch, tool_factory=TimeoutTool) as (claim, worker, handoff):
        _, rid = await start(a, p, claim)
        await app.state.workflow.tick()
        result = (await admin.get(f"/api/runs/{rid}")).json()
        assert result["process_status"] == "FAILED" and result["error_code"] == "NETWORK_TIMEOUT"
        assert result["assessment"] is None and len(result["evidence"]) == 2
        assert worker.tool.calls == 2


@pytest.mark.parametrize("change,process", [({"path": None}, "NEEDS_INFO"), ({"asset_alias": "elsewhere"}, "OUT_OF_SCOPE"),
    ({"control_path": None}, "NEEDS_INFO"), ({"category": "XSS"}, "UNSUPPORTED"), ({"method": "GET"}, "UNSUPPORTED"),
    ({"control_path": "/outside/control"}, "UNSUPPORTED"), ({"claim_count": 2}, "NEEDS_INFO")])
async def test_gate_zero_io(env, tmp_path, monkeypatch, change, process):
    app, p, a, b, admin = env
    async with runtime(env, tmp_path, monkeypatch) as (claim, worker, handoff):
        _, rid = await start(a, p, claim | change)
        await app.state.workflow.tick()
        output = (await a.get(f"/api/runs/{rid}")).json()
        assert output["process_status"] == process
        assert output["counters"]["target_requests"] == 0
        assert not worker.state["seen"]


@pytest.mark.parametrize("operation", ["cancel", "scope", "membership"])
async def test_stop_active_io_retains_trace_no_verdict(env, tmp_path, monkeypatch, operation):
    app, p, a, b, admin = env
    dispatched = asyncio.Event()
    class SlowTool:
        def __init__(self, real): self.real = real; self.calls = 0
        async def execute(self, *args):
            self.calls += 1
            if self.calls == 2:
                dispatched.set()
                await asyncio.sleep(30)
            return await self.real.execute(*args)
    async with runtime(env, tmp_path, monkeypatch, tool_factory=SlowTool) as (claim, worker, handoff):
        _, rid = await start(a, p, claim)
        tick = asyncio.create_task(app.state.workflow.tick())
        try:
            # Allow host setup/first-login latency; cancellation itself must still finish in 5s.
            # Production action/run deadlines are unchanged.
            await asyncio.wait_for(dispatched.wait(), 15)
            if operation == "cancel":
                assert (await a.post(f"/api/runs/{rid}/cancel")).status_code == 200
            elif operation == "scope":
                await activate(admin, p)
            else:
                async with app.state.db.transaction() as conn:
                    await conn.execute("UPDATE memberships SET enabled=0 WHERE user_id=(SELECT owner_user_id FROM runs WHERE run_id=?)", (rid,))
            await asyncio.wait_for(tick, 5)
            for _ in range(20):
                if not worker.task: break
                await asyncio.sleep(.1)
            assert worker.tool.calls == 2 and worker.task is None
            async with app.state.db.connect() as conn:
                assert (await one(conn, "SELECT count(*) FROM evidence WHERE run_id=?", (rid,)))[0] == 1
                assert not await one(conn, "SELECT 1 FROM assessments WHERE run_id=?", (rid,))
                assert (await one(conn, "SELECT queue_status FROM runs WHERE run_id=?", (rid,)))[0] != "LEASED"
                assert (await one(conn, "SELECT dirty FROM target_bindings"))[0] == 1
        finally:
            if not tick.done():
                tick.cancel()
            await asyncio.gather(tick, return_exceptions=True)
