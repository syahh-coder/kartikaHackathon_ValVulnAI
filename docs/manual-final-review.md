# Review manual terakhir

Dikerjakan **setelah integrasi kode selesai**, sesuai instruksi13 November2026. Checklist ini tidak mengubah GT/status otomatis dan tidak mengharuskan pengembangan M6.

## A. Coba alur yang akan didemokan

1. Buka app8000 sebagai admin dan baca guideline aktif. Pastikan in-scope/out-of-scope terpisah dari laporan hunter. Scope diaktifkan admin; akun lain tidak dapat menggantinya lewat teks laporan.
2. Sebagai hunter, kirim satu laporan untuk subtype produk, minta saran AI ketika akses model siap, lalu **Siapkan validasi dari saran AI**.
3. Periksa primary claim, aset, path, kontrol dan arah akun. Jika informasi kurang, lengkapi atau revisi laporan dan minta saran baru. Jangan memasukkan ID objek dari salinan manual8001 ke target worker asli.
4. Konfirmasi snapshot. Backend harus menghentikan OOS/unsupported tanpa job; snapshot/readiness/scope yang berubah meminta tindakan baru.
5. Pada kondisi lab yang disiapkan operator, jalankan tiga jalur produk: BAC-08, XSS-08, UP-04, dengan kontrol yang relevan. Detail rute dan13 kondisi existing di [manual-lab.md](manual-lab.md). Jangan menjalankan seluruh evaluator historis hanya demi checklist ini.
6. Admin membaca evidence/verdict, menulis review dan membagikan ringkasan. Hunter hanya melihat laporan sendiri dan ringkasan yang dipublikasikan; raw evidence/catatan privat tetap dibatasi.

App asli dan lab manual menggunakan DB/snapshot berbeda. Pengujian manual dapat mengubah/menghapus objek di lab; reset hanya dilakukan operator secara eksplisit setelah tidak ada run aktif, bukan melalui prompt/report atau startup. Pilih kondisi target yang benar; kegagalan reproduksi saja bukan REFUTED.

## B. Akses provider

Ikuti [provider-setup.md](provider-setup.md): OpenRouter dahulu, Azure jika dipilih dan konfigurasinya lengkap. Jalankan smoke melalui API/ledger. Jangan mengaktifkan PAYG, membeli kredit atau menambah budget untuk meluluskan pemeriksaan. Periksa unknown lama di ledger, termasuk reservasiRp100 dari timeout historis; jangan menghapusnya tanpa bukti rekonsiliasi.

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
