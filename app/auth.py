import asyncio
import hmac
import secrets
import time
from dataclasses import dataclass

from fastapi import APIRouter, Depends, Request, Response
from pwdlib import PasswordHash

from app.common import AppError, audit, digest, rate_limit
from app.schemas import Login
from app.storage.db import all_rows, one

router = APIRouter()
passwords = PasswordHash.recommended()
_dummy_hash: str | None = None


def set_cookie(response: Response, request: Request, name: str, value: str, age: int):
    response.set_cookie(name, value, max_age=age, httponly=True,
                        secure=request.app.state.config.cookie_secure, samesite="strict", path="/")


def require_origin(request: Request):
    if request.headers.get("origin") != request.app.state.config.public_origin:
        raise AppError(403, "ORIGIN_DENIED", "Origin permintaan tidak diizinkan.")


@dataclass(frozen=True)
class Principal:
    user_id: str
    login_name: str
    session_hash: str


async def principal(request: Request) -> Principal:
    session = request.cookies.get("valvuln_session", "")
    async with request.app.state.db.connect() as conn:
        row = await one(conn, "SELECT s.*,u.login_name,u.enabled FROM sessions s JOIN users u USING(user_id) "
                             "WHERE session_id_hash=?", (digest(session),))
    if not row or not row["enabled"] or row["revoked_at"] or row["expires_at"] <= time.time():
        raise AppError(401, "SESSION_REQUIRED", "Silakan login kembali.")
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        require_origin(request)
        token = request.headers.get("x-csrf-token", "")
        if not token or not hmac.compare_digest(digest(token), row["csrf_hash"]):
            raise AppError(403, "CSRF_DENIED", "Token CSRF tidak sah.")
    return Principal(row["user_id"], row["login_name"], row["session_id_hash"])


async def member(conn, user: Principal, program_id: str, admin: bool = False):
    row = await one(conn, "SELECT m.role FROM memberships m JOIN programs p USING(program_id) "
                         "WHERE m.user_id=? AND m.program_id=? AND m.enabled=1 AND p.enabled=1",
                    (user.user_id, program_id))
    if not row:
        raise AppError(404, "NOT_FOUND", "Objek tidak ditemukan.")
    if admin and row["role"] != "PROGRAM_ADMIN":
        raise AppError(403, "ROLE_DENIED", "Tindakan memerlukan admin program.")
    return row["role"]


async def owned(conn, table: str, column: str, object_id: str, user: Principal, *, owner_only: bool = False):
    # Identifiers are constants from application call sites, never client input.
    if (table, column) not in {("conversations", "conversation_id"), ("reports", "report_id"),
                              ("runs", "run_id"), ("attachments", "attachment_id")}:
        raise ValueError("Unknown resource")
    row = await one(conn, f"SELECT * FROM {table} WHERE {column}=?", (object_id,))
    if not row:
        raise AppError(404, "NOT_FOUND", "Objek tidak ditemukan.")
    role = await member(conn, user, row["program_id"])
    if row["owner_user_id"] != user.user_id and role != "PROGRAM_ADMIN":
        raise AppError(404, "NOT_FOUND", "Objek tidak ditemukan.")
    if owner_only and row["owner_user_id"] != user.user_id:
        raise AppError(403, "OWNER_REQUIRED", "Hanya pemilik dapat mengubah draf laporan.")
    return row, role


@router.get("/api/auth/csrf")
async def csrf(request: Request, response: Response):
    # A nonce for login is server-recorded, expiring, and single-use.
    nonce, token, now = secrets.token_urlsafe(32), secrets.token_urlsafe(32), time.time()
    async with request.app.state.db.transaction() as conn:
        await rate_limit(conn, "csrf:" + (request.client.host if request.client else "local"), 30, 60)
        await conn.execute("DELETE FROM login_nonces WHERE expires_at<?", (now,))
        await conn.execute("INSERT INTO login_nonces VALUES (?,?,?)", (digest(nonce), digest(token), now+600))
    set_cookie(response, request, "valvuln_login", nonce, 600)
    return {"csrf_token": token}


