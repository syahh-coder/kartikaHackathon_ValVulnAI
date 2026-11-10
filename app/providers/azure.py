"""Azure Foundry resource OpenAI v1 chat, TEXT ONLY; no project/agent endpoints."""
import re
from decimal import Decimal, ROUND_CEILING
from urllib.parse import urlsplit

from app.providers.contracts import ProviderFailure
from app.providers.openrouter import OpenRouterTransport, request_body as openrouter_body
from app.providers.triage_contracts import MAX_INPUT_TOKENS, MAX_OUTPUT_TOKENS


def endpoint(config) -> str:
    value = config.azure_endpoint
    # Exact public resource origins only. No user-supplied paths, ports, proxies or redirects.
    if not re.fullmatch(r"https://[a-z0-9][a-z0-9-]*\.(?:openai\.azure\.com|services\.ai\.azure\.com)(?:/openai/v1/?)?/?", value):
        raise ProviderFailure("CONFIGURATION_REQUIRED", cost_idr=0)
    url = urlsplit(value)
    return f"https://{url.hostname}/openai/v1/chat/completions"


def require_configuration(config) -> None:
    if config.triage_mode == "replay":
        raise ProviderFailure("REPLAY_NOT_CONFIGURED", cost_idr=0)
    if config.triage_mode != "live":
        return
    key = config.azure_api_key.get_secret_value() if config.azure_api_key else ""
    if (not key.strip() or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", config.azure_expected_model)
            or not config.azure_api_capabilities_verified
            or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", config.triage_model)
            or config.triage_provider_slug != "azure" or config.triage_provider_name != "Azure"
            or not config.triage_access_verified or not config.triage_token_bound_verified
            or not config.triage_price_snapshot or config.triage_usd_to_idr is None
            or config.triage_prompt_usd_per_million is None or config.triage_completion_usd_per_million is None
            or config.triage_reservation_idr <= 0):
        raise ProviderFailure("CONFIGURATION_REQUIRED", cost_idr=0)
    endpoint(config)
    maximum = ((MAX_INPUT_TOKENS * config.triage_prompt_usd_per_million +
                MAX_OUTPUT_TOKENS * config.triage_completion_usd_per_million) /
               Decimal(1_000_000) * config.triage_usd_to_idr).to_integral_value(rounding=ROUND_CEILING)
    if maximum > config.triage_reservation_idr or config.triage_reservation_idr > config.budget_idr:
        raise ProviderFailure("CONFIGURATION_REQUIRED", cost_idr=0)


def structured_schema(value):
    # Azure strict schema omits these constraints; full original schema is still
    # validated locally after the response. Never change properties or enum values.
    unsupported = {"minLength", "maxLength", "pattern", "format", "minimum", "maximum", "multipleOf",
                   "minItems", "maxItems", "uniqueItems", "minProperties", "maxProperties", "title", "default"}
    if isinstance(value, list):
        return [structured_schema(v) for v in value]
    if not isinstance(value, dict):
        return value
    result = {}
    for key, item in value.items():
        if key in unsupported:
            continue
        # Property/definition names may themselves match JSON-schema keywords.
        result[key] = ({name: structured_schema(node) for name, node in item.items()}
                       if key in {"properties", "$defs"} else structured_schema(item))
    return result


def request_body(config, prompt, **contract):
    body = openrouter_body(config, prompt, **contract)
    del body["provider"]
    # Restrict deployments to the operator-verified non-reasoning chat contract.
    body["max_completion_tokens"] = body.pop("max_tokens")
    body["response_format"]["json_schema"]["schema"] = structured_schema(body["response_format"]["json_schema"]["schema"])
    return body


class AzureTransport(OpenRouterTransport):
    provider_id = "azure"
    # Azure v1 usage has token counts, not a per-request monetary invoice.
    # Retain the full reservation as COST_UNKNOWN; never settle a tariff estimate.
    reported_cost_supported = False

    def prepare(self, prompt):
        require_configuration(self.config)
        secret = self.config.azure_api_key.get_secret_value()
        return endpoint(self.config), {"api-key": secret}, request_body(self.config, prompt, **self.contract), secret

    def response_provider(self, body, raw):
        # This denotes the configured Azure endpoint, not model-vendor attestation.
        return "Azure"
