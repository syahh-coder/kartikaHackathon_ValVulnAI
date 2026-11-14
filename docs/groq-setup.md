# Groq direct —14 November2026

**Status aktual: CODE_TESTED dan satu triage LIVE_VERIFIED.** Model `openai/gpt-oss-120b` mengembalikan respons terstruktur lewat API aplikasi dan ledger existing. Ini bukti koneksi/integrasi teks, bukan benchmark, GT atau validasi seluruh kerentanan.

## Pengaturan

Prioritas terbaru: **Groq → OpenRouter → Azure Foundry**, dipilih eksplisit tanpa fallback otomatis. Pengguna mengonfirmasi Free Plan; adapter awal Groq hanya menerima profil FREE_TIER bertarif input/output0. Tidak mendukung perpindahan otomatis ke paket berbayar.

Template publik: [`.env.groq.example`](../.env.groq.example). Key hanya disimpan di `.env.groq`/`.env` privat, bukan source atau worker. Untuk instalasi existing, pengaturan triage Groq telah disalin ke `.env` tanpa mengubah budget/data/transport atau menghapus key lain. Startup normal tetap:

```powershell
docker compose up -d --build
```

Untuk memilih profil file Groq secara eksplisit pada **project/volume yang sama**:

```powershell
.\.venv\Scripts\python.exe -m scripts.check_text_provider_config --provider groq --env-file .env.groq
docker compose -f compose.yaml -f compose.provider.groq.yaml up -d --no-deps app
```

Jangan mengganti project Compose atau volume untuk memperoleh ledger/budget baru. Key saja belum cukup untuk membuat instalasi baru live: konfirmasi tier/akses, model, profil harga, token-bound dan reservasi sesuai keadaan akun.

## Kontrak adapter

- Fixed endpoint `https://api.groq.com/openai/v1/chat/completions`, bearer key, tanpa redirect/proxy environment.
- Dua model yang didukung: `openai/gpt-oss-120b` dan `openai/gpt-oss-20b`; model lain gagal konfigurasi sampai ditinjau.
- Strict JSON schema, non-streaming, 8192 input/4096 completion token, `reasoning_effort=low`, `include_reasoning=false`.
- Schema cloud memakai subset tanpa constraint batas panjang/rentang; validasi lokal tetap lengkap. Tidak mengirim tools/function/hosted search/code execution atau field routing OpenRouter.
- Byte-BPE/Harmony memakai batas konservatif byte UTF-8 +1024 framing pada kontrak existing; usage nyata ikut diperiksa. [Konfigurasi tokenizer resmi](https://huggingface.co/openai/gpt-oss-120b/blob/main/tokenizer_config.json), [encoding Harmony](https://github.com/openai/tiktoken/blob/main/tiktoken_ext/openai_public.py).
- Groq melaporkan usage token, bukan tagihan moneter per respons pada kontrak ini. **Reservasi tetap COST_UNKNOWN; harga Free Plan tidak diubah menjadi bukti tagihan nol.**

Dasar: [strict outputs dan model](https://console.groq.com/docs/structured-outputs), [reasoning controls](https://console.groq.com/docs/reasoning), [API compatibility](https://console.groq.com/docs/openai). Limit aktual akun mengacu [Groq Console Limits](https://console.groq.com/settings/limits). Ringkasan publik saat pemeriksaan:30RPM/1000RPD/8000TPM/200000TPD pada model GPT-OSS; input/output/reasoning dan attempt gagal dapat mengurangi kuota. Bukan jaminan40 slot A/B pasti cukup dalam sehari.

## Hasil14 November

- Metadata key/model HTTP200, GPT-OSS120B aktif, context metadata131072. Tidak ada generasi saat pemeriksaan metadata.
- Uji terarah:85 kasus unik, hasil terakhir seluruhnya lulus. Failure awal memakai field/status fixture evaluator yang salah; fixture diperbaiki dan dua tes relevan lulus, failure awal tetap disimpan. Termasuk Groq→draf tiga subtype, dua kondisi BAC→worker ASGI/verifier→review/publikasi dan pemisahan ledger.
- App dibangun/diperbarui pada volume existing setelah backup dan nol pekerjaan aktif. Docker Desktop sebelumnya mati dan dinyalakan; worker/lab/manual tidak diganti saat update provider.
- **Satu smoke live sukses**, requested/resolved model `openai/gpt-oss-120b`, inference endpoint Groq, finish_reason stop. Usage **1225 input/302 output token**, target requests0.
- Ledger **59→60**; seluruh59 baris lama identik. Baris baru menahan reservasiRp100, `COST_UNKNOWN`, actual_idr null. Total budget tidak dinaikkan.
- Run/action/handoff/evidence/assessment/report/revisi/scope/program/target/membership/user/evaluation tetap identik. Perubahan tabel percakapan/sesi/triage/ledger/audit merupakan dampak smoke normal.

Bukti privat: `artifacts/groq-20261114/`. Isi laporan/secret/response mentah tidak disalin ke dokumen ini. Belum menjalankan GT manual, freeze, eksperimen40 slot atau reset lab. Langkah berikutnya [review manual terakhir](manual-final-review.md).

Untuk uji koneksi berikutnya yang mempunyai alasan konkret:

```powershell
.\.venv\Scripts\python.exe -m scripts.smoke_text_provider --execute --provider groq
```

Tidak perlu mengulang smoke yang sudah sukses hanya untuk menampilkan status. Live proof ini terikat satu attempt; readiness `CONFIGURED_NOT_VERIFIED` adalah pemeriksaan konfigurasi, bukan penghapus bukti sukses pada riwayat triage.
