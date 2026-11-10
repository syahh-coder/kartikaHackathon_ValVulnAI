# Mencoba kandidat paket lokal

Status aktual dan arsip/checksum: [final-review.md](final-review.md). Paket adalah source kandidat review, bukan release publik atau image prebuilt. Model live dan benchmark belum diverifikasi. Python baseline 3.11; Docker Linux containers dan Compose diperlukan untuk topologi produk. Unduhan awal image/dependensi memerlukan internet; paket tidak sepenuhnya offline.

## Setup baru, terpisah dari data yang sudah ada

Untuk **preview triage MOCK saja**, gunakan Compose tersendiri tanpa lab/worker/key dan volume preview baru. Perintah dasar ini khusus MOCK. Pengaktifan Azure pada preview harus memakai overlay dan ledger yang sama sesuai panduan Azure di bawah; jangan membuat volume lain untuk menambah budget:

```powershell
docker compose -p valvuln-review -f compose.preview.yaml up -d --build
docker compose -p valvuln-review -f compose.preview.yaml exec app python -m app.operator
# Buka http://127.0.0.1:8010, login dengan akun/password sintetis hasil seed.
docker compose -p valvuln-review -f compose.preview.yaml stop
```

Tidak perlu menyiapkan scope/target untuk mengirim teks dan meminta saran MOCK. Bukti lab tidak tersedia pada preview; screenshot evidence dalam materi berasal dari rekaman sintetis QA terpisah. Preview tidak memasang volume aplikasi aktif dan tidak membaca `.env` provider. Compose preview diuji build/start pada project/volume baru, health/readiness di port8010 dan cleanup; ID container/data aktif tetap sama. Bukti di `artifacts/r4/preview-check.json`. Startup/restart juga diuji melalui container network-none dan ekstraksi source HTTP.

Ekstrak ZIP source ke folder baru. Jangan gunakan nama project Compose atau subnet yang bertabrakan dengan instalasi lain yang sedang berjalan. Config default memakai subnet lab tetap; dua stack lab default tidak bisa dijalankan bersamaan tanpa penyesuaian operator. Pemeriksaan batch ini menjalankan app terpisah dengan jaringan `none`; tidak menyalakan ulang lab aktif.

```powershell
Copy-Item .env.example .env  # setup pertama; jangan overwrite konfigurasi yang sudah ada
py -3.11 scripts/setup_local.py
docker compose up -d --build
docker compose exec app python -m app.operator
```

Seed meminta password lokal 12–128 karakter untuk akun sintetis `hunter-a`, `hunter-b`, `admin`. Tidak mengubah password akun yang sudah ada, mengaktifkan scope atau mereset data. Buka http://127.0.0.1:8000. Setelah setup/seed, startup normal `docker compose up -d --build`. `docker compose stop` mempertahankan volume; jangan memakai `down -v` untuk berhenti normal.

Login hunter, pilih program, buat laporan teks biasa dan tekan Kirim. **Minta saran AI** adalah tindakan eksplisit terpisah. Default **MOCK** mengembalikan respons tetap berlabel; bukan model nyata. Mengirim teks, refresh status, startup dan restart tidak memicu model/target otomatis. Scope admin dan prasyarat lab tetap harus dipenuhi untuk fitur pemeriksaan produk yang sudah ada. Jangan mengaktifkan validasi target hanya untuk melihat triage.

Provider teks dapat dipilih eksplisit OpenRouter atau Azure Foundry; keduanya sudah diuji dengan respons simulasi. Pengguna memilih Azure Students: isi `.env.azure` privat dan ikuti [setup Azure pada web8010](azure-setup.md), menggunakan project/volume/ledger preview yang sama. Jangan membuat ledger baru atau memakai evaluator instalasi8000 untuk memisahkan budget. OpenRouter tetap memakai `.env` sesuai [runbook](r3-runbook.md). Key hanya untuk app/evaluator. Konfigurasi live tidak sah gagal jelas tanpa fallback. Gemini direct/OpenAI direct/Grok direct/OAuth/replay belum menjadi adapter produk; kontrak Azure v1 terbatas seperti panduan. Belum ada verifikasi live.

## Yang diperiksa pada paket review

- Tes projection/dispatch menggunakan HTTP simulasi dan database sementara; tidak membuktikan respons model nyata.
- Image app/evaluator review dibangun terpisah. App baru dengan jaringan none/volume disposable diuji health, seed dan restart; data/ledger/service aktif dibandingkan sebelum/sesudah.
- Arsip diekstrak ke folder baru dan diperiksa checksum, import source, startup HTTP, login/draft/restart tanpa provider/target. Interpreter/dependensi host yang sudah terpasang dipakai; ini tidak membuktikan instalasi dependensi dari nol pada laptop juri.
- Full cold build ketiga service dari cache kosong belum diverifikasi pada paket terbaru. Worker/lab source dan pin dipertahankan; tidak dibuat ulang atau dijalankan demi pengemasan ini.

## Jika ada kendala

`CONFIGURATION_REQUIRED`: mode live belum memiliki profil lengkap; lihat field konkret runbook. Jangan mengganti live menjadi mock diam-diam. `APPLICATION_SCHEMA_006_REQUIRED`: service aktif masih source lama; lakukan update app dan backup sesuai prosedur operator saat siap, bukan membuat ledger baru. `CONTEXT_LIMIT`: input terlalu besar bagi cap; revisi report/prompt sebelum freeze, jangan memotong hasil diam-diam. `SLOT_ALREADY_DISPATCHED`: hasil sudah dicatat; ekspor, jangan replay. `EVALUATION_ACTIVE_OR_INTERRUPTED`: tunggu proses berjalan atau gunakan pemulihan eksplisit sesuai runbook.

Jika daemon Docker tidak terjangkau, periksa Docker Desktop Linux containers/context. Jika subnet/port bentrok, jangan menghentikan stack pengguna lain secara otomatis. Build memerlukan registry/Python index yang bisa diakses dan versi lock yang tersedia; gunakan output aktual untuk diagnosis. Lisensi proyek belum dipilih pengguna; kandidat lokal tidak memberikan lisensi baru atas source/dependensi. Jangan mendistribusikan image/binary sebelum notice/source obligation ditinjau.
