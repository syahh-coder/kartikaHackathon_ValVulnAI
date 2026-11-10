from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DTO(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=False)


class Login(DTO):
    login_name: str = Field(min_length=1, max_length=64, pattern=r"^[a-z0-9._-]+$")
    password: str = Field(min_length=1, max_length=128)


class MessageInput(DTO):
    body: str = Field(min_length=1, max_length=32_000)
    title: str = Field(default="Laporan", min_length=1, max_length=200)
    expected_draft_version: int = Field(ge=0)


class Rule(DTO):
    asset_alias: str = Field(min_length=1, max_length=64, pattern=r"^[a-z0-9-]+$")
    path_template: str = Field(min_length=1, max_length=200)
    methods: list[Literal["GET", "POST", "PUT", "PATCH", "DELETE"]] = Field(min_length=1, max_length=5)
    capabilities: list[Literal["BAC", "XSS", "UPLOAD", "BUSINESS_LOGIC"]] = Field(min_length=1, max_length=4)


class ScopeDraft(DTO):
    source_text: str = Field(min_length=1, max_length=32_000)
    in_scope_rules: list[Rule] = Field(min_length=1, max_length=24)
    out_of_scope_rules: list[Rule] = Field(default_factory=list, max_length=24)
    business_rules: str = Field(default="", max_length=4000)
    business_rules_version: str | None = Field(default=None, pattern=r"^[A-Za-z0-9._-]{1,64}$")

    @field_validator("source_text")
    @classmethod
    def source_bytes(cls, value):
        if not value.strip():
            raise ValueError("Guideline text cannot be blank")
        if len(value.encode("utf-8")) > 131072:
            raise ValueError("Guideline exceeds 128 KiB")
        return value


class Claim(DTO):
    asset_alias: str | None = Field(default=None, max_length=64)
    path: str | None = Field(default=None, max_length=2048)
    method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"] = "GET"
    category: Literal["BAC", "XSS", "UPLOAD", "BUSINESS_LOGIC", "DOS", "OTHER"] = "BAC"
    account_aliases: list[str] = Field(default_factory=list, max_length=2)
    primary_claim: str = Field(default="", max_length=2000)
    claim_count: int = Field(default=1, ge=1, le=20)
    control_path: str | None = Field(default=None, max_length=2048)


class SnapshotInput(DTO):
    expected_draft_version: int = Field(ge=1)
    claim: Claim


class RunInput(DTO):
    report_revision_id: str
    execution_mode: Literal["mock", "live", "replay"] = "mock"
    tool_execution_mode: Literal["NONE", "LAB"] = "NONE"


class ReviewInput(DTO):
    analyst_override: Literal["CONFIRMED", "REFUTED", "INCONCLUSIVE"] | None = None
    reviewer_note: str = Field(min_length=1, max_length=2000)
