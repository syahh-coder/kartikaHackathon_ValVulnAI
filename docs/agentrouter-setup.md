# Panduan Menjalankan ValVuln AI dengan AgentRouter

Adapter **AgentRouter** (`https://agentrouter.org`) telah diintegrasikan ke sistem triage AI teks ValVuln AI secara aman (*TEXT-ONLY*, isolasi kredensial, proteksi budget).

---

## 1. Masukkan API Key Anda

Buka file privat [`.env.agentrouter`](file:///d:/BelajarCyberSec/kartikaHackathon/.env.agentrouter) di root folder proyek:

```powershell
notepad .env.agentrouter
```

Cari baris berikut dan tempelkan API key Anda:
```env
VALVULN_AGENTROUTER_API_KEY=sk-ar-xxxxxx...
```

*(Opsional)* Anda dapat menyesuaikan model jika ingin menggunakan model tertentu (default: `openai/gpt-4o-mini`):
```env
VALVULN_TRIAGE_MODEL=openai/gpt-4o-mini
```
Model lain yang didukung AgentRouter antara lain: `anthropic/claude-3-5-sonnet`, `deepseek/deepseek-chat`, `google/gemini-2.0-flash`, dll.

> [!NOTE]
> File `.env.agentrouter` otomatis diabaikan oleh Git (`.gitignore: .env.*`), sehingga key Anda tidak akan pernah ter-commit atau bocor.

---

## 2. Periksa Validitas Konfigurasi

Jalankan script verifikasi preflight:

```powershell
.\.venv\Scripts\python.exe -m scripts.check_agentrouter_config
```

Jika key sudah diisi, output akan menampilkan:
```text
=== Pemeriksaan Konfigurasi AgentRouter ===
[OK] VALVULN_TRIAGE_MODE=live
[OK] VALVULN_TRIAGE_PROVIDER=agentrouter
[OK] VALVULN_AGENTROUTER_API_KEY terisi
[OK] VALVULN_AGENTROUTER_ENDPOINT valid
[OK] VALVULN_TRIAGE_MODEL terisi
...
Status validasi provider: BERHASIL (Konfigurasi siap untuk live chat triage)
```

---

## 3. Jalankan Aplikasi

Untuk menjalankan aplikasi web ValVuln AI dengan konfigurasi AgentRouter:

### Opsi A: Local Uvicorn (PowerShell)
```powershell
# Copy ke .env aktif lokal
Copy-Item .env.agentrouter .env

# Jalankan server FastAPI
.\.venv\Scripts\python.exe -m uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000
```
Buka browser di: [http://127.0.0.1:8000](http://127.0.0.1:8000)

### Opsi B: Docker Compose
```powershell
docker compose --env-file .env.agentrouter up -d --build
```

