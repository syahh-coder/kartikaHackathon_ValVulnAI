import asyncio
from contextlib import asynccontextmanager
import hashlib
import os
from pathlib import Path
import secrets
import time

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, ConfigDict, Field
from pwdlib import PasswordHash
from boundary.middleware import BodyLimit

from lab.storage import connect, migrate, one


def hashed(value: str):
    return hashlib.sha256(value.encode()).hexdigest()


class Login(BaseModel):
    model_config = ConfigDict(extra="forbid")
    login_name: str = Field(max_length=64)
    password: str = Field(max_length=128)


def create_app(db_path: Path | None = None):
    path = db_path or Path(os.environ.get("LAB_DATA_DIR", "/data")) / "lab.sqlite3"
    @asynccontextmanager
    async def lifespan(app):
        await migrate(path)
        yield
    app = FastAPI(title="Portal Lab Sintetis", docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)
    app.add_middleware(BodyLimit,maximum=4096)

    @app.middleware("http")
    async def headers_and_audit(request: Request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"]="no-store"
        response.headers["X-Content-Type-Options"]="nosniff"
        if request.url.path != "/api/health":
            async with connect(path) as db:
                await db.execute("INSERT INTO access_log(actor_id,method,path,status,created_at) VALUES (?,?,?,?,?)",
                                 (getattr(request.state,"actor",None),request.method,request.url.path,response.status_code,time.time()))
                await db.commit()
        return response

    async def actor(request: Request, db):
        session = await one(db, "SELECT s.*,u.alias FROM sessions s JOIN users u ON s.user_id=u.id WHERE token_hash=? AND expires>?",
                            (hashed(request.cookies.get("lab_session", "")),time.time()))
        if not session:
            raise HTTPException(401)
        request.state.actor=session["user_id"]
        if request.method in {"DELETE", "POST", "PATCH", "PUT"}:
            if (request.headers.get("origin")!="http://lab:8001" or
                    not secrets.compare_digest(hashed(request.headers.get("x-csrf-token","")),session["csrf_hash"])):
                raise HTTPException(403)
        return session

    @app.get("/api/health")
    async def health():
        async with connect(path) as db:
            ready=await one(db,"SELECT 1 FROM settings WHERE key='snapshot_id'")
        return {"status":"ok","seeded":bool(ready)}

    @app.post("/api/auth/login")
    async def login(body: Login, request: Request, response: Response):
        if request.headers.get("origin")!="http://lab:8001":
            raise HTTPException(403)
        async with connect(path) as db:
            user=await one(db,"SELECT * FROM users WHERE alias=?",(body.login_name,))
        if not user or not await asyncio.to_thread(PasswordHash.recommended().verify,body.password,user["password_hash"]):
            raise HTTPException(401)
        token,csrf=secrets.token_urlsafe(32),secrets.token_urlsafe(32)
        async with connect(path) as db:
            await db.execute("DELETE FROM sessions WHERE expires<=?",(time.time(),))
            await db.execute("INSERT INTO sessions VALUES (?,?,?,?)",(hashed(token),user["id"],hashed(csrf),time.time()+300))
            await db.commit()
        response.set_cookie("lab_session",token,httponly=True,samesite="strict",max_age=300)
        return {"account_alias":user["alias"],"user_id":user["id"],"csrf_token":csrf}

    @app.get("/api/requests")
    async def requests(request: Request):
        async with connect(path) as db:
            user=await actor(request,db)
            async with db.execute("SELECT r.id,r.title,a.id attachment_id FROM requests r LEFT JOIN attachments a ON a.request_id=r.id AND a.deleted=0 WHERE r.owner_id=? ORDER BY r.id LIMIT 128",(user["user_id"],)) as cur:
                rows=await cur.fetchall()
        return {"requests":[dict(r) for r in rows]}

    @app.get("/api/attachments/{attachment_id}")
    async def attachment(attachment_id: str, request: Request):
        async with connect(path) as db:
            user=await actor(request,db)
            row=await one(db,"SELECT * FROM attachments WHERE id=? AND uploader_id=? AND deleted=0",(attachment_id,user["user_id"]))
            if not row:
                raise HTTPException(404)
        return {"attachment_id":row["id"],"owner_alias":user["alias"],"filename":row["filename"],"content":row["content"]}

    @app.delete("/api/attachments/{attachment_id}")
    async def delete_attachment(attachment_id: str, request: Request):
        async with connect(path) as db:
            await db.execute("BEGIN IMMEDIATE")
            user=await actor(request,db)
            row=await one(db,"SELECT * FROM attachments WHERE id=? AND deleted=0",(attachment_id,))
            enforce=await one(db,"SELECT value FROM settings WHERE key='delete_owner_check'")
            # Development BAC-08 only: the evaluator selects this one missing owner check.
            if not row or not enforce or (enforce[0]=="1" and row["uploader_id"]!=user["user_id"]):
                raise HTTPException(404)
            await db.execute("UPDATE attachments SET deleted=1 WHERE id=?",(attachment_id,))
            delay=await one(db,"SELECT value FROM settings WHERE key='operator_delay_next_delete'")
            await db.execute("DELETE FROM settings WHERE key='operator_delay_next_delete'")
            await db.commit()
        if delay:
            # Operator-only bounded fault fixture: mutation committed, response delayed.
            # There is no HTTP route or worker tool that can arm it.
            await asyncio.sleep(min(8,max(0,float(delay[0]))))
        return {"attachment_id":attachment_id,"deleted":True}

    @app.get("/notifications/preview", response_class=HTMLResponse)
    async def notification_preview(request: Request):
        async with connect(path) as db:
            await actor(request, db)
            mode = await one(db, "SELECT value FROM settings WHERE key='notification_dom_html'")
            network = await one(db, "SELECT 1 FROM settings WHERE key='operator_browser_network'")
            delay = await one(db, "SELECT 1 FROM settings WHERE key='operator_browser_delay'")
        if delay:
            async with connect(path) as db:
                await db.execute("INSERT OR REPLACE INTO settings VALUES ('operator_browser_delay_started','1')")
                await db.commit()
            await asyncio.sleep(8)
        # XSS-08 development: the evaluator selects the sink, never a runtime parameter.
        sink = "innerHTML" if mode and mode[0] == "1" else "textContent"
        probes = """
fetch('http://169.254.169.254/latest').catch(()=>{});
fetch('http://host.docker.internal:8000/api/health').catch(()=>{});
fetch('/api/health').catch(()=>{});
localStorage.setItem('vv-context-probe','synthetic-only');
sessionStorage.setItem('vv-context-probe','synthetic-only');
new WebSocket('ws://198.51.100.10/socket');
window.open('http://198.51.100.10/popup');
const frame=document.createElement('iframe'); frame.src='http://198.51.100.10/frame';document.body.append(frame);
if(navigator.serviceWorker)navigator.serviceWorker.register('/notifications/sw').catch(()=>{});
window.__vvMarker('00000000-0000-0000-0000-000000000000');
const link=document.createElement('a');link.href=URL.createObjectURL(new Blob(['inert download fixture']));link.download='probe.txt';link.click();
""" if network else ""
        return HTMLResponse("""<!doctype html><html lang="id"><meta charset="utf-8">
<title>Pratinjau notifikasi lab</title><body><h1>Pratinjau notifikasi sintetis</h1>
<div id="preview"></div><script>
const preview=document.getElementById('preview');
preview.SINK=decodeURIComponent(location.hash.slice(1));
preview.dataset.ready='true';
PROBES
</script></body></html>""".replace("SINK", sink).replace("PROBES", probes))

    from lab.xss_catalog import register
    register(app, path, actor)
    from lab.uploads import register as register_uploads
    register_uploads(app, path, actor)
    from lab.business import register as register_business
    register_business(app, path, actor)
    return app
