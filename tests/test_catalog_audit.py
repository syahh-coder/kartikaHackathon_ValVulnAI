from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

from evaluator.catalog_audit import audit, main
from evaluator.development_history import DEVELOPMENT_HISTORY


CATALOG = Path(__file__).resolve().parents[1]/"evaluator/catalog.json"


def catalog():
    return json.loads(CATALOG.read_text(encoding="utf-8"))


def test_current_catalog_is_valid_but_incomplete_and_grouping_blocks_freeze():
    result = audit(catalog())
    assert result["status"] == "VALID" and result["recorded_reproduced"] == 13
    assert len(result["unreproduced_ids"]) == len(result["unknown_group_ids"]) == 11
    assert result["declared_catalog_ready"] is False and result["benchmark_ready"] is False
    assert result["development_evaluation_conflicts"] == [{"root_cause_group": "html-element-output", "development": ["UP-04"],
                                                           "evaluation": ["XSS-01", "XSS-02", "XSS-03", "XSS-04"]}]


@pytest.mark.parametrize("damage", ["duplicate", "missing", "wrong_category", "unknown_status", "missing_reference", "outside_doc", "bad_group", "allocation", "extra_field"])
def test_invalid_catalog_cannot_pass(damage):
    value = catalog()
    row = value["entries"][7]
    if damage == "duplicate":
        value["entries"][0] = deepcopy(row)
    elif damage == "missing":
        value["entries"].pop()
    elif damage == "wrong_category":
        row["category"] = "UPLOAD"
    elif damage == "unknown_status":
        row["status"] = "PASSED_INDUSTRY"
    elif damage == "missing_reference":
        row["verification_document"] = None
    elif damage == "outside_doc":
        row["verification_document"] = "docs/../../outside.md"
    elif damage == "bad_group":
        row["root_cause_group"] = "../other"
    elif damage == "allocation":
        row["allocation"] = "evaluation"
    elif damage == "extra_field":
        row["expected_verdict"] = "CONFIRMED"
    result = audit(value)
    assert result["status"] == "INVALID" and not result["declared_catalog_ready"]


def test_even_complete_synthetic_metadata_does_not_grant_benchmark_readiness():
    value = catalog()
    for row in value["entries"]:
        row.update(status="OPERATOR_REPRODUCED", root_cause_group=row["id"].lower(), verification_document="docs/synthetic.md")
    for point_id, group, document in DEVELOPMENT_HISTORY:
        next(row for row in value["entries"] if row["id"] == point_id)["root_cause_group"] = group
    result = audit(value)
    assert result["declared_catalog_ready"] is True
    assert result["benchmark_ready"] is False


def test_cli_require_ready_returns_blocking_exit_code(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["catalog_audit", "--require-ready"])
    with pytest.raises(SystemExit) as stopped:
        main()
    assert stopped.value.code == 2
    assert json.loads(capsys.readouterr().out)["recorded_reproduced"] == 13


def test_reallocation_cannot_erase_documented_development_history():
    value = catalog()
    # Complete synthetic metadata in memory isolates the history gate from
    # unrelated pending-point checks. Never write these statuses to the catalog.
    for row in value["entries"]:
        if row["status"] == "PLANNED":
            row.update(status="OPERATOR_REPRODUCED", root_cause_group=row["id"].lower(),
                       verification_document="docs/synthetic.md")
    by_id = {row["id"]: row for row in value["entries"]}
    by_id["UP-03"]["allocation"] = "development"
    by_id["UP-04"]["allocation"] = "non_benchmark"
    result = audit(value)
    assert result["status"] == "VALID"
    assert result["unreproduced_ids"] == result["unknown_group_ids"] == []
    assert result["development_evaluation_conflicts"] == []
    assert result["historical_development_evaluation_conflicts"] == [{
        "root_cause_group": "html-element-output", "development_history_ids": ["UP-04"],
        "evaluation": ["XSS-01", "XSS-02", "XSS-03", "XSS-04"]}]
    assert not result["declared_catalog_ready"] and not result["benchmark_ready"]


@pytest.mark.parametrize("new_group", ["different-upload-group", None])
def test_renaming_or_removing_a_group_cannot_erase_history(new_group):
    value = catalog()
    row = next(row for row in value["entries"] if row["id"] == "UP-04")
    row.update(status="PLANNED", root_cause_group=new_group)
    result = audit(value)
    assert result["status"] == "VALID"
    assert result["development_history_group_mismatches"] == [
        {"id": "UP-04", "recorded_group": "html-element-output", "current_group": new_group}]
    assert result["historical_development_evaluation_conflicts"]
    assert not result["declared_catalog_ready"]


def test_candidate_inventory_counts_areas_and_groups_without_selecting_a_split():
    value = catalog()
    unchanged = deepcopy(value)
    inventory = audit(value)["held_out_candidate_inventory"]
    assert value == unchanged
    assert inventory["XSS"] == {"target_area_count": 4, "recorded_unexposed_ids": ["XSS-06"],
                                "recorded_area_count": 1, "recorded_independent_group_count": 1,
                                "area_shortfall": 3}
    assert inventory["UPLOAD"]["recorded_unexposed_ids"] == ["UP-01", "UP-02", "UP-03"]
    assert inventory["UPLOAD"]["recorded_independent_group_count"] == 2
    assert inventory["BAC"]["area_shortfall"] == 4
    assert inventory["BUSINESS_LOGIC"]["area_shortfall"] == 1


def test_unknown_and_unreproduced_metadata_is_not_a_held_out_candidate():
    value = catalog()
    row = next(row for row in value["entries"] if row["id"] == "XSS-06")
    row.update(status="PLANNED", root_cause_group=None, verification_document=None)
    inventory = audit(value)["held_out_candidate_inventory"]
    assert inventory["XSS"]["recorded_unexposed_ids"] == []
    assert inventory["XSS"]["area_shortfall"] == 4


def test_candidate_that_becomes_development_is_removed_with_its_whole_group():
    value = catalog()
    by_id = {row["id"]: row for row in value["entries"]}
    by_id["UP-02"]["allocation"] = "development"
    by_id["UP-04"]["allocation"] = "non_benchmark"
    result = audit(value)
    assert result["held_out_candidate_inventory"]["UPLOAD"]["recorded_unexposed_ids"] == ["UP-03"]
    assert any(conflict["root_cause_group"] == "upload-active-content-origin"
               for conflict in result["development_evaluation_conflicts"])


@pytest.mark.parametrize("development", [False, True])
def test_total_allocation_counts_cannot_hide_wrong_category_counts(development):
    value = catalog()
    by_id = {row["id"]: row for row in value["entries"]}
    if development:
        by_id["UP-04"]["allocation"] = "non_benchmark"
        by_id["XSS-05"]["allocation"] = "development"
    else:
        by_id["UP-01"]["allocation"] = "non_benchmark"
        by_id["XSS-05"]["allocation"] = "evaluation"
    result = audit(value)
    assert result["status"] == "INVALID"
    assert result["errors"] == ["DEVELOPMENT_CATEGORY_COUNTS" if development else "EVALUATION_CATEGORY_COUNTS"]


def test_history_has_existing_document_references():
    root = CATALOG.parents[1]
    for point_id, group, document in DEVELOPMENT_HISTORY:
        assert (root / document).is_file()
        assert point_id in {"BAC-08", "XSS-08", "UP-04"}
