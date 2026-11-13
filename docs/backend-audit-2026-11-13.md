# Audit backend, akses lab dan OpenRouter — 13 November 2026

Lingkup: lima permintaan pengguna, yaitu kesesuaian orkestrasi, pembukaan lab Docker untuk manual, daftar celah yang diterapkan, kesiapan OpenRouter dengan key lokal, dan flowchart backend untuk handoff FE. Source/konfigurasi lokal dan runtime dibaca ulang; catatan 7 November bukan dianggap status live hari ini.

## Hasil utama

1. **Orkestrasi:** sesuai scope triage teks + pemeriksaan fixture yang dipersempit, belum agent adaptif. Model memberi saran; claim/run/plan lab terpisah dan planner masih deterministik/mock. [Flowchart dan kontrak BE](backend-flow.md).
2. **Lab:** Docker Desktop berhasil dijangkau. Salinan manual berjalan di **http://127.0.0.1:8001/**; source DB asli hanya dibaca dan hash sebelum/sesudah sama. [Login, route dan operasi](manual-lab.md).
3. **Kerentanan:** 13 kondisi yang sudah ada diaktifkan pada salinan manual: BAC-08, XSS-01..08, UP-01..04. BAC-01..07/BL-01..04 tetap ditunda. Ini bukan 13 reproduksi baru atau GT dataset yang sudah diterima.
4. **OpenRouter:** key lolos metadata HTTP200; model `nvidia/nemotron-3.5-lightning:free` tersedia dan harga prompt/completion pada metadata nol. Tetapi satu triage nyata melalui API/ledger gagal TRANSPORT_TIMEOUT sekitar30,69detik. **LIVE_VERIFIED=false**.
5. **Handoff FE:** [api/openapi.json](api/openapi.json) dihasilkan dari source:35 path/37 operasi. [backend-flow.md](backend-flow.md) menjelaskan auth/role, scope, triage, queue/worker/verifier, review/publikasi dan batas same-origin.

## OpenRouter: arti hasil pemeriksaan

- Key dibaca dari konfigurasi privat dan tidak dicetak. `GET /api/v1/key` berhasil; angka limit pada metadata key tidak dianggap saldo/token gratis proyek.
- Metadata model/provider saat pemeriksaan: model tersedia, provider Nvidia, harga prompt/completion0. Endpoint tidak mencantumkan dukungan `structured_outputs` atau `response_format`.
- Dokumentasi primer OpenRouter menyatakan dukungan schema ditentukan per endpoint dan menyarankan `require_parameters=true`: [Structured Outputs](https://openrouter.ai/docs/guides/features/structured-outputs). Source lokal saat audit memakai false; ini ketidaksesuaian yang perlu dibereskan sebelum freeze.
- Request smoke hanya satu, retry mati, input sintetis tanpa tools dan tanpa request target. Akun hunter-a menggunakan API login/intake yang sebenarnya pada ASGI app; adapter melakukan HTTP nyata. Database memakai volume aplikasi asli `kartikahackathon_app_data`, bukan ledger baru atau preview untuk melewati budget.
- Sebelum smoke, database aplikasi di-backup secara konsisten ke `.local-data/backups/backend-audit-20261113/valvuln-before-smoke.sqlite3`. Tidak ada migrasi baru karena schema006 sesuai source dan tidak ada run/triage aktif.
- Setelah smoke,39 run,125 action,115 evidence dan15 assessment tetap sama. Baris ledger lama tetap sama;58 menjadi59 dan attempt24 menjadi25 karena satu smoke yang baru.
- Attempt gagal memegang reservasi **Rp100, COST_UNKNOWN, actual_idr=null**. Ini reservasi konservatif, bukan bukti tagihan Rp100 atau biaya nol. Tidak direkonsiliasi otomatis hanya berdasarkan tarif nol.
- GET metadata publik dari jaringan container yang sama berhasil HTTP200, sehingga konektivitas dasar tersedia. Timeout generasi tidak membuktikan refusal atau kualitas model; penyebab respons lambat belum dipastikan.
- Tidak mengulang inferensi, berpindah model berbayar, membeli kredit atau menjalankan benchmark untuk mencari hasil sukses. Profil output/schema belum layak dianggap tervalidasi.

Probe API ber-ledger berada di [scripts/smoke_openrouter_audited.py](../scripts/smoke_openrouter_audited.py); script mengharuskan database/ledger existing, preflight free-profile, schema yang sesuai dan tanpa pekerjaan aktif. Script smoke langsung `scripts/smoke_openrouter_live.py` yang sudah ada dibaca tetapi tidak dipakai karena melewati ledger, mencetak respons mentah dan menampilkan biaya unknown sebagai0.

## Pemeriksaan dan hasil yang benar-benar diamati

| Pemeriksaan | Hasil |
| --- | --- |
| Unit/integrasi akses manual | **7 passed** final dalam1,48detik; ASGI/database sementara, tanpa provider nyata |
| Route manual normal | Home/health/login/ID objek/pencarian/notifikasi/pemasok HTTP200; Origin asing ditolak |
| Isolasi manual | Uvicorn UID10001, CapEff/CapPrm/CapBnd0, koneksi keluar baru ditolak; port hanya127.0.0.1 |
| Kontrak OpenRouter existing | **1 failed** dalam1,34detik: tes mengharapkan max_tokens1024, body aktual4096. Assertion berikutnya juga meminta require_parameters=true sedangkan source false; bagian itu diketahui dari static read, bukan failure kedua yang dijalankan |
| Metadata provider | Key/model/endpoints HTTP200; tidak melakukan inferensi saat metadata |
| Smoke generasi nyata | Satu attempt, TRANSPORT_TIMEOUT, COST_UNKNOWN; tidak ada job/aksi target |
| OpenAPI | Snapshot35 path/37 operasi, tanpa lifespan/DB/provider |

Artefak tersimpan privat pada `artifacts/backend-audit-20261113/`, termasuk preflight metadata, backup metadata, smoke, pemeriksaan jaringan container, hasil JUnit dan runtime manual. Data secret/GT tidak disalin ke dokumen. Tes kontrak gagal dan percobaan awal manual tidak dihapus/disamarkan sebagai kelulusan.

## Perubahan pada batch ini

- Menambah Compose manual, helper salinan DB tanpa overwrite, origin manual opt-in dan halaman bantuan operator dengan ID objek milik akun sendiri.
- Menambah firewall mode manual pada bootstrap; service app/worker/lab asli tidak dibangun ulang atau diaktifkan. Proses manual mempunyai network/volume terpisah.
- Menambah probe smoke API ber-ledger serta snapshot OpenAPI dan tiga dokumen audit/handoff.
- Tidak mengubah key, profil model privat, cap output pilihan pengguna, konfigurasi routing existing, katalog/grup/GT, manifest lama, tag rilis atau publikasi.

Salinan manual bukan target agent baru. Pemeriksaan asli tetap membutuhkan readiness/snapshot/binding worker. FE teman pengguna dapat mulai dari kontrak API; tindak lanjut backend paling mendesak adalah konsistensi cap/schema/routing dan satu smoke ulang hanya setelah perubahan profil yang beralasan serta review biaya unknown.
