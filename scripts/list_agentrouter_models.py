"""Utility script to query the live list of models available on your AgentRouter account."""
import sys
import httpx
from app.config import Settings


def main():
    config = Settings(_env_file=".env.agentrouter")
    key = config.agentrouter_api_key.get_secret_value() if config.agentrouter_api_key else ""
    if not key.strip():
        print("[ERROR] VALVULN_AGENTROUTER_API_KEY belum diisi di file .env.agentrouter.")
        print("Silakan buka .env.agentrouter dan masukkan API key Anda terlebih dahulu.")
        return 1

    headers = {"Authorization": f"Bearer {key}"}
    urls_to_try = [
        "https://agentrouter.org/v1/models",
        "https://co.agentrouter.org/v1/models",
    ]

    print("Menghubungi AgentRouter untuk mengambil daftar model aktif...\n")
    data = None
    for url in urls_to_try:
        try:
            resp = httpx.get(url, headers=headers, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                print(f"[OK] Berhasil terhubung ke: {url}")
                break
            elif resp.status_code == 401:
                print(f"[ERROR] API key ditolak (401 Unauthorized) oleh {url}.")
                return 1
        except Exception as exc:
            continue

    if not data or "data" not in data:
        print("[INFO] Tidak dapat mengambil daftar model otomatis secara langsung.")
        print("Anda dapat melihat daftar model di dashboard web: https://agentrouter.org")
        return 1

    models = sorted([m.get("id") for m in data.get("data", []) if m.get("id")])
    print(f"\nDitemukan {len(models)} model yang tersedia di akun Anda:")
    print("-" * 50)
    for model_id in models:
        print(f" - {model_id}")
    print("-" * 50)
    print("\nSalin salah satu nama model di atas ke `VALVULN_TRIAGE_MODEL` di file `.env.agentrouter`.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

