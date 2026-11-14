# Review manual terakhir

Dikerjakan **setelah integrasi kode selesai**, sesuai instruksi13 November2026. Checklist ini tidak mengubah GT/status otomatis dan tidak mengharuskan pengembangan M6.

## A. Coba alur yang akan didemokan

**Akses manual terbaru:**8001 sekarang target worker yang sama. Sesudah memilih kondisi, admin perlu **Aktifkan pengujian manual** dan membuka tautan lab; validasi agent dikunci selama sesi ini. Selesai manual, reset untuk membuka validasi kembali. Rujukan "salinan8001" pada riwayat di bawah mengacu versi lama; salinan itu sekarang berhenti/opsional8002. [Panduan aktif](manual-lab.md).

1. Buka app8000 sebagai admin dan baca guideline aktif. Pastikan in-scope/out-of-scope terpisah dari laporan hunter. Scope diaktifkan admin; akun lain tidak dapat menggantinya lewat teks laporan.
2. Sebagai hunter, kirim satu laporan untuk subtype produk, minta saran AI ketika akses model siap, lalu **Siapkan validasi dari saran AI**.
3. Periksa primary claim, aset, path, kontrol dan arah akun. Jika informasi kurang, lengkapi atau revisi laporan dan minta saran baru. Jangan memasukkan ID objek dari salinan manual8001 ke target worker asli.
4. Konfirmasi snapshot. Backend harus menghentikan OOS/unsupported tanpa job; snapshot/readiness/scope yang berubah meminta tindakan baru.
5. Pada kondisi lab yang disiapkan operator, jalankan tiga jalur produk: BAC-08, XSS-08, UP-04, dengan kontrol yang relevan. Detail rute dan13 kondisi existing di [manual-lab.md](manual-lab.md). Jangan menjalankan seluruh evaluator historis hanya demi checklist ini.
6. Admin membaca evidence/verdict, menulis review dan membagikan ringkasan. Hunter hanya melihat laporan sendiri dan ringkasan yang dipublikasikan; raw evidence/catatan privat tetap dibatasi.

App asli dan lab manual menggunakan DB/snapshot berbeda. Pengujian manual dapat mengubah/menghapus objek di lab; reset hanya dilakukan operator secara eksplisit setelah tidak ada run aktif, bukan melalui prompt/report atau startup. Pilih kondisi target yang benar; kegagalan reproduksi saja bukan REFUTED.

### Jika validasi menampilkan TARGET_DIRTY

**Jalur UI terbaru:** sebagai admin, buka **Reset data lab**, pilih **Lab rentan / Lab kontrol diperbaiki**, lalu **Terapkan kondisi & reset data lab**. Tunggu status lab siap dan cek kondisi terpasang, lalu ulangi validasi. Untuk sesi rentan pilih vulnerable; fixed adalah kontrol perbaikan yang disiapkan operator, bukan remediasi AI. Kontrak API dan batas kegagalan ada di [lab-reset-ui.md](lab-reset-ui.md). CLI di bawah tetap cadangan operator; catatan vulnerable-only berikut adalah riwayat sebelum persetujuan dua mode.

Untuk sesi demo rentan, jalankan manual dari root repo:

```powershell
.\.venv\Scripts\python.exe -m scripts.reset_demo_lab --execute
```

Helper operator ini menolak worker/run aktif, masuk maintenance, membuat backup SQLite pada volume lab, reset BAC-08/XSS-08/UP-04 vulnerable, memeriksa seed/health dan melepas snapshot setelah acknowledgment worker. Jika pemeriksaan gagal, target tetap terkunci. Output sukses `VULNERABLE_READY` memuat ID objek baru. Refresh app dan ulangi validasi; sesuaikan path BAC/upload jika memakai ID sebelum reset. Laporan/ledger dan salinan manual8001 tidak direset. Helper bukan tool AI dan tidak dipanggil otomatis oleh app. Menjalankan tanpa `--execute` hanya menampilkan bantuan.

**Koreksi pengguna14 November2026:** lab memang sengaja rentan. Sesi coba produk sekarang memakai BAC-08/XSS-08/UP-04 vulnerable; jangan memakai fixed sebagai default pemulihan. Kondisi diaktifkan dengan maintenance evaluator `--condition vulnerable --xss-condition vulnerable --upload-point UP-04 --upload-condition vulnerable`, dilanjutkan assertion seed/health dan release snapshot worker. Bukti kondisi/readiness serta preservasi14 tabel aplikasi ada di `artifacts/target-recovery-20261114/vulnerable-ready.json`. Ini bukan reproduksi baru atau pengesahan GT. Catatan fixed/fixed di bawah adalah riwayat pemulihan awal, sebelum koreksi ini.

