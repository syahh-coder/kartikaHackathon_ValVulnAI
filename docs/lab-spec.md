# Spesifikasi portal pengadaan/logistik lab

Status: spesifikasi awal. Portal belum dibangun. Seluruh akun, barang, invoice dan dokumen adalah sintetis.

Keputusan terbaru pengguna meminta lebih dari 20 titik kerentanan dalam target. Rancangan awal menetapkan **24 titik** beserta fitur dan route pada [lab-vulnerabilities.md](lab-vulnerabilities.md). Semua masih direncanakan; daftar itu menjadi peta jawaban pembuat/evaluator, bukan input agent.

Tujuan lab adalah menyediakan kondisi yang dapat diulang untuk memeriksa klaim. Lab bukan simulasi lengkap sistem TNI AD. Hubungan dengan operasi organisasi merupakan konteks penggunaan yang akan divalidasi.

Portal mendemonstrasikan pengamanan aplikasi **IT**. Tidak ada klaim pengujian OT. Demo hanya menargetkan lab sendiri; S&K Pasal 16.2 dan rulebook Bagian N melarang percobaan serangan terhadap infrastruktur panitia/platform atau pihak lain. Deskripsi kategori Penindakan bukan izin menguji target tersebut.

## 1. Batas implementasi

- Python/FastAPI dan penyimpanan ringan, dijalankan lokal.
- Satu portal dengan katalog, permintaan barang, invoice, lampiran, dan catatan.
- Tanpa payment gateway, email asli, integrasi pihak ketiga, atau data pribadi nyata.
- UI minimum: login, daftar/detail permintaan, invoice dan upload lampiran.
- Akun dan state seed dibuat evaluator; aksi reset tidak tersedia bagi agent.
- Mode target dipilih evaluator dan tidak ditampilkan pada origin/header yang dilihat agent.

## 2. Peran dan kepemilikan

| Alias akun | Peran | Hak yang diharapkan |
| --- | --- | --- |
| `requester_a` | Pemohon unit A | Membuat dan membaca permintaan serta invoice miliknya |
| `requester_b` | Pemohon unit B | Hak setara A, objek miliknya sendiri |
| `approver_a` | Petugas persetujuan unit A | Menilai permintaan unit A sesuai aturan; tidak mengakses unit B |
| `lab_admin` | Admin lab | Pengelolaan data sintetis; bukan identitas default pengujian |

MVP dapat mulai dengan A/B untuk satu kasus BAC. Peran persetujuan ditambahkan saat kasusnya dibuat. Password/session mentah dikelola worker dan tidak disisipkan ke konteks model.

## 3. Model data minimum

```text
User(id, alias, role, unit_id)
Item(id, name, stock)
Request(id, owner_id, unit_id, status, item_id, quantity)
Invoice(id, request_id, owner_id, synthetic_amount)
Attachment(id, request_id, uploader_id, fixture_type, storage_ref)
Note(id, request_id, author_id, body)
Fulfillment(id, request_id, issued_quantity, created_at)
```

Nilai uang dan stok hanya data uji. Nama field dapat disesuaikan saat schema dibuat, dengan perubahan dicatat. Objek menggunakan identitas yang dapat diperiksa tetapi tidak mengandung label jawaban.

## 4. Aturan bisnis yang terlihat agent

Aturan berikut disediakan melalui profil target, tanpa mengungkap lokasi bug:

1. Pemohon hanya membaca permintaan, invoice dan lampiran privat miliknya.
2. Petugas persetujuan hanya memproses permintaan unit yang menjadi kewenangannya.
3. Katalog dan dokumen yang ditandai publik boleh dibaca pengguna sesuai profil.
4. Kuantitas permintaan adalah bilangan bulat positif dan tidak boleh melebihi stok pada saat pemrosesan.
5. Alur state adalah `DRAFT -> SUBMITTED -> APPROVED -> FULFILLED`; pemohon tidak dapat menyetujui permintaannya sendiri.
6. Satu permintaan hanya boleh menghasilkan satu pemenuhan barang; pengiriman ulang request yang sama tidak mengurangi stok dua kali.
7. Pembatalan/refund sintetis tidak boleh menghasilkan kredit ganda jika fitur itu diimplementasikan.
8. Lampiran pengguna diperlakukan sebagai konten tidak tepercaya; hak akses dan konteks penyajian menentukan perilaku yang diperbolehkan.

