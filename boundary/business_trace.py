"""Offline consistency audit of a synthetic four-event normal procurement trace.

No transport, lab import, actor attestation, tool execution or vulnerability verdict.
Only the fixed CREATE/SUBMIT/APPROVE/FULFILL control fixture is supported.
"""
from typing import Literal
from uuid import UUID

from pydantic import Field, StrictInt

from boundary.business_types import Fulfillment, Record, SHA256, State


SNAPSHOT_FIELDS = ("request_id", "item_id", "quantity", "state", "version", "stock", "unit")
RULES_VERSION = "procurement-controls-v1"
OPERATIONS = ["CREATE", "SUBMIT", "APPROVE", "FULFILL"]
STATES = ["DRAFT", "SUBMITTED", "APPROVED", "FULFILLED"]


class Snapshot(Record):
    request_id: UUID
    item_id: UUID
    quantity: StrictInt = Field(ge=1, le=1000)
    state: Literal["DRAFT", "SUBMITTED", "APPROVED", "FULFILLED"]
    version: StrictInt = Field(ge=1, le=1000000)
    stock: StrictInt = Field(ge=0, le=10000)
    unit: str = Field(min_length=1, max_length=64)


class Actor(Record):
    actor_id: UUID
    unit: str = Field(min_length=1, max_length=64)
    staff_unit: str | None = Field(max_length=64)


class Event(Record):
    event_id: UUID
    request_id: UUID
    actor_id: UUID
    operation: Literal["CREATE", "EDIT", "SUBMIT", "APPROVE", "FULFILL"]
    before: Snapshot | None
    after: Snapshot
    created_at: float = Field(ge=0)


class Trace(Record):
    rules_version: str = Field(min_length=1, max_length=128)
    request_id: UUID
    owner_id: UUID
    approved_by: UUID | None
    actors: list[Actor] = Field(max_length=64)
    events: list[Event] = Field(max_length=128)
    final: Snapshot
    state: State
    fulfillment: Fulfillment


class Phase(Record):
    phase: Literal["initialize", "restart"]
    trace: Trace


class TraceRecord(Record):
    format_version: StrictInt = Field(ge=1, le=1)
    mode: Literal["synthetic normal workflow ASGI only"]
    phases: list[Phase] = Field(min_length=2, max_length=2)
    source_sha256: dict[str, SHA256] = Field(min_length=1, max_length=128)


def _output(status: str, findings: list[str]) -> dict:
    return {"status": status, "mode": "offline normal-workflow trace consistency only",
            "findings": findings, "vulnerability_verdict": None, "ground_truth": None,
            "not_assessed": ["Origin/authenticity of captures and actor/unit metadata",
                             "Authorization enforcement for unrecorded actions",
                             "Vulnerability impact and exploit controls", "Live model behavior"]}


def _check_trace(trace: Trace, missing: set[str], issues: set[str]) -> None:
    if trace.rules_version != RULES_VERSION:
        missing.add("RULES_VERSION_UNSUPPORTED")
        return
    if len(trace.events) < 4:
        missing.add("INDIVIDUAL_EVENTS_INCOMPLETE")
        return
    if [event.operation for event in trace.events] != OPERATIONS:
        issues.add("NORMAL_EVENT_SEQUENCE_MISMATCH")
        return
    actors = {actor.actor_id: actor for actor in trace.actors}
    if len(actors) != len(trace.actors):
        issues.add("DUPLICATE_ACTOR_ID")
    if len({event.event_id for event in trace.events}) != 4:
        issues.add("DUPLICATE_EVENT_ID")
    previous = None
    for index, event in enumerate(trace.events):
        after = event.after
        if event.request_id != trace.request_id or after.request_id != trace.request_id:
            issues.add("EVENT_REQUEST_BINDING_MISMATCH")
        if event.before != previous:
            issues.add("EVENT_STATE_CHAIN_MISMATCH")
        if after.state != STATES[index] or after.version != index + 1:
            issues.add("EVENT_TRANSITION_MISMATCH")
        if previous:
            if (after.item_id, after.quantity, after.unit) != (previous.item_id, previous.quantity, previous.unit):
                issues.add("MATERIAL_FIELDS_CHANGED")
            expected_stock = previous.stock - after.quantity if index == 3 else previous.stock
            if after.stock != expected_stock:
                issues.add("EVENT_STOCK_MISMATCH")
        actor = actors.get(event.actor_id)
        if actor is None:
            missing.add("EVENT_ACTOR_METADATA_MISSING")
        elif actor.unit != after.unit:
            issues.add("ACTOR_UNIT_MISMATCH")
        if index < 2:
            if event.actor_id != trace.owner_id:
                issues.add("REQUEST_OWNER_BINDING_MISMATCH")
        elif actor and actor.staff_unit != after.unit:
            issues.add("STAFF_ASSIGNMENT_MISMATCH")
        if index == 2 and (event.actor_id == trace.owner_id or event.actor_id != trace.approved_by):
            issues.add("APPROVAL_ACTOR_MISMATCH")
        previous = after
    if trace.final != previous:
        issues.add("FINAL_EVENT_STATE_MISMATCH")
    fulfillment = trace.fulfillment
    last = trace.events[-1]
    if (fulfillment.request_id != trace.request_id or fulfillment.actor_id != last.actor_id or
            fulfillment.request_version != 3 or fulfillment.quantity != trace.final.quantity or
            fulfillment.stock_after != trace.final.stock or
            fulfillment.stock_before != trace.events[-2].after.stock or
            fulfillment.stock_before - fulfillment.stock_after != fulfillment.quantity):
        issues.add("FULFILLMENT_TRACE_MISMATCH")
    state = trace.state
    if state.stock != trace.final.stock or state.events != 4 or state.fulfillments != 1:
        issues.add("AGGREGATE_TRACE_MISMATCH")
    if len(state.requests) != 1:
        missing.add("SINGLE_REQUEST_TRACE_INCOMPLETE")
    else:
        row = state.requests[0]
        if (row.request_id, row.quantity, row.state, row.version) != (
                trace.request_id, trace.final.quantity, trace.final.state, trace.final.version):
            issues.add("REQUEST_FINAL_STATE_MISMATCH")


def audit(value: object) -> dict:
    try:
        record = TraceRecord.model_validate(value)
    except ValueError:
        return _output("INVALID", ["TRACE_SCHEMA_INVALID"])
    missing, issues = set(), set()
    if [phase.phase for phase in record.phases] != ["initialize", "restart"]:
        missing.add("PHASE_ORDER_INCOMPLETE")
    for phase in record.phases:
        _check_trace(phase.trace, missing, issues)
    if record.phases[0].trace != record.phases[1].trace:
        issues.add("RESTART_TRACE_CHANGED")
    result = _output("INCOMPLETE" if missing else "INCONSISTENT" if issues else "CONSISTENT",
                     sorted(missing | issues))
    result["phases_checked"] = 2
    return result


