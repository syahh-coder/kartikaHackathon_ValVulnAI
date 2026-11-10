import hashlib
import json
import time
import uuid

from fastapi import Request
from fastapi.responses import JSONResponse

from app.storage.db import one


def uid() -> str:
    return str(uuid.uuid4())


def digest(value: str | bytes) -> str:
    return hashlib.sha256(value.encode() if isinstance(value, str) else value).hexdigest()


def packed(value) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


class AppError(Exception):
    def __init__(self, status: int, code: str, message: str, retryable: bool = False,
                 *, field_errors: list[dict[str, str]] | None = None):
        self.status, self.code, self.message, self.retryable = status, code, message, retryable
        self.field_errors = field_errors or []


async def error_response(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(status_code=exc.status, content={
        "request_id": getattr(request.state, "request_id", uid()), "error_code": exc.code,
        "message": exc.message, "field_errors": exc.field_errors, "retryable": exc.retryable,
    }, headers={"Retry-After": "60"} if exc.status == 429 else {})


async def audit(conn, actor: str | None, event: str, details: dict, run_id: str | None = None):
    await conn.execute("INSERT INTO audit_events VALUES (?,?,?,?,?,?)",
                       (uid(), actor, run_id, event, packed(details), time.time()))


async def rate_limit(conn, bucket: str, maximum: int, seconds: int):
    now = time.time()
    await conn.execute("DELETE FROM rate_events WHERE event_at<?", (now - 3600,))
    row = await one(conn, "SELECT count(*) n FROM rate_events WHERE bucket=? AND event_at>?",
                    (bucket, now - seconds))
    if row["n"] >= maximum:
        raise AppError(429, "RATE_LIMIT", "Batas permintaan tercapai. Coba lagi nanti.", True)
    await conn.execute("INSERT INTO rate_events VALUES (?,?)", (bucket, now))
