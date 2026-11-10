"""Create/check private Azure text settings locally. Makes zero provider requests."""
import argparse
import json
from decimal import Decimal, ROUND_CEILING
from pathlib import Path

from pydantic import ValidationError

from app.config import Settings
from app.providers.contracts import ProviderFailure
from app.providers.text_provider import require_configuration, secret

ROOT = Path(__file__).resolve().parents[1]


def check(path: Path) -> dict:
    if not path.is_file():
        return {"status": "CONFIGURATION_REQUIRED", "missing": ["private_config_file"], "provider_requests": 0}
    try:
        config = Settings(_env_file=path)
    except (ValidationError, ValueError, OSError):
        # Validation exceptions may contain input values, including credentials.
        return {"status": "CONFIGURATION_INVALID", "message": "Periksa nama field, tipe angka dan true/false di file privat.",
                "provider_requests": 0}
    required = {
        "VALVULN_TRIAGE_MODE=live": config.triage_mode == "live",
        "VALVULN_TRIAGE_PROVIDER=azure": config.triage_provider == "azure",
        "VALVULN_AZURE_API_KEY": bool(secret(config).strip()),
        "VALVULN_AZURE_ENDPOINT": bool(config.azure_endpoint),
        "VALVULN_TRIAGE_MODEL": bool(config.triage_model),
        "VALVULN_AZURE_EXPECTED_MODEL": bool(config.azure_expected_model),
        "VALVULN_TRIAGE_PROVIDER_SLUG=azure": config.triage_provider_slug == "azure",
        "VALVULN_TRIAGE_PROVIDER_NAME=Azure": config.triage_provider_name == "Azure",
        "VALVULN_TRIAGE_ACCESS_VERIFIED": config.triage_access_verified,
        "VALVULN_TRIAGE_TOKEN_BOUND_VERIFIED": config.triage_token_bound_verified,
        "VALVULN_AZURE_API_CAPABILITIES_VERIFIED": config.azure_api_capabilities_verified,
        "VALVULN_TRIAGE_PRICE_SNAPSHOT": bool(config.triage_price_snapshot),
        "VALVULN_TRIAGE_PROMPT_USD_PER_MILLION": config.triage_prompt_usd_per_million is not None,
        "VALVULN_TRIAGE_COMPLETION_USD_PER_MILLION": config.triage_completion_usd_per_million is not None,
        "VALVULN_TRIAGE_USD_TO_IDR": config.triage_usd_to_idr is not None,
        "VALVULN_TRIAGE_RESERVATION_IDR": config.triage_reservation_idr > 0,
    }
    minimum = None
    if all(value is not None for value in (config.triage_prompt_usd_per_million,
                                           config.triage_completion_usd_per_million, config.triage_usd_to_idr)):
        minimum = int(((8192 * config.triage_prompt_usd_per_million + 1024 * config.triage_completion_usd_per_million)
                       / Decimal(1_000_000) * config.triage_usd_to_idr).to_integral_value(rounding=ROUND_CEILING))
    valid = all(required.values())
    if valid:
        try:
            require_configuration(config)
        except ProviderFailure:
            valid = False
    return {"status": "CONFIGURED_NOT_VERIFIED" if valid else "CONFIGURATION_REQUIRED",
            "missing": [name for name, present in required.items() if not present],
            "endpoint_model_and_reservation_valid": valid, "minimum_reservation_idr": minimum,
            "live_verified": False, "provider_requests": 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, default=ROOT/".env.azure")
    parser.add_argument("--init", action="store_true", help="Create only if missing; never overwrite existing config")
    args = parser.parse_args()
    if args.init and not args.env_file.exists():
        with args.env_file.open("x", encoding="utf-8") as stream:
            stream.write((ROOT/".env.azure.example").read_text(encoding="utf-8"))
    result = check(args.env_file)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "CONFIGURED_NOT_VERIFIED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