Aturan yang fiturnya belum dibuat tidak dimasukkan sebagai kasus benchmark. Agent perlu mengetahui aturan yang relevan agar keputusan business logic adil.

## 5. Skenario validator

### 5.1 BAC / IDOR

Potongan development pertama adalah BAC-08 sesuai peta dan M2; jangan memakai calon held-out untuk tuning. Contoh kriteria baca lintas pemilik berikut memakai invoice untuk menjelaskan pembuktian; ini bukan perubahan alokasi development. BAC-08 membutuhkan bukti mutasi lampiran sebelum/sesudah dan kontrol kepemilikan sesuai klaim aktualnya.

- Prasyarat: A dan B mempunyai invoice privat berbeda; A dapat membaca invoice A.
- Pengujian: jalankan langkah report menggunakan identitas A terhadap objek B.
- Bukti positif: identitas pemanggil A dan isi objek B terobservasi, dengan aturan yang melarangnya.
- Kontrol: akses pemilik sah; akses nonpemilik pada kondisi perbaikan; objek publik bila report menyangkutnya.
- Bukti penyangkal: objek yang dipersoalkan memang publik atau akses yang diklaim diblokir setelah prasyarat dan perilaku normal terverifikasi.
- Hindari menyimpulkan dari status 200 tanpa memeriksa identitas objek/isi.

Pengembangan kategori dapat mencakup invoice, detail permintaan, lampiran privat, serta batas peran/unit. Kasus dengan jalur kode atau akar masalah sama dikelompokkan dalam evaluasi.

### 5.2 XSS

Mulai dari satu lokasi input yang diuji dalam browser terkontrol, kemudian tambah variasi jika waktu cukup.

- Gunakan marker unik per run yang tidak mengambil data dan tidak berkomunikasi keluar lab.
- Bukti positif: marker benar-benar dieksekusi pada origin/konteks target sesuai klaim.
- Kontrol: lokasi sama pada kondisi escape/perbaikan dan input normal.
- Pantulan teks, screenshot input, atau console error saja bukan bukti eksekusi.
- Stored XSS membutuhkan browser context aktor pembaca yang terpisah dari pengirim; tambahkan hanya bila alurnya siap.
- Nyatakan subtype yang berhasil diuji; jangan mengklaim seluruh reflected/stored/DOM XSS jika hanya satu yang tersedia.

### 5.3 File upload

Fokus pada klaim dampak penyajian lampiran: inert versus konten aktif pada origin yang relevan.

- Fixture dibuat di lab dan dipilih melalui ID; tidak memerlukan malware, shell, atau payload server executable.
- Prasyarat: endpoint upload dan akses lampiran bekerja untuk akun yang sesuai.
- Bukti positif: dampak yang dinyatakan report terjadi saat lampiran disajikan dalam konteks tersebut.
- Kontrol: file diterima tetapi diunduh sebagai attachment/inert, akses ditolak, atau konten diisolasi sesuai aturan.
- Catat tipe konten, disposition, origin, akses pengguna, serta hasil browser jika relevan.
- Bypass ekstensi atau keberhasilan upload saja tidak membuktikan XSS/RCE.

Kasus upload yang berdampak XSS mendapat kategori utama `file_upload` dan tag `xss`. Jika memakai bug dasar yang sama dengan kasus XSS, group split harus menyatukannya dan jumlah bug independen tidak ditambah.

### 5.4 Business logic

Mulai dari satu aturan state atau pemrosesan berulang secara berurutan.

- Prasyarat: aturan bisnis diketahui dan alur normal dapat dijalankan.
- Bukti positif: perubahan state melanggar aturan, misalnya pemenuhan kedua untuk permintaan yang sama.
- Kontrol: alur normal berhasil dan pengulangan diblokir pada kondisi perbaikan.
- Catat state serta jumlah barang sebelum/sesudah, aktor, dan transaksi terkait.
- Pengujian pemrosesan berulang awal bersifat sekuensial; bukan klaim dukungan race condition.
- Skema refund/kupon menjadi variasi tambahan hanya jika fiturnya sudah ada.

