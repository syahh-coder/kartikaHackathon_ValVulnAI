"""Regression tests of safe business controls; ASGI only, no exploitation runner."""
import asyncio
import json
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient
import pytest
from pydantic import ValidationError

from lab import business
from lab.business import CreateRequest, VersionInput
from lab.business_setup import provision
from lab.main import create_app
from lab.maintenance import reset
from lab.storage import connect, one
from test_lab_bac import ACCOUNTS


PASSWORD = "only-synthetic-staff-password"


async def session(app, alias, password=PASSWORD):
    client = AsyncClient(transport=ASGITransport(app=app), base_url="http://lab:8001", headers={"Origin": "http://lab:8001"})
    response = await client.post("/api/auth/login", json={"login_name": alias, "password": password})
    assert response.status_code == 200
    client.headers["X-CSRF-Token"] = response.json()["csrf_token"]
    return client


@pytest.fixture
async def business_env(tmp_path):
    path = tmp_path / "lab.sqlite3"
    seed = await reset(path, ACCOUNTS, "fixed")
    setup = await provision(path, PASSWORD)
    app = create_app(path)
    async with app.router.lifespan_context(app):
        a = await session(app, "requester-a", ACCOUNTS["requester-a"]["password"])
        b = await session(app, "requester-b", ACCOUNTS["requester-b"]["password"])
        staff = await session(app, "approver_a")
        try:
            yield app, path, seed, setup, a, b, staff
        finally:
            for client in (a, b, staff):
                await client.aclose()


async def create(a, item_id, quantity=5):
    response = await a.post("/api/requests", json={"title": "Permintaan sintetis", "item_id": item_id, "quantity": quantity})
    assert response.status_code == 201, response.text
    return response.json()


async def approve(a, staff, row):
    path = f"/api/requests/{row['request_id']}"
    submitted = await a.post(path+"/submit", json={"expected_version": row["version"]})
    assert submitted.status_code == 200
    approved = await staff.post(path+"/approve", json={"expected_version": submitted.json()["version"]})
    assert approved.status_code == 200
    return approved.json()


async def state(path):
    async with connect(path) as db:
        counts = []
        for table in ("business_requests", "business_events", "business_fulfillments"):
            counts.append((await one(db, f"SELECT count(*) FROM {table}"))[0])
        return (*counts, (await one(db, "SELECT stock FROM business_items"))[0])


async def test_normal_workflow_records_before_after_and_fulfills_once(business_env):
    app, path, seed, setup, a, b, staff = business_env
    row = await create(a, setup["item_id"])
    rid = row["request_id"]
    listing = (await a.get("/api/requests")).json()["requests"]
    assert any(r["id"] == rid and r["attachment_id"] is None for r in listing)
    approved = await approve(a, staff, row)
    first = await staff.post(f"/api/requests/{rid}/fulfill", json={"expected_version": approved["version"]})
    second = await staff.post(f"/api/requests/{rid}/fulfill", json={"expected_version": approved["version"]})
    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
    assert first.json()["stock_before"] == 100 and first.json()["stock_after"] == 95
    observed = (await a.get(f"/api/requests/{rid}")).json()
    assert (observed["state"], observed["version"], observed["stock"]) == ("FULFILLED", 4, 95)
    assert [e["operation"] for e in observed["events"]] == ["CREATE", "SUBMIT", "APPROVE", "FULFILL"]
    assert len({e["event_id"] for e in observed["events"]}) == 4
    assert observed["events"][-1]["before"]["stock"] == 100
    assert observed["events"][-1]["after"]["stock"] == 95
    assert await state(path) == (1, 4, 1, 95)
    assert (await staff.post(f"/api/requests/{rid}/fulfill", json={"expected_version": 4})).status_code == 409


@pytest.mark.parametrize("quantity", [0, -1, 1001, True, False, "5", 5.0, None])
def test_quantity_requires_bounded_strict_integer(quantity):
    with pytest.raises(ValidationError):
        CreateRequest(title="Synthetic", item_id=uuid4(), quantity=quantity)


