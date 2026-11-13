"""Bounded, non-streaming OpenRouter TEXT-ONLY transport. No worker dependency."""
import json
import math
import re
from dataclasses import dataclass
from decimal import Decimal, ROUND_CEILING
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone

import httpx

from app.config import Settings
from app.common import packed
from app.providers.contracts import ProviderFailure, ProviderResult
from app.providers.redaction import redact_text, redact_value
from app.providers.triage_contracts import MAX_INPUT_TOKENS, MAX_OUTPUT_TOKENS, SYSTEM_PROMPT, TriageSuggestion

ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
MAX_RESPONSE_BYTES = 65_536


def require_configuration(config: Settings) -> None:
    if config.triage_mode == "replay":
        raise ProviderFailure("REPLAY_NOT_CONFIGURED", cost_idr=0)
    if config.triage_mode != "live":
        return
    key = config.openrouter_api_key.get_secret_value() if config.openrouter_api_key else ""
    if (not key.strip() or not config.triage_model or not config.triage_provider_slug or
            not config.triage_provider_name or not config.triage_access_verified or
            not config.triage_token_bound_verified or not config.triage_price_snapshot or
            config.triage_usd_to_idr is None or config.triage_prompt_usd_per_million is None or
            config.triage_completion_usd_per_million is None or config.triage_reservation_idr <= 0):
        raise ProviderFailure("CONFIGURATION_REQUIRED", cost_idr=0)
    # No auto router, free router or preset. A fixed exact model is required.
    if (config.triage_model in {"openrouter/auto", "openrouter/free"} or
            not re.fullmatch(r"[A-Za-z0-9._-]+/[A-Za-z0-9._-]+(?::free)?", config.triage_model)):
        raise ProviderFailure("CONFIGURATION_REQUIRED", cost_idr=0)
    maximum = ((MAX_INPUT_TOKENS * config.triage_prompt_usd_per_million +
                MAX_OUTPUT_TOKENS * config.triage_completion_usd_per_million) /
               Decimal(1_000_000) * config.triage_usd_to_idr).to_integral_value(rounding=ROUND_CEILING)
    if maximum > config.triage_reservation_idr or config.triage_reservation_idr > config.budget_idr:
        raise ProviderFailure("CONFIGURATION_REQUIRED", cost_idr=0)


def request_body(config: Settings, prompt: str, *, system_prompt: str = SYSTEM_PROMPT,
                 schema: dict | None = None, schema_name: str = "triage") -> dict:
    return {
        "model": config.triage_model, "stream": False, "temperature": 0,
        "max_tokens": MAX_OUTPUT_TOKENS,
        "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
        "response_format": {"type": "json_schema", "json_schema": {
            "name": schema_name, "strict": True, "schema": schema if schema is not None else TriageSuggestion.model_json_schema()}},
        "provider": {"only": [config.triage_provider_slug], "allow_fallbacks": False,
                     "require_parameters": False, "max_price": {
                         "prompt": float(config.triage_prompt_usd_per_million or 0),
                         "completion": float(config.triage_completion_usd_per_million or 0), "request": 0}},
    }


def input_token_bound(config: Settings, prompt: str, **contract) -> int:
    # Conservative bound ONLY for operator-verified byte BPE tokenizers.
    # Include the schema/system strings plus 1024 tokens for chat framing.
    body = request_body(config, prompt, **contract)
    return len(json.dumps(body, ensure_ascii=False).encode("utf-8")) + 1024


def strict_json(text: str):
    def pairs(values):
        obj = {}
        for key, value in values:
            if key in obj:
                raise ValueError("Duplicate JSON key")
            obj[key] = value
        return obj
    def constant(_):
        raise ValueError("Non-finite JSON value")
    return json.loads(text, object_pairs_hook=pairs, parse_constant=constant)


def redacted_snapshot(data: bytes, secret: str) -> str:
    text = data.decode("utf-8", errors="replace")
    try:
        # Decode JSON escapes before redaction: an escaped key is still a secret.
        return packed(redact_value(strict_json(text), secret))
    except (ValueError, RecursionError):
        return redact_text(text, secret)


@dataclass
class TextReply:
    result: ProviderResult
    redacted_response: str
    cost_usd: str | None


class TextFailure(ProviderFailure):
    def __init__(self, code: str, *, raw: str | None = None, retry_after: float = 0):
        super().__init__(code, retry_after=retry_after)
        self.raw = raw


def retry_delay(value: str | None) -> float:
    if value is None:
        return 0
    try:
        seconds = float(value)
    except ValueError:
        try:
            seconds = (parsedate_to_datetime(value) - datetime.now(timezone.utc)).total_seconds()
        except (TypeError, ValueError, OverflowError):
            return 61  # Invalid header must not cause an immediate retry.
    return max(0, seconds) if math.isfinite(seconds) else 61


