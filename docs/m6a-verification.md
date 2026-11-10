# M6a - Fondasi kontrol bisnis aman, 6 November 2026

Status: **M6a selesai untuk kontrol aman; M6 masih sebagian**. Tidak ada titik kerentanan tambahan yang dinyatakan terimplementasi/terverifikasi. Hitungan tetap 13 dari 24 berdasarkan bukti tahap sebelumnya. Planner tetap mock dan `BUSINESS_LOGIC` tetap UNSUPPORTED pada validator produk.

## Perubahan yang tersedia

- Migrasi lab `004_business_controls.sql`: inventaris stok, penugasan petugas per unit, state/versi permintaan, pemenuhan unik dan jurnal sebelum/sesudah. Tabel baru terpisah dari kolom request lama; migrasi tidak melakukan seed, reset, perubahan scope atau akses target otomatis.
- `lab/business.py`: alur aman DRAFT -> SUBMITTED -> APPROVED -> FULFILLED. Pemohon hanya membuat/mengubah objek miliknya; petugas hanya menyetujui/memenuhi unit kewenangannya, dan tidak menyetujui permintaan sendiri. Peran ditetapkan operator pada database, bukan field request/login.
- Kuantitas integer ketat 1–1000, stok integer 0–10000. Barang/jumlah hanya berubah saat DRAFT. Mutasi memakai `expected_version`, transaksi SQLite dan jurnal; gagal menulis jurnal membatalkan perubahan stok/state. Stok diperiksa saat pemenuhan, karena approval tidak mereservasi stok.
- Satu pemenuhan per permintaan dengan constraint unik. Pengulangan sekuensial memakai versi permintaan yang sama mengembalikan pemenuhan tersimpan tanpa mutasi tambahan. Versi lain ditolak. Ini kontrak idempotensi lokal, bukan klaim pengujian race condition.
- Maksimum 64 permintaan bisnis dan 128 event per permintaan. GET detail membaca state/jurnal dalam snapshot transaksi yang sama. Daftar permintaan kini menyertakan permintaan milik pengguna yang belum memiliki lampiran.
- Aturan publik autentikasi pada `/api/business-rules` menggunakan versi `procurement-controls-v1`, tanpa flag kondisi/label GT. Aturan ini belum otomatis dimasukkan ke context model/worker.

Route baru: GET `/api/items`, GET `/api/business-rules`, POST `/api/requests`, GET/PATCH `/api/requests/{id}` dan POST suffix `/submit`, `/approve`, `/fulfill`. Endpoint baru tidak ditambahkan ke profil/tool worker, planner atau UI validasi.

`lab/business_setup.py` adalah setup operator eksplisit saat maintenance, setelah lab sintetis disiapkan. Ia menambahkan `approver_a` untuk unit A (tugas persetujuan dan pemenuhan digabung pada satu petugas), satu barang/stok 100, serta snapshot netral baru. Path database divalidasi read-only sebelum migrasi; database aplikasi/missing file ditolak tanpa perubahan schema. Password diminta interaktif dan tidak dicetak. Setup berulang mempertahankan stok/password/snapshot; konflik akun tidak mengubah hak. Petugas tidak diberi hak unit B. Reset evaluator yang sudah ada membersihkan tabel baru dalam urutan foreign key yang benar. Tidak ada akun/secret petugas baru pada worker yang sedang berjalan.

## Pemeriksaan aktual

- **95 tes terarah lulus dalam 70,52 detik**, termasuk **28 tes M6a**: alur normal, penolakan input/state/peran/unit/CSRF, versi usang, field approval terkunci, stok saat pemenuhan, idempotensi, rollback jurnal, batas data, migrasi 003 -> 004, startup/persistensi, konflik setup dan reset. Tes juga mencakup regresi auth/catalog lab, app bootstrap/auth/policy/storage dan kontrak provider simulasi yang relevan. Suite penuh tidak dijalankan pada batch ini.
- Percobaan M6a pertama: 7 gagal/16 lulus karena helper tes membentuk async generator dengan `tuple`; helper diperbaiki, lalu 23 tes lulus. Tiga regresi batas data/setup/migrasi, lalu dua guard path database tambahan ditambahkan sebelum pemeriksaan akhir 95 tes. Tidak melemahkan aturan bisnis untuk meluluskan tes.
- `python -m scripts.m6a_controls_check` lulus pada database sementara/ASGI: DRAFT, stok 100, jumlah 7 -> FULFILLED, stok 93, versi 4; pemenuhan kedua menghasilkan record yang sama dan empat event, tanpa pengurangan kedua. Menggunakan password acak sintetis yang tidak dibaca dari secret operator.
- Pemeriksaan yang sama lulus dalam container disposable UID 10001, `--network none`, root filesystem read-only, `/tmp` tmpfs, capability ALL dropped, no-new-privileges, RAM 256 MiB dan 64 PID, tanpa host volume/secret. Tidak menguji jaringan TCP, browser atau workflow worker; HTTP dijalankan in-process melalui ASGI.
- Build langsung dari `lab/Dockerfile` dengan `--network=none` gagal karena layer instalasi dependensi tidak tersedia pada cache untuk opsi itu dan pip tidak dapat menjangkau indeks. Pemeriksaan container memakai image turunan `kartikahackathon-lab:latest` lokal dengan source lab baru disalin di atasnya; tidak memasang dependensi baru. Build normal bersih M6a belum diulang.
- Service Compose aktif tetap menggunakan image M5; tidak dilakukan rebuild/restart/reset atau provisioning pada data aktif. Hasil container disposable tidak membuktikan M6a telah aktif di service tersebut.

## Artefak dan menjalankan ulang

Artefak privat di `artifacts/m6a/`: hasil host `20261106T023947146715Z-controls.json` dan container `20261106T023950272423Z-container-controls.json`, dengan hash source dan state sebelum/sesudah. Script host tidak menghubungi service yang sedang berjalan atau membaca `.env`/secret operator, tidak memanggil provider dan tidak membuat job aplikasi.

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_lab_business_controls.py -q
.\.venv\Scripts\python.exe -m scripts.m6a_controls_check
```

Jalankan dari root repo. Kedua perintah menggunakan database sementara, tanpa reset database proyek. Untuk setup persisten kelak, operator perlu maintenance/idle, migrasi image yang sesuai, setup interaktif pada database lab eksplisit dan verifikasi/release snapshot baru. Prosedur layanan persisten ini belum dijalankan pada M6a.

Hash manifest M5 tetap bukti untuk source M5 saat audit sebelumnya. Source lab kini berubah secara sengaja; auditor M5 terhadap checkout M6a akan menolak perbedaan tersebut. Jangan mengganti hash/hasil lama agar cocok atau menganggap audit lama sebagai verifikasi kode baru.

## Yang masih terbuka

M6 belum memenuhi kelengkapan 24 titik: BAC-01..07 dan BL-01..04 tetap PLANNED. Belum ada verifier/assessment/UI business logic, context agent terintegrasi, bukti reproduksi titik tambahan, GT manusia, model live atau benchmark. Jurnal bisnis berisi event lab; bukan evidence platform dengan run/action ID. Pengelompokan UP-04 dengan XSS-01..05 juga belum selesai untuk freeze. Tidak commit/push/deploy/rilis.
