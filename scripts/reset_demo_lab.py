"""Explicit operator reset of the internal demo lab, keeping all implemented flaws enabled."""
import argparse
import json

from evaluator.m2 import cli, compose, operator, ready


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", help="Reset synthetic lab data now")
    args = parser.parse_args(argv)
    if not args.execute:
        parser.print_help()
        return 0

    # Existing operator guards reject queued/active runs before touching lab data.
    ready()
    operator("maintenance_enter")
    backup = compose(
        "exec", "-T", "--user", "10001:10001", "lab", "python", "-c",
        "import sqlite3,time; from pathlib import Path; "
        "p=Path('/data/backups')/('demo-reset-'+str(time.time_ns())+'.sqlite3'); "
        "p.parent.mkdir(exist_ok=True); "
        "s=sqlite3.connect('/data/lab.sqlite3'); d=sqlite3.connect(p); "
        "s.backup(d); d.close(); s.close(); print(str(p))",
    ).strip()
    snapshot = cli(
        "lab", "lab.maintenance", "reset",
        "--condition", "vulnerable", "--all-supported",
    )
    inspected = cli("lab", "lab.maintenance", "inspect")
    if (inspected["snapshot_id"] != snapshot["snapshot_id"] or
            len(inspected["attachments"]) != 2 or
            any(item["deleted"] for item in inspected["attachments"])):
        raise RuntimeError("LAB_ASSERTION_FAILED; target remains in maintenance")
    health = json.loads(compose(
        "exec", "-T", "--user", "10001:10001", "lab", "python", "-c",
        "import urllib.request; "
        "print(urllib.request.urlopen('http://127.0.0.1:8001/api/health',timeout=3).read().decode())",
    ))
    if health != {"status": "ok", "seeded": True}:
        raise RuntimeError("LAB_HEALTH_FAILED; target remains in maintenance")
    released = operator("maintenance_release", {"snapshot_id": snapshot["snapshot_id"]})
    print(json.dumps({
        "status": "VULNERABLE_READY", "ready": released["ready"],
        "coverage": "ALL_IMPLEMENTED",
        "snapshot_id": snapshot["snapshot_id"], "lab_backup": backup,
        "conditions": {"BAC-08": "vulnerable", "XSS-08": "vulnerable", "UP-04": "vulnerable"},
        "objects": snapshot["objects"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
