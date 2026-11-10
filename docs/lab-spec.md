# Spesifikasi portal pengadaan/logistik lab

**Scope submission 7 November 2026:** perluasan ke 24 titik menjadi backlog, bukan gate submission sempit. Pertahankan perilaku/isolasi dan bukti lab yang sudah ada; R1 triage teks tidak mengakses atau mengubah target. M6 asli masih sebagian dan mekanisme BUSINESS_LOGIC belum tersedia. [Pemilik cakupan aktif](submission-scope.md); spesifikasi penuh di bawah tetap referensi backlog, bukan klaim implementasi.

Status 6 November 2026: BAC-08, delapan XSS dan empat upload memiliki bukti operator, total 13 titik; [M5](m5-verification.md), [M4c](m4c-verification.md). M6a menambah kontrol bisnis aman/state/stok pada source yang diuji host/container disposable, tanpa mekanisme kerentanan baru atau validator produk. Service Compose aktif masih M5. Seluruh akun, barang, invoice dan dokumen adalah sintetis.

Keputusan terbaru pengguna meminta lebih dari 20 titik kerentanan dalam target. Rancangan awal menetapkan **24 titik** beserta fitur dan route pada [lab-vulnerabilities.md](lab-vulnerabilities.md). 13 titik memiliki bukti operator (BAC-08, delapan XSS dan empat upload), 11 titik BAC/business logic tetap direncanakan; bukti M5 5 November diaudit ulang 6 November; daftar menjadi peta jawaban pembuat/evaluator, bukan input agent.

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
| `requester-a` | Pemohon unit A | Membuat dan membaca permintaan serta invoice miliknya |
| `requester-b` | Pemohon unit B | Hak setara A, objek miliknya sendiri |
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

## Implementasi development M4a

XSS-08 preview notifikasi pada GET /notifications/preview kini tersedia bagi akun lab yang terautentikasi. Fragment fixture diterapkan melalui innerHTML pada kondisi rentan dan textContent pada perbaikan; pilihan kondisi hanya maintenance evaluator, bukan request/response flag. Reset BAC dan XSS mempunyai parameter operator terpisah; reset biasa tetap membuat XSS fixed. Browser worker tidak mendapat source lab, peta bug, label kondisi atau reset endpoint.

Dua akun dan kontrol inert/marker direproduksi operator dengan PNG/event, bukan GT manusia dataset utama. [Hasil M4a](m4-verification.md). Pada batch M4a total dua titik development direproduksi operator; M4c kemudian melengkapi tujuh titik XSS lain. Target 24 dan 20 laporan tetap. Fault fixture network/delay hanya dapat dipasang melalui maintenance CLI lokal untuk uji batas/cancel, bukan menu admin program atau tool model.

## Implementasi tujuh fitur XSS M4c

Migrasi `002_xss_catalog.sql` menambah katalog shared dengan note/description, alasan permintaan, komentar dengan nama tampilan, pemasok name/code, dan tabel penugasan reviewer. Seed requester-b ditugaskan membaca review/komentar permintaan sintetis requester-a; ini izin fitur review saja, bukan hak baca/hapus lampiran atau mutasi objek pemilik lain. Pemohon A tetap tidak dapat membuka tampilan review petugas; B tidak dapat mengedit alasan A. Peran unit/approver lengkap belum tersedia dan tidak disimulasikan sebagai otorisasi seluruh unit.

Input mutasi maksimal 1.024 karakter dan memerlukan session/Origin/CSRF; nama tampilan tidak menerima role dari client. Rendering HTML element, atribut value berpetik ganda dan DOM fragment mempunyai perbaikan masing-masing. Kontrol field/view selalu di-escape/textContent; query view bukan sakelar kondisi rentan. Kondisi hanya dapat dipilih pada reset maintenance CLI, satu titik tambahan per snapshot; default seluruhnya fixed. Tidak ada reset endpoint, label kondisi atau peta bug pada response.

Untuk stored XSS, input disimpan melalui HTTP oleh A dan dibaca oleh context browser B yang terpisah, tanpa payload di URL tampilan. Katalog/pemasok sintetis memang shared; alasan/komentar mengikuti kepemilikan atau penugasan review eksplisit. Rute, bukti, kontrol dan grup pada [hasil M4c](m4c-verification.md). Data/GT manusia dan validator produk bagi rute baru belum dibuat.


## Fondasi kontrol bisnis aman M6a

M6b kemudian memeriksa alur normal yang sama melintasi dua container dan satu volume uji: stok/fulfillment/snapshot/jurnal dipertahankan, tanpa reset data proyek. Aturan scope terikat run juga masuk konteks mock NONE tanpa tool, belum agent business logic LAB. Katalog privat mengaudit status/grouping dan tetap menolak kesiapan 24 titik. [Hasil M6b](m6b-verification.md).

Migrasi 004 menambah tabel terpisah untuk stok, petugas, state/versi permintaan, pemenuhan unik dan event sebelum/sesudah. Aturan versi `procurement-controls-v1` tersedia setelah autentikasi melalui GET `/api/business-rules`; API bisnis menegakkan kepemilikan, unit, larangan persetujuan sendiri, urutan state, bilangan bulat positif, field material DRAFT saja, versi dan stok saat pemenuhan. Pengulangan pemenuhan identik mengembalikan hasil tersimpan. Ini kontrol aman, bukan reproduksi BL-01..04 atau bukti race condition.

Setup operator eksplisit menambah petugas `approver_a` unit A dengan tugas persetujuan dan pemenuhan gabungan; hak ini tidak diwariskan requester-b yang hanya ditugaskan membaca fitur review M4c. Tidak ada akses unit B atau role dari client. Startup hanya migrasi, tanpa akun/stock/seed/reset baru. Setup berulang tidak mengganti password/stok; reset evaluator membersihkan tabel baru. Source diuji pada database sementara, belum pada data/service Compose aktif. [Pemeriksaan dan batas M6a](m6a-verification.md).
