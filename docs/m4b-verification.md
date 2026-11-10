# Hasil M4b lokal - 5 November 2026

**Status terbaru:** M4 selesai teknis lokal setelah M4c melengkapi tujuh titik XSS/kontrol; [hasil M4c](m4c-verification.md). Catatan M4b di bawah adalah riwayat batch; cakupan workflow/UI tetap XSS-08 development.

**Checkpoint M4b selesai teknis lokal.** M4b menghubungkan satu klaim XSS pratinjau notifikasi ke workflow, browser worker, verifier bukti tersimpan, assessment, UI serta review/publikasi/ekspor. **M4 masih sebagian**: tujuh titik XSS lain belum dibuat. Planner tetap mock, bukan model AI live; payload/script laporan tidak dijalankan. GT manusia, dataset utama dan benchmark belum tersedia.

## Kontrak yang tersedia

- Validator dipilih aplikasi dari kategori klaim tersimpan. XSS hanya menerima satu klaim GET `/notifications/preview`, dua akun requester dan tanpa path kontrol tambahan. Kontrol/fixture tidak dipilih dari teks laporan.
- Empat probe berurutan: inert-v1 lalu marker-v1 pada tiap akun. Nonce dibuat aplikasi tiap aksi. Total delapan request termasuk login, 20 operasi browser logis, satu panggilan mock dan biaya Rp0 dalam cap bersama yang sudah ada. Satu job/context aktif.
- Verifier memeriksa empat observasi RECEIVED dan ikatannya ke run/action/urutan, envelope/argumen/hash, scope/epoch, snapshot/boot, waktu capture, alias, nonce/fixture, provenance dan hash evidence. Kedua pasangan harus konsisten. Kontrol JavaScript, penyimpanan awal kosong, teks inert, marker frame utama/origin dan PNG/hash diperlukan.
- CONFIRMED berarti fixture marker dieksekusi pada pratinjau di kedua akun dengan kontrol inert berhasil. REFUTED berarti fixture tampil sebagai teks tanpa marker dengan kontrol lengkap. Bukti kurang/hasil campuran menjadi INCONCLUSIVE; timeout/error menghentikan run tanpa refutation.
- Verdict terbatas pada fixture/rute/snapshot ini. Payload lain, persistensi, eksfiltrasi dan klaim tambahan belum diuji. Tidak membaca label evaluator atau database lab untuk menetapkan verdict.
- Bukti DOM/event/PNG tetap INTERNAL khusus admin, ditampilkan sebagai JSON inert. Hunter hanya mendapat teks tetap milik aplikasi setelah review/publikasi. Ringkasan tidak menyalin nonce, alias, path, DOM/PNG, model output atau catatan analis. Override analis terpisah dari raw; review ulang menarik publikasi lama.
- UI menyediakan pemilih BAC/XSS, mengunci rute XSS dan menyembunyikan kontrol objek BAC. Mode NONE tetap simulasi nol request. Register capability/scope dan reset target tetap operasi operator eksplisit, bukan startup/migrasi otomatis.

## Pemeriksaan aktual

| Pemeriksaan | Hasil |
| --- | --- |
| Suite host terisolasi | 156 passed in 150.04s; tanpa transport HTTP eksternal/provider live |
| Hardening terakhir | 31 passed in 32.14s, termasuk timestamp/scope/verifier XSS dan kontrak browser |
| API produk, kondisi rentan | CONFIRMED, empat evidence, delapan request/20 operasi browser, review/publikasi/ekspor dan idempotency lulus |
| API produk, kondisi perbaikan | REFUTED dengan kontrol teks inert/JS dan text sink; jumlah evidence/request sama |
| Bukti rusak/akses | Kasus salah run/boot/snapshot/akun/urutan/waktu, argumen/provenance/hash/nonce palsu dan bukti hilang tidak mendukung verdict. Hunter ditolak pada bukti mentah/ekspor pemilik lain |
| Penghentian | Unit cancel/scope/membership menyimpan bukti sebelumnya dan mencegah akun berikutnya. Timeout tidak menghasilkan REFUTED |
| Cancel produk aktual setelah perbaikan | PASS, run `94d95dc8-409b-454f-aa4a-fee33a7be4a8`; log tepat satu login dan satu dokumen, tanpa request lanjutan/favicon, assessment null, nol evidence karena aksi pertama dibatalkan, dirty gate dan nol Chromium |
| Regresi jaringan worker akhir | PASS, run `fb662ea4-6b5e-4b20-80a8-2213b01a7477`; lima request, satu WebSocket, satu popup dan satu download diblokir; empat request aktual hanya login/preview, context baru, nol Chromium tersisa |
| QA UI host | PASS, run `e7456b6e-793f-440e-be96-c9a7dd9a5e8b`; pemilih kemampuan/rute, bukti inert, review/publikasi/ekspor serta lima viewport diperiksa, nol page error/request eksternal |

Tes host memakai browser transport simulasi untuk kontrak/workflow; bukti eksekusi Chromium berasal dari smoke Docker aktual. Paket Python/browser/seccomp tidak berubah dari [inventaris M4a](dependencies-m4.json); source cleanup worker berubah pada batch ini. Model live tidak dipanggil dan kuota start produk tidak dihapus/diubah.

