"""Synthetic portal features. Conditions are maintenance-only, never request flags."""
from html import escape
from uuid import uuid4

from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, ConfigDict, Field

from lab.storage import connect, one


# This is lab implementation, not an answer manifest or runtime validator context.
POINTS = {
    "XSS-01": "catalog_search_html", "XSS-02": "catalog_note_html",
    "XSS-03": "review_reason_html", "XSS-04": "comment_name_html",
    "XSS-05": "supplier_name_html", "XSS-06": "tracking_attribute_html",
    "XSS-07": "request_fragment_html",
}


class TextInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    value: str = Field(min_length=1, max_length=1024)


def document(title: str, content: str, script: str = "") -> HTMLResponse:
    # content/script are composed by these fixed handlers; the dashboard never renders them.
    return HTMLResponse('<!doctype html><html lang="id"><meta charset="utf-8">'
        f'<title>{escape(title)}</title><body><h1>{escape(title)}</h1>{content}'
        '<script>document.documentElement.dataset.ready="true";</script>'
        + script + '</body></html>')


async def enabled(db, key):
    row = await one(db, "SELECT value FROM settings WHERE key=?", (key,))
    return bool(row and row[0] == "1")


def register(app, path, actor):
    async def request_object(db, object_id, user, *, writing=False):
        row = await one(db, "SELECT * FROM requests WHERE id=?", (object_id,))
        assigned = await one(db, "SELECT 1 FROM request_reviewers WHERE request_id=? AND reviewer_id=?", (object_id, user["user_id"]))
        if not row or (row["owner_id"] != user["user_id"] and (writing or not assigned)):
            raise HTTPException(404)
        return row

    @app.get("/catalog/search")
    async def search(request: Request, q: str = "", view: str = "result"):
        if len(q) > 1024 or view not in {"result", "text"}:
            raise HTTPException(422)
        async with connect(path) as db:
            await actor(request, db)
            # Reflected HTML text context; a separate text renderer is always escaped.
            value = q if view == "result" and await enabled(db, "catalog_search_html") else escape(q)
        return document("Pencarian katalog sintetis", f'<div id="probe">{value}</div>')

    @app.patch("/api/catalog/items/{item_id}/note")
    async def edit_note(item_id: str, body: TextInput, request: Request):
        async with connect(path) as db:
            user = await actor(request, db)
            item = await one(db, "SELECT * FROM catalog_items WHERE id=? AND owner_id=?", (item_id, user["user_id"]))
            if not item:
                raise HTTPException(404)
            await db.execute("UPDATE catalog_items SET note=? WHERE id=?", (body.value, item_id))
            # Independent text field for the negative control, populated through the same input.
            await db.execute("UPDATE catalog_items SET description=? WHERE id=?", (body.value, item_id))
            await db.commit()
        return {"updated": True, "item_id": item_id}

    @app.get("/catalog/items/{item_id}")
    async def item_detail(item_id: str, request: Request, field: str = "note"):
        if field not in {"note", "description"}:
            raise HTTPException(422)
        async with connect(path) as db:
            await actor(request, db)
            # Catalog notes are intentionally shared; private attachments remain separate.
            item = await one(db, "SELECT * FROM catalog_items WHERE id=?", (item_id,))
            if not item:
                raise HTTPException(404)
            value = item[field]
            if field == "description" or not await enabled(db, "catalog_note_html"):
                value = escape(value)
        return document("Detail barang sintetis", f'<section id="probe">{value}</section>')

    @app.patch("/api/requests/{request_id}/reason")
    async def edit_reason(request_id: str, body: TextInput, request: Request):
        async with connect(path) as db:
            user = await actor(request, db)
            await request_object(db, request_id, user, writing=True)
            await db.execute("UPDATE request_details SET reason=? WHERE request_id=?", (body.value, request_id))
            await db.commit()
        return {"updated": True, "request_id": request_id}

    @app.get("/requests/{request_id}/review")
    async def review(request_id: str, request: Request, view: str = "review"):
        if view not in {"review", "audit"}:
            raise HTTPException(422)
        async with connect(path) as db:
            user = await actor(request, db)
            if not await one(db, "SELECT 1 FROM request_reviewers WHERE request_id=? AND reviewer_id=?", (request_id, user["user_id"])):
                raise HTTPException(403)
            await request_object(db, request_id, user)
            detail = await one(db, "SELECT reason FROM request_details WHERE request_id=?", (request_id,))
            if not detail:
                raise HTTPException(404)
            value = detail[0]
            if view == "audit" or not await enabled(db, "review_reason_html"):
                value = escape(value)
        return document("Review permintaan sintetis", f'<blockquote id="probe">{value}</blockquote>')

    @app.patch("/api/profile/display-name")
    async def edit_name(body: TextInput, request: Request):
        async with connect(path) as db:
            user = await actor(request, db)
            await db.execute("UPDATE users SET display_name=? WHERE id=?", (body.value, user["user_id"]))
            await db.commit()
        return {"updated": True}

    @app.post("/api/requests/{request_id}/comments")
    async def add_comment(request_id: str, body: TextInput, request: Request):
        async with connect(path) as db:
            user = await actor(request, db)
            await request_object(db, request_id, user, writing=True)
            comment_id = str(uuid4())
            # A bounded replacement keeps this synthetic feature small; no arbitrary SQL/script.
            await db.execute("DELETE FROM comments WHERE request_id=? AND author_id=?", (request_id, user["user_id"]))
            await db.execute("INSERT INTO comments VALUES (?,?,?,?)", (comment_id, request_id, user["user_id"], body.value))
            await db.commit()
        return {"comment_id": comment_id}

    @app.get("/requests/{request_id}/comments")
    async def comment_list(request_id: str, request: Request, field: str = "name"):
        if field not in {"name", "body"}:
            raise HTTPException(422)
        async with connect(path) as db:
            user = await actor(request, db)
            await request_object(db, request_id, user)
            comment = await one(db, "SELECT c.body,u.display_name FROM comments c JOIN users u ON u.id=c.author_id WHERE c.request_id=? ORDER BY c.rowid DESC LIMIT 1", (request_id,))
            if not comment:
                raise HTTPException(404)
            value = comment["display_name"] if field == "name" else comment["body"]
            if field == "body" or not await enabled(db, "comment_name_html"):
                value = escape(value)
        return document("Komentar permintaan sintetis", f'<div id="probe">{value}</div>')

    @app.patch("/api/suppliers/{supplier_id}/name")
    async def edit_supplier(supplier_id: str, body: TextInput, request: Request):
        async with connect(path) as db:
            user = await actor(request, db)
            supplier = await one(db, "SELECT * FROM suppliers WHERE id=? AND owner_id=?", (supplier_id, user["user_id"]))
            if not supplier:
                raise HTTPException(404)
            await db.execute("UPDATE suppliers SET name=?,code=? WHERE id=?", (body.value, body.value, supplier_id))
            await db.commit()
        return {"updated": True, "supplier_id": supplier_id}

    @app.get("/suppliers")
    async def supplier_list(request: Request, supplier_id: str, field: str = "name"):
        if field not in {"name", "code"}:
            raise HTTPException(422)
        async with connect(path) as db:
            await actor(request, db)
            supplier = await one(db, "SELECT * FROM suppliers WHERE id=?", (supplier_id,))
            if not supplier:
                raise HTTPException(404)
            value = supplier[field]
            if field == "code" or not await enabled(db, "supplier_name_html"):
                value = escape(value)
        return document("Daftar pemasok sintetis", f'<div id="probe">{value}</div>')

    @app.get("/tracking")
    async def tracking(request: Request, ref: str = "", view: str = "tracking"):
        if len(ref) > 1024 or view not in {"tracking", "text"}:
            raise HTTPException(422)
        async with connect(path) as db:
            await actor(request, db)
            value = ref if view == "tracking" and await enabled(db, "tracking_attribute_html") else escape(ref, quote=True)
        # Attribute-context injection, distinct from element text/DOM sinks.
        return document("Pelacakan sintetis", f'<input id="probe" value="{value}">')

    @app.get("/requests/view")
    async def fragment_panel(request: Request, view: str = "detail"):
        if view not in {"detail", "text"}:
            raise HTTPException(422)
        async with connect(path) as db:
            await actor(request, db)
            html_sink = view == "detail" and await enabled(db, "request_fragment_html")
        # Independent frontend panel. The fragment never reaches the HTTP server.
        sink = "innerHTML" if html_sink else "textContent"
        return document("Panel permintaan sintetis", '<div id="probe"></div>',
            '<script>const panel=document.getElementById("probe");'
            f'panel.{sink}=decodeURIComponent(location.hash.slice(1));</script>')
