from copy import deepcopy
from itertools import count
import json
from uuid import UUID

import pytest

from evaluator import business_trace_audit as verifier
from scripts.m6e_trace_check import run_check


def record():
    uid = lambda number: str(UUID(int=number))
    snapshots = [{"request_id": uid(2), "item_id": uid(6), "quantity": 7, "unit": "A",
                  "state": state, "version": index + 1, "stock": 93 if index == 3 else 100}
                 for index, state in enumerate(verifier.STATES)]
    events = [{"event_id": uid(10 + index), "request_id": uid(2),
               "actor_id": uid(5 if index < 2 else 4), "operation": operation,
               "before": deepcopy(snapshots[index-1]) if index else None,
               "after": deepcopy(snapshots[index]), "created_at": 12345.0 + index}
              for index, operation in enumerate(verifier.OPERATIONS)]
    trace = {"rules_version": "procurement-controls-v1", "request_id": uid(2), "owner_id": uid(5),
             "approved_by": uid(4), "actors": [{"actor_id": uid(5), "unit": "A", "staff_unit": None},
                                               {"actor_id": uid(4), "unit": "A", "staff_unit": "A"}],
             "events": events, "final": deepcopy(snapshots[-1]),
             "state": {"snapshot_id": uid(1), "stock": 93, "requests": [
                 {"request_id": uid(2), "quantity": 7, "state": "FULFILLED", "version": 4}],
                 "events": 4, "fulfillments": 1, "schema_version": 4},
             "fulfillment": {"id": uid(3), "request_id": uid(2), "actor_id": uid(4), "quantity": 7,
                             "request_version": 3, "stock_before": 100, "stock_after": 93, "created_at": 12348.0}}
    return {"format_version": 1, "mode": "synthetic normal workflow ASGI only",
            "phases": [{"phase": "initialize", "trace": trace}, {"phase": "restart", "trace": deepcopy(trace)}],
            "source_sha256": {"synthetic.py": "a" * 64}}


def test_consistent_trace_is_not_attestation_or_vulnerability_verdict():
    result = verifier.audit(record())
    assert result["status"] == "CONSISTENT" and result["findings"] == []
    assert result["vulnerability_verdict"] is None and result["ground_truth"] is None
    assert "authenticity" in result["not_assessed"][0]


@pytest.mark.parametrize("damage,finding", [
    ("sequence", "NORMAL_EVENT_SEQUENCE_MISMATCH"),
    ("chain", "EVENT_STATE_CHAIN_MISMATCH"),
    ("create_before", "EVENT_STATE_CHAIN_MISMATCH"),
    ("transition", "EVENT_TRANSITION_MISMATCH"),
    ("request", "EVENT_REQUEST_BINDING_MISMATCH"),
    ("owner", "REQUEST_OWNER_BINDING_MISMATCH"),
    ("self_approval", "APPROVAL_ACTOR_MISMATCH"),
    ("approver", "APPROVAL_ACTOR_MISMATCH"),
    ("unit", "ACTOR_UNIT_MISMATCH"),
    ("staff", "STAFF_ASSIGNMENT_MISMATCH"),
    ("material", "MATERIAL_FIELDS_CHANGED"),
    ("stock", "EVENT_STOCK_MISMATCH"),
    ("event_id", "DUPLICATE_EVENT_ID"),
    ("actor_id", "DUPLICATE_ACTOR_ID"),
    ("final", "FINAL_EVENT_STATE_MISMATCH"),
    ("fulfillment_actor", "FULFILLMENT_TRACE_MISMATCH"),
    ("aggregate", "AGGREGATE_TRACE_MISMATCH"),
    ("final_request", "REQUEST_FINAL_STATE_MISMATCH"),
])
def test_recorded_contradictions_are_detected_even_when_repeated_identically(damage, finding):
    value = record()
    trace = value["phases"][0]["trace"]
    events = trace["events"]
    if damage == "sequence":
        events[2]["operation"] = "SUBMIT"
    elif damage == "chain":
        events[2]["before"]["stock"] = 99
    elif damage == "create_before":
        events[0]["before"] = deepcopy(events[0]["after"])
    elif damage == "transition":
        events[2]["after"]["version"] = 8
    elif damage == "request":
        events[1]["request_id"] = str(UUID(int=999))
    elif damage == "owner":
        events[1]["actor_id"] = trace["approved_by"]
    elif damage == "self_approval":
        events[2]["actor_id"] = trace["owner_id"]
    elif damage == "approver":
        trace["approved_by"] = trace["owner_id"]
    elif damage == "unit":
        trace["actors"][1]["unit"] = "B"
    elif damage == "staff":
        trace["actors"][1]["staff_unit"] = "B"
    elif damage == "material":
        events[2]["after"]["quantity"] = 8
    elif damage == "stock":
        events[3]["after"]["stock"] = 92
    elif damage == "event_id":
        events[2]["event_id"] = events[0]["event_id"]
    elif damage == "actor_id":
        trace["actors"].append(deepcopy(trace["actors"][0]))
    elif damage == "final":
        trace["final"]["stock"] = 92
    elif damage == "fulfillment_actor":
        trace["fulfillment"]["actor_id"] = trace["owner_id"]
    elif damage == "aggregate":
        trace["state"]["events"] = 5
    elif damage == "final_request":
        trace["state"]["requests"][0]["version"] = 5
    value["phases"][1]["trace"] = deepcopy(trace)
    result = verifier.audit(value)
    assert result["status"] == "INCONSISTENT" and finding in result["findings"]
    assert "RESTART_TRACE_CHANGED" not in result["findings"]
    assert result["vulnerability_verdict"] is None and result["ground_truth"] is None


