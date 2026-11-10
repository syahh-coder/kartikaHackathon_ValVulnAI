import asyncio
import hashlib
import json
import time
from uuid import uuid4

import httpx
import pytest
from pydantic import ValidationError

from boundary.contracts import ActionEnvelope, Control, HttpArguments, Observation, canonical, signed, verified
from boundary.files import read_json, write_json
from lab.main import create_app
from lab.maintenance import reset
from worker.http_tool import HttpTool
from worker.service import Worker

KEY=b"test-key-material-not-a-real-key!"
ACCOUNTS={x:{"password":"synthetic-lab-test-only"} for x in ("requester-a","requester-b")}


def envelope(**kwargs):
    now=time.time()
    data=dict(run_id=str(uuid4()),action_id=str(uuid4()),action_seq=1,program_id=str(uuid4()),scope_version_id=str(uuid4()),
              authorization_epoch=1,target_snapshot_id=str(uuid4()),validated_arguments={"method":"GET","relative_path":"/api/attachments/sample","account_alias":"requester-a"},
              allowed_rules=[{"path_template":"/api/attachments/{id}","methods":["GET","DELETE"]}],issued_at=now,expires_at=now+10,
              network_remaining=40,artifact_remaining=16777216)
    return ActionEnvelope(**(data|kwargs))


@pytest.mark.parametrize("arguments",[
    {"method":"POST"}, {"relative_path":"http://metadata.invalid/"}, {"relative_path":"//lab:8001/a"},
    {"relative_path":"/api/attachments/%252f"}, {"relative_path":"/api/attachments/a?url=x"},
    {"relative_path":"/api/attachments/../reset"}, {"account_alias":"lab-admin"}, {"headers":{"Host":"other"}},
    {"script":"process.exit()"}, {"relative_path":"/api/auth/login"},
])
def test_structured_arguments_reject_routes_identity_and_scripts(arguments):
    with pytest.raises(ValidationError):
        HttpArguments(**({"method":"GET","relative_path":"/api/attachments/sample","account_alias":"requester-a"}|arguments))


def test_hmac_expiry_and_rule_exclusions():
    e=envelope()
    value=e.model_dump(mode="json")
    assert verified(signed(value,KEY),KEY)==value
    tampered=signed(value,KEY)
    tampered["payload"]["authorization_epoch"]=999
    with pytest.raises(ValueError): verified(tampered,KEY)
    with pytest.raises(ValueError): e.authorize(e.expires_at+1)
    with pytest.raises(ValueError):
        envelope(excluded_rules=[{"path_template":"/api/attachments/{id}","methods":["GET"]}]).authorize()


async def test_worker_real_lab_asgi_identity_and_mutation(tmp_path):
    path=tmp_path/"lab.sqlite3"
    seeded=await reset(path,ACCOUNTS,"vulnerable")
    lab=create_app(path)
    async with lab.router.lifespan_context(lab):
        tool=HttpTool(ACCOUNTS,httpx.ASGITransport(app=lab))
        e=envelope(validated_arguments={"method":"DELETE","relative_path":"/api/attachments/"+seeded["objects"]["requester-b"]["attachment_id"],"account_alias":"requester-a"})
        result=await tool.execute(e,"a"*64,str(uuid4()))
        assert result.status=="OK" and result.http_status==200
        assert result.request_attempts==2 and result.responses_received==2
        assert result.actor_alias=="requester-a" and '"deleted":true' in result.body
        assert ACCOUNTS["requester-a"]["password"] not in result.model_dump_json()
        follow=envelope(validated_arguments={"method":"GET","relative_path":e.validated_arguments.relative_path,"account_alias":"requester-b"})
        assert (await tool.execute(follow,"b"*64,str(uuid4()))).http_status==404


async def test_redirect_never_followed_and_secrets_redacted():
    requests=[]
    def transport(request):
        requests.append(request)
        assert request.url.host=="172.30.74.3" and request.headers["host"]=="lab:8001"
        if request.url.path=="/api/auth/login":
            return httpx.Response(200,json={"account_alias":"requester-a","csrf_token":"csrf-secret"},headers={"Set-Cookie":"lab_session=cookie-secret; Path=/"})
        return httpx.Response(302,headers={"Location":"http://169.254.169.254/latest"},stream=httpx.ByteStream(b"cookie-secret csrf-secret synthetic-lab-test-only"))
    result=await HttpTool(ACCOUNTS,httpx.MockTransport(transport)).execute(envelope(),"c"*64,str(uuid4()))
    assert result.error_code=="REDIRECT_BLOCKED" and len(requests)==2
    assert result.body=="[REDACTED] [REDACTED] [REDACTED]"


