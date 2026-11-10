# Peta rencana kerentanan portal lab

**Keputusan 7 November 2026:** target 24 titik dan alokasi evaluasi lama pada dokumen ini menjadi backlog/protokol v1. Status aktual dan riwayat grup tetap dipertahankan, M6 tidak dicentang selesai. Submission functional-v2 memakai subtype produk BAC-08/XSS-08/UP-04 dan tidak mengklaim held-out akar masalah baru; [scope](submission-scope.md), [evaluasi aktif](evaluation.md). Tidak mengubah katalog/gate/manifest untuk memenuhi scope baru.

Status audit 6 November 2026: **BAC-08, XSS-01..08 dan UP-01..04 IMPLEMENTED / OPERATOR-REPRODUCED**, total **13 dari 24 titik**, dengan kondisi rentan/perbaikan dan kontrol ([M2](m2-verification.md), [M4c](m4c-verification.md), [M5](m5-verification.md)). Bukti upload berasal dari runtime 5 November dan diaudit offline 6 November, bukan reproduksi ulang. **11 titik lain PLANNED / BELUM DIIMPLEMENTASIKAN / BELUM DIVERIFIKASI MANUAL**: BAC-01..07 dan BL-01..04. GT manusia untuk 20 laporan masih pending. Workflow/UI upload hanya UP-04; UP-01..03 operator.

Dokumen ini untuk pembuat lab dan evaluator. Jangan dimount ke worker, dikirim ke model validator, dimasukkan ke profil publik target, atau dijadikan tool pencarian agent. Aturan akses/bisnis yang diperlukan tetap diberikan melalui profil tanpa membocorkan jawaban.

Status terstruktur per ID disimpan pada [evaluator/catalog.json](../evaluator/catalog.json), dengan pemeriksaan offline `python -m evaluator.catalog_audit --require-ready`. M6b memvalidasi tepat 24 ID/alokasi/status/reference, tanpa mengeksekusi target. Saat ini gate exit 2 karena 11 mekanisme PLANNED dan konflik grup development/evaluasi; status reproduksi terdahulu adalah catatan historis, bukan GT manusia atau reproduksi ulang. [Hasil M6b](m6b-verification.md).

M6a menambah implementasi kontrol aman fitur permintaan/persetujuan/pemenuhan, bukan mekanisme kerentanan BL-01..04. Status empat titik BL tetap PLANNED dan hitungan tetap 13/24. Source baru diuji pada database sementara dan container disposable, belum service Compose aktif. [Hasil M6a](m6a-verification.md).

## 1. Jumlah dan pemakaian

| Kategori | Titik lab | Area evaluasi | Titik development cadangan | Non-benchmark | Laporan valid | Laporan tidak valid |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| BAC / IDOR | 8 | 4 | 1 | 3 | 4 | 4 |
| XSS | 8 | 4 | 1 | 3 | 4 | 4 |
| File upload | 4 | 1 | 1 | 2 | 1 | 1 |
| Business logic | 4 | 1 | 1 | 2 | 1 | 1 |
| Total | 24 | 10 | 4 | 10 | 10 | 10 |

Setiap area evaluasi menyumbang dua teks laporan berbeda: satu klaim yang terbukti dan satu klaim keliru yang dapat dibantah pada kontrol relevan. Dua puluh laporan utama bukan 20 bug berbeda. Titik pada fitur berbeda juga belum otomatis berarti akar masalah implementasi yang independen.

Revisi 4 November 2026 mengurangi dataset dari 40 ke 20 laporan, tanpa mengurangi target 24 titik lab. Sepuluh titik berlabel Non-benchmark tetap bagian rancangan lab, tetapi tidak dihitung sebagai kasus utama atau dipilih sesudah melihat hasil untuk memperbaiki metrik. Perubahan alokasi dilakukan sebelum freeze dengan pemeriksaan grouping; tidak otomatis menjadi tambahan data tuning.

## 2. BAC / IDOR

