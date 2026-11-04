# Kontrak runtime lokal dan pemulihan

Status: rancangan untuk implementasi M1-M4, ditulis saat audit dokumentasi 3 November 2026. Belum ada Compose, service, database produk, worker atau pengujian jaringan yang dijalankan. Bukan petunjuk run yang sudah bekerja. Kontrak schema/izin/API tetap dimiliki [architecture.md](architecture.md); distribusi tanpa live web pada [distribution.md](distribution.md).

## 1. Topologi minimum

Packaging MVP diperjelas pada 4 November 2026: **tiga container yang berjalan terus**, bernama `app`, `worker` dan `lab`. UI disajikan app; Chromium berjalan di worker. Tidak ada container database, frontend atau evaluator tambahan. Pada pengembangan M1 hanya app yang diperlukan; tiga service adalah topologi MVP lengkap, bukan syarat menjalankan seluruhnya sebelum lab dibuat. Pilihan stack dan ringkasan volume dimiliki [prd.md](../prd.md).

| Komponen | Koneksi dan data | Larangan |
| --- | --- | --- |
| Aplikasi FastAPI + satu dispatcher | UI/API pada loopback host; SQLite, ledger dan evidence privat; akses provider model yang dikonfigurasi | Tidak bergabung ke jaringan target lab, tidak meneruskan endpoint jaringan bebas dari chat |
| Worker HTTP/browser | Hanya jaringan lab internal; inbox job read-only, outbox hasil terpisah dan akun uji yang diperlukan | Tidak menerima `.env` aplikasi, key model, SQLite, source/evaluator/GT, Docker socket atau internet umum |
| Portal lab | Jaringan internal yang sama dengan worker, data sintetis | Tanpa port publik/internet, source evaluator, atau mount job/evidence aplikasi |
| Operator/evaluator | Menyiapkan seed/kondisi, memeriksa health dan reset melalui jalur maintenance lokal terpisah | Bukan tool agent atau menu admin program |

Jalur app <-> worker dipilih **file JSON terstruktur pada dua volume handoff sempit**, bukan worker mengakses database/API utama. App menulis inbox dan membaca outbox; worker membaca inbox dan menulis outbox. Tidak membuat Redis, broker cloud atau Docker container target baru per report. App tidak mendapatkan akses target hanya untuk mengecek health saat intake.

Port default rancangan: app memublikasikan hanya `127.0.0.1:8000`, sedangkan lab melayani port internal `8001` tanpa port host; worker tanpa listener host. App mempunyai jaringan sendiri dengan akses provider, worker/lab hanya `lab_internal`. Tidak menyatukan semua service ke default network Compose. Port/DNS binding tetap konfigurasi operator dan diuji sebelum disebut bekerja.

Inbox/outbox hanya memuat job/action yang sedang diproses. Riwayat report/evidence final berada di storage app yang tidak dimount ke worker. Source proyek tidak di-bind-mount seluruhnya ke worker/target; image menyalin modul yang diperlukan saja. Fixture UI juga bukan context model. Akun target disediakan sebagai alias dengan material credential lokal terpisah, dibaca worker dan tidak disalin ke prompt/artefak.

Gunakan jaringan Compose internal serta batas egress aktual. `internal: true` adalah konfigurasi awal, bukan bukti bahwa host gateway, IPv6, DNS atau control plane telah tertutup. Policy tujuan tetap berlaku; buktikan konektivitas positif ke origin target dan penolakan tujuan lain pada NET-01/02/03. Jika batas jaringan tidak dapat dibuktikan pada host, jangan mengaktifkan worker lewat UI sampai isolasi diperbaiki. Dua service yang berbagi network tidak otomatis terisolasi satu sama lain.

## 2. Handoff dan kaitan action

Envelope minimum yang dibuat aplikasi:

