"""Explicit provider selection for text paths. Never falls back or dispatches a worker."""
import json

from app.providers import agentrouter, azure, groq, openrouter

PROVIDER_PRIORITY = ["groq", "openrouter", "azure"]


def _module(config):
    if config.triage_provider == "groq":
        return groq
    if config.triage_provider == "agentrouter":
        return agentrouter
    return azure if config.triage_provider == "azure" else openrouter


def secret(config) -> str:
    if config.triage_provider == "groq":
        key = config.groq_api_key
    elif config.triage_provider == "agentrouter":
        key = config.agentrouter_api_key
    elif config.triage_provider == "azure":
        key = config.azure_api_key
    else:
        key = config.openrouter_api_key
    return key.get_secret_value() if key else ""


def require_configuration(config):
    return _module(config).require_configuration(config)


def input_token_bound(config, prompt, **contract):
    body = _module(config).request_body(config, prompt, **contract)
    return len(json.dumps(body, ensure_ascii=False).encode("utf-8")) + 1024


def transport(config, **contract):
    if config.triage_provider == "groq":
        return groq.GroqTransport(config, **contract)
    if config.triage_provider == "agentrouter":
        return agentrouter.AgentRouterTransport(config, **contract)
    if config.triage_provider == "azure":
        return azure.AzureTransport(config, **contract)
    return openrouter.OpenRouterTransport(config, **contract)


def profile(config) -> dict:
    # Persist resource/model identity so freeze detects endpoint or deployment changes.
    if config.triage_mode == "live":
        if config.triage_provider == "groq":
            return {"groq_endpoint": groq.ENDPOINT, "reasoning_effort": "low", "include_reasoning": False,
                    "cost_accounting": "FULL_RESERVATION_COST_UNKNOWN", "schema_mode": "STRICT_SUBSET_LOCAL_FULL_VALIDATION"}
        if config.triage_provider == "azure":
            return {"azure_endpoint": azure.endpoint(config), "resolved_model_expected": config.azure_expected_model,
                    "cost_accounting": "FULL_RESERVATION_COST_UNKNOWN"}
        if config.triage_provider == "agentrouter":
            return {"agentrouter_endpoint": agentrouter.endpoint(config),
                    "cost_accounting": "FULL_RESERVATION_COST_UNKNOWN"}
    return {}


def expected_model(config):
    return config.azure_expected_model if config.triage_provider == "azure" else config.triage_model
