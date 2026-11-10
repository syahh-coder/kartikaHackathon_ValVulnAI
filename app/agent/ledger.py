import time

from app.common import AppError, uid
from app.storage.db import one


async def budget_used(conn) -> int:
    row = await one(conn, "SELECT coalesce(sum(CASE WHEN status='SETTLED' THEN actual_idr "
                          "WHEN status IN ('RESERVED','COST_UNKNOWN') THEN reserved_idr ELSE 0 END),0) FROM ledger")
    return row[0]


async def reserve(conn, run_id: str | None, maximum_idr: int, budget_idr: int,
                  attempt_id: str | None = None, *, triage_id: str | None = None,
                  evaluation_id: str | None = None) -> str:
    if await one(conn, "SELECT 1 FROM provider_attempts WHERE error_code='COST_EXCEEDS_RESERVATION'"):
        raise AppError(503, "COST_REVIEW_REQUIRED", "Biaya memerlukan rekonsiliasi operator sebelum dispatch baru.")
    if maximum_idr < 0 or maximum_idr + await budget_used(conn) > budget_idr:
        raise AppError(429, "BUDGET_LIMIT", "Reservasi melampaui sisa budget.")
    entry = uid()
    await conn.execute("INSERT INTO ledger(entry_id,run_id,provider_attempt_id,reserved_idr,status,created_at,triage_id,evaluation_id) "
                       "VALUES (?,?,?,?,'RESERVED',?,?,?)",
                       (entry, run_id, attempt_id, maximum_idr, time.time(), triage_id, evaluation_id))
    return entry


async def reconcile(conn, entry_id: str, actual_idr: int | None):
    row = await one(conn, "SELECT * FROM ledger WHERE entry_id=?", (entry_id,))
    if not row or row["status"] not in {"RESERVED", "COST_UNKNOWN"}:
        raise AppError(409, "LEDGER_CONFLICT", "Reservasi sudah direkonsiliasi.")
    if actual_idr is None:
        await conn.execute("UPDATE ledger SET status='COST_UNKNOWN' WHERE entry_id=?", (entry_id,))
    elif not 0 <= actual_idr <= row["reserved_idr"]:
        raise AppError(409, "COST_EXCEEDS_RESERVATION", "Biaya melampaui reservasi; perlu rekonsiliasi operator.")
    else:
        await conn.execute("UPDATE ledger SET actual_idr=?,status='SETTLED' WHERE entry_id=?", (actual_idr, entry_id))
