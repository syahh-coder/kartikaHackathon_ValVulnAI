"""Fixed-origin Groq Free Plan chat adapter, TEXT ONLY with strict schema."""
from app.config import Settings
from app.providers.azure import structured_schema
from app.providers.contracts import ProviderFailure
from app.providers.openrouter import OpenRouterTransport, request_body as openrouter_body

ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
MODELS = {"openai/gpt-oss-120b", "openai/gpt-oss-20b"}


def require_configuration(config: Settings) -> None:
    if config.triage_mode == "replay":
        raise ProviderFailure("REPLAY_NOT_CONFIGURED", cost_idr=0)
    if config.triage_mode != "live":
        return
    key = config.groq_api_key.get_secret_value() if config.groq_api_key else ""
    if (not key.strip() or config.triage_model not in MODELS or
            config.triage_provider_slug != "groq" or config.triage_provider_name != "Groq" or
            config.triage_access_tier != "FREE_TIER" or not config.triage_access_verified or
            not config.triage_token_bound_verified or not config.triage_price_snapshot or
            config.triage_prompt_usd_per_million != 0 or config.triage_completion_usd_per_million != 0 or
            config.triage_usd_to_idr is None or not 0 < config.triage_reservation_idr <= config.budget_idr):
        raise ProviderFailure("CONFIGURATION_REQUIRED", cost_idr=0)


def request_body(config: Settings, prompt: str, **contract) -> dict:
    body = openrouter_body(config, prompt, **contract)
    del body["provider"]  # Groq has no OpenRouter vendor-routing fields.
    body["max_completion_tokens"] = body.pop("max_tokens")
    body["reasoning_effort"] = "low"
    body["include_reasoning"] = False
    body["response_format"]["json_schema"]["schema"] = structured_schema(body["response_format"]["json_schema"]["schema"])
    return body


class GroqTransport(OpenRouterTransport):
    provider_id = "groq"
    # Groq usage reports tokens, not a per-request monetary invoice.
    # Even Free Plan keeps unknown reservation; never infer a zero bill.
    reported_cost_supported = False

    def prepare(self, prompt: str):
        require_configuration(self.config)
        key = self.config.groq_api_key.get_secret_value()
        return ENDPOINT, {"Authorization": "Bearer " + key}, request_body(self.config, prompt, **self.contract), key

    def response_provider(self, body: dict, raw: str) -> str:
        return "Groq"  # Configured endpoint identity, not model-vendor attestation.
