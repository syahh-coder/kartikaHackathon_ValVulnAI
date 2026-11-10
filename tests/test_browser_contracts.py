import base64
import hashlib
import json
import time
from uuid import uuid4

import httpx
import pytest
from pydantic import ValidationError

from app.agent.xss import verify_pair
from app.common import AppError
from app.m2_operator import execute
from app.storage.db import one
from app.transport import Handoff
from boundary.browser import BrowserCapture, MarkerEvent, allowed_browser_url
from boundary.contracts import ActionEnvelope, BrowserArguments, BrowserObservation, canonical, signed, verified
from boundary.files import read_json, write_json
from lab.main import create_app
from lab.maintenance import reset
from worker.service import Worker

PNG = base64.b64encode(b"\x89PNG\r\n\x1a\nsynthetic-unit-fixture").decode()


def captures():
    common = dict(run_id=uuid4(), target_snapshot_id=uuid4(), boot_id=uuid4(), envelope_hash="a"*64,
        status="OK", http_status=200, actor_alias="requester-a", method="GET", relative_path="/notifications/preview",
        request_attempts=2, responses_received=2, captured_at=time.time())
    result = []
    for seq, fixture in enumerate(("inert-v1", "marker-v1"), 1):
        nonce = uuid4()
        capture = BrowserCapture(fixture=fixture, nonce=nonce, browser_version="unit-fixture", js_control=True, initial_storage_empty=True,
            payload_visible_as_text=seq==1, screenshot_base64=PNG,
            screenshot_sha256=hashlib.sha256(base64.b64decode(PNG)).hexdigest(),
            marker_events=[] if seq==1 else [MarkerEvent(nonce=nonce, origin="http://lab:8001", path="/notifications/preview", frame="main")])
        body=capture.model_dump_json()
        result.append(BrowserObservation(**common, action_id=uuid4(), action_seq=seq,
            body=body, body_sha256=hashlib.sha256(body.encode()).hexdigest()).model_dump(mode="json"))
    return result


@pytest.mark.parametrize("change", [{"script":"alert(1)"}, {"fixture":"custom"},
    {"relative_path":"http://169.254.169.254/latest"}, {"account_alias":"admin"},
    {"method":"POST"}, {"nonce":"from-report"}])
def test_no_arbitrary_script_identity_route_or_fixture(change):
    with pytest.raises(ValidationError):
        BrowserArguments(**(dict(account_alias="requester-a",fixture="marker-v1",nonce=str(uuid4()))|change))


@pytest.mark.parametrize("url", ["http://lab:8001/api/health", "http://lab:8001/notifications/preview?next=x",
    "http://lab:8002/notifications/preview", "http://user:pass@lab:8001/notifications/preview",
    "file:///run/secrets/job_key", "data:text/html,<script></script>", "http://169.254.169.254/latest",
    "http://host.docker.internal:8000/", "https://lab:8001/notifications/preview"])
def test_browser_network_default_deny(url):
    args=BrowserArguments(account_alias="requester-a",fixture="inert-v1",nonce=uuid4())
    assert not allowed_browser_url(url,args)
    assert allowed_browser_url("http://lab:8001/notifications/preview#fixture",args)


def test_execution_requires_controls_and_origin_bound_fresh_event():
    control,probe=captures()
    assert verify_pair(control,probe)=="CONFIRMED"
    for change in ({"run_id":str(uuid4())}, {"actor_alias":"requester-b"}, {"truncated":True},
                   {"status":"FAILED","error_code":"BROWSER_TIMEOUT"}):
        assert verify_pair(control,probe|change)=="INCONCLUSIVE"
    body=json.loads(probe["body"])
    # Merely reflecting the nonce, without a callback or a text sink control, is no refutation.
    body["marker_events"]=[]
    body["dom_excerpt"]="untrusted text mentioning "+body["nonce"]
    def update(value):
        text=json.dumps(value)
        return probe|{"body":text,"body_sha256":hashlib.sha256(text.encode()).hexdigest()}
    assert verify_pair(control,update(body))=="INCONCLUSIVE"
    body["payload_visible_as_text"]=True
    assert verify_pair(control,update(body))=="REFUTED"
    body["marker_events"]=[{"nonce":str(uuid4()),"origin":"http://lab:8001","path":"/notifications/preview","frame":"main"}]
    assert verify_pair(control,update(body))=="INCONCLUSIVE"
    body["marker_events"][0]["nonce"]=body["nonce"]
    body["marker_events"][0]["origin"]="http://other.invalid"
    assert verify_pair(control,update(body))=="INCONCLUSIVE"
    body=json.loads(probe["body"])
    body["screenshot_sha256"]="0"*64
    assert verify_pair(control,update(body))=="INCONCLUSIVE"
    body["screenshot_base64"],body["screenshot_sha256"]="",""
    assert verify_pair(control,update(body))=="INCONCLUSIVE"
    with pytest.raises(ValidationError):
        BrowserObservation.model_validate(probe|{"request_attempts":3,"responses_received":3})


@pytest.mark.parametrize("condition,sink",[("vulnerable","innerHTML"),("fixed","textContent")])
async def test_lab_preview_auth_and_evaluator_sink(tmp_path,condition,sink):
    accounts={a:{"password":"synthetic-browser-only"} for a in ("requester-a","requester-b")}
    await reset(tmp_path/"lab.db",accounts,"fixed",xss_condition=condition)
    lab=create_app(tmp_path/"lab.db")
    async with lab.router.lifespan_context(lab):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=lab),base_url="http://lab:8001",headers={"Origin":"http://lab:8001"}) as client:
            assert (await client.get('/notifications/preview')).status_code==401
            assert (await client.post('/api/auth/login',json={"login_name":"requester-a","password":accounts["requester-a"]["password"]})).status_code==200
            page=await client.get('/notifications/preview')
            assert page.status_code==200 and "preview."+sink in page.text
            assert "vulnerable" not in page.text and "delete_owner_check" not in page.text
            assert (await client.post('/notifications/preview/reset')).status_code==404


