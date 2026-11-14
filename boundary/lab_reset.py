"""Private operator mailbox; never a report/model/worker tool."""
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

LabCondition = Literal["vulnerable", "fixed"]


class ResetRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: UUID
    operation: Literal["RESET_VULNERABLE_DEMO", "RESET_DEMO_LAB"]
    condition: LabCondition = "vulnerable"
    issued_at: float = Field(allow_inf_nan=False)
    expires_at: float = Field(allow_inf_nan=False)

    @model_validator(mode="after")
    def legacy_condition(self):
        if self.operation == "RESET_VULNERABLE_DEMO" and self.condition != "vulnerable":
            raise ValueError("Legacy reset only permits vulnerable")
        return self


class ResetResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: UUID
    status: Literal["SUCCEEDED", "FAILED"]
    condition: LabCondition | None = None
    coverage: Literal["ALL_IMPLEMENTED"] | None = None
    snapshot_id: UUID | None = None
    objects: dict[str, dict[str, UUID]] = Field(default_factory=dict)
    error_code: Literal["RESET_FAILED", "REQUEST_EXPIRED"] | None = None