```text
schema_version, run_id, action_id, action_seq
program_id, target_id, scope_version_id, authorization_epoch
tool_name, validated_arguments, account_alias
issued_at, expires_at, limits_remaining, envelope_hash
```

- Nama file/path dibuat aplikasi dari ID yang divalidasi. Argumen model tidak dapat memilih path, nama volume atau channel.
- Tulis melalui file sementara lalu rename atomik; pembaca hanya menerima dokumen lengkap yang lolos schema dan batas byte. Tolak symlink/path traversal, sequence lama serta envelope yang kedaluwarsa.
- App mempertahankan catatan immutable envelope/action pada SQLite di luar volume. Outbox wajib cocok dengan run/action/sequence yang outstanding; jangan mempercayai ID, path/hash atau verdict yang diklaim di body target.
- Worker mengembalikan observasi hasil eksekusi dan capture teredaksi. App memvalidasi jenis/ukuran artefak, membuat ID/provenance, lalu mengimpor ke storage privat; tidak menyajikan direktori outbox sebagai static web.
- Handoff diberi acknowledgment dan deduplikasi action ID. Jika worker kehilangan acknowledgment setelah aksi mutasi, hasilnya ambigu: jangan menjalankan ulang aksi secara otomatis. Catat `ACTION_OUTCOME_UNKNOWN` dan hentikan run untuk review/reset.
- Instruksi di JSON report, response HTML atau file upload tetap data. Tidak ada JSON yang diubah menjadi Python/shell/eval.

Gate scope membuat izin run; policy app memeriksa setiap action sebelum inbox ditulis dan worker memeriksa profil lokal/expiry/cancel sebelum I/O. Pembatalan/revokasi dikirim lewat control record inbox yang dibuat app. Browser dan request aktif ditutup saat record diterima; deadline lokal tetap menutupnya walau app mati. Tidak ada jaminan efek mutasi yang sudah terjadi bisa dibatalkan.

## 3. Antrean, lease dan crash

- SQLite hanya milik app. Buat job, uniqueness idempotency, pemeriksaan kuota dan reservasi budget dalam transaksi singkat; jangan menahan transaksi ketika menunggu model/browser. Gunakan akses database async atau jalur thread yang tepat agar busy wait tidak memblok event loop.
- Satu dispatcher dan satu run pengujian aktif; tidak meluncurkan banyak scheduler lewat setiap proses web. Startup menolak dispatcher ganda. Tidak memakai beberapa replica API yang masing-masing menganggap dirinya pemilik worker.
- `queue_status=QUEUED` dipasang setelah scope/prasyarat lolos; start lease atomik memeriksa scope/membership terkini, worker sehat, target siap serta budget. Deadline antrean awal lima menit; jika habis, FAILED dengan `QUEUE_EXPIRED` dan tanpa verdict teknis.
- Worker memberi heartbeat tiap dua detik lewat outbox. Lease dianggap hilang setelah sepuluh detik tanpa heartbeat. Nilai ini awal dan perlu diperiksa pada development.
- Timeout request sepuluh detik dan waktu aktif run 180 detik tetap berlaku; waktu aktif dihitung dari dimulainya pipeline model/scope, waktu antrean dicatat terpisah. Antrean bukan cara menambah jatah kerja aktif. Semua panggilan model pada run, termasuk ekstraksi/verifier/retry, masuk cap 12 panggilan.
- Cancel/scope berubah/revoke: hentikan dispatch dan model call baru, tutup request/browser aktif, simpan status/alasan serta artefak yang sudah ada. Pemanggilan provider yang telanjur terkirim mungkin tetap ditagihkan; cancel tidak menjanjikan pengembalian biaya.
- Crash/restart: tandai run LEASED yang kehilangan proses sebagai FAILED (`WORKER_LOST` atau `PROCESS_INTERRUPTED`). Jangan auto-resume atau auto-replay mutasi. Queued job diperiksa ulang sebelum lease berikutnya; run yang gagal hanya dapat diulang sebagai run baru.
- Target yang mungkin berubah setelah crash/cancel/timeout/mutasi diberi `TARGET_DIRTY`. Jangan menjalankan job lain pada target itu sebelum evaluator memastikan reset/health dan melepas tanda dirty. Tidak memberi tool reset kepada model agar antrean tampak berhasil.

