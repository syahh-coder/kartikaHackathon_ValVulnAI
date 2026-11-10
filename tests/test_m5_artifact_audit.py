"""Offline audit must reject incomplete, stale and corrupted recorded evidence."""
import base64
import copy
import hashlib
import json

import pytest

from scripts.audit_m5_artifacts import PNG_SIGNATURE, audit


@pytest.fixture
def records(tmp_path):
    source = tmp_path / "source.py"
    source.write_text("# synthetic source\n", encoding="utf-8")
    png = PNG_SIGNATURE + b"synthetic signature/hash fixture only"
    capture = {"screenshot_base64": base64.b64encode(png).decode(), "screenshot_sha256": hashlib.sha256(png).hexdigest()}
    results = []
    for point in ("UP-01", "UP-02", "UP-03", "UP-04"):
        for condition in ("vulnerable", "fixed"):
            rid = f"{point}-{condition}"
            result = {"point": point, "condition": condition, "run_id": rid, "status": "PASS"}
            if point == "UP-04":
                verdict = "CONFIRMED" if condition == "vulnerable" else "REFUTED"
                result.update(verdict=verdict, publication_export="PASS", evidence=[copy.deepcopy(capture) for _ in range(3)] + [{}, {}],
                              private_run={"run_id": rid, "process_status": "COMPLETED", "execution_mode": "mock", "inference_provider": "mock",
                                           "assessment": {"system_verified": {"verdict": verdict}}, "counters": {"target_requests": 10}})
            else:
                result["probe"] = {"status": "PASS", "observations": [copy.deepcopy(capture) for _ in range(3)] if point != "UP-03" else [{"source": "operator_http"}]}
            results.append(result)
    record = {"status": "PASS", "points": [f"UP-{i:02d}" for i in range(1, 5)], "results": results,
              "source_sha256": {"source.py": hashlib.sha256(source.read_bytes()).hexdigest()},
              "final_state": {"heartbeat": {"status": "IDLE", "dirty": False, "active_run_id": None, "dirty_run_id": None, "snapshot_id": "snapshot"},
                              "browser_processes": [], "access_log": []}}
    ui = {"status": "PASS", "run_id": "UP-04-vulnerable", "new_runs": 0, "target_requests": 0, "page_errors": [], "external_requests": [],
          "upload_form_and_switch": "PASS", "inert_evidence": "PASS", "private_projection_export": "PASS", "viewports": [1366, 1024, 768, 390, 360],
          "download": {"filename": "valvuln-UP-04-vulnerable.json", "failure": None}}
    return tmp_path, record, ui


def check(records):
    root, record, ui = records
    manifest, ui_path = root / "manifest.json", root / "ui.json"
    manifest.write_text(json.dumps(record), encoding="utf-8")
    ui_path.write_text(json.dumps(ui), encoding="utf-8")
    return audit(root, [manifest], ui_path)


def test_complete_records_pass_without_product_imports_or_network(records):
    result = check(records)
    assert result["status"] == "PASS"
    assert result["conditions"] == 8 and result["screenshot_hash_checks"] == 18


@pytest.mark.parametrize("damage,expected", [
    ("source", "SOURCE_HASH_MISMATCH"), ("missing_condition", "INCOMPLETE_OR_DUPLICATE_CONDITIONS"),
    ("duplicate", "INCOMPLETE_OR_DUPLICATE_CONDITIONS"), ("png", "PNG_HASH_MISMATCH"),
    ("missing_png", "SCREENSHOTS_INCOMPLETE"), ("cleanup", "UNCLEAN_RECORDED_WORKER"),
    ("ui_run", "UI_RUN_MISMATCH"), ("path", "SOURCE_PATH_OUTSIDE_ROOT"),
    ("verdict", "RECORDED_VERDICT_MISMATCH"), ("export", "UI_EXPORT_INCOMPLETE"),
])
def test_damaged_records_fail_closed(records, damage, expected):
    root, record, ui = records
    if damage == "source":
        (root / "source.py").write_text("changed", encoding="utf-8")
    elif damage == "missing_condition":
        record["results"].pop()
    elif damage == "duplicate":
        record["results"].append(copy.deepcopy(record["results"][0]))
    elif damage == "png":
        record["results"][0]["probe"]["observations"][0]["screenshot_sha256"] = "0" * 64
    elif damage == "missing_png":
        record["results"][0]["probe"]["observations"][0] = {}
    elif damage == "cleanup":
        record["final_state"]["heartbeat"]["dirty"] = True
    elif damage == "ui_run":
        ui["run_id"] = "UP-01-vulnerable"
    elif damage == "path":
        record["source_sha256"]["../outside.py"] = "0" * 64
    elif damage == "verdict":
        record["results"][-1]["verdict"] = "CONFIRMED"
    elif damage == "export":
        ui["download"]["failure"] = "cancelled"
    result = check(records)
    assert result["status"] == "FAIL" and expected in result["errors"]


def test_missing_or_malformed_files_do_not_pass(tmp_path):
    manifest = tmp_path / "broken.json"
    manifest.write_text("[]", encoding="utf-8")
    result = audit(tmp_path, [manifest], tmp_path / "missing-ui.json")
    assert result["status"] == "FAIL"
    assert {"INVALID_MANIFEST", "INVALID_UI_RECORD"} <= set(result["errors"])
