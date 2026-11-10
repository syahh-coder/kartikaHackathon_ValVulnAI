"""Version-bound business rules for the tool-free mock path only.

Never imports lab/evaluator data, fetches a URL, accepts report instructions as
policy, or extends LAB planning. A context does not grant a capability or verdict.
"""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.common import AppError, digest, packed
from app.schemas import ScopeDraft
from app.storage.db import one


PROMPT_VERSION = "m6-simulation-context-v1"


class SimulationContext(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    mode: Literal["simulation_only"] = "simulation_only"
    run_id: str
    program_id: str
    scope_version_id: str
    scope_version: int = Field(ge=1)
    authorization_epoch: int = Field(ge=0)
    business_rules: str = Field(max_length=4000)
    business_rules_version: str | None
    business_rules_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    target_requests_allowed: Literal[False] = False


async def build(conn, run_id: str) -> SimulationContext:
    run = await one(conn, "SELECT * FROM runs WHERE run_id=?", (run_id,))
    if not run:
        raise AppError(404, "NOT_FOUND", "Run tidak ditemukan.")
    if run["execution_mode"] != "mock" or run["tool_execution_mode"] != "NONE":
        raise AppError(422, "SIMULATION_ONLY", "Konteks ini hanya untuk simulasi tanpa tool.")
    scope = await one(conn, "SELECT * FROM scope_versions WHERE scope_version_id=? AND program_id=?",
                      (run["scope_version_id"], run["program_id"]))
    if not scope:
        raise AppError(422, "CONTEXT_SCOPE_REQUIRED", "Versi aturan yang terikat pada run tidak tersedia.")
    try:
        rules = ScopeDraft.model_validate_json(scope["rules_json"])
    except ValueError:
        raise AppError(422, "CONTEXT_SCOPE_INVALID", "Schema aturan tersimpan tidak sah.") from None
    return SimulationContext(run_id=run_id, program_id=run["program_id"], scope_version_id=scope["scope_version_id"],
                             scope_version=scope["version"], authorization_epoch=run["authorization_epoch"],
                             business_rules=rules.business_rules, business_rules_version=rules.business_rules_version,
                             business_rules_sha256=digest(rules.business_rules))


def prompt(context: SimulationContext) -> str:
    return packed({"prompt_version": PROMPT_VERSION, "purpose": "Simulasi kontrak; tanpa tool, pengujian target atau inferensi live.",
                   "context": context.model_dump(), "tools": []})