@pytest.mark.parametrize("version", [0, True, "1", 1.0, 1000001])
def test_version_requires_bounded_strict_integer(version):
    with pytest.raises(ValidationError):
        VersionInput(expected_version=version)


async def test_auth_csrf_schema_and_public_rules(business_env):
    app, path, seed, setup, a, b, staff = business_env
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://lab:8001") as anon:
        assert (await anon.get("/api/business-rules")).status_code == 401
        assert (await anon.get("/api/items")).status_code == 401
    rules = (await a.get("/api/business-rules")).json()
    assert rules["version"] == business.RULES_VERSION and rules["rules"] == business.BUSINESS_RULES
    assert not any(word in json.dumps(rules) for word in ("vulnerable", "BL-", "password", "snapshot_id"))
    payload = {"title": "Synthetic", "item_id": setup["item_id"], "quantity": 2}
    for extra in ({"role": "admin"}, {"owner_id": seed["objects"]["requester-b"]["user_id"]}, {"state": "APPROVED"}, {"approved_by": "self"}):
        assert (await a.post("/api/requests", json=payload|extra)).status_code == 422
    for headers in ({"Origin": "http://outside.invalid"}, {"X-CSRF-Token": "invalid"}):
        assert (await a.post("/api/requests", json=payload, headers=headers)).status_code == 403
    assert await state(path) == (0, 0, 0, 100)
    assert (await a.post("/api/requests", json=payload|{"item_id": str(uuid4())})).status_code == 404


async def test_state_ownership_unit_and_self_approval_controls(business_env):
    app, path, seed, setup, a, b, staff = business_env
    row = await create(a, setup["item_id"])
    route = f"/api/requests/{row['request_id']}"
    initial = await state(path)
    for suffix in ("/approve", "/fulfill"):
        assert (await staff.post(route+suffix, json={"expected_version": 1})).status_code == 409
        assert (await a.post(route+suffix, json={"expected_version": 1})).status_code == 404
        assert (await b.post(route+suffix, json={"expected_version": 1})).status_code == 404
    assert (await b.get(route)).status_code == 404
    assert (await b.post(route+"/submit", json={"expected_version": 1})).status_code == 404
    assert (await staff.post(route+"/submit", json={"expected_version": 1})).status_code == 404
    assert await state(path) == initial
    await a.post(route+"/submit", json={"expected_version": 1})
    async with connect(path) as db:
        # Role assignment is test/operator data, never a client-provided field.
        await db.execute("INSERT INTO business_staff VALUES (?,?)", (seed["objects"]["requester-a"]["user_id"], "unit-1"))
        await db.execute("INSERT INTO business_staff VALUES (?,?)", (seed["objects"]["requester-b"]["user_id"], "unit-2"))
        await db.commit()
    assert (await a.post(route+"/approve", json={"expected_version": 2})).status_code == 403
    assert (await b.post(route+"/approve", json={"expected_version": 2})).status_code == 404
    brow = await create(b, setup["item_id"])
    assert (await staff.get(f"/api/requests/{brow['request_id']}")).status_code == 404
    assert (await staff.post(f"/api/requests/{brow['request_id']}/fulfill", json={"expected_version": 1})).status_code == 404


async def test_edit_versions_and_material_lock(business_env):
    app, path, seed, setup, a, b, staff = business_env
    row = await create(a, setup["item_id"])
    route = f"/api/requests/{row['request_id']}"
    payload = {"item_id": setup["item_id"], "quantity": 9, "expected_version": 1}
    assert (await b.patch(route, json=payload)).status_code == 404
    updated = await a.patch(route, json=payload)
    assert updated.status_code == 200 and updated.json()["version"] == 2
    assert (await a.patch(route, json=payload)).status_code == 409
    approved = await approve(a, staff, updated.json())
    current = await state(path)
    assert (await a.patch(route, json=payload|{"expected_version": approved["version"]})).status_code == 409
    assert await state(path) == current
    import sqlite3
    async with connect(path) as db:
        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            await db.execute("UPDATE business_requests SET quantity=10 WHERE request_id=?", (row["request_id"],))


