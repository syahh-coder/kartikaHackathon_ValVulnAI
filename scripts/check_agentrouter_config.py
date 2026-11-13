import sys
from decimal import Decimal, ROUND_CEILING

from app.config import Settings
from app.providers.agentrouter import endpoint, require_configuration
from app.providers.contracts import ProviderFailure
from app.providers.triage_contracts import MAX_INPUT_TOKENS, MAX_OUTPUT_TOKENS


def check():
    config = Settings(_env_file=".env.agentrouter")
    print("=== Pemeriksaan Konfigurasi AgentRouter ===")
    checks = {
        "VALVULN_TRIAGE_MODE=live": config.triage_mode == "live",
        "VALVULN_TRIAGE_PROVIDER=agentrouter": config.triage_provider == "agentrouter",
        "VALVULN_AGENTROUTER_API_KEY terisi": bool(config.agentrouter_api_key and config.agentrouter_api_key.get_secret_value().strip()),
        "VALVULN_AGENTROUTER_ENDPOINT valid": bool(config.agentrouter_endpoint),
        "VALVULN_TRIAGE_MODEL terisi": bool(config.triage_model),
        "VALVULN_TRIAGE_PROVIDER_SLUG=agentrouter": config.triage_provider_slug == "agentrouter",
        "VALVULN_TRIAGE_PROVIDER_NAME=AgentRouter": config.triage_provider_name == "AgentRouter",
        "VALVULN_TRIAGE_ACCESS_VERIFIED=true": config.triage_access_verified,
        "VALVULN_TRIAGE_TOKEN_BOUND_VERIFIED=true": config.triage_token_bound_verified,
        "VALVULN_TRIAGE_PRICE_SNAPSHOT terisi": bool(config.triage_price_snapshot),
        "Tarif prompt USD terisi": config.triage_prompt_usd_per_million is not None,
        "Tarif completion USD terisi": config.triage_completion_usd_per_million is not None,
        "Kurs USD/IDR terisi": config.triage_usd_to_idr is not None,
        "VALVULN_TRIAGE_RESERVATION_IDR > 0": config.triage_reservation_idr > 0,
    }

    all_ok = True
    for name, ok in checks.items():
        status = "[OK]" if ok else "[BELUM]"
        print(f"{status} {name}")
        if not ok:
            all_ok = False

    if config.triage_prompt_usd_per_million is not None and config.triage_completion_usd_per_million is not None and config.triage_usd_to_idr is not None:
        min_res = int(((MAX_INPUT_TOKENS * config.triage_prompt_usd_per_million +
                        MAX_OUTPUT_TOKENS * config.triage_completion_usd_per_million) /
                       Decimal(1_000_000) * config.triage_usd_to_idr).to_integral_value(rounding=ROUND_CEILING))
        print(f"\nEstimasi reservasi minimum per pemanggilan: Rp{min_res:,}")
        if config.triage_reservation_idr < min_res:
            print(f"[PERINGATAN] VALVULN_TRIAGE_RESERVATION_IDR ({config.triage_reservation_idr}) lebih kecil dari kalkulasi batas ({min_res})")
            all_ok = False

    try:
        require_configuration(config)
        print("\nStatus validasi provider: BERHASIL (Konfigurasi siap untuk live chat triage)")
    except ProviderFailure as exc:
        print(f"\nStatus validasi provider: {exc.code} (Masih ada konfigurasi yang belum lengkap)")
        all_ok = False

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(check())

