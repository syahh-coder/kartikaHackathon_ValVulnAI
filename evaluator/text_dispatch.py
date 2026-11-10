"""One text prediction per slot, charged to the existing application ledger. No target imports."""
import asyncio
import json
import time
from contextlib import suppress

from app.agent.ledger import reconcile, reserve
from app.auth import Principal
from app.common import AppError, packed, uid
from app.providers.contracts import ProviderFailure
from app.providers.openrouter import TextFailure
from app.providers.text_provider import expected_model, input_token_bound, profile, require_configuration, secret
from app.providers.text_provider import transport as make_transport
from app.providers.redaction import redact_value
from app.storage.db import one
from evaluator.functional_v2 import EvaluationError, parse_prediction
from evaluator.text_context import CONTRACT, PROMPT_VERSION, sha


def configuration(config) -> dict:
    c = config
    return {"provider": c.triage_provider, "model": c.triage_model, "provider_slug": c.triage_provider_slug,
            "provider_name": c.triage_provider_name, "access_tier": c.triage_access_tier,
            "price_snapshot": c.triage_price_snapshot, "prompt_price": str(c.triage_prompt_usd_per_million),
            "completion_price": str(c.triage_completion_usd_per_million), "usd_to_idr": str(c.triage_usd_to_idr),
            "reservation_idr": c.triage_reservation_idr, "budget_idr": c.budget_idr,
            "timeout_seconds": c.triage_timeout_seconds, "input_limit": 8192, "output_limit": 1024,
            "temperature": 0, "attempts_per_slot": 1, "fallbacks": [], "tools": [],
            "contract_hash": sha(packed(CONTRACT)), "prompt_version": PROMPT_VERSION, **profile(c)}


async def guard_user(conn, user: Principal):
    if not await one(conn, "SELECT 1 FROM users WHERE user_id=? AND enabled=1", (user.user_id,)):
        raise EvaluationError("USER_DISABLED")