class OpenRouterTransport:
    provider_id = "openrouter"
    reported_cost_supported = True
    def __init__(self, config: Settings, *, http_transport: httpx.AsyncBaseTransport | None = None,
                 system_prompt: str = SYSTEM_PROMPT, schema: dict | None = None, schema_name: str = "triage"):
        self.config, self.http_transport = config, http_transport
        self.contract = {"system_prompt": system_prompt, "schema": schema, "schema_name": schema_name}

    def prepare(self, prompt: str):
        require_configuration(self.config)
        body = request_body(self.config, prompt, **self.contract)
        secret = self.config.openrouter_api_key.get_secret_value()
        return ENDPOINT, {"Authorization": "Bearer " + secret, "X-OpenRouter-Metadata": "enabled"}, body, secret

    def response_provider(self, body: dict, raw: str) -> str | None:
        actual_provider = body.get("provider")
        routing = body.get("openrouter_metadata")
        if routing:
            selected = [p["provider"] for p in routing["endpoints"]["available"] if p.get("selected") is True]
            if len(selected) != 1 or (actual_provider and actual_provider != selected[0]):
                raise TextFailure("PROVIDER_DRIFT", raw=raw)
            actual_provider = selected[0]
        return actual_provider

    async def dispatch(self, call_id: str, prompt: str) -> TextReply:
        config = self.config
        if config.triage_mode != "live":
            raise ProviderFailure("CONFIGURATION_REQUIRED", cost_idr=0)
        endpoint, headers, body, secret = self.prepare(prompt)
        if len(json.dumps(body, ensure_ascii=False).encode("utf-8")) + 1024 > MAX_INPUT_TOKENS:
            raise ProviderFailure("CONTEXT_LIMIT", cost_idr=0)
        # Fixed origin, no redirects/proxy environment, no SDK retries or hosted tools.
        try:
            async with httpx.AsyncClient(transport=self.http_transport, trust_env=False,
                                        follow_redirects=False, timeout=config.triage_timeout_seconds) as client:
                async with client.stream("POST", endpoint, headers=headers, json=body) as response:
                    data = bytearray()
                    async for chunk in response.aiter_bytes(chunk_size=4096):
                        data.extend(chunk)
                        if len(data) > MAX_RESPONSE_BYTES:
                            prefix = data[:MAX_RESPONSE_BYTES].decode("utf-8", errors="replace")
                            raise TextFailure("RESPONSE_LIMIT", raw=redact_text(prefix, secret) + "\n[TRUNCATED: RESPONSE_LIMIT]")
                    raw = redacted_snapshot(data, secret)
                    retry_header = response.headers.get("retry-after")
                    status, delay = response.status_code, retry_delay(retry_header)
        except httpx.TimeoutException:
            raise TextFailure("TRANSPORT_TIMEOUT") from None
        except httpx.TransportError:
            raise TextFailure("TRANSPORT_ERROR") from None
        code = {401: "AUTH_ERROR", 402: "QUOTA_EXHAUSTED", 403: "POLICY_BLOCKED",
                408: "TRANSPORT_TIMEOUT", 429: "TEMPORARY_429" if retry_header else "AMBIGUOUS_429"}.get(status)
        if code or status != 200:
            raise TextFailure(code or ("SERVER_ERROR" if 500 <= status < 600 else "HTTP_ERROR"),
                              raw=raw, retry_after=delay)
        try:
            body = strict_json(data.decode("utf-8"))
            if not isinstance(body, dict):
                raise ValueError()
            if body.get("error"):
                # A 200 error envelope is not a usable completion; never retry ambiguous errors.
                raise TextFailure("PROVIDER_ERROR", raw=raw)
            choices = body["choices"]
            if not isinstance(choices, list) or len(choices) != 1:
                raise ValueError()
            choice = choices[0]
            if not isinstance(choice, dict):
                raise ValueError()
            message = choice["message"]
            if not isinstance(message, dict) or message.get("role", "assistant") != "assistant":
                raise ValueError()
            if message.get("tool_calls") or message.get("function_call"):
                raise TextFailure("TOOLS_FORBIDDEN", raw=raw)
            actual_provider = self.response_provider(body, raw)
            usage = body.get("usage")
            counts = None
            cost_usd, cost_idr = None, None
            if usage is not None:
                if not isinstance(usage, dict):
                    raise ValueError()
                server_tools = usage.get("server_tool_use_details")
                if server_tools and (server_tools.get("tool_calls_executed", 0) or server_tools.get("tool_calls_requested", 0)):
                    raise TextFailure("TOOLS_FORBIDDEN", raw=raw)
                if "prompt_tokens" in usage or "completion_tokens" in usage:
                    counts = {"input_tokens": usage["prompt_tokens"], "output_tokens": usage["completion_tokens"]}
                    if any(type(n) is not int or n < 0 for n in counts.values()):
                        raise ValueError()
                    if counts["input_tokens"] > MAX_INPUT_TOKENS or counts["output_tokens"] > MAX_OUTPUT_TOKENS:
                        raise TextFailure("TOKEN_LIMIT", raw=raw)
                if self.reported_cost_supported and usage.get("cost") is not None:
                    value = usage["cost"]
                    if type(value) not in {int, float} or not math.isfinite(value) or value < 0:
                        raise ValueError()
                    cost_usd = str(value)
                    cost_idr = int((Decimal(cost_usd) * config.triage_usd_to_idr).to_integral_value(rounding=ROUND_CEILING))
            result = ProviderResult(call_id=call_id, provider_id=self.provider_id, requested_model_id=config.triage_model,
                                    resolved_model_id=body["model"], inference_provider=actual_provider,
                                    provider_request_id=body["id"], text=message.get("content") or "",
                                    refusal=bool(message.get("refusal")) or choice["finish_reason"] == "content_filter",
                                    finish_reason=choice["finish_reason"], usage=counts,
                                    cost_status="KNOWN" if cost_idr is not None else "COST_UNKNOWN", actual_cost_idr=cost_idr)
            return TextReply(result, raw, cost_usd)
        except (ValueError, KeyError, TypeError, AttributeError, UnicodeError, RecursionError):
            raise TextFailure("SCHEMA_ERROR", raw=raw) from None
