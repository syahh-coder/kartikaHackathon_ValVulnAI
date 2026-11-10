import pytest
from httpx import ASGITransport, AsyncClient

from lab.main import create_app
from lab.maintenance import inspect, reset

ACCOUNTS={a:{"password":"only-synthetic-lab-password"} for a in ("requester-a","requester-b")}


async def login(app, alias):
    client=AsyncClient(transport=ASGITransport(app=app),base_url="http://lab:8001",headers={"Origin":"http://lab:8001"})
    response=await client.post("/api/auth/login",json={"login_name":alias,"password":ACCOUNTS[alias]["password"]})
    assert response.status_code==200
    client.headers["X-CSRF-Token"]=response.json()["csrf_token"]
    return client


@pytest.mark.parametrize("condition,cross_status,after_status",[("vulnerable",200,404),("fixed",404,200)])
async def test_bac08_real_mutation_and_owner_control(tmp_path,condition,cross_status,after_status):
    path=tmp_path/"lab.sqlite3"
    seeded=await reset(path,ACCOUNTS,condition)
    app=create_app(path)
    async with app.router.lifespan_context(app):
        a,b=[await login(app,x) for x in ACCOUNTS]
        try:
            bpath="/api/attachments/"+seeded["objects"]["requester-b"]["attachment_id"]
            apath="/api/attachments/"+seeded["objects"]["requester-a"]["attachment_id"]
            assert (await b.get(bpath)).status_code==200
            assert (await a.get(bpath)).status_code==404  # No second read IDOR point.
            assert (await a.delete(bpath)).status_code==cross_status
            assert (await b.get(bpath)).status_code==after_status
            assert (await a.get(apath)).status_code==200
            assert (await a.delete(apath)).status_code==200
            assert (await a.get(apath)).status_code==404
            assert (await b.get("/api/health")).json()=={"status":"ok","seeded":True}
            assert (await b.post("/reset")).status_code==404
            assert (await b.get("/openapi.json")).status_code==404
            public=(await b.get("/api/requests")).text
            assert "delete_owner_check" not in public and condition not in public
        finally:
            await a.aclose(); await b.aclose()


async def test_reset_and_restart_preserve_expected_boundaries(tmp_path):
    path=tmp_path/"lab.sqlite3"
    first=await reset(path,ACCOUNTS,"vulnerable")
    app=create_app(path)
    async with app.router.lifespan_context(app):
        a=await login(app,"requester-a")
        aid=first["objects"]["requester-b"]["attachment_id"]
        assert (await a.delete("/api/attachments/"+aid)).status_code==200
        assert (await inspect(path))["attachments"][1]["deleted"] is True
    app2=create_app(path)
    async with app2.router.lifespan_context(app2):
        assert (await inspect(path))["attachments"][1]["deleted"] is True
        second=await reset(path,ACCOUNTS,"fixed")
        assert second["snapshot_id"] != first["snapshot_id"]
        assert all(not x["deleted"] for x in (await inspect(path))["attachments"])
        assert (await a.get("/api/requests")).status_code==401
    await a.aclose()


async def test_lab_auth_csrf_and_input(tmp_path):
    path=tmp_path/"lab.sqlite3"
    seeded=await reset(path,ACCOUNTS,"fixed")
    app=create_app(path)
    async with app.router.lifespan_context(app):
        a=await login(app,"requester-a")
        route="/api/attachments/"+seeded["objects"]["requester-a"]["attachment_id"]
        assert (await a.delete(route,headers={"Origin":"http://evil.invalid"})).status_code==403
        assert (await a.delete(route,headers={"X-CSRF-Token":"wrong"})).status_code==403
        assert (await a.get(route)).status_code==200
        assert (await a.post("/api/auth/login",json={"login_name":"requester-a","password":ACCOUNTS['requester-a']['password'],"role":"admin"})).status_code==422
        await a.aclose()
