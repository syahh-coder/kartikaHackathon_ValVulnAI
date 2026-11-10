import asyncio
import hashlib
import json
import time
from uuid import UUID

import httpx

from boundary.contracts import ActionEnvelope, LAB_IP, ORIGIN, Observation


class HttpTool:
    def __init__(self, accounts: dict, transport=None):
        self.accounts, self.transport = accounts, transport

    async def execute(self, envelope: ActionEnvelope, envelope_hash: str, boot_id: str) -> Observation:
        args=envelope.validated_arguments
        count={"request_attempts":0,"responses_received":0}
        body,status,error,http_status,truncated="","OK",None,None,False
        secrets_to_remove=[x["password"] for x in self.accounts.values()]
        try:
            envelope.authorize()
            if envelope.artifact_remaining<4096:
                raise ValueError("ARTIFACT_LIMIT")
            async with asyncio.timeout(max(0.001,envelope.expires_at-time.time())):
                # Literal IP fixes the actual socket destination. Host/Origin remain the
                # registered origin, and are never accepted from tool/report arguments.
                async with httpx.AsyncClient(base_url=f"http://{LAB_IP}:8001",trust_env=False,
                                             follow_redirects=False,timeout=10,transport=self.transport,
                                             headers={"Host":"lab:8001","Origin":ORIGIN,"Accept":"application/json","Accept-Encoding":"identity"}) as client:
                    count["request_attempts"]+=1
                    login=await client.post("/api/auth/login",json={"login_name":args.account_alias,"password":self.accounts[args.account_alias]["password"]})
                    count["responses_received"]+=1
                    if login.status_code!=200 or len(login.content)>4096:
                        raise ValueError("AUTH_FAILED")
                    identity=login.json()
                    if identity.get("account_alias")!=args.account_alias or not isinstance(identity.get("csrf_token"),str):
                        raise ValueError("IDENTITY_MISMATCH")
                    secrets_to_remove += [identity["csrf_token"], *[c.value for c in client.cookies.jar]]
                    envelope.authorize()
                    count["request_attempts"]+=1
                    async with client.stream(args.method,args.relative_path,headers={"X-CSRF-Token":identity["csrf_token"]}) as response:
                        count["responses_received"]+=1
                        http_status=response.status_code
                        if response.headers.get("content-encoding", "identity")!="identity":
                            raise ValueError("ENCODING_DENIED")
                        data=bytearray()
                        async for part in response.aiter_raw():
                            if len(data)+len(part)>1048576:
                                data.extend(part[:1048576-len(data)])
                                truncated=True
                                break
                            data.extend(part)
                        body=bytes(data).decode("utf-8",errors="replace")
                        if 300<=http_status<400:
                            raise ValueError("REDIRECT_BLOCKED")
                        if truncated:
                            raise ValueError("RESPONSE_LIMIT")
        except asyncio.CancelledError:
            status="ACTION_OUTCOME_UNKNOWN" if args.method=="DELETE" else "CANCELLED"
            error=status
        except TimeoutError:
            status="ACTION_OUTCOME_UNKNOWN" if args.method=="DELETE" else "FAILED"
            error="NETWORK_TIMEOUT"
        except (ValueError,KeyError,json.JSONDecodeError) as exc:
            status="FAILED"
            error=str(exc) if str(exc) in {"ACTION_EXPIRED","POLICY_BLOCKED","AUTH_FAILED","IDENTITY_MISMATCH","REDIRECT_BLOCKED","RESPONSE_LIMIT","ENCODING_DENIED","ARTIFACT_LIMIT"} else "RESPONSE_SCHEMA_ERROR"
        except httpx.HTTPError:
            status="ACTION_OUTCOME_UNKNOWN" if args.method=="DELETE" else "FAILED"
            error="NETWORK_ERROR"
        for value in secrets_to_remove:
            if value:
                body=body.replace(value,"[REDACTED]")
        maximum=max(0,min(2*1048576,envelope.artifact_remaining)-4096)
        while len(json.dumps(body,ensure_ascii=False).encode())>maximum and body:
            body=body[:len(body)//2]
            truncated,status,error=True,"FAILED","ARTIFACT_LIMIT"
        return Observation(run_id=envelope.run_id,action_id=envelope.action_id,action_seq=envelope.action_seq,
                           envelope_hash=envelope_hash,target_snapshot_id=envelope.target_snapshot_id,boot_id=UUID(boot_id),
                           status=status,error_code=error,http_status=http_status,actor_alias=args.account_alias,
                           method=args.method,relative_path=args.relative_path,body=body,body_sha256=hashlib.sha256(body.encode()).hexdigest(),
                           truncated=truncated,**count,captured_at=time.time())
