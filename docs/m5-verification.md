# Hasil M5 lokal - 5 November 2026, audit ulang 6 November

Status: **M5 selesai teknis lokal**, ditutup 6 November 2026 setelah audit artefak runtime 5 November. Suite host sebelumnya **205 passed in 193.58s**, tanpa skip; pemeriksaan ulang batch ini **27 tes terarah lulus** (15 defensif M5 dan 12 auditor offline). Suite penuh tidak diulang pada batch audit. Model tetap mock; belum ada hasil model live, GT dataset manusia atau benchmark.

## Perubahan dan batas alur produk

Lab menambah empat titik upload dengan kondisi evaluator terpisah melalui migrasi `003_uploads.sql`: blob berukuran kecil dalam SQLite, metadata upload/owner/request dan renderer preview/label. Tidak menulis nama berkas kiriman ke filesystem. Konten maksimum 1.024 byte, nama maksimum 256 karakter, tiga media type terdaftar dan maksimal 64 upload sintetis per reset. Input base64/ukuran/nama/CSRF/Origin/session/kepemilikan diperiksa; tipe eksekusi server tidak tersedia. Startup hanya memigrasi schema, tanpa reset, upload, browser atau model otomatis.

Alur produk development **UP-04** tersedia melalui API/UI untuk satu klaim nama lampiran pada `/requests/{id}/attachments`. Planner tetap deterministik/mock: upload fixture teks inert oleh A -> baca nama melalui browser B -> upload fixture teks dengan nama marker oleh A -> baca daftar B -> baca label aman B. B harus ditugaskan pada permintaan A. Isi file selalu teks tetap milik aplikasi, bukan lampiran/script laporan. Dua upload menghasilkan ID berbeda. Kontrol hanya tampilan label, tidak menganggap isi teks aktif sebagai klaim yang diuji.

`UploadArguments` hanya menerima route POST permintaan UUID, akun A, ID fixture dan nonce aplikasi; tidak menerima filename, content, URL/script/header bebas. BrowserArguments menambah operasi daftar/label dengan path terdaftar, tanpa query/fragment. Model/tool tidak mendapat peta UP-01..03, source lab, label kondisi atau endpoint reset. Rute preview/penimpaan tambahan hanya dijangkau evaluator operator saat maintenance, bukan planner produk.

Handoff/backend/worker memeriksa scope setiap aksi: izin GET daftar saja tidak cukup; POST upload dan GET kontrol label juga wajib. Tiap aksi tetap maksimum dua request (login dan tindakan), browser 30 detik, upload 10 detik; satu run UP-04 memakai 10 request dan 15 operasi browser dalam cap lama 40 request/30 operasi/180 detik. POST fixture menandai target dirty sebelum I/O. Crash/cancel yang ambigu tidak memutar ulang upload; reset evaluator diperlukan. Trace upload selesai tetap ada bila browser berikutnya dibatalkan.

Verifier mengikat lima action/evidence ke claim, actor, nonce, file/request ID, snapshot/scope/epoch/boot, fingerprint envelope, hash observation dan waktu. Isi/hash/ukuran upload harus cocok dengan fixture tetap; dua upload tidak boleh memakai ID yang sama. CONFIRMED memerlukan event nonce pada main frame/origin/rute daftar, kontrol inert dan label aman, JS aktif, storage/context baru serta PNG valid. REFUTED memerlukan nama marker tampil sebagai teks dan semua kontrol lengkap. Bukti hilang/rusak, timeout dan hasil campuran tidak mendukung verdict tersebut. Verifier XSS-08 kini juga memeriksa operasi/rute eksplisit setelah perluasan kontrak browser.

Bukti mentah upload/browser/PNG tetap INTERNAL untuk admin dan disajikan sebagai teks inert. Review/publikasi memberi hunter ringkasan tetap tanpa nama mentah, nonce, ID/path, DOM/PNG, output model atau catatan analis. Override analis dan hasil mentah tetap terpisah. UI menambah pilihan upload dengan penjelasan fixture; tidak memberi opsi upload arbitrary code.

## Titik lab dan kontrol

| Titik | Dampak yang diperiksa | Kondisi perbaikan/kontrol | Grup sementara |
| --- | --- | --- | --- |
| UP-01, evaluasi | SVG upload disajikan inline pada `/attachments/{id}/preview` dan mengeksekusi marker di origin lab | Preview perbaikan berupa teks; download fixture yang sama memiliki Content-Disposition attachment/octet-stream/CSP sandbox dan diverifikasi sebagai event download browser, tanpa eksekusi | upload-active-content-origin |
| UP-02, non-benchmark | HTML upload disajikan aktif pada `/documents/{id}/preview` | Preview perbaikan dan `/documents/{id}/text` menampilkan isi identik sebagai teks | upload-active-content-origin |
| UP-03, non-benchmark | Upload A bernama sama mengubah isi upload B yang sudah ada melalui storage key bersama | Storage key UUID unik mempertahankan isi B; nama berbeda tidak mengubahnya. Download B oleh A tetap ditolak | upload-shared-filename-storage; tag sekunder BAC |
| UP-04, development | Nama upload dirender sebagai HTML aktif ketika reviewer B membaca daftar A | Kondisi escape dan `/requests/{id}/attachment-labels` menampilkan nama utuh sebagai teks | html-element-output; tag sekunder XSS |

