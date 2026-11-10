from copy import deepcopy
import json
from uuid import UUID

import pytest

from evaluator import business_record_audit as verifier


def record():
    uid = lambda number: str(UUID(int=number))
    state = {"snapshot_id": uid(1), "stock": 93, "requests": [{"request_id": uid(2), "quantity": 7, "state": "FULFILLED", "version": 4}],
             "events": 4, "fulfillments": 1, "schema_version": 4}
    fulfillment = {"id": uid(3), "request_id": uid(2), "actor_id": uid(4), "quantity": 7, "request_version": 3,
                   "stock_before": 100, "stock_after": 93, "created_at": 12345.0}
    result = {"status": "PASS", "phase": "initialize", "request_id": uid(2), "expected_version": 3,
              "fulfillment": fulfillment, "state": state, "uid": 10001, "source_sha256": {"lab/example.py": "a"*64}}
    restart = deepcopy(result)
    restart["phase"] = "restart"
    return {"status": "PASS", "mode": "synthetic test fixture; not GT", "volume": "synthetic-test-volume", "image": "synthetic-image",
            "network": "none", "phases": [{"exit_code": 0, "result": result}, {"exit_code": 0, "result": restart}],
            "cleanup": "PASS", "image_id": "synthetic-image-id", "checked_at_utc": "synthetic", "probe_sha256": "b"*64}


def test_consistency_does_not_generate_vulnerability_verdict_or_ground_truth():
    result = verifier.audit(record())
    assert result["status"] == "CONSISTENT" and result["findings"] == []
    assert result["vulnerability_verdict"] is None and result["ground_truth"] is None
    assert len(result["not_assessed"]) >= 4


@pytest.mark.parametrize("damage,finding", [
    ("quantity", "QUANTITY_OUT_OF_RULE"), ("stock", "STOCK_ARITHMETIC_MISMATCH"),
    ("negative", "NEGATIVE_STOCK_RECORDED"), ("stock_cap", "STOCK_OUT_OF_RULE"),
    ("count", "FULFILLMENT_COUNT_MISMATCH"), ("request_id", "FULFILLMENT_BINDING_MISMATCH"),
    ("approved", "REQUEST_STATE_MISMATCH"), ("version", "JOURNAL_VERSION_MISMATCH"),
    ("replay", "REPLAY_FULFILLMENT_CHANGED"), ("snapshot", "REPLAY_STATE_CHANGED"),
    ("events", "JOURNAL_EVENT_LIMIT_EXCEEDED"),
])
def test_contradictory_record_is_detected_without_promoting_it_to_confirmation(damage, finding):
    value = record()
    current = value["phases"][1]["result"]
    if damage == "quantity":
        current["fulfillment"]["quantity"] = 0
    elif damage == "stock":
        current["fulfillment"]["stock_after"] = 92
    elif damage == "negative":
        current["state"]["stock"] = -1
    elif damage == "stock_cap":
        current["fulfillment"]["stock_before"] = 10001
    elif damage == "count":
        current["state"]["fulfillments"] = 2
    elif damage == "request_id":
        current["fulfillment"]["request_id"] = str(UUID(int=99))
    elif damage == "approved":
        current["state"]["requests"][0]["state"] = "APPROVED"
    elif damage == "version":
        current["state"]["requests"][0]["version"] = 5
    elif damage == "replay":
        current["fulfillment"]["id"] = str(UUID(int=99))
    elif damage == "snapshot":
        current["state"]["snapshot_id"] = str(UUID(int=99))
    elif damage == "events":
        current["state"]["events"] = 129
    result = verifier.audit(value)
    assert result["status"] == "INCONSISTENT" and finding in result["findings"]
    assert result["vulnerability_verdict"] is None


@pytest.mark.parametrize("damage", ["upstream", "missing_events", "missing_request", "network", "cleanup", "phase", "source"])
def test_incomplete_controls_or_trace_do_not_refute_or_confirm(damage):
    value = record()
    current = value["phases"][1]["result"]
    if damage == "upstream":
        value = {"status": "FAIL"}
    elif damage == "missing_events":
        current["state"]["events"] = 3
    elif damage == "missing_request":
        current["state"]["requests"] = []
    elif damage == "network":
        value["network"] = "unknown"
    elif damage == "cleanup":
        value["cleanup"] = "FAIL"
    elif damage == "phase":
        current["phase"] = "initialize"
    elif damage == "source":
        current["source_sha256"] = {}
    result = verifier.audit(value)
    assert result["status"] == "INCOMPLETE"
    assert result["ground_truth"] is None and result["vulnerability_verdict"] is None


