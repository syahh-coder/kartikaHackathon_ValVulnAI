"""Secret-safe local checks; never contacts a provider or changes configuration."""
import argparse
import json
from decimal import Decimal, ROUND_CEILING
from pathlib import Path

from pydantic import ValidationError

from app.config import Settings
from app.providers.contracts import ProviderFailure
from app.providers.text_provider import PROVIDER_PRIORITY, require_configuration, secret
from app.providers.triage_contracts import MAX_INPUT_TOKENS, MAX_OUTPUT_TOKENS


def check(path: Path, provider: str) -> dict:
    result = {"provider": provider, "priority": PROVIDER_PRIORITY,
              "automatic_fallback": False, "provider_requests": 0, "live_verified": False,
              "input_tokens": MAX_INPUT_TOKENS, "output_tokens": MAX_OUTPUT_TOKENS}
    if not path.is_file():
        return result | {"status": "CONFIGURATION_REQUIRED", "missing": ["private_config_file"]}
    try:
        config = Settings(_env_file=path)
    except (ValidationError, ValueError, OSError):
        return result | {"status": "CONFIGURATION_INVALID", "missing": ["valid_field_names_and_types"]}
    required = {"triage_mode=live": config.triage_mode == "live",
                "triage_provider=" + provider: config.triage_provider == provider,
                "api_key": bool(secret(config).strip()), "model": bool(config.triage_model),
                "provider_slug": bool(config.triage_provider_slug), "provider_name": bool(config.triage_provider_name),
                "access_verified": config.triage_access_verified,
                "token_bound_verified": config.triage_token_bound_verified,
                "price_snapshot": bool(config.triage_price_snapshot),
                "prompt_price": config.triage_prompt_usd_per_million is not None,
                "completion_price": config.triage_completion_usd_per_million is not None,
                "exchange_rate": config.triage_usd_to_idr is not None, "reservation": config.triage_reservation_idr > 0}
    minimum = None
    if all(required[k] for k in ("prompt_price", "completion_price", "exchange_rate")):
        minimum = int(((MAX_INPUT_TOKENS * config.triage_prompt_usd_per_million +
                        MAX_OUTPUT_TOKENS * config.triage_completion_usd_per_million) / Decimal(1_000_000) *
                       config.triage_usd_to_idr).to_integral_value(rounding=ROUND_CEILING))
    missing = [k for k, valid in required.items() if not valid]
    if not missing:
        try:
            require_configuration(config)
        except ProviderFailure:
            missing.append("endpoint_model_provider_and_reservation_contract")
    return result | {"status": "CONFIGURATION_REQUIRED" if missing else "CONFIGURED_NOT_VERIFIED",
                     "missing": missing, "minimum_reservation_idr": minimum,
                     "requires_endpoint_json_schema_support": True}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", choices=["groq", "openrouter", "azure"], default="groq")
    parser.add_argument("--env-file", type=Path)
    args = parser.parse_args(argv)
    path = args.env_file or Path(".env" if args.provider == "openrouter" else ".env." + args.provider)
    result = check(path, args.provider)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "CONFIGURED_NOT_VERIFIED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
