"""Host uses real lab HTTP in-process and simulated browser; Docker proves execution."""
import asyncio
import base64
from contextlib import asynccontextmanager
import hashlib
import json
import time
from uuid import uuid4

import httpx
import pytest
from pydantic import ValidationError

from app.agent import upload
from app.common import AppError
from app.m2_operator import execute
from app.storage.db import one
from boundary.browser import BrowserCapture, MarkerEvent
from boundary.contracts import ActionEnvelope, BrowserArguments, UploadArguments, UploadObservation, BrowserObservation, canonical
from boundary.uploads import CONTENT, CONTENT_SHA256, filename
from lab.main import create_app
from lab.maintenance import reset
from test_lab_bac import ACCOUNTS, login
from test_m3_bac import runtime, start
from test_browser_contracts import PNG
from worker.upload_tool import UploadTool

RID = "10000000-0000-4000-8000-000000000001"
CLAIM = {"asset_alias":"portal", "path":f"/requests/{RID}/attachments", "method":"GET", "category":"UPLOAD",
    "account_aliases":["requester-a","requester-b"], "primary_claim":"Nama fixture upload mengeksekusi marker pada daftar"}


def body(rid, name="fixture.txt", data=CONTENT, media="text/plain"):
    return {"request_id":rid,"filename":name,"media_type":media,"content_base64":base64.b64encode(data).decode()}


@pytest.mark.parametrize("point", ("UP-01","UP-02","UP-03","UP-04"))
@pytest.mark.parametrize("condition", ("vulnerable","fixed"))
async def test_lab_upload_modes_content_ownership_and_controls(tmp_path, point, condition):
    path = tmp_path/'lab.sqlite3'
    seed = await reset(path,ACCOUNTS,"fixed",upload_point=point,upload_condition=condition)
    a_id, b_id = [seed['objects'][x]['request_id'] for x in ACCOUNTS]
    app = create_app(path)
    async with app.router.lifespan_context(app):
        a,b = await login(app,'requester-a'), await login(app,'requester-b')
        try:
            payload = b'<svg xmlns="http://www.w3.org/2000/svg" onload="void(0)"/>' if point=='UP-01' else b'<script>void(0)</script>'
            media='image/svg+xml' if point=='UP-01' else 'text/html'
            name=filename('marker-v1',uuid4())
            value=(await a.post('/api/attachments',json=body(a_id,name,payload,media))).json()
            uid=value['upload_id']
            download=await a.get(f'/attachments/{uid}/download')
            assert download.content==payload and download.headers['content-disposition'].startswith('attachment;')
            assert download.headers['content-type']=='application/octet-stream'
            assert (await b.get(f'/attachments/{uid}/download')).status_code==404
            assert (await b.post('/api/attachments',json=body(a_id))).status_code==404
            if point in {'UP-01','UP-02'}:
                route=f'/attachments/{uid}/preview' if point=='UP-01' else f'/documents/{uid}/preview'
                page=await a.get(route)
                assert page.status_code==200
                assert page.content==payload if condition=='vulnerable' else b'&lt;' in page.content
            if point=='UP-03':
                original=(await b.post('/api/attachments',json=body(b_id,'same.txt',b'B original'))).json()['upload_id']
                assert (await b.get(f'/attachments/{original}/download')).content==b'B original'
                await a.post('/api/attachments',json=body(a_id,'same.txt',b'A replacement'))
                assert (await b.get(f'/attachments/{original}/download')).content==(b'A replacement' if condition=='vulnerable' else b'B original')
            if point=='UP-04':
                page=await b.get(f'/requests/{a_id}/attachments')
                assert (name if condition=='vulnerable' else '&lt;svg') in page.text
                assert '&lt;svg' in (await b.get(f'/requests/{a_id}/attachment-labels')).text
                assert (await a.get(f'/requests/{b_id}/attachments')).status_code==404
        finally:
            await a.aclose(); await b.aclose()


