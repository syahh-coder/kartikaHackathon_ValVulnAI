# Kontrak runtime lokal dan pemulihan

**Update runtime13 November2026:** app utama diperbarui dengan bridge AI-ke-draf klaim dan cap teks4096/triage-v2. Backup dibuat saat nol pekerjaan aktif;26 tabel identik sebelum/sesudah dan ID worker/lab/manual tetap. Tidak ada migrasi, reset, inferensi cloud atau pengaktifan overlay Azure pada batch ini. Overlay `compose.provider.azure.yaml` mengganti provider pada app_data/ledger utama yang sama; `compose.azure.yaml` lama hanya preview. [Hasil](ai-validation-integration.md), [operasi provider](provider-setup.md).

**Side plane manual 13 November 2026:** [compose.manual-lab.yaml](../compose.manual-lab.yaml) menjalankan satu salinan operator di127.0.0.1:8001 dengan volume/network terpisah dan koneksi keluar baru diblok firewall. Salinan bukan binding target worker dan tidak memakai ledger/API key. Source lab asli dibaca saat salinan dibuat; instance app/worker/lab asli tidak direcreate. [Operasi manual dan kondisi aktual](manual-lab.md), [hasil audit](backend-audit-2026-11-13.md). Topologi default tiga service di bawah tetap jalur produk.

**Pembaruan runtime Azure7 November:** adapter teks tersedia dan lulus148 tes simulasi/regresi. Overlay [compose.azure.yaml](../compose.azure.yaml) hanya untuk app preview8010 dengan `.env.azure` privat dan volume/ledger preview yang sama; planner mock, dispatcher target mati. Overlay live belum dijalankan karena input akun belum lengkap. Source schema tetap006; instalasi asli8000/worker/lab dipertahankan. [Panduan](azure-setup.md), [hasil](azure-verification.md). Catatan005 dan provider rencana di bawah merupakan riwayat checkpoint lama.

**R3b/R4 terbaru:** source schema006 dan runner evaluasi teks memakai ledger aplikasi yang sama, tanpa run lab baru. Compose env_file hanya app/evaluator; worker/lab tidak menerima key. Profil `evaluation` opsional memakai app_data yang sama dan folder privat artefak, tanpa jaringan lab. Source app/worker/lab tetap tidak menyalin evaluator/GT. Image review terpisah dan app-only startup/restart network-none/volume baru diuji; container/data/ledger aktif tidak diperbarui. [Runbook](r3-runbook.md), [hasil aktual](r3-r4-verification.md), [indeks review](final-review.md). Paragraf source005/topologi R1/R2 di bawah adalah hasil tahap itu.

**R2 7 November CODE_TESTED dan QA lokal lulus:** UI memakai triage R1, status model/provider dan konfigurasi, polling/cancel/discovery serta penanda hasil lama. Ringkasan observasi adalah GET read-only aplikasi, tanpa inference atau target execution; hanya membaca bukti tersimpan yang binding/hash-nya cocok, mengikuti projection owner/admin/publikasi. Tidak ada migrasi/topologi/mount/service aktif baru; source schema tetap 005. [Bukti dan batas QA sintetis R2](r2-verification.md).

**Status aktif 7 November 2026:** source [R1 provider/triage teks](r1-verification.md) CODE_TESTED melalui app ASGI/database sementara dan HTTP simulasi; LIVE_VERIFIED belum, CONFIGURATION_REQUIRED. Mode `VALVULN_TRIAGE_MODE` terpisah dari planner/transport lab. Satu triage aktif, deadline default 30 detik (maksimum 60), retry default mati/maksimum satu, reservasi per attempt di ledger lama yang sama; crash/cancel mempertahankan biaya unknown tanpa replay. Input 8192/output 1024, envelope 64 KiB, tokenizer/batas konservatif wajib diverifikasi operator sebelum live. Migrasi source app 005 belum diterapkan ke service aktif. Tidak mengubah topologi/mount/target/service Compose, mapping environment Compose atau gate katalog. Key hanya pada app, tidak dikirim ke worker/UI/log. [Keputusan scope](submission-scope.md).

