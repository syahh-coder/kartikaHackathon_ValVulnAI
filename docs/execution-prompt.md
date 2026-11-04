# Handoff eksekusi ke chat baru

Disiapkan dan diperbarui 4 November 2026. Pengguna telah menyatakan **UI fix sebagai baseline untuk mulai backend**, dengan kemungkinan perbaikan berikutnya. Gate UI terpenuhi dan prompt siap menjalankan M1 di chat baru tanpa meminta persetujuan UI ulang. Ini bukan bukti backend sudah dimulai atau keamanan runtime telah diuji; periksa file terbaru saat handoff.

## Temuan audit sebelum handoff

- Struktur dokumen cukup untuk memulai fondasi lokal secara bertahap. Keamanan runtime belum terbukti; acceptance criteria backend tetap BELUM DIUJI.
- Docker CLI 29.7.2 dan Compose v5.3.1 terdeteksi, tetapi koneksi named pipe docker_engine gagal pada sesi audit. Python 3.11.9 dan Git 2.55.0.windows.2 terdeteksi. Cek ulang saat eksekusi; jangan menganggap kondisi ini permanen atau memperbaikinya dengan reset/reinstalasi destruktif.
- Source aplikasi/Compose/dependensi produk belum tersedia. UI hanya prototipe statis yang sudah menjalani QA terbatas; bukan auth/LLM/target nyata. Tidak ada dataset berlabel, hasil model atau hibah Azure yang dianggap aktif.
- Target startup satu perintah sudah ditulis sebagai kriteria, dengan setup/seed terpisah, persistensi data dan tanpa inference/reset otomatis.
- Scope tetap 20 laporan 10/10 dan 24 titik lab; target 24 titik masih menjadi beban waktu. Jangan memperkecilnya diam-diam atau membuat label/bukti final sebelum lab siap.

## Prompt siap salin

Prasyarat UI sudah dipenuhi oleh jawaban pengguna pada 4 November 2026. Perbaikan UI yang menyusul tidak menghalangi M1 dan tidak mengubah fitur simulasi menjadi backend nyata. Ruang lingkup prompt ini tetap implementasi M1 lokal; cloud, publikasi dan model live belum diotorisasi untuk tahap ini.

