import asyncio
import json
import time
from uuid import uuid4

import httpx
import pytest

from app.storage.db import one
from boundary.files import read_json, write_json
from lab.main import create_app
from lab.maintenance import reset
from lab import reset_control
from tests.test_lab_reset_ui import prepare, wait_done, protected


async def test_manual_admin_only_idle_and_reset_revokes(env, tmp_path, monkeypatch):
    app, program, hunter, _, admin = env
    root, beat = prepare(app, tmp_path, monkeypatch)
    app.state.config.shared_lab_manual = True
    async with app.state.db.transaction() as conn:
        await conn.execute("UPDATE target_bindings SET snapshot_id=?", (beat["snapshot_id"],))
    url = f"/api/programs/{program}/lab-manual-session"
    body = {"confirm": "OPEN_SHARED_MANUAL_LAB"}
    before = await protected(app.state.db)
    assert (await hunter.post(url, json=body)).status_code == 403
    assert (await admin.post(url, json=body, headers={"X-CSRF-Token": "wrong"})).status_code == 403
    beat.update(status="BUSY", active_run_id=str(uuid4()))
    assert (await admin.post(url, json=body)).status_code == 409
    assert not (root/"manual-session.json").exists()
    beat.update(status="IDLE", active_run_id=None)
    response = await admin.post(url, json=body)
    assert response.status_code == 200 and response.json()["snapshot_id"] == beat["snapshot_id"]
    status = (await admin.get(f"/api/programs/{program}/lab-reset")).json()
    assert status["manual_active"] and status["target"]["maintenance"] and status["target"]["dirty"]
    assert read_json(root, "manual-session.json")["active"]
    assert await protected(app.state.db) == before
    reset_response = await admin.post(f"/api/programs/{program}/lab-reset", json={"confirm": "RESET_DEMO_LAB", "condition": "fixed"})
    assert reset_response.status_code == 202
    assert read_json(root, "manual-session.json")["active"] is False
    rid = reset_response.json()["request_id"]
    write_json(root, f"{rid}.result.json", {"request_id": rid, "status": "FAILED", "condition": "fixed", "error_code": "RESET_FAILED"})
    await wait_done(app)


async def test_shared_target_gate_same_snapshot_and_worker_access(tmp_path, monkeypatch):
    root = tmp_path/"control"
    root.mkdir()
    path = tmp_path/"lab.sqlite3"
    accounts = {a: {"password": "synthetic-shared-lab-password"} for a in ["requester-a", "requester-b"]}
    seed = await reset(path, accounts, "fixed")
    monkeypatch.setenv("LAB_MANUAL_ORIGIN", "http://127.0.0.1:8001")
    monkeypatch.setenv("LAB_SHARED_MANUAL", "1")
    monkeypatch.setenv("LAB_RESET_CONTROL_DIR", str(root))
    app = create_app(path)
    login = {"login_name": "requester-a", "password": accounts["requester-a"]["password"]}
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://127.0.0.1:8001", headers={"Origin": "http://127.0.0.1:8001"}) as client:
            assert "Target yang sama" in (await client.get("/")).text
            assert (await client.post("/api/auth/login", json=login)).status_code == 409
            assert (await client.get("/notifications/preview")).status_code == 409
            write_json(root, "manual-session.json", {"active": True, "expires_at": time.time()+60, "snapshot_id": seed["snapshot_id"]})
            assert (await client.post("/api/auth/login", json=login)).status_code == 200
            result = (await client.get("/manual/objects")).json()
            assert result["snapshot_id"] == seed["snapshot_id"]
            assert result["purpose"] == "SHARED_WORKER_TARGET"
            assert "preview.textContent=" in (await client.get("/notifications/preview")).text
            for session in [{"active": False, "expires_at": 0},
                            {"active": True, "expires_at": time.time()-1, "snapshot_id": seed["snapshot_id"]},
                            {"active": True, "expires_at": time.time()+60, "snapshot_id": str(uuid4())}]:
                write_json(root, "manual-session.json", session)
                assert (await client.get("/notifications/preview")).status_code == 409
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app, client=("172.30.74.2", 10000)), base_url="http://lab:8001", headers={"Origin": "http://lab:8001"}) as worker:
            assert (await worker.post("/api/auth/login", json=login)).status_code == 200
            assert (await worker.get("/notifications/preview")).status_code == 200


async def test_reset_waits_for_manual_handler_lock(tmp_path, monkeypatch):
    root = tmp_path/"control"
    root.mkdir()
    (root/f"{uuid4()}.request.json").write_text("{}")
    called = asyncio.Event()
    async def consume(root, path, name):
        (root/name).unlink()
        called.set()
    monkeypatch.setattr(reset_control, "reset_once", consume)
    lock = asyncio.Lock()
    await lock.acquire()
    task = asyncio.create_task(reset_control.loop(root, tmp_path/"unused.sqlite3", lock))
    await asyncio.sleep(0.05)
    assert not called.is_set()
    lock.release()
    await asyncio.wait_for(called.wait(), 1)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
