"""Safe synthetic procurement workflow and its public business rules.

All mutations authenticate through the existing lab session/CSRF boundary.
No report-driven scripts, weakened modes, worker tools or evaluator labels.
"""
import json
from pathlib import Path
import time
from typing import Awaitable, Callable
from uuid import UUID, uuid4

import aiosqlite
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, StrictInt

from lab.storage import connect, one


RULES_VERSION = "procurement-controls-v1"
BUSINESS_RULES = [
    "Kuantitas harus bilangan bulat 1–1000; stok tidak boleh negatif.",
    "Pemohon hanya membuat, membaca dan mengubah permintaan miliknya.",
    "Petugas persetujuan/pemenuhan hanya memproses permintaan unit kewenangannya.",
    "Urutan wajib DRAFT → SUBMITTED → APPROVED → FULFILLED; persetujuan sendiri dilarang.",
    "Barang dan jumlah hanya dapat diubah saat DRAFT; perubahan memerlukan versi terbaru.",
    "Satu permintaan menghasilkan paling banyak satu pemenuhan; pengulangan yang sama mengembalikan hasil tersimpan.",
    "Stok diperiksa dan dikurangi atomik saat pemenuhan; persetujuan belum mereservasi stok.",
]


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CreateRequest(Input):
    title: str = Field(min_length=1, max_length=200)
    item_id: UUID
    quantity: StrictInt = Field(ge=1, le=1000)


class VersionInput(Input):
    expected_version: StrictInt = Field(ge=1, le=1000000)


class EditRequest(VersionInput):
    item_id: UUID
    quantity: StrictInt = Field(ge=1, le=1000)


async def snapshot(db: aiosqlite.Connection, rid: str) -> dict:
    row = await one(db, "SELECT b.*,r.owner_id,r.title,u.alias owner_alias,u.unit,i.name item_name,i.stock "
                    "FROM business_requests b JOIN requests r ON r.id=b.request_id "
                    "JOIN users u ON u.id=r.owner_id JOIN business_items i ON i.id=b.item_id WHERE b.request_id=?", (rid,))
    if not row:
        raise HTTPException(404, "REQUEST_NOT_FOUND")
    return dict(row)


def public(row: dict) -> dict:
    return {k: row[k] for k in ("request_id", "title", "owner_alias", "unit", "item_id", "item_name", "quantity", "state", "version", "stock")}


async def record(db: aiosqlite.Connection, rid: str, actor_id: str, operation: str, before: dict, after: dict) -> None:
    count = await one(db, "SELECT count(*) FROM business_events WHERE request_id=?", (rid,))
    if count[0] >= 128:
        raise HTTPException(409, "EVENT_LIMIT")
    await db.execute("INSERT INTO business_events VALUES (?,?,?,?,?,?,?)",
                     (str(uuid4()), rid, actor_id, operation, json.dumps(before), json.dumps(after), time.time()))


def require_version(row: dict, body: VersionInput) -> None:
    if row["version"] != body.expected_version:
        raise HTTPException(409, "STALE_VERSION")


async def staff(db: aiosqlite.Connection, user_id: str, unit: str) -> bool:
    return bool(await one(db, "SELECT 1 FROM business_staff WHERE user_id=? AND unit=?", (user_id, unit)))


