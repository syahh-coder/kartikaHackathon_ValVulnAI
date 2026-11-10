import pytest
from decimal import Decimal
from pydantic import SecretStr

from app.config import Settings
from app.providers.agentrouter import endpoint, require_configuration, request_body, AgentRouterTransport
from app.providers.contracts import ProviderFailure

SYNTHETIC_KEY = SecretStr("sk-ar-test-agentrouter-key-12345678")


def base_settings(**kwargs):
    values = {
        "triage_mode": "live",
        "triage_provider": "agentrouter",
        "agentrouter_api_key": SYNTHETIC_KEY,
        "agentrouter_endpoint": "https://agentrouter.org/v1/chat/completions",
        "triage_model": "openai/gpt-4o-mini",
        "triage_provider_slug": "agentrouter",
        "triage_provider_name": "AgentRouter",
        "triage_access_verified": True,
        "triage_token_bound_verified": True,
        "triage_price_snapshot": "test",
        "triage_prompt_usd_per_million": Decimal("0.15"),
        "triage_completion_usd_per_million": Decimal("0.60"),
        "triage_usd_to_idr": Decimal("16000"),
        "triage_reservation_idr": 100,
        "budget_idr": 50000,
    }
    values.update(kwargs)
    return Settings(_env_file=None, **values)


def test_agentrouter_endpoint_resolution():
    cfg = base_settings(agentrouter_endpoint="https://agentrouter.org/v1")
    assert endpoint(cfg) == "https://agentrouter.org/v1/chat/completions"

    cfg2 = base_settings(agentrouter_endpoint="https://agentrouter.org")
    assert endpoint(cfg2) == "https://agentrouter.org/v1/chat/completions"

    cfg3 = base_settings(agentrouter_endpoint="https://co.agentrouter.org/v1/chat/completions")
    assert endpoint(cfg3) == "https://co.agentrouter.org/v1/chat/completions"


def test_agentrouter_require_configuration_success():
    cfg = base_settings()
    require_configuration(cfg)


def test_agentrouter_missing_key_fails():
    cfg = base_settings(agentrouter_api_key=None)
    with pytest.raises(ProviderFailure) as exc:
        require_configuration(cfg)
    assert exc.value.code == "CONFIGURATION_REQUIRED"


def test_agentrouter_request_body_formatting():
    cfg = base_settings()
    body = request_body(cfg, "Laporan pengujian")
    assert body["model"] == "openai/gpt-4o-mini"
    assert "provider" not in body
    assert body["messages"][-1]["content"] == "Laporan pengujian"


def test_agentrouter_transport_prepare():
    cfg = base_settings()
    transport = AgentRouterTransport(cfg)
    url, headers, body, secret = transport.prepare("Halo AI")
    assert url == "https://agentrouter.org/v1/chat/completions"
    assert headers["Authorization"] == "Bearer sk-ar-test-agentrouter-key-12345678"
    assert secret == "sk-ar-test-agentrouter-key-12345678"
    assert transport.response_provider(body, "") == "AgentRouter"
