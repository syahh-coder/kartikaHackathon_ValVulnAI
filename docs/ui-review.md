# Review prototipe UI v0.1

QA prototipe: 3 November 2026. Status terbaru **4 November 2026: pengguna menerima UI sebagai baseline fix untuk mulai backend**, dengan perbaikan berikutnya tetap boleh. Gate UI sudah terpenuhi; M1 dimulai di chat baru tanpa konfirmasi UI ulang. Ini persetujuan baseline visual/alur, bukan verifikasi backend atau model.

Pembaruan backend M2 dicatat terpisah pada [m2-verification.md](m2-verification.md): worker HTTP/lab dan isolasi sudah diuji operator, bukan QA browser UI produk. Baseline ui-prototype tetap tidak diubah pada M1-M2.

## Artefak

- [Halaman interaktif](../ui-prototype/dist/index.html) dan [cara membuka](../ui-prototype/README.md).
- [Pratinjau desktop](../ui-prototype/previews/desktop.png), [hasil contoh](../ui-prototype/previews/report.png), [ponsel](../ui-prototype/previews/mobile.png).
- [Pilihan 11 referensi](design-references.md) dan [spesifikasi desain](design.md).

Seluruh respons, laporan dan bukti adalah fixture UI, bukan keluaran model/pentest. Pemilih role berada pada bar Prototipe UI agar layar dapat direview; tidak ada login atau otorisasi nyata. Fixture bukan bagian dataset 20 laporan/GT final.

## Pemeriksaan yang benar-benar dijalankan

Browser: Chromium **156.0.8078.4** dari cache host. Harness: playwright-core **1.64.1** yang sudah tersedia, tanpa instalasi dependensi proyek. Tidak menjalankan detector/CLI Impeccable, Taste atau Hallmark. Hasil mentah ringkas disimpan di [qa-results.json](../ui-prototype/qa-results.json).

| Pemeriksaan | Hasil dan batas |
| --- | --- |
| Sintaks JavaScript | `node --check ui-prototype/dist/app.js` lulus |
| Entri file lokal | `file://` berhasil memuat HTML/CSS/JS, tanpa build/server |
| Entri HTTP lokal | Perintah server statis pada README dijalankan; GET `http://127.0.0.1:43127` menghasilkan HTTP 200 `text/html` dan dipakai QA browser |
| Responsivitas | Chat/example diuji pada lebar 320, 390, 768, 1280, 1366 dan 1440 px; tidak ada overflow horizontal dokumen. Tambahan halaman admin diperiksa pada 320 px; tabel mempunyai scroll lokal |
| Interaksi inti | Contoh report, draft, pemilih status, upload, pembatalan simulasi, pilihan program, pratinjau login, tema, publikasi ringkasan dan guideline version dapat diklik |
| Semua state hasil | Draft, informasi kurang, OOS, running, confirmed, refuted, inconclusive, gagal dan cancelled tersedia. Pemilihan state eksplisit; bukan klasifikasi AI |
| Upload | TXT/MD diterima; file PDF, >128 KiB dan UTF-8 tidak valid ditolak pada uji; batas gabungan teks diterapkan di UI. Ini validasi client prototipe, bukan kontrol server |
| Rendering input | Contoh teks berisi tag script/img tetap menjadi teks; tidak terbentuk node script/img di area report. Tidak menganggapnya audit XSS lengkap |
| Draft | Pesan/lampiran yang belum dikirim bertahan ketika pindah percakapan; isi guideline draft bertahan saat pindah halaman dalam tab yang sama |
| Keyboard/focus | Skip link, dialog native melalui Enter/Escape serta pemulihan focus diperiksa. Navigasi ponsel membuat area utama inert dan mengembalikan focus saat ditutup |
| Label/reduced motion | Input/select/textarea mempunyai label; reduced motion menghasilkan durasi transisi 0 s pada tombol contoh. Nama tombol scope tetap tersedia saat teksnya disembunyikan di ponsel |
| Kontras sampel | Pasangan token teks utama/sekunder/dim pada latar terkait diperiksa; pasangan terang dim/raised diperbaiki menjadi sekitar 4,85:1. Ini sampel palet, bukan audit seluruh rendered pair/WCAG |
| Error/jaringan | Tidak ada uncaught page error pada skenario yang dijalankan. Jalur file lokal mencatat nol request HTTP/eksternal; jalur server hanya mengakses file localhost. Tidak ada panggilan model/target |

## Perbaikan yang ditemukan lewat QA

