from typing import Literal, Protocol

from pydantic import Field, model_validator

from app.schemas import DTO


class ProviderProfile(DTO):
    provider_id: str = Field(min_length=1, max_length=64)
    model_id: str = Field(min_length=1, max_length=128)
    credential_ref: str | None = None
    inference_provider_policy: str = "fixed"
    access_tier: Literal["FREE_TIER", "PROMO_CREDIT", "PAID"]
    enabled: bool = False
    tools_verified: bool = False
    schema_verified: bool = False
    tier_verified: bool = False
    max_input_tokens: int = Field(default=8192, ge=1, le=8192)
    max_output_tokens: int = Field(default=1024, ge=1, le=1024)
    max_cost_idr: int = Field(ge=0, le=50_000)
    price_snapshot: str


class ProviderResult(DTO):
    call_id: str
    provider_id: str
    requested_model_id: str
    resolved_model_id: str
    inference_provider: str
    text: str = Field(default="", max_length=32_000)
    proposed_tool_calls: list[dict] = Field(default_factory=list, max_length=8)
    refusal: bool = False
    finish_reason: str = "stop"
    usage: dict[str, int] | None = None
    cost_status: Literal["KNOWN", "COST_UNKNOWN"] = "COST_UNKNOWN"
    actual_cost_idr: int | None = Field(default=None, ge=0)
    provider_request_id: str | None = None
    redacted_raw_response_ref: str | None = None

    @model_validator(mode="after")
    def validate_cost_and_usage(self):
        if self.cost_status=="KNOWN" and self.actual_cost_idr is None:
            raise ValueError("Known cost requires actual_cost_idr")
        if self.cost_status=="COST_UNKNOWN" and self.actual_cost_idr is not None:
            raise ValueError("Unknown cost must retain reservation")
        if self.usage and any(n<0 for n in self.usage.values()):
            raise ValueError("Token usage cannot be negative")
        return self


class ProviderFailure(Exception):
    def __init__(self, code: str, retry_after: float = 0, cost_idr: int | None = None):
        self.code, self.retry_after, self.cost_idr = code, retry_after, cost_idr


class Transport(Protocol):
    async def dispatch(self, profile: ProviderProfile, call_id: str, prompt: str) -> ProviderResult: ...
