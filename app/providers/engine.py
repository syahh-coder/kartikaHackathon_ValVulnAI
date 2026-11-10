"""Legacy planner provider contract; text triage has an independent lifecycle."""
import asyncio
import time

from app.agent.ledger import reconcile, reserve
from app.common import AppError, packed, uid
from app.providers.contracts import ProviderFailure, ProviderProfile, ProviderResult, Transport
from app.storage.db import Database, one


class ProviderSession:
    def __init__(self, db: Database, run_id: str, primary: ProviderProfile, fallbacks: list[ProviderProfile],
                 transport: Transport, budget_idr: int, *, benchmark: bool = False, deadline: float | None = None):
        self.db, self.run_id, self.primary, self.fallbacks = db, run_id, primary, fallbacks
        self.transport, self.budget_idr, self.benchmark = transport, budget_idr, benchmark
        self.deadline = deadline if deadline is not None else time.time()+180
        self.locked: ProviderProfile | None = None
        self.target_action_started = False

    @staticmethod
    def eligible(profile: ProviderProfile) -> bool:
        return profile.enabled and profile.tools_verified and profile.schema_verified and profile.tier_verified

    async def call(self, prompt: str, input_tokens: int | None) -> ProviderResult:
        # The run's first successful provider is authoritative even if the caller
        # reconstructs a session object within the same run.
        async with self.db.connect() as conn:
            run = await one(conn, "SELECT model_id,inference_provider FROM runs WHERE run_id=?", (self.run_id,))
        if run and run["inference_provider"]:
            candidates = [p for p in [self.primary, *self.fallbacks] if
                          p.provider_id==run["inference_provider"] and p.model_id==run["model_id"]]
            if not candidates:
                raise ProviderFailure("PROVIDER_LOCKED", cost_idr=0)
            self.locked = candidates[0]
        profile = self.locked or self.primary
        if not self.eligible(profile):
            raise ProviderFailure("CONFIGURATION_REQUIRED", cost_idr=0)
        # Caller must use a compatible tokenizer; unknown counts never dispatch.
        if input_tokens is None or input_tokens<0 or input_tokens>profile.max_input_tokens:
            raise ProviderFailure("CONTEXT_LIMIT", cost_idr=0)
        call_id, reason = uid(), None
        for attempt in range(2):
            if input_tokens > profile.max_input_tokens:
                raise ProviderFailure("CONTEXT_LIMIT", cost_idr=0)
            if time.time() >= self.deadline:
                raise ProviderFailure("RUN_TIMEOUT", cost_idr=0)
            attempt_id = uid()
            async with self.db.transaction() as conn:
                run = await one(conn, "SELECT * FROM runs WHERE run_id=?", (self.run_id,))
                if not run or run["queue_status"] != "LEASED":
                    raise ProviderFailure("RUN_STOPPED", cost_idr=0)
                current = await one(conn, "SELECT count(*) FROM provider_attempts WHERE run_id=?", (self.run_id,))
                if current[0] >= 12:
                    raise ProviderFailure("MODEL_CALL_LIMIT", cost_idr=0)
                ledger_id = await reserve(conn, self.run_id, profile.max_cost_idr, self.budget_idr, attempt_id)
                await conn.execute("INSERT INTO provider_attempts(provider_attempt_id,call_id,run_id,provider_id,model_id,"
                                   "status,error_code,fallback_reason,usage_json,created_at) "
                                   "VALUES (?,?,?,?,?,'DISPATCHED',NULL,?,NULL,?)",
                                   (attempt_id, call_id, self.run_id, profile.provider_id, profile.model_id, reason, time.time()))
            result = None
            try:
                async with asyncio.timeout(max(0.001, self.deadline-time.time())):
                    result = await self.transport.dispatch(profile, call_id, prompt)
                if not isinstance(result, ProviderResult):
                    raise ProviderFailure("SCHEMA_ERROR")
                if (result.call_id != call_id or result.provider_id != profile.provider_id or
                        result.requested_model_id != profile.model_id or result.resolved_model_id != profile.model_id or
                        result.inference_provider != profile.inference_provider_policy):
                    raise ProviderFailure("PROVIDER_DRIFT", cost_idr=result.actual_cost_idr)
                async with self.db.connect() as conn:
                    still_active = await one(conn, "SELECT queue_status FROM runs WHERE run_id=?", (self.run_id,))
                if still_active[0] != "LEASED":
                    raise ProviderFailure("RUN_STOPPED", cost_idr=result.actual_cost_idr)
                if result.refusal:
                    raise ProviderFailure("PROVIDER_REFUSED", cost_idr=result.actual_cost_idr)
            except asyncio.CancelledError:
                await self._finish(attempt_id, ledger_id, "RUN_STOPPED", None, None)
                raise
            except (ProviderFailure, TimeoutError) as exc:
                failure = exc if isinstance(exc, ProviderFailure) else ProviderFailure("TRANSPORT_TIMEOUT")
                await self._finish(attempt_id, ledger_id, failure.code, failure.cost_idr, result)
                if (attempt or self.locked or self.target_action_started or self.benchmark or
                        failure.code not in {"TEMPORARY_429", "SERVER_ERROR", "TRANSPORT_TIMEOUT", "QUOTA_EXHAUSTED"}):
                    raise failure
                candidates = [p for p in self.fallbacks if self.eligible(p) and p.provider_id != profile.provider_id]
                if failure.code == "QUOTA_EXHAUSTED":
                    candidates = [p for p in candidates if p.access_tier == "FREE_TIER"]
                if candidates:
                    profile, reason = candidates[0], failure.code
                elif failure.code != "QUOTA_EXHAUSTED":
                    reason = "RETRY:"+failure.code
                else:
                    raise failure
                if failure.retry_after < 0 or time.time()+failure.retry_after >= self.deadline:
                    raise ProviderFailure("RUN_TIMEOUT")
                if failure.retry_after:
                    await asyncio.sleep(failure.retry_after)
                continue
            except Exception:
                await self._finish(attempt_id, ledger_id, "ADAPTER_ERROR", None, None)
                raise ProviderFailure("ADAPTER_ERROR") from None
            await self._finish(attempt_id, ledger_id, None, result.actual_cost_idr if result.cost_status=="KNOWN" else None, result)
            self.locked = profile
            async with self.db.transaction() as conn:
                await conn.execute("UPDATE runs SET model_id=?,inference_provider=? WHERE run_id=?",
                                   (result.resolved_model_id, result.provider_id, self.run_id))
            return result
        raise AssertionError("bounded provider loop exhausted")

    async def _finish(self, attempt_id: str, entry_id: str, code: str | None, cost: int | None, result: ProviderResult | None):
        async with self.db.transaction() as conn:
            await reconcile(conn, entry_id, cost)
            await conn.execute("UPDATE provider_attempts SET status=?,error_code=?,usage_json=? WHERE provider_attempt_id=?",
                               ("FAILED" if code else "SUCCEEDED", code, packed(result.usage) if result else None, attempt_id))