async def test_upload_rejects_bad_inputs_and_csrf(tmp_path):
    seed=await reset(tmp_path/'lab.db',ACCOUNTS,'fixed')
    app=create_app(tmp_path/'lab.db')
    rid=seed['objects']['requester-a']['request_id']
    async with app.router.lifespan_context(app):
        a=await login(app,'requester-a')
        try:
            for change in ({'filename':'../x'}, {'filename':'x\\y'}, {'filename':'x\r\ny'}, {'content_base64':'%%%'} ,
                           {'media_type':'application/x-executable'}, {'arbitrary_script':'bad'}, {'filename':'x'*257}):
                assert (await a.post('/api/attachments',json=body(rid)|change)).status_code==422
            assert (await a.post('/api/attachments',json=body(rid,data=b'x'*1025))).status_code==413
            assert (await a.post('/api/attachments',json=body(rid),headers={'X-CSRF-Token':'bad'})).status_code==403
            assert (await a.post('/api/attachments',json=body(rid),headers={'Origin':'http://evil.invalid'})).status_code==403
            assert (await a.post(f'/api/requests/{uuid4()}/attachments',json=body(rid))).status_code==422
        finally: await a.aclose()


@pytest.mark.parametrize('change', ({'filename':'from-report'}, {'content_base64':'anything'}, {'nonce':'from-report'},
    {'account_alias':'requester-b'}, {'method':'DELETE'}, {'relative_path':'http://169.254.169.254/'},
    {'relative_path':'/api/attachments'}, {'fixture':'custom'}))
def test_upload_tool_rejects_free_files_scripts_and_destinations(change):
    with pytest.raises(ValidationError):
        UploadArguments(**({'relative_path':f'/api/requests/{RID}/attachments','fixture':'marker-v1','nonce':uuid4()}|change))


def envelope(**changes):
    args=UploadArguments(relative_path=f'/api/requests/{RID}/attachments',fixture='marker-v1',nonce=uuid4())
    now=time.time()
    return ActionEnvelope(**(dict(run_id=uuid4(),action_id=uuid4(),action_seq=1,program_id=uuid4(),scope_version_id=uuid4(),authorization_epoch=1,
        target_snapshot_id=uuid4(),tool_name='upload_fixture',validated_arguments=args,
        allowed_rules=[{'path_template':'/api/requests/{id}/attachments','methods':['POST']}],issued_at=now,expires_at=now+10,
        network_remaining=40,artifact_remaining=16777216)|changes))


async def test_upload_tool_bounds_scope_redirect_and_redaction():
    e=envelope()
    def transport(request):
        assert request.url.host=='172.30.74.3' and request.headers['host']=='lab:8001'
        if request.url.path=='/api/auth/login':
            return httpx.Response(200,json={'account_alias':'requester-a','csrf_token':'secret-csrf'},headers={'set-cookie':'lab_session=secret-cookie; Path=/'})
        data=json.loads(request.content)
        assert data['filename']==filename(e.validated_arguments.fixture,e.validated_arguments.nonce)
        return httpx.Response(200,json={'upload_id':str(uuid4()),'request_id':RID,'filename':data['filename'],'media_type':'text/plain',
            'content_sha256':CONTENT_SHA256,'size':len(CONTENT),'unexpected':'secret-cookie'})
    result=await UploadTool(ACCOUNTS,httpx.MockTransport(transport)).execute(e,'a'*64,str(uuid4()))
    assert result.status=='OK' and result.request_attempts==2 and result.responses_received==2
    assert all(secret not in result.body for secret in ['secret-csrf','secret-cookie',ACCOUNTS['requester-a']['password']])
    def deny(request): raise AssertionError('No transport permitted')
    for invalid in (envelope(issued_at=1,expires_at=2),envelope(allowed_rules=[{'path_template':'/notifications/preview','methods':['GET']}]),envelope(artifact_remaining=1)):
        result=await UploadTool(ACCOUNTS,httpx.MockTransport(deny)).execute(invalid,'a'*64,str(uuid4()))
        assert result.status=='FAILED' and result.request_attempts==0
    calls=[]
    def redirect(request):
        calls.append(str(request.url))
        return httpx.Response(302,headers={'location':'http://198.51.100.10/'})
    result=await UploadTool(ACCOUNTS,httpx.MockTransport(redirect)).execute(e,'a'*64,str(uuid4()))
    assert result.status=='FAILED' and len(calls)==1