UP-01/02 satu grup penyajian konten aktif, bukan dua akar masalah independen. **UP-04 development dan XSS-01..05 dikelompokkan konservatif sebagai html-element-output**. Karena development kini menyentuh grup yang sama, jangan menyatakan XSS-01..05 held-out independen. M7 harus meninjau/revisi alokasi atau implementasi sebelum freeze, sambil mempertahankan 20 laporan 10/10 dan target 24 titik; tidak mengganti kasus sesudah melihat hasil model. UP-01 tetap kandidat evaluasi upload dengan grup terpisah dari UP-04.

## Pemeriksaan aktual

- 205 tes host: kedua kondisi empat titik lab, isi/download/ownership, CSRF/schema/ukuran/path, tool/redirect/redaksi, alur produk/verdict/publikasi/ekspor dan bukti rusak, gate POST/kontrol sebelum transport, timeout/cancel/recovery tanpa replay. Transport HTTP luar dinonaktifkan pada suite; browser host disimulasikan untuk kontrak.
- Artefak runtime Chromium/API 5 November: `20261105T140236Z-verification.json` mencatat UP-04 dua kondisi, CONFIRMED/REFUTED, lima evidence dan 10 request per run. `20261105T140436Z-verification.json` mencatat UP-01..03 enam kondisi lulus. Browser aktual berasal dari Docker worker, bukan tes simulasi; audit 6 November tidak menjalankan ulang reproduksi.
- Auditor offline baru `scripts/audit_m5_artifacts.py`: delapan kondisi unik, 120 pemeriksaan hash source (60 file per manifest) dan 18 signature/hash PNG lulus. Memeriksa hasil tercatat, cleanup, keterikatan run QA, ekspor dan viewport. Menolak source berbeda/path keluar root, kondisi hilang/duplikat dan artefak rusak. Manifest lokal tidak bertanda tangan; kecocokan hash bukan autentikasi independen, GT manusia, atau reproduksi baru.
- QA UI ulang 6 November: pilihan upload/pergantian kategori, bukti admin inert, projection/ekspor hunter dan viewport 1366/1024/768/390/360 lulus; nol run/request target baru, error halaman dan request eksternal. Percobaan pertama gagal karena unduhan JSON `canceled`; pemeriksaan unduhan sintetis lokal dan satu pengulangan QA lulus tanpa perubahan kode aplikasi. Penyebab pembatalan pertama belum dipastikan; hasil gagal tetap tersimpan. Runner kini menampilkan pesan error pada stderr.
- Kondisi akhir diperiksa ulang secara read-only: tiga container berjalan, app/lab healthy; worker tanpa aksi aktif dan bersih; app ready, bukan maintenance, tanpa job QUEUED/LEASED. Snapshot app/worker/lab sama dan seluruh flag lab fixed. Pembacaan SQLite lab pertama memakai UID root gagal read-only; pembacaan memakai UID pemilik 10001 berhasil tanpa perubahan izin/data. Riwayat dan ledger tidak direset.
- Tes awal penolakan scope mencoba mengubah snapshot aktif dan ditolak trigger immutable. Tes diperbaiki untuk membuat/aktivasi versi baru melalui API admin, tanpa melemahkan trigger; 52 tes terarah kemudian lulus sebelum suite penuh.

## Menjalankan ulang dan artefak

Setelah setup/seed/startup normal dan tanpa run lain:

```powershell
# Audit bukti yang sudah tersimpan, tanpa Docker, koneksi jaringan atau reset:
.\.venv\Scripts\python.exe scripts/audit_m5_artifacts.py artifacts/m5/20261105T140236Z-verification.json artifacts/m5/20261105T140436Z-verification.json --ui-record artifacts/m5/ui-verification.json
# Reproduksi operator berikut adalah operasi terpisah dari audit offline:
.\.venv\Scripts\python.exe -m evaluator.m5
# Hanya bagian yang berubah/gagal; riwayat percobaan tidak ditimpa:
.\.venv\Scripts\python.exe -m evaluator.m5 --point UP-04
.\.venv\Scripts\python.exe -m evaluator.m5 --point UP-01 --point UP-02 --point UP-03
$env:VALVULN_PLAYWRIGHT_CORE='D:/ProjectWeb/webBisnisPadang/node_modules/playwright-core'
node scripts/m5_ui_smoke.cjs
```

Runner UP-04 membutuhkan dua start akun demo hunter-a dalam kuota yang berlaku, tidak menghapus/mengubah kuota. Titik lain operator saja, tanpa pemanggilan provider atau hasil assessment produk. Runner memeriksa idle/antrean, masuk maintenance sebelum reset/transport operator, mengembalikan semua kondisi ke fixed dan me-release snapshot baru sesudah nol Chromium. Cleanup yang gagal mempertahankan status belum siap. Hanya database lab sintetis yang direset; riwayat/ledger/evidence aplikasi dipertahankan.

Artefak privat di `artifacts/m5/`: hasil bertimestamp `*-verification.json`, capture operator per run, PNG per evidence ID, QA UI dan final-state. Capture mentah disimpan sebelum assertion; percobaan gagal dipertahankan. Manifest mencatat hash source dan image yang dipakai. Probe operator dikirim lewat stdin Docker exec pada worker idle, tidak disalin ke image/agent. Account secrets hanya dibaca untuk login, tanpa cookie/password/CSRF mentah pada ekspor. QA UI membuka run selesai tanpa start/request target baru.

Tidak menambah dependency Python/Chromium/OS atau service; inventaris M1/M2/M4a tetap berlaku. Seluruh perubahan lokal, tanpa commit/push/deploy/rilis/pemanggilan model live. Total 13 dari 24 titik mempunyai bukti operator tersimpan. Tahap berikutnya M6 business logic dan tujuh BAC yang tersisa; belum dimulai pada batch ini. Grouping UP-04/XSS HTML harus diselesaikan sebelum freeze M7/M8.
