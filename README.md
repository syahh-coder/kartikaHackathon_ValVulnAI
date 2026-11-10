# ValVuln AI: Agen Validasi Laporan Kerentanan

**Azure Foundry untuk akun pelajar:** pengguna memilih jalur ini pada7 November. Adapter triage teks/evaluator dan checker tersedia,148 tes terarah lulus (simulasi); LIVE_VERIFIED=false. Isi `.env.azure` privat mengikuti [cara mengambil key/endpoint/deployment dan mengaktifkan web8010](docs/azure-setup.md). Template publik [`.env.azure.example`](.env.azure.example); [hasil dan batas](docs/azure-verification.md). Preview tetap MOCK sampai overlay Azure diaktifkan setelah konfigurasi lengkap. Ringkasan observasi aplikasi tidak memanggil AI; gunakan tombol **Minta saran AI** pada percakapan hunter.

Purwarupa untuk Kartika Cyber Hackathon 2026 oleh tim solo **ukas and codex vs everbody**.

ValVuln AI adalah nama kerja untuk draf formulir. Rekomendasi kategori setelah membaca rulebook: **Penindakan**, karena fungsi utamanya adalah pengujian aktif/reproduksi klaim kerentanan. Pada 3 November 2026 pengguna menyatakan pendaftaran program diterima; asisten tidak mengirim formulir atau memverifikasi platform langsung. Pada 4 November 2026 pengguna menerima UI saat ini sebagai **baseline fix untuk mulai backend**, dengan perbaikan UI yang masih boleh menyusul. M1 fondasi lokal selesai pada 4 November 2026; persetujuan UI tetap bukan bukti keamanan worker/model.

Tujuan: memeriksa scope laporan, mereproduksi klaim terhadap portal pengadaan/logistik lab, dan menyajikan bukti yang dapat ditinjau analis.

## Status saat ini

**Paket review terbaru 7 November: READY_FOR_REVIEW_WITH_PENDING_INPUTS.** Sisa kode independen R3b–R3f dan persiapan R4 tersedia: konteks/prediksi A/B, runner teks dengan ledger aplikasi bersama, gate freeze, hasil pending, arsip source/checksum serta slide/gambar/preview demo lokal. [Buka indeks review, bukti tes dan input pengguna](docs/final-review.md). [Quick start kandidat paket](docs/review-quickstart.md), [runbook evaluator](docs/r3-runbook.md), [bahan presentasi](submission/README.md).

**CODE_TESTED lokal; LIVE_VERIFIED=false, FROZEN=false, EVALUATED=false.** Dua puluh kandidat tetap 0 GT manusia dan 0 konteks bukti kasus final; metrik benchmark null. Simulasi40 slot terpisah dari hasil nyata. Schema source006 diuji pada data disposable; service/37 riwayat run/ledger pengguna tetap dipertahankan. Belum ada push, release, upload atau submit. Paragraf checkpoint R3a/R2 di bawah adalah riwayat sebelum paket review ini.

**Mode kerja terbaru 7 November 2026:** lanjutkan seluruh pekerjaan independen sisa R3 sampai paket/artefak R4 siap direview pengguna sekaligus, mengikuti [prompt aktif](docs/execution-prompt.md). Tidak berhenti meminta izin di tiap sub-tahap. GT/key/bukti yang belum tersedia tetap pending, tanpa menghalangi pengemasan independen atau dipalsukan sebagai hasil. Publikasi dan submit sesudah review. Dokumen ini belum menyatakan R3b/R4 sudah diimplementasikan.

**Status aktif 7 November 2026: persiapan R3a CODE_TESTED; R3 belum selesai.** Peta subtype/bukti, paket privat **20 kandidat teks** (8/8/4), lembar GT manusia kosong serta scorer offline functional-v2 tersedia. **26 tes terarah lulus**. Semua kandidat masih menunggu penerimaan/GT; 40 slot A/B NOT_STARTED, belum ada skor model. [Hasil dan petunjuk review GT](docs/r3-verification.md). R1/R2 tetap tersedia tanpa pengulangan; [UI R2](docs/r2-verification.md). **LIVE_VERIFIED belum**, service/data aktif tidak diperbarui.

