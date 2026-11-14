import asyncio
import json
import sqlite3
import time
from uuid import uuid4

import pytest

from app.storage.db import all_rows, one
from app.transport import Handoff
from boundary.files import read_json, write_json
from lab import reset_control
from lab.maintenance import reset

CONFIRM = {"confirm": "RESET_VULNERABLE_DEMO"}


def prepare(app, tmp_path, monkeypatch):
    root = tmp_path / "control"
    root.mkdir()
    write_json(root, "heartbeat.json", {"captured_at": time.time(), "status": "IDLE"})
    app.state.config.lab_reset_control_dir = root
    app.state.config.transport_key_file = tmp_path / "key"
    app.state.config.transport_key_file.write_text("ab" * 32)
    beat = {"status": "IDLE", "active_run_id": None, "dirty": True, "snapshot_id": str(uuid4())}
    monkeypatch.setattr(Handoff, "heartbeat", lambda self: beat.copy())
    def control(self, kind, **kwargs):
        assert kind == "RESET_RELEASE"
        beat.update(snapshot_id=kwargs["snapshot_id"], dirty=False)
    monkeypatch.setattr(Handoff, "control", control)
    return root, beat


async def wait_done(app):
    await asyncio.wait_for(app.state.lab_reset.task, 5)
    return app.state.lab_reset.stored()


async def protected(db):
    async with db.connect() as conn:
        return {t: [dict(r) for r in await all_rows(conn, "SELECT * FROM " + t + " ORDER BY rowid")]
                for t in ["reports", "report_revisions", "runs", "ledger", "provider_attempts", "text_triages", "scope_versions"]}


async def test_admin_only_and_csrf(env):
    app, p, hunter, _, admin = env
    for method in ["get", "post"]:
        kwargs = {"json": CONFIRM} if method == "post" else {}
        r = await getattr(hunter, method)(f"/api/programs/{p}/lab-reset", **kwargs)
        assert r.status_code == 403
    r = await admin.post(f"/api/programs/{p}/lab-reset", json=CONFIRM, headers={"X-CSRF-Token": "invalid"})
    assert r.status_code == 403 and r.json()["error_code"] == "CSRF_DENIED"
    assert (await admin.get(f"/api/programs/{uuid4()}/lab-reset")).status_code == 404


@pytest.mark.parametrize("payload", [{}, {"confirm": "fixed"}, {**CONFIRM, "condition": "fixed"},
                                     {"confirm": "RESET_DEMO_LAB", "condition": "custom"},
                                     {"confirm": "RESET_DEMO_LAB", "condition": "fixed", "command": "anything"}])
async def test_no_invalid_or_unconfirmed_options(env, payload):
    _, p, _, _, admin = env
    assert (await admin.post(f"/api/programs/{p}/lab-reset", json=payload)).status_code == 422


async def test_unconfigured_no_change(env):
    app, p, _, _, admin = env
    before = await protected(app.state.db)
    r = await admin.post(f"/api/programs/{p}/lab-reset", json=CONFIRM)
    assert r.status_code == 503
    assert await protected(app.state.db) == before
    async with app.state.db.connect() as conn:
        assert (await one(conn, "SELECT maintenance FROM target_bindings"))[0] == 0


async def test_busy_worker_does_not_enqueue(env, tmp_path, monkeypatch):
    app, p, _, _, admin = env
    root, beat = prepare(app, tmp_path, monkeypatch)
    beat.update(status="BUSY", active_run_id=str(uuid4()))
    r = await admin.post(f"/api/programs/{p}/lab-reset", json=CONFIRM)
    assert r.status_code == 409 and r.json()["error_code"] == "WORKER_BUSY"
    assert not list(root.glob("*.request.json"))


