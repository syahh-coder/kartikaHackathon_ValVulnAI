import hashlib
import hmac
import json
import re
import time
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

ORIGIN = "http://lab:8001"
LAB_IP = "172.30.74.3"
WORKER_IP = "172.30.74.2"
ALIASES = ("requester-a", "requester-b")


def canonical(value: dict) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class HttpArguments(Strict):
    method: Literal["GET", "DELETE"]
    relative_path: str = Field(pattern=r"^/api/attachments/[A-Za-z0-9_-]{1,64}$")
    account_alias: Literal["requester-a", "requester-b"]


class BrowserArguments(Strict):
    operation: Literal["notification_probe", "upload_list_probe"] = "notification_probe"
    method: Literal["GET"] = "GET"
    relative_path: str = "/notifications/preview"
    account_alias: Literal["requester-a", "requester-b"]
    fixture: Literal["inert-v1", "marker-v1"]
    nonce: UUID

    @model_validator(mode="after")
    def fixed_route(self):
        if self.operation == "notification_probe":
            if self.relative_path != "/notifications/preview":
                raise ValueError("BROWSER_ROUTE_DENIED")
        elif not re.fullmatch(r"/requests/[a-f0-9-]{36}/(?:attachments|attachment-labels)", self.relative_path):
            raise ValueError("BROWSER_ROUTE_DENIED")
        else:
            UUID(self.relative_path.split('/')[2])
        return self


class UploadArguments(Strict):
    operation: Literal["upload_fixture"] = "upload_fixture"
    method: Literal["POST"] = "POST"
    relative_path: str = Field(pattern=r"^/api/requests/[a-f0-9-]{36}/attachments$")
    account_alias: Literal["requester-a"] = "requester-a"
    fixture: Literal["inert-v1", "marker-v1"]
    nonce: UUID

    @model_validator(mode="after")
    def object_id(self):
        UUID(self.relative_path.split('/')[3])
        return self


class ScopedRule(Strict):
    path_template: Literal["/api/attachments/{id}", "/notifications/preview", "/api/requests/{id}/attachments",
                           "/requests/{id}/attachments", "/requests/{id}/attachment-labels"]
    methods: list[Literal["GET", "DELETE", "POST"]] = Field(min_length=1, max_length=3)


class ActionEnvelope(Strict):
    schema_version: Literal[1] = 1
    run_id: UUID
    action_id: UUID
    action_seq: int = Field(ge=1, le=40)
    program_id: UUID
    target_id: Literal["portal-lab"] = "portal-lab"
    scope_version_id: UUID
    authorization_epoch: int = Field(ge=0)
    target_snapshot_id: UUID
    tool_name: Literal["http_request", "browser_probe", "upload_fixture"] = "http_request"
    validated_arguments: HttpArguments | BrowserArguments | UploadArguments
    allowed_rules: list[ScopedRule] = Field(min_length=1, max_length=24)
    excluded_rules: list[ScopedRule] = Field(default_factory=list, max_length=24)
    issued_at: float
    expires_at: float
    network_remaining: int = Field(ge=2, le=40)
    artifact_remaining: int = Field(ge=1, le=16777216)

    @model_validator(mode="after")
    def limits(self):
        browser = isinstance(self.validated_arguments, BrowserArguments)
        if browser != (self.tool_name == "browser_probe"):
            raise ValueError("TOOL_ARGUMENT_MISMATCH")
        if isinstance(self.validated_arguments, UploadArguments) != (self.tool_name == "upload_fixture"):
            raise ValueError("TOOL_ARGUMENT_MISMATCH")
        if not 0 < self.expires_at-self.issued_at <= (30 if browser else 10):
            raise ValueError("Action validity exceeds tool deadline")
        return self

    def authorize(self, now: float | None = None):
        now = time.time() if now is None else now
        if self.issued_at > now+1 or self.expires_at <= now:
            raise ValueError("ACTION_EXPIRED")
        method = self.validated_arguments.method
        path = self.validated_arguments.relative_path
        def applies(rule):
            template = rule.path_template
            a, b = template.split('/'), path.split('/')
            matches = len(a) == len(b) and all(x == y or (x == '{id}' and bool(re.fullmatch(r'[A-Za-z0-9_-]{1,64}', y))) for x,y in zip(a,b))
            return matches and method in rule.methods
        if any(applies(r) for r in self.excluded_rules):
            raise ValueError("POLICY_BLOCKED")
        if not any(applies(r) for r in self.allowed_rules):
            raise ValueError("POLICY_BLOCKED")


class Observation(Strict):
    schema_version: Literal[1] = 1
    run_id: UUID
    action_id: UUID
    action_seq: int = Field(ge=1, le=40)
    envelope_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    target_snapshot_id: UUID
    boot_id: UUID
    status: Literal["OK", "FAILED", "CANCELLED", "ACTION_OUTCOME_UNKNOWN"]
    error_code: str | None = Field(default=None, max_length=64)
    http_status: int | None = Field(default=None, ge=100, le=599)
    actor_alias: Literal["requester-a", "requester-b"]
    method: Literal["GET", "DELETE", "POST"]
    relative_path: str = Field(max_length=100)
    body: str = Field(default="", max_length=1048576)
    body_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    truncated: bool = False
    request_attempts: int = Field(ge=0, le=2)
    responses_received: int = Field(ge=0, le=2)
    captured_at: float

    @model_validator(mode="after")
    def consistent(self):
        if hashlib.sha256(self.body.encode()).hexdigest() != self.body_sha256:
            raise ValueError("BODY_HASH_MISMATCH")
        if self.responses_received > self.request_attempts:
            raise ValueError("COUNTER_MISMATCH")
        return self


class BrowserObservation(Observation):
    tool_name: Literal["browser_probe"] = "browser_probe"


class UploadObservation(Observation):
    tool_name: Literal["upload_fixture"] = "upload_fixture"


def observation_from(value: dict) -> Observation:
    cls = {"browser_probe": BrowserObservation, "upload_fixture": UploadObservation}.get(value.get("tool_name"), Observation)
    return cls.model_validate(value)


class Control(Strict):
    schema_version: Literal[1] = 1
    control_id: UUID
    kind: Literal["ACK", "CANCEL", "RESET_RELEASE"]
    run_id: UUID | None = None
    action_id: UUID | None = None
    snapshot_id: UUID | None = None
    issued_at: float
    expires_at: float

    @model_validator(mode="after")
    def scope(self):
        if not 0 < self.expires_at-self.issued_at <= 30:
            raise ValueError("Control expiry exceeds limit")
        if self.kind=="ACK" and (not self.action_id or not self.run_id):
            raise ValueError("ACK needs run/action")
        if self.kind=="CANCEL" and not self.run_id:
            raise ValueError("CANCEL needs run")
        if self.kind=="RESET_RELEASE" and not self.snapshot_id:
            raise ValueError("Release needs a neutral snapshot ID")
        return self


def signed(payload: dict, key: bytes) -> dict:
    return {"payload": payload, "signature": hmac.new(key, canonical(payload), hashlib.sha256).hexdigest()}


def verified(document: dict, key: bytes) -> dict:
    if set(document) != {"payload", "signature"} or not isinstance(document["signature"], str):
        raise ValueError("ENVELOPE_INVALID")
    expected = hmac.new(key, canonical(document["payload"]), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(document["signature"], expected):
        raise ValueError("SIGNATURE_INVALID")
    return document["payload"]
