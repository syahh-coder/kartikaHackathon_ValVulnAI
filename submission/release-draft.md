# Draft release — belum diterbitkan

Judul usulan: **ValVuln AI — purwarupa lokal untuk triage laporan dan review bukti**.

ValVuln AI menerima laporan teks, menawarkan triage terstruktur dan menyediakan review bukti dengan role/scope server-side. Pemeriksaan produk tersedia untuk BAC-08, XSS-08 dan metadata nama upload UP-04 melalui fixture lab terdaftar. Planner pemeriksaan tetap deterministik; model hanya memproses teks.

Status kandidat review: CODE_TESTED lokal dengan simulasi. LIVE_VERIFIED, FROZEN dan EVALUATED belum terpenuhi. Dua puluh kandidat benchmark masih menunggu GT/bukti; tidak ada skor akurasi produk. Business logic dan sisa M6 DEFERRED untuk submission.

Berkas lokal yang perlu ditinjau: ZIP source dan checksum pada indeks final-review; quick start; slide HTML/PDF; thumbnail; maksimal lima screenshot; preview MOCK serta naskah demo. ZIP tidak memuat database, ledger, key, kandidat/GT privat atau binary image.

Sebelum publikasi, isi:

- Tag/commit yang benar-benar memuat source final, lalu build ulang ZIP dan checksum dari versi itu.
- Lisensi kode asli pilihan pengguna; inventaris dan notice pihak ketiga tetap berlaku.
- Link video YouTube <=10 menit dan slide publik aktual.
- Hasil smoke live/benchmark yang sudah ditinjau, atau keterbatasan yang tetap pending tanpa klaim palsu.
- Hasil clean build penuh pada lingkungan penilai; image/download membutuhkan internet dan belum dibundel.

Publikasi belum diotorisasi pada pekerjaan ini. Jangan membuat release, push, upload atau submit berdasarkan keberadaan draft ini.