class SimulatedUpload:
    def __init__(self, condition='vulnerable', failure=False, waiting=False):
        self.condition,self.failure,self.waiting=condition,failure,waiting
        self.calls=0
        self.started=asyncio.Event()

    async def execute(self,e,fingerprint,boot):
        self.calls+=1
        args=e.validated_arguments
        if self.waiting and self.calls==2:
            self.started.set(); await asyncio.Event().wait()
        browser=isinstance(args,BrowserArguments)
        if browser:
            marker=args.fixture=='marker-v1' and self.condition=='vulnerable' and args.relative_path.endswith('/attachments')
            cap=BrowserCapture(fixture=args.fixture,nonce=args.nonce,path=args.relative_path,browser_version='simulated-only',js_control=True,
                initial_storage_empty=True,payload_visible_as_text=not marker,screenshot_base64=PNG,screenshot_sha256=hashlib.sha256(base64.b64decode(PNG)).hexdigest(),
                marker_events=[MarkerEvent(nonce=args.nonce,origin='http://lab:8001',path=args.relative_path,frame='main')] if marker else [])
            data=cap.model_dump_json()
        else:
            data=json.dumps({'upload_id':str(uuid4()),'request_id':RID,'filename':filename(args.fixture,args.nonce),'media_type':'text/plain','content_sha256':CONTENT_SHA256,'size':len(CONTENT)})
        fail=self.failure and self.calls==2
        cls=BrowserObservation if browser else UploadObservation
        return cls(run_id=e.run_id,action_id=e.action_id,action_seq=e.action_seq,envelope_hash=fingerprint,target_snapshot_id=e.target_snapshot_id,
            boot_id=boot,status='FAILED' if fail else 'OK',error_code='BROWSER_TIMEOUT' if fail else None,http_status=200,actor_alias=args.account_alias,
            method=args.method,relative_path=args.relative_path,body=data,body_sha256=hashlib.sha256(data.encode()).hexdigest(),request_attempts=2,responses_received=2,captured_at=time.time())


@asynccontextmanager
async def upload_runtime(env,tmp_path,monkeypatch,**kwargs):
    app,*_=env
    tool=SimulatedUpload(**kwargs)
    async with runtime(env,tmp_path,monkeypatch,tool_factory=lambda _:tool) as (_,worker,handoff):
        await execute('register_upload',{},app.state.db,app.state.config,handoff)
        yield tool,worker


@pytest.mark.parametrize('condition,verdict', [('vulnerable','CONFIRMED'),('fixed','REFUTED')])
async def test_upload_product_verdict_controls_publication_and_tamper(env,tmp_path,monkeypatch,condition,verdict):
    app,p,a,b,admin=env
    async with upload_runtime(env,tmp_path,monkeypatch,condition=condition) as (tool,worker):
        _,rid=await start(a,p,CLAIM)
        await app.state.workflow.tick()
        result=(await admin.get(f'/api/runs/{rid}')).json()
        assert result['process_status']=='COMPLETED',result
        assert result['assessment']['system_verified']['verdict']==verdict
        assert tool.calls==5 and len(result['evidence'])==5
        assert result['counters']['target_requests']==10 and result['counters']['browser_actions']==15
        assert (await b.get(f'/api/runs/{rid}/export')).status_code==404
        for item in result['evidence']: assert (await a.get('/api/evidence/'+item['evidence_id'])).status_code==404
        assert (await admin.post(f'/api/runs/{rid}/publish')).status_code==409
        assert (await admin.post(f'/api/runs/{rid}/review',json={'reviewer_note':'private review'})).status_code==200
        assert (await admin.post(f'/api/runs/{rid}/publish')).status_code==200
        exported=(await a.get(f'/api/runs/{rid}/export')).json()
        assert exported['assessment']['verdict']==verdict
        assert 'upload dan browser' in exported['assessment']['summary']
        for secret in ('<svg','private review','requester-a','screenshot_base64','evidence_id'): assert secret not in json.dumps(exported)
        async with app.state.db.transaction() as conn:
            row=await one(conn,'SELECT * FROM handoff_actions WHERE run_id=? AND action_seq=4',(rid,))
            original=json.loads(row['observation_json'])
            for field,value in [('run_id',str(uuid4())),('boot_id',str(uuid4())),('actor_alias','requester-a'),('captured_at',0),('request_attempts',1)]:
                await conn.execute('SAVEPOINT tamper')
                doc=original|{field:value}
                await conn.execute('UPDATE handoff_actions SET observation_json=? WHERE action_id=?',(json.dumps(doc),row['action_id']))
                await conn.execute('UPDATE evidence SET sha256=? WHERE action_id=?',(hashlib.sha256(canonical(doc)).hexdigest(),row['action_id']))
                assert (await upload.verify(conn,rid))['verdict']=='INCONCLUSIVE'
                await conn.execute('ROLLBACK TO tamper');await conn.execute('RELEASE tamper')
            await conn.execute('DELETE FROM evidence WHERE run_id=? AND kind=?',(rid,'UPLOAD_EXCHANGE'))
            assert (await upload.verify(conn,rid))['verdict']=='INCONCLUSIVE'


