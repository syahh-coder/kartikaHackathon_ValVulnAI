# ValVuln AI

Purwarupa lokal untuk membantu triage laporan kerentanan, menyiapkan klaim pemeriksaan, dan memverifikasi klaim yang didukung pada lab sendiri.

**Kondisi lab dari UI:** login admin → **Reset data lab** → pilih **Lab rentan / Lab kontrol diperbaiki** → **Terapkan kondisi & reset data lab**. Pilihan berlaku untuk13 titik existing BAC-08/XSS-01..08/UP-01..04, termasuk pencarian katalog. Validasi otomatis agent tetap3 jalur BAC-08/XSS-08/UP-04 dan verdict mengikuti bukti. Laporan/ledger tersimpan, ID objek lab berubah. Mode kontrol bukan AI memperbaiki celah. [Panduan dan API untuk FE](docs/lab-reset-ui.md).

**Uji manual target yang sama:** di panel admin klik **Aktifkan pengujian manual**, lalu **Buka lab manual di port8001**. Login memakai akun lab requester-a/requester-b. Snapshot, objek dan kondisi mengikuti target worker. Selama sesi manual, validasi agent dikunci; setelah selesai gunakan reset untuk membuka validasi kembali. [Panduan](docs/manual-lab.md).

**Status 14 November 2026:** **Groq GPT-OSS120B berhasil satu triage live** melalui API aplikasi/ledger existing;85 tes terarah mempunyai hasil terakhir lulus. AI mengisi draf klaim dan pengguna mengonfirmasi sebelum backend membuat run. **Benchmark/GT manual belum selesai.** [Hasil dan konfigurasi Groq](docs/groq-setup.md), [baseline integrasi](docs/ai-validation-integration.md).

Tim: **ukas and codex vs everbody**. [Repository](https://github.com/syahh-coder/kartikaHackathon_ValVulnAI).

## Alur yang tersedia

1. Hunter/admin login, memilih program, lalu mengirim teks atau laporan TXT/MD.
2. Admin mengatur guideline dan in-scope/out-of-scope terversi, terpisah dari laporan.
3. **Minta saran AI** mengekstrak klaim dan informasi yang kurang. Prioritas provider: **Groq**, **OpenRouter**, lalu **Azure Foundry**, dipilih operator tanpa fallback otomatis.
4. **Siapkan validasi dari saran AI** mengisi formulir klaim. Backend memeriksa binding, scope, subtype dan prasyarat. Pengguna memeriksa/melengkapi field lalu mengonfirmasi.
5. Backend memeriksa ulang izin/readiness, membuat run, dan worker menjalankan fixture HTTP/browser terdaftar.
6. Verifier menilai dampak/kontrol. Admin meninjau lalu membagikan ringkasan tersanitasi kepada hunter.

Model hanya menghasilkan data terstruktur, tanpa tools atau akses langsung ke Docker. Planner lab tetap deterministik. Saran AI, hasil verifier dan keputusan admin mempunyai asal yang berbeda.

## Menjalankan

Butuh Docker Desktop/Engine Linux containers. Python 3.11 dipakai untuk helper setup pertama dan evaluator host.

```powershell
# Setup pertama: jangan menimpa .env jika sudah ada.
Copy-Item .env.example .env
py -3.11 scripts/setup_local.py
docker compose up -d --build
docker compose exec app python -m app.operator
```

Seed meminta password lokal 12–128 karakter untuk akun sintetis `admin`, `hunter-a`, dan `hunter-b`. Buka **http://127.0.0.1:8000**. Setelah setup/seed, startup cukup:

```powershell
docker compose up -d --build
```

Default instalasi baru **MOCK**, tanpa API key. Startup tidak memanggil AI atau menguji target. Scope dan kondisi lab disiapkan operator secara eksplisit; [quick start](docs/review-quickstart.md) dan [panduan manual](docs/manual-lab.md). Restart mempertahankan volume/database/ledger; gunakan `docker compose stop` untuk berhenti.

Tiga container normal: app, worker dan lab. SQLite app/lab terpisah; satu worker aktif. Port 8000 hanya loopback, lab asli tidak dipublikasikan. Salinan manual opsional memakai container/volume terpisah di **http://127.0.0.1:8001** setelah disiapkan; bukan target agent.

## Provider AI

[Groq yang sudah terhubung](docs/groq-setup.md), [konfigurasi dan pergantian provider](docs/provider-setup.md). Key hanya di file privat; tidak diberikan ke worker/lab.

```powershell
.\.venv\Scripts\python.exe -m scripts.check_text_provider_config --provider groq
.\.venv\Scripts\python.exe -m scripts.check_text_provider_config --provider openrouter
.\.venv\Scripts\python.exe -m scripts.check_text_provider_config --provider azure
```

Checker tidak menghubungi provider. Kedua adapter memerlukan endpoint/model yang mendukung strict JSON schema, akses/kuota dan profil biaya yang diverifikasi. API key saja belum cukup. Smoke live ditunda sampai konfigurasi siap. Budget bersama maksimal **Rp50.000**; biaya tidak diketahui tetap menahan reservasi.

## Cakupan dan bukti

| Bagian | Kondisi aktual |
| --- | --- |
| Validasi produk | BAC-08: hapus lampiran lintas pemilik; XSS-08: pratinjau notifikasi; UP-04: nama lampiran |
| Lab manual | 13 kondisi existing: BAC-08, XSS-01..08, UP-01..04; bukan 13 subtype produk otomatis |
| Di luar scope aktif | BUSINESS_LOGIC, BAC-01..07, DoS/race, eksekusi PoC/script bebas |
| AI live | Groq GPT-OSS120B: satu triage sukses; OpenRouter sebelumnya timeout, Azure menunggu konfigurasi |
| Evaluasi | 20 kandidat; GT manual/bukti per kasus dan 40 slot A/B nyata masih pending |
| Materi | Slide, thumbnail dan screenshot lokal tersedia; video/tautan final menunggu review |

`OUT_OF_SCOPE`, `UNSUPPORTED`, timeout dan kegagalan reproduksi tidak otomatis berarti laporan salah. Produk menilai klaim/bukti; tidak menentukan apakah teks ditulis manusia atau AI. Belum ada klaim accuracy, precision, recall atau penghematan waktu.

## Pengembangan dan handoff

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.lock
.\.venv\Scripts\python.exe -m pip install --no-deps -e .
.\.venv\Scripts\python.exe -m pytest -q tests/test_ai_validation_draft.py tests/test_provider_operations.py
```

- [Flowchart dan kontrak backend](docs/backend-flow.md), [OpenAPI](docs/api/openapi.json), [roles](docs/roles.md).
- [PRD](prd.md), [arsitektur](docs/architecture.md), [runtime](docs/runtime.md), [batas keamanan](docs/security-review.md).
- [Evaluasi functional-v2](docs/evaluation.md), [runbook](docs/r3-runbook.md), [13 titik lab](docs/manual-lab.md).
- [Paket review terkini](docs/final-review.md), [review manual terakhir](docs/manual-final-review.md), [materi submission](submission/README.md).
- [Distribusi](docs/distribution.md), [checklist](docs/submission-checklist.md), [atribusi/lisensi](docs/third-party.md).

Repo GitHub menjadi kanal source dan integrasi AI yang dipublikasikan. Release aplikasi, video YouTube, slide publik dan submit formulir belum selesai. Lisensi proyek belum dipilih pengguna. Riwayat tahap lama tersedia pada dokumen verifikasi dan Git; M6 tetap DEFERRED, tidak menjadi antrean kerja aktif.
