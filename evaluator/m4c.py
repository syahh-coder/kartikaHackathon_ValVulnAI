"""Explicit operator reproduction of the seven remaining XSS points. No AI/GT."""
import base64
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from uuid import uuid4

from evaluator.m2 import cli, compose, operator, ready
from evaluator.m4 import browser_processes, lab_log
from evaluator.xss_cases import POINTS

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / "artifacts/m4c"


def catalog_manifest() -> dict:
    """Combine successful operator checks, retaining failed attempts separately."""
    latest, failed = {}, []
    lab_files = ("lab/main.py", "lab/xss_catalog.py", "lab/maintenance.py", "lab/migrations/002_xss_catalog.sql")
    current = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in lab_files}
    for path in sorted(DIRECTORY.glob("*-verification.json")):
        document = json.loads(path.read_text(encoding="utf-8"))
        if document["status"] != "PASS":
            failed.append(path.name)
        if any(document.get("source_sha256", {}).get(name) != digest for name, digest in current.items()):
            continue
        for result in document["results"]:
            if result["status"] == "PASS":
                latest[(result["point"], result["condition"])] = (path.name, result)
    points = []
    for point in POINTS:
        phases = {}
        for condition in ("vulnerable", "fixed"):
            found = latest.get((point, condition))
            if found:
                artifact, record = found
                phases[condition] = {"artifact": artifact, "run_id": record["run_id"], "snapshot_id": record["snapshot_id"],
                    "actual_requests": record["actual_requests"],
                    "evidence_ids": [o["evidence_id"] for o in record["observations"]]}
        points.append({"point": point, "status": "OPERATOR-REPRODUCED" if len(phases) == 2 else "INCOMPLETE",
            "root_cause_group": "html-element-output" if point in POINTS[:5] else
                "html-attribute-output" if point == "XSS-06" else "dom-fragment-innerhtml",
            "phases": phases, "human_dataset_gt": "PENDING"})
    manifest = {"source": "operator checks; not product assessments or benchmark", "source_sha256": current,
        "complete": all(p["status"] == "OPERATOR-REPRODUCED" for p in points), "points": points, "failed_attempts": failed}
    (DIRECTORY / "catalog-manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def reproduce(points: tuple[str, ...] = POINTS) -> None:
    DIRECTORY.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = {"status": "RUNNING", "source": "operator reproduction; not model or human dataset GT",
        "model_calls": 0, "results": [], "started_at": stamp, "points_requested": list(points),
        "source_sha256": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in (
            "lab/main.py", "lab/xss_catalog.py", "lab/maintenance.py", "lab/migrations/002_xss_catalog.sql",
            "evaluator/m4c.py", "evaluator/m4c_probe.py", "evaluator/xss_cases.py")}}
    maintenance = False
    try:
        ready()
        operator("maintenance_enter")
        maintenance = True
        output["images"] = json.loads(compose("images", "--format", "json"))
        # The runtime worker image contains neither this mapping nor this probe script.
        mapping = (ROOT / "evaluator/xss_cases.py").read_text(encoding="utf-8")
        script = (ROOT / "evaluator/m4c_probe.py").read_text(encoding="utf-8").replace(
            "    # CASE_SOURCE is inserted from the repository-owned mapping by the host runner.",
            "    # Repository-owned operator mapping, no labels or condition included.")
        script = mapping + "\n" + script
        for point in points:
            for condition in ("vulnerable", "fixed"):
                snapshot = cli("lab", "lab.maintenance", "reset", "--condition", "fixed",
                    "--xss-point", point, "--point-condition", condition)
                config = {"point": point, "snapshot_id": snapshot["snapshot_id"],
                    "objects": snapshot["objects"], "run_id": str(uuid4())}
                response = json.loads(compose("exec", "-T", "--user", "10001:10001", "worker", "python", "-",
                    json.dumps(config), input=script))
                observations = response["observations"]
                record = {"point": point, "condition": condition, "run_id": config["run_id"],
                    "snapshot_id": snapshot["snapshot_id"], "observations": observations, "status": "CHECKING",
                    "probe_status": response["status"], "probe_error_type": response.get("error_type"),
                    "diagnostics": response.get("diagnostics")}
                output["results"].append(record)
                # Save all raw observations before assertions; failures remain reviewable.
                raw_file = DIRECTORY / f"{stamp}-{point}-{condition}.json"
                raw_file.write_text(json.dumps(record, indent=2), encoding="utf-8")
                assert response["status"] == "PASS", response.get("error_type")
                assert [o["kind"] for o in observations] == ["inert", "marker", "safe"]
                for obs in observations:
                    assert obs["run_id"] == config["run_id"] and obs["snapshot_id"] == snapshot["snapshot_id"]
                    assert obs["js_control"] and obs["initial_storage_empty"] and obs["counters"]["documents"] == 1
                    assert obs["response"]["status"] == 200
                    png = base64.b64decode(obs["screenshot_base64"], validate=True)
                    assert png.startswith(b"\x89PNG\r\n\x1a\n") and hashlib.sha256(png).hexdigest() == obs["screenshot_sha256"]
                    (DIRECTORY / (obs["evidence_id"] + ".png")).write_bytes(png)
                    if obs["writes"]:
                        assert obs["writer"]["actor_alias"] == "requester-a" and obs["reader"]["actor_alias"] == "requester-b"
                        assert obs["writer"]["user_id"] != obs["reader"]["user_id"]
                inert, marker, safe = observations
                assert inert["payload_visible_as_text"] and not inert["marker_events"]
                assert safe["payload_visible_as_text"] and not safe["marker_events"]
                if condition == "vulnerable":
                    assert len(marker["marker_events"]) == 1
                    event = marker["marker_events"][0]
                    assert event["nonce"] == marker["nonce"] and event["origin"] == "http://lab:8001"
                    assert event["frame"] == "main" and event["path"] == marker["path"]
                else:
                    assert marker["payload_visible_as_text"] and not marker["marker_events"]
                assert len({o["nonce"] for o in observations}) == 3
                log = lab_log()
                # Each fixture: optional writer login + writes; reader login + one document.
                expected_requests = sum(2 + (1 + len(o["writes"]) if o["writes"] else 0) for o in observations)
                assert sum(row[2] for row in log) == expected_requests
                assert not browser_processes()
                record.update(status="PASS", actual_requests=expected_requests, access_log=log)
                raw_file.write_text(json.dumps(record, indent=2), encoding="utf-8")
                print(json.dumps({"point": point, "condition": condition, "status": "PASS", "requests": expected_requests}), flush=True)
        output["status"] = "PASS"
    except BaseException as exc:
        output.update(status="FAILED", error_type=type(exc).__name__)
        raise
    finally:
        try:
            if maintenance:
                if browser_processes():
                    raise RuntimeError("Browser still running; keep target in maintenance")
                snapshot = cli("lab", "lab.maintenance", "reset", "--condition", "fixed")
                operator("maintenance_release", {"snapshot_id": snapshot["snapshot_id"]})
                output["final_state"] = {"snapshot_id": snapshot["snapshot_id"], "all_conditions": "fixed",
                    "heartbeat": operator("heartbeat"), "browser_processes": browser_processes(), "access_log": lab_log()}
        except BaseException as exc:
            output.update(status="FAILED", cleanup_error_type=type(exc).__name__)
            print("Cleanup failed; target remains unavailable for review", file=sys.stderr)
        output["finished_at"] = datetime.now(timezone.utc).isoformat()
        text = json.dumps(output, indent=2)
        (DIRECTORY / f"{stamp}-verification.json").write_text(text, encoding="utf-8")
        (DIRECTORY / "verification.json").write_text(text, encoding="utf-8")
        catalog_manifest()
    if output["status"] != "PASS":
        raise RuntimeError("Operator reproduction incomplete")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--point", choices=POINTS, action="append", help="Recheck only selected points, without discarding earlier artifacts")
    args = parser.parse_args()
    reproduce(tuple(args.point) if args.point else POINTS)