async def test_browser_handoff_policy_provenance_and_private_capture(env,tmp_path):
    app,p,a,b,admin=env
    inbox,outbox=tmp_path/'inbox',tmp_path/'outbox'
    inbox.mkdir();outbox.mkdir()
    key=b'unit-browser-key-material-32byte'
    boot,snapshot=str(uuid4()),str(uuid4())
    def heartbeat():
        write_json(outbox,'heartbeat.json',signed(dict(boot_id=boot,snapshot_id=snapshot,captured_at=time.time(),status='IDLE',dirty=False,dirty_run_id=None,active_run_id=None),key))
    heartbeat()
    h=Handoff(app.state.db,app.state.config,inbox,outbox,key)
    async with app.state.db.transaction() as conn:
        await conn.execute('UPDATE target_bindings SET ready=1,snapshot_id=?',(snapshot,))
    await execute('register_browser',{},app.state.db,app.state.config,h)
    run=await execute('begin_browser',{},app.state.db,app.state.config,h)
    rid=run['run_id']
    args=BrowserArguments(account_alias='requester-a',fixture='inert-v1',nonce=uuid4())
    aid=await h.issue(rid,args)
    async with app.state.db.connect() as conn:
        row=await one(conn,'SELECT * FROM handoff_actions WHERE action_id=?',(aid,))
    control,_=captures()
    cap=json.loads(control['body']);cap['nonce']=str(args.nonce)
    body=json.dumps(cap)
    obs=control|dict(run_id=rid,action_id=aid,boot_id=boot,target_snapshot_id=snapshot,envelope_hash=row['envelope_hash'],
        body=body,body_sha256=hashlib.sha256(body.encode()).hexdigest(),captured_at=time.time())
    mismatch=dict(obs);bad=json.loads(body);bad['nonce']=str(uuid4());mismatch['body']=json.dumps(bad)
    mismatch['body_sha256']=hashlib.sha256(mismatch['body'].encode()).hexdigest()
    with pytest.raises(AppError): await h.import_result(rid,aid,signed(mismatch,key))
    await h.import_result(rid,aid,signed(obs,key))
    async with app.state.db.connect() as conn:
        evidence=await one(conn,'SELECT * FROM evidence WHERE action_id=?',(aid,))
        assert evidence['kind']=='BROWSER_PROBE' and evidence['visibility']=='INTERNAL'
        assert json.loads(evidence['provenance_json'])['source']=='worker_browser'
        counters=json.loads((await one(conn,'SELECT counters_json FROM runs WHERE run_id=?',(rid,)))[0])
        assert counters['target_requests']==2 and counters['browser_actions']==5
    assert (await a.get('/api/evidence/'+evidence['evidence_id'])).status_code==404
    assert (await admin.get('/api/evidence/'+evidence['evidence_id'])).status_code==200


async def test_browser_crash_journal_does_not_replay(tmp_path):
    import asyncio
    inbox,outbox=tmp_path/'inbox',tmp_path/'outbox'
    inbox.mkdir();outbox.mkdir()
    key=b'unit-browser-key-material-32byte'
    now=time.time()
    envelope=ActionEnvelope(run_id=uuid4(),action_id=uuid4(),action_seq=1,program_id=uuid4(),scope_version_id=uuid4(),
        authorization_epoch=1,target_snapshot_id=uuid4(),tool_name='browser_probe',issued_at=now,expires_at=now+30,
        network_remaining=40,artifact_remaining=16777216,
        allowed_rules=[{'path_template':'/notifications/preview','methods':['GET']}],
        validated_arguments=BrowserArguments(account_alias='requester-a',fixture='marker-v1',nonce=uuid4()))
    class WaitingTool:
        calls=0
        async def execute(self,*args):
            self.calls+=1
            await asyncio.sleep(60)
    tool=WaitingTool()
    worker=Worker(inbox,outbox,key,{},tool)
    worker.state.update(snapshot_id=str(envelope.target_snapshot_id),dirty=False)
    filename=str(envelope.action_id)+'.job.json'
    write_json(inbox,filename,signed(envelope.model_dump(mode='json'),key))
    await worker.accept(inbox/filename)
    await asyncio.sleep(0)
    assert tool.calls==1
    worker.task.cancel()
    await asyncio.gather(worker.task,return_exceptions=True)
    recovered=Worker(inbox,outbox,key,{},tool)
    recovered.recover()
    result=verified(read_json(outbox,str(envelope.action_id)+'.result.json',2*1048576),key)
    assert result['tool_name']=='browser_probe' and result['status']=='ACTION_OUTCOME_UNKNOWN'
    assert recovered.state['dirty'] and recovered.state['dirty_run_id'] is None
    # An identical delivery re-publishes unknown, while a new action is dirty-blocked.
    await recovered.accept(inbox/filename)
    assert recovered.task is None and tool.calls==1
    following=envelope.model_copy(update={'action_id':uuid4(),'action_seq':2})
    new_name=str(following.action_id)+'.job.json'
    write_json(inbox,new_name,signed(following.model_dump(mode='json'),key))
    with pytest.raises(ValueError,match='TARGET_DIRTY'):
        await recovered.accept(inbox/new_name)
    assert tool.calls==1