| ID | Fitur / route rencana | Celah yang harus dibuktikan | Kontrol atau dasar laporan negatif | Pemakaian |
| --- | --- | --- | --- | --- |
| BAC-01 | Detail invoice, `GET /api/invoices/{id}` | Pemohon A dapat membaca invoice privat B | Pembacaan dokumen yang memang publik diperbolehkan; laporan yang menyebutnya akses privat harus diperiksa terhadap aturan objek | Evaluasi |
| BAC-02 | Detail permintaan, `GET /api/requests/{id}` | Pemohon dapat membaca permintaan privat unit lain | Detail yang telah dilindungi menolak nonpemilik sementara pemilik sah tetap dapat membaca | Evaluasi |
| BAC-03 | Unduh lampiran privat, `GET /api/attachments/{id}/download` | Pengguna dapat mengambil lampiran privat milik pengguna lain | Route download pembanding memeriksa kepemilikan dan tidak mengembalikan isi file pada penolakan | Evaluasi |
| BAC-04 | Edit catatan permintaan, `PATCH /api/notes/{id}` | Pengguna dapat mengubah catatan pengguna lain tanpa hak | Field/jalur edit terlindungi tidak berubah; state sebelum/sesudah dan identitas diperiksa | Evaluasi |
| BAC-05 | Pembatalan permintaan, `POST /api/requests/{id}/cancel` | Pemohon membatalkan permintaan privat pengguna lain | Endpoint pembanding menolak pembatalan lintas pemilik dan status tetap | Non-benchmark |
| BAC-06 | Persetujuan unit, `POST /api/requests/{id}/approve` | Petugas unit A dapat menyetujui permintaan unit B | Petugas memang boleh menyetujui permintaan unitnya sendiri; klaim eskalasi pada tindakan sah tersebut tidak valid | Non-benchmark |
| BAC-07 | Ekspor laporan unit, `POST /api/unit-reports/export` | Filter unit dapat menghasilkan data privat unit lain | Ekspor ringkasan publik atau ekspor dengan pembatas unit tidak membocorkan baris privat | Non-benchmark |
| BAC-08 | Hapus lampiran, `DELETE /api/attachments/{id}` | Pengguna dapat menghapus lampiran pengguna lain | Pemeriksaan pemilik pada route pembanding menolak dan file masih ada | Development |

Setiap bukti harus mengikat akun, objek, aturan, dan dampak. Menerima status 200 atau respons generik bukan bukti akses lintas hak. Kontrol publik/aman merupakan data lab yang perlu dibuat dan diperiksa; bukan asumsi untuk memberi label negatif.

## 3. XSS

| ID | Fitur / route rencana | Celah yang harus dibuktikan | Kontrol atau dasar laporan negatif | Pemakaian |
| --- | --- | --- | --- | --- |
| XSS-01 | Pencarian katalog, `GET /catalog/search` | Input pencarian dieksekusi pada konteks HTML halaman target | Pencarian pembanding meng-escape input sehingga hanya teks, dengan konteks browser diperiksa | Evaluasi |
| XSS-02 | Catatan barang, `GET /catalog/items/{id}` | Catatan tersimpan dieksekusi ketika dilihat pengguna lain | Deskripsi teks pada fitur yang sama ditampilkan inert sesuai aturan | Evaluasi |
| XSS-03 | Alasan permintaan, `GET /requests/{id}/review` | Alasan yang dikirim pemohon dieksekusi pada tampilan petugas | Tampilan audit pembanding meng-escape alasan dan marker tidak dieksekusi | Evaluasi |
| XSS-04 | Nama tampilan pada komentar, `GET /requests/{id}/comments` | Nama tampilan dimasukkan ke HTML tanpa pengamanan konteks | Isi komentar yang di-escape tidak mengakibatkan eksekusi meskipun input terpantul | Evaluasi |
| XSS-05 | Nama pemasok, `GET /suppliers` | Nilai nama pemasok tersimpan dieksekusi pada daftar | Field kode pemasok ditampilkan sebagai teks dan kontrol normal tetap berjalan | Non-benchmark |
| XSS-06 | Referensi pelacakan, `GET /tracking` | Input masuk ke konteks atribut yang dapat memicu marker dalam browser lab | Halaman pembanding mengodekan nilai menurut konteks atribut | Non-benchmark |
| XSS-07 | Panel detail berbasis fragmen URL, `GET /requests/view` | JavaScript frontend memasukkan fragmen ke sink HTML yang dapat dieksekusi | Panel pembanding memakai penyajian teks; raw fragment bukan bukti eksekusi | Non-benchmark |
| XSS-08 | Pratinjau notifikasi, `GET /notifications/preview` | IMPLEMENTED / OPERATOR-REPRODUCED M4a: fragmen fixture mencapai innerHTML dan callback nonce main frame pada origin lab | Kondisi textContent menampilkan fixture sebagai teks; kontrol inert/JS/context baru/PNG diperiksa | Development; GT manusia pending |

