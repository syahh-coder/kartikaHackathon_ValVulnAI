import hashlib
import json
import time
from uuid import uuid4

import pytest

from app.common import AppError
from app.m2_operator import execute
from app.transport import Handoff
from app.storage.db import one
from boundary.contracts import HttpArguments, Observation, signed
from boundary.files import write_json
from conftest import activate

KEY=b"12345678901234567890123456789012"


@pytest.fixture
async def handoff_env(env,tmp_path):
    app,p,a,b,admin=env
    await activate(admin,p)
    inbox,outbox=tmp_path/"inbox",tmp_path/"outbox"
    inbox.mkdir(); outbox.mkdir()
    boot,snapshot=str(uuid4()),str(uuid4())
    def heartbeat():
        write_json(outbox,"heartbeat.json",signed({"boot_id":boot,"captured_at":time.time(),"status":"IDLE","active_run_id":None,"snapshot_id":snapshot,"dirty":False,"dirty_run_id":None},KEY))
    heartbeat()
    async with app.state.db.transaction() as conn:
        await conn.execute("UPDATE target_bindings SET ready=1,snapshot_id=?",(snapshot,))
    h=Handoff(app.state.db,app.state.config,inbox,outbox,KEY)
    run=await execute("begin",{"path":"/api/attachments/sample"},app.state.db,app.state.config,h)
    yield app,h,run["run_id"],heartbeat


async def test_import_evidence_matches_immutable_outstanding_and_dedup(handoff_env):
    app,h,rid,heartbeat=handoff_env
    aid=await h.issue(rid,HttpArguments(method="GET",relative_path="/api/attachments/sample",account_alias="requester-a"))
    async with app.state.db.connect() as conn:
        row=await one(conn,"SELECT * FROM handoff_actions WHERE action_id=?",(aid,))
        run=await one(conn,"SELECT * FROM runs WHERE run_id=?",(rid,))
    e=json.loads(row["envelope_json"])
    obs=Observation(run_id=rid,action_id=aid,action_seq=1,envelope_hash=row["envelope_hash"],target_snapshot_id=run["target_snapshot_id"],boot_id=run["worker_boot_id"],
                    status="OK",http_status=200,actor_alias="requester-a",method="GET",relative_path="/api/attachments/sample",body="{}",body_sha256=hashlib.sha256(b"{}").hexdigest(),
                    request_attempts=2,responses_received=2,captured_at=time.time())
    for override in ({"run_id":str(uuid4())},{"action_id":str(uuid4())},{"action_seq":2},{"actor_alias":"requester-b"},{"boot_id":str(uuid4())},{"envelope_hash":"f"*64}):
        bad=obs.model_dump(mode="json")|override
        with pytest.raises(AppError): await h.import_result(rid,aid,signed(bad,KEY))
    result=await h.import_result(rid,aid,signed(obs.model_dump(mode="json"),KEY))
    assert result["http_status"]==200
    await h.import_result(rid,aid,signed(obs.model_dump(mode="json"),KEY))
    async with app.state.db.connect() as conn:
        assert (await one(conn,"SELECT count(*) FROM evidence WHERE run_id=?",(rid,)))[0]==1
        assert (await one(conn,"SELECT count(*) FROM provider_attempts WHERE run_id=?",(rid,)))[0]==0


async def test_revocation_no_job_and_dirty_reset_guard(handoff_env):
    app,h,rid,heartbeat=handoff_env
    with pytest.raises(AppError):
        await execute("maintenance_enter",{},app.state.db,app.state.config,h)
    async with app.state.db.transaction() as conn:
        await conn.execute("UPDATE programs SET authorization_epoch=authorization_epoch+1")
    with pytest.raises(AppError):
        await h.issue(rid,HttpArguments(method="DELETE",relative_path="/api/attachments/sample",account_alias="requester-a"))
    assert not list(h.inbox.glob("*.job.json"))