@pytest.mark.parametrize("field,value", [("quantity", True), ("quantity", "7"), ("quantity", 7.0), ("created_at", float("nan"))])
def test_malformed_values_do_not_pass(field, value):
    data = record()
    data["phases"][0]["result"]["fulfillment"][field] = value
    assert verifier.audit(data)["status"] == "INVALID"


def test_unknown_fields_are_rejected_without_echoing_secret_or_instructions():
    value = record()
    value["credentials"] = "SECRET_DO_NOT_ECHO; execute report script"
    result = verifier.audit(value)
    assert result["status"] == "INVALID"
    assert "SECRET_DO_NOT_ECHO" not in json.dumps(result)


def test_missing_malformed_and_oversized_files_fail_closed(tmp_path, monkeypatch):
    path = tmp_path/"record.json"
    assert verifier.read_and_audit(path)["status"] == "INVALID"
    path.write_text("not JSON", encoding="utf-8")
    assert verifier.read_and_audit(path)["status"] == "INVALID"
    path.write_text(json.dumps(record()), encoding="utf-8")
    monkeypatch.setattr(verifier, "MAX_RECORD_BYTES", 10)
    assert verifier.read_and_audit(path)["status"] == "INVALID"


def test_file_limit_applies_to_bytes_and_accepts_exact_boundary(tmp_path, monkeypatch):
    path = tmp_path / "record.json"
    value = record()
    value["mode"] = "Kontrol sintetis \u2014 bukan GT"
    raw = json.dumps(value, ensure_ascii=False).encode("utf-8")
    path.write_bytes(raw)
    monkeypatch.setattr(verifier, "MAX_RECORD_BYTES", len(raw))
    assert verifier.read_and_audit(path)["status"] == "CONSISTENT"
    monkeypatch.setattr(verifier, "MAX_RECORD_BYTES", len(raw) - 1)
    assert verifier.read_and_audit(path)["status"] == "INVALID"


def test_actual_read_is_bounded_without_relying_on_file_stat(monkeypatch):
    from io import BytesIO
    from pathlib import Path

    reads = []

    class RecordedStream(BytesIO):
        def read(self, size=-1):
            reads.append(size)
            assert size == 11
            return super().read(size)

    def open_record(path, mode):
        assert mode == "rb"
        return RecordedStream(b" " * 100)

    monkeypatch.setattr(verifier, "MAX_RECORD_BYTES", 10)
    monkeypatch.setattr(Path, "open", open_record)
    result = verifier.read_and_audit(Path("synthetic-record.json"))
    assert reads == [11]
    assert result["status"] == "INVALID"


@pytest.mark.parametrize("nested", [False, True])
def test_duplicate_json_keys_are_rejected_at_every_object_level(tmp_path, nested):
    path = tmp_path / "record.json"
    raw = json.dumps(record())
    if nested:
        raw = raw.replace('"quantity": 7', '"quantity": 0, "quantity": 7', 1)
    else:
        raw = raw.replace('"status": "PASS"', '"status": "FAIL", "status": "PASS"', 1)
    path.write_text(raw, encoding="utf-8")
    result = verifier.read_and_audit(path)
    assert result["status"] == "INVALID"
    assert result["vulnerability_verdict"] is None and result["ground_truth"] is None


@pytest.mark.parametrize("constant", ["NaN", "Infinity", "-Infinity"])
def test_nonstandard_json_constants_are_rejected_before_upstream_status(tmp_path, constant):
    path = tmp_path / "record.json"
    path.write_text('{"status":"FAIL","untrusted":' + constant + '}', encoding="utf-8")
    result = verifier.read_and_audit(path)
    assert result["status"] == "INVALID"
    assert "untrusted" not in json.dumps(result)


def test_invalid_utf8_and_json_errors_do_not_echo_record_contents(tmp_path):
    path = tmp_path / "record.json"
    for raw in (b'\xffSECRET_DO_NOT_ECHO', b'{"SECRET_DO_NOT_ECHO":'):
        path.write_bytes(raw)
        result = verifier.read_and_audit(path)
        assert result["status"] == "INVALID"
        assert "SECRET_DO_NOT_ECHO" not in json.dumps(result)