Chat biasa menyimpan draft terlebih dahulu. Jika fitur balasan live diaktifkan, panggilannya memakai quota/ledger dan antrean model yang sama; tidak membuat loop target baru. Pada M1, balasan mock tetap berlabel dan tidak menghabiskan API.

## 4. Penyimpanan dan umur data

Dua database SQLite dipisah: `/data/valvuln.sqlite3` pada volume `app_data` hanya dibuka app, `/data/lab.sqlite3` pada `lab_data` hanya dibuka lab/maintenance operator. Pakai aiosqlite untuk akses async dan SQL berparameter, dengan migrasi SQL bernomor. Worker tidak membuka keduanya. Dua volume lain adalah `job_inbox` (app RW, worker RO) dan `job_outbox` (worker RW, app RO). File database tidak diletakkan pada volume handoff atau dibagikan antarservice.

- Volume app menyimpan schema version/migrasi, session/membership, draft/revisi, scope snapshot, run/action, ledger, assessment dan audit admin. Setiap foreign key harus mengikat program/report/run terkait; DTO ownership tidak diambil dari model.
- Aktifkan foreign key SQLite, migrasi terversi dan uniqueness yang dibutuhkan; pin strategi journal/busy timeout saat bootstrap dan uji concurrency yang relevan. Backup dilakukan ketika run berhenti dan storage konsisten, bukan menyalin database aktif secara sembarang.
- Restart mempertahankan draft/riwayat pada volume; ini berbeda dari prototipe UI yang masih hanya memori tab. UI mengambil ulang draft dari API setelah login. Tidak menjanjikan draft survive reload sebelum backend terpasang/diuji.
- Session demo: expiry awal delapan jam, logout/revoke berlaku server-side. Seed meminta password demo dari operator atau menghasilkan password lokal sementara; tidak membundel session aktif atau password akun asli.
- Pertahankan hasil eksperimen mentah dan ledger sampai scoring/submission selesai; tidak ada penghapusan otomatis berdasarkan verdict. Cache/handoff boleh dibersihkan setelah acknowledgment, impor evidence dan penutupan job. Jangan membersihkan run aktif atau menghapus kegagalan agar metrik tampak bagus.
- Reset target hanya mengubah state lab dan akun uji, bukan report, hasil, audit atau saldo budget. Reset penuh data aplikasi adalah operasi operator terpisah dengan backup dan target eksplisit; jangan menjadi tindakan startup atau endpoint chat.
- Akhiri/cleanup context dan storage browser pada pergantian akun/run. File aktif tidak diberikan ke dashboard sebagai HTML/SVG inline. Artifact path tidak berasal dari input pengguna.

## 5. Batas data dan disk awal

Nilai berikut adalah rancangan default, belum hasil kalibrasi. Pastikan satuan byte dan karakter tidak dicampur; batas yang paling ketat berlaku.

| Resource | Batas awal | Saat batas tercapai |
| --- | ---: | --- |
| Lampiran report/guideline | 128 KiB; satu file TXT/MD UTF-8 per draft | Tolak sebelum ekstraksi; pertahankan draft lama |
| Gabungan teks laporan + lampiran | 32.000 karakter | Tolak input, bukan memotong klaim diam-diam |
| Body request/fixture ke lab | 128 KiB | Policy menolak sebelum dikirim |
| Body response yang dibaca/capture | 1 MiB per request | Hentikan pembacaan dan tandai truncated; jangan memakai bagian hilang sebagai bukti ketiadaan dampak |
| Screenshot | 2 MiB per file | Gunakan viewport/capture yang lebih kecil atau tandai bukti tidak lengkap; jangan mengklaim gambar telah tersimpan |
| Artefak total per run | 16 MiB | Hentikan capture/aksi dengan `ARTIFACT_LIMIT`; pertahankan catatan yang sudah ada |
| Storage artefak lokal | 1 GiB; sisakan ruang disk host minimal 2 GiB | Tolak job baru dengan `STORAGE_LIMIT`; tidak menghapus hasil tanpa operator |

