import asyncio
from contextlib import asynccontextmanager, suppress
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
from lab.manual_access import register_manual_home, validate_manual_origin
from boundary.files import read_json


def hashed(value: str):
    return hashlib.sha256(value.encode()).hexdigest()


class Login(BaseModel):
    model_config = ConfigDict(extra="forbid")
    login_name: str = Field(max_length=64)
    password: str = Field(max_length=128)


def create_app(db_path: Path | None = None):
    path = db_path or Path(os.environ.get("LAB_DATA_DIR", "/data")) / "lab.sqlite3"
    manual_origin = validate_manual_origin(os.environ.get("LAB_MANUAL_ORIGIN", ""))
    allowed_origins = {"http://lab:8001"}
    if manual_origin:
        allowed_origins.add(manual_origin)
    shared_manual = os.environ.get("LAB_SHARED_MANUAL") == "1"
    control_dir = Path(os.environ["LAB_RESET_CONTROL_DIR"]) if os.environ.get("LAB_RESET_CONTROL_DIR") else None
    if shared_manual and (manual_origin != "http://127.0.0.1:8001" or control_dir is None):
        raise ValueError("Shared manual target requires its private control channel and loopback origin")
    manual_lock = asyncio.Lock()
    @asynccontextmanager
    async def lifespan(app):
        await migrate(path)
        reset_task = None
        if control_dir is not None:
            from lab.reset_control import loop
            reset_task = asyncio.create_task(loop(control_dir, path, manual_lock))
        try:
            yield
        finally:
            if reset_task:
                reset_task.cancel()
                with suppress(asyncio.CancelledError):
                    await reset_task
    app = FastAPI(title="Portal Lab Sintetis", docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)
    app.add_middleware(BodyLimit,maximum=4096)
    register_manual_home(app, manual_origin, shared=shared_manual)

    async def manual_enabled():
        try:
            session = read_json(control_dir, "manual-session.json", 4096)
            if session.get("active") is not True or time.time() >= session["expires_at"]:
                return False
            async with connect(path) as db:
                snapshot = await one(db, "SELECT value FROM settings WHERE key='snapshot_id'")
            return bool(snapshot and session.get("snapshot_id") == snapshot[0])
        except (OSError, ValueError, KeyError, TypeError):
            return False

    @app.middleware("http")
    async def manual_gate(request: Request, call_next):
        # Worker identity is its fixed internal peer IP, not a spoofable Host/Origin.
        manual_peer = shared_manual and (not request.client or request.client.host != "172.30.74.2")
        public = request.method == "GET" and request.url.path in {"/", "/api/health"}
        if manual_peer and not public:
            async with manual_lock:
                if not await manual_enabled():
                    from fastapi.responses import JSONResponse
                    return JSONResponse({"error_code": "MANUAL_SESSION_REQUIRED", "detail": "Aktifkan pengujian manual melalui tombol admin ValVuln terlebih dahulu."}, status_code=409)
                return await call_next(request)
        return await call_next(request)

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
            if (request.headers.get("origin") not in allowed_origins or
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
        if request.headers.get("origin") not in allowed_origins:
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

    if manual_origin:
        @app.get("/manual/objects", include_in_schema=False)
        async def manual_objects(request: Request):
            async with connect(path) as db:
                user = await actor(request, db)
                objects = {}
                for table, owner in (("requests", "owner_id"), ("attachments", "uploader_id"),
                                     ("catalog_items", "owner_id"), ("suppliers", "owner_id")):
                    async with db.execute(f"SELECT id FROM {table} WHERE {owner}=? ORDER BY id LIMIT 128", (user["user_id"],)) as cursor:
                        objects[table] = [row[0] for row in await cursor.fetchall()]
                snapshot = await one(db, "SELECT value FROM settings WHERE key='snapshot_id'")
            return {"account_alias": user["alias"], "objects": objects,
                    "snapshot_id": snapshot[0] if snapshot else None,
                    "purpose": "SHARED_WORKER_TARGET" if shared_manual else "MANUAL_COPY_ONLY"}

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
