# Lab Docker untuk verifikasi manual

Status **14 November2026**: **http://127.0.0.1:8001/** membuka service/database yang sama dengan target worker `lab:8001`. Pilihan admin **Lab rentan / Lab kontrol diperbaiki** kini mengatur seluruh13 titik existing BAC-08/XSS-01..08/UP-01..04, termasuk pencarian katalog. Ini memperbaiki cakupan reset sebelumnya yang hanya3 titik produk, serta menggantikan salinan terpisah8001. Bukti manual tetap perlu dicatat terikat snapshot; tidak otomatis menjadi evidence run atau GT manusia yang diterima.

**Hasil terbaru:**23 tes terarah lulus; tombol UI sudah diuji fixed lalu vulnerable dengan13 flag cocok dan snapshot port8001 sama. Teks inert pada hasil pencarian katalog mengikuti mode; parameter view=text tetap kontrol aman. Kondisi akhir rentan/sesi manual aktif. Setelah reset, login ulang dan masukkan ulang data/payload karena seed/ID/sesi lab diganti. [Bukti dan batas pemeriksaan](lab-reset-ui.md#cakupan-seluruh-titik-existing-14-november-2026).

## 1. Login dan objek uji

1. Di ValVuln8000 sebagai admin, buka **Reset data lab**, pilih kondisi dan terapkan/reset. Klik **Aktifkan pengujian manual**, lalu tautan **Buka lab manual di port8001**. Aktivasi tidak mengganti data/kondisi; agent dikunci maintenance selama sesi ini.
2. Pilih akun `requester-a` atau `requester-b`. Password masing-masing tersedia pada file privat `.local-data/secrets/lab-accounts.json`; nilainya tidak disalin ke dokumen/source/chat.
3. Tekan Login, lalu **Lihat ID objek akun ini**. Respons memuat ID permintaan, lampiran, barang katalog dan pemasok yang dimiliki akun tersebut.
4. Buka halaman contoh melalui tautan. Route yang membutuhkan ID menggunakan ID dari akun yang sesuai. Login akun kedua melalui profil/incognito browser terpisah bila perlu membandingkan dua aktor.
5. Untuk request mutasi manual, pertahankan cookie sesi, `Origin: http://127.0.0.1:8001` dan `X-CSRF-Token` dari respons login. Sesi lab berlaku lima menit; login ulang bila kedaluwarsa.

`GET /manual/objects` memerlukan login dan sesi manual admin aktif; respons menampilkan snapshot_id yang sama dengan target worker serta purpose SHARED_WORKER_TARGET. Root/login tidak mengaktifkan sesi admin dengan sendirinya. Jika MANUAL_SESSION_REQUIRED/409, aktifkan kembali dari panel admin. Sesi manual berlaku1jam, sementara cookie akun lab lima menit. Selesai menguji, gunakan **Terapkan kondisi & reset data lab** untuk mencabut sesi dan membuka validasi kembali; ID objek berubah. Kedaluwarsa sesi tidak otomatis membuka validasi agent.

## 2. Kerentanan yang sudah diimplementasikan

Katalog mencatat **13 titik dengan reproduksi operator historis**. Salinan lama mengaktifkan13 titik pada13 November; volume itu tetap disimpan dan kini berhenti. Tombol admin pada target bersama8001 sekarang mengatur seluruh13 kondisi pada tabel. Kontrol pembanding seperti pencarian view=text tetap escaped meskipun mode rentan. Kapabilitas otomatis tetap3 subtype produk; flag mode/laporan tes tidak mengesahkan GT atau menyatakan reproduksi eksploitasi13 titik telah diulang.

| ID | Fitur dan route aktual | Perilaku rentan yang tersedia | Kontrol pembanding |
| --- | --- | --- | --- |
| BAC-08 | Lampiran: `GET/DELETE /api/attachments/{attachment_id}` | Pemeriksaan pemilik dapat hilang pada penghapusan lampiran | Pembacaan lampiran tetap milik pemilik; kondisi fixed memeriksa pemilik saat delete |
| XSS-01 | `GET /catalog/search?q=...` | Query ditempatkan pada konteks HTML hasil pencarian | `view=text` menampilkan teks yang di-escape |
| XSS-02 | `PATCH /api/catalog/items/{item_id}/note`, `GET /catalog/items/{item_id}` | Catatan katalog tersimpan dirender sebagai HTML | Field `description` di-escape |
| XSS-03 | `PATCH /api/requests/{request_id}/reason`, `GET /requests/{request_id}/review` | Alasan permintaan dirender sebagai HTML pada halaman review | Tampilan audit/teks pembanding di-escape |
| XSS-04 | `PATCH /api/profile/display-name`, komentar pada `/api/requests/{request_id}/comments` dan `/requests/{request_id}/comments` | Nama tampilan komentar dirender sebagai HTML | Isi komentar/field teks pembanding di-escape |
| XSS-05 | `PATCH /api/suppliers/{supplier_id}/name`, `GET /suppliers?supplier_id=...` | Nama pemasok dirender sebagai HTML | Field kode pemasok di-escape |
| XSS-06 | `GET /tracking?ref=...` | Referensi masuk ke konteks atribut HTML | Tampilan pembanding mengodekan konteks atribut |
| XSS-07 | `GET /requests/view` dengan fragmen URL | Fragmen mencapai sink DOM HTML | Tampilan pembanding memakai teks |
| XSS-08 | `GET /notifications/preview` dengan fragmen URL | Pratinjau memakai sink `innerHTML` pada kondisi rentan | Kondisi fixed memakai `textContent` |
| UP-01 | Upload melalui `POST /api/attachments`, preview `/attachments/{upload_id}/preview` | SVG sintetis dapat disajikan aktif pada origin lab | `/attachments/{upload_id}/download` menyajikan attachment |
| UP-02 | Upload melalui API yang sama, `/documents/{upload_id}/preview` | HTML sintetis dapat disajikan aktif pada origin lab | `/documents/{upload_id}/text` adalah viewer teks |
| UP-03 | `POST /api/attachments` | Nama berkas yang sama dapat memakai namespace penyimpanan bersama dan menimpa isi objek lain | Kondisi fixed memakai kunci penyimpanan unik |
| UP-04 | `/api/requests/{request_id}/attachments`, `/requests/{request_id}/attachments` | Nama lampiran dirender sebagai HTML pada daftar | `/requests/{request_id}/attachment-labels` menampilkan label aman |

API upload lab menggunakan JSON terstruktur dengan `request_id`, `filename`, `media_type` dan `content_base64`, maksimal 1.024 byte konten sintetis. Ini berbeda dari upload laporan TXT/MD pada aplikasi ValVuln. Rincian implementasi berada di `lab/uploads.py`, `lab/xss_catalog.py` dan `lab/main.py`.

**Yang dilewati:** BAC-01..07 dan BL-01..04 tetap DEFERRED/PLANNED. Kontrol bisnis aman yang ada tidak dihitung sebagai empat kerentanan BL yang sudah diterapkan. Jangan menganggap nama route rencana pada dokumen lama berarti celah tersebut tersedia.

Kemampuan produk otomatis saat ini hanya subtype **BAC-08, XSS-08 dan UP-04**. Titik lain pada tabel merupakan fitur lab untuk verifikasi operator. Jumlah titik bukan jumlah akar masalah independen; grouping historis tetap ada di [peta lab](lab-vulnerabilities.md).

## 3. Isolasi dan pengoperasian

| Bagian | Nilai |
| --- | --- |
| Project Compose | `kartikahackathon` |
| File Compose | [compose.yaml](../compose.yaml) |
| Container | `kartikahackathon-lab-1` |
| Port | `127.0.0.1:8001` saja |
| Volume target bersama | `kartikahackathon_lab_data` |
| Volume salinan lama, dipertahankan | `valvuln_manual_lab_data_20261113`, service berhenti |
| Origin manual | `http://127.0.0.1:8001` |
| Akun/isi | Dua akun dan data sintetis target worker yang sama |

```powershell
# Startup normal, tidak mereset data atau membuka sesi manual otomatis
docker compose up -d --build
```

Lab tetap mempunyai IP internal worker172.30.74.3 dan network tambahan lab_manual_access untuk publish loopback8001. Bootstrap menolak koneksi keluar baru/forwarding dan menurunkan Uvicorn keUID10001 tanpa capability. App tidak masuk network target; API model/key, app DB, Docker socket dan GT tidak dipasang pada lab. Salinan lama tidak dijalankan normal. [Compose salinan](../compose.manual-lab.yaml) disediakan hanya opsional pada8002; jika operator membutuhkannya, rebuild eksplisit diperlukan untuk origin/port baru. Kondisinya terpisah dari tombol admin.

Origin manual opt-in LAB_MANUAL_ORIGIN dengan LAB_SHARED_MANUAL dan kanal kontrol privat; worker tetap memakai http://lab:8001. Origin asing/mutasi tanpaCSRF ditolak. Peer worker dikenali melalui IP internal tetap, bukan header Host/Origin. Request manual selain root/health membutuhkan sesi aktif terikat snapshot; reset menunggu handler manual yang masih berjalan. Worker tetap tidak memperoleh kontrol reset/sesi manual.

## 4. Riwayat salinan awal13 November2026

- [Helper persiapan](../scripts/prepare_manual_lab.py) membaca database dan WAL dari volume asal saat lab asal berhenti, memakai backup SQLite ke volume manual baru dan memeriksa hash source tetap sama. Helper menolak menimpa DB manual yang sudah ada.
- Snapshot salinan saat dibuat: `fc21167a-402c-459b-80b2-a027bf94ba4d`. Perubahan manual selanjutnya perlu dicatat oleh operator bila hendak dijadikan bukti.
- Pemeriksaan runtime lulus: halaman utama/health/login, endpoint ID objek, pencarian, notifikasi dan pemasok dengan parameter yang benar merespons 200; Origin asing ditolak.
- Proses Uvicorn berjalan sebagai UID 10001 dengan permitted/effective/bounding capability nol; koneksi keluar TCP baru ditolak.
- **7 tes akses terarah lulus** pada database sementara, termasuk lab default yang menolak Origin manual dan tidak mempunyai endpoint manual, isolasi ID objek serta CSRF.
- Percobaan salinan awal gagal karena akses SQLite WAL pada mount read-only; artefak volume awal dipertahankan. Bridge internal awal tidak mempublikasikan port host; konfigurasi diganti bridge khusus dengan firewall egress sebelum dinyatakan dapat diakses.

Hasil pemeriksaan disimpan privat pada `artifacts/backend-audit-20261113/`. Tidak ada klaim seluruh celah direproduksi ulang, GT disahkan, benchmark berjalan atau target asli direset oleh pembukaan akses ini.

## 4a. Akses bersama14 November2026

28 tes terarah lulus31,34detik: role/CSRF/idle, sesi manual aktif/kedaluwarsa/snapshot salah, jalur worker, revokasi saat reset, lock handler manual, dua mode/reset/anti-replay serta akses manual legacy. Smoke UI menerapkan vulnerable lalu fixed, mengaktifkan sesi manual dan login dua akun di8001. Snapshot dan objek akun yang dibaca manual cocok dengan status target worker pada kedua mode. Halaman pratinjau memakai innerHTML saat vulnerable dan textContent saat fixed; hanya teks inert diuji, tidak mengeksekusi payload/script uji.

14 tabel aplikasi yang diperiksa termasuk68 baris ledger identik sebelum/sesudah. Jalur health worker keIP pinned172.30.74.3 tetap OK, UID lab10001 dan koneksi keluar baru diblok. Salinan lama berhenti tanpa volume dihapus. Kondisi akhir fixed dengan sesi manual aktif, target maintenance/dirty dan worker IDLE; ini penguncian yang disengaja sampai admin reset, bukan kegagalan kesiapan. Tidak ada inferensi model, exploit, run validasi baru atau pengesahan GT.

Artefak privat: `artifacts/shared-manual-lab-20261114/targeted.xml`, `ui-smoke.json`, screenshot admin, `before.json` dan `preservation.json`. OpenAPI diperbarui; source belum di-push/rilis. Snapshot/ID berubah jika pengguna melakukan reset lagi.

## 5. Cek XSS-08 manual dan kendala popup

Pada akses bersama sekarang, pilih kondisi lalu **Aktifkan pengujian manual** di admin sebelum login dan mencoba URL. Mode rentan memakai sink HTML; kontrol diperbaiki menampilkan payload sebagai teks. Setelah setiap reset, sesi manual perlu diaktifkan lagi dan akun lab perlu login ulang. Riwayat pengujian browser berikut dilakukan pada salinan lama, bukan bukti otomatis untuk snapshot baru.

Login pada origin yang sama `http://127.0.0.1:8001/`, lalu buka URL berikut dan reload halaman setelah URL berubah:

```text
http://127.0.0.1:8001/notifications/preview#%3Cimg%20src%3D%22data%3A%2C%22%20onerror%3D%22alert%28%27ValVuln-XSS%27%29%22%3E
```

Pada kondisi rentan, popup `ValVuln-XSS` berasal dari event handler elemen yang dimasukkan melalui fragment URL. Halaman membaca fragment hanya saat load; navigasi yang hanya mengubah hash pada tab yang sudah terbuka tidak mengeksekusi sink lagi. Gunakan reload/Ctrl+Shift+R. Jika halaman berisi HTTP401, login ulang; sesi berlaku lima menit. Pertahankan hostname127.0.0.1 yang sama dengan halaman login.

Kontrol inert: `/notifications/preview#Kontrol-inert-ValVuln`, lalu reload; teks tampil tanpa popup. Pada14 November2026, Chromium host menguji kedua akun pada salinan manual: kontrol tanpa alert, perubahan hash saja tanpa alert, reload payload menghasilkan alert pada masing-masing akun. Bukti privat: `artifacts/manual-check-20261114/browser-xss08.json`. Pemeriksaan ini tidak mengubah target worker, kondisi lab, GT atau ledger dan tidak melakukan inferensi model. Hasil salinan manual tidak otomatis menjadi bukti run produk.
