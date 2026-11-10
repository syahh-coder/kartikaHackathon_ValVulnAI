# Hasil M4c lokal - 5 November 2026

Status: **M4 selesai teknis lokal**. Tujuh titik tambahan XSS-01 sampai XSS-07 lulus dua kondisi/kontrol Chromium; XSS-08 dan workflow/UI development tetap berdasarkan M4a/M4b. Suite host akhir **180 passed in 235.86s**, tanpa skip. M5 belum dimulai.

## Lingkup dan pemisahan produk

M4c melengkapi tujuh titik lab XSS-01 sampai XSS-07. Alur produk/UI tetap mendukung XSS-08 development dengan fixture tetap sesuai [hasil M4b](m4b-verification.md). Rute baru tidak didaftarkan pada profil/scope planner produk, tidak dipakai untuk tuning, dan tidak otomatis memperoleh assessment. Tes memastikan BrowserArguments dan planner development menolak ketujuh rute itu. Ini membedakan kelengkapan lab M4 dari cakupan validator/model live.

Migrasi SQLite `002_xss_catalog.sql` menambah data katalog, alasan, komentar, pemasok, nama tampilan dan penugasan reviewer. Migrasi startup mempertahankan objek/snapshot lama tanpa seed/reset/panggilan target. Data baru dibuat melalui reset evaluator eksplisit. Akun requester-b mendapat penugasan baca review untuk permintaan sintetis requester-a; kepemilikan lampiran privat tidak berubah. Menulis catatan/alasan/pemasok/komentar tetap memerlukan pemilik, session, Origin dan CSRF. Nama tampilan hanya dapat diubah pemilik session, tanpa input role.

## Titik, konteks dan kontrol

| Titik | Input dan tampilan aktual | Kontrol yang selalu inert | Grup akar masalah konservatif |
| --- | --- | --- | --- |
| XSS-01 | `q` pada GET `/catalog/search`, HTML reflected | `view=text`, input identik di-escape | html-element-output |
| XSS-02 | PATCH `/api/catalog/items/{id}/note`, GET `/catalog/items/{id}` oleh akun lain | `field=description`, teks tersimpan di-escape | html-element-output |
| XSS-03 | PATCH `/api/requests/{id}/reason`, GET `/requests/{id}/review` oleh reviewer ditugaskan | `view=audit`, alasan di-escape | html-element-output |
| XSS-04 | PATCH `/api/profile/display-name`, POST komentar, GET `/requests/{id}/comments` oleh akun lain | `field=body`, isi komentar di-escape | html-element-output |
| XSS-05 | PATCH `/api/suppliers/{id}/name`, GET `/suppliers?supplier_id=...` oleh akun lain | `field=code`, nilai kode di-escape | html-element-output |
| XSS-06 | `ref` pada GET `/tracking`, konteks atribut value berpetik ganda | `view=text`, encoding atribut mempertahankan nilai input utuh | html-attribute-output |
| XSS-07 | Fragmen URL pada GET `/requests/view`, DOM innerHTML | `view=text`, textContent | dom-fragment-innerhtml |

Tiap titik mempunyai handler/input/state sendiri. Pengelompokan di atas sengaja konservatif: XSS-01 sampai XSS-05 tidak dihitung sebagai lima sampel akar masalah independen. XSS-07 dan development XSS-08 satu keluarga DOM fragment/innerHTML; XSS-07 tetap non-benchmark. Pemeriksaan grup final dan GT manusia tetap M7, sebelum freeze/hasil model. Tidak ada perubahan target 24 titik atau 20 laporan 10/10.

## Cara verifikasi operator

Evaluator host menolak mulai saat ada antrean/run aktif, lalu menempatkan target dalam maintenance. Chromium operator dijalankan lewat Docker exec pada namespace worker yang idle, dengan UID 10001, profil sandbox/egress yang sama. Source probe dan mapping tetap dari repositori dikirim sementara melalui stdin; tidak disalin ke image, handoff tool, konteks model atau artefak produk. Tidak mengirim label kondisi/GT ke proses browser. Ini jalur operator berwenang yang terpisah dari `Worker.service`, bukan perluasan izin agent untuk menjalankan script report atau terminal.

Untuk tiap titik, evaluator memilih kondisi rentan lalu perbaikan melalui CLI lab. Hanya satu titik baru yang rentan per snapshot; BAC dan XSS-08 tetap fixed. Tiap kondisi menjalankan tiga browser context baru: input inert, marker nonce lokal, dan marker baru melalui tampilan kontrol aman. Untuk stored XSS, input benar-benar disimpan melalui HTTP oleh requester-a; requester-b login terpisah kemudian membaca halaman tanpa payload pada URL. Cookie/storage konteks awal kosong dan kontrol JavaScript harus berhasil.

Semua navigasi browser dimediasi HTTPX ke IP lab literal. Hanya satu GET dokumen utama tepat yang boleh diteruskan per aksi; redirect, subresource, popup, WebSocket dan download diblokir. Query dibangun operator dari fixture tetap dan UUID objek yang divalidasi. Tidak ada script/URL/locator/eval kiriman report. Marker berupa callback lokal tanpa akses data atau callback jaringan. Batas 30 detik per fixture, tiga fixture per kondisi, maksimal 1 MiB dokumen dan 256 KiB PNG; satu probe operator aktif. Batas produk tidak dinaikkan.