| Sebelum | Sesudah | Alasan |
| --- | --- | --- |
| Draft/lampiran dapat hilang saat pindah percakapan | Draft dan lampiran dipertahankan di memori per percakapan | Menghindari kehilangan input selama review |
| Field guideline kembali ke nilai awal saat pindah halaman | Field draft dipulihkan dari memori tab | Perilaku Simpan draf menjadi konsisten |
| Tombol scope kehilangan nama ketika label disembunyikan di ponsel | Nama aksesibel eksplisit mengikuti versi scope | Kontrol tetap bisa dikenali |
| Label running hanya pada metadata yang tersembunyi di layar kecil | Label Pengujian berjalan juga ditampilkan bersama kontrol proses | Status tetap terbaca pada 320 px |
| Notifikasi overlay menutupi tombol/composer | Notifikasi menjadi bar dalam flow di bawah header, dapat ditutup | Tidak menghalangi tindakan pengguna |
| Teks dim pada raised surface terang di bawah target kontras | Token tema terang diperbaiki; sampel mencapai sekitar 4,85:1 | Menjaga keterbacaan alternatif tema |

## Yang belum diverifikasi

- Pemeriksaan visual/interaksi rinci yang belum tercakup QA tetap terbatas; pengguna sudah menerima baseline pada 4 November. Persetujuan pengguna tidak disamakan dengan audit aksesibilitas atau keamanan lengkap.
- Screen reader NVDA/VoiceOver, perangkat sentuh fisik, zoom browser 200%, Firefox/Safari dan seluruh kombinasi kontras.
- Autentikasi, otorisasi/ownership server, policy, worker, Docker, bukti nyata atau model live. M1 kemudian menguji fondasi auth/API/app Docker secara terpisah; lihat [hasil M1](m1-verification.md). Itu bukan QA browser UI backend atau worker/model live. Status per acceptance criteria pada [security-review.md](security-review.md).
- Pemrosesan file PDF/OCR, durable storage, pemulihan draft setelah reload atau sinkronisasi antartab.

## Review pengguna sebelum lanjut

- [ ] Pilihan panduan dan arah grafit + sage sesuai untuk produk.
- [ ] Kepadatan sidebar, ukuran teks, ruang chat dan composer nyaman di laptop pengguna.
- [ ] Tampilan bug hunter/admin, scope, guideline dan bukti mudah dipahami.
- [ ] Seluruh perubahan visual/interaksi yang diminta pengguna sudah diterapkan.
- [x] Pengguna menyatakan **UI fix sebagai baseline mulai backend** pada 4 November 2026, dengan kemungkinan perbaikan nanti.

Palet grafit + sage dipilih pengguna dan baseline UI sudah diterima secara eksplisit pada 4 November. Checkbox detail lain tetap tidak dicentang tanpa pernyataan/pemeriksaan spesifik. Yang tersedia masih prototipe simulasi, bukan kelulusan milestone validasi BAC atau model live.

## Revisi label model

Pengguna meminta nama model terlihat di samping keterangan mode. Header kini menampilkan Qwen3-Coder di samping Simulasi; klik label membuka ID `qwen/qwen3-coder`, akses rencana OpenRouter dan status belum terhubung. Nama/provider adalah konfigurasi rencana, bukan model yang telah dipanggil. Tidak menambah model selector atau akses API.

Pemeriksaan browser khusus revisi pada 320, 390, 768, 1366 dan 1440 px: label tetap dalam header, tanpa overflow horizontal; dialog detail dibuka/ditutup dan focus kembali ke tombol model. Tidak ada page error atau request eksternal. Screenshot pratinjau dan `qa-results.json` diperbarui. Pada saat QA 3 November, status masih menunggu review; konfirmasi baseline diberikan pengguna pada 4 November. Tidak menjalankan ulang QA browser hanya untuk perubahan status dokumentasi ini.

## QA UI backend M3 - 5 November 2026

UI produk pada app kini memakai session/role dan API aktual, dengan tampilan baseline grafit/sage. Login hunter/admin, pilih program, chat/upload, draft reload/navigasi, validasi BAC, polling terminal, review/publikasi dan ekspor diuji di Chromium host. Lima viewport: 320/390/768/1366/1440; tiga screenshot lokal. Laporan dan response ditampilkan inert; evidence hanya admin, export hunter memakai ringkasan tersanitasi. Respons sesi/polling/navigasi lama ditolak. Hasil/version/artefak dan kegagalan yang diperbaiki pada [m3-verification.md](m3-verification.md). Ini bukan browser worker atau integrasi model live; `ui-prototype/` tetap simulasi terpisah.

## UI evidence M4a - 5 November 2026

QA Chromium host pada bukti browser operator aktual lulus: admin membuka BROWSER_PROBE sebagai JSON teks, termasuk HTML/nonce/base64 screenshot, tanpa node img/script aktif. Hunter ditolak pada evidence/ekspor run admin. Nol page error/request eksternal; tidak membuat run/request target baru. Artefak privat artifacts/m4/ui-evidence-verification.json dan admin-evidence-ui.png; [hasil M4a](m4-verification.md). Ini pemeriksaan rendering/privasi, belum alur validasi atau publikasi XSS milik hunter melalui UI.
