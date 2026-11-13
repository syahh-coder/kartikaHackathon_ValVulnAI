"""Azure integration with synthetic credentials and intercepted HTTP only."""
import json
from decimal import Decimal
from pathlib import Path

import httpx
import pytest
from pydantic import SecretStr

from app.agent.ledger import budget_used
from app.common import packed, uid
from app.config import Settings
from app.main import create_app
from app.providers.azure import AzureTransport, endpoint, request_body, structured_schema
from app.providers.contracts import ProviderFailure
from app.providers.text_provider import expected_model, profile, require_configuration, secret, transport
from app.providers.triage_contracts import TriageSuggestion
from app.storage.db import all_rows, one
from conftest import activate, report_for
from evaluator.text_benchmark import config_readiness
from evaluator.text_context import CONTRACT
from evaluator.text_dispatch import configuration, dispatch
from scripts.check_azure_config import check
from test_text_triage import SUGGESTION, HttpScript, finished, live_config, submit

KEY = "synthetic-azure-private-value-never-real"
MODEL = "synthetic-model-2026-01-01"


def azure_config(**updates):
    return live_config(triage_provider="azure", azure_api_key=SecretStr(KEY),
                       azure_endpoint="https://synthetic-valvuln.openai.azure.com/",
                       azure_expected_model=MODEL, azure_api_capabilities_verified=True,
                       triage_model="synthetic-deployment", triage_provider_slug="azure",
                       triage_provider_name="Azure").model_copy(update=updates)


def completion(**updates):
    return {"id": "synthetic-azure-completion", "model": MODEL,
            "choices": [{"finish_reason": "stop", "message": {"role": "assistant", "content": packed(SUGGESTION)}}],
            "usage": {"prompt_tokens": 50, "completion_tokens": 80, "total_tokens": 130}, **updates}


@pytest.mark.parametrize("url", ["http://synthetic.openai.azure.com", "https://localhost", "https://127.0.0.1",
    "https://synthetic.openai.azure.com.evil.test", "https://user@synthetic.openai.azure.com",
    "https://synthetic.openai.azure.com:443", "https://synthetic.services.ai.azure.com/api/projects/p",
    "https://synthetic.openai.azure.com?key=private", "https://synthetic.openai.azure.com/#x",
    "https://synthetic.openai.azure.com/openai/v1/chat/completions"])
def test_rejects_unsafe_or_wrong_endpoint(url):
    with pytest.raises(ProviderFailure):
        require_configuration(azure_config(azure_endpoint=url))


@pytest.mark.parametrize("url", ["https://synthetic.openai.azure.com", "https://synthetic.openai.azure.com/openai/v1/",
                               "https://synthetic.services.ai.azure.com/openai/v1"])
def test_resource_v1_endpoint(url):
    config = azure_config(azure_endpoint=url)
    require_configuration(config)
    assert endpoint(config).endswith("/openai/v1/chat/completions")


@pytest.mark.parametrize("changes", [{"azure_api_key": None}, {"azure_api_capabilities_verified": False},
    {"azure_expected_model": ""}, {"triage_access_verified": False}, {"triage_token_bound_verified": False},
    {"triage_reservation_idr": 1}, {"triage_model": "openrouter/auto"}, {"triage_provider_name": "Other"}])
def test_configuration_fails_before_dispatch(changes):
    with pytest.raises(ProviderFailure):
        require_configuration(azure_config(**changes))


def test_schema_factory_and_identity_pin():
    config = azure_config()
    assert isinstance(transport(config), AzureTransport)
    assert secret(config) == KEY and expected_model(config) == MODEL
    body = request_body(config, "Synthetic JSON report")
    assert body["model"] == config.triage_model and body["max_completion_tokens"] == 4096
    assert not any(k in body for k in ("provider", "tools", "functions", "max_tokens"))
    schema = body["response_format"]["json_schema"]["schema"]
    assert schema["additionalProperties"] is False
    assert "maxLength" not in schema["properties"]["primary_claim"]
    assert "maxLength" in TriageSuggestion.model_json_schema()["properties"]["primary_claim"]
    assert structured_schema({"properties": {"title": {"type": "string", "maxLength": 1}}}) == {"properties": {"title": {"type": "string"}}}
    assert profile(config)["resolved_model_expected"] == MODEL
    assert configuration(config) != configuration(azure_config(azure_endpoint="https://different.openai.azure.com"))
    assert config_readiness(config)["status"] == "CONFIGURED_NOT_VERIFIED"