Cap jaringan 40 mencakup navigasi/subresource browser, bukan 40 request HTTP ditambah jaringan browser tak terbatas. Catat denied attempts terpisah dari koneksi yang dieksekusi. Jika asset target menghabiskan budget, sederhanakan lab atau revisi limit pada development sebelum freeze; jangan mengecualikan request yang merepotkan saat benchmark.

Target token awal: maksimum 8.192 token input terkirim per panggilan dan 1.024 output, maksimum 12 panggilan per run termasuk retry. Bukan jaminan semua report sepanjang 32.000 karakter muat. Gunakan tokenizer kompatibel saat tersedia; jika hitungan tidak diketahui jangan menganggap reservasi biaya aman. Tolak/minta peringkasan sebelum dispatch bila report + aturan + tools melebihi cap; jangan menghapus langkah PoC untuk membuat konteks muat. Observasi/riwayat diringkas dengan rujukan evidence, tanpa mengganti bukti asli.

Ledger menyimpan biaya estimasi maksimum, usage aktual, sisa reservasi dan status rekonsiliasi. Harga/provider/token cap dibekukan sebelum live. Jika panggilan timeout setelah dikirim dan usage tidak diketahui, pertahankan reservasi konservatif sebagai `COST_UNKNOWN`; jangan membukukan nol lalu menghabiskan saldo lagi. Pembelian kredit dan biaya token dipisah; perubahan cap/budget bukan tool model.

## 6. Start, health, stop dan reset

### Kontrak startup satu perintah

Target operasi normal MVP adalah `docker compose up -d --build` dari root proyek, setelah Docker/Compose, konfigurasi privat serta seed awal siap. Perintah belum tersedia sekarang karena Compose/source belum dibuat. M1 boleh menyediakan app saja; worker/lab ditambahkan saat benar-benar diimplementasikan. Jangan membuat service dummy untuk meluluskan pemeriksaan topologi.

- Semua dependensi runtime app/worker/lab berada di image; operator tidak harus menjalankan server Python/npm pada host untuk startup normal. Evaluator/scoring host tetap alat terpisah dan membutuhkan Python sesuai PRD.
- Startup memeriksa konfigurasi dan migrasi schema dengan satu pemilik/lock, lalu menyalakan service. Seed akun/program pertama dilakukan operator; restart tidak mengganti password, mengaktifkan guideline, mengganti kondisi lab, menghapus evidence, atau mengosongkan ledger.
- Default pengembangan adalah mock yang terlihat jelas. Pilihan live yang belum terkonfigurasi gagal eksplisit, bukan fallback mock. Startup tidak menjalankan smoke model berbayar/gratis atau benchmark secara otomatis.
- Startup worker idle tidak menguji target. Health service lab lokal dan maintenance evaluator dibedakan dari aksi validasi; request intake OOS/UNKNOWN tetap menghasilkan nol request target.
- `/api/health` app membuktikan liveness saja; readiness worker/lab/config memakai status yang benar. Dependency gagal/tidak tersedia memblok validasi target dan ditampilkan di UI, bukan mengubah hasil report menjadi REFUTED.
- Verifikasi cold start, restart/stop-start dan pelestarian volume pada milestone terkait. Kelulusan M1 app tidak berarti perintah telah menyalakan tiga service MVP lengkap.

### Maintenance operator