def register(app: FastAPI, path: Path,
             actor: Callable[[Request, aiosqlite.Connection], Awaitable[aiosqlite.Row]]) -> None:
    @app.get("/api/business-rules")
    async def rules(request: Request):
        async with connect(path) as db:
            await actor(request, db)
        return {"version": RULES_VERSION, "rules": BUSINESS_RULES, "synthetic": True}

    @app.get("/api/items")
    async def items(request: Request):
        async with connect(path) as db:
            await actor(request, db)
            async with db.execute("SELECT id,name,stock FROM business_items ORDER BY id LIMIT 64") as cursor:
                rows = await cursor.fetchall()
        return {"items": [dict(row) for row in rows], "synthetic": True}

    @app.post("/api/requests", status_code=201)
    async def create(body: CreateRequest, request: Request):
        async with connect(path) as db:
            await db.execute("BEGIN IMMEDIATE")
            user = await actor(request, db)
            if not await one(db, "SELECT 1 FROM business_items WHERE id=?", (str(body.item_id),)):
                raise HTTPException(404, "ITEM_NOT_FOUND")
            if (await one(db, "SELECT count(*) FROM business_requests"))[0] >= 64:
                raise HTTPException(409, "REQUEST_LIMIT")
            rid = str(uuid4())
            await db.execute("INSERT INTO requests(id,owner_id,title) VALUES (?,?,?)", (rid, user["user_id"], body.title))
            await db.execute("INSERT INTO request_details VALUES (?,?)", (rid, ""))
            await db.execute("INSERT INTO business_requests VALUES (?,?,?,'DRAFT',1,NULL)", (rid, str(body.item_id), body.quantity))
            result = public(await snapshot(db, rid))
            await record(db, rid, user["user_id"], "CREATE", {}, result)
            await db.commit()
        return result

    @app.get("/api/requests/{request_id}")
    async def detail(request_id: UUID, request: Request):
        async with connect(path) as db:
            await db.execute("BEGIN")
            user = await actor(request, db)
            row = await snapshot(db, str(request_id))
            if row["owner_id"] != user["user_id"] and not await staff(db, user["user_id"], row["unit"]):
                raise HTTPException(404, "REQUEST_NOT_FOUND")
            async with db.execute("SELECT e.id,e.operation,u.alias actor_alias,e.before_json,e.after_json "
                                  "FROM business_events e JOIN users u ON u.id=e.actor_id WHERE e.request_id=? ORDER BY e.rowid LIMIT 128", (str(request_id),)) as cursor:
                events = await cursor.fetchall()
        return {**public(row), "events": [{"event_id": e["id"], "operation": e["operation"], "actor_alias": e["actor_alias"],
                                           "before": json.loads(e["before_json"]), "after": json.loads(e["after_json"])} for e in events]}

    @app.patch("/api/requests/{request_id}")
    async def edit(request_id: UUID, body: EditRequest, request: Request):
        rid = str(request_id)
        async with connect(path) as db:
            await db.execute("BEGIN IMMEDIATE")
            user = await actor(request, db)
            row = await snapshot(db, rid)
            if row["owner_id"] != user["user_id"]:
                raise HTTPException(404, "REQUEST_NOT_FOUND")
            require_version(row, body)
            if row["state"] != "DRAFT":
                raise HTTPException(409, "MATERIAL_FIELDS_LOCKED")
            if not await one(db, "SELECT 1 FROM business_items WHERE id=?", (str(body.item_id),)):
                raise HTTPException(404, "ITEM_NOT_FOUND")
            await db.execute("UPDATE business_requests SET item_id=?,quantity=?,version=version+1 WHERE request_id=?",
                             (str(body.item_id), body.quantity, rid))
            result = public(await snapshot(db, rid))
            await record(db, rid, user["user_id"], "EDIT", public(row), result)
            await db.commit()
        return result

    async def transition(rid: str, body: VersionInput, request: Request, operation: str):
        async with connect(path) as db:
            await db.execute("BEGIN IMMEDIATE")
            user = await actor(request, db)
            row = await snapshot(db, rid)
            if operation == "SUBMIT":
                if row["owner_id"] != user["user_id"]:
                    raise HTTPException(404, "REQUEST_NOT_FOUND")
            else:
                if not await staff(db, user["user_id"], row["unit"]):
                    raise HTTPException(404, "REQUEST_NOT_FOUND")
                if operation == "APPROVE" and row["owner_id"] == user["user_id"]:
                    raise HTTPException(403, "SELF_APPROVAL_DENIED")
            if operation == "FULFILL":
                existing = await one(db, "SELECT * FROM business_fulfillments WHERE request_id=?", (rid,))
                if existing:
                    if row["state"] != "FULFILLED" or existing["request_version"] != body.expected_version:
                        raise HTTPException(409, "STALE_VERSION")
                    return dict(existing)
            require_version(row, body)
            expected, following = {"SUBMIT": ("DRAFT", "SUBMITTED"), "APPROVE": ("SUBMITTED", "APPROVED"),
                                   "FULFILL": ("APPROVED", "FULFILLED")}[operation]
            if row["state"] != expected:
                raise HTTPException(409, "STATE_TRANSITION_DENIED")
            fulfillment = None
            if operation == "FULFILL":
                async with db.execute("UPDATE business_items SET stock=stock-? WHERE id=? AND stock>=?",
                                      (row["quantity"], row["item_id"], row["quantity"])) as cursor:
                    if cursor.rowcount != 1:
                        raise HTTPException(409, "INSUFFICIENT_STOCK")
                fulfillment = {"id": str(uuid4()), "request_id": rid, "actor_id": user["user_id"], "quantity": row["quantity"],
                               "request_version": body.expected_version, "stock_before": row["stock"],
                               "stock_after": row["stock"]-row["quantity"], "created_at": time.time()}
                await db.execute("INSERT INTO business_fulfillments VALUES (?,?,?,?,?,?,?,?)", tuple(fulfillment.values()))
            await db.execute("UPDATE business_requests SET state=?,version=version+1,approved_by=? WHERE request_id=?",
                             (following, user["user_id"] if operation == "APPROVE" else row["approved_by"], rid))
            result = public(await snapshot(db, rid))
            await record(db, rid, user["user_id"], operation, public(row), result)
            await db.commit()
        return fulfillment or result

    @app.post("/api/requests/{request_id}/submit")
    async def submit(request_id: UUID, body: VersionInput, request: Request):
        return await transition(str(request_id), body, request, "SUBMIT")

    @app.post("/api/requests/{request_id}/approve")
    async def approve(request_id: UUID, body: VersionInput, request: Request):
        return await transition(str(request_id), body, request, "APPROVE")

    @app.post("/api/requests/{request_id}/fulfill")
    async def fulfill(request_id: UUID, body: VersionInput, request: Request):
        return await transition(str(request_id), body, request, "FULFILL")