```text
Kita melanjutkan ValVuln AI di workspace D:\BelajarCyberSec\kartikaHackathon.
Baca dan ikuti AGENTS.md terbaru. Pengguna sudah menyatakan UI fix sebagai baseline untuk mulai backend pada 4 November 2026; perbaikan UI nanti tetap boleh. Ini instruksi mengerjakan M1 lokal di chat baru; jangan mengandalkan ingatan chat lain.

Awali dengan prd.md, README.md, docs/implementation.md, docs/architecture.md, docs/runtime.md, docs/security-review.md, docs/ui-review.md dan docs/execution-prompt.md. Baca plan.md/user-flow/evaluation sesuai dependensi pekerjaan. Periksa kondisi filesystem dan lingkungan terbaru, lalu kerjakan; tidak perlu mengulang seluruh riset/provider atau menambah dokumen perencanaan tanpa masalah konkret.

Gate UI sudah terpenuhi dan dicatat pada AGENTS.md/ui-review.md. Jangan meminta konfirmasi UI lagi atau menunda fondasi sampai semua kemungkinan polish visual selesai. Pertahankan baseline UI; lakukan perbaikan relevan ketika integrasi nanti membutuhkan, dengan pemeriksaan sesuai perubahan.

Mulai dan selesaikan M1 dalam sub-batch yang diperiksa berurutan:
1. Bootstrap Python 3.11/FastAPI/Uvicorn/Pydantic, konfigurasi tervalidasi dan contoh env tanpa secret, SQLite via aiosqlite, migrasi SQL dan Compose untuk app nyata.
2. Seed operator dua bug hunter dan satu admin, session/membership/ownership server-side, program/scope terversi, draft/report/revisi dan kontrak run/action/evidence/assessment. Pertahankan desain UI yang disetujui; integrasi UI backend lengkap mengikuti M3.
3. Policy tanpa akses target, state/queue/idempotency/ledger, adapter mock berlabel, kontrak provider/error dan pemeriksaan M1 yang relevan.

Target MVP lengkap tiga container app/worker/lab, dua SQLite terpisah dan empat named volume. M1 tidak membuat worker/lab dummy, tidak memulai portal rentan/Playwright atau menulis seluruh aplikasi sekaligus. Setelah setup/config/seed, target operasi normal adalah docker compose up -d --build; sekarang belum tersedia. Startup/restart tidak mereset data/ledger, mengaktifkan scope atau memanggil model/target otomatis. Evaluator dan reset adalah operasi operator terpisah.

Cek Docker daemon/context/plugin secara read-only. Pada audit sebelumnya CLI tersedia tetapi daemon belum terhubung. Bila masih gagal, lanjutkan kode dan pemeriksaan independen yang bisa dijalankan tanpa Docker; catat build/runtime belum terverifikasi. Jangan reset Docker, menghapus volume atau mengubah konfigurasi host hanya untuk meluluskan tes. Siapkan dependency lokal proyek bila diperlukan dan dapat dilakukan; jangan ubah environment sistem tanpa kebutuhan.

Gunakan target milik sendiri, akun/data sintetis, satu job aktif, TXT/MD sesuai batas, dan semua enforcement pada backend. OOS/UNKNOWN/unsupported tidak membuat job atau request target. Worker kelak tidak mendapat key model, GT/source jawaban, evaluator reset atau Docker socket; tools terstruktur, tanpa shell/eval/script bebas dari report. CONFIRMED memerlukan dampak/bukti; error/refusal bukan REFUTED.

M1 memakai mock dan respons simulasi untuk pengujian kontrak. Jangan membeli kredit, memanggil API live, mengaktifkan Azure/PAYG, deploy cloud, push/publish repo, atau memasang skill pentest yang belum dipilih. OpenRouter awal, Gemini cadangan, OpenAI/xAI opsional, Azure Students kandidat pending; Plus/Codex bukan key API generik. Batas biaya pribadi tetap Rp50.000 dan kuota/grant tidak diasumsikan aktif. Benchmark kelak memakai model/provider beku tanpa fallback.

Dataset tetap 20 teks berbeda (10 valid/10 tidak valid; 8 BAC, 8 XSS, 2 upload, 2 business logic), disusun setelah lab aktual siap dan GT manual diverifikasi. Lab tetap rancangan 24 titik dengan jawaban evaluator terpisah. Jangan membuat laporan final, angka metrik atau bukti sintetis seolah sudah diuji pada M1.

Kerjakan sendiri tanpa sub-agent. Jangan berhenti pada rencana atau meminta konfirmasi tiap file/checkpoint yang sudah diotorisasi. Uji kasus batas dan kontrol yang relevan pada setiap potongan, perbaiki kegagalan, pertahankan perubahan pengguna, lalu perbarui status M1 dan README dengan hasil aktual. Jangan menandai tahap selesai karena mock/source sudah ada jika pemeriksaan wajib belum dapat dijalankan.

Untuk turn pertama ini, ruang lingkup implementasi adalah M1. Akhiri dengan file/perilaku yang berubah, pemeriksaan dan hasil nyata, bagian yang belum terverifikasi, hambatan lingkungan serta checkpoint berikutnya. Jangan langsung lompat ke M2 atau seluruh M1-M10 dalam satu batch.
```

## Setelah M1

Chat berikutnya dapat membaca hasil M1 dan melanjutkan checkpoint yang benar. Perubahan source/status/dokumen wajib menjadi sumber handoff berikutnya; prompt ini tidak membekukan kondisi repo selamanya. Persetujuan baseline UI tetap berlaku sampai pengguna memberikan perubahan arahan, dan tidak membatalkan acceptance criteria backend/worker/model.