Status audit 6 November 2026: M1-M5 selesai teknis lokal. [Hasil M5](m5-verification.md), [M4c](m4c-verification.md). Jalur produk/UI BAC-08, XSS-08 dan UP-04 fixture tetap, planner mock; model live belum tersedia. Kontrak schema/izin di [architecture.md](architecture.md).

Runtime M5: satu run UP-04 memakai lima aksi, 10 request (termasuk login) dan 15 operasi browser dalam cap 40 request/30 operasi/180 detik. Upload maksimum 10 detik dan respons 4 KiB; browser maksimum 30 detik per aksi. Policy memerlukan POST upload, GET daftar dan GET label aman sebelum dispatch. Mutasi ditandai dirty sebelum I/O; cancel/crash ambigu tidak mengulang upload dan memerlukan reset evaluator. Tidak ada reset/fixture/browser/model otomatis saat startup. UP-01..03 tetap evaluator operator saat maintenance. Audit offline hanya membaca artefak; tidak menjalankan transport, reset, scoring atau provider.

## 1. Topologi minimum

Pembaruan 6 November: app Compose telah dibangun/dijalankan ulang untuk [review rekaman bisnis manual](business-record-review.md); worker/lab tetap container M5 yang sama. Nol job aktif sebelum update, 37 riwayat run/ledger dipertahankan, migrasi app 004 dan health/UI lulus. File unggahan memakai evidence storage privat yang masuk kuota, maksimum 128 KiB/record dan 20 record/report; tidak masuk antrean/evidence worker atau ledger provider. Tidak memanggil target/model. Paragraf M6a/b di bawah mencatat kondisi batch terdahulu; source lab tetap belum diaktifkan di service lab proyek.