async def test_upload_timeout_does_not_refute(env,tmp_path,monkeypatch):
    app,p,a,b,admin=env
    async with upload_runtime(env,tmp_path,monkeypatch,failure=True):
        _,rid=await start(a,p,CLAIM)
        await app.state.workflow.tick()
        result=(await admin.get(f'/api/runs/{rid}')).json()
        assert result['process_status']=='FAILED' and result['assessment'] is None


@pytest.mark.parametrize('removed', ('/api/requests/{id}/attachments','/requests/{id}/attachment-labels'))
async def test_upload_scope_requires_post_and_safe_control_before_dispatch(env,tmp_path,monkeypatch,removed):
    app,p,a,b,admin=env
    async with upload_runtime(env,tmp_path,monkeypatch) as (tool,_):
        async with app.state.db.transaction() as conn:
            scope=await one(conn,"SELECT * FROM scope_versions WHERE state='ACTIVE'")
            rules=json.loads(scope['rules_json'])
            rules['in_scope_rules']=[r for r in rules['in_scope_rules'] if r['path_template']!=removed]
        from conftest import activate
        await activate(admin,p,rules)
        _,rid=await start(a,p,CLAIM)
        await app.state.workflow.tick()
        result=(await admin.get(f'/api/runs/{rid}')).json()
        assert result['process_status']=='POLICY_BLOCKED' and tool.calls==0


async def test_upload_cancel_retains_completed_upload_and_stops_next_fixture(env,tmp_path,monkeypatch):
    app,p,a,b,admin=env
    async with upload_runtime(env,tmp_path,monkeypatch,waiting=True) as (tool,worker):
        _,rid=await start(a,p,CLAIM)
        task=asyncio.create_task(app.state.workflow.tick())
        await asyncio.wait_for(tool.started.wait(),10)
        assert (await a.post(f'/api/runs/{rid}/cancel')).status_code==200
        await asyncio.wait_for(task,10)
        result=(await admin.get(f'/api/runs/{rid}')).json()
        assert result['process_status']=='CANCELLED' and result['assessment'] is None
        assert len(result['evidence'])==1 and result['evidence'][0]['kind']=='UPLOAD_EXCHANGE'
        assert tool.calls==2


async def test_upload_crash_recovers_unknown_without_replay(tmp_path):
    from worker.service import Worker
    from boundary.files import read_json,write_json
    from boundary.contracts import verified,signed,observation_from
    inbox,outbox=tmp_path/'inbox',tmp_path/'outbox'
    inbox.mkdir();outbox.mkdir()
    key=b'upload-recovery-unit-key-32-bytes!'
    e=envelope()
    worker=Worker(inbox,outbox,key,ACCOUNTS)
    fingerprint=hashlib.sha256(canonical(e.model_dump(mode='json'))).hexdigest()
    worker.state.update(snapshot_id=str(e.target_snapshot_id),dirty=True,dirty_run_id=str(e.run_id),
        active={'envelope':e.model_dump(mode='json'),'hash':fingerprint})
    worker.save()
    recovered=Worker(inbox,outbox,key,ACCOUNTS)
    recovered.recover()
    result=observation_from(verified(read_json(outbox,str(e.action_id)+'.result.json',2*1048576),key))
    assert result.tool_name=='upload_fixture' and result.status=='ACTION_OUTCOME_UNKNOWN'
    assert recovered.state['dirty'] and recovered.state['dirty_run_id'] is None
    name=str(e.action_id)+'.job.json'
    write_json(inbox,name,signed(e.model_dump(mode='json'),key))
    await recovered.accept(inbox/name)
    assert recovered.task is None