@pytest.mark.parametrize("damage,finding", [
    ("events", "INDIVIDUAL_EVENTS_INCOMPLETE"), ("actor", "EVENT_ACTOR_METADATA_MISSING"),
    ("rules", "RULES_VERSION_UNSUPPORTED"), ("phase", "PHASE_ORDER_INCOMPLETE"),
    ("request", "SINGLE_REQUEST_TRACE_INCOMPLETE"),
])
def test_missing_support_is_incomplete_without_a_verdict(damage, finding):
    value = record()
    trace = value["phases"][0]["trace"]
    if damage == "events":
        trace["events"].pop(2)
    elif damage == "actor":
        trace["actors"].pop()
    elif damage == "rules":
        trace["rules_version"] = "unknown-rules-version"
    elif damage == "phase":
        value["phases"][1]["phase"] = "initialize"
    elif damage == "request":
        trace["state"]["requests"] = []
    result = verifier.audit(value)
    assert result["status"] == "INCOMPLETE" and finding in result["findings"]
    assert result["vulnerability_verdict"] is None


def test_restart_metadata_and_snapshot_must_match():
    value = record()
    value["phases"][1]["trace"]["state"]["snapshot_id"] = str(UUID(int=999))
    result = verifier.audit(value)
    assert result["status"] == "INCONSISTENT" and "RESTART_TRACE_CHANGED" in result["findings"]


@pytest.mark.parametrize("bad", [True, "7", 7.0, 0, 1001])
def test_trace_quantity_requires_bounded_strict_integer(bad):
    value = record()
    value["phases"][0]["trace"]["events"][0]["after"]["quantity"] = bad
    assert verifier.audit(value)["status"] == "INVALID"


def test_schema_errors_and_parser_errors_never_echo_input(tmp_path):
    path = tmp_path / "trace.json"
    value = record()
    value["instructions"] = "SECRET_DO_NOT_ECHO; execute script"
    result = verifier.audit(value)
    assert result["status"] == "INVALID" and "SECRET_DO_NOT_ECHO" not in json.dumps(result)
    raw = json.dumps(record()).replace('"format_version": 1', '"format_version": 0, "format_version": 1')
    path.write_text(raw, encoding="utf-8")
    assert verifier.read_and_audit(path)["status"] == "INVALID"
    path.write_text(json.dumps(record()), encoding="utf-8")
    assert verifier.read_and_audit(path)["status"] == "CONSISTENT"
    assert verifier.read_and_audit(tmp_path / "missing.json")["status"] == "INVALID"


async def test_actual_asgi_normal_workflow_captures_chain_and_preserves_it_after_restart(monkeypatch):
    # secrets is shared with lab session creation; preserve token uniqueness.
    sequence = count()
    monkeypatch.setattr("scripts.m6e_trace_check.secrets.token_urlsafe",
                        lambda length: f"synthetic-secret-never-export-{next(sequence)}")
    value = await run_check()
    result = verifier.audit(value)
    assert result["status"] == "CONSISTENT", result
    assert value["phases"][0]["trace"] == value["phases"][1]["trace"]
    assert value["phases"][0]["trace"]["state"]["stock"] == 93
    serialized = json.dumps(value)
    for forbidden in ("synthetic-secret-never-export", "password_hash", "csrf_token", "lab_session"):
        assert forbidden not in serialized
