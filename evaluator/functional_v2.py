"""Offline functional-v2 preparation/scoring. No provider, target or reset imports."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

PROTOCOL = "functional-v2"
GROUPS = {"BAC-08": "attachment-delete-owner-check", "XSS-08": "dom-fragment-innerhtml", "UP-04": "html-element-output"}
TARGET = {"BAC-08": 8, "XSS-08": 8, "UP-04": 4}


class EvaluationError(ValueError):
    pass


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class GroundTruth(Strict):
    label: Literal["VALID", "INVALID"]
    reviewer: str = Field(min_length=1, max_length=100)
    rationale: str = Field(min_length=1, max_length=2000)
    target_snapshot: str = Field(min_length=1, max_length=200)
    condition_reference: str = Field(min_length=1, max_length=500)
    scope_version: str = Field(min_length=1, max_length=200)
    rules_version: str = Field(min_length=1, max_length=200)
    evidence_reference: str = Field(min_length=1, max_length=1000)

    @model_validator(mode="after")
    def nonblank(self):
        if any(not value.strip() for value in self.model_dump().values()):
            raise ValueError("Ground truth fields cannot be blank")
        return self


class DraftCase(Strict):
    report_id: str = Field(pattern=r"^RPT-[0-9]{3}$")
    report_file: str = Field(pattern=r"^reports/RPT-[0-9]{3}\.txt$")
    report_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    subtype: Literal["BAC-08", "XSS-08", "UP-04"]
    scenario_id: str = Field(min_length=1, max_length=100)
    root_cause_group: str = Field(min_length=1, max_length=100)
    report_variant_group: str = Field(min_length=1, max_length=100)
    accepted_by_human: bool = False
    exclusion_reason: str | None = Field(default=None, min_length=1, max_length=2000)
    ground_truth: GroundTruth | None = None

    @model_validator(mode="after")
    def binding(self):
        if self.report_file != f"reports/{self.report_id}.txt" or self.root_cause_group != GROUPS[self.subtype]:
            raise ValueError("Report/group binding differs")
        if self.ground_truth is not None and not self.accepted_by_human:
            raise ValueError("GT requires an accepted report")
        if self.exclusion_reason is not None and (self.accepted_by_human or self.ground_truth is not None):
            raise ValueError("Excluded report cannot have binary GT")
        return self


class DraftManifest(Strict):
    protocol: Literal["functional-v2"] = PROTOCOL
    status: Literal["DRAFT_NOT_FROZEN"] = "DRAFT_NOT_FROZEN"
    dataset_version: str = Field(min_length=1, max_length=80)
    cases: list[DraftCase] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def unique(self):
        if len({c.report_id for c in self.cases}) != len(self.cases):
            raise ValueError("Duplicate report ID")
        if len({c.report_sha256 for c in self.cases}) != len(self.cases):
            raise ValueError("Duplicate report text")
        return self


class ModelPrediction(Strict):
    prediction: Literal["VALID", "INVALID", "ABSTAIN"]
    reason: str = Field(min_length=1, max_length=2000)
    references: list[str] = Field(min_length=1, max_length=40)


def parse_prediction(raw: str, allowed_references: set[str]) -> ModelPrediction:
    if len(raw.encode("utf-8")) > 32_000:
        raise EvaluationError("PREDICTION_LIMIT")
    try:
        result = ModelPrediction.model_validate(parse_json(raw))
        if len(set(result.references)) != len(result.references) or not set(result.references) <= allowed_references:
            raise ValueError("Unknown or duplicate reference")
        if not result.reason.strip():
            raise ValueError("Blank reason")
        return result
    except (ValueError, TypeError, RecursionError):
        raise EvaluationError("PREDICTION_SCHEMA_OR_REFERENCE") from None


class Outcome(Strict):
    report_id: str = Field(pattern=r"^RPT-[0-9]{3}$")
    arm: Literal["A", "B"]
    status: Literal["SUCCESS", "ERROR", "NOT_STARTED"] = "NOT_STARTED"
    prediction: Literal["VALID", "INVALID", "ABSTAIN"] | None = None
    error_code: str | None = Field(default=None, max_length=100)
    attempts: int = Field(default=0, ge=0, le=2)
    cost_idr: int | None = Field(default=None, ge=0)
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    elapsed_seconds: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    raw_response_reference: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def consistent(self):
        if self.status == "NOT_STARTED":
            if (self.prediction is not None or self.error_code is not None or self.attempts != 0 or
                    any(x is not None for x in (self.cost_idr, self.input_tokens, self.output_tokens,
                                               self.elapsed_seconds, self.raw_response_reference))):
                raise ValueError("Unstarted slot cannot contain results or fake zero cost")
        elif self.attempts == 0:
            raise ValueError("Started slot requires attempt count")
        elif self.status == "SUCCESS":
            if self.prediction is None or self.error_code is not None or not self.raw_response_reference:
                raise ValueError("Success requires prediction and original output reference")
        elif self.prediction is not None or not self.error_code:
            raise ValueError("Error cannot contain a prediction")
        return self


class Outcomes(Strict):
    protocol: Literal["functional-v2"] = PROTOCOL
    origin: Literal["UNVERIFIED_IMPORTED_RECORDS", "SIMULATION"] = "UNVERIFIED_IMPORTED_RECORDS"
    slots: list[Outcome] = Field(max_length=200)


def parse_json(text: str):
    def pairs(values):
        result = {}
        for key, value in values:
            if key in result:
                raise ValueError("Duplicate key")
            result[key] = value
        return result
    def constant(_):
        raise ValueError("Non-finite constant")
    return json.loads(text, object_pairs_hook=pairs, parse_constant=constant)


def read_document(path: Path, maximum: int = 1_048_576):
    with path.open("rb") as stream:
        raw = stream.read(maximum + 1)
    if len(raw) > maximum:
        raise EvaluationError("DOCUMENT_LIMIT")
    try:
        return parse_json(raw.decode("utf-8"))
    except (ValueError, UnicodeError, RecursionError):
        raise EvaluationError("DOCUMENT_JSON_INVALID") from None


def read_manifest(packet: Path, manifest_path: Path | None = None) -> DraftManifest:
    manifest_path = manifest_path or packet / "manifest.draft.json"
    if manifest_path.is_symlink() or not manifest_path.resolve().is_relative_to(packet.resolve()):
        raise EvaluationError("MANIFEST_PATH_INVALID")
    manifest = DraftManifest.model_validate(read_document(manifest_path))
    for case in manifest.cases:
        path = packet / case.report_file
        if path.is_symlink() or not path.resolve().is_relative_to(packet.resolve()):
            raise EvaluationError("REPORT_PATH_INVALID")
        with path.open("rb") as stream:
            raw = stream.read(32_001)
        if len(raw) > 32_000 or not raw.strip() or hashlib.sha256(raw).hexdigest() != case.report_sha256:
            raise EvaluationError("REPORT_HASH_OR_SIZE")
    return manifest


def readiness(manifest: DraftManifest) -> dict:
    counts = Counter(c.subtype for c in manifest.cases)
    labels = Counter(c.ground_truth.label for c in manifest.cases if c.ground_truth)
    per_subtype = {s: dict(Counter(c.ground_truth.label for c in manifest.cases if c.subtype == s and c.ground_truth)) for s in TARGET}
    excluded = [c.report_id for c in manifest.cases if c.exclusion_reason is not None]
    pending = [c.report_id for c in manifest.cases if c.report_id not in excluded and (not c.accepted_by_human or c.ground_truth is None)]
    issues = []
    if dict(counts) != TARGET:
        issues.append("REPORT_ALLOCATION_REQUIRED")
    if pending:
        issues.append("HUMAN_REPORT_ACCEPTANCE_AND_GT_REQUIRED")
    if excluded:
        issues.append("REPLACEMENT_REPORTS_REQUIRED")
    if not pending and (labels != Counter(VALID=10, INVALID=10) or any(
            per_subtype[s].get("VALID", 0) != n//2 or per_subtype[s].get("INVALID", 0) != n//2 for s, n in TARGET.items())):
        issues.append("HUMAN_GT_BALANCE_DIFFERS_FROM_TARGET")
    # A populated worksheet is not evidence binding, freeze, provider verification or a benchmark.
    return {"protocol": PROTOCOL, "status": "PREPARATION_ONLY", "report_texts": len(manifest.cases),
            "allocation": dict(counts), "human_accepted": sum(c.accepted_by_human for c in manifest.cases),
            "human_gt": dict(labels), "pending_report_ids": pending, "issues": issues,
            "excluded_report_ids": excluded,
            "root_cause_groups": len({c.root_cause_group for c in manifest.cases}),
            "scenarios": len({c.scenario_id for c in manifest.cases}),
            "report_variant_groups": len({c.report_variant_group for c in manifest.cases}),
            "gt_worksheet_complete": not issues, "benchmark_ready": False,
            "remaining_benchmark_requirements": ["CASE_BOUND_REDACTED_EVIDENCE_B", "PRIVATE_FREEZE",
                                                 "LIVE_MODEL_AND_SHARED_LEDGER"],
            "metrics": None}


def schedule(manifest: DraftManifest) -> Outcomes:
    return Outcomes(slots=[Outcome(report_id=c.report_id, arm=a) for c in manifest.cases for a in ("A", "B")])


def arm_metrics(cases: list[DraftCase], rows: list[Outcome]) -> dict:
    lookup = {r.report_id: r for r in rows}
    if len({c.report_id for c in cases}) != len(cases) or len(lookup) != len(rows) or set(lookup) != {c.report_id for c in cases}:
        raise EvaluationError("SCHEDULE_MISMATCH")
    if any(c.ground_truth is None or not c.accepted_by_human for c in cases):
        raise EvaluationError("HUMAN_GT_REQUIRED")
    count = Counter(TP=0, FP=0, TN=0, FN=0, abstain_positive=0, abstain_negative=0,
                    error_positive=0, error_negative=0, not_started_positive=0, not_started_negative=0)
    for case in cases:
        row = lookup[case.report_id]
        positive = case.ground_truth.label == "VALID"
        suffix = "positive" if positive else "negative"
        if row.status == "NOT_STARTED":
            count["not_started_" + suffix] += 1
        elif row.status == "ERROR":
            count["error_" + suffix] += 1
        elif row.prediction == "ABSTAIN":
            count["abstain_" + suffix] += 1
        else:
            count[("TP" if positive else "FP") if row.prediction == "VALID" else ("FN" if positive else "TN")] += 1
    n, positive_n = len(cases), sum(c.ground_truth.label == "VALID" for c in cases)
    tp, fp, tn, fn = (count[k] for k in ("TP", "FP", "TN", "FN"))
    def ratio(a, b):
        return a/b if b else None
    precision, recall = ratio(tp, tp+fp), ratio(tp, positive_n)
    f1 = None if precision is None or recall is None else (2*precision*recall/(precision+recall) if precision+recall else 0.0)
    started = sum(r.status != "NOT_STARTED" for r in rows)
    success = sum(r.status == "SUCCESS" for r in rows)
    known = [r.cost_idr for r in rows if r.status != "NOT_STARTED" and r.cost_idr is not None]
    token_rows = [r for r in rows if r.status != "NOT_STARTED"]
    return {**dict(count), "scheduled": n, "gt_positive": positive_n, "gt_negative": n-positive_n,
            "FN_effective": positive_n-tp, "precision": precision, "recall_end_to_end": recall,
            "strict_accuracy": ratio(tp+tn, n), "coverage": ratio(tp+fp+tn+fn, n), "f1": f1,
            "started": started, "successful_responses": success, "completion": ratio(success, n),
            "attempts": sum(r.attempts for r in rows), "known_cost_idr": sum(known) if known else None,
            "unknown_cost_slots": sum(r.status != "NOT_STARTED" and r.cost_idr is None for r in rows),
            "known_input_tokens": sum(r.input_tokens for r in token_rows if r.input_tokens is not None) if any(r.input_tokens is not None for r in token_rows) else None,
            "known_output_tokens": sum(r.output_tokens for r in token_rows if r.output_tokens is not None) if any(r.output_tokens is not None for r in token_rows) else None,
            "unknown_usage_slots": sum(r.input_tokens is None or r.output_tokens is None for r in token_rows),
            "known_elapsed_seconds": sum(r.elapsed_seconds for r in token_rows if r.elapsed_seconds is not None) if any(r.elapsed_seconds is not None for r in token_rows) else None}


def score(manifest: DraftManifest, outcomes: Outcomes) -> dict:
    if len({(r.report_id, r.arm) for r in outcomes.slots}) != len(outcomes.slots):
        raise EvaluationError("DUPLICATE_SLOT")
    expected = {(c.report_id, a) for c in manifest.cases for a in ("A", "B")}
    if {(r.report_id, r.arm) for r in outcomes.slots} != expected:
        raise EvaluationError("SCHEDULE_MISMATCH")
    return {"protocol": PROTOCOL, "status": "OFFLINE_RECORD_SCORING", "origin": outcomes.origin,
            "benchmark_claim_allowed": False, "live_verified": False,
            "notes": "Imported records only; no attestation of human labels, evidence origin, provider or billing. Never drops scheduled slots.",
            "arms": {a: arm_metrics(manifest.cases, [r for r in outcomes.slots if r.arm == a]) for a in ("A", "B")},
            "groups": {"root_cause_groups": len({c.root_cause_group for c in manifest.cases}),
                       "report_variant_groups": len({c.report_variant_group for c in manifest.cases})}}


def write_new(path: Path, value: dict):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["check", "schedule", "score"])
    parser.add_argument("packet", type=Path)
    parser.add_argument("--outcomes", type=Path)
    parser.add_argument("--manifest", type=Path, help="Explicit reviewed manifest inside the packet; original draft is preserved")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        manifest = read_manifest(args.packet, args.manifest)
        if args.operation == "check":
            result = readiness(manifest)
        elif args.operation == "schedule":
            result = schedule(manifest).model_dump()
        else:
            if not args.outcomes:
                raise EvaluationError("OUTCOMES_REQUIRED")
            result = score(manifest, Outcomes.model_validate(read_document(args.outcomes)))
        if args.output:
            write_new(args.output, result)
        else:
            print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        return 2 if args.operation == "check" and not result["gt_worksheet_complete"] else 0
    except (ValueError, TypeError, OSError):
        print(json.dumps({"status": "ERROR", "error_code": "EVALUATION_INPUT_OR_OUTPUT_INVALID"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
