import httpx
import pytest

from lab.main import create_app
from lab.maintenance import reset
from lab.manual_access import validate_manual_origin


@pytest.mark.parametrize("origin", ["http://0.0.0.0:8001", "https://example.com:8001", "http://127.0.0.1:8001/path",
                                   "http://127.0.0.1:8001#fragment", "http://u:p@127.0.0.1:8001"])
def test_manual_access_rejects_non_loopback_origin(origin):
    with pytest.raises(ValueError):
        validate_manual_origin(origin)


@pytest.mark.asyncio
@pytest.mark.parametrize("manual", [False, True])
async def test_manual_login_preserves_origin_and_csrf(tmp_path, monkeypatch, manual):
    if manual:
        monkeypatch.setenv("LAB_MANUAL_ORIGIN", "http://127.0.0.1:8001")
    else:
        monkeypatch.delenv("LAB_MANUAL_ORIGIN", raising=False)
    path = tmp_path / "lab.sqlite3"
    accounts = {name: {"password": "synthetic-manual-test-password"} for name in ("requester-a", "requester-b")}
    data = await reset(path, accounts, "fixed")
    app = create_app(path)
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://127.0.0.1:8001") as client:
            unauthenticated = await client.get("/manual/objects")
            assert unauthenticated.status_code == (401 if manual else 404)
            body = {"login_name": "requester-a", "password": accounts["requester-a"]["password"]}
            rejected = await client.post("/api/auth/login", json=body, headers={"Origin": "http://example.com"})
            assert rejected.status_code == 403
            response = await client.post("/api/auth/login", json=body, headers={"Origin": "http://127.0.0.1:8001"})
            assert response.status_code == (200 if manual else 403)
            internal = await client.post("/api/auth/login", json=body, headers={"Origin": "http://lab:8001"})
            assert internal.status_code == 200
            target = data["objects"]["requester-a"]["attachment_id"]
            denied = await client.delete(f"/api/attachments/{target}", headers={"Origin": "http://lab:8001"})
            assert denied.status_code == 403
            own = await client.get(f"/api/attachments/{target}")
            assert own.status_code == 200
            objects = await client.get("/manual/objects")
            assert objects.status_code == (200 if manual else 404)
            if manual:
                assert objects.json()["objects"]["requests"] == [data["objects"]["requester-a"]["request_id"]]
            home = await client.get("/")
            assert home.status_code == (200 if manual else 404)