Berikutnya **R3b: review GT pengguna, bukti B per kasus, integrasi prediksi/runner A/B dan freeze**, lalu R4 paket sesuai [scope submission](docs/submission-scope.md). Dukungan produk tetap BAC-08, XSS-08 dan UP-04; BUSINESS_LOGIC belum didukung. Target benchmark 20 teks 10/10 tetap target; kandidat bukan laporan final atau bug independen/held-out. Buka `artifacts/r3/candidates-v1/gt-review.csv` untuk review, jangan mengisi label otomatis. [Checkpoint aktif R3](docs/execution-prompt.md).

Status/verifikasi 6 November di bawah adalah riwayat hasil lokal. Source R1/R2 berubah pada 7 November; data runtime aktif tetap dipertahankan. R2 diuji pada app ASGI dan server/browser loopback dengan database disposable, bukan deployment container.

**Alur review rekaman bisnis dan workflow langkah admin tersedia di produk lokal:** pelapor menyimpan snapshot, admin mengunggah JSON, memeriksa **Langkah berikutnya**, meninjau dan membagikan ringkasan. **172 tes serta QA desktop/mobile lulus**, app Compose sudah diperbarui tanpa mengubah 37 riwayat run/ledger. Pilih **Siapkan review bukti bisnis** pada laporan. [Panduan dan batas review bisnis](docs/business-record-review.md). Konteks workflow dapat diekspor oleh admin, tetap tanpa eksekusi target/model; belum validator business logic otomatis, M6 tetap sebagian.

**M1–M5 selesai teknis lokal; M6 sebagian, 6 November 2026.** M6a/b menambahkan kontrol bisnis aman, konteks aturan pada simulasi tanpa tool, persistensi dan katalog. **145 tes terarah lulus**, serta dua container dengan satu volume khusus mempertahankan stok/fulfillment saat restart. [Hasil M6b dan batas](docs/m6b-verification.md). Hitungan tetap 13 dari 24 titik; 11 masih PLANNED dan konflik grouping evaluasi belum selesai. Planner mock; model live/GT manusia/benchmark belum tersedia. Business logic belum didukung validator produk.

Tambahan auditor rekaman offline: **25 tes baru lulus**, dua rekaman persistensi tersimpan konsisten. Perintah `python -m evaluator.business_record_audit <file.json>` hanya memeriksa konsistensi state/stok/replay dan tidak menghasilkan verdict kerentanan atau GT. [Batas audit rekaman](docs/m6b-verification.md).

Penguatan parser [M6d](docs/m6d-verification.md) sudah diverifikasi: 33 tes parser dan dua rekaman historis lulus. [M6e](docs/m6e-verification.md) menambah audit event kontrol normal, dengan **97 tes terarah lulus** dan trace ASGI dua lifecycle CONSISTENT. Auditor memeriksa hubungan aktor/unit, urutan persetujuan, stok serta replay berdasarkan rekaman; hasil bukan bukti keaslian capture atau verdict kerentanan. Jalankan `.\.venv\Scripts\python.exe -m scripts.m6e_trace_check` untuk database uji sementara, atau `python -m evaluator.business_trace_audit <file.json>` untuk rekaman tersimpan. Ini belum validator BUSINESS_LOGIC produk.

Review grouping [M6f](docs/m6f-verification.md): **21 tes lulus**, gate katalog kini mempertahankan riwayat development walaupun label alokasi berubah. Split masih belum boleh freeze: HTML development UP-04 berbagi grup evaluasi XSS, dan kandidat di luar grup development belum memenuhi empat area XSS. Alokasi/status/grup katalog tetap; `python -m evaluator.catalog_audit --require-ready` mengembalikan exit 2 yang diharapkan. Ini review offline, tanpa run target/model baru.

