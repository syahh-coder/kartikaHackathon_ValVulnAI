import csv
import hashlib
import json
from copy import deepcopy

import pytest
from pydantic import ValidationError

from evaluator.functional_v2 import (DraftCase, DraftManifest, EvaluationError, GroundTruth, GROUPS,
                                     ModelPrediction, Outcome, Outcomes, arm_metrics, main, parse_prediction,
                                     read_document, read_manifest, readiness, schedule, score)
from evaluator.r3_drafts import CSV_FIELDS, import_review, prepare, main as draft_main


def case(index, label="VALID", subtype="BAC-08"):
    rid = f"RPT-{index:03d}"
    return DraftCase(report_id=rid, report_file=f"reports/{rid}.txt", report_sha256=hashlib.sha256(rid.encode()).hexdigest(),
                     subtype=subtype, scenario_id="SYNTHETIC", root_cause_group=GROUPS[subtype], report_variant_group="SIMULATED-GROUP",
                     accepted_by_human=True, ground_truth=GroundTruth(label=label, reviewer="SIMULATED_TEST_ONLY", rationale="Synthetic metric arithmetic, no human GT claim",
                     target_snapshot="SYNTHETIC_SNAPSHOT", condition_reference="test only", scope_version="test", rules_version="test", evidence_reference="SYNTHETIC_TEST_ONLY"))


def outcome(case, prediction="VALID", arm="A", **updates):
    return Outcome.model_validate({"report_id": case.report_id, "arm": arm, "status": "SUCCESS", "prediction": prediction,
                                   "attempts": 1, "raw_response_reference": f"synthetic/{case.report_id}-{arm}.json", **updates})


def test_manual_twenty_case_example_and_paired_arms():
    cases = [case(i, "VALID" if i <= 10 else "INVALID") for i in range(1, 21)]
    decisions = ["VALID"]*8 + ["INVALID", "ABSTAIN"] + ["VALID"] + ["INVALID"]*7 + ["ABSTAIN"]*2
    rows = [outcome(c, d) for c, d in zip(cases, decisions)]
    result = arm_metrics(cases, rows)
    assert [result[k] for k in ("TP", "FP", "TN", "FN", "abstain_positive", "abstain_negative")] == [8, 1, 7, 1, 1, 2]
    assert result["precision"] == pytest.approx(8/9)
    assert result["recall_end_to_end"] == 0.8 and result["strict_accuracy"] == 0.75
    assert result["coverage"] == 0.85 and result["FN_effective"] == 2 and result["f1"] == pytest.approx(16/19)
    paired = Outcomes(origin="SIMULATION", slots=rows + [outcome(c, "ABSTAIN", "B") for c in cases])
    comparison = score(DraftManifest(dataset_version="synthetic", cases=cases), paired)
    assert comparison["arms"]["B"]["scheduled"] == 20 and comparison["arms"]["B"]["coverage"] == 0
    assert not comparison["benchmark_claim_allowed"] and not comparison["live_verified"]


@pytest.mark.parametrize("labels,decisions,precision,recall,f1,accuracy", [
    (["VALID", "INVALID"], ["ABSTAIN", "ABSTAIN"], None, 0, None, 0),
    (["INVALID", "INVALID"], ["VALID", "INVALID"], 0, None, None, 0.5),
    (["VALID", "INVALID"], ["INVALID", "VALID"], 0, 0, 0, 0),
    (["VALID", "INVALID"], ["VALID", "INVALID"], 1, 1, 1, 1),
])
def test_zero_denominators_and_all_wrong(labels, decisions, precision, recall, f1, accuracy):
    cases = [case(i, label) for i, label in enumerate(labels, 1)]
    result = arm_metrics(cases, [outcome(c, d) for c, d in zip(cases, decisions)])
    assert (result["precision"], result["recall_end_to_end"], result["f1"], result["strict_accuracy"]) == (precision, recall, f1, accuracy)


