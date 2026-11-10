"""AgentRouter OpenAI-compatible v1 chat transport. Bounded, non-streaming, TEXT-ONLY."""
import json
import re
from decimal import Decimal, ROUND_CEILING
from urllib.parse import urlsplit

import httpx

from app.config import Settings
from app.providers.contracts import ProviderFailure
from app.providers.openrouter import OpenRouterTransport, request_body as openrouter_body
from app.providers.triage_contracts import MAX_INPUT_TOKENS, MAX_OUTPUT_TOKENS

DEFAULT_ENDPOINT = "https://agentrouter.org/v1/chat/completions"


def endpoint(config: Settings) -> str:
    value = config.agentrouter_endpoint or DEFAULT_ENDPOINT
    url = urlsplit(value)
    if url.scheme != "https" or not url.hostname:
        raise ProviderFailure("CONFIGURATION_REQUIRED", cost_idr=0)
    # Ensure standard OpenAI-compatible chat completions path (/v1/chat/completions)
    path = url.path.rstrip("/")
    if not path.endswith("/chat/completions"):
        if path.endswith("/v1"):
            path = f"{path}/chat/completions"
        else:
            path = f"{path}/v1/chat/completions"
    return f"https://{url.hostname}{path}"


def require_configuration(config: Settings) -> None:
    if config.triage_mode == "replay":
        raise ProviderFailure("REPLAY_NOT_CONFIGURED", cost_idr=0)
    if config.triage_mode != "live":
        return
    key = config.agentrouter_api_key.get_secret_value() if config.agentrouter_api_key else ""
    if (not key.strip() or not config.triage_model or
            config.triage_provider_slug != "agentrouter" or config.triage_provider_name != "AgentRouter" or
            not config.triage_access_verified or not config.triage_token_bound_verified or
            not config.triage_price_snapshot or config.triage_usd_to_idr is None or
            config.triage_prompt_usd_per_million is None or config.triage_completion_usd_per_million is None or
            config.triage_reservation_idr <= 0):
        raise ProviderFailure("CONFIGURATION_REQUIRED", cost_idr=0)

    endpoint(config)

    maximum = ((MAX_INPUT_TOKENS * config.triage_prompt_usd_per_million +
                MAX_OUTPUT_TOKENS * config.triage_completion_usd_per_million) /
               Decimal(1_000_000) * config.triage_usd_to_idr).to_integral_value(rounding=ROUND_CEILING)
    if maximum > config.triage_reservation_idr or config.triage_reservation_idr > config.budget_idr:
        raise ProviderFailure("CONFIGURATION_REQUIRED", cost_idr=0)


def request_body(config: Settings, prompt: str, **contract) -> dict:
    body = openrouter_body(config, prompt, **contract)
    # Strip openrouter-specific vendor routing block
    body.pop("provider", None)
    return body


class AgentRouterTransport(OpenRouterTransport):
    provider_id = "agentrouter"
    reported_cost_supported = False

    def prepare(self, prompt: str):
        require_configuration(self.config)
        secret = self.config.agentrouter_api_key.get_secret_value()
        url = endpoint(self.config)
        headers = {
            "Authorization": f"Bearer {secret}",
            "Content-Type": "application/json",
        }
        return url, headers, request_body(self.config, prompt, **self.contract), secret

    def response_provider(self, body: dict, raw: str) -> str:
        return "AgentRouter"