Gunakan marker lokal unik yang tidak mengambil data atau menghubungi layanan luar. Setiap subtype yang disebut harus benar-benar ada. Jika beberapa titik memakai renderer rentan yang sama, catat akar masalah bersama dan sesuaikan group split.

### Implementasi/operator M4c

XSS-01..07 kini memiliki HTTP input/tampilan aktual sesuai tabel, dua kondisi dan jalur kontrol aman. XSS-02..05 memakai write requester-a dan browser pembaca requester-b yang baru; review permintaan A diberikan ke B melalui penugasan eksplisit tanpa akses lampiran privat. XSS-06 memakai fixture konteks atribut, XSS-07 fragmen DOM. [M4c](m4c-verification.md) mencatat 14 fase/42 capture/138 request dan status per titik. Manifest privat `artifacts/m4c/catalog-manifest.json` mengikat run/snapshot/evidence, hash source lab, artefak kondisi serta percobaan gagal. Ini reproduksi operator, bukan label dataset manusia atau kemampuan planner live.

Grup konservatif sementara: XSS-01..05 = `html-element-output`, XSS-06 = `html-attribute-output`, XSS-07 dan XSS-08 = `dom-fragment-innerhtml`. Lima fitur HTML memiliki input/state/handler sendiri, tetapi tidak dihitung sebagai lima sampel akar masalah independen. XSS-07 tetap non-benchmark; overlap DOM development tidak masuk held-out. Tinjau grouping final sebelum freeze. Keempat area evaluasi XSS tidak dipakai untuk tuning planner; runtime UI tetap hanya XSS-08.

## 4. File upload

| ID | Fitur / route rencana | Celah yang harus dibuktikan | Kontrol atau dasar laporan negatif | Pemakaian |
| --- | --- | --- | --- | --- |
| UP-01 | Preview lampiran SVG, `GET /attachments/{id}/preview` | Konten aktif dari fixture SVG dieksekusi pada origin target karena cara penyajian | Jalur download menyajikan fixture sebagai attachment/inert; klaim eksekusi melalui jalur itu dibantah berdasarkan konteks aktual | Evaluasi |
| UP-02 | Preview dokumen HTML, `GET /documents/{id}/preview` | File fixture HTML yang diunggah menjadi konten aktif di origin target | Viewer teks pembanding tidak mengeksekusi konten meski upload diterima | Non-benchmark |
| UP-03 | Penyimpanan lampiran, `POST /api/attachments` | Nama berkas yang bertabrakan menimpa konten lampiran milik pengguna lain | Upload dengan kunci penyimpanan unik tidak menimpa objek pembanding; perubahan isi diverifikasi | Non-benchmark |
| UP-04 | Nama berkas pada daftar upload, `GET /requests/{id}/attachments` | Metadata nama berkas dirender sebagai HTML aktif | Label nama file aman ditampilkan sebagai teks | Development |

UP-01/02/04 mempunyai tag sekunder XSS dan UP-03 dapat bertag BAC. Jangan menghitung satu mekanisme bersama dua kali sebagai akar masalah independen. Tidak ada kebutuhan shell, malware, eksekusi server, atau fixture destruktif. Jika bukti menunjukkan suatu perilaku tidak dapat dieksploitasi pada konfigurasi browser target, jangan mempertahankannya sebagai celah hanya untuk memenuhi hitungan.