Kode kontrol lab M6a/b tersedia di source; worker/lab Compose tetap image M5. App sudah diperbarui untuk review manual di atas, bukan menjalankan validator BUSINESS_LOGIC LAB. Pemeriksaan persistensi lab sebelumnya memakai database/volume khusus uji. Dari root: `.\.venv\Scripts\python.exe -m scripts.m6b_persistence_check` (perlu image lokal pemeriksaan M6a) dan `.\.venv\Scripts\python.exe -m evaluator.catalog_audit --require-ready`. Gate katalog tetap exit 2 karena belum siap; ini tidak berarti M6 selesai.

App dan UI chat backend tersedia pada **http://127.0.0.1:8000**. Login menggunakan akun demo operator; role diperiksa server. Validasi produk mendukung BAC penghapusan lampiran lintas akun, XSS pratinjau notifikasi dan nama lampiran upload UP-04 melalui fixture tetap. Payload/script laporan tidak dijalankan; isi upload berupa teks tetap aplikasi. Tujuh rute XSS tambahan dan UP-01..03 hanya evaluator operator, belum planner/UI. Model live, 11 titik lain, dataset berlabel dan benchmark belum tersedia. [Prototipe UI](ui-prototype/README.md) tetap terpisah dengan data simulasi.

Repo GitHub: [syahh-coder/kartikaHackathon_ValVulnAI](https://github.com/syahh-coder/kartikaHackathon_ValVulnAI). Perubahan M1-M5 lokal belum di-commit/push; belum ada release aplikasi atau deployment.

Reproduksi tujuh titik XSS tambahan, hanya saat tidak ada run aktif: `.\.venv\Scripts\python.exe -m evaluator.m4c`. Evaluator masuk maintenance dan mereset **lab sintetis** tiap kondisi, lalu mengembalikan semua kondisi ke fixed; riwayat/ledger aplikasi tetap. Detail kontrol, opsi satu titik dan artefak privat pada [panduan M4c](docs/m4c-verification.md).

### Menjalankan aplikasi lokal dengan Docker

Docker Desktop/Engine harus berjalan dalam mode Linux containers. Verifikasi sesi ini: Engine 29.7.2, Compose v5.3.1, context desktop-linux. Port 8000 hanya dipublikasikan ke loopback. Dari root repo:

```powershell
Copy-Item .env.example .env  # hanya setup pertama jika .env belum ada
py -3.11 scripts/setup_local.py  # buat hanya secret transport/lab yang belum ada
docker compose up -d --build
docker compose exec app python -m app.operator
```

Perintah seed terakhir meminta kata sandi demo lokal 12-128 karakter untuk akun sintetis `hunter-a`, `hunter-b`, `admin`. Seed dapat diulang tanpa mengganti password atau mengaktifkan scope. Setelah setup/seed, startup normal cukup:

```powershell
docker compose up -d --build
```

Pada M2 **app, worker HTTP dan lab nyata** berjalan. SQLite app berada pada `app_data`, SQLite portal pada `lab_data`; `job_inbox`/`job_outbox` hanya handoff sempit. Worker/lab tidak memublikasikan port host. Data app berada pada named volume `app_data`; restart tidak menghapus draft/hasil/ledger atau mengaktifkan scope. Pekerjaan pending menjadi `PROCESS_INTERRUPTED`, sehingga perlu permintaan eksplisit baru. Startup tidak memanggil model/target. `docker compose stop app` menghentikan app sambil mempertahankan volume. Tidak ada perintah reset volume pada alur normal.

`GET /api/health` membuktikan liveness/schema app. `GET /api/readiness` membaca heartbeat worker dan readiness lab yang telah diverifikasi operator, dan melaporkan jalur HTTP dan browser notifikasi terbatas dari UI; gate scope/dirty/snapshot tetap wajib pada start dan setiap aksi. Sebelum seed/reset evaluator, lab tetap OPERATOR_CHECK_REQUIRED. Provider live tetap CONFIGURATION_REQUIRED. Konfigurasi live/replay tidak diam-diam menjadi mock. Tidak memerlukan API key untuk M1.

### Pengembangan dan pengujian host

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.lock
.\.venv\Scripts\python.exe -m pip install --no-deps -e .
.\.venv\Scripts\python.exe -m pytest -q
```

Alternatif menjalankan Python lokal, saat port 8000 tidak dipakai app Docker:

```powershell
.\.venv\Scripts\python.exe -m app.operator
.\.venv\Scripts\python.exe -m uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000 --workers 1 --no-access-log
```

Alternatif host memakai `.local-data/`, terpisah dari volume Docker; jangan menjalankan dua proses app pada direktori data yang sama. Smoke runtime Uvicorn yang diverifikasi pada sesi ini adalah Docker, sedangkan suite host memakai ASGI app aktual.

Untuk menjalankan ulang smoke Docker dengan akun yang sudah di-seed, sediakan `VALVULN_SEED_PASSWORD` melalui environment lokal atau gunakan seed smoke otomatis pada volume baru:

```powershell
.\.venv\Scripts\python.exe scripts/m1_smoke.py --seed --restart-check --stop-start-check
```

Smoke membuat report/scope **simulasi**, memeriksa akses silang, idempotency dan persistensi, lalu meninggalkan riwayatnya. Bila password belum diberikan, smoke pertama menyimpan password acak lokal pada `.local-data/demo-password.txt` yang diabaikan Git; jangan bagikan file tersebut. Seed tidak mengganti password akun yang telah ada. Perintah ini eksplisit menjalankan smoke dan restart app, bukan perilaku startup.

### Urutan API M1

Bagian berikut menjalankan workflow mock API biasa dengan `tool_execution_mode=NONE`, tanpa akses target. Runner operator M2 terpisah di bawah. Schema lokal: `/openapi.json`. Gunakan origin persis `http://127.0.0.1:8000`, cookie session, dan header `X-CSRF-Token` untuk mutasi:

1. `GET /api/auth/csrf`, lalu `POST /api/auth/login` dengan token login, `login_name` dan `password`; role tidak diterima dari client. Gunakan token CSRF baru dari respons login.
2. `GET /api/programs`. Admin membuat `scope-drafts` dan mengaktifkannya secara eksplisit hanya untuk binding operator. Seed sendiri belum mengaktifkan guideline.
3. Buat `conversations`, kirim `messages` dengan `expected_draft_version`; upload opsional satu TXT/MD UTF-8, maksimal 128 KiB, gabungan 32.000 karakter. Kirim tidak otomatis memulai run.
4. `POST /api/conversations/{id}/reports` mengunci revisi dan klaim utama. `POST /api/reports/{id}/runs` memakai revision ID, `execution_mode=mock` dan `Idempotency-Key`.
5. Poll `GET /api/runs/{id}`. Hasil mock `INCONCLUSIVE`, nol request target; export/projection mengikuti ownership. Penolakan gate tidak membuat job. Contoh yang dapat dijalankan ada pada [smoke script](scripts/m1_smoke.py).


### Demo UI BAC development M3

1. Login `admin`. Jika guideline belum aktif, buka **Guideline program**, isi teks aturan dan JSON berikut, simpan lalu aktifkan draf. Aktivasi versi baru menghentikan run lama; jangan mengubah guideline saat operator lain sedang menguji.

```json
{"in_scope_rules":[{"asset_alias":"portal","path_template":"/api/attachments/{id}","methods":["GET","DELETE"],"capabilities":["BAC"]}],"out_of_scope_rules":[],"business_rules":"Akun hanya boleh membaca dan menghapus lampiran miliknya sendiri."}
```

2. Saat tidak ada run aktif, evaluator menyiapkan target sintetis secara eksplisit:

```powershell
.\.venv\Scripts\python.exe -m evaluator.m2 reset --condition fixed
```

3. Login `hunter-a` atau `hunter-b`, pilih program, buat laporan dan tekan **Kirim**. Upload TXT/MD opsional. Kirim hanya menyimpan draf.
4. Pilih **Validasi snapshot**. Isi path korban `/api/attachments/<attachment_id requester-b>` dan kontrol `/api/attachments/<attachment_id requester-a>` dari output reset, dengan arah akun requester-a ke requester-b. Pilih HTTP lab aktual. Klaim diisi terstruktur; belum diekstrak model dari teks.
5. Run lengkap menghasilkan tujuh evidence internal dan 14 request target termasuk login. Pada kondisi fixed, verifier seharusnya REFUTED jika kontrol lengkap; ringkasan hunter menunggu admin review dan publikasi. Admin membuka laporan, membaca bukti, menyimpan review lalu **Bagikan ringkasan**. Ekspor mengikuti role.
6. Setiap run menghapus objek kontrol, sehingga run berikutnya perlu reset evaluator dan ID objek terbaru. Untuk kondisi rentan, gunakan reset `--condition vulnerable`; efek kehilangan akses pemilik diperlukan untuk CONFIRMED. Edit/kirim draf baru sebelum membuat snapshot dengan path baru. Tidak ada reset dari UI/model.

Teks/pesan yang sudah dikirim tersimpan di server; teks yang belum dikirim hanya bertahan dalam memori tab selama navigasi dan hilang saat reload/logout. Hunter tidak menerima evidence mentah atau catatan internal. Model live tetap belum terhubung.

Pemeriksaan otomatis eksplisit, saat tidak ada run lain:

```powershell
.\.venv\Scripts\python.exe -m evaluator.m3
# Opsional QA browser host, dengan playwright-core/Chromium yang sudah tersedia:
$env:VALVULN_PLAYWRIGHT_CORE='C:/path/to/node_modules/playwright-core'
$env:VALVULN_CHROMIUM='C:/path/to/chrome.exe'
node scripts/m3_ui_smoke.cjs
node scripts/m3_ui_session_check.cjs  # gunakan run QA yang sudah selesai, tanpa run/reset baru
```

Runner API menyiapkan kondisi rentan/perbaikan, zero-I/O dan cancel, lalu reset fixed; QA browser juga mengubah lab dan meninggalkan riwayat app. Password demo dibaca lokal dari `.local-data/demo-password.txt` yang telah disiapkan smoke/operator, tanpa dicetak. Batas tiga start per akun per jam tetap berlaku; tunggu kuota pulih sebelum mengulang. QA browser dapat memakai `VALVULN_SMOKE_HUNTER=hunter-b` untuk akun hunter kedua. Browser QA host bukan browser worker produk. Artefak privat di `artifacts/m3/`; hasil/batas di [verifikasi M3](docs/m3-verification.md).

### Lab BAC development dan evaluator M2

Setelah akun platform di-seed, siapkan kondisi lab secara eksplisit:

```powershell
.\.venv\Scripts\python.exe -m evaluator.m2 reset --condition fixed
```

Untuk reproduksi development terkontrol:

```powershell
.\.venv\Scripts\python.exe -m evaluator.m2 verify
.\.venv\Scripts\python.exe -m evaluator.m2 crash-check
.\.venv\Scripts\python.exe -m evaluator.m2 network
```

`verify` menjalankan kondisi rentan/perbaikan dengan kontrol pemilik dan pemeriksaan dirty-target, lalu meninggalkan lab dalam kondisi fixed dengan seed baru. Jika belum ada scope aktif, verify mengaktifkan guideline development menggunakan admin platform melalui CLI operator; scope aktif yang sudah ada tidak ditimpa. `crash-check` secara eksplisit mematikan worker setelah mutasi, memeriksa jurnal unknown/no-replay, lalu reset fixed. Keduanya membuat riwayat development baru, bukan 20 laporan benchmark atau hasil model. Gunakan saat tidak ada run lain.

Reset hanya mengubah database lab. App menyimpan evidence/ledger dan memeriksa ulang membership/scope per aksi sebelum menulis job bertanda HMAC. Tool menerima metode/path/alias terstruktur, tanpa URL bebas, header kredensial, shell atau script. Mode model tetap mock; run operator mempunyai `tool_execution_mode=LAB` dan assessment null. Menyelesaikan reproduksi operator tidak berarti verifier/agent AI sudah berfungsi.

Firewall worker/lab dikonfigurasi dalam namespace container saat bootstrap, lalu Python turun ke UID 10001 dengan seluruh capability dihapus. Mount, probe jaringan, batas dan hasil aktual pada [verifikasi M2](docs/m2-verification.md). Browser belum dipasang. Jangan mengganti subnet/IPAM sendiri tanpa memperbarui profil dan aturan firewall bersamaan.

### Browser development M4a (operator)

Chromium/Playwright Python dipasang pada image worker saja; sandbox diwajibkan aktif. Startup normal tetap satu perintah Compose dan tidak melakukan probe/reset otomatis. Worker kini memiliki cap 1 GiB RAM/256 PID, tmpfs 256 MiB dan shared memory privat 128 MiB. Build awal mengunduh browser/dependensi dan dapat memerlukan waktu/ruang disk lebih besar.

Saat tidak ada run lain, jalankan secara eksplisit:

```powershell
.\.venv\Scripts\python.exe -m evaluator.m4
# Pemeriksaan ulang bagian cancel saja, bila diperlukan:
.\.venv\Scripts\python.exe -m evaluator.m4 --cancel-only
```

Evaluator mendaftarkan izin development browser melalui versi scope, me-reset data lab sintetis, menguji XSS-08 rentan/perbaikan dengan marker lokal/kontrol inert, jaringan serta cancel, lalu mengembalikan BAC/XSS ke fixed. Tidak mengubah report/evidence/ledger lama. Browser tidak mendapat URL/script/eval bebas dari report, key model, GT/reset atau akses jaringan umum.

Runner M4a tetap jalur operator dengan assessment null. Sejak M4b UI juga menyediakan XSS fixture tetap melalui workflow produk; raw JSON/PNG hanya admin. Hunter menerima ringkasan tetap setelah review/publikasi. Readiness `lab_tools=HTTP_AND_BOUNDED_NOTIFICATION_BROWSER` menyatakan profil tersedia, bukan izin melewati scope/dirty gate. [Hasil M4b](docs/m4b-verification.md) mencatat perbaikan request tambahan dan future route saat cancel.

### Demo UI XSS development M4b

Saat tidak ada run aktif, operator mendaftarkan profil/scope dan menyiapkan lab sintetis secara eksplisit:

```powershell
.\.venv\Scripts\python.exe -c "from evaluator.m2 import operator; print(operator('register_browser'))"
.\.venv\Scripts\python.exe -m evaluator.m2 reset --condition fixed --xss-condition vulnerable
```

Login hunter, buat/kirim laporan, tekan **Validasi snapshot**, pilih **XSS · pratinjau notifikasi (fixture tetap)** lalu mulai. Empat probe memakai delapan request termasuk login, 20 operasi browser logis dan satu panggilan mock Rp0. Admin meninjau bukti JSON inert lalu **Review hasil → Bagikan ringkasan**. Hunter mendapat verdict/ringkasan setelah publikasi; raw DOM/PNG/catatan tetap privat. Reset operator diperlukan sebelum run berikutnya; gunakan `--xss-condition fixed` untuk kondisi perbaikan. Register tidak dilakukan pada setiap startup.

Smoke eksplisit: `python -m evaluator.m4b`, `python -m evaluator.m4b --cancel-only` atau `python -m evaluator.m4 --network-only` sesuai kebutuhan. [QA UI host](scripts/m4b_ui_smoke.cjs) memerlukan playwright-core/Chromium yang sudah tersedia. Kuota start tetap berlaku; runner mereset hanya lab dan mempertahankan riwayat/ledger aplikasi. [Perintah, hasil dan kegagalan awal](docs/m4b-verification.md).

## Batas yang sudah dikonfirmasi

| Bagian | Pilihan |
| --- | --- |
| Pengembang | Solo, sekitar 3 jam/hari selama 10 hari kerja |
| Stack | Python + FastAPI |
| Target | Portal pengadaan/logistik buatan sendiri, data sintetis |
| UI/platform | Chat dan upload TXT/MD; satu program; role bug hunter/admin dari server |
| Scope | Guideline admin terversi; gate backend sebelum worker mengakses Docker internal |
| Kapabilitas sasaran | BAC/IDOR, XSS, file upload, business logic |
| Model awal | Qwen3-Coder melalui OpenRouter |
| Provider cadangan rencana | Gemini direct Free Tier; OpenAI Platform API dan xAI/Grok opsional, akses/billing belum siap |
| Budget total API | Maksimal Rp50.000; key belum tersedia |
| Pengembangan awal | Adapter mock yang diberi label jelas |
| Dataset evaluasi utama | 20 laporan berbeda, 10 valid dan 10 tidak valid setelah verifikasi manual |
| Target kerentanan lab | 24 titik target; BAC-08 dan XSS-08 development direproduksi operator, 22 lainnya masih spesifikasi |
| Pembuat laporan | Asisten menyusun 20 draf setelah lab siap; GT diverifikasi pengguna |

Model utama diakses lewat API dan tidak dijalankan di laptop. Koneksi API eksternal berarti aplikasi belum sepenuhnya offline. Setiap hasil mock akan diberi label dan tidak dihitung sebagai benchmark model live.

## Dokumen pengembangan

- [Rencana dan milestone](plan.md)
- [PRD, tech stack, container dan database](prd.md)
- [Daftar Azure for Students dan cek akses Foundry](docs/azure-students.md)
- [Aturan kerja asisten coding](AGENTS.md)
- [Arsitektur dan kontrak komponen](docs/architecture.md)
- [Runtime, antrean, penyimpanan dan batas resource](docs/runtime.md)
- [Hasil audit dokumentasi dan dependensi terbuka](docs/documentation-audit.md)
- [Prompt handoff dan eksekusi M1 di chat baru](docs/execution-prompt.md)
- [Review keamanan dan pengujian yang belum dijalankan](docs/security-review.md)
- [Desain UI dan label hasil](docs/design.md)
- [Pemilihan 11 referensi desain](docs/design-references.md)
- [Review UI, pemeriksaan browser dan status persetujuan](docs/ui-review.md)
- [Prototipe UI lokal dan cara membuka](ui-prototype/README.md)
- [Alur pengguna dan kondisi gagal](docs/user-flow.md)
- [Implementasi bertahap dan checkpoint](docs/implementation.md)
- [Spesifikasi portal lab](docs/lab-spec.md)
- [Peta 24 titik kerentanan dan fitur](docs/lab-vulnerabilities.md)
- [Dataset, ground truth, dan evaluasi](docs/evaluation.md)
- [Draf isian pendaftaran](docs/registration.md)
- [Penyelarasan rulebook dan S&K](docs/rules-alignment.md)
- [Checklist submission](docs/submission-checklist.md)
- [Rencana distribusi GitHub tanpa live web](docs/distribution.md)
- [Deklarasi komponen dan atribusi](docs/third-party.md)
- [Sumber PDF dan provenance](docs/sources/README.md)

`AGENTS.md` mengatur pekerjaan pada repositori. Instruksi agent dalam produk akan disimpan terpisah saat implementasi.

## Alur produk yang dituju

1. Bug hunter/admin login, memilih satu program dan chat/unggah report TXT/MD.
2. Guideline aktif ditetapkan admin terpisah dari report; backend memeriksa scope, izin dan prasyarat. OOS/UNKNOWN tanpa akses target.
3. Setelah lolos, agent merencanakan HTTP/browser dan kontrol pada portal Docker internal yang sudah berjalan.
4. Worker menjalankan tindakan yang lolos policy per aksi; tidak membuat container target baru per report.
5. Verifier memeriksa dampak/kontrol untuk `CONFIRMED`, `REFUTED`, atau `INCONCLUSIVE`.
6. Admin meninjau bukti internal dan membagikan hasil tersanitasi. Bug hunter hanya melihat laporan sendiri; ekspor mengikuti izin yang sama.

Keberhasilan menjalankan PoC tidak otomatis membuktikan dampak. Kegagalan reproduksi atau penolakan model juga tidak otomatis membuat report tidak valid.

## Budget dan akses model

Biaya token yang rendah berbeda dari minimum pembelian kredit. [Terms OpenRouter](https://openrouter.ai/terms), diperiksa 3 November 2026, mencantumkan minimum pembelian USD 5 per transaksi. Biaya rupiah checkout dan fee aktual perlu diperiksa terhadap batas Rp50.000 sebelum mengaktifkan pemakaian berbayar.

Terms tersebut juga mensyaratkan usia minimal 18 tahun; pengguna sudah mengonfirmasi 18+ pada 3 November 2026. Ini menyelesaikan syarat usia, bukan kesiapan key atau budget. Target A/B adalah 40 run untuk 20 laporan, dengan kemungkinan banyak panggilan model per run B; perhitungan biaya mengikuti [rancangan evaluasi](docs/evaluation.md).

Tier gratis tidak menjamin model pilihan tersedia atau kuotanya cukup. Pengembangan mock tetap dapat dilanjutkan tanpa key; benchmark model live menunggu akses yang benar-benar tersedia. Tidak ada pembelian atau pemanggilan model berbayar yang dilakukan pada tahap dokumentasi.

Rencana provider diperluas pada 4 November 2026 di [PRD](prd.md): Gemini direct menjadi kandidat cadangan gratis; OpenAI Platform API dan xAI/Grok tetap opsional dengan billing yang diperiksa sendiri. Plus/Codex tidak otomatis memberi kredit Platform API. Sign in with ChatGPT merupakan jalur resmi lain untuk plan pengguna yang eligible dan memerlukan integrasi/consent tersendiri; belum tersedia pada produk. Status akses bersumber pada dokumentasi primer yang ditautkan PRD, bukan pemeriksaan akun privat.

Fallback dicatat dan hanya boleh sebelum respons sukses pertama/aksi target; setelah itu provider terkunci. Quota/kredit habis hanya dialihkan ke profil gratis terverifikasi yang sudah dikonfigurasi, tanpa otomatis berbayar. Benchmark mematikan fallback agar hasil model/provider tidak tercampur. Jumlah container tetap tiga.

## Urutan implementasi

Mulai dari kontrak data dan satu alur BAC lengkap: target lab, dua akun, kondisi rentan/perbaikan, worker HTTP, kontrol, evidence, serta hasil yang dapat diperiksa. Integrasi model live menyusul setelah alur tools berfungsi dan akses API siap.

Fondasi M1, worker/lab M2, alur BAC/UI M3, integrasi XSS-08 M4b dan tujuh fitur XSS lab M4c tersedia. M4 selesai teknis lokal; berikutnya M5 upload. Lima belas titik lab kategori lain masih pending. Model live menunggu key/budget dan tahap terkait.

## Hasil evaluasi

Belum tersedia. Akurasi, precision, recall, coverage, biaya, dan penghematan waktu akan diisi dari eksperimen aktual sesuai [prosedur evaluasi](docs/evaluation.md).

## Kelengkapan lomba

Keputusan submission: **Link Karya berupa repo GitHub publik**, berisi source/paket versi rilis, petunjuk menjalankan lokal dan tautan video/slide. Tidak membuat live web, GitHub Pages atau VPS untuk jalur ini. Repo publik sudah tersedia pada URL di atas; push awal diotorisasi untuk dokumentasi dan UI. Release aplikasi belum dibuat. Video YouTube, slide publik, thumbnail serta screenshot tetap diisi terpisah pada platform.

Deadline dari kedua PDF adalah **15 November 2026 pukul 23:59 WIB**. Paket submission menyiapkan link karya yang dapat dicoba, thumbnail 1200 x 630 px maksimal 500 KB, screenshot maksimal lima, video YouTube maksimal 10 menit, slide, serta dokumentasi teknis. AI merupakan bagian tema/rubrik; kemampuan model perlu ditunjukkan secara nyata, sementara mock selalu diberi label. Daftar lengkap dan perbedaan dokumen ada pada checklist di atas.
