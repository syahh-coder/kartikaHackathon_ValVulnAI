import time

import pytest

from app.agent.ledger import budget_used
from app.common import AppError
from app.providers.contracts import ProviderFailure, ProviderProfile, ProviderResult
from app.providers.engine import ProviderSession
from app.storage.db import all_rows, one
from conftest import activate, report_for
from test_workflow import start


def profile(name, tier="PAID", **kwargs):
    return ProviderProfile(provider_id=name, model_id="simulated-model", access_tier=tier,
                           enabled=True, tools_verified=True, schema_verified=True, tier_verified=True,
                           max_cost_idr=100, price_snapshot="simulation-only", **kwargs)


def result_for(p, call_id, **kwargs):
    base = dict(call_id=call_id, provider_id=p.provider_id, requested_model_id=p.model_id,
                resolved_model_id=p.model_id, inference_provider="fixed", text="SIMULATED",
                usage={"input_tokens": 10, "output_tokens": 5}, cost_status="KNOWN", actual_cost_idr=10)
    return ProviderResult(**(base | kwargs))


class ScriptedTransport:
    def __init__(self, responses):
        self.responses, self.calls = list(responses), []
    async def dispatch(self, p, call_id, prompt):
        self.calls.append(p.provider_id)
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return result_for(p, call_id, **(response or {}))


@pytest.fixture
async def provider_env(env):
    app, p, a, _, admin = env
    await activate(admin, p)
    _, rid, rev = await report_for(a, p)
    run_id = (await start(a, rid, rev)).json()["run_id"]
    assert await app.state.workflow.lease_next() == run_id
    return app.state.db, run_id


@pytest.mark.parametrize("error", ["TEMPORARY_429", "SERVER_ERROR", "TRANSPORT_TIMEOUT"])
async def test_temporary_fallback_recorded_cost_unknown(provider_env, error):
    db, run_id = provider_env
    transport = ScriptedTransport([ProviderFailure(error), None])
    session = ProviderSession(db, run_id, profile("primary"), [profile("free", "FREE_TIER")], transport, 50_000)
    result = await session.call("synthetic", 10)
    assert result.provider_id=="free" and transport.calls==["primary", "free"]
    async with db.connect() as conn:
        events = await all_rows(conn, "SELECT * FROM provider_attempts ORDER BY created_at")
        assert len(events)==2 and events[0]["status"]=="FAILED" and events[1]["fallback_reason"]==error
        assert events[0]["call_id"]==events[1]["call_id"]
        assert await budget_used(conn)==110  # unknown primary reserves 100; simulated second costs 10
        assert (await one(conn, "SELECT inference_provider FROM runs WHERE run_id=?", (run_id,)))[0]=="free"


async def test_quota_only_verified_operator_free_tier(provider_env):
    db, run_id = provider_env
    unverified = profile("unverified", "FREE_TIER").model_copy(update={"tier_verified": False})
    transport = ScriptedTransport([ProviderFailure("QUOTA_EXHAUSTED", cost_idr=0), None])
    session = ProviderSession(db, run_id, profile("primary"), [profile("paid"), unverified, profile("free", "FREE_TIER")], transport, 50_000)
    assert (await session.call("synthetic", 10)).provider_id=="free"
    assert transport.calls==["primary", "free"]


async def test_quota_never_escalates_to_paid(provider_env):
    db, run_id = provider_env
    transport = ScriptedTransport([ProviderFailure("QUOTA_EXHAUSTED", cost_idr=0)])
    session = ProviderSession(db, run_id, profile("primary"), [profile("paid")], transport, 50_000)
    with pytest.raises(ProviderFailure, match="QUOTA_EXHAUSTED"):
        await session.call("synthetic", 10)
    assert transport.calls==["primary"]


@pytest.mark.parametrize("code", ["PROVIDER_REFUSED", "AUTH_ERROR", "CONFIGURATION_REQUIRED", "SCHEMA_ERROR", "CONTEXT_LIMIT", "POLICY_BLOCKED", "AMBIGUOUS_429"])
async def test_no_fallback_for_non_transient(provider_env, code):
    db, run_id = provider_env
    transport = ScriptedTransport([ProviderFailure(code, cost_idr=0)])
    session = ProviderSession(db, run_id, profile("primary"), [profile("free", "FREE_TIER")], transport, 50_000)
    with pytest.raises(ProviderFailure):
        await session.call("synthetic", 10)
    assert transport.calls==["primary"]


