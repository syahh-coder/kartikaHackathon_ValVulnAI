import hashlib
from uuid import uuid4

import httpx

from test_handoff_worker import ACCOUNTS,envelope
from worker.http_tool import HttpTool


async def test_response_truncation_and_artifact_budget():
    def transport(request):
        if request.url.path=="/api/auth/login":
            return httpx.Response(200,json={"account_alias":"requester-a","csrf_token":"test-csrf"})
        return httpx.Response(200,stream=httpx.ByteStream(b"x"*1048577))
    tool=HttpTool(ACCOUNTS,httpx.MockTransport(transport))
    result=await tool.execute(envelope(),"f"*64,str(uuid4()))
    assert result.truncated and result.error_code=="RESPONSE_LIMIT"
    assert len(result.body)==1048576 and result.body_sha256==hashlib.sha256(result.body.encode()).hexdigest()
    result=await tool.execute(envelope(artifact_remaining=4096),"f"*64,str(uuid4()))
    assert result.truncated and result.error_code=="ARTIFACT_LIMIT" and result.body==""


async def test_no_network_when_artifact_budget_missing_or_expired():
    def deny(request): raise AssertionError("Transport must not be called")
    tool=HttpTool(ACCOUNTS,httpx.MockTransport(deny))
    for e in (envelope(artifact_remaining=1),envelope(issued_at=1,expires_at=2)):
        result=await tool.execute(e,"e"*64,str(uuid4()))
        assert result.status=="FAILED" and result.request_attempts==0