async def test_http_auth_bounded_contract_and_unknown_cost():
    config = azure_config()
    # Even an invented monetary field must not be treated as an Azure invoice.
    script = HttpScript([completion(usage={"prompt_tokens": 50, "completion_tokens": 80, "cost": 0})])
    reply = await AzureTransport(config, http_transport=httpx.MockTransport(script)).dispatch("call", "JSON report")
    request = script.requests[0]
    assert request.headers["api-key"] == KEY and "authorization" not in request.headers
    assert str(request.url) == endpoint(config)
    assert reply.result.provider_id == "azure" and reply.result.inference_provider == "Azure"
    assert reply.result.requested_model_id != reply.result.resolved_model_id
    assert reply.result.cost_status == "COST_UNKNOWN" and reply.result.actual_cost_idr is None
    assert reply.cost_usd is None and reply.result.usage["input_tokens"] == 50


@pytest.mark.parametrize("status,code", [(302,"HTTP_ERROR"),(401,"AUTH_ERROR"),(403,"POLICY_BLOCKED"),
    (429,"AMBIGUOUS_429"),(500,"SERVER_ERROR")])
async def test_http_failure_no_redirect_or_retry_and_key_redacted(status, code):
    script = HttpScript([httpx.Response(status, json={"message": KEY}, headers={"Location": "https://evil.test"})])
    with pytest.raises(ProviderFailure) as caught:
        await AzureTransport(azure_config(), http_transport=httpx.MockTransport(script)).dispatch("call", "JSON report")
    assert caught.value.code == code and KEY not in caught.value.raw and len(script.requests) == 1


@pytest.mark.parametrize("body,code", [
    (completion(choices=[{"finish_reason": "tool_calls", "message": {"tool_calls": [{"id": "x"}]}}]), "TOOLS_FORBIDDEN"),
    (completion(usage={"prompt_tokens": 8193, "completion_tokens": 0}), "TOKEN_LIMIT"),
    (completion(usage={"prompt_tokens": True, "completion_tokens": 0}), "SCHEMA_ERROR"),
    (completion(choices=[]), "SCHEMA_ERROR"),
])
async def test_protocol_rejection(body, code):
    with pytest.raises(ProviderFailure) as caught:
        await AzureTransport(azure_config(), http_transport=httpx.MockTransport(HttpScript([body]))).dispatch("call", "JSON report")
    assert caught.value.code == code


@pytest.mark.parametrize("mutation,error", [({}, None), ({"model": "changed-version"}, "PROVIDER_DRIFT"),
    ({"choices": [{"finish_reason": "stop", "message": {"refusal": "cannot help"}}]}, "PROVIDER_REFUSED"),
    ({"choices": [{"finish_reason": "stop", "message": {"content": packed(SUGGESTION | {"reason": "x"*1501})}}]}, "SCHEMA_ERROR")])
