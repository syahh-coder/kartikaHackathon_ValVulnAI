import json
import time

import pytest
from httpx import ASGITransport, AsyncClient

from app.common import digest
from app.operator import seed
from app.storage.db import one
from conftest import CLAIM, ORIGIN, PASSWORD, SCOPE, activate, logged_client, report_for


async def test_ownership_role_and_membership(env):
    app, p, a, b, admin = env
    cid, rid, rev = await report_for(a, p)
    for suffix in (f"conversations/{cid}", f"reports/{rid}"):
        assert (await b.get("/api/"+suffix)).status_code == 404
        assert (await admin.get("/api/"+suffix)).status_code == 200
    assert (await b.post(f"/api/conversations/{cid}/messages", json={"body": "overwrite", "expected_draft_version": 1})).status_code == 404
    assert (await admin.post(f"/api/conversations/{cid}/messages", json={"body": "overwrite", "expected_draft_version": 1})).status_code == 403
    assert (await a.get(f"/api/programs/{p}/reports")).json()[0]["report_id"] == rid
    assert (await b.get(f"/api/programs/{p}/reports")).json() == []
    assert (await a.post(f"/api/programs/{p}/scope-drafts", json=SCOPE)).status_code == 403
    assert (await a.post(f"/api/conversations/{cid}/messages", json={"body": "x", "expected_draft_version": 1, "role": "PROGRAM_ADMIN"})).status_code == 422
    async with app.state.db.transaction() as conn:
        uid = (await one(conn, "SELECT user_id FROM users WHERE login_name='hunter-a'"))[0]
        await conn.execute("UPDATE memberships SET enabled=0 WHERE user_id=?", (uid,))
    assert (await a.get(f"/api/reports/{rid}")).status_code == 404


async def test_csrf_origin_rotation_expiry_logout(env):
    app, p, a, _, _ = env
    assert (await a.post(f"/api/programs/{p}/conversations", headers={"X-CSRF-Token": ""})).status_code == 403
    assert (await a.post(f"/api/programs/{p}/conversations", headers={"Origin": "https://evil.invalid"})).status_code == 403
    assert (await a.post(f"/api/programs/{p}/conversations", headers={"Origin": ""})).status_code == 403
    old = a.cookies.get("valvuln_session")
    nonce = (await a.get("/api/auth/csrf")).json()["csrf_token"]
    login = await a.post("/api/auth/login", json={"login_name": "hunter-a", "password": PASSWORD}, headers={"X-CSRF-Token": nonce})
    assert login.status_code == 200
    a.headers["X-CSRF-Token"] = login.json()["csrf_token"]
    assert a.cookies.get("valvuln_session") != old
    async with app.state.db.connect() as conn:
        assert (await one(conn, "SELECT revoked_at FROM sessions WHERE session_id_hash=?", (digest(old),)))[0]
    assert (await a.post("/api/auth/logout")).status_code == 200
    assert (await a.get("/api/me")).status_code == 401
    c = await logged_client(app, "hunter-a")
    async with app.state.db.transaction() as conn:
        await conn.execute("UPDATE sessions SET expires_at=? WHERE session_id_hash=?", (time.time()-1, digest(c.cookies.get("valvuln_session"))))
    assert (await c.get("/api/me")).status_code == 401
    await c.aclose()


async def test_login_no_role_and_rate_limit(env):
    app, *_ = env
    async with AsyncClient(transport=ASGITransport(app=app), base_url=ORIGIN, headers={"Origin": ORIGIN}) as client:
        assert (await client.post("/api/auth/login", json={"login_name": "admin", "password": PASSWORD})).status_code == 403
        for i in range(5):
            token = (await client.get("/api/auth/csrf")).json()["csrf_token"]
            r = await client.post("/api/auth/login", json={"login_name": "unknown", "password": "bad"}, headers={"X-CSRF-Token": token})
            assert r.status_code == 401
        token = (await client.get("/api/auth/csrf")).json()["csrf_token"]
        r = await client.post("/api/auth/login", json={"login_name": "unknown", "password": "bad"}, headers={"X-CSRF-Token": token})
        assert r.status_code == 429
        assert r.json()["retryable"] is True
        r = await client.post("/api/auth/login", json={"login_name": "admin", "password": "never-echo-this", "role": "PROGRAM_ADMIN"})
        assert r.status_code == 422 and "never-echo-this" not in r.text