Pemeriksaan penutup: 29 Markdown/215 link lokal dan fence lulus, sintaks Python/JavaScript dan `git diff --check` lulus. `artifacts/m4b/final-state.json` mencatat image worker akhir, lab fixed/fixed, target ready/bersih, nol job aktif/Chromium/error callback, serta nol request lab sejak reset akhir. Readiness worker IDLE, lab OPERATOR_VERIFIED dan provider CONFIGURATION_REQUIRED. Screenshot hunter desktop/mobile dan admin tersimpan privat; mobile ditinjau visual. Semua perubahan tetap lokal, tanpa commit/push/deployment.

## Bug cancel yang ditemukan dan diperbaiki

Smoke API pertama meluluskan kedua kondisi, lalu **gagal** pada hitungan request cancel. Log aktual menunjukkan satu login, dua GET preview dan satu favicon, walaupun tidak ada proses browser tersisa. `unroute_all` sebelum context ditutup melepaskan navigasi yang tertahan ke jaringan Chromium, di luar pencatatan request tool. Ini bug cleanup, bukan bukti refutation atau kegagalan fixture XSS.

Worker kini mempertahankan routing sampai context tertutup, menolak callback baru selama closing, membatalkan handler yang menunggu, lalu menutup context/browser. Route yang dibatalkan juga di-abort, sehingga future internal Playwright selesai; tanpa ini log sempat menunjukkan pending task saat garbage collection. Regresi cancel produk dan probe network diulang pada worker baru. Tes cancel M4a sebelumnya belum menghitung log request aktual sesudah cleanup; hasil terbaru di atas memperbaiki celah pemeriksaan tersebut.

Artefak `artifacts/m4b/api-verification.json` dan salinan bertimestamp tetap berstatus FAILED untuk percobaan awal, dengan dua fase kondisi yang berhasil. `cancel-verification.json` menyimpan regresi yang lulus. QA UI pertama juga berstatus FAILED karena locator judul cocok dengan sidebar, heading dan bubble sekaligus; berhenti sebelum start run. Riwayat gagal tidak dihapus atau diganti menjadi PASS.

Percobaan UI berikutnya, run `59c525a4-bab8-4b49-979d-221d4a127076`, berakhir ACTION_OUTCOME_UNKNOWN setelah login/Chromium mulai dan sebelum request dokumen. Tidak ada restart/OOM/zombie pada pemeriksaan; akar penyebab timeout itu belum dibuktikan. Run/evidence tetap gagal tanpa assessment, bukan REFUTED. Worker akhir kemudian menyelesaikan run UI `e7456b6e-793f-440e-be96-c9a7dd9a5e8b` dengan delapan request/empat bukti. Pemeriksaan QA sempat berhenti karena asumsi teks `onerror` pada sink rentan; yang benar diperiksa adalah event marker. Form/pemilih/rute dan browser sudah lulus pada run itu, lalu review/publikasi/ekspor dilanjutkan pada **run yang sama**, tanpa request target/start baru. Artefak setiap percobaan bertimestamp tetap disimpan; hasil QA akhir menandai resumed_existing_run.

## Menjalankan ulang

```powershell
.\.venv\Scripts\python.exe -m evaluator.m4b
# Hanya kasus terkait, agar tidak mengulang run/kuota tanpa alasan:
.\.venv\Scripts\python.exe -m evaluator.m4b --cancel-only
# Bila kuota akun hunter telah terpakai, admin juga tunduk pada kuotanya sendiri:
.\.venv\Scripts\python.exe -m evaluator.m4b --cancel-only --cancel-account admin
.\.venv\Scripts\python.exe -m evaluator.m4 --network-only
$env:VALVULN_PLAYWRIGHT_CORE='D:/ProjectWeb/webBisnisPadang/node_modules/playwright-core'
node scripts/m4b_ui_smoke.cjs
# Opsional: lanjutkan hanya review/publikasi/ekspor run UI yang sudah selesai.
# Set VALVULN_SMOKE_HUNTER dan VALVULN_SMOKE_RESUME_RUN sesuai pemilik/run tersebut.
```

Evaluator/QA mereset hanya lab sintetis dan meninggalkan riwayat aplikasi/evidence/ledger. Perlu akun demo lokal yang sudah di-seed dan `.local-data/demo-password.txt`; file password tidak boleh dibagikan. Runner API penuh membutuhkan dua start hunter-a dan satu akun cancel (default hunter-b) dalam kuota yang berlaku. Runner UI menambah satu run hunter-b, atau hunter-a jika VALVULN_SMOKE_HUNTER diatur. Mode resume memakai run selesai tanpa start/request target baru. Jalankan bergantian, tanpa run lain. Artefak privat ada di `artifacts/m4b/`, regresi jaringan di `artifacts/m4/network-verification.json`, dan capture mentah pada volume app; semuanya dikecualikan Git.

Checkpoint berikutnya: tujuh titik XSS lain secara bertahap dengan kontrol per titik. Target tetap 24 titik (dua development direproduksi, 22 lain pending), 20 laporan dengan GT manusia, dan model live hanya setelah akses/budget siap. Tidak push, deploy, membuat rilis atau menjalankan benchmark pada batch ini.