async def dispatch(db, config, user, *, freeze_hash, report_key, arm, text, references,
                   guard, run_id=None, transport=None) -> dict:
    """No retry: ambiguous outcomes remain charged/unknown and cannot be replayed by this runner."""
    if config.triage_mode != "live":
        raise EvaluationError("CONFIGURATION_REQUIRED")
    require_configuration(config)
    if input_token_bound(config, text, **CONTRACT) > 8192:
        raise EvaluationError("CONTEXT_LIMIT")
    evaluation_id, attempt_id, call_id = uid(), uid(), uid()
    start = time.monotonic()
    async with db.transaction() as conn:
        await guard_user(conn, user)
        await guard(conn)
        if await one(conn, "SELECT 1 FROM evaluation_jobs WHERE status='DISPATCHED'"):
            raise EvaluationError("EVALUATION_ACTIVE_OR_INTERRUPTED")
        if await one(conn, "SELECT 1 FROM text_triages WHERE status IN ('PENDING','RUNNING')"):
            raise EvaluationError("TEXT_TRIAGE_ACTIVE")
        if await one(conn, "SELECT 1 FROM evaluation_jobs WHERE freeze_hash=? AND report_key=? AND arm=?",
                     (freeze_hash, report_key, arm)):
            raise EvaluationError("SLOT_ALREADY_DISPATCHED")
        await conn.execute("INSERT INTO evaluation_jobs(evaluation_id,freeze_hash,report_key,arm,requested_by,run_id,status,"
                           "input_json,config_json,created_at) VALUES (?,?,?,?,?,?,'DISPATCHED',?,?,?)",
                           (evaluation_id, freeze_hash, report_key, arm, user.user_id, run_id, text,
                            packed(configuration(config)), time.time()))
        entry = await reserve(conn, None, config.triage_reservation_idr, config.budget_idr, attempt_id,
                              evaluation_id=evaluation_id)
        await conn.execute("INSERT INTO provider_attempts(provider_attempt_id,call_id,provider_id,model_id,status,created_at,evaluation_id) "
                           "VALUES (?,?,?,?,'DISPATCHED',?,?)",
                           (attempt_id, call_id, config.triage_provider, config.triage_model, time.time(), evaluation_id))
    reply, error, prediction, raw, cost = None, None, None, None, None
    metadata = {"input_hash": sha(text), **configuration(config)}
    adapter = transport if transport is not None else make_transport(config, **CONTRACT)
    task = asyncio.create_task(adapter.dispatch(call_id, text))
    try:
        deadline = start + config.triage_timeout_seconds
        while True:
            if time.monotonic() >= deadline:
                raise ProviderFailure("TRANSPORT_TIMEOUT")
            async with db.connect() as conn:
                await guard_user(conn, user)
                await guard(conn)
            done, _ = await asyncio.wait([task], timeout=min(0.1, max(0, deadline-time.monotonic())))
            if done:
                reply = task.result()
                break
        result = reply.result
        raw, cost = reply.redacted_response, result.actual_cost_idr
        metadata.update({"resolved_model": result.resolved_model_id, "inference_provider": result.inference_provider,
                         "provider_request_id": result.provider_request_id, "usage": result.usage,
                         "cost_usd": reply.cost_usd, "reported_actual_cost_idr": cost,
                         "finish_reason": result.finish_reason})
        if cost is not None and cost > config.triage_reservation_idr:
            raise ProviderFailure("COST_EXCEEDS_RESERVATION")
        if (result.call_id != call_id or result.provider_id != config.triage_provider or
                result.requested_model_id != config.triage_model or result.resolved_model_id != expected_model(config) or
                result.inference_provider != config.triage_provider_name):
            raise ProviderFailure("PROVIDER_DRIFT")
        if result.refusal:
            raise ProviderFailure("PROVIDER_REFUSED")
        if result.finish_reason != "stop":
            raise ProviderFailure("INCOMPLETE_RESPONSE")
        parsed = parse_prediction(result.text, references)
        prediction = redact_value(parsed.model_dump(), secret(config))
        async with db.connect() as conn:
            await guard_user(conn, user)
            await guard(conn)
    except asyncio.CancelledError:
        error = "INTERRUPTED_OUTCOME_UNKNOWN"
        raise
    except (ProviderFailure, EvaluationError, AppError) as exc:
        error = getattr(exc, "code", str(exc))
        if isinstance(exc, TextFailure):
            raw = exc.raw
    except Exception:
        error = "UNEXPECTED_DISPATCH_ERROR"
    finally:
        if not task.done():
            task.cancel()
        with suppress(asyncio.CancelledError, Exception):
            await task
        # Preserve even invalid/refused outputs before any analyst correction.
        if error:
            prediction = None
        metadata = redact_value(metadata, secret(config))
        async with db.transaction() as conn:
            await reconcile(conn, entry, None if error == "COST_EXCEEDS_RESERVATION" else cost)
            outcome = {"status": "ERROR" if error else "SUCCESS", "prediction": prediction, "error_code": error,
                       "attempts": 1, "cost_idr": cost if error != "COST_EXCEEDS_RESERVATION" else None,
                       "input_tokens": reply.result.usage.get("input_tokens") if reply and reply.result.usage else None,
                       "output_tokens": reply.result.usage.get("output_tokens") if reply and reply.result.usage else None,
                       "elapsed_seconds": time.monotonic()-start, "evaluation_id": evaluation_id,
                       "raw_response_reference": f"application-db:provider_attempts/{attempt_id}",
                       "raw_response_redacted": raw, "metadata": metadata}
            await conn.execute("UPDATE provider_attempts SET status=?,error_code=?,metadata_json=?,redacted_response=?,"
                               "usage_json=?,finished_at=? WHERE provider_attempt_id=?",
                               (outcome["status"], error, packed(metadata), raw,
                                packed(reply.result.usage) if reply and reply.result.usage else None, time.time(), attempt_id))
            await conn.execute("UPDATE evaluation_jobs SET status=?,output_json=?,error_code=?,finished_at=? WHERE evaluation_id=?",
                               (outcome["status"], packed(outcome), error, time.time(), evaluation_id))
    return outcome