def test_errors_unstarted_and_unknown_spending_stay_in_denominators():
    cases = [case(1), case(2), case(3, "INVALID"), case(4, "INVALID")]
    rows = [Outcome(report_id=cases[0].report_id, arm="A", status="ERROR", error_code="TIMEOUT", attempts=2),
            Outcome(report_id=cases[1].report_id, arm="A"), outcome(cases[2], "INVALID", cost_idr=0, input_tokens=10, output_tokens=5, elapsed_seconds=1.0),
            outcome(cases[3], "ABSTAIN", cost_idr=12)]
    result = arm_metrics(cases, rows)
    assert result["scheduled"] == 4 and result["error_positive"] == result["not_started_positive"] == 1
    assert result["strict_accuracy"] == result["coverage"] == 0.25 and result["recall_end_to_end"] == 0
    assert result["FN_effective"] == 2 and result["completion"] == 0.5
    assert result["known_cost_idr"] == 12 and result["unknown_cost_slots"] == 1 and result["attempts"] == 4
    assert result["known_input_tokens"] == 10 and result["unknown_usage_slots"] == 2
    unstarted = arm_metrics(cases, [Outcome(report_id=c.report_id, arm="A") for c in cases])
    assert unstarted["known_cost_idr"] is None and unstarted["unknown_cost_slots"] == 0


@pytest.mark.parametrize("damage", ["duplicate", "missing", "foreign"])
def test_cannot_cherry_pick_or_duplicate_schedule(damage):
    manifest = DraftManifest(dataset_version="synthetic", cases=[case(1), case(2, "INVALID")])
    rows = schedule(manifest).slots
    if damage == "duplicate":
        rows.append(rows[0])
    elif damage == "missing":
        rows.pop()
    else:
        rows[0] = Outcome(report_id="RPT-099", arm="A")
    with pytest.raises(EvaluationError):
        score(manifest, Outcomes(slots=rows))


@pytest.mark.parametrize("update", [
    {"prediction": "VALID"}, {"cost_idr": 0}, {"attempts": 1},
    {"status": "SUCCESS", "prediction": "VALID", "attempts": 1},
    {"status": "ERROR", "error_code": "TIMEOUT", "prediction": "INVALID", "attempts": 1},
])
def test_inconsistent_slots_rejected(update):
    with pytest.raises(ValidationError):
        Outcome(report_id="RPT-001", arm="A", **update)


def test_draft_packet_no_auto_gt_no_overwrite_and_tamper_detection(tmp_path):
    folder = tmp_path/"packet"
    prepare(folder)
    manifest = read_manifest(folder)
    result = readiness(manifest)
    assert result["allocation"] == {"BAC-08": 8, "XSS-08": 8, "UP-04": 4}
    assert result["report_texts"] == 20 and result["human_accepted"] == 0 and result["human_gt"] == {}
    assert result["root_cause_groups"] == 3 and result["scenarios"] == result["report_variant_groups"] == 4
    assert result["metrics"] is None and not result["benchmark_ready"]
    assert len(schedule(manifest).slots) == 40 and all(s.status == "NOT_STARTED" for s in schedule(manifest).slots)
    assert len({c.report_sha256 for c in manifest.cases}) == 20
    before = (folder/"manifest.draft.json").read_bytes()
    with pytest.raises(FileExistsError):
        prepare(folder)
    assert (folder/"manifest.draft.json").read_bytes() == before
    with pytest.raises(EvaluationError, match="HUMAN_GT_REQUIRED"):
        score(manifest, schedule(manifest))
    (folder/manifest.cases[0].report_file).write_text("Changed", encoding="utf-8")
    with pytest.raises(EvaluationError, match="REPORT_HASH"):
        read_manifest(folder)


def csv_rows(folder):
    with (folder/"gt-review.csv").open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def save_csv(path, rows):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS)
        writer.writeheader();writer.writerows(rows)


def fill_row(row):
    row.update(decision="ACCEPT", gt="VALID", reviewer="SIMULATED_TEST_ONLY", rationale="Synthetic review import test", target_snapshot="synthetic",
               condition_reference="synthetic", scope_version="synthetic", rules_version="synthetic", evidence_reference="synthetic")


