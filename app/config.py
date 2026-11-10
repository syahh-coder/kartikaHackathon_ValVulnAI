from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from decimal import Decimal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="VALVULN_", env_file=".env", extra="forbid")
    data_dir: Path = Path(".local-data")
    public_origin: str = "http://127.0.0.1:8000"
    allow_http_loopback: bool = True
    cookie_secure: bool = False
    execution_mode: Literal["mock", "live", "replay"] = "mock"
    # Text inference is independent of the deterministic lab planner.
    triage_mode: Literal["mock", "live", "replay"] = "mock"
    triage_provider: Literal["openrouter", "azure"] = "openrouter"
    openrouter_api_key: SecretStr | None = Field(default=None, repr=False)
    azure_api_key: SecretStr | None = Field(default=None, repr=False)
    azure_endpoint: str = Field(default="", max_length=300)
    azure_expected_model: str = Field(default="", max_length=128)
    azure_api_capabilities_verified: bool = False
    triage_model: str = Field(default="", max_length=128)
    triage_provider_slug: str = Field(default="", max_length=128)
    triage_provider_name: str = Field(default="", max_length=128)
    triage_access_tier: Literal["FREE_TIER", "PROMO_CREDIT", "PAID"] = "PAID"
    triage_access_verified: bool = False
    triage_token_bound_verified: bool = False
    triage_price_snapshot: str = Field(default="", max_length=500)
    triage_prompt_usd_per_million: Decimal | None = Field(default=None, ge=0, allow_inf_nan=False)
    triage_completion_usd_per_million: Decimal | None = Field(default=None, ge=0, allow_inf_nan=False)
    triage_usd_to_idr: Decimal | None = Field(default=None, gt=0, allow_inf_nan=False)
    triage_reservation_idr: int = Field(default=0, ge=0, le=50_000)
    triage_timeout_seconds: float = Field(default=30, ge=0.1, le=60, allow_inf_nan=False)
    triage_retry_enabled: bool = False
    budget_idr: int = Field(default=50_000, ge=0, le=50_000)
    session_hours: int = Field(default=8, ge=1, le=8)
    min_free_bytes: int = Field(default=2 * 1024**3, ge=0)
    storage_limit_bytes: int = Field(default=1024**3, ge=1)
    queue_limit: int = Field(default=5, ge=1, le=5)
    dispatcher_enabled: bool = True
    transport_key_file: Path | None = None

    @model_validator(mode="after")
    def secure_origin(self) -> "Settings":
        url = urlsplit(self.public_origin)
        if (url.scheme not in {"http", "https"} or not url.hostname or
                url.username or url.password or url.path or url.query or url.fragment):
            raise ValueError("PUBLIC_ORIGIN must be an exact HTTP(S) origin without a path")
        if url.scheme == "http":
            if not self.allow_http_loopback or url.hostname not in {"127.0.0.1", "localhost", "::1"}:
                raise ValueError("HTTP is restricted to explicit loopback development")
            if self.cookie_secure:
                raise ValueError("Secure cookie requires HTTPS; use explicit loopback HTTP settings")
        elif not self.cookie_secure:
            raise ValueError("HTTPS requires COOKIE_SECURE=true")
        return self

    @property
    def db_path(self) -> Path:
        return self.data_dir / "valvuln.sqlite3"
