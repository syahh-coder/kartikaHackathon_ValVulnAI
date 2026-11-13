# Role dan hak akses ValVuln AI

Tanggal: **13 November 2026**. Status: **rancangan fitur dan hak akses**, berdasarkan permintaan pengguna. Dokumen ini tidak mengatur UI dan tidak menyatakan semua fitur di bawah sudah diimplementasikan. Schema, autentikasi dan enforcement teknis mengikuti [architecture.md](architecture.md).

## 1. Dua role pengguna

| Role | Tanggung jawab utama |
| --- | --- |
| **Bug hunter** | Membaca aturan program, memasukkan laporan, melengkapi informasi dan mengikuti hasil laporannya sendiri |
| **Admin program** | Mengatur aturan/scope program, memasukkan laporan, meninjau laporan program dan membagikan hasil kepada pelapor |

MVP memakai satu program. Hak admin berlaku pada program yang dikelolanya. Role berasal dari akun dan membership di server; pengguna tidak dapat memilih atau menaikkan role melalui isi laporan. Akun hunter dan admin sama-sama dapat menjadi pengirim laporan.

## 2. Fitur admin program

### 2.1 Mengatur scope dan guideline

Admin dapat menyusun, menyimpan draf dan mengaktifkan aturan program yang berisi:

- **In-scope:** aset/fitur/path yang diizinkan untuk diperiksa dan tindakan yang diperbolehkan.
- **Out-of-scope:** aset/fitur/path, tindakan atau jenis pengujian yang dikecualikan.
- **Prasyarat:** akun uji, akses dan informasi yang dibutuhkan agar laporan bisa diperiksa.
- **Aturan bisnis:** perilaku aplikasi yang dianggap benar, misalnya batas kepemilikan dan syarat persetujuan.

Aturan berasal dari admin dan mempunyai versi. Laporan hunter tidak dapat mengganti scope aktif. Jika aturan berkonflik, out-of-scope tetap membatasi izin. Scope admin juga harus berada dalam target dan batas teknis yang sudah didaftarkan operator.

Menyimpan draf belum mengubah aturan aktif. Aktivasi versi baru dicatat beserta admin dan waktunya; pemeriksaan yang sudah dibuat tetap dapat ditelusuri ke versi aturan yang dipakai.

### 2.2 Memasukkan laporan

Admin dapat:

- Membuat dan mengirim laporan miliknya sendiri.
- Memasukkan laporan bug hunter yang diterima lewat kanal lain, misalnya teks/email yang disalin atau file TXT/MD yang diunggah.
- Mencatat sumber laporan dan identitas pelapor yang diketahui sebagai atribusi.
- Menambahkan informasi atau revisi pada laporan yang admin buat sendiri.

Untuk laporan dari kanal lain, admin tetap tercatat sebagai akun yang memasukkan laporan. Nama pelapor yang ditulis dalam dokumen tidak otomatis menjadi akun/pemilik atau memberi akses aplikasi. Pada rancangan MVP, akses pelapor terdaftar menggunakan laporan yang dia kirim melalui akunnya sendiri; pemindahan kepemilikan laporan impor ke akun lain ditunda.

### 2.3 Memeriksa dan menindaklanjuti laporan

Admin dapat:

- Melihat laporan dalam programnya, termasuk laporan yang dikirim bug hunter.
- Membaca klaim, versi scope, status pemeriksaan, saran AI serta bukti internal yang telah direduksi dari credential.
- Meninjau assessment dan menyimpan keputusan manusia beserta alasan; hasil asli sistem tetap tersimpan.
- Membatalkan pemeriksaan dalam programnya sesuai kebijakan penghentian.
- Menyetujui dan membagikan ringkasan hasil/bukti yang aman kepada pemilik laporan.
- Mengekspor informasi sesuai hak akses yang sama dengan informasi yang dapat dibaca.

Admin tidak menimpa teks asli laporan bug hunter. Koreksi admin disimpan sebagai review/catatan terpisah; revisi dari pelapor tetap mempunyai riwayatnya sendiri.

## 3. Fitur bug hunter

Bug hunter dapat:

1. Membaca guideline aktif program: in-scope, out-of-scope, prasyarat dan aturan bisnis yang dipublikasikan.
2. Membuat laporan melalui teks atau unggahan TXT/MD.
3. Menyimpan draf, memperbaiki teks dan menambahkan informasi pada laporannya sendiri.
4. Mengirim laporan untuk diperiksa; laporan yang sudah dikirim mempunyai snapshot/revisi yang dapat ditelusuri.
5. Meminta saran AI untuk membantu memahami klaim dan informasi yang masih kurang, sesuai mode/akses model yang tersedia.
6. Meminta pemeriksaan pada kemampuan produk yang didukung, setelah scope, prasyarat dan izin lolos backend.
7. Melihat status serta ringkasan hasil laporannya sendiri; rincian bukti mengikuti persetujuan publikasi admin.
8. Membatalkan proses miliknya yang masih berjalan dan mengekspor hasil yang memang boleh dia lihat.

Perubahan teks setelah pengiriman menjadi revisi baru. Perubahan itu tidak diam-diam mengganti snapshot pemeriksaan yang sedang berjalan.

Bug hunter tidak dapat mengubah guideline, melihat laporan hunter lain, membaca bukti internal mentah, mengubah verdict sistem atau menerbitkan hasil review admin.

## 4. Matriks izin

Tabel berikut adalah target izin fitur. Akses setiap objek tetap memerlukan membership program yang sesuai.

