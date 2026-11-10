# Checklist pendaftaran dan submission

**Paket persiapan lokal sudah tersedia untuk review:** [indeks file dan hasil aktual](final-review.md). Slide9 halaman, thumbnail1200×630/153445 byte dan3 screenshot serta draft preview/storyboard disiapkan. Checkbox publikasi/submission, video YouTube, lisensi, GT/live/freeze/benchmark tidak dicentang tanpa bukti. Status READY_FOR_REVIEW_WITH_PENDING_INPUTS berbeda dari submission lengkap.

**Scope aktif 7 November 2026:** gunakan [submission-scope.md](submission-scope.md) dan [functional-v2](evaluation.md). Target 24 titik/protokol held-out lama menjadi backlog dan tidak dinyatakan selesai. Fitur AI, mode pemeriksaan, hasil verifier dan batas tiga subtype produk harus konsisten pada README/video/slide.

Status: daftar kerja; checkbox belum menyatakan kegiatan selesai. Dasar: [rulebook](https://drive.google.com/file/d/1IN7FukytvtJBIbw2yPoSprEaTrZdbfMM/view) G/H/I dan [S&K](https://drive.google.com/file/d/1PWLGVasB0OahUCd5gL_UCElK8cnFdK4l/view) Pasal 5, 8-10.

Deadline resmi pada kedua PDF: **15 November 2026 pukul 23:59 WIB**. Target internal siap 14 November. Perubahan resmi tetap dipantau.

## 1. Pendaftaran awal

Pada 3 November 2026 pengguna menyatakan pendaftaran program diterima. Bukti platform tidak dibaca/disimpan asisten; checklist rincian pribadi tidak otomatis dicentang. Penerimaan pendaftaran berbeda dari lolos final.

- [ ] Nama tim `ukas and codex vs everbody` benar dan hanya satu tim diikuti.
- [ ] Solo; akun ketua tidak ditambahkan sebagai anggota duplikat.
- [ ] Data WA, alamat, pekerjaan dan afiliasi diisi pengguna sesuai keadaan sebenarnya.
- [ ] Status WNI dan persetujuan membaca S&K dikonfirmasi sendiri pengguna.
- [ ] Nama karya/deskripsi dari [draf pendaftaran](registration.md) ditinjau pengguna.
- [ ] Pilih satu kategori: rekomendasi **Penindakan**.
- [ ] Simpan bukti konfirmasi penerimaan dari platform/email setelah benar-benar diterima.

Pengguna telah mengonfirmasi berusia **18 tahun atau lebih** pada 3 November 2026; minimum usia lomba 17 tahun terpenuhi berdasarkan pernyataan pengguna. Usia persis, nomor telepon, alamat dan dokumen identitas tidak perlu dicatat di repository.

## 2. Link karya yang dapat dicoba

Keputusan pengguna: **URL repo GitHub publik sebagai Link Karya, tanpa live web/GitHub Pages/VPS**. Repo tersedia di [syahh-coder/kartikaHackathon_ValVulnAI](https://github.com/syahh-coder/kartikaHackathon_ValVulnAI); push awal dokumentasi/UI diotorisasi 4 November 2026. Release aplikasi belum dibuat. Paket lokal dan prosedur kesiapan mengikuti [distribution.md](distribution.md); video, slide serta upload gambar tetap disiapkan pada field masing-masing.

- [ ] Link publik dapat diakses penilai selama penjurian.
- [ ] Field Link Karya menunjuk repo publik; README menautkan release, petunjuk menjalankan, video dan slide yang aktual.
- [ ] Jika berupa download/repository, package, dependensi, seed dan instruksi memungkinkan aplikasi dijalankan.
- [ ] Setup telah dicoba dari kondisi bersih dan tidak bergantung pada path laptop pribadi.
- [ ] Data demo sintetis; tidak ada secret atau credential aktif milik pengguna.
- [ ] Mode demo dan kebutuhan API dijelaskan; keterbatasan live/mock/replay terlihat.
- [ ] Target rentan tetap di lab terisolasi; tidak perlu membuatnya publik untuk menyediakan link karya.

## 3. Thumbnail dan screenshot

- [ ] Thumbnail berukuran **1200 x 630 px**.
- [ ] Format thumbnail **JPG, PNG, atau WebP** dan ukuran maksimal **500 KB**.
- [ ] Nama karya dan visual sesuai produk yang benar-benar ada.
- [ ] Screenshot antarmuka maksimal **lima gambar**.
- [ ] Screenshot mencakup input report, scope/rencana, bukti, verdict/review, dan evaluasi jika tersedia.
- [ ] Screenshot diperiksa agar tidak membocorkan API key, session secret, data pribadi atau GT tersembunyi.

## 4. Video YouTube

- [ ] Video maksimal **10 menit**, diunggah ke **YouTube** dan dapat diakses penilai.
- [ ] Menjelaskan masalah, manfaat, pengguna dan alur kerja.
- [ ] Memperlihatkan model AI berperan pada workflow dan hasil pengujian nyata.
- [ ] Memperlihatkan paling tidak satu kasus positif serta kontrol/hasil yang berbeda.
- [ ] Live, rekaman autentik, replay dan mock dibedakan.
- [ ] Tidak mencantumkan metrik atau penghematan yang belum diukur.
- [ ] Audio, teks dan bukti cukup terbaca.

## 5. Slide dan dokumentasi teknis

- [ ] Slide memuat latar belakang, solusi, fitur, arsitektur, teknologi, implementasi dan hasil aktual.
- [ ] Sumber angka masalah serta periode pengamatan tercantum dekat klaimnya.
- [ ] Ringkasan/proposal solusi tersedia untuk mendukung aspek dokumentasi.
- [ ] README berisi instalasi dan cara penggunaan yang telah diverifikasi.
- [ ] Arsitektur, kontrak tools, scope, reset dan batas deployment internal dijelaskan.
- [ ] Dataset aktual, GT, split, hasil per kategori, coverage dan kegagalan dijelaskan bila eksperimen telah dilakukan.
- [ ] Jika benchmark functional-v2 disertakan: target 20 teks 10 valid/10 tidak valid, alokasi 8 BAC/8 XSS/4 upload pada subtype yang didukung, GT manual dan bukti relevan; jumlah aktual/kekurangan dilaporkan. Draf asisten bukan GT final.
- [ ] Nyatakan mekanisme benchmark sudah dikenal saat development; tidak mengklaim held-out akar masalah baru atau 20 bug independen. Prediksi A/B terpisah dari verdict verifier.
- [ ] Status backlog 24 titik dijelaskan jujur: 13 reproduksi historis/11 PLANNED pada keputusan scope, M6 asli belum lulus. Bukan syarat baru dari panitia atau gate submission functional-v2.
- [ ] Konfigurasi model/provider/prompt dan batas run dicatat.
- [ ] [Deklarasi pihak ketiga](third-party.md) lengkap: sumber, versi/commit, hak penggunaan, atribusi dan modifikasi.
- [ ] Bahan pre-existing dibedakan dari kontribusi yang dibuat selama program.
- [ ] Lisensi kode asli proyek dipilih pengguna dan disertakan bersama notice pihak ketiga sebelum publikasi.

## 6. Sebelum menekan submit

- [ ] Nama, kategori dan deskripsi konsisten antara formulir, README, slide dan video.
- [ ] Seluruh kelengkapan yang diminta platform telah diisi; field baru diperiksa terhadap dokumen resmi.
- [ ] Tautan dicek dari akses yang setara dengan penilai.
- [ ] Satu submission tim; bila memperbarui, periksa versi terakhir yang dinilai.
- [ ] Bukti submission dan waktu penerimaannya disimpan setelah proses berhasil.

## 7. Jika lolos final

- [ ] Siap hadir sendiri sebagai perwakilan tim solo pada **24 November 2026 di Jakarta**.
- [ ] Presentasi final maksimal **10 menit termasuk tanya jawab**.
- [ ] Perangkat, reset demo, koneksi model dan rekaman cadangan telah disiapkan.

Kesiapan perjalanan dan penerimaan final belum dikonfirmasi. Checklist tidak menyatakan bahwa peserta telah lolos atau hadiah tertentu pasti diterima.
