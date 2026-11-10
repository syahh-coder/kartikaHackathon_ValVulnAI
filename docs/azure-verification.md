# Verifikasi adapter Azure Foundry, 7 November 2026

**CODE_TESTED. LIVE_VERIFIED=false; CONFIGURATION_REQUIRED.** Akun/kredit/kuota/deployment Azure belum tersedia untuk diperiksa. Tidak ada pemanggilan cloud, target, pembelian, provisioning, upgrade billing, publikasi atau submission pada batch ini.

## Perubahan

- Provider eksplisit `VALVULN_TRIAGE_PROVIDER=openrouter|azure`; default OpenRouter lama dipertahankan. Azure memakai key resource dan OpenAI v1 Chat Completions pada hostname Azure yang divalidasi; project endpoint, origin lain, port, userinfo, query dan redirect ditolak. No tools, fallback, auto-routing atau model-to-worker dispatch.
- Triage/UI readiness dan evaluator teks menggunakan factory yang sama. Deployment name dipisahkan dari model/version respons yang dikunci. Endpoint/model masuk snapshot konfigurasi evaluator. Redaksi menggunakan key provider terpilih, termasuk key Azure yang tidak memiliki awalan `sk-`.
- Transport HTTP dibatasi timeout, 8192 input/1024 output dan respons64KiB. Azure strict schema membuang constraint yang tidak didukung API; schema Pydantic asli tetap memeriksa panjang, enum, subtype dan referensi sesudah respons. Refusal, model drift dan respons tidak sah tidak menjadi saran/verdict.
- Biaya Azure tetap COST_UNKNOWN dengan reservasi penuh; token usage disimpan. Tidak membuat tagihan aktual dari estimasi tarif atau kredit gratis. Freeze smoke tetap memerlukan rekonsiliasi biaya sesuai gate lama, bukan dilonggarkan agar lolos.
- Template publik `.env.azure.example`, file privat `.env.azure` yang dibuat tanpa overwrite, checker tanpa jaringan dan overlay `compose.azure.yaml` untuk volume preview yang sudah ada. Panduan pengguna ada di [azure-setup.md](azure-setup.md).

## Pemeriksaan aktual

Perintah:

```powershell
.venv\Scripts\python.exe -m pytest tests/test_azure_text.py tests/test_text_triage.py tests/test_text_benchmark.py tests/test_form_validation_feedback.py -q --tb=short --junitxml=artifacts/azure-setup/targeted-tests.xml
```

**148 passed dalam95,70 detik**, terdiri40 kasus Azure baru dan108 regresi terkait. Semua HTTP provider dicegat `httpx.MockTransport`; fixture melarang HTTP jaringan nyata. Mencakup:

- Penolakan endpoint/key/akses/batas cadangan tidak sah sebelum dispatch, autentikasi `api-key`, kontrak JSON dan pin model/deployment.
- HTTP error/redirect/refusal/tools/limit/schema, redaksi nilai key dan validasi lokal sesudah normalisasi schema.
- Alur API hunter ke saran Azure simulasi, provenance/attempt, reservasi COST_UNKNOWN, tanpa record run/action/evidence/assessment baru; live salah konfigurasi tidak fallback ke mock atau membuat ledger.
- Dispatch evaluator dengan kontrak prediksi melalui ledger yang sama, readiness saat startup tanpa request, checker menyembunyikan input invalid.
- Regresi OpenRouter, pembatalan/otorisasi/ledger/freeze serta feedback validasi guideline admin.

JUnit: [targeted-tests.xml](../artifacts/azure-setup/targeted-tests.xml). Fixture awal sempat gagal karena duplikasi keyword, tipe secret dan nama field tes; sudah diperbaiki sebelum pemeriksaan final di atas. Hasil kegagalan awal tidak dihitung sebagai lulus.

Overlay Compose diperiksa melalui parsing JSON lokal tanpa mencetak env: [compose-check.json](../artifacts/azure-setup/compose-check.json), PASS. Menunjukkan app-only, provider Azure live eksplisit, planner mock, dispatcher mati dan volume `valvuln-review_preview_data` yang sama. Overlay **belum dijalankan** karena konfigurasi belum lengkap. File konfigurasi privat sudah diperiksa sekali tanpa request; key, endpoint, deployment/model dan harga/kelayakan akses masih perlu diisi.

Preview8010 dibangun ulang dengan source app terbaru, tetap MOCK. Health006 dan readiness diperiksa; hash enam file app/provider cocok host. Semua16 tabel bisnis preview identik sebelum/sesudah, begitu pula snapshot data dan ID container app/worker/lab instalasi asli8000. [Hasil update preview](../artifacts/azure-setup/preview-update-result.json), [log build](../artifacts/azure-setup/preview-build.log), [snapshot sebelum update](../artifacts/azure-setup/runtime-before-update.json). Pemeriksaan hash pertama sempat memasukkan file evaluator yang memang tidak ada pada image app; diperbaiki menjadi pemeriksaan source app tanpa mengulang rebuild. Evaluator diuji pada host, bukan dijalankan pada image app.

Paket source terbaru disiapkan sebagai reviewv5 pada [final-review.md](final-review.md); arsip sebelumnya dipertahankan. Tidak ada migrasi schema baru; schema source tetap006. Instalasi asli8000 dan M6 DEFERRED tidak dikerjakan ulang.

## Checkpoint berikutnya

Pengguna mengaktifkan Students dan menyediakan konfigurasi pada `.env.azure` sesuai [langkah konkret](azure-setup.md). Setelah akses/kredit/kuota/tarif lengkap, satu smoke teks eksplisit melalui ledger aplikasi dapat dijalankan dalam budget. Sampai respons aktual diperiksa, integrasi tetap CODE_TESTED. GT, bukti kandidat, freeze, benchmark dan review/publikasi tetap terpisah.
