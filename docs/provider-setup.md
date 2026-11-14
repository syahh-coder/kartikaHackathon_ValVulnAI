# Provider AI: Groq, OpenRouter dan Azure Foundry

**Keputusan aktif14 November2026: Groq utama**, OpenRouter lalu Azure Foundry sebagai cadangan yang dipilih eksplisit; tanpa fallback otomatis. [Groq setup dan satu smoke live sukses](groq-setup.md). Adapter tersedia pada intake/evaluator teks; hasil sukses satu model bukan jaminan semua model/deployment kompatibel. AgentRouter tetap kode legacy opsional, bukan prioritas submission. Petunjuk OpenRouter/Azure di bawah tetap berlaku untuk pemilihan provider tersebut.

## 1. Kontrak bersama

- Mode model teks terpisah dari planner lab. Planner tetap deterministik/mock, worker tidak mendapat key model.
- Satu provider/model dipilih eksplisit; tidak ada fallback otomatis, perpindahan berbayar, provisioning cloud atau reset ledger.
- Batas8192 input/4096 output token, temperature0, non-streaming dan strict JSON schema. Respons divalidasi lagi di aplikasi. Tidak semua model reasoning mendukung kontrak ini.
- Profil akses/tokenizer/harga/kurs diverifikasi operator. Reservasi mencakup cap maksimum dan total budget tetapRp50.000. Reservasi unknown bukan biaya nol atau tagihan aktual.
- Mengisi key tidak otomatis menjalankan inferensi. Jangan mengirim key melalui chat atau menyimpannya di source.

Dasar API: [OpenRouter Structured Outputs](https://openrouter.ai/docs/guides/features/structured-outputs) menjelaskan `response_format=json_schema` serta pemilihan endpoint kompatibel; aplikasi memakai `require_parameters=true`. [Microsoft structured outputs](https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/structured-outputs?view=foundry-classic) mendokumentasikan schema pada Chat Completions dan endpoint resource OpenAI v1. Kontrak source dibatasi ke deployment chat yang diverifikasi, bukan seluruh model Foundry.

## 2. OpenRouter — cadangan

1. Untuk setup pertama salin `.env.example` ke `.env` jika file belum ada. Konfigurasi yang sudah ada tidak ditimpa.
2. Isi `VALVULN_TRIAGE_MODE=live`, `VALVULN_TRIAGE_PROVIDER=openrouter`, key lokal, exact model ID, inference provider slug/name, akses/tier, tarif/kurs dan reservasi.
3. Pilih pasangan model+endpoint yang benar-benar mendukung `response_format`/structured outputs. Metadata model tersedia tidak berarti endpoint mendukung schema. Profil gratis sebelumnya yang timeout belum dianggap lolos; jangan mengulang model itu tanpa perbaikan yang beralasan.
4. Verifikasi batas tokenizer byte-BPE sebelum menyetel flag token-bound. Jika metadata belum cukup, biarkan konfigurasi belum terverifikasi.
5. Jalankan checker **tanpa jaringan**:

```powershell
.\.venv\Scripts\python.exe -m scripts.check_text_provider_config --provider openrouter --env-file .env
```

`CONFIGURED_NOT_VERIFIED` hanya berarti field dan kontrak lokal lengkap. Jika harga metadata nol, biaya respons tetap harus dibaca dari bukti respons/ledger; jangan melepaskan reservasi historis unknown hanya berdasarkan harga nol.

Setelah konfigurasi diubah, terapkan ke app pada project yang sama, ketika tidak ada run/triage aktif:

```powershell
docker compose up -d --no-deps app
```

## 3. Azure Foundry — cadangan berikutnya

1. Isi `.env.azure` berdasarkan `.env.azure.example` jika belum dibuat. Panduan akun/deployment: [Azure setup](azure-setup.md), [Students](azure-students.md).
2. Gunakan resource origin seperti `https://NAMA.openai.azure.com`, bukan project endpoint. Adapter menuju `/openai/v1/chat/completions` dengan `api-key` dan deployment name pada `model`.
3. Isi identitas model hasil yang diharapkan, key/resource/deployment, kompatibilitas strict schema, akses kredit/kuota, tarif/kurs dan reservasi. Deployment reasoning atau fitur lain yang belum diverifikasi tidak otomatis didukung.
4. Jalankan checker lokal:

```powershell
.\.venv\Scripts\python.exe -m scripts.check_text_provider_config --provider azure --env-file .env.azure
```

Ketika siap, ganti **app utama yang sama**, bukan project/volume baru:

```powershell
docker compose -f compose.yaml -f compose.provider.azure.yaml up -d --no-deps app
```

Overlay ini tidak mengubah worker/lab atau volume `app_data`. Pastikan project Compose tetap `kartikahackathon` pada instalasi existing. Overlay lama `compose.azure.yaml` khusus preview8010; jangan memakainya sebagai pengganti overlay utama ini. Kembali ke OpenRouter memakai `.env` OpenRouter dan perintah Compose dasar pada bagian2.

Azure tidak melaporkan tagihan moneter aktual per respons pada adapter ini. Respons berhasil tetap memegang reservasi `COST_UNKNOWN`. Bukti kredit/biaya dan rekonsiliasi perlu review operator; jangan membuat ledger baru untuk melewati gate freeze.

## 4. Smoke live terakhir, saat siap

Smoke memakai **API app yang sedang berjalan dan ledger aslinya**, tanpa menguji target. Cek profil/akses terlebih dahulu; ulang hanya setelah penyebab kegagalan ditangani. Script default tidak mengirim request:

```powershell
.\.venv\Scripts\python.exe -m scripts.smoke_text_provider
# Jalankan salah satu secara eksplisit ketika key/profil siap:
.\.venv\Scripts\python.exe -m scripts.smoke_text_provider --execute --provider groq
.\.venv\Scripts\python.exe -m scripts.smoke_text_provider --execute --provider openrouter
# Atau sesudah overlay Azure diterapkan:
.\.venv\Scripts\python.exe -m scripts.smoke_text_provider --execute --provider azure
```

Default membaca password demo dari `.local-data/demo-password.txt`. Jika password tidak disimpan di sana, gunakan `--password-file` dengan file privat yang berisi password akun demo yang sama. Jangan mencetak nilai password. Script tidak membuat akun/seed atau memutar password.

Hasil sukses membuktikan satu triage live, bukan kualitas model/benchmark atau validasi semua kerentanan. Script lama `smoke_openrouter_live.py` sekarang mengarah ke jalur aman ini; tidak lagi memanggil adapter langsung atau mengubah biaya unknown menjadi0. `smoke_openrouter_audited.py` dipertahankan sebagai reproduksi audit historis, bukan perintah operasi utama.

Setelah smoke dan review biaya, lanjut [review manual terakhir](manual-final-review.md), lalu evaluator sesuai [runbook](r3-runbook.md). Benchmark mengunci satu provider/model dan mematikan fallback.