Penanda ini mengunci lab setelah aksi sebelumnya yang mungkin mengubah target, termasuk probe browser. Restart app tidak membersihkannya. Operator perlu memastikan tidak ada run aktif dan worker IDLE, menyimpan backup lab jika datanya masih dibutuhkan, lalu menjalankan reset resmi. Contoh berikut dari root repo hanya untuk kontrol negatif fixed/fixed yang sengaja dipilih; tidak mempertahankan kondisi rentan sesi pengguna:

```powershell
.\.venv\Scripts\python.exe -m evaluator.m2 reset --condition fixed --xss-condition fixed
```

Perintah ini mengganti data sintetis/ID objek pada lab internal, memeriksa seed dan health, lalu menunggu acknowledgment snapshot worker. Tidak mereset laporan, akun platform atau ledger; tidak mengubah salinan manual8001. Kondisi di atas adalah fixed/fixed, bukan skenario rentan. Untuk percobaan XSS-08 rentan yang sengaja dipilih operator, gunakan `--xss-condition vulnerable`; ini tidak mengesahkan GT kandidat. ID BAC/upload lama harus diperiksa ulang terhadap snapshot baru. Reset bukan tool AI dan tidak dijalankan otomatis dari chat.

Pemulihan14 November2026: flag dirty berasal dari run lab historis; tidak ada job aktif. Backup lab dibuat sebelum reset fixed/fixed. Setelah reset, app ready/dirty=0/maintenance=0, worker IDLE/dirty=false dan snapshot app-worker-lab sama. Seluruh baris pada14 tabel yang diperiksa (termasuk laporan, runs, triage, evidence dan61 baris ledger) identik; audit maintenance dan binding target diperbarui sesuai operasi. Tidak ada inferensi model atau run validasi baru. Bukti lokal privat: `artifacts/target-recovery-20261114/recovery.json`.

## B. Akses provider

Ikuti [Groq setup](groq-setup.md) dan [provider-setup.md](provider-setup.md): Groq utama, OpenRouter/Azure cadangan dipilih eksplisit. Satu smoke Groq sudah sukses; tidak perlu mengulang tanpa perubahan yang beralasan. Jangan mengaktifkan PAYG, membeli kredit atau menambah budget untuk meluluskan pemeriksaan. Periksa unknown lama dan baru di ledger, termasuk reservasiRp100 dari timeout OpenRouter sertaRp100 smoke Groq; jangan menghapusnya tanpa bukti rekonsiliasi.

## C. Ground truth20 kandidat

Worksheet privat: `artifacts/r3/candidates-v1/gt-review.csv`.

- Semua20 masih PENDING/GT kosong sebelum review manusia. Teks usulan asisten bukan label final.
- Baca setiap laporan, verifikasi klaim/bukti pada fitur/snapshot terkait, lalu isi keputusan ACCEPT/EXCLUDE/PENDING dan GT sesuai panduan [R3](r3-verification.md).
- Target10 VALID/10 INVALID tidak membenarkan mengubah label supaya seimbang. OOS/unsupported/kekurangan bukti tidak otomatis INVALID.
- Bukti per kasus harus terikat kandidat; hasil historis atas kasus lain bukan pengganti.
- Sesudah label/bukti/provider siap, ikuti [runbook](r3-runbook.md) untuk smoke/freeze/40 slot A/B/scoring. Sampel20 teks pada mekanisme yang dikenal adalah evaluasi fungsional kecil, bukan20 bug independen atau akurasi industri.

## D. Materi dan publikasi

- Pilih lisensi kode asli dan tinjau atribusi/pre-existing.
- Tinjau slide, thumbnail dan maksimal5 screenshot. MOCK/sintetis tetap dilabeli; ambil ulang bila ingin menampilkan hasil nyata yang sudah diverifikasi.
- Rekam video final≤10menit dengan narasi dan alur aktual; preview MOCK bukan video final.
- Isi link video YouTube dan slide publik. Pastikan repo/paket/instruksi dapat dicoba dari akses setara juri.
- Push/release/upload/submit dilakukan setelah otorisasi pengguna. Source sebelumnya sudah di-push; itu tidak berarti perubahan baru atau formulir final sudah dikirim.

Jika prasyarat nyata belum tersedia, tampilkan keterbatasannya dan jangan mengisi metrik palsu. Kode/provider yang sudah diuji tidak perlu dibuat ulang hanya karena checklist manual masih pending.