async def test_available_stock_checked_at_fulfillment_and_failure_unchanged(business_env):
    app, path, seed, setup, a, b, staff = business_env
    first = await approve(a, staff, await create(a, setup["item_id"], 60))
    second = await approve(a, staff, await create(a, setup["item_id"], 60))
    assert (await staff.post(f"/api/requests/{first['request_id']}/fulfill", json={"expected_version": first["version"]})).status_code == 200
    before = await state(path)
    response = await staff.post(f"/api/requests/{second['request_id']}/fulfill", json={"expected_version": second["version"]})
    assert response.status_code == 409 and response.json()["detail"] == "INSUFFICIENT_STOCK"
    assert await state(path) == before
    assert (await a.get(f"/api/requests/{second['request_id']}")).json()["state"] == "APPROVED"


async def test_fulfillment_transaction_rolls_back_if_journal_fails(business_env, monkeypatch):
    app, path, seed, setup, a, b, staff = business_env
    row = await approve(a, staff, await create(a, setup["item_id"]))
    before = await state(path)
    async def unavailable(*args):
        raise HTTPException(409, "TEST_JOURNAL_FAILURE")
    monkeypatch.setattr(business, "record", unavailable)
    assert (await staff.post(f"/api/requests/{row['request_id']}/fulfill", json={"expected_version": row["version"]})).status_code == 409
    assert await state(path) == before
    assert (await a.get(f"/api/requests/{row['request_id']}")).json()["state"] == "APPROVED"


async def test_stale_parallel_edits_serialize_without_lost_update(business_env):
    app, path, seed, setup, a, b, staff = business_env
    row = await create(a, setup["item_id"])
    responses = await asyncio.gather(*(a.patch(f"/api/requests/{row['request_id']}", json={"item_id": setup["item_id"], "quantity": n, "expected_version": 1}) for n in (6, 7)))
    assert sorted(r.status_code for r in responses) == [200, 409]
    observed = (await a.get(f"/api/requests/{row['request_id']}")).json()
    assert observed["version"] == 2 and len(observed["events"]) == 2


async def test_setup_repeat_and_startup_preserve_data_and_password(business_env):
    app, path, seed, setup, a, b, staff = business_env
    row = await create(a, setup["item_id"])
    again = await provision(path, "different-unused-password")
    assert again == setup|{"changed": False}
    other = create_app(path)
    async with other.router.lifespan_context(other):
        client = await session(other, "approver_a")
        assert (await client.get(f"/api/requests/{row['request_id']}")).json()["version"] == 1
        await client.aclose()
    assert await state(path) == (1, 1, 0, 100)
    await reset(path, ACCOUNTS, "fixed")
    async with connect(path) as db:
        assert (await one(db, "SELECT count(*) FROM business_requests"))[0] == 0
        assert (await one(db, "SELECT count(*) FROM business_staff"))[0] == 0
        assert (await one(db, "SELECT count(*) FROM users"))[0] == 2
    assert (await staff.get("/api/items")).status_code == 401


async def test_unseeded_startup_does_not_provision_roles_inventory_or_state(tmp_path):
    path = tmp_path / "fresh.sqlite3"
    app = create_app(path)
    async with app.router.lifespan_context(app):
        async with connect(path) as db:
            for table in ("users", "business_items", "business_staff", "business_requests", "settings"):
                assert (await one(db, f"SELECT count(*) FROM {table}"))[0] == 0


def test_product_business_validator_remains_explicitly_unsupported():
    from app.agent.lab_validation import validator_for
    from app.common import AppError
    from app.schemas import Claim
    with pytest.raises(AppError) as error:
        validator_for(Claim(category="BUSINESS_LOGIC"))
    assert error.value.code == "UNSUPPORTED"