Evaluator adalah CLI Python pada host operator, menyimpan GT/scoring di luar container. Operator memanggil fungsi maintenance seed/reset yang terbatas di lab lewat Docker CLI host, ketika run tidak aktif; ini bukan route HTTP, tool agent, atau shell yang menerima isi report. CLI maintenance lab hanya menangani state sintetis dan tidak membawa manifest jawaban/scoring evaluator. Tidak memasang Docker socket pada app, worker ataupun lab. Mekanisme ini belum dibuat/diuji, dan perintah aktual baru masuk README setelah terverifikasi.

Urutan yang akan diimplementasikan:

1. Periksa konfigurasi, schema/migrasi, ruang disk, konektivitas Docker dan batas resource; jangan mengaktifkan live tanpa key/cap biaya.
2. Operator menyiapkan akun/membership, binding target dan guideline aktif yang telah ditinjau. Evaluator menyiapkan lab/seed serta health assertion di luar intake agent.
3. Jalankan worker dengan mount/network minimal dan uji konektivitas yang diizinkan/ditolak. App hanya mengaktifkan tombol validasi bila gate dependency siap.
4. Jalankan satu kasus development yang direproduksi manual dan periksa capture/control/assessment. API liveness app tidak membuktikan worker, model atau lab berfungsi.
5. Saat stop, hentikan penerimaan job baru, cancel/selesaikan job aktif sesuai batas, tutup context, flush hasil/ledger, dan pertahankan volume. Pembersihan/reset target dilakukan evaluator setelah aktivitas berhenti.

`/api/health` hanya mengembalikan liveness dan schema app tanpa credential/binding privat; readiness dependency/admin terpisah dan tidak diakses dari tool target. Default port direncanakan pada bagian 1; port yang benar-benar dapat dipakai, perintah Compose, ukuran image serta alokasi RAM/CPU diverifikasi ketika bootstrap, lalu README memuat perintah yang benar-benar diuji. Laptop 16 GB dan anggaran Docker 4-6 GB tetap target awal; belum jaminan pemakaian nyata.

## 7. Checkpoint implementasi

- M1: migrasi/storage, job/lease/idempotency/ledger pada adapter mock, error API dan input-limit cases; tidak membuka target.
- M2: topologi, handoff, reset evaluator, health, efek mutasi dan crash/dirty-target; jalankan NET-01/03.
- M3: cancellation, restart, scope revoke, draft persistence, projection bukti serta integrasi UI tanpa kontrol prototipe.
- M4: batas browser/network, pergantian akun, marker XSS dengan nonce/action/frame/origin yang dicatat worker; teks yang menyebut nonce saja bukan bukti callback eksekusi.
- M8: tokenizer/cap biaya, usage/refusal/COST_UNKNOWN, dukungan tools aktual dan tidak ada fallback model/provider diam-diam.

Profil/fallback mengikuti prd.md dan architecture.md: free tier/promosi tidak berarti jatah tanpa batas. Simpan reservasi per dispatch meskipun provider berpindah, dan pertahankan COST_UNKNOWN pada timeout yang mungkin ditagihkan. Free tier habis menghentikan jalur itu; tidak ada eskalasi ke paid atau rotasi key untuk memperluas kuota. Setelah respons pertama dikonsumsi, provider terkunci. Benchmark mematikan seluruh fallback/auto-routing. Key OpenRouter/Gemini/OpenAI/xAI hanya di app; tidak dipasang pada worker/target.

Tidak ada checkbox pada dokumen ini yang menyatakan tes tersebut lulus. Hasil aktual dicatat pada milestone dan [security-review.md](security-review.md), bukan disimpulkan dari rancangan.

## Sumber teknis primer

- [Docker Compose networks](https://docs.docker.com/reference/compose-file/networks/): konfigurasi internal network; bukan jaminan isolasi seluruh channel pada host tertentu.
- [SQLite transactions](https://sqlite.org/lang_transaction.html): dasar transaksi dan penanganan konflik penulis.