Update workflow langkah admin berikutnya juga hanya mengganti app, tanpa migrasi baru. Endpoint konteks melakukan pembacaan lokal terbatas dan tidak mengantrekan aksi/worker/model. Snapshot database/ledger sebelum/sesudah identik, worker/lab tetap ID yang sama dan source workflow/JS container cocok host. [Hasil workflow](business-record-review.md#workflow-bukti-dan-konteks-terstruktur).

M6b memeriksa persistensi pada dua container pengganti dengan satu volume baru khusus uji, bukan volume/service Compose proyek. Stok, versi, fulfillment, snapshot dan jurnal bisnis dipertahankan; replay tidak menambah mutasi. Cleanup memerlukan prefix UUID serta label pemeriksaan yang cocok. Runner tidak melakukan pull/build, membaca secret operator atau memanggil worker/model. Service aktif tetap M5. Integrasi konteks baru hanya mock NONE pada source; seluruh run LAB/business logic tetap mengikuti capability yang sudah ada. [Hasil M6b](m6b-verification.md).

M6a diuji pada database sementara/ASGI dan container disposable turunan image lab lokal, non-root/read-only/network none tanpa volume/secret. Service Compose aktif tetap image M5. Startup source baru hanya memigrasi tabel lab kosong; tidak menyediakan akun petugas, barang atau state bisnis otomatis. Setup `lab.business_setup` adalah operasi operator saat maintenance/idle: path database lab eksplisit, password interaktif, snapshot baru, lalu verifikasi/release terpisah. Guard identitas database diperiksa read-only sebelum migrasi untuk menghindari perubahan pada database aplikasi yang salah dipilih. Tidak ada register worker/tool/capability baru atau perubahan kuota/ledger. [Hasil dan batas M6a](m6a-verification.md).

Packaging MVP diperjelas pada 4 November 2026: **tiga container yang berjalan terus**, bernama `app`, `worker` dan `lab`. UI disajikan app; Chromium berjalan di worker. Tidak ada container database, frontend atau evaluator tambahan. Pada pengembangan M1 hanya app yang diperlukan; tiga service adalah topologi MVP lengkap, bukan syarat menjalankan seluruhnya sebelum lab dibuat. Pilihan stack dan ringkasan volume dimiliki [prd.md](../prd.md).

| Komponen | Koneksi dan data | Larangan |
| --- | --- | --- |
| Aplikasi FastAPI + satu dispatcher | UI/API pada loopback host; SQLite, ledger dan evidence privat; akses provider model yang dikonfigurasi | Tidak bergabung ke jaringan target lab, tidak meneruskan endpoint jaringan bebas dari chat |
| Worker HTTP/browser | Hanya jaringan lab internal; inbox job read-only, outbox hasil terpisah dan akun uji yang diperlukan | Tidak menerima `.env` aplikasi, key model, SQLite, source/evaluator/GT, Docker socket atau internet umum |
| Portal lab | Jaringan internal yang sama dengan worker, data sintetis | Tanpa port publik/internet, source evaluator, atau mount job/evidence aplikasi |
| Operator/evaluator | Menyiapkan seed/kondisi, memeriksa health dan reset melalui jalur maintenance lokal terpisah | Bukan tool agent atau menu admin program |

Jalur app <-> worker dipilih **file JSON terstruktur pada dua volume handoff sempit**, bukan worker mengakses database/API utama. App menulis inbox dan membaca outbox; worker membaca inbox dan menulis outbox. Tidak membuat Redis, broker cloud atau Docker container target baru per report. App tidak mendapatkan akses target hanya untuk mengecek health saat intake.

Port default rancangan: app memublikasikan hanya `127.0.0.1:8000`, sedangkan lab melayani port internal `8001` tanpa port host; worker tanpa listener host. App mempunyai jaringan sendiri dengan akses provider, worker/lab hanya `lab_internal`. Tidak menyatukan semua service ke default network Compose. Pada M2 binding socket dikunci IP 172.30.74.3:8001 (Host/Origin lab:8001), tanpa DNS/proxy untuk worker. Subnet 172.30.74.0/29, worker .2; jangan mengganti IP tanpa mengubah firewall dan profil bersama.

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
- Crash/restart: tandai run LEASED yang kehilangan proses sebagai FAILED (`WORKER_LOST` atau `PROCESS_INTERRUPTED`). Jangan auto-resume atau auto-replay mutasi. Pada M1 startup menandai semua QUEUED/LEASED yang tertinggal sebagai FAILED PROCESS_INTERRUPTED; tidak menjalankan inference otomatis setelah restart. Permintaan eksplisit baru dengan run ID baru diperlukan. Lease baru saat app berjalan tetap memeriksa membership/scope/dirty-target/expiry. Ini memperketat rancangan awal yang memperbolehkan queued job dilanjutkan setelah recheck.
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

Target operasi normal MVP adalah `docker compose up -d --build` dari root proyek, setelah Docker/Compose, konfigurasi privat serta seed awal siap. Perintah diuji pada M1 untuk app, dan pada M2 untuk tiga service nyata setelah setup secret serta seed/maintenance operator. M1 boleh menyediakan app saja; worker/lab ditambahkan saat benar-benar diimplementasikan. Jangan membuat service dummy untuk meluluskan pemeriksaan topologi.

- Semua dependensi runtime app/worker/lab berada di image; operator tidak harus menjalankan server Python/npm pada host untuk startup normal. Evaluator/scoring host tetap alat terpisah dan membutuhkan Python sesuai PRD.
- Startup memeriksa konfigurasi dan migrasi schema dengan satu pemilik/lock, lalu menyalakan service. Seed akun/program pertama dilakukan operator; restart tidak mengganti password, mengaktifkan guideline, mengganti kondisi lab, menghapus evidence, atau mengosongkan ledger.
- Default pengembangan adalah mock yang terlihat jelas. Pilihan live yang belum terkonfigurasi gagal eksplisit, bukan fallback mock. Startup tidak menjalankan smoke model berbayar/gratis atau benchmark secara otomatis.
- Startup worker idle tidak menguji target. Health service lab lokal dan maintenance evaluator dibedakan dari aksi validasi; request intake OOS/UNKNOWN tetap menghasilkan nol request target.
- `/api/health` app membuktikan liveness saja; readiness worker/lab/config memakai status yang benar. Dependency gagal/tidak tersedia memblok validasi target dan ditampilkan di UI, bukan mengubah hasil report menjadi REFUTED.
- Verifikasi cold start, restart/stop-start dan pelestarian volume pada milestone terkait. Kelulusan M1 app tidak berarti perintah telah menyalakan tiga service MVP lengkap.

### Maintenance operator

Evaluator adalah CLI Python pada host operator, menyimpan GT/scoring di luar container. Operator memanggil fungsi maintenance seed/reset yang terbatas di lab lewat Docker CLI host, ketika run tidak aktif; ini bukan route HTTP, tool agent, atau shell yang menerima isi report. CLI maintenance lab hanya menangani state sintetis dan tidak membawa manifest jawaban/scoring evaluator. Tidak memasang Docker socket pada app, worker ataupun lab. Mekanisme M2 sudah dibuat/diuji melalui `python -m evaluator.m2`; perintah aktual pada README dan hasil pada m2-verification.md. CLI reset tidak menjadi route/tool agent.

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

Hasil fondasi M1 sudah dicatat pada [m1-verification.md](m1-verification.md), milestone dan [security-review.md](security-review.md). Bagian M2-M8 tetap rancangan yang belum lulus hanya karena mock tersedia.

## Sumber teknis primer

- [Docker Compose networks](https://docs.docker.com/reference/compose-file/networks/): konfigurasi internal network; bukan jaminan isolasi seluruh channel pada host tertentu.
- [SQLite transactions](https://sqlite.org/lang_transaction.html): dasar transaksi dan penanganan konflik penulis.


## Implementasi HTTP M2

M2 memasang firewall namespace dengan bootstrap root (NET_ADMIN/SETUID/SETGID/SETPCAP), kemudian setpriv menghapus capability dan menjalankan Python UID/GID 10001. DNS Docker ditolak sebelum aturan ESTABLISHED; IPv6 ditutup. Probe aktual, mount read-only, symlink dan batasnya tercatat pada m2-verification.md. Tidak membuat perubahan firewall host atau privileged container. Worker/target tidak memiliki transport provider/model key.

Handoff mengunci scope epoch, snapshot target dan worker boot ID. Worker journaling mendahului I/O; mutasi memegang dirty_run_id agar kontrol lanjutan dalam run yang sama dapat berjalan, sementara run lain ditolak. Selesai/cancel/crash melepas dirty_run_id tanpa membersihkan dirty. Hanya evaluator setelah reset/assertion/health dan acknowledgment snapshot netral yang melepaskannya. Tidak ada auto-reset/resume target saat startup.

M2 operator memakai execution_mode=mock untuk mode model, tool_execution_mode=LAB untuk I/O aktual; model tidak dipanggil dan assessment null. Workflow mock API biasa tetap tool_execution_mode=NONE. Semua login worker masuk reservasi/cap 40 dispatch target. Counter dispatch mencakup upaya transport, bukan jaminan delivery ketika terjadi timeout; responses_received dan outcome unknown dicatat terpisah. Browser tidak ada pada M2.

## Runtime M3 yang diverifikasi

Run UI dengan `execution_mode=mock` dan `tool_execution_mode=LAB` memakai planner deterministik serta tujuh aksi HTTP aktual (14 request termasuk login per aksi). NONE tetap simulasi tanpa request target. OOS/UNKNOWN/unsupported/prasyarat kurang tidak mengakses target. Satu job aktif, snapshot/scope/boot worker dikunci; cancel/revoke menghentikan aksi berikutnya dan I/O aktif, tanpa undo mutasi. Target dirty memerlukan reset evaluator sebelum run berikutnya.

`/api/readiness` kini melaporkan jalur validasi UI AVAILABLE jika transport/heartbeat dapat dibaca; kesiapan target ditampilkan terpisah sebagai OPERATOR_VERIFIED/OPERATOR_CHECK_REQUIRED. AVAILABLE bukan izin melewati dirty/snapshot/scope/capability: gate start dan per aksi tetap menentukan. Model live selalu CONFIGURATION_REQUIRED. Runner `evaluator.m3` dan QA browser adalah operasi eksplisit, tidak dijalankan startup.

## Runtime M4a

Worker menambah Playwright Python/Chromium melalui requirements-worker.lock; tidak dipasang pada app/lab/host test. Chromium penuh headless diluncurkan non-root dengan chromium_sandbox=True, namespace/seccomp aktif. Worker memakai profil seccomp terbatas turunan Playwright dengan chroot untuk sandbox namespace, tetap tanpa SYS_ADMIN/privileged/host IPC. Konfigurasi/cache browser berada di XDG tmpfs, root filesystem read-only. Cap worker aktual: RAM 1 GiB, 256 PID, tmpfs 256 MiB, shared memory privat 128 MiB. Inventaris pin/OS pada [dependencies-m4.json](dependencies-m4.json); source/notice pada [third-party.md](third-party.md).

Browser probe hanya satu halaman, dua request termediiasi (login + dokumen), lima operasi logis, deadline aksi 30 detik. Semua request browser lain ditolak; byte respons dibaca terbatas oleh HTTPX sebelum dikirim ke browser. PNG 256 KiB dan DOM excerpt 8.192 karakter masuk budget artefak/provenance yang sama. Fresh context dan cookie/storage diperiksa, lalu ditutup setiap aksi. Browser menandai target dirty secara konservatif; reset evaluator tetap diperlukan untuk run berikutnya.

Cancel/scope/membership memakai control channel M3 untuk menghentikan browser dan request HTTPX yang sedang berjalan; cleanup mempertahankan intercept sampai context tertutup, membatalkan callback pending dan menyelesaikan route dengan abort. Unroute sebelum close terbukti melepas navigasi ke jaringan langsung pada M4b; urutan itu sudah diperbaiki dan diuji ulang. Fixture delay server dapat selesai sesudah client berhenti, sehingga evaluator menunggu handler tersebut selesai sebelum reset. Tidak menjanjikan undo efek target. Recovery browser unknown/no replay diuji pada journal unit; SIGKILL aktual M2 adalah pengujian HTTP, bukan browser.

Startup tidak meluncurkan browser/probe atau mereset target. Readiness lab_tools=HTTP_AND_BOUNDED_NOTIFICATION_BROWSER sejak M4b menggambarkan jalur UI BAC dan XSS pratinjau terbatas; scope/capability/dirty/snapshot tetap diperiksa saat start/per aksi. XSS memakai empat probe, delapan request, 20 operasi browser logis dan mock planner Rp0 dalam cap bersama. Setelah run target dirty sampai reset operator. Cancel sebelum observasi pertama dapat menyisakan nol evidence, assessment null. [Hasil M4b](m4b-verification.md).

## Maintenance operator M4c

Evaluator `python -m evaluator.m4c` berjalan di host, menolak run/antrean aktif dan masuk maintenance sebelum reset/transport. Probe kode tetap operator dikirim via stdin Docker exec ke namespace worker idle; file evaluator/manifest/GT tidak disalin atau dimount ke image/agent. Operator memakai Chromium sandbox/UID/egress yang sama untuk satu dokumen tepat per context. Ini bukan tool runtime atau akses terminal dari report/model. Rute produk, scope tool dan readiness tidak diperluas ke tujuh fitur baru.

Tiap kondisi mempunyai tiga context baru (inert/marker/jalur aman), maksimal 30 detik per fixture dan 95 detik per probe, batas dokumen/PNG 1 MiB/256 KiB. Input stored ditulis lewat HTTP A lalu dibaca akun B, bukan ditanam melalui database. Output dengan ID operator/provenance/hash tersimpan privat di host; tidak mencampurkan assessment/ledger app atau GT manusia. Reset lab akhir mengembalikan seluruh kondisi fixed dan menghapus log lab sintetis setelah capture; release maintenance hanya sesudah nol Chromium. Riwayat app/evidence/kuota tidak dihapus. Cleanup yang gagal mempertahankan target unavailable; operasi host Docker tetap di luar model.
