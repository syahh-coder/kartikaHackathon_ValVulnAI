"""Offline integrity audit of existing M5 records; never contacts the app or lab.

This checks recorded evidence, not reproduction, ground truth or live model quality.
Pass explicit timestamped manifests so partial reruns cannot hide older results.
"""
import argparse
import base64
from collections import Counter
import hashlib
import json
from pathlib import Path


MAX_RECORD_BYTES = 16 * 1024 * 1024
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def read_record(path: Path) -> dict:
    if path.stat().st_size > MAX_RECORD_BYTES:
        raise ValueError("RECORD_TOO_LARGE")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("RECORD_NOT_OBJECT")
    return value


def audit(root: Path, manifests: list[Path], ui_record: Path) -> dict:
    root = root.resolve()
    errors, cases, run_ids, ui_run_ids = [], Counter(), set(), set()
    screenshots = source_files = 0

    def require(condition: bool, code: str):
        if not condition:
            errors.append(code)

    def captures(value):
        nonlocal screenshots
        if isinstance(value, dict):
            if "screenshot_base64" in value:
                raw = base64.b64decode(value["screenshot_base64"], validate=True)
                require(raw.startswith(PNG_SIGNATURE), "INVALID_PNG")
                require(hashlib.sha256(raw).hexdigest() == value.get("screenshot_sha256"), "PNG_HASH_MISMATCH")
                screenshots += 1
            for key, child in value.items():
                if key == "body" and isinstance(child, str):
                    try:
                        child = json.loads(child)
                    except ValueError:
                        continue
                captures(child)
        elif isinstance(value, list):
            for child in value:
                captures(child)

    for path in manifests:
        try:
            record = read_record(path)
            require(record.get("status") == "PASS", "MANIFEST_NOT_PASS")
            sources = record.get("source_sha256")
            require(isinstance(sources, dict) and bool(sources), "MISSING_SOURCE_HASHES")
            for name, expected in (sources or {}).items():
                relative = Path(name.replace("\\", "/"))
                target = (root / relative).resolve()
                if relative.is_absolute() or not target.is_relative_to(root):
                    errors.append("SOURCE_PATH_OUTSIDE_ROOT")
                    continue
                source_files += 1
                require(target.is_file() and hashlib.sha256(target.read_bytes()).hexdigest() == expected, "SOURCE_HASH_MISMATCH")
            final = record["final_state"]
            heartbeat = final["heartbeat"]
            require(heartbeat.get("status") == "IDLE" and heartbeat.get("dirty") is False
                    and heartbeat.get("active_run_id") is None and heartbeat.get("dirty_run_id") is None
                    and bool(heartbeat.get("snapshot_id")), "UNCLEAN_RECORDED_WORKER")
            require(final.get("browser_processes") == [] and final.get("access_log") == [], "UNCLEAN_RECORDED_TARGET")
            results = record["results"]
            require(set(record["points"]) == {r["point"] for r in results}, "POINT_LIST_MISMATCH")
            for result in results:
                pair = (result["point"], result["condition"])
                cases[pair] += 1
                require(result.get("status") == "PASS", "CASE_NOT_PASS")
                require(result["run_id"] not in run_ids, "DUPLICATE_RUN")
                run_ids.add(result["run_id"])
                if result["point"] == "UP-04":
                    if result["condition"] == "vulnerable":
                        ui_run_ids.add(result["run_id"])
                    private = result["private_run"]
                    require(private.get("run_id") == result["run_id"] and private.get("process_status") == "COMPLETED", "PRODUCT_RUN_MISMATCH")
                    require(private.get("execution_mode") == "mock" and private.get("inference_provider") == "mock", "UNEXPECTED_MODEL_MODE")
                    expected = "CONFIRMED" if result["condition"] == "vulnerable" else "REFUTED"
                    require(result.get("verdict") == expected and private["assessment"]["system_verified"]["verdict"] == expected, "RECORDED_VERDICT_MISMATCH")
                    require(result.get("publication_export") == "PASS", "PUBLICATION_NOT_PASS")
                    require(len(result["evidence"]) == 5 and private["counters"]["target_requests"] == 10, "PRODUCT_EVIDENCE_INCOMPLETE")
                else:
                    require(result["probe"].get("status") == "PASS" and bool(result["probe"].get("observations")), "OPERATOR_EVIDENCE_INCOMPLETE")
            captures(results)
        except (OSError, ValueError, KeyError, TypeError, AttributeError, RecursionError):
            errors.append("INVALID_MANIFEST")

    expected_cases = Counter({(f"UP-{i:02d}", condition): 1 for i in range(1, 5) for condition in ("vulnerable", "fixed")})
    require(cases == expected_cases, "INCOMPLETE_OR_DUPLICATE_CONDITIONS")
    require(screenshots == 18, "SCREENSHOTS_INCOMPLETE")
    try:
        ui = read_record(ui_record)
        require(ui.get("status") == "PASS" and ui.get("run_id") in ui_run_ids, "UI_RUN_MISMATCH")
        require(ui.get("new_runs") == 0 and ui.get("target_requests") == 0
                and ui.get("page_errors") == [] and ui.get("external_requests") == [], "UI_NOT_CLEAN")
        require(all(ui.get(k) == "PASS" for k in ("upload_form_and_switch", "inert_evidence", "private_projection_export")), "UI_CHECK_INCOMPLETE")
        require(set(ui.get("viewports", [])) == {1366, 1024, 768, 390, 360}, "UI_VIEWPORTS_INCOMPLETE")
        require(ui.get("download", {}).get("filename") == f"valvuln-{ui.get('run_id')}.json"
                and ui["download"].get("failure") is None, "UI_EXPORT_INCOMPLETE")
    except (OSError, ValueError, KeyError, TypeError):
        errors.append("INVALID_UI_RECORD")
    return {"status": "FAIL" if errors else "PASS", "mode": "offline recorded-evidence integrity only",
            "manifests": len(manifests), "conditions": sum(cases.values()), "source_hash_checks": source_files,
            "screenshot_hash_checks": screenshots, "errors": sorted(set(errors))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifests", nargs="+", type=Path)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--ui-record", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.root, args.manifests, args.ui_record)
    print(json.dumps(result, indent=2))
    raise SystemExit(result["status"] != "PASS")


if __name__ == "__main__":
    main()