async def test_worker_dedup_snapshot_and_crash_journal(tmp_path):
    inbox,outbox=tmp_path/"inbox",tmp_path/"outbox"
    inbox.mkdir(); outbox.mkdir()
    class FakeTool:
        calls=0
        async def execute(self,e,fingerprint,boot):
            self.calls+=1
            return Observation(run_id=e.run_id,action_id=e.action_id,action_seq=e.action_seq,envelope_hash=fingerprint,
                               target_snapshot_id=e.target_snapshot_id,boot_id=boot,status="OK",http_status=200,
                               actor_alias=e.validated_arguments.account_alias,method=e.validated_arguments.method,relative_path=e.validated_arguments.relative_path,
                               body="{}",body_sha256=hashlib.sha256(b"{}").hexdigest(),request_attempts=2,responses_received=2,captured_at=time.time())
    tool=FakeTool()
    worker=Worker(inbox,outbox,KEY,ACCOUNTS,tool)
    e=envelope()
    payload=e.model_dump(mode="json")
    name=str(e.action_id)+".job.json"
    write_json(inbox,name,signed(payload,KEY))
    with pytest.raises(ValueError,match="SNAPSHOT_STALE"):
        await worker.accept(inbox/name)
    worker.state.update(snapshot_id=str(e.target_snapshot_id),dirty=False)
    await worker.accept(inbox/name)
    await worker.task; await worker.finish()
    await worker.accept(inbox/name)
    assert tool.calls==1
    # A restart after a known result can republish it, without repeating I/O.
    other=Worker(inbox,outbox,KEY,ACCOUNTS,tool)
    other.recover(); await other.accept(inbox/name)
    assert tool.calls==1
    # A claimed but unfinished action is ambiguous; never replay, even for GET.
    second=envelope(run_id=e.run_id,action_seq=2,target_snapshot_id=e.target_snapshot_id)
    other.state["active"]={"envelope":second.model_dump(mode="json"),"hash":"d"*64}
    other.save()
    after_crash=Worker(inbox,outbox,KEY,ACCOUNTS,tool)
    after_crash.recover()
    recovered=Observation.model_validate(verified(read_json(outbox,str(second.action_id)+".result.json"),KEY))
    assert recovered.status=="ACTION_OUTCOME_UNKNOWN" and after_crash.state["dirty"]
    assert tool.calls==1


def test_partial_oversize_and_symlink_files(tmp_path):
    write_json(tmp_path,"safe.json",{"x":1})
    assert read_json(tmp_path,"safe.json")=={"x":1}
    with pytest.raises(ValueError): read_json(tmp_path,"../safe.json")
    with pytest.raises(ValueError): write_json(tmp_path,"large.json",{"x":"y"*100},10)
    (tmp_path/"broken.json").write_text('{"unfinished":')
    with pytest.raises(ValueError): read_json(tmp_path,"broken.json")
    assert not list(tmp_path.glob("*.partial"))


async def test_cancel_record_remains_effective_after_other_cancel(tmp_path):
    inbox,outbox=tmp_path/"inbox",tmp_path/"outbox"
    inbox.mkdir();outbox.mkdir()
    worker=Worker(inbox,outbox,KEY,ACCOUNTS)
    e=envelope()
    worker.state.update(snapshot_id=str(e.target_snapshot_id),dirty=False)
    for run in (e.run_id,uuid4()):
        now=time.time()
        c=Control(control_id=uuid4(),kind="CANCEL",run_id=run,issued_at=now,expires_at=now+30)
        write_json(inbox,str(c.control_id)+".control.json",signed(c.model_dump(mode="json"),KEY))
    await worker.controls()
    name=str(e.action_id)+".job.json"
    write_json(inbox,name,signed(e.model_dump(mode="json"),KEY))
    with pytest.raises(ValueError,match="RUN_CANCELLED"):
        await worker.accept(inbox/name)
