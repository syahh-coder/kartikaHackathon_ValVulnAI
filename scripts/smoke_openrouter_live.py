"""Perform a live triage smoke test using the configured OpenRouter credentials."""
import asyncio
import json
import sys

from app.config import Settings
from app.providers.openrouter import OpenRouterTransport
from app.providers.triage_contracts import TriageSuggestion

SAMPLE_PROMPT = json.dumps({
    "report": {
        "title": "IDOR / BAC on user procurement invoice view",
        "text": "Bug hunter menemukan bahwa mengubah parameter id dari 101 ke 102 pada endpoint /api/procurement/invoices/101 memungkinkan akses ke invoice milik vendor lain tanpa otorisasi.",
        "attachment_text": "",
        "draft_version": 1
    },
    "public_scope": {
        "scope_version_id": "scope-v1",
        "version": 1,
        "rules": [
            "In scope: Insecure Direct Object References (IDOR/BAC) pada modul pengadaan.",
            "Out of scope: DoS, social engineering."
        ]
    },
    "data_authority": "UNTRUSTED_DATA_ONLY",
    "target_execution_allowed": False
})


async def run_smoke():
    print("=== LIVE SMOKE TEST: OpenRouter Text Triage ===")
    config = Settings()

    print(f"Provider      : {config.triage_provider}")
    print(f"Mode          : {config.triage_mode}")
    print(f"Model Target  : {config.triage_model}")
    print(f"Provider Slug : {config.triage_provider_slug}")

    if config.triage_mode != "live":
        print("\n[ERROR] VALVULN_TRIAGE_MODE di .env masih 'mock'. Ubah menjadi 'live' terlebih dahulu.")
        return 1

    transport = OpenRouterTransport(config)
    print("\nMengirim sample triage report ke OpenRouter...")
    try:
        reply = await transport.dispatch("smoke-call-001", SAMPLE_PROMPT)
        print("\n[SUCCESS] Respons berhasil diterima dari AI!")
        print(f"Model yang merespons : {reply.result.resolved_model_id}")
        print(f"Provider inferensi   : {reply.result.inference_provider}")
        print(f"Usage Token          : {reply.result.usage}")
        print(f"Biaya IDR (estimasi) : Rp{reply.result.actual_cost_idr or 0}")
        print("-" * 50)
        print("Konten Triage JSON:")
        print(reply.result.text)
        print("-" * 50)
        return 0
    except Exception as exc:
        print(f"\n[ERROR] Triage gagal: {exc}")
        if hasattr(exc, "raw") and exc.raw:
            print(f"Detail respons server: {exc.raw}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(run_smoke()))