async def test_snapshot_immutable_and_seed_repeat(env):
    app, p, a, _, _ = env
    cid, rid, rev = await report_for(a, p, text="Isi awal <script>alert(1)</script>")
    assert (await a.post(f"/api/conversations/{cid}/messages", json={"body": "tambahan", "expected_draft_version": 1})).status_code == 201
    new = await a.post(f"/api/conversations/{cid}/reports", json={"expected_draft_version": 2, "claim": CLAIM})
    assert new.status_code == 201 and new.json()["report_revision_id"] != rev
    result = (await a.get(f"/api/reports/{rid}")).json()
    assert len(result["revisions"]) == 2
    assert result["revisions"][0]["body"] == "Isi awal <script>alert(1)</script>"
    assert (await a.post(f"/api/conversations/{cid}/reports", json={"expected_draft_version": 1, "claim": CLAIM})).status_code == 409
    async with app.state.db.connect() as conn:
        old_hash = (await one(conn, "SELECT password_hash FROM users WHERE login_name='hunter-a'"))[0]
    await seed(app.state.db, "another-synthetic-password")
    async with app.state.db.connect() as conn:
        assert old_hash == (await one(conn, "SELECT password_hash FROM users WHERE login_name='hunter-a'"))[0]
        assert (await one(conn, "SELECT active_scope_version_id FROM programs"))[0] is None
        assert (await one(conn, "SELECT count(*) FROM users"))[0] == 3


async def test_scope_draft_activation_binding(env):
    app, p, a, _, admin = env
    assert (await a.get(f"/api/programs/{p}/guidelines")).json()["state"] == "NOT_CONFIGURED"
    r = await admin.post(f"/api/programs/{p}/scope-drafts", json=SCOPE)
    assert r.status_code == 201
    assert (await a.get(f"/api/programs/{p}/guidelines")).json()["state"] == "NOT_CONFIGURED"
    bad = json.loads(json.dumps(SCOPE))
    bad["in_scope_rules"][0]["asset_alias"] = "http://evil.invalid"
    assert (await admin.post(f"/api/programs/{p}/scope-drafts", json=bad)).status_code == 422
    bad["in_scope_rules"][0]["asset_alias"] = "metadata"
    assert (await admin.post(f"/api/programs/{p}/scope-drafts", json=bad)).status_code == 422
    scope_id = await activate(admin, p)
    public = (await a.get(f"/api/programs/{p}/guidelines")).json()
    assert public["scope_version_id"] == scope_id
    assert "http://lab" not in json.dumps(public)


@pytest.mark.parametrize("filename,raw,status", [
    ("report.pdf", b"data", 415), ("../report.txt", b"data", 422),
    ("report.txt", b"\xff", 415), ("report.txt", b"x"*131073, 413),
    ("report.md", b"x"*32001, 413), ("report.txt", b"\x00", 415),
])
async def test_upload_rejects_invalid(env, filename, raw, status):
    _, p, a, _, _ = env
    cid = (await a.post(f"/api/programs/{p}/conversations")).json()["conversation_id"]
    result = await a.post(f"/api/conversations/{cid}/attachments", files={"file": (filename, raw)})
    assert result.status_code == status, result.text
    assert (await a.get(f"/api/conversations/{cid}")).json()["attachment"] is None


async def test_upload_inert_ownership_limits(env):
    app, p, a, b, admin = env
    cid = (await a.post(f"/api/programs/{p}/conversations")).json()["conversation_id"]
    raw = b'<img src="https://external.invalid/track" onerror="alert(1)">'
    r = await a.post(f"/api/conversations/{cid}/attachments", files={"file": ("<img>.md", raw)})
    assert r.status_code == 201, r.text
    aid = r.json()["attachment_id"]
    assert (await b.get(f"/api/attachments/{aid}")).status_code == 404
    response = await a.get(f"/api/attachments/{aid}")
    assert response.content == raw and response.headers["content-type"].startswith("text/plain")
    assert response.headers["content-disposition"].startswith("attachment")
    assert (await a.post(f"/api/conversations/{cid}/attachments", files={"file": ("x.txt", b"x")})).status_code == 409
    assert (await a.post(f"/api/conversations/{cid}/messages", json={"body": "x"*32000, "expected_draft_version": 1})).status_code == 413
    cid2 = (await a.post(f"/api/programs/{p}/conversations")).json()["conversation_id"]
    r = await a.post(f"/api/conversations/{cid2}/attachments", files={"file": ("x.txt", b"x")}, data={"purpose": "GUIDELINE"})
    assert r.status_code in {400,422}
    assert not list(app.state.config.data_dir.glob("uploads/<*"))