async def test_refusal_result_and_provider_lock(provider_env):
    db, run_id = provider_env
    transport = ScriptedTransport([None, ProviderFailure("SERVER_ERROR", cost_idr=0)])
    session = ProviderSession(db, run_id, profile("primary"), [profile("free", "FREE_TIER")], transport, 50_000)
    await session.call("first", 10)
    with pytest.raises(ProviderFailure):
        await session.call("second", 10)
    assert transport.calls==["primary", "primary"]
    refusal = ScriptedTransport([{"refusal": True}])
    other = ProviderSession(db, run_id, profile("primary"), [profile("free", "FREE_TIER")], refusal, 50_000)
    with pytest.raises(ProviderFailure, match="PROVIDER_REFUSED"):
        await other.call("refused", 10)
    assert refusal.calls==["primary"]


async def test_benchmark_and_target_action_disable_fallback(provider_env):
    db, run_id = provider_env
    for benchmark in (True, False):
        transport = ScriptedTransport([ProviderFailure("SERVER_ERROR", cost_idr=0)])
        session = ProviderSession(db, run_id, profile("primary"), [profile("free", "FREE_TIER")], transport, 50_000, benchmark=benchmark)
        session.target_action_started = not benchmark
        with pytest.raises(ProviderFailure):
            await session.call("synthetic", 10)
        assert transport.calls==["primary"]
    drift = ScriptedTransport([{"resolved_model_id": "different-model"}])
    session = ProviderSession(db, run_id, profile("primary"), [], drift, 50_000, benchmark=True)
    with pytest.raises(ProviderFailure, match="PROVIDER_DRIFT"):
        await session.call("synthetic", 10)


async def test_two_dispatch_limit_and_global_call_cap(provider_env):
    db, run_id = provider_env
    transport = ScriptedTransport([ProviderFailure("SERVER_ERROR", cost_idr=0), ProviderFailure("SERVER_ERROR", cost_idr=0)])
    session = ProviderSession(db, run_id, profile("primary"), [], transport, 50_000)
    with pytest.raises(ProviderFailure):
        await session.call("synthetic", 10)
    assert transport.calls==["primary", "primary"]
    transport = ScriptedTransport([None]*11)
    session = ProviderSession(db, run_id, profile("primary"), [], transport, 50_000)
    for _ in range(10):
        await session.call("synthetic", 10)
    with pytest.raises(ProviderFailure, match="MODEL_CALL_LIMIT"):
        await session.call("synthetic", 10)
    assert len(transport.calls)==10


async def test_shared_budget_after_fallback(provider_env):
    db, run_id = provider_env
    transport = ScriptedTransport([ProviderFailure("TRANSPORT_TIMEOUT"), None])
    session = ProviderSession(db, run_id, profile("primary"), [profile("free", "FREE_TIER")], transport, 150)
    with pytest.raises(AppError) as exc:
        await session.call("synthetic", 10)
    assert exc.value.code=="BUDGET_LIMIT"
    assert transport.calls==["primary"]
    async with db.connect() as conn:
        assert await budget_used(conn)==100


@pytest.mark.parametrize("tokens", [None, 8193, -1])
async def test_unknown_or_excess_context_never_dispatches(provider_env, tokens):
    db, run_id = provider_env
    transport = ScriptedTransport([])
    session = ProviderSession(db, run_id, profile("primary"), [], transport, 50_000)
    with pytest.raises(ProviderFailure, match="CONTEXT_LIMIT"):
        await session.call("synthetic", tokens)
    assert transport.calls==[]


async def test_deadline_retry_after_and_missing_config(provider_env):
    db, run_id = provider_env
    transport = ScriptedTransport([ProviderFailure("TEMPORARY_429", retry_after=300, cost_idr=0)])
    session = ProviderSession(db, run_id, profile("primary"), [], transport, 50_000, deadline=time.time()+5)
    with pytest.raises(ProviderFailure, match="RUN_TIMEOUT"):
        await session.call("synthetic", 10)
    assert transport.calls==["primary"]
    transport = ScriptedTransport([])
    p = profile("primary").model_copy(update={"enabled": False})
    with pytest.raises(ProviderFailure, match="CONFIGURATION_REQUIRED"):
        await ProviderSession(db, run_id, p, [], transport, 50_000).call("synthetic", 10)
    assert transport.calls==[]
