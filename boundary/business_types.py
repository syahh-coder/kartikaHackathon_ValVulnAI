"""Bounded types and JSON decoding for untrusted recorded business data."""
import json
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StrictInt

SHA256 = Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]

class Record(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class RequestState(Record):
    request_id: UUID
    quantity: StrictInt = Field(ge=-100000, le=100000)
    state: Literal["DRAFT", "SUBMITTED", "APPROVED", "FULFILLED"]
    version: StrictInt = Field(ge=1, le=1000000)


class State(Record):
    snapshot_id: UUID
    stock: StrictInt = Field(ge=-100000, le=100000)
    requests: list[RequestState] = Field(max_length=64)
    events: StrictInt = Field(ge=0, le=8192)
    fulfillments: StrictInt = Field(ge=0, le=64)
    schema_version: StrictInt = Field(ge=1, le=1000)


class Fulfillment(Record):
    id: UUID
    request_id: UUID
    actor_id: UUID
    quantity: StrictInt = Field(ge=-100000, le=100000)
    request_version: StrictInt = Field(ge=1, le=1000000)
    stock_before: StrictInt = Field(ge=-100000, le=100000)
    stock_after: StrictInt = Field(ge=-100000, le=100000)
    created_at: float = Field(ge=0)


def _unique_object(pairs: list[tuple[str, object]]) -> dict:
    """Reject ambiguous JSON instead of silently retaining the final value."""
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("Duplicate JSON key")
        value[key] = item
    return value


def _reject_constant(value: str) -> None:
    raise ValueError("Non-finite JSON constant")


def decode_json(raw: bytes, maximum: int) -> object:
    if len(raw) > maximum:
        raise ValueError("Oversized record")
    return json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object,
                      parse_constant=_reject_constant)
