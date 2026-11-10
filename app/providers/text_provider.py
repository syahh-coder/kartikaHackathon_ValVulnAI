"""Explicit provider selection for text paths. Never falls back or dispatches a worker."""
import json

from app.providers import azure, openrouter


def secret(config) -> str:
    key = config.azure_api_key if config.triage_provider == "azure" else config.openrouter_api_key
    return key.get_secret_value() if key else ""


def require_configuration(config):
    return (azure if config.triage_provider == "azure" else openrouter).require_configuration(config)


def input_token_bound(config, prompt, **contract):
    body = (azure if config.triage_provider == "azure" else openrouter).request_body(config, prompt, **contract)
    return len(json.dumps(body, ensure_ascii=False).encode("utf-8")) + 1024


def transport(config, **contract):
    return (azure.AzureTransport if config.triage_provider == "azure" else openrouter.OpenRouterTransport)(config, **contract)


def profile(config) -> dict:
    # Persist resource/model identity so freeze detects endpoint or deployment changes.
    return ({"azure_endpoint": azure.endpoint(config), "resolved_model_expected": config.azure_expected_model,
             "cost_accounting": "FULL_RESERVATION_COST_UNKNOWN"}
            if config.triage_provider == "azure" and config.triage_mode == "live" else {})


def expected_model(config):
    return config.azure_expected_model if config.triage_provider == "azure" else config.triage_model
