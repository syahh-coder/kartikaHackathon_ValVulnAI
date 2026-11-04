# Penyelarasan karya dengan rulebook dan S&K

Status: pembandingan dokumen pendaftaran, belum merupakan konfirmasi atau keputusan panitia. Diperiksa 3 November 2026.

## 1. Sumber yang benar-benar dibaca

| Kode | Dokumen | Lokasi |
| --- | --- | --- |
| R | Rulebook Kartika Cyber Hackathon 2026, 10 halaman; dikeluarkan Oktober 2026 | [PDF Drive](https://drive.google.com/file/d/1IN7FukytvtJBIbw2yPoSprEaTrZdbfMM/view) |
| S | Syarat dan Ketentuan, 12 halaman; menampilkan pembaruan 20 Oktober 2026 | [PDF Drive](https://drive.google.com/file/d/1PWLGVasB0OahUCd5gL_UCElK8cnFdK4l/view) |
| F | Teks formulir yang diberikan pengguna di percakapan | Nama tim maksimal 30 karakter, data pribadi, nama/deskripsi/kategori, checkbox |
| W | Website resmi sebagai sumber tambahan dan pemantauan perubahan | [kartikacyberhackathon.id](https://kartikacyberhackathon.id/) |

Nomor halaman di bawah mengikuti halaman PDF. Salinan lokal, hash dan cara pembacaan dicatat di [sources/README.md](sources/README.md). Dokumen tidak menetapkan bahwa rulebook otomatis mengalahkan S&K. Bagian yang berbeda dipertahankan sebagai catatan; ketentuan submission yang dapat dipenuhi bersamaan digabung dalam checklist.

## 2. Kesesuaian ide

| Topik | Dasar | Penyesuaian karya |
| --- | --- | --- |
| Tema keamanan IT/OT dengan AI | S Pasal 2.1, halaman 2 | Fokus aplikasi web IT; model memahami report, merencanakan pengujian dan membaca bukti. Tidak mengklaim OT |
| Satu kategori saat pendaftaran | R Bagian B, halaman 3; S Pasal 5.1, halaman 3 | Rekomendasi Penindakan; jangan memilih beberapa kategori |
| Penindakan memuat pengujian kerentanan/AI pentest | R Bagian B, halaman 3 | Reproduksi aktif PoC menjadi fungsi utama; dashboard mendukung hasilnya |
| Karya software/API/framework diperbolehkan | R B; S Pasal 5.2 | Python/FastAPI, worker dan portal lab sesuai bentuk solusi yang disebut |
| Individu diperbolehkan | R D, halaman 4; S Pasal 4.1, halaman 2 | Tetap solo dengan nama tim `ukas and codex vs everbody` |
| Satu peserta satu tim | R D; S Pasal 4.2 | Pengguna memeriksa status keikutsertaan sendiri |
| Data pendaftaran benar | R C/E; S Pasal 3.5 dan 6 | Data pribadi diisi langsung pengguna; tidak direkayasa atau dimasukkan ke repo |
| Orisinalitas selama program | R G, halaman 5-6; S Pasal 5.3 | Bangun workflow, lab dan evaluasi sendiri; simpan riwayat pengerjaan |
| Dasar pre-existing boleh dengan deklarasi | R G; S Pasal 5.3 | Catat komponen yang sudah ada sebelum periode program dan kontribusi baru tim |
| Library, API, model AI dan tools pihak ketiga boleh | R G, halaman 6; S Pasal 5.4 | Catat sumber, versi, lisensi/terms dan atribusi pada `third-party.md` |
| Larangan menyerang infrastruktur pihak lain | R N, halaman 9; S Pasal 16.2, halaman 9 | Target hanya portal lab sendiri, akses worker dibatasi profil |
| Data pihak ketiga dan komponen berhak cipta | R G/N; S Pasal 5.5 dan 14 | Pakai data sintetis, komponen dengan hak penggunaan yang sesuai |

Pemilihan Penindakan merupakan interpretasi kecocokan fungsi, bukan klaim bahwa Dukungan Teknologi tidak mungkin diterima. Jika panitia memberi arahan kategori yang berbeda, catat dan sinkronkan semua dokumen.

## 3. Submission: gabungan kelengkapan yang perlu disiapkan

| Artefak | Rujukan | Keputusan implementasi |
| --- | --- | --- |
| Link publik karya yang memungkinkan penilai mencoba/evaluasi | R G, halaman 5; S Pasal 8.2-8.3, halaman 4 | Dipilih repo GitHub publik + paket/petunjuk lokal, tanpa live web; akses harus memungkinkan juri mencoba, bukan hanya membaca source |
| Thumbnail | R G, halaman 5 | 1200 x 630 px; JPG/PNG/WebP; maksimal 500 KB |
| Screenshot | R G, halaman 5 | Maksimal lima gambar antarmuka |
| Video | R G, halaman 5; S Pasal 8.2 | YouTube maksimal 10 menit, menjelaskan manfaat dan cara kerja |
| Slide presentasi | R G; S Pasal 8.2 | Masalah, solusi, fitur, arsitektur, teknologi, evaluasi dan implementasi |
| Dokumentasi teknis | S Pasal 8.2; rubrik R H dan S 9.2 | Arsitektur, instalasi, penggunaan dan kondisi demo |
| Proposal/ringkasan solusi | Rubrik dokumentasi R H dan S 9.2 | Sertakan ringkasan terstruktur; tidak mengarang field upload yang belum terlihat |
| Atribusi/deklarasi | R G; S Pasal 5.3-5.4 | Sertakan daftar komponen dan asal pengerjaan |

R Bagian G dan S Pasal 8.1 sepakat deadline **15 November 2026 pukul 23:59 WIB**. Satu submission per tim; pembaruan sebelum deadline diperbolehkan dan versi terakhir yang dinilai (R G; S 8.5). Tidak ditemukan keharusan membeli VPS atau model merek tertentu.

## 4. Rubrik dan bukti yang disiapkan

| Aspek | Bobot | Bukti tim |
| --- | ---: | --- |
| Relevansi/manfaat | 25% | Kebutuhan validasi laporan dan potensi penerapan IT satuan; data eksternal dengan periode/sumber |
| Inovasi teknis/pemanfaatan AI | 25% | Perencanaan uji, adaptasi observasi, penilaian berbukti; peran model nyata |
| Fungsionalitas purwarupa | 25% | Reproduksi terkontrol, kontrol negatif, bukti, review analis |
| Kelayakan implementasi | 15% | Resource laptop, biaya aktual, cara deploy worker internal |
| Dokumentasi | 10% | Dokumen setup, arsitektur, evaluasi, proposal dan video |

R H, halaman 6 menamai komponen inovasi secara umum; S 9.2, halaman 5 secara eksplisit menekankan AI. Untuk proposal ini, jelaskan kontribusi AI dan tunjukkan integrasi model yang benar-benar berjalan. Mock mendukung pengembangan tetapi tidak menjadi bukti kemampuan model.

Target **20 laporan, 10 valid dan 10 tidak valid**, lab lebih dari 20 titik dengan rancangan 24, serta metrik precision/recall/coverage merupakan keputusan evaluasi tim sendiri; rulebook tidak mewajibkan angka tersebut. Asisten menyusun draf report dan pengguna memverifikasi GT manual.

## 5. Perbedaan dokumen dan tindakan

| Hal | Rulebook | S&K | Penanganan |
| --- | --- | --- | --- |
| Usia | Bagian C menyebut pelajar tanpa minimum yang sama; K juga membahas pemenang di bawah 17 tahun | Pasal 3.2 mewajibkan minimal 17 saat pendaftaran | Pengguna telah mengonfirmasi 17 tahun atau lebih, sehingga memenuhi minimum tersebut. Jangan menggeneralisasi bahwa semua peserta di bawah 17 pasti boleh |
| Webinar kedua | F dan M: 5 November 2026 | Pasal 7.1/20: 27 Oktober 2026 | Rencana kerja memakai 5 November dari rulebook/website; periksa kanal pengumuman resmi untuk pelaksanaan |
| Kelengkapan karya | Thumbnail, screenshot, YouTube, slide dan akses project | Dokumentasi teknis eksplisit ditambah link/video/slide | Siapkan gabungan yang kompatibel, jangan menghilangkan artefak hanya karena tidak disebut pada dokumen lain |
| Golden Ticket | J/K: hanya bagi pemenang di bawah 26; skenario di bawah 17 dijelaskan | Pasal 12 tidak merinci batas usia yang sama | Catat sebagai rincian tambahan rulebook yang perlu dikonfirmasi jika relevan, bukan jaminan hak tiap peserta |

Ketentuan usia Golden Ticket berbeda dari usia minimum pendaftaran. Tidak perlu mengetahui tanggal lahir atau usia persis pengguna untuk menyiapkan draf ide karya ini.

## 6. Final dan hak atas karya

- R I, halaman 6-7 dan S Pasal 10, halaman 5-6: final 24 November 2026 di Hotel Aston Kartika Jakarta; minimal satu perwakilan wajib hadir. Peserta solo berarti hadir sendiri bila terpilih. Ketidakhadiran mengakibatkan gugur sesuai dokumen.
- Presentasi final 10 menit termasuk penjelasan, demo dan tanya jawab. Ini batas terpisah dari video submission maksimal 10 menit.
- R N dan S Pasal 14: HKI karya tetap pada pembuat; penyelenggara memperoleh lisensi untuk kepentingan publikasi/evaluasi yang dijelaskan dokumen. Adopsi oleh PUSSIBERAD dibahas lebih lanjut dengan tim. Baca ketentuan asli sebelum menyetujui.
- Pada 3 November 2026 pengguna menyatakan pendaftaran program diterima; asisten tidak memverifikasi platform. Ini tidak menyatakan lolos final, adopsi instansi atau kemenangan.

## 7. Draft klarifikasi jika diperlukan

Belum dikirim kepada siapa pun:

> Halo panitia, saya peserta solo dengan rencana agen AI untuk mereproduksi klaim laporan kerentanan pada lab milik sendiri. Saya melihat webinar kedua tertulis 5 November pada rulebook dan 27 Oktober pada S&K. Mohon arahan jadwal terbaru. Untuk persiapan submission, saya akan menyiapkan link karya, thumbnail, screenshot, video YouTube, slide dan dokumentasi teknis; mohon arahan jika ada ketentuan upload tambahan pada platform.

Pertanyaan usia di bawah 17 tidak diperlukan untuk pengguna ini karena usia minimal telah dikonfirmasi. Komunikasi keluar hanya dilakukan pengguna atau atas instruksi eksplisit pengguna.