async def test_business_request_and_event_limits_leave_state_unchanged(business_env):
    app, path, seed, setup, a, b, staff = business_env
    row = await create(a, setup["item_id"])
    async with connect(path) as db:
        for _ in range(127):
            await db.execute("INSERT INTO business_events VALUES (?,?,?,'EDIT','{}','{}',0)",
                             (str(uuid4()), row["request_id"], seed["objects"]["requester-a"]["user_id"]))
        await db.commit()
    before = await state(path)
    rejected = await a.patch(f"/api/requests/{row['request_id']}", json={"item_id": setup["item_id"], "quantity": 9, "expected_version": 1})
    assert rejected.status_code == 409 and rejected.json()["detail"] == "EVENT_LIMIT"
    assert await state(path) == before
    observed = (await a.get(f"/api/requests/{row['request_id']}")).json()
    assert observed["quantity"] == 5 and observed["version"] == 1
    for _ in range(63):
        await create(a, setup["item_id"])
    before = await state(path)
    response = await a.post("/api/requests", json={"title": "Synthetic", "item_id": setup["item_id"], "quantity": 1})
    assert response.status_code == 409 and response.json()["detail"] == "REQUEST_LIMIT"
    assert await state(path) == before


async def test_setup_conflict_does_not_repurpose_existing_account(business_env):
    app, path, seed, setup, a, b, staff = business_env
    async with connect(path) as db:
        await db.execute("DELETE FROM business_staff")
        await db.commit()
    with pytest.raises(ValueError, match="conflict"):
        await provision(path, "different-unused-password")
    async with connect(path) as db:
        assert (await one(db, "SELECT count(*) FROM business_staff"))[0] == 0
        assert (await one(db, "SELECT value FROM settings WHERE key='snapshot_id'"))[0] == setup["snapshot_id"]
    client = await session(app, "approver_a")
    await client.aclose()


async def test_schema_upgrade_preserves_existing_lab_rows(tmp_path):
    # Build the actual earlier three-version layout before applying migration 004.
    import lab.storage as storage
    path = tmp_path / "upgrade.sqlite3"
    async with connect(path) as db:
        await db.execute("CREATE TABLE schema_versions(version INTEGER PRIMARY KEY)")
        for migration in sorted((Path(storage.__file__).parent/'migrations').glob('00[123]_*.sql')):
            await db.executescript(migration.read_text(encoding='utf-8'))
            await db.execute("INSERT INTO schema_versions VALUES (?)", (int(migration.name.split('_')[0]),))
        await db.execute("INSERT INTO users(id,alias,unit,password_hash,display_name) VALUES ('existing','old-user','unit-1','synthetic-hash','Synthetic')")
        await db.execute("INSERT INTO requests VALUES ('old-request','existing','Kept')")
        await db.execute("INSERT INTO settings VALUES ('snapshot_id','unchanged')")
        await db.commit()
    await storage.migrate(path)
    await storage.migrate(path)
    async with connect(path) as db:
        assert (await one(db, "SELECT title FROM requests WHERE id='old-request'"))[0] == "Kept"
        assert (await one(db, "SELECT value FROM settings WHERE key='snapshot_id'"))[0] == "unchanged"
        assert (await one(db, "SELECT count(*) FROM schema_versions"))[0] == 4
        assert (await one(db, "SELECT count(*) FROM business_staff"))[0] == 0


async def test_setup_wrong_database_rejected_before_schema_changes(tmp_path):
    path = tmp_path / "app.sqlite3"
    async with connect(path) as db:
        await db.execute("CREATE TABLE users(user_id TEXT PRIMARY KEY,login_name TEXT)")
        await db.execute("INSERT INTO users VALUES ('kept','demo')")
        await db.commit()
    with pytest.raises(ValueError, match="lab database"):
        await provision(path, PASSWORD)
    async with connect(path) as db:
        tables = await db.execute_fetchall("SELECT name FROM sqlite_master WHERE type='table'")
        assert [r[0] for r in tables] == ["users"]
        assert (await one(db, "SELECT login_name FROM users"))[0] == "demo"


async def test_setup_missing_database_does_not_create_file(tmp_path):
    path = tmp_path / "missing.sqlite3"
    with pytest.raises(ValueError, match="seeded lab"):
        await provision(path, PASSWORD)
    assert not path.exists()
