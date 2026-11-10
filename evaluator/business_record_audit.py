"""Offline consistency checks for recorded M6b normal-workflow persistence data.

Reads bounded JSON only. No target transport, lab import, tool planning, script
execution, label mutation, or vulnerability verdict. Metadata is not attested.
"""
import argparse
import json
from pathlib import Path
from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field, StrictInt

from boundary.business_types import Record, RequestState, State, Fulfillment, SHA256, decode_json


MAX_RECORD_BYTES = 16 * 1024 * 1024
SHA256 = Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]


class Result(Record):
    status: Literal["PASS"]
    phase: Literal["initialize", "restart"]
    request_id: UUID
    expected_version: StrictInt = Field(ge=1, le=1000000)
    fulfillment: Fulfillment
    state: State
    uid: StrictInt
    source_sha256: dict[str, SHA256] = Field(max_length=128)


class Phase(Record):
    exit_code: StrictInt
    result: Result


class PersistenceRecord(Record):
    status: Literal["PASS"]
    mode: str = Field(max_length=256)
    volume: str = Field(max_length=256)
    image: str = Field(max_length=256)
    network: str = Field(max_length=32)
    phases: list[Phase] = Field(min_length=2, max_length=2)
    cleanup: str = Field(max_length=32)
    image_id: str = Field(max_length=128)
    checked_at_utc: str = Field(max_length=64)
    probe_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


def audit(value: dict) -> dict:
    output = {"status": "INCOMPLETE", "mode": "offline recorded-state consistency only", "findings": [],
              "vulnerability_verdict": None, "ground_truth": None,
              "not_assessed": ["Origin/authenticity of captures", "Actor permissions and unit assignments",
                               "Individual approval transitions absent from aggregate records", "Live model behavior"]}
    if not isinstance(value, dict) or value.get("status") != "PASS":
        output["findings"] = ["UPSTREAM_CHECK_NOT_PASS"]
        return output
    try:
        record = PersistenceRecord.model_validate(value)
    except ValueError:
        # Never echo validation input, arbitrary field values, tokens or filenames.
        output.update(status="INVALID", findings=["RECORD_SCHEMA_INVALID"])
        return output
    missing, issues = set(), set()
    if record.cleanup != "PASS" or record.network != "none":
        missing.add("RECORDED_ISOLATION_OR_CLEANUP_NOT_PASS")
    if [p.result.phase for p in record.phases] != ["initialize", "restart"]:
        missing.add("PHASE_ORDER_INCOMPLETE")
    for phase in record.phases:
        result, state, fulfillment = phase.result, phase.result.state, phase.result.fulfillment
        if phase.exit_code != 0 or result.uid != 10001:
            missing.add("PHASE_EXECUTION_NOT_VERIFIED")
        if len(state.requests) != 1 or state.events < 4:
            missing.add("SINGLE_REQUEST_TRACE_INCOMPLETE")
        if not result.source_sha256:
            missing.add("SOURCE_REFERENCES_MISSING")
        if not 1 <= fulfillment.quantity <= 1000:
            issues.add("QUANTITY_OUT_OF_RULE")
        if min(state.stock, fulfillment.stock_before, fulfillment.stock_after) < 0:
            issues.add("NEGATIVE_STOCK_RECORDED")
        if max(state.stock, fulfillment.stock_before, fulfillment.stock_after) > 10000:
            issues.add("STOCK_OUT_OF_RULE")
        if fulfillment.stock_before-fulfillment.stock_after != fulfillment.quantity:
            issues.add("STOCK_ARITHMETIC_MISMATCH")
        if state.stock != fulfillment.stock_after:
            issues.add("STOCK_STATE_MISMATCH")
        if state.fulfillments != 1:
            issues.add("FULFILLMENT_COUNT_MISMATCH")
        if len(state.requests) == 1 and state.events > 128:
            issues.add("JOURNAL_EVENT_LIMIT_EXCEEDED")
        if result.request_id != fulfillment.request_id or result.expected_version != fulfillment.request_version:
            issues.add("FULFILLMENT_BINDING_MISMATCH")
        for row in state.requests:
            if len(state.requests) == 1 and row.version != state.events:
                issues.add("JOURNAL_VERSION_MISMATCH")
            if (row.request_id != result.request_id or row.quantity != fulfillment.quantity or
                    row.state != "FULFILLED" or row.version != fulfillment.request_version+1):
                issues.add("REQUEST_STATE_MISMATCH")
    initial, repeated = [p.result for p in record.phases]
    if initial.state != repeated.state:
        issues.add("REPLAY_STATE_CHANGED")
    if initial.fulfillment != repeated.fulfillment:
        issues.add("REPLAY_FULFILLMENT_CHANGED")
    if initial.source_sha256 != repeated.source_sha256:
        missing.add("SOURCE_REFERENCES_CHANGED")
    output["status"] = "INCOMPLETE" if missing else "INCONSISTENT" if issues else "CONSISTENT"
    output["findings"] = sorted(missing | issues)
    output["phases_checked"] = 2
    return output


def read_json_record(path: Path) -> object:
    """Read bounded, unambiguous JSON; callers must validate its schema."""
    with path.open("rb") as stream:
        raw = stream.read(MAX_RECORD_BYTES + 1)
    if len(raw) > MAX_RECORD_BYTES:
        raise ValueError("Oversized record")
    return decode_json(raw, MAX_RECORD_BYTES)


def read_and_audit(path: Path) -> dict:
    try:
        return audit(read_json_record(path))
    except (OSError, ValueError, RecursionError):
        return {"status": "INVALID", "mode": "offline recorded-state consistency only", "findings": ["RECORD_READ_ERROR"],
                "vulnerability_verdict": None, "ground_truth": None}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path)
    args = parser.parse_args()
    result = read_and_audit(args.record)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["status"] == "CONSISTENT" else 2)


if __name__ == "__main__":
    main()
