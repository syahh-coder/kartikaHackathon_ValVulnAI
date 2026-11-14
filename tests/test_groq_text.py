"""Groq HTTP is intercepted; never uses real keys, cloud or external targets."""
import json
from decimal import Decimal

import httpx
import pytest
from pydantic import SecretStr

from app.providers.groq import ENDPOINT, GroqTransport, request_body, require_configuration
from app.providers.contracts import ProviderFailure
from app.providers.text_provider import profile, secret, transport
from app.storage.db import one
from evaluator.text_benchmark import config_readiness
from evaluator.text_context import CONTRACT
from evaluator.text_dispatch import configuration, dispatch
from scripts.check_text_provider_config import check
from test_provider_operations import env_file
from test_text_triage import SUGGESTION, HttpScript, finished, live_config, submit, triage_env

KEY = "synthetic-groq-private-value-never-real"
MODEL = "openai/gpt-oss-120b"


def groq_config(**updates):
    return live_config(triage_provider="groq", groq_api_key=SecretStr(KEY), openrouter_api_key=None,
        triage_model=MODEL, triage_provider_slug="groq", triage_provider_name="Groq", triage_access_tier="FREE_TIER",
        triage_prompt_usd_per_million=Decimal("0"), triage_completion_usd_per_million=Decimal("0")).model_copy(update=updates)


def completion(**updates):
    return {"id": "synthetic-groq-request", "model": MODEL,
        "choices": [{"finish_reason": "stop", "message": {"role": "assistant", "content": json.dumps(SUGGESTION)}}],
        "usage": {"prompt_tokens": 50, "completion_tokens": 80}, **updates}


def test_contract_factory_snapshot_and_checker(tmp_path):
    config = groq_config()
    require_configuration(config)
    body = request_body(config, "Synthetic JSON report")
    assert body["model"] == MODEL and body["max_completion_tokens"] == 4096
    assert body["reasoning_effort"] == "low" and body["include_reasoning"] is False
    assert body["response_format"]["json_schema"]["strict"]
    assert "validation_fields" in body["response_format"]["json_schema"]["schema"]["required"]
    assert not any(k in body for k in ("provider", "tools", "functions", "max_tokens"))
    assert isinstance(transport(config), GroqTransport) and secret(config) == KEY
    assert profile(config)["groq_endpoint"] == ENDPOINT
    assert configuration(config)["include_reasoning"] is False
    assert config_readiness(config)["status"] == "CONFIGURED_NOT_VERIFIED"
    assert check(env_file(tmp_path, config), "groq")["status"] == "CONFIGURED_NOT_VERIFIED"


@pytest.mark.parametrize("updates", [{"groq_api_key": None}, {"triage_model": "openrouter/auto"},
    {"triage_model": "unverified/model"}, {"triage_provider_name": "Other"}, {"triage_provider_slug": "other"},
    {"triage_access_verified": False}, {"triage_token_bound_verified": False}, {"triage_access_tier": "PAID"},
    {"triage_price_snapshot": ""}, {"triage_prompt_usd_per_million": 1}, {"triage_completion_usd_per_million": 1},
    {"triage_reservation_idr": 0}, {"triage_reservation_idr": 101, "budget_idr": 100}])
def test_missing_unverified_or_paid_configuration_fails_closed(updates):
    with pytest.raises(ProviderFailure, match="CONFIGURATION_REQUIRED"):
        require_configuration(groq_config(**updates))


async def test_fixed_origin_auth_and_no_invented_zero_bill():
    script = HttpScript([completion(usage={"prompt_tokens": 50, "completion_tokens": 80, "cost": 0})])
    reply = await GroqTransport(groq_config(), http_transport=httpx.MockTransport(script)).dispatch("call", "JSON")
    request = script.requests[0]
    assert str(request.url) == ENDPOINT and request.headers["Authorization"] == "Bearer " + KEY
    assert reply.result.provider_id == "groq" and reply.result.inference_provider == "Groq"
    assert reply.result.actual_cost_idr is None and reply.result.cost_status == "COST_UNKNOWN" and reply.cost_usd is None


@pytest.mark.parametrize("change,code", [
    ({"model": "different"}, "PROVIDER_DRIFT"),
    ({"choices": [{"finish_reason": "length", "message": {"content": "{}"}}]}, "INCOMPLETE_RESPONSE"),
    ({"choices": [{"finish_reason": "stop", "message": {"refusal": "Not allowed", "content": ""}}]}, "PROVIDER_REFUSED"),
    ({"choices": [{"finish_reason": "stop", "message": {"tool_calls": [{"id": "no"}], "content": "{}"}}]}, "TOOLS_FORBIDDEN"),
    ({"choices": [{"finish_reason": "stop", "message": {"content": "{}"}}]}, "SCHEMA_ERROR"),
])
async def test_invalid_refusal_and_drift_do_not_dispatch_target(triage_env, change, code):
    app, _, hunter, _, _, cid, _ = triage_env
    config = groq_config(data_dir=app.state.config.data_dir, min_free_bytes=0)
    script = HttpScript([completion(**change)])
    app.state.text_triage.config = config
    app.state.text_triage.transport = GroqTransport(config, http_transport=httpx.MockTransport(script))
    result = await finished(app, hunter, (await submit(hunter, cid)).json()["triage_id"])
    assert result["status"] == "FAILED" and result["error_code"] == code
    assert len(script.requests) == 1 and result["attempts"][0]["cost_status"] == "COST_UNKNOWN"


async def test_429_is_bounded_without_fallback(triage_env):
    app, _, hunter, _, _, cid, _ = triage_env
    config = groq_config(data_dir=app.state.config.data_dir, min_free_bytes=0)
    script = HttpScript([httpx.Response(429, json={"error": {"message": "Rate limit"}}, headers={"retry-after": "60"})])
    app.state.text_triage.config = config
    app.state.text_triage.transport = GroqTransport(config, http_transport=httpx.MockTransport(script))
    result = await finished(app, hunter, (await submit(hunter, cid)).json()["triage_id"])
    assert result["error_code"] == "TEMPORARY_429" and len(script.requests) == 1


async def test_evaluator_uses_same_ledger_and_retains_unknown(env):
    app, _, _, _, _ = env
    from test_text_benchmark import admin_user
    user = await admin_user(app)
    async def guard(conn): pass
    prediction = {"prediction": "ABSTAIN", "reason": "Insufficient observations", "references": ["REPORT"]}
    script = HttpScript([completion(choices=[{"finish_reason": "stop", "message": {"content": json.dumps(prediction)}}])])
    config = groq_config(data_dir=app.state.config.data_dir, min_free_bytes=0)
    result = await dispatch(app.state.db, config, user, freeze_hash="SIMULATED-GROQ", report_key="case", arm="A",
        text="Synthetic report", references={"REPORT"}, guard=guard,
        transport=GroqTransport(config, http_transport=httpx.MockTransport(script), **CONTRACT))
    assert result["status"] == "SUCCESS", result
    async with app.state.db.connect() as conn:
        row = await one(conn, "SELECT status,actual_idr FROM ledger WHERE evaluation_id IS NOT NULL")
        assert row["status"] == "COST_UNKNOWN" and row["actual_idr"] is None
