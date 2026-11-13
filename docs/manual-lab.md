# Lab Docker untuk verifikasi manual

Status **13 November 2026**: salinan lab manual berjalan dan dapat dibuka di **http://127.0.0.1:8001/**. Ini target sintetis milik proyek untuk operator. Salinan terpisah dari portal `lab:8001` yang terdaftar pada worker; verifikasi manual di sini tidak otomatis menjadi bukti run/GT pada instance lain.

## 1. Login dan objek uji

1. Buka http://127.0.0.1:8001/.
2. Pilih akun `requester-a` atau `requester-b`. Password masing-masing tersedia pada file privat `.local-data/secrets/lab-accounts.json`; nilainya tidak disalin ke dokumen/source/chat.
3. Tekan Login, lalu **Lihat ID objek akun ini**. Respons memuat ID permintaan, lampiran, barang katalog dan pemasok yang dimiliki akun tersebut.
4. Buka halaman contoh melalui tautan. Route yang membutuhkan ID menggunakan ID dari akun yang sesuai. Login akun kedua melalui profil/incognito browser terpisah bila perlu membandingkan dua aktor.
5. Untuk request mutasi manual, pertahankan cookie sesi, `Origin: http://127.0.0.1:8001` dan `X-CSRF-Token` dari respons login. Sesi lab berlaku lima menit; login ulang bila kedaluwarsa.

`GET /manual/objects` hanya tersedia pada instance manual dan memerlukan login. Di lab default endpoint ini tidak terdaftar. Halaman awal adalah bantuan operator minimal; FE produk dikerjakan terpisah.

## 2. Kerentanan yang sudah diimplementasikan

Katalog mencatat **13 titik dengan reproduksi operator historis**. Kondisi masing-masing diaktifkan pada salinan manual tanggal 13 November. Pada batch ini yang diperiksa ulang adalah akses/login/route normal dan konfigurasi kondisi, bukan reproduksi eksploitasi ulang 13 titik. GT manusia tetap memerlukan verifikasi klaim yang relevan.

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
| Project Compose | `valvuln-manual` |
| File Compose | [compose.manual-lab.yaml](../compose.manual-lab.yaml) |
| Container | `valvuln-manual-manual_lab-1` |
| Port | `127.0.0.1:8001` saja |
| Volume salinan | `valvuln_manual_lab_data_20261113` |
| Volume asal | `kartikahackathon_lab_data`, hanya dibaca saat penyalinan |
| Origin manual | `http://127.0.0.1:8001` |
| Akun/isi | Dua akun dan data sintetis yang disalin dari lab proyek |

```powershell
# Menjalankan ulang salinan yang sudah disiapkan, tanpa reset data
docker compose -p valvuln-manual -f compose.manual-lab.yaml up -d

# Menghentikan akses manual, tanpa menghapus volume
docker compose -p valvuln-manual -f compose.manual-lab.yaml stop
```

Bootstrap manual menerima koneksi pada port 8001 yang dipublikasikan Docker di loopback, menolak koneksi keluar baru dan menurunkan proses Uvicorn menjadi UID 10001 tanpa capability. Network ini terpisah dari network worker. API model/key dan evaluator/GT tidak dipasang pada container manual.

Normalisasi Origin manual bersifat opt-in melalui `LAB_MANUAL_ORIGIN`; lab default tetap menggunakan `http://lab:8001`. Origin asing dan mutasi tanpa token CSRF tetap ditolak. Konfigurasi manual tidak dimasukkan ke binding target worker atau manifest benchmark.

## 4. Kondisi data dan pemeriksaan aktual

- [Helper persiapan](../scripts/prepare_manual_lab.py) membaca database dan WAL dari volume asal saat lab asal berhenti, memakai backup SQLite ke volume manual baru dan memeriksa hash source tetap sama. Helper menolak menimpa DB manual yang sudah ada.
- Snapshot salinan saat dibuat: `fc21167a-402c-459b-80b2-a027bf94ba4d`. Perubahan manual selanjutnya perlu dicatat oleh operator bila hendak dijadikan bukti.
- Pemeriksaan runtime lulus: halaman utama/health/login, endpoint ID objek, pencarian, notifikasi dan pemasok dengan parameter yang benar merespons 200; Origin asing ditolak.
- Proses Uvicorn berjalan sebagai UID 10001 dengan permitted/effective/bounding capability nol; koneksi keluar TCP baru ditolak.
- **7 tes akses terarah lulus** pada database sementara, termasuk lab default yang menolak Origin manual dan tidak mempunyai endpoint manual, isolasi ID objek serta CSRF.
- Percobaan salinan awal gagal karena akses SQLite WAL pada mount read-only; artefak volume awal dipertahankan. Bridge internal awal tidak mempublikasikan port host; konfigurasi diganti bridge khusus dengan firewall egress sebelum dinyatakan dapat diakses.

Hasil pemeriksaan disimpan privat pada `artifacts/backend-audit-20261113/`. Tidak ada klaim seluruh celah direproduksi ulang, GT disahkan, benchmark berjalan atau target asli direset oleh pembukaan akses ini.