@router.post("/api/auth/login")
async def login(body: Login, request: Request, response: Response):
    global _dummy_hash
    require_origin(request)
    db, now = request.app.state.db, time.time()
    ip = request.client.host if request.client else "local"
    async with db.transaction() as conn:
        await rate_limit(conn, "login-ip:"+ip, 10, 60)
        await rate_limit(conn, "login-user:"+body.login_name, 5, 60)
        nonce = await one(conn, "SELECT * FROM login_nonces WHERE nonce_hash=?",
                          (digest(request.cookies.get("valvuln_login", "")),))
        if (not nonce or nonce["expires_at"] <= now or
                not hmac.compare_digest(nonce["csrf_hash"], digest(request.headers.get("x-csrf-token", "")))):
            raise AppError(403, "CSRF_DENIED", "Token CSRF login tidak sah.")
        await conn.execute("DELETE FROM login_nonces WHERE nonce_hash=?", (nonce["nonce_hash"],))
        row = await one(conn, "SELECT * FROM users WHERE login_name=?", (body.login_name,))
    if _dummy_hash is None:
        _dummy_hash = await asyncio.to_thread(passwords.hash, secrets.token_urlsafe(32))
    valid = await asyncio.to_thread(passwords.verify, body.password, row["password_hash"] if row else _dummy_hash)
    if not valid or not row or not row["enabled"]:
        raise AppError(401, "LOGIN_FAILED", "Nama akun atau kata sandi tidak sesuai.")
    session, token = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    async with db.transaction() as conn:
        # Recheck enabled after hashing and rotate any prior session.
        enabled = await one(conn, "SELECT enabled FROM users WHERE user_id=?", (row["user_id"],))
        if not enabled["enabled"]:
            raise AppError(401, "LOGIN_FAILED", "Nama akun atau kata sandi tidak sesuai.")
        await conn.execute("UPDATE sessions SET revoked_at=? WHERE session_id_hash=?",
                           (now, digest(request.cookies.get("valvuln_session", ""))))
        active = await all_rows(conn, "SELECT session_id_hash FROM sessions WHERE user_id=? AND revoked_at IS NULL "
                                     "AND expires_at>? ORDER BY created_at DESC", (row["user_id"], now))
        for old in active[2:]:
            await conn.execute("UPDATE sessions SET revoked_at=? WHERE session_id_hash=?", (now, old[0]))
        await conn.execute("INSERT INTO sessions VALUES (?,?,?,?,?,NULL)",
                           (digest(session), row["user_id"], digest(token), now,
                            now + request.app.state.config.session_hours*3600))
        await audit(conn, row["user_id"], "LOGIN", {})
    set_cookie(response, request, "valvuln_session", session, request.app.state.config.session_hours*3600)
    set_cookie(response, request, "valvuln_csrf", token, request.app.state.config.session_hours*3600)
    response.delete_cookie("valvuln_login", path="/")
    return {"user_id": row["user_id"], "login_name": row["login_name"], "csrf_token": token}


@router.get("/api/me")
async def me(request: Request, user: Principal = Depends(principal)):
    async with request.app.state.db.connect() as conn:
        rows = await all_rows(conn, "SELECT m.program_id,m.role FROM memberships m JOIN programs p USING(program_id) "
                                   "WHERE user_id=? AND m.enabled=1 AND p.enabled=1", (user.user_id,))
    return {"user_id": user.user_id, "login_name": user.login_name, "memberships": [dict(r) for r in rows],
            "csrf_token": request.cookies.get("valvuln_csrf", "")}


@router.post("/api/auth/logout")
async def logout(request: Request, response: Response, user: Principal = Depends(principal)):
    async with request.app.state.db.transaction() as conn:
        await conn.execute("UPDATE sessions SET revoked_at=? WHERE session_id_hash=?", (time.time(), user.session_hash))
    response.delete_cookie("valvuln_session", path="/")
    response.delete_cookie("valvuln_csrf", path="/")
    return {"status": "logged_out"}