| Tindakan | Bug hunter | Admin program |
| --- | --- | --- |
| Membaca guideline aktif | Ya | Ya |
| Membuat/mengubah draf guideline | Tidak | Ya |
| Mengaktifkan versi guideline | Tidak | Ya |
| Membuat dan mengirim laporan | Ya, milik sendiri | Ya, milik sendiri atau input dari kanal lain |
| Mengubah draf/teks laporan | Milik sendiri | Milik sendiri; tidak menimpa teks hunter |
| Membaca laporan | Milik sendiri | Laporan dalam programnya |
| Meminta saran AI | Draf milik sendiri | Draf milik sendiri |
| Memulai pemeriksaan | Laporan milik sendiri, jika diizinkan | Laporan milik sendiri, jika diizinkan |
| Membatalkan proses | Milik sendiri | Proses dalam programnya, sesuai jenis proses |
| Membaca bukti internal teredaksi | Tidak | Ya, dalam programnya |
| Meninjau/mengoreksi assessment | Tidak | Ya, alasan dan riwayat wajib |
| Membagikan ringkasan hasil | Tidak | Ya, setelah review |
| Membaca/mengekspor hasil publikasi | Milik sendiri | Dalam programnya |
| Mengubah role, key model atau budget | Tidak | Bukan kewenangan admin program |
| Mengatur seed/reset/kondisi rentan lab | Tidak | Bukan kewenangan admin program |

Admin yang membaca laporan hunter tidak otomatis boleh mengirim ulang draf atau memicu pemeriksaan baru atas nama hunter. Pekerjaan tersebut membutuhkan aksi pemilik atau alur delegasi khusus yang ditunda dari MVP.

## 5. Tambahan fitur yang disarankan

Bagian ini merupakan **usulan tambahan**, belum menjadi klaim fitur tersedia. Prioritaskan setelah fungsi dasar kedua role jelas.

| Fitur | Pelaku | Tujuan |
| --- | --- | --- |
| Permintaan informasi tambahan | Admin meminta, pemilik laporan menjawab | Memperjelas prasyarat/PoC tanpa mengubah teks asli |
| Penanda laporan duplikat | Admin, dengan referensi laporan terkait | Mengurangi pemeriksaan berulang; isi laporan hunter lain tetap privat |
| Status penanganan laporan | Admin dan pemilik sesuai tahap | Membedakan belum dikirim, menunggu informasi, sedang ditinjau dan sudah selesai ditangani |
| Riwayat aktivitas | Dibuat sistem, dibaca sesuai izin | Menelusuri pengiriman, revisi, aktivasi scope, review dan publikasi |

Status penanganan tidak mengganti verdict teknis. Laporan duplikat atau belum didukung tidak otomatis berarti klaimnya salah. Riwayat aktivitas sistem yang sudah ada dapat dipakai ulang; jangan membuat sistem audit baru hanya karena usulan ini.

## 6. Data minimum pada laporan

- Program tujuan, judul, deskripsi/fitur, klaim utama, prasyarat, langkah reproduksi, hasil aktual, hasil yang diharapkan dan dampak yang diklaim.
- Akun pemilik dan akun yang membuat/mengirim data ditentukan server, bukan dipercaya dari field unggahan.
- Sumber/atribusi pelapor untuk input admin dicatat terpisah dari pemilik akun.
- Revisi laporan, waktu pengiriman dan versi scope yang dipakai pemeriksaan dipertahankan.

Pemisahan akun pembuat dengan atribusi pelapor eksternal adalah kebutuhan rancangan input admin. Pemetaan field dan migrasi, bila diperlukan, ditentukan saat implementasi; jangan menganggap field sumber/atribusi sudah tersedia hanya karena dicantumkan di sini.

## 7. Aturan hasil dan tanggung jawab sistem

- Backend memeriksa scope serta izin; AI memberi saran dan penjelasan dalam kemampuan yang tersedia.
- Hasil AI, hasil pemeriksaan teknis dan keputusan review admin dapat dibaca sebagai informasi yang berbeda dengan asal yang jelas.
- `CONFIRMED` memerlukan bukti dampak, `REFUTED` memerlukan bantahan/kontrol yang memadai, dan `INCONCLUSIVE` dipakai saat bukti belum cukup.
- Error model, timeout, OOS dan kategori belum didukung tidak otomatis menjadi laporan tidak valid.
- Publikasi hanya membuka ringkasan/bukti yang diizinkan. Raw credential, catatan privat dan data akun lain tetap dibatasi.
- Role admin program tidak memberi akses konfigurasi infrastruktur, API key, GT evaluator atau reset lab. Pekerjaan itu milik operator di luar dua role produk ini.

Dokumen ini tidak memperluas kemampuan pemeriksaan yang sudah disepakati pada [scope submission](submission-scope.md); pengembangan M6 yang ditunda tetap di luar lingkup aktif.

## 8. Urutan penetapan fitur

1. Pastikan dua role dapat membuat laporan sendiri dan membaca data sesuai kepemilikan/program.
2. Pastikan hanya admin dapat mengatur serta mengaktifkan scope.
3. Lengkapi input laporan eksternal oleh admin dengan atribusi yang jelas.
4. Pastikan review, publikasi dan ekspor mengikuti matriks izin.
5. Tinjau usulan permintaan informasi/duplikat/status setelah kebutuhan dasar disepakati.

Matriks dan urutan ini adalah rancangan fitur. Implementasi dan pengujian penerimaannya dicatat terpisah pada [implementation.md](implementation.md); perubahan dokumen ini tidak menjalankan atau mengubah backend.
