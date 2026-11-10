"""Synthetic upload storage and presentation; conditions selected only by maintenance."""
import base64
import binascii
import hashlib
from html import escape
from pathlib import Path
from typing import Awaitable, Callable
from uuid import uuid4

import aiosqlite
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator

from lab.storage import connect, one

POINTS = {"UP-01": "upload_svg_inline", "UP-02": "upload_html_inline",
          "UP-03": "upload_shared_name", "UP-04": "upload_filename_html"}
MAX_CONTENT = 1024


class UploadInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: str = Field(pattern=r"^[a-f0-9-]{36}$")
    filename: str = Field(min_length=1, max_length=256)
    media_type: str = Field(pattern=r"^(text/plain|text/html|image/svg\+xml)$")
    content_base64: str = Field(min_length=1, max_length=1368)

    @field_validator("filename")
    @classmethod
    def basename(cls, value: str) -> str:
        if any(c in value for c in ("/", "\\", "\x00", "\r", "\n")) or value in {".", ".."}:
            raise ValueError("FILENAME_DENIED")
        return value

    def content(self) -> bytes:
        try:
            content = base64.b64decode(self.content_base64, validate=True)
        except (ValueError, binascii.Error):
            raise HTTPException(422, "Invalid base64")
        if not content or len(content) > MAX_CONTENT:
            raise HTTPException(413, "Fixture exceeds 1024 bytes")
        return content


async def mode(db: aiosqlite.Connection, key: str) -> bool:
    row = await one(db, "SELECT value FROM settings WHERE key=?", (key,))
    return bool(row and row[0] == "1")


def register(app: FastAPI, path: Path,
             actor: Callable[[Request, aiosqlite.Connection], Awaitable[aiosqlite.Row]]) -> None:
    async def authorized_request(db: aiosqlite.Connection, rid: str, user: aiosqlite.Row, *, write: bool = False) -> None:
        row = await one(db, "SELECT owner_id FROM requests WHERE id=?", (rid,))
        assigned = await one(db, "SELECT 1 FROM request_reviewers WHERE request_id=? AND reviewer_id=?", (rid, user["user_id"]))
        if not row or (row[0] != user["user_id"] and (write or not assigned)):
            raise HTTPException(404)

    async def store(body: UploadInput, request: Request) -> dict:
        content = body.content()
        async with connect(path) as db:
            await db.execute("BEGIN IMMEDIATE")
            user = await actor(request, db)
            await authorized_request(db, body.request_id, user, write=True)
            if (await one(db, "SELECT count(*) FROM uploads"))[0] >= 64:
                raise HTTPException(409, "Synthetic upload capacity reached")
            upload_id = str(uuid4())
            # UP-03: a deliberately shared storage namespace; metadata ownership still checked.
            key = ("shared:" + hashlib.sha256(body.filename.encode()).hexdigest()
                   if await mode(db, "upload_shared_name") else "unique:" + str(uuid4()))
            await db.execute("INSERT INTO upload_blobs VALUES (?,?) ON CONFLICT(storage_key) DO UPDATE SET content=excluded.content", (key, content))
            await db.execute("INSERT INTO uploads VALUES (?,?,?,?,?,?)",
                (upload_id, body.request_id, user["user_id"], body.filename, body.media_type, key))
            await db.commit()
        return {"upload_id": upload_id, "request_id": body.request_id, "filename": body.filename,
                "media_type": body.media_type, "content_sha256": hashlib.sha256(content).hexdigest(), "size": len(content)}

    @app.post("/api/attachments")
    async def upload(body: UploadInput, request: Request):
        return await store(body, request)

    @app.post("/api/requests/{request_id}/attachments")
    async def request_upload(request_id: str, body: UploadInput, request: Request):
        if request_id != body.request_id:
            raise HTTPException(422)
        return await store(body, request)

    async def owned_upload(upload_id: str, request: Request) -> dict:
        async with connect(path) as db:
            user = await actor(request, db)
            row = await one(db, "SELECT u.*,b.content FROM uploads u JOIN upload_blobs b USING(storage_key) WHERE u.id=? AND u.uploader_id=?", (upload_id, user["user_id"]))
            if not row:
                raise HTTPException(404)
        return dict(row)

    @app.get("/attachments/{upload_id}/download")
    async def download(upload_id: str, request: Request):
        row = await owned_upload(upload_id, request)
        # Constant filename avoids reflecting attacker metadata in response headers.
        return Response(row["content"], media_type="application/octet-stream", headers={
            "Content-Disposition": 'attachment; filename="synthetic-fixture.bin"',
            "Content-Security-Policy": "sandbox; default-src 'none'"})

    @app.get("/attachments/{upload_id}/preview")
    async def svg_preview(upload_id: str, request: Request):
        row = await owned_upload(upload_id, request)
        if row["media_type"] != "image/svg+xml":
            raise HTTPException(415)
        async with connect(path) as db:
            inline = await mode(db, "upload_svg_inline")
        if inline:
            return Response(row["content"], media_type="image/svg+xml")
        return HTMLResponse('<!doctype html><html><body><h1>SVG sebagai teks</h1><pre id="preview">'
            + escape(row["content"].decode("utf-8", errors="replace")) + '</pre></body></html>')

    @app.get("/documents/{upload_id}/preview")
    async def html_preview(upload_id: str, request: Request):
        row = await owned_upload(upload_id, request)
        if row["media_type"] != "text/html":
            raise HTTPException(415)
        async with connect(path) as db:
            inline = await mode(db, "upload_html_inline")
        if inline:
            return HTMLResponse(row["content"])
        return HTMLResponse('<!doctype html><html><body><h1>Dokumen sebagai teks</h1><pre id="preview">'
            + escape(row["content"].decode("utf-8", errors="replace")) + '</pre></body></html>')

    @app.get("/documents/{upload_id}/text")
    async def text_view(upload_id: str, request: Request):
        row = await owned_upload(upload_id, request)
        return HTMLResponse('<!doctype html><html><body><pre id="preview">'
            + escape(row["content"].decode("utf-8", errors="replace")) + '</pre></body></html>')

    @app.get("/requests/{request_id}/attachments", response_class=HTMLResponse)
    @app.get("/requests/{request_id}/attachment-labels", response_class=HTMLResponse)
    async def listing(request_id: str, request: Request):
        async with connect(path) as db:
            user = await actor(request, db)
            await authorized_request(db, request_id, user)
            # Latest upload is the selected item; earlier files remain accessible by ID.
            row = await one(db, "SELECT filename FROM uploads WHERE request_id=? ORDER BY rowid DESC LIMIT 1", (request_id,))
            name = row[0] if row else "Belum ada lampiran"
            raw = request.url.path.endswith("/attachments") and await mode(db, "upload_filename_html")
        value = name if raw else escape(name)
        return HTMLResponse('<!doctype html><html lang="id"><meta charset="utf-8"><title>Lampiran sintetis</title>'
            '<body><h1>Lampiran permintaan sintetis</h1><div id="preview">' + value +
            '</div><script>document.getElementById("preview").dataset.ready="true";</script></body></html>')