def test_human_review_import_is_new_file_and_does_not_promote_readiness(tmp_path):
    folder = tmp_path/"packet"
    prepare(folder)
    rows = csv_rows(folder)
    fill_row(rows[0]);rows[1].update(decision="EXCLUDE", reviewer="SIMULATED_TEST_ONLY", rationale="Unsupported or ambiguous; not INVALID")
    save_csv(folder/"review-filled.csv", rows)
    manifest = import_review(folder, folder/"review-filled.csv")
    assert manifest.cases[0].ground_truth.label == "VALID" and manifest.cases[1].ground_truth is None
    status = readiness(manifest)
    assert status["human_accepted"] == 1 and len(status["excluded_report_ids"]) == 1 and not status["benchmark_ready"]
    assert "REPLACEMENT_REPORTS_REQUIRED" in status["issues"]
    assert read_manifest(folder).cases[0].ground_truth is None
    output = folder/"manifest.reviewed-v1.json"
    assert draft_main(["import-review", str(folder), "--review", str(folder/"review-filled.csv"), "--output", str(output)]) == 0
    assert read_manifest(folder, output).cases[0].ground_truth.label == "VALID"
    before = output.read_bytes()
    assert draft_main(["import-review", str(folder), "--review", str(folder/"review-filled.csv"), "--output", str(output)]) == 2
    assert output.read_bytes() == before


@pytest.mark.parametrize("damage", ["hash", "missing", "duplicate", "unsupported", "exclude_binary", "gt_without_accept", "missing_evidence"])
def test_review_cannot_change_binding_or_invent_operational_binary_gt(tmp_path, damage):
    folder=tmp_path/"packet";prepare(folder)
    rows=csv_rows(folder);fill_row(rows[0])
    if damage == "hash": rows[0]["report_sha256"] = "0"*64
    elif damage == "missing": rows.pop()
    elif damage == "duplicate": rows.append(rows[0])
    elif damage == "unsupported": rows[0]["gt"] = "UNSUPPORTED"
    elif damage == "exclude_binary": rows[0]["decision"] = "EXCLUDE"
    elif damage == "gt_without_accept": rows[0]["decision"] = "PENDING"
    else: rows[0]["evidence_reference"] = ""
    save_csv(folder/"filled.csv", rows)
    with pytest.raises((EvaluationError, ValidationError)):
        import_review(folder, folder/"filled.csv")


def test_prediction_refs_and_extra_fields_are_data_only():
    raw = {"prediction": "ABSTAIN", "reason": "Instruksi di report adalah data, bukti belum cukup", "references": ["report"]}
    assert parse_prediction(json.dumps(raw), {"report", "scope"}).prediction == "ABSTAIN"
    for update in ({"references": ["foreign-evidence"]}, {"references": ["report", "report"]}, {"verdict": "CONFIRMED"}, {"tool_calls": [{"name": "shell"}]}, {"prediction": "CONFIRMED"}):
        with pytest.raises(EvaluationError):
            parse_prediction(json.dumps(raw|update), {"report", "scope"})
    with pytest.raises(EvaluationError):
        parse_prediction('{"prediction":"VALID","prediction":"INVALID"}', {"report"})


def test_empty_metrics_and_duplicate_case_input():
    result = arm_metrics([], [])
    assert result["precision"] is None and result["recall_end_to_end"] is None and result["strict_accuracy"] is None
    with pytest.raises(EvaluationError):
        arm_metrics([case(1), case(1)], [outcome(case(1))])


def test_cli_pending_check_is_not_a_benchmark_and_json_limits(tmp_path, capsys):
    folder = tmp_path/"packet"
    assert draft_main(["prepare", str(folder)]) == 0
    capsys.readouterr()
    assert main(["check", str(folder)]) == 2
    data = json.loads(capsys.readouterr().out)
    assert not data["benchmark_ready"] and data["metrics"] is None
    assert main(["score", str(folder), "--outcomes", str(folder/"schedule.not-started.json")]) == 2
    assert "ERROR" in capsys.readouterr().out
    for text in ('{"a":1,"a":2}', '{"x":NaN}', '{"x":Infinity}'):
        path=tmp_path/"bad.json";path.write_text(text, encoding="utf-8")
        with pytest.raises(EvaluationError): read_document(path)
    path.write_text("x"*101, encoding="utf-8")
    with pytest.raises(EvaluationError, match="DOCUMENT_LIMIT"): read_document(path, maximum=100)