Bukti privat mencakup run/action/evidence/snapshot ID, identitas writer/reader, method/path dan hash input/response mutasi, event nonce/origin/frame/path, kontrol JS/storage/teks, DOM inert, PNG dan hash serta log jumlah request lab. Capture disimpan sebelum assertion hasil. Bukti operator tidak masuk ledger/verdict produk, kuota start pengguna atau hasil benchmark. Password, CSRF dan cookie mentah tidak disimpan ke artefak.

## Hasil dan artefak

- 180 tes host lulus: 24 tes baru mencakup kedua kondisi tujuh titik, CSRF/ownership/reviewer/schema/batas input, pemisahan tool/planner, migrasi database lama dan reset. Tes host tanpa transport eksternal; bukti eksekusi berasal dari Chromium Docker.
- Pemeriksaan Chromium: **14 fase kondisi lulus, 42 context/capture/PNG, 138 request lab aktual**. Tujuh marker kondisi rentan dieksekusi pada main frame/origin/path yang benar; 35 capture lain tidak mengeksekusi marker dan mempertahankan teks/nilai input. Stored XSS-02..05 dibaca requester-b sesudah HTTP write requester-a. Setiap kondisi memiliki kontrol inert dan jalur aman.
- Manifest tujuh titik lengkap, hash source lab cocok; akhir runner semua kondisi fixed, nol request setelah reset, worker IDLE/bersih dan nol proses Chromium. Screenshot kondisi fixed XSS-03 juga ditinjau visual sebagai teks inert. Bukti UI produk tetap hasil M4b karena UI/app/worker produk tidak berubah pada M4c.
- Regresi jaringan XSS-08 pada lab baru **PASS**, run `8e598164-8fb4-42d9-b8ad-8fb52b5cd63c`: lima request, satu WebSocket, satu popup dan satu download diblokir. Hanya empat request login/preview mencapai lab, storage baru pada aksi berikutnya, nol Chromium tersisa. Artefak `artifacts/m4/network-verification.json`; tidak menjalankan ulang kuota start UI atau model.
- Artefak privat di `artifacts/m4c/`: `*-verification.json`, capture per titik/kondisi dan PNG per evidence ID. `catalog-manifest.json` menggabungkan hasil lulus dengan hash source lab yang cocok dan tetap mencantumkan percobaan gagal.
- Manifest mencatat hash source implementasi/evaluator dan ID image app/worker/lab. Tidak menambah dependensi Python, Chromium, OS atau service baru; inventaris [M4a](dependencies-m4.json) tetap berlaku.
- Pemeriksaan penutup: 30 Markdown/232 link lokal/fence dan sintaks Python lulus; `git diff --check` lulus. `artifacts/m4c/final-state.json` merekam binding ready/maintenance=false/dirty=false dengan snapshot sama seperti worker, seluruh kondisi fixed, nol request setelah reset/nol Chromium. Readiness: app ready, worker IDLE, lab OPERATOR_VERIFIED dan live_provider CONFIGURATION_REQUIRED.

Percobaan pertama XSS-01 berhenti TimeoutError sebelum menghasilkan capture. Artefak `20261105T131908Z-verification.json` tetap FAILED, nol assessment, dan cleanup mengembalikan target fixed/bersih. Tidak menyatakan timeout sebagai REFUTED. Setelah penambahan diagnostik tahap, pengujian XSS-01 yang diulang meluluskan kedua kondisi. Akar penyebab timeout pertama belum dibuktikan; suite host sempat berjalan bersamaan, tetapi itu bukan bukti penyebab.

Tes terarah awal gagal karena seed baru menyebut kolom `unit_id`, sementara schema lama memakai `unit`. Nama kolom seed diperbaiki tanpa mengubah data/schema lama; 40 tes terarah kemudian lulus, diikuti suite 180 tes di atas. Hasil lulus tidak menghapus kegagalan percobaan sebelumnya.

## Menjalankan ulang

Sesudah setup/seed dan startup Compose normal, saat tidak ada run lain:

```powershell
.\.venv\Scripts\python.exe -m evaluator.m4c
# Ulangi hanya titik terkait bila ada kegagalan/perubahan:
.\.venv\Scripts\python.exe -m evaluator.m4c --point XSS-03
```

Evaluator hanya mereset database sintetis lab, mempertahankan riwayat/evidence/ledger aplikasi, dan mengembalikan seluruh kondisi ke fixed sebelum release maintenance. Bila Chromium belum tertutup atau cleanup gagal, target tidak dinyatakan siap. Startup normal tidak menjalankan evaluator atau reset. Mapping/manifest bug tidak dibundel ke worker/app image; Docker exec operator eksplisit memerlukan akses host Docker.

Model live, GT manusia, benchmark, 15 titik lab kategori lain dan rilis/submission masih pending. Langkah berikutnya setelah M4 ditutup adalah M5 upload; tidak memulainya dalam batch M4 ini. Seluruh perubahan lokal, tanpa commit/push/deployment.
