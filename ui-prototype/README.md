# Prototipe UI ValVuln AI

Prototipe HTML/CSS/JavaScript lokal untuk review desain. Pengguna memilih grafit + hijau sage. Sumber berada pada `dist/`; tidak memerlukan npm install atau build. Seluruh laporan, respons dan bukti adalah fixture berlabel simulasi.

## Membuka

Buka [dist/index.html](dist/index.html) dengan browser Chromium/Chrome/Edge modern. Jalur file lokal diperiksa melalui Chromium headless saat QA; tidak membutuhkan web server atau koneksi internet. Browser default pengguna belum dibuka/diuji secara manual oleh asisten.

Alternatif server statis dari root repo:

```powershell
python -m http.server 43127 --bind 127.0.0.1 --directory ui-prototype/dist
```

Kemudian buka `http://127.0.0.1:43127`. Ini server file untuk pratinjau, bukan backend FastAPI. Hentikan dengan Ctrl+C. Jalur server diverifikasi menghasilkan HTTP 200 dan dipakai QA browser pada 3 November 2026; server milik asisten dihentikan setelah pemeriksaan. Jalankan sendiri perintah di atas bila ingin memakai URL localhost. Detail ada pada [review UI](../docs/ui-review.md).

## Yang bisa ditinjau

- Chat laporan baru, contoh percakapan, pencarian dan draft pesan.
- Upload TXT/MD UTF-8 maksimal 128 KiB, batas gabungan teks 32.000 karakter; parsing lokal inert, tanpa autofetch URL.
- Pilihan program, layar login contoh, tema gelap/terang dan navigasi ponsel.
- Label model Qwen3-Coder di samping Simulasi; klik untuk melihat ID/provider rencana dan status belum terhubung.
- Tampilan scope, informasi kurang, OOS, draft, berjalan, confirmed/refuted/inconclusive, gagal dan dibatalkan.
- Pratinjau admin untuk laporan program, guideline draf/aktivasi, evidence, catatan review dan publikasi ringkasan.
- Salin/ekspor ringkasan contoh yang selalu diberi label bukan hasil validasi.

Gunakan menu `…` di judul percakapan untuk melihat variasi status. Pada draft baru, Validasi laporan membuka pemilih skenario UI secara eksplisit; tidak mengklasifikasikan report dengan AI. Pergantian role di bar Prototipe UI hanya membantu review layar.

## Batas penting

Tidak ada autentikasi, otorisasi server, database, model, worker, Docker atau pentest. Semua fixture dapat dilihat dari source; penyembunyian menu bukan kontrol keamanan. Jangan masukkan password atau laporan asli. Draft, lampiran, catatan dan perubahan guideline hanya hidup di memori tab dan hilang ketika reload; hanya preferensi tema yang disimpan di localStorage. Tidak menganggap fixture invoice sebagai kasus evaluasi atau GT yang sudah diverifikasi.

Status 4 November 2026: **UI v0.1 diterima pengguna sebagai baseline fix untuk mulai backend**, dengan perbaikan berikutnya tetap boleh. Gate UI terpenuhi; M1 dikerjakan di chat baru tanpa konfirmasi UI ulang. Prototipe tetap simulasi, bukan backend/worker/model yang sudah berfungsi. Referensi yang dipilih ada di [design-references.md](../docs/design-references.md); spesifikasi utama tetap [design.md](../docs/design.md).