async def test_ui_text_flow_preserves_cost_and_separates_worker(env, mutation, error):
    app, program, hunter, _, admin = env
    await activate(admin, program)
    cid, _, _ = await report_for(hunter, program, text="Synthetic report with private value " + KEY)
    config = azure_config(data_dir=app.state.config.data_dir, min_free_bytes=0)
    app.state.text_triage.config = config
    script = HttpScript([completion(**mutation)])
    app.state.text_triage.transport = AzureTransport(config, http_transport=httpx.MockTransport(script))
    response = await submit(hunter, cid)
    assert response.status_code == 202, response.text
    result = await finished(app, hunter, response.json()["triage_id"])
    assert result["provider"] == "azure" and result["error_code"] == error
    assert result["status"] == ("FAILED" if error else "SUCCEEDED")
    assert result["verdict"] is None and result["target_execution_allowed"] is False
    assert KEY not in result.__str__() and KEY not in script.requests[0].content.decode()
    async with app.state.db.connect() as conn:
        ledger = await one(conn, "SELECT * FROM ledger")
        assert ledger["status"] == "COST_UNKNOWN" and ledger["actual_idr"] is None
        assert await budget_used(conn) == config.triage_reservation_idr
        attempt = await one(conn, "SELECT * FROM provider_attempts")
        assert attempt["provider_id"] == "azure"
        for table in ("runs", "actions", "handoff_actions", "evidence", "assessments"):
            assert (await one(conn, f"SELECT count(*) FROM {table}"))[0] == 0


async def test_missing_azure_key_fails_closed_without_ledger(env):
    app, program, hunter, _, _ = env
    cid, _, _ = await report_for(hunter, program)
    app.state.text_triage.config = azure_config(azure_api_key=None)
    response = await submit(hunter, cid)
    assert response.status_code == 503 and response.json()["error_code"] == "CONFIGURATION_REQUIRED"
    async with app.state.db.connect() as conn:
        assert not await all_rows(conn, "SELECT * FROM ledger")
        assert not await all_rows(conn, "SELECT * FROM text_triages")


async def test_readiness_startup_no_network_no_mock_fallback(tmp_path):
    app = create_app(azure_config(data_dir=tmp_path, azure_api_key=None, dispatcher_enabled=False))
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app), base_url="http://127.0.0.1:8000") as client:
            data = (await client.get("/api/readiness")).json()
            assert data["triage_mode"] == "live" and data["triage_provider"] == "azure"
            assert data["text_provider"] == "CONFIGURATION_REQUIRED"
            assert KEY not in packed(data)
        async with app.state.db.connect() as conn:
            assert not await all_rows(conn, "SELECT * FROM provider_attempts")


async def test_evaluator_uses_same_azure_transport_ledger_and_contract(env):
    from app.auth import Principal
    app, _, _, _, _ = env
    async with app.state.db.connect() as conn:
        row = await one(conn, "SELECT user_id FROM users WHERE login_name='admin'")
    user = Principal(row[0], "admin", "local-operator")
    async def guard(conn):
        pass
    # Use schema-native field names from the evaluation contract.
    from evaluator.functional_v2 import ModelPrediction
    prediction = ModelPrediction(prediction="ABSTAIN", reason="Synthetic incomplete evidence", references=["report"]).model_dump()
    script = HttpScript([completion(choices=[{"finish_reason": "stop", "message": {"content": packed(prediction)}}])])
    config = azure_config()
    result = await dispatch(app.state.db, config, user, freeze_hash=uid(), report_key="DEV", arm="SMOKE",
                            text="Synthetic JSON report", references={"report"}, guard=guard,
                            transport=AzureTransport(config, http_transport=httpx.MockTransport(script), **CONTRACT))
    assert result["status"] == "SUCCESS", result
    assert result["cost_idr"] is None
    async with app.state.db.connect() as conn:
        assert (await one(conn, "SELECT status FROM ledger"))[0] == "COST_UNKNOWN"
        assert (await one(conn, "SELECT provider_id FROM provider_attempts"))[0] == "azure"


def test_private_checker_masks_invalid_values_and_template(tmp_path):
    path = tmp_path/"private.env"
    path.write_text("VALVULN_AZURE_API_KEY="+KEY+"\nVALVULN_BUDGET_IDR="+KEY, encoding="utf-8")
    result = check(path)
    assert result["status"] == "CONFIGURATION_INVALID" and KEY not in packed(result)
    path.write_text(Path(".env.azure.example").read_text(encoding="utf-8"), encoding="utf-8")
    result = check(path)
    assert "VALVULN_AZURE_API_KEY" in result["missing"] and result["provider_requests"] == 0
