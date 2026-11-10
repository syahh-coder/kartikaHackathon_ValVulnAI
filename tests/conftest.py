import pytest
from httpx import ASGITransport, AsyncClient

from app.config import Settings
from app.main import create_app
from app.operator import seed

ORIGIN = "http://127.0.0.1:8000"
PASSWORD = "synthetic-test-password-only"
RULE = {"asset_alias": "portal", "path_template": "/api/attachments/{id}",
        "methods": ["GET", "DELETE"], "capabilities": ["BAC"]}
SCOPE = {"source_text": "Data sintetis. Uji BAC lampiran memakai dua akun.", "in_scope_rules": [RULE]}
CLAIM = {"asset_alias": "portal", "path": "/api/attachments/sample", "method": "DELETE",
         "category": "BAC", "account_aliases": ["requester-a", "requester-b"],
         "primary_claim": "Akun A dapat menghapus lampiran milik B"}


@pytest.fixture(autouse=True)
def no_network_http(monkeypatch):
    # ASGI clients remain usable; any real HTTP transport in M1 tests fails immediately.
    import httpx
    import urllib.request
    async def deny_async(*args, **kwargs):
        raise AssertionError("M1 tests must not send real HTTP requests")
    def deny(*args, **kwargs):
        raise AssertionError("M1 tests must not send real HTTP requests")
    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", deny_async)
    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", deny)
    monkeypatch.setattr(urllib.request, "urlopen", deny)


async def logged_client(app, name):
    client = AsyncClient(transport=ASGITransport(app=app), base_url=ORIGIN, headers={"Origin": ORIGIN})
    csrf = (await client.get("/api/auth/csrf")).json()["csrf_token"]
    res = await client.post("/api/auth/login", json={"login_name": name, "password": PASSWORD}, headers={"X-CSRF-Token": csrf})
    assert res.status_code == 200, res.text
    client.headers["X-CSRF-Token"] = res.json()["csrf_token"]
    return client


@pytest.fixture
async def env(tmp_path):
    app = create_app(Settings(data_dir=tmp_path, dispatcher_enabled=False, min_free_bytes=0, _env_file=None))
    async with app.router.lifespan_context(app):
        program = await seed(app.state.db, PASSWORD)
        a, b, admin = [await logged_client(app, n) for n in ("hunter-a", "hunter-b", "admin")]
        yield app, program, a, b, admin
        for client in (a, b, admin):
            await client.aclose()


async def activate(admin, program, scope=None):
    result = await admin.post(f"/api/programs/{program}/scope-drafts", json=scope or SCOPE)
    assert result.status_code == 201, result.text
    scope_id = result.json()["scope_version_id"]
    result = await admin.post(f"/api/programs/{program}/scope-drafts/{scope_id}/activate")
    assert result.status_code == 200, result.text
    return scope_id


async def report_for(client, program, claim=None, text="Laporan sintetis tanpa permintaan jaringan"):
    c = await client.post(f"/api/programs/{program}/conversations")
    assert c.status_code == 201, c.text
    cid = c.json()["conversation_id"]
    m = await client.post(f"/api/conversations/{cid}/messages", json={"body": text, "expected_draft_version": 0})
    assert m.status_code == 201, m.text
    r = await client.post(f"/api/conversations/{cid}/reports", json={"expected_draft_version": 1, "claim": claim or CLAIM})
    assert r.status_code == 201, r.text
    return cid, r.json()["report_id"], r.json()["report_revision_id"]
