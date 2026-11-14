"""Lab-local consumer of explicit admin maintenance requests. No public route."""
import asyncio
import json
import os
from pathlib import Path
import sqlite3
import time

import httpx

from boundary.files import read_json, write_json
from boundary.lab_reset import ResetRequest, ResetResult
from lab.maintenance import inspect, reset


async def health_check():
    async with httpx.AsyncClient(trust_env=False, follow_redirects=False, timeout=3) as client:
        response = await client.get("http://127.0.0.1:8001/api/health")
        if response.status_code != 200 or response.json() != {"status": "ok", "seeded": True}:
            raise ValueError("HEALTH_ASSERTION_FAILED")


def backup(path: Path) -> str:
    folder = path.parent / "backups"
    folder.mkdir(exist_ok=True)
    target = folder / f"admin-reset-{time.time_ns()}.sqlite3"
    with sqlite3.connect(path) as source, sqlite3.connect(target) as destination:
        source.backup(destination)
    return str(target)


async def reset_once(root: Path, db_path: Path, name: str):
    request = ResetRequest.model_validate(read_json(root, name, 4096))
    if name != f"{request.request_id}.request.json":
        raise ValueError("REQUEST_NAME_MISMATCH")
    if (root / f"{request.request_id}.result.json").exists():
        # A duplicate delivery keeps the first result; never repeat the mutation.
        (root / name).unlink()
        return
    now = time.time()
    if not now - 30 <= request.issued_at <= now + 1 or not now < request.expires_at <= request.issued_at + 30:
        result = ResetResult(request_id=request.request_id, condition=request.condition, status="FAILED", error_code="REQUEST_EXPIRED")
        write_json(root, f"{request.request_id}.result.json", result.model_dump(mode="json"), 16384)
        (root / name).unlink()
        return
    # Rename before mutation. A claimed request is never replayed after a crash.
    claimed = root / f"{request.request_id}.claimed.json"
    (root / name).rename(claimed)
    write_json(root, "heartbeat.json", {"captured_at": now, "status": "BUSY"}, 4096)
    try:
        await asyncio.to_thread(backup, db_path)
        accounts = json.loads(Path(os.environ.get("LAB_ACCOUNTS_FILE", "/run/secrets/lab_accounts")).read_text())
        snapshot = await reset(db_path, accounts, request.condition, all_supported=True)
        state = await inspect(db_path)
        if (state["snapshot_id"] != snapshot["snapshot_id"] or len(state["attachments"]) != 2 or
                any(a["deleted"] for a in state["attachments"])):
            raise ValueError("SEED_ASSERTION_FAILED")
        # Health goes only to the lab's own loopback, not any report-supplied URL.
        await health_check()
        result = ResetResult(request_id=request.request_id, condition=request.condition, coverage="ALL_IMPLEMENTED", status="SUCCEEDED", **snapshot)
    except Exception:
        result = ResetResult(request_id=request.request_id, condition=request.condition, status="FAILED", error_code="RESET_FAILED")
    write_json(root, f"{request.request_id}.result.json", result.model_dump(mode="json"), 16384)
    claimed.unlink()


async def loop(root: Path, db_path: Path, manual_lock: asyncio.Lock | None = None):
    # This volume is mounted only on app and lab, never worker or manual copy.
    root.mkdir(parents=True, exist_ok=True)
    while True:
        unknown = any(root.glob("*.claimed.json"))
        write_json(root, "heartbeat.json", {"captured_at": time.time(), "status": "UNKNOWN" if unknown else "IDLE"}, 4096)
        if not unknown:
            for request in sorted(root.glob("*.request.json")):
                try:
                    if manual_lock is not None:
                        async with manual_lock:
                            await reset_once(root, db_path, request.name)
                    else:
                        await reset_once(root, db_path, request.name)
                except (OSError, ValueError):
                    # Invalid files are quarantined, never interpreted as code or retried.
                    request.rename(request.with_suffix(".rejected"))
        await asyncio.sleep(0.25)
