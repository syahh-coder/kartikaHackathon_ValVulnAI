"""Offline catalog metadata lint; no target/model access or exploit execution.

Recorded statuses are declarations linked to earlier review documents. A valid
catalog is not fresh evidence, GT, benchmark readiness or permission to act.
"""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import re

from evaluator.development_history import DEVELOPMENT_HISTORY, EVALUATION_AREAS, HISTORY_VERSION


EXPECTED = {f"{prefix}-{i:02d}": category for prefix, count, category in
            (("BAC", 8, "BAC"), ("XSS", 8, "XSS"), ("UP", 4, "UPLOAD"), ("BL", 4, "BUSINESS_LOGIC")) for i in range(1, count+1)}
FIELDS = {"id", "category", "allocation", "status", "root_cause_group", "verification_document"}
STATUSES = {"PLANNED", "IMPLEMENTED", "OPERATOR_REPRODUCED", "MANUALLY_VERIFIED"}
REPRODUCED = {"OPERATOR_REPRODUCED", "MANUALLY_VERIFIED"}


def _review_history(rows: list[dict]) -> dict:
    by_id = {row["id"]: row for row in rows}
    history_groups = defaultdict(list)
    for point_id, group, document in DEVELOPMENT_HISTORY:
        history_groups[group].append(point_id)
    historical_conflicts = [
        {"root_cause_group": group, "development_history_ids": sorted(point_ids),
         "evaluation": sorted(row["id"] for row in rows
                              if row["allocation"] == "evaluation" and row["root_cause_group"] == group)}
        for group, point_ids in sorted(history_groups.items())
        if any(row["allocation"] == "evaluation" and row["root_cause_group"] == group for row in rows)
    ]
    mismatches = [{"id": point_id, "recorded_group": group,
                   "current_group": by_id[point_id]["root_cause_group"]}
                  for point_id, group, document in DEVELOPMENT_HISTORY
                  if by_id[point_id]["root_cause_group"] != group]
    exposed_groups = set(history_groups) | {row["root_cause_group"] for row in rows
                                           if row["allocation"] == "development" and row["root_cause_group"]}
    mismatched_ids = {row["id"] for row in mismatches}
    inventory = {}
    for category, target in EVALUATION_AREAS.items():
        candidates = [row for row in rows if row["category"] == category and row["status"] in REPRODUCED
                      and row["root_cause_group"] and row["root_cause_group"] not in exposed_groups
                      and row["id"] not in mismatched_ids]
        inventory[category] = {
            "target_area_count": target, "recorded_unexposed_ids": sorted(row["id"] for row in candidates),
            "recorded_area_count": len(candidates),
            "recorded_independent_group_count": len({row["root_cause_group"] for row in candidates}),
            "area_shortfall": max(0, target - len(candidates)),
        }
    return {"development_history_version": HISTORY_VERSION,
            "historical_development_evaluation_conflicts": historical_conflicts,
            "development_history_group_mismatches": mismatches,
            "held_out_candidate_inventory": inventory}


def audit(catalog: dict) -> dict:
    errors = []
    try:
        if set(catalog) != {"schema_version", "notes", "entries"} or catalog["schema_version"] != 1:
            raise ValueError("CATALOG_SCHEMA")
        rows = catalog["entries"]
        if not isinstance(rows, list) or len(rows) != 24:
            raise ValueError("CATALOG_SIZE")
        for row in rows:
            if set(row) != FIELDS or row["id"] not in EXPECTED or row["category"] != EXPECTED[row["id"]]:
                raise ValueError("ENTRY_SCHEMA")
            if row["status"] not in STATUSES or row["allocation"] not in {"development", "evaluation", "non_benchmark"}:
                raise ValueError("ENTRY_STATUS_OR_ALLOCATION")
            group, doc = row["root_cause_group"], row["verification_document"]
            if group is not None and not re.fullmatch(r"[a-z0-9-]{1,80}", group):
                raise ValueError("GROUP_SCHEMA")
            if doc is not None and not re.fullmatch(r"docs/[a-z0-9-]+\.md", doc):
                raise ValueError("DOCUMENT_SCHEMA")
            if row["status"] in REPRODUCED and (not group or not doc):
                raise ValueError("REPRODUCED_WITHOUT_REFERENCE")
        if Counter(r["id"] for r in rows) != Counter(EXPECTED.keys()):
            raise ValueError("DUPLICATE_OR_MISSING_ID")
        if Counter(r["allocation"] for r in rows) != {"development": 4, "evaluation": 10, "non_benchmark": 10}:
            raise ValueError("ALLOCATION_COUNTS")
        if Counter(r["category"] for r in rows if r["allocation"] == "evaluation") != EVALUATION_AREAS:
            raise ValueError("EVALUATION_CATEGORY_COUNTS")
        if Counter(r["category"] for r in rows if r["allocation"] == "development") != dict.fromkeys(EVALUATION_AREAS, 1):
            raise ValueError("DEVELOPMENT_CATEGORY_COUNTS")
    except (ValueError, KeyError, TypeError) as error:
        errors.append(str(error) if isinstance(error, ValueError) else "CATALOG_SCHEMA")
        return {"status": "INVALID", "errors": errors, "declared_catalog_ready": False, "benchmark_ready": False}
    groups = defaultdict(list)
    for row in rows:
        if row["root_cause_group"]:
            groups[row["root_cause_group"]].append(row)
    conflicts = [{"root_cause_group": group, "development": sorted(r["id"] for r in members if r["allocation"] == "development"),
                  "evaluation": sorted(r["id"] for r in members if r["allocation"] == "evaluation")}
                 for group, members in sorted(groups.items())
                 if {"development", "evaluation"} <= {r["allocation"] for r in members}]
    pending = sorted(r["id"] for r in rows if r["status"] not in REPRODUCED)
    unknown = sorted(r["id"] for r in rows if r["root_cause_group"] is None)
    history = _review_history(rows)
    return {"status": "VALID", "errors": [], "total": len(rows), "declared_status_counts": dict(Counter(r["status"] for r in rows)),
            "recorded_reproduced": len(rows)-len(pending), "unreproduced_ids": pending, "unknown_group_ids": unknown,
            "development_evaluation_conflicts": conflicts, **history,
            "declared_catalog_ready": not pending and not unknown and not conflicts
                and not history["historical_development_evaluation_conflicts"]
                and not history["development_history_group_mismatches"],
            "benchmark_ready": False,
            "limitations": "Metadata and documented system-development history only; not live-model exposure, human GT, fresh evidence or benchmark readiness. Candidate IDs do not revise allocations or select reports."}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=Path(__file__).with_name("catalog.json"))
    parser.add_argument("--require-ready", action="store_true")
    args = parser.parse_args()
    try:
        if args.catalog.stat().st_size > 1048576:
            raise ValueError("Catalog too large")
        result = audit(json.loads(args.catalog.read_text(encoding="utf-8")))
    except (OSError, ValueError):
        result = {"status": "INVALID", "errors": ["CATALOG_READ_ERROR"], "declared_catalog_ready": False, "benchmark_ready": False}
    print(json.dumps(result, indent=2))
    raise SystemExit(1 if result["status"] == "INVALID" else 2 if args.require_ready and not result["declared_catalog_ready"] else 0)


if __name__ == "__main__":
    main()