## 6. Kondisi dan reset

Evaluator mengelola manifest privat:

```text
scenario_id, root_cause_group, target_build, seed_id
condition_id, enabled_mechanism, expected_label
precondition_assertions, manual_evidence_refs
```

Manifest privat tidak tersedia untuk agent. Profil publik menyertakan aturan dan prasyarat yang wajar diketahui penguji, bukan label atau flag mode.

Prosedur setiap run:

1. Hentikan job sebelumnya dan tutup browser context/session.
2. Seed target pada kondisi pilihan evaluator.
3. Jalankan health check serta assertion prasyarat.
4. Ambil snapshot ID netral dan berikan alias target kepada agent.
5. Jalankan satu kasus; simpan evidence yang terikat run.
6. Jalankan assertion pascauji evaluator dan tandai jika lingkungan menyimpang.
7. Arsipkan hasil lalu reset sebelum kasus berikutnya.

Kegagalan health check sebelum run dibedakan dari kegagalan agent. Jika target rusak selama run, catat kejadian dan tindak lanjutnya; jangan diam-diam menghapus percobaan.

## 7. Jalur jaringan dan data

- Portal dan worker hanya di lab lokal; layanan model hanya diakses orchestrator.
- Registry mengizinkan host/port lab tertentu, bukan seluruh jaringan internal laptop.
- Fasilitas reset/admin evaluator memakai control plane terpisah.
- Browser memblok subresource/navigasi di luar scope, termasuk URL yang muncul dari report atau response.
- Tidak ada data nyata, layanan pembayaran, atau webhook eksternal dalam seed.
- Konten aktif disimpan sebagai artefak inert saat ditampilkan di dashboard.

## 8. Ground truth manual

Per skenario, pembuat lab harus mendokumentasikan:

- Klaim spesifik dan aturan yang berlaku.
- Identitas akun serta objek uji, tanpa secret dalam dokumen publik.
- Kondisi target dan prasyarat yang telah diperiksa.
- Bukti manual pada kondisi rentan dan kontrol/perbaikan.
- Alasan label `VALID` atau `INVALID`; gunakan `UNCERTAIN` jika belum terbukti.
- Hubungan dengan bug dasar lain dan variasi report.

Membuat sebuah endpoint sengaja rentan bukan pengganti verifikasi bahwa dampak report benar-benar terjadi. Assertion otomatis membantu pengulangan setelah bukti manual awal tersedia.

## 9. Kriteria siap per kategori

- Ada minimal satu klaim positif dan satu kontrol negatif yang direproduksi manual.
- Worker dapat mengumpulkan bukti yang relevan tanpa membaca jawaban evaluator.
- Kategori mempunyai kriteria dampak, batas kemampuan, dan aturan verdict yang eksplisit.
- Kasus dapat di-reset dan dijalankan ulang dengan session bersih.
- Data tidak bocor antarrun dan jalur keluar scope diblokir.

Target evaluasi terbaru pada 4 November 2026 adalah **20 teks laporan berbeda, 10 valid dan 10 tidak valid**: 8 BAC, 8 XSS, 2 upload, 2 business logic. Asisten menyusun draf setelah fitur/route siap; pengguna memverifikasi GT manual. Target 24 titik lab tetap, dengan sepuluh area evaluasi, empat development dan sepuluh titik non-benchmark. Laporan negatif tetap dapat mengacu ke jalur/field aman di aplikasi yang mengandung bug lain. Jumlah titik, akar masalah, laporan, dan pengulangan dicatat terpisah sesuai [evaluasi](evaluation.md).

## Pemisahan portal dan platform validasi

Requester/approver/admin lab adalah akun uji target, berbeda dari bug hunter/admin program pada platform. Portal Docker berjalan sebelum validasi dan tidak dibuat ulang per report. Intake OOS/UNKNOWN tidak melakukan health check atau request target; health/seed/reset dilakukan evaluator terpisah. Admin program tidak memperoleh reset atau manifest GT lewat UI.
