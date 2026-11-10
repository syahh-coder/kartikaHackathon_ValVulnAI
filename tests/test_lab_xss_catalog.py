from html import escape

import httpx
import pytest

from evaluator.xss_cases import POINTS, case, fixture
from lab.main import create_app
from lab.maintenance import reset
from lab.storage import connect, one
from lab.xss_catalog import POINTS as SETTINGS
from tests.test_lab_bac import ACCOUNTS, login


@pytest.mark.parametrize("point", POINTS)
@pytest.mark.parametrize("condition", ("vulnerable", "fixed"))
async def test_separate_points_persist_input_and_encode_controls(tmp_path, point, condition):
    path = tmp_path / "lab.sqlite3"
    seed = await reset(path, ACCOUNTS, "fixed", xss_point=point, point_condition=condition)
    app = create_app(path)
    value = fixture(point, "00000000-0000-4000-8000-000000000001")
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://lab:8001") as anonymous:
            _, route = case(point, seed["objects"], value)
            assert (await anonymous.get(route)).status_code == 401
        a, b = await login(app, "requester-a"), await login(app, "requester-b")
        try:
            writes, route = case(point, seed["objects"], value)
            for method, target in writes:
                assert (await a.request(method, target, json={"value": value})).status_code == 200
            page = await b.get(route)
            assert page.status_code == 200
            if point == "XSS-07":
                assert ("panel.innerHTML" if condition == "vulnerable" else "panel.textContent") in page.text
            else:
                assert (value if condition == "vulnerable" else escape(value)) in page.text
            _, safe_route = case(point, seed["objects"], value, safe=True)
            safe_page = await b.get(safe_route)
            assert safe_page.status_code == 200
            assert ("panel.textContent" if point == "XSS-07" else escape(value)) in safe_page.text
            assert not any(key in page.text for key in SETTINGS.values())
        finally:
            await a.aclose()
            await b.aclose()
    # A new app instance migrates without resetting values or maintenance conditions.
    restarted = create_app(path)
    async with restarted.router.lifespan_context(restarted):
        async with connect(path) as db:
            modes = dict(await db.execute_fetchall("SELECT key,value FROM settings WHERE key IN (" + ",".join("?" for _ in SETTINGS) + ")", tuple(SETTINGS.values())))
            assert sum(v == "1" for v in modes.values()) == (condition == "vulnerable")
            if point == "XSS-02":
                assert (await one(db, "SELECT note FROM catalog_items WHERE id=?", (seed["objects"]["requester-a"]["item_id"],)))[0] == value


async def test_catalog_writes_enforce_owner_csrf_schema_and_assigned_review(tmp_path):
    path = tmp_path / "lab.sqlite3"
    seed = await reset(path, ACCOUNTS, "fixed")
    app = create_app(path)
    async with app.router.lifespan_context(app):
        a, b = await login(app, "requester-a"), await login(app, "requester-b")
        try:
            for point in ("XSS-02", "XSS-03", "XSS-05"):
                writes, _ = case(point, seed["objects"], "text")
                method, route = writes[0]
                assert (await b.request(method, route, json={"value": "text"})).status_code == 404
                assert (await a.request(method, route, json={"value": "text"}, headers={"Origin": "http://evil.invalid"})).status_code == 403
                assert (await a.request(method, route, json={"value": "text"}, headers={"X-CSRF-Token": "bad"})).status_code == 403
                assert (await a.request(method, route, json={"value": "x"*1025})).status_code == 422
                assert (await a.request(method, route, json={"value": "text", "condition": "vulnerable"})).status_code == 422
            assert (await a.patch("/api/profile/display-name", json={"value": "text"}, headers={"X-CSRF-Token": "bad"})).status_code == 403
            rid = seed["objects"]["requester-a"]["request_id"]
            other = seed["objects"]["requester-b"]["request_id"]
            assert (await a.get(f"/requests/{rid}/review")).status_code == 403
            assert (await b.get(f"/requests/{rid}/review")).status_code == 200
            assert (await b.get(f"/requests/{other}/review")).status_code == 403
            assert (await a.get(f"/requests/{other}/comments")).status_code == 404
            assert (await b.post(f"/api/requests/{rid}/comments", json={"value": "text"})).status_code == 404
            assert (await a.patch("/api/profile/display-name", json={"value": "text", "role": "reviewer"})).status_code == 422
        finally:
            await a.aclose()
            await b.aclose()
    await reset(path, ACCOUNTS, "fixed")
    async with connect(path) as db:
        assert (await one(db, "SELECT count(*) FROM comments"))[0] == 0
        assert (await one(db, "SELECT count(*) FROM sessions"))[0] == 0


async def test_unknown_point_cannot_reset_existing_lab(tmp_path):
    path = tmp_path / "lab.sqlite3"
    seed = await reset(path, ACCOUNTS, "fixed")
    with pytest.raises(ValueError):
        await reset(path, ACCOUNTS, "fixed", xss_point="XSS-99", point_condition="vulnerable")
    async with connect(path) as db:
        assert (await one(db, "SELECT value FROM settings WHERE key='snapshot_id'"))[0] == seed["snapshot_id"]


@pytest.mark.parametrize("point", POINTS)
def test_catalog_routes_are_not_runtime_tools_or_development_planner_inputs(point):
    from pydantic import ValidationError
    from uuid import uuid4
    from app.agent.xss import prerequisites
    from app.common import AppError
    from app.schemas import Claim
    from boundary.contracts import BrowserArguments
    objects = {"requester-a": {k: str(uuid4()) for k in ("request_id", "item_id", "supplier_id")}}
    _, route = case(point, objects, "inert")
    path = route.split("?")[0]
    with pytest.raises(ValidationError):
        BrowserArguments(account_alias="requester-a", fixture="inert-v1", nonce=uuid4(), relative_path=path)
    with pytest.raises(AppError, match="XSS lab"):
        prerequisites(Claim(category="XSS", method="GET", path=path, asset_alias="portal",
            account_aliases=["requester-a", "requester-b"], primary_claim="Klaim sintetis"))


async def test_upgrade_legacy_lab_preserves_objects_and_fails_closed(tmp_path):
    from pathlib import Path
    from lab.storage import migrate
    path = tmp_path / "lab.sqlite3"
    async with connect(path) as db:
        await db.executescript((Path(__file__).parents[1] / "lab/migrations/001_portal.sql").read_text())
        await db.execute("CREATE TABLE schema_versions(version INTEGER PRIMARY KEY)")
        await db.execute("INSERT INTO schema_versions VALUES (1)")
        await db.execute("INSERT INTO users VALUES ('legacy','requester-a','unit-1','synthetic-hash')")
        await db.execute("INSERT INTO requests VALUES ('request-old','legacy','Tidak direset')")
        await db.execute("INSERT INTO settings VALUES ('snapshot_id','unchanged')")
        await db.commit()
    await migrate(path)
    await migrate(path)
    async with connect(path) as db:
        assert (await one(db, "SELECT title FROM requests WHERE id='request-old'"))[0] == "Tidak direset"
        assert (await one(db, "SELECT value FROM settings WHERE key='snapshot_id'"))[0] == "unchanged"
        assert (await one(db, "SELECT count(*) FROM schema_versions"))[0] == 3
        assert (await one(db, "SELECT count(*) FROM settings WHERE value='1'"))[0] == 0
