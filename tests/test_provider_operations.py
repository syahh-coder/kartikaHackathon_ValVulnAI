"""Configuration/smoke tools cannot silently generate or switch providers."""
import json
import pytest

from app.agent.text_triage import TextTriage
from app.providers import azure, openrouter
from app.providers.triage_contracts import MAX_OUTPUT_TOKENS, TriageSuggestion
from evaluator.text_dispatch import configuration
from scripts.check_text_provider_config import check
from scripts.smoke_text_provider import main
from test_azure_text import azure_config
from test_text_triage import live_config


def env_file(tmp_path, config):
    values = config.model_dump(exclude={"openrouter_api_key", "azure_api_key", "agentrouter_api_key", "groq_api_key"})
    for key in ("openrouter_api_key", "azure_api_key", "groq_api_key"):
        secret = getattr(config, key)
        if secret:
            values[key] = secret.get_secret_value()
    path = tmp_path / "config.env"
    path.write_text("\n".join("VALVULN_" + k.upper() + "=" +
                              (str(v).lower() if isinstance(v, bool) else str(v))
                              for k, v in values.items() if v is not None), encoding="utf-8")
    return path


@pytest.mark.parametrize("provider", ["openrouter", "azure"])
def test_reservation_schema_and_snapshots_match_wire_contract(tmp_path, provider):
    config = (live_config if provider == "openrouter" else azure_config)()
    module = openrouter if provider == "openrouter" else azure
    request = module.request_body(config, "Synthetic text")
    cap_key = "max_tokens" if provider == "openrouter" else "max_completion_tokens"
    assert request[cap_key] == MAX_OUTPUT_TOKENS == 4096
    assert configuration(config)["output_limit"] == TextTriage(None, config).configuration()["output_tokens"] == 4096
    result = check(env_file(tmp_path, config), provider)
    assert result["status"] == "CONFIGURED_NOT_VERIFIED", result
    assert result["minimum_reservation_idr"] == 279
    assert not result["live_verified"] and result["provider_requests"] == 0
    assert result["priority"] == ["groq", "openrouter", "azure"] and not result["automatic_fallback"]
    schema = request["response_format"]["json_schema"]["schema"]
    assert "validation_fields" in schema["required"]
    assert "validation_fields" in TriageSuggestion.model_json_schema()["properties"]
    if provider == "openrouter":
        assert request["provider"]["require_parameters"] and not request["provider"]["allow_fallbacks"]
    else:
        assert not any(k in request for k in ("provider", "tools", "functions"))


@pytest.mark.parametrize("provider", ["openrouter", "azure"])
def test_missing_key_or_small_reservation_fails_closed(tmp_path, provider):
    config = (live_config if provider == "openrouter" else azure_config)()
    missing = config.model_copy(update={"openrouter_api_key": None, "azure_api_key": None})
    result = check(env_file(tmp_path, missing), provider)
    assert result["status"] == "CONFIGURATION_REQUIRED" and "api_key" in result["missing"]
    result = check(env_file(tmp_path, config.model_copy(update={"triage_reservation_idr": 200})), provider)
    assert result["status"] == "CONFIGURATION_REQUIRED" and result["minimum_reservation_idr"] == 279


def test_mismatched_provider_never_falls_back(tmp_path):
    result = check(env_file(tmp_path, azure_config()), "openrouter")
    assert result["status"] == "CONFIGURATION_REQUIRED" and "triage_provider=openrouter" in result["missing"]
    assert not result["automatic_fallback"] and result["provider_requests"] == 0


def test_smoke_requires_explicit_execution(capsys):
    assert main([]) == 2
    result = json.loads(capsys.readouterr().out)
    assert result == {"status": "LIVE_TEST_DEFERRED", "provider_requests": 0, "live_verified": False}