@pytest.mark.parametrize("health_ok", [True, False])
@pytest.mark.parametrize("condition", ["vulnerable", "fixed"])
async def test_mailbox_reset_preserves_app_and_applies_condition(env, tmp_path, monkeypatch, health_ok, condition):
    app, p, _, _, admin = env
    root, beat = prepare(app, tmp_path, monkeypatch)
    db_path = tmp_path / "lab.sqlite3"
    accounts = {a: {"password": "synthetic-reset-demo-password"} for a in ["requester-a", "requester-b"]}
    accounts_file = tmp_path / "accounts.json"
    accounts_file.write_text(json.dumps(accounts))
    monkeypatch.setenv("LAB_ACCOUNTS_FILE", str(accounts_file))
    original = await reset(db_path, accounts, "fixed")
    async def health():
        if not health_ok:
            raise ValueError("FAILED_HEALTH")
    monkeypatch.setattr(reset_control, "health_check", health)
    before = await protected(app.state.db)
    body = {"confirm": "RESET_DEMO_LAB", "condition": condition}
    r = await admin.post(f"/api/programs/{p}/lab-reset", json=body)
    assert r.status_code == 202
    request_id = r.json()["request_id"]
    original_request = read_json(root, f"{request_id}.request.json")
    assert original_request["condition"] == condition
    duplicate = await admin.post(f"/api/programs/{p}/lab-reset", json=body)
    assert duplicate.status_code == 409
    await reset_control.reset_once(root, db_path, f"{request_id}.request.json")
    result = await wait_done(app)
    assert result["status"] == ("SUCCEEDED" if health_ok else "FAILED")
    async with app.state.db.connect() as conn:
        target = await one(conn, "SELECT * FROM target_bindings")
    assert bool(target["maintenance"]) is not health_ok
    assert bool(target["dirty"]) is not health_ok
    assert await protected(app.state.db) == before
    with sqlite3.connect(db_path) as conn:
        values = dict(conn.execute("SELECT key,value FROM settings"))
    assert values["delete_owner_check"] == ("0" if condition == "vulnerable" else "1")
    assert values["notification_dom_html"] == ("1" if condition == "vulnerable" else "0")
    assert values["upload_filename_html"] == ("1" if condition == "vulnerable" else "0")
    from lab.xss_catalog import POINTS
    from lab.uploads import POINTS as UPLOAD_POINTS
    assert all(values[key] == ("1" if condition == "vulnerable" else "0") for key in [*POINTS.values(), *UPLOAD_POINTS.values()])
    assert values["snapshot_id"] != original["snapshot_id"]
    assert len(list((tmp_path / "backups").glob("*.sqlite3"))) == 1
    if health_ok:
        assert target["snapshot_id"] == beat["snapshot_id"] == result["snapshot_id"]
    response = await admin.get(f"/api/programs/{p}/lab-reset")
    assert response.json()["status"] == result["status"]
    assert response.json()["applied_condition"] == (condition if health_ok else None)
    assert response.json()["applied_coverage"] == ("ALL_IMPLEMENTED" if health_ok else None)
    write_json(root, f"{request_id}.request.json", original_request)
    await reset_control.reset_once(root, db_path, f"{request_id}.request.json")
    assert len(list((tmp_path / "backups").glob("*.sqlite3"))) == 1


@pytest.mark.parametrize("result_condition,coverage", [("vulnerable", "ALL_IMPLEMENTED"), ("fixed", None)])
async def test_result_condition_or_coverage_mismatch_keeps_target_locked(env, tmp_path, monkeypatch, result_condition, coverage):
    app, p, _, _, admin = env
    root, _ = prepare(app, tmp_path, monkeypatch)
    response = await admin.post(f"/api/programs/{p}/lab-reset", json={"confirm": "RESET_DEMO_LAB", "condition": "fixed"})
    rid = response.json()["request_id"]
    write_json(root, f"{rid}.result.json", {"request_id": rid, "status": "SUCCEEDED", "condition": result_condition, "coverage": coverage, "snapshot_id": str(uuid4())})
    assert (await wait_done(app))["status"] == "FAILED"
    async with app.state.db.connect() as conn:
        assert (await one(conn, "SELECT maintenance,dirty FROM target_bindings"))[:] == (1, 1)


async def test_legacy_confirmation_defaults_to_vulnerable(env, tmp_path, monkeypatch):
    app, p, _, _, admin = env
    root, _ = prepare(app, tmp_path, monkeypatch)
    response = await admin.post(f"/api/programs/{p}/lab-reset", json=CONFIRM)
    assert response.status_code == 202 and response.json()["condition"] == "vulnerable"
    rid = response.json()["request_id"]
    assert read_json(root, f"{rid}.request.json")["condition"] == "vulnerable"
    write_json(root, f"{rid}.result.json", {"request_id": rid, "status": "FAILED", "condition": "vulnerable", "error_code": "RESET_FAILED"})
    await wait_done(app)


async def test_expired_request_does_not_reset(tmp_path, monkeypatch):
    root = tmp_path / "control"
    root.mkdir()
    rid = str(uuid4())
    write_json(root, f"{rid}.request.json", {"request_id": rid, "operation": "RESET_VULNERABLE_DEMO", "issued_at": time.time()-60, "expires_at": time.time()-30})
    async def forbidden(*args, **kwargs):
        raise AssertionError("must not reset")
    monkeypatch.setattr(reset_control, "reset", forbidden)
    await reset_control.reset_once(root, tmp_path/"absent.sqlite3", f"{rid}.request.json")
    assert read_json(root, f"{rid}.result.json")["error_code"] == "REQUEST_EXPIRED"
    assert not (tmp_path/"absent.sqlite3").exists()


async def test_claimed_request_not_replayed(tmp_path, monkeypatch):
    root = tmp_path/"control"
    root.mkdir()
    (root/"previous.claimed.json").write_text("{}")
    async def forbidden(*args):
        raise AssertionError("must not replay unknown mutation")
    monkeypatch.setattr(reset_control, "reset_once", forbidden)
    task = asyncio.create_task(reset_control.loop(root, tmp_path/"absent.sqlite3"))
    await asyncio.sleep(0.05)
    assert read_json(root, "heartbeat.json")["status"] == "UNKNOWN"
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task


async def test_recovery_does_not_enqueue(env, tmp_path, monkeypatch):
    app, _, *_ = env
    root, _ = prepare(app, tmp_path, monkeypatch)
    app.state.lab_reset.save({"status": "RUNNING", "request_id": str(uuid4())})
    await app.state.lab_reset.recover()
    assert app.state.lab_reset.stored()["error_code"] == "RESET_OUTCOME_UNKNOWN"
    assert not list(root.glob("*.request.json"))
