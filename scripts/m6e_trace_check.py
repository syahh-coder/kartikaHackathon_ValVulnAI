"""Capture the safe normal workflow on a new temporary database via ASGI only.

No configurable target/database, socket transport, project volume, worker or model.
Only selected event fields and actor/unit assignments are exported; no credentials.
"""
import asyncio
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import secrets
from tempfile import TemporaryDirectory

from evaluator.business_trace_audit import SNAPSHOT_FIELDS, audit
from lab.business import RULES_VERSION, public, snapshot
from lab.storage import connect, one
from scripts.m6b_persistence_probe import check


async def capture(path: Path, result: dict) -> dict:
    """Read a consistent snapshot of the dedicated control database."""
    rid = result["request_id"]
    async with connect(path) as db:
        await db.execute("BEGIN")
        row = await snapshot(db, rid)
        async with db.execute("SELECT id,request_id,actor_id,operation,before_json,after_json,created_at "
                              "FROM business_events WHERE request_id=? ORDER BY rowid LIMIT 128", (rid,)) as cursor:
            rows = await cursor.fetchall()
        events = []
        for event in rows:
            before, after = json.loads(event["before_json"]), json.loads(event["after_json"])
            events.append({"event_id": event["id"], "request_id": event["request_id"],
                           "actor_id": event["actor_id"], "operation": event["operation"],
                           "created_at": event["created_at"],
                           "before": {key: before[key] for key in SNAPSHOT_FIELDS} if before else None,
                           "after": {key: after[key] for key in SNAPSHOT_FIELDS}})
        actors = []
        for actor_id in sorted({event["actor_id"] for event in events} | {row["owner_id"]}):
            actor = await one(db, "SELECT u.id actor_id,u.unit,s.unit staff_unit FROM users u "
                              "LEFT JOIN business_staff s ON s.user_id=u.id WHERE u.id=?", (actor_id,))
            if actor is not None:
                actors.append(dict(actor))
        current_snapshot = await one(db, "SELECT value FROM settings WHERE key='snapshot_id'")
        if current_snapshot[0] != result["state"]["snapshot_id"]:
            raise ValueError("SNAPSHOT_CHANGED")
    final = public(row)
    return {"rules_version": RULES_VERSION, "request_id": rid, "owner_id": row["owner_id"],
            "approved_by": row["approved_by"], "actors": actors, "events": events,
            "final": {key: final[key] for key in SNAPSHOT_FIELDS},
            "state": result["state"], "fulfillment": result["fulfillment"]}


async def run_check() -> dict:
    payload = {"phase": "initialize", "password": secrets.token_urlsafe(24),
               "staff_password": secrets.token_urlsafe(24)}
    with TemporaryDirectory(prefix="valvuln-m6e-") as directory:
        path = Path(directory) / "normal-controls.sqlite3"
        first = await check(payload, path)
        initial_trace = await capture(path, first)
        payload.update(phase="restart", expected=first)
        second = await check(payload, path)
        restarted_trace = await capture(path, second)
    names = ["boundary/business_types.py", "boundary/business_trace.py",
             "evaluator/business_record_audit.py", "evaluator/business_trace_audit.py",
             "scripts/m6b_persistence_probe.py", "scripts/m6e_trace_check.py",
             "lab/business.py", "lab/business_setup.py", "lab/storage.py", "lab/main.py",
             "lab/maintenance.py", "lab/migrations/004_business_controls.sql"]
    return {"format_version": 1, "mode": "synthetic normal workflow ASGI only",
            "phases": [{"phase": "initialize", "trace": initial_trace},
                       {"phase": "restart", "trace": restarted_trace}],
            "source_sha256": {name: hashlib.sha256(Path(name).read_bytes()).hexdigest() for name in names}}


def main() -> None:
    record = asyncio.run(run_check())
    result = audit(record)
    directory = Path("artifacts/m6e")
    directory.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    path = directory / f"{stamp}-normal-trace.json"
    raw = json.dumps(record, indent=2).encode("utf-8")
    with path.open("xb") as stream:
        stream.write(raw)
    summary = {"record": path.as_posix(), "record_sha256": hashlib.sha256(raw).hexdigest(),
               "result": result, "database": "temporary database removed; ASGI only"}
    with (directory / f"{stamp}-audit.json").open("x", encoding="utf-8") as stream:
        json.dump(summary, stream, indent=2)
    print(json.dumps(summary, indent=2))
    raise SystemExit(0 if result["status"] == "CONSISTENT" else 2)


if __name__ == "__main__":
    main()
