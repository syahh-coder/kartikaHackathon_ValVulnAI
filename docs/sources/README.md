# Sumber aturan lomba

Dua PDF yang ditautkan pengguna diunduh dan dibaca pada 3 November 2026. Salinan lokal dipertahankan untuk audit; nama file adalah nama lokal yang dipilih asisten.

| File lokal | Sumber resmi yang diberikan pengguna | Halaman | SHA-256 |
| --- | --- | ---: | --- |
| `rulebook.pdf` | [Rulebook](https://drive.google.com/file/d/1IN7FukytvtJBIbw2yPoSprEaTrZdbfMM/view) | 10 | `8e903e2e95aee3411c73e1239ee5a0326522258b3cdc93679ffcf6833744a795` |
| `terms.pdf` | [Syarat dan Ketentuan](https://drive.google.com/file/d/1PWLGVasB0OahUCd5gL_UCElK8cnFdK4l/view) | 12 | `9c596e27e5cb1167d7f3ca5e8bfb191a674d6a7c31e3eb43ba41be693ed9e665` |

S&K menampilkan pembaruan 20 Oktober 2026 dan berlaku sejak Oktober 2026. Rulebook menyebut Oktober 2026 tanpa tanggal pembaruan rinci yang sama. Tanggal pembacaan bukan bukti bahwa salah satu dokumen mempunyai prioritas hukum atas dokumen lain.

## Cara pembacaan

Viewer web tidak dapat mengakses PDF, tetapi kedua PDF berhasil diunduh dari tautan publik. Instalasi pembaca PDF tambahan tidak dijalankan karena review persetujuan otomatis gagal akibat batas penggunaan. Ekstraksi dilakukan lokal menggunakan Python standard library, dekompresi stream, dan pemetaan font Unicode yang tertanam; skrip sementara berada di `.cache/read_pdf.py`.

Hasil ekstraksi lokal `rulebook.txt` dan `terms.txt` bukan transkrip resmi. Beberapa glyph bullet/dekoratif dan sedikit karakter tidak terpetakan; perbandingan klausa dilakukan pada teks yang terbaca, dan klausul bernomor dipertahankan sebagai rujukan. Jika membutuhkan pembuktian tata letak atau ada frasa ambigu, buka PDF aslinya. Hash di atas mengidentifikasi versi file yang dibaca.

PDF/TXT lokal dan `.cache` dikecualikan dari publikasi Git secara default. Tautan resmi menjadi sumber publik; ringkasan yang digunakan proyek ada di [rules-alignment.md](../rules-alignment.md).
