"""Bounded fixture upload, credentials by alias; no user file or script execution."""
import asyncio
import base64
import hashlib
import json
import time

import httpx

from boundary.contracts import ActionEnvelope, UploadObservation, LAB_IP, ORIGIN
from boundary.uploads import CONTENT, CONTENT_SHA256, filename


class UploadTool:
    def __init__(self, accounts: dict, transport=None):
        self.accounts, self.transport = accounts, transport

    async def execute(self, envelope: ActionEnvelope, fingerprint: str, boot_id: str) -> UploadObservation:
        args = envelope.validated_arguments
        attempts, responses, status_code = 0, 0, None
        status, error, body = "OK", None, ""
        try:
            if envelope.artifact_remaining < 4096:
                raise ValueError("ARTIFACT_LIMIT")
            async with asyncio.timeout(max(.001, envelope.expires_at-time.time())):
                async with httpx.AsyncClient(base_url=f"http://{LAB_IP}:8001", trust_env=False, follow_redirects=False, transport=self.transport,
                        timeout=8, headers={"Host": "lab:8001", "Origin": ORIGIN, "Accept-Encoding": "identity"}) as client:
                    async def exchange(method: str, path: str, payload: dict, headers: dict | None = None):
                        nonlocal attempts, responses, status_code
                        envelope.authorize()
                        if attempts >= min(2, envelope.network_remaining):
                            raise ValueError("NETWORK_LIMIT")
                        attempts += 1
                        async with client.stream(method, path, json=payload, headers=headers) as response:
                            responses += 1
                            status_code = response.status_code
                            if status_code != 200 or response.headers.get("content-encoding", "identity") != "identity":
                                raise ValueError("UPLOAD_FAILED")
                            raw = bytearray()
                            async for chunk in response.aiter_bytes():
                                if len(raw)+len(chunk)>4096:
                                    raise ValueError("RESPONSE_LIMIT")
                                raw.extend(chunk)
                            return json.loads(raw)
                    identity = await exchange("POST", "/api/auth/login", {"login_name": args.account_alias,
                        "password": self.accounts[args.account_alias]["password"]})
                    if identity.get("account_alias") != args.account_alias:
                        raise ValueError("AUTH_FAILED")
                    rid = args.relative_path.split('/')[3]
                    expected_name = filename(args.fixture, args.nonce)
                    value = await exchange("POST", args.relative_path, {"request_id": rid, "filename": expected_name,
                        "media_type": "text/plain", "content_base64": base64.b64encode(CONTENT).decode()},
                        {"X-CSRF-Token": identity["csrf_token"]})
                    from uuid import UUID
                    UUID(value["upload_id"])
                    if (value["request_id"] != rid or value["filename"] != expected_name or value["media_type"] != "text/plain"
                            or value["content_sha256"] != CONTENT_SHA256 or value["size"] != len(CONTENT)):
                        raise ValueError("UPLOAD_SCHEMA_ERROR")
                    # Copy only known fields, never echo arbitrary response/session material.
                    body = json.dumps({k:value[k] for k in ("upload_id", "request_id", "filename", "media_type", "content_sha256", "size")})
        except asyncio.CancelledError:
            status, error = "ACTION_OUTCOME_UNKNOWN", "CANCELLED"
        except TimeoutError:
            status, error = "ACTION_OUTCOME_UNKNOWN", "UPLOAD_TIMEOUT"
        except (httpx.HTTPError, ValueError, KeyError, TypeError):
            status, error = "FAILED", "UPLOAD_FAILED"
        return UploadObservation(run_id=envelope.run_id, action_id=envelope.action_id, action_seq=envelope.action_seq,
            envelope_hash=fingerprint, target_snapshot_id=envelope.target_snapshot_id, boot_id=boot_id,
            status=status, error_code=error, actor_alias=args.account_alias, method="POST", relative_path=args.relative_path,
            http_status=status_code, body=body, body_sha256=hashlib.sha256(body.encode()).hexdigest(),
            request_attempts=attempts, responses_received=responses, captured_at=time.time())