Grouping M5: UP-01/02 `upload-active-content-origin`, UP-03 `upload-shared-filename-storage`, UP-04 `html-element-output`. Development UP-04 berbagi grup terakhir dengan XSS-01..05; alokasi evaluasi HTML saat ini belum independen dan harus ditinjau/revisi sebelum freeze, tanpa memilih kasus sesudah melihat hasil model. Empat ID upload bukan empat grup independen.

Review [M6f](m6f-verification.md) mempertahankan grup konservatif dan alokasi di atas. Riwayat development UP-04 tetap menghalangi evaluasi grup HTML meskipun label alokasinya dipindahkan. Hanya XSS-06 tercatat sebagai kandidat XSS di luar grup development; belum cukup bagi rancangan empat area XSS. Ini review metadata/source, tanpa reproduksi baru, penggantian manifest atau kenaikan status/hitungan titik.

## 5. Business logic

| ID | Fitur / route rencana | Celah yang harus dibuktikan | Kontrol atau dasar laporan negatif | Pemakaian |
| --- | --- | --- | --- | --- |
| BL-01 | Pemenuhan barang, `POST /api/requests/{id}/fulfill` | Permintaan yang belum disetujui dapat dipenuhi karena pemeriksaan alur state hilang | Jalur pembanding mewajibkan approval; hak akses aktor sudah diverifikasi sehingga ini klaim aturan bisnis, bukan sekadar bypass role | Evaluasi |
| BL-02 | Pemrosesan ulang pemenuhan, route fulfill yang sama dengan mekanisme kasus terpisah | Pengulangan request berurutan menyebabkan pemenuhan/pengurangan stok ganda | Jalur idempotent mengembalikan hasil sebelumnya dan tidak mengubah stok dua kali | Non-benchmark |
| BL-03 | Jumlah barang pada permintaan/pemenuhan, `POST /api/requests` | Kuantitas tidak sah memengaruhi stok/pemenuhan secara bertentangan dengan aturan bilangan positif | Validasi server menolak jumlah tidak sah dan state stok tetap | Non-benchmark |
| BL-04 | Ubah permintaan setelah approval, `PATCH /api/requests/{id}` | Perubahan jumlah/barang setelah persetujuan berlaku tanpa persetujuan ulang | Jalur pembanding mengunci field atau mengembalikan status untuk persetujuan ulang | Development |

Pengujian BL-02 bersifat sekuensial; bukan klaim dukungan race condition. Jika BL-01 dan BL-02 berbagi handler, masing-masing mekanisme dan grup akar masalah harus ditinjau berdasarkan implementasi, bukan nama ID.

## 6. Verifikasi dan manifest privat

Saat implementasi, setiap titik harus mendapat catatan berikut:

```text
vulnerability_id, feature, actual_route, primary_category, secondary_tags
root_cause_group, implementation_revision, target_build
status: PLANNED | IMPLEMENTED | OPERATOR_REPRODUCED | MANUALLY_VERIFIED
affected_actor, affected_object, relevant_rule, preconditions
positive_manual_evidence, negative_control_evidence
report_ids, evaluation_or_development, reviewer_note
```

Route aktual boleh berubah sebelum freeze, tetapi daftar dan draf report harus diperbarui bersama. Titik baru disebut kerentanan nyata setelah dampaknya direproduksi manual; status PLANNED atau banyaknya flag mode tidak cukup.

Target 24 titik menambah pekerjaan terhadap jadwal 30 jam. Utamakan portal sederhana, kontrol yang dapat diulang, dan dokumentasi GT sejak setiap fitur dibuat. Jika target lebih dari 20 belum tercapai, laporkan kekurangan dan koordinasikan scope; jangan menaikkan hitungan dari parafrasa report atau banyak run.

Empat titik cadangan tidak boleh berbagi akar masalah dengan held-out tanpa penanganan grouping yang jelas. Jika implementasi menyebabkan overlap, revisi alokasi sebelum melihat hasil final. Semua 20 laporan utama tetap berstatus draf sampai GT dan pembagian data dibekukan sesuai [evaluation.md](evaluation.md).
