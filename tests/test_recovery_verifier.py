import time

import pytest

from app.agent.verifier import AssessmentProposal, validate_assessment
from app.common import AppError, uid
from app.storage.db import one
from conftest import activate, report_for
from test_workflow import start


async def test_lease_loss_stops_and_does_not_replay(env):
    app, p, a, _, admin = env
    await activate(admin, p)
    _, rid, rev = await report_for(a, p)
    run_id = (await start(a, rid, rev)).json()["run_id"]
    await app.state.workflow.lease_next()
    async with app.state.db.transaction() as conn:
        await conn.execute("UPDATE runs SET lease_expires_at=? WHERE run_id=?", (time.time()-1, run_id))
    await app.state.workflow.tick()
    result = (await a.get(f"/api/runs/{run_id}")).json()
    assert result["process_status"]=="FAILED" and result["error_code"]=="WORKER_LOST"
    assert result["assessment"] is None
    async with app.state.db.connect() as conn:
        assert (await one(conn, "SELECT count(*) FROM provider_attempts"))[0]==0


async def test_dirty_target_blocks_new_lease(env):
    app, p, a, _, admin = env
    await activate(admin, p)
    _, rid, rev = await report_for(a, p)
    run_id = (await start(a, rid, rev)).json()["run_id"]
    async with app.state.db.transaction() as conn:
        await conn.execute("UPDATE target_bindings SET dirty=1")
    await app.state.workflow.tick()
    result = (await a.get(f"/api/runs/{run_id}")).json()
    assert result["error_code"]=="TARGET_DIRTY" and result["assessment"] is None


async def test_active_timeout_does_not_refute(env):
    app, p, a, _, admin = env
    await activate(admin, p)
    _, rid, rev = await report_for(a, p)
    run_id = (await start(a, rid, rev)).json()["run_id"]
    await app.state.workflow.lease_next()
    async with app.state.db.transaction() as conn:
        await conn.execute("UPDATE runs SET started_at=? WHERE run_id=?", (time.time()-181, run_id))
    from app.providers.contracts import ProviderFailure
    with pytest.raises(ProviderFailure):
        await app.state.workflow.transition(run_id, "PLANNED")
    result = (await a.get(f"/api/runs/{run_id}")).json()
    assert result["error_code"]=="RUN_TIMEOUT" and result["assessment"] is None


async def test_assessment_rejects_fake_evidence_and_claims(env):
    app, p, a, b, admin = env
    await activate(admin, p)
    _, rid, rev = await report_for(a, p)
    run_id = (await start(a, rid, rev)).json()["run_id"]
    await app.state.workflow.tick()
    async with app.state.db.connect() as conn:
        claim = (await one(conn, "SELECT primary_claim_id FROM runs WHERE run_id=?", (run_id,)))[0]
        eid = (await one(conn, "SELECT evidence_id FROM evidence WHERE run_id=?", (run_id,)))[0]
        data = {"claim_id": claim, "verdict": "INCONCLUSIVE", "reasoning": "No impact evidence", "next_action": "M2"}
        for override in ({"claim_id": uid()}, {"supporting_evidence_ids": [uid()]},
                         {"verdict": "CONFIRMED", "supporting_evidence_ids": [eid], "controls_performed": ["fabricated"]},
                         {"verdict": "REFUTED", "contradicting_evidence_ids": [eid]}):
            with pytest.raises(AppError):
                await validate_assessment(conn, run_id, AssessmentProposal(**(data | override)))
        assert (await validate_assessment(conn, run_id, AssessmentProposal(**data)))["verdict"]=="INCONCLUSIVE"
