# Scope submission setelah review M6

**Penyelesaian kode13 November2026:** AI TEXT-ONLY dapat mengisi draf klaim v2 yang harus dikonfirmasi pemilik sebelum run. Model tidak menetapkan scope/izin atau mengakses worker langsung; tiga subtype dan fixture tetap. OpenRouter utama/Azure cadangan dipilih eksplisit, tanpa fallback otomatis. [Implementasi](ai-validation-integration.md), [review terakhir](manual-final-review.md). Tidak memperluas M6 atau mengubah kebutuhan GT/live/evaluasi.

**Checkpoint implementasi terbaru:** seluruh kode independen sisa R3 dan persiapan R4 telah disiapkan menjadi paket lokal READY_FOR_REVIEW_WITH_PENDING_INPUTS. [Indeks pengguna](final-review.md), [hasil R3/R4](r3-r4-verification.md). Runner/builder/freeze gate tersedia, tetapi GT0, bukti kandidat belum terikat, key/profil live belum tersedia dan benchmark belum berjalan. M6 tetap DEFERRED; publikasi menunggu review. Bagian yang menyebut belum ada runner menggambarkan keadaan saat keputusan scope awal.

Keputusan aktif **7 November 2026**, setelah pengguna menyetujui rekomendasi penyempitan scope dan meminta dokumentasi serta prompt lanjutan. Ini perubahan rencana, bukan bukti implementasi. Dokumen ini memiliki keputusan cakupan submission; detail eksperimen berada di [evaluation.md](evaluation.md), urutan pekerjaan di [implementation.md](implementation.md), dan instruksi batch berikutnya di [execution-prompt.md](execution-prompt.md).

## 1. Masalah yang dihentikan

**Penegasan pengguna 7 November:** skip pekerjaan M6 yang belum dapat diselesaikan dan lanjut ke checkpoint berikutnya. Status M6 asli sekarang **DEFERRED untuk submission**. Tujuh BAC (BAC-01..07) dan empat business logic (BL-01..04) tidak dikejar pada jalur aktif. Jangan menjadikan angka 13/24 atau gate lama sebagai blocker R2, dan jangan mengulang pengujian M6 untuk melaporkan angka yang sama. Status katalog PLANNED dan riwayat bukti tetap jujur; DEFERRED adalah keputusan pekerjaan, bukan label kebenaran report atau kelulusan teknis.

M6 asli menggabungkan validator business logic dan kelengkapan 24 titik. Source saat review masih menyediakan validator BAC-08, XSS-08 dan UP-04; BUSINESS_LOGIC tidak didukung. Katalog mencatat 13 reproduksi operator historis dan 11 PLANNED. Parser, auditor rekaman dan workflow admin tidak menyelesaikan kekurangan tersebut. Jumlah tes bukan persentase penyelesaian M6.

Jangan menambah auditor, ekspor atau layar review bisnis sebagai pekerjaan utama berikutnya. Pertahankan fitur yang sudah ada. Hentikan perluasan lab sampai jalur submission minimum terbukti.

## 2. Produk submission yang dituju

Tujuan menerima dan membantu memeriksa tumpukan laporan tetap dipertahankan. Submission dibatasi menjadi **triage berbantuan AI, pemeriksaan produk terdaftar yang sudah tersedia, dan ringkasan bukti untuk admin**. Ini lebih sempit daripada rencana awal agent eksploitasi adaptif.

| Bagian | Scope aktif | Batas klaim |
| --- | --- | --- |
| Intake | Login, chat/upload TXT/MD, scope admin terversi, kepemilikan | Report dan output model tidak memberi izin transport |
| AI | Ekstraksi klaim, saran kelengkapan/scope/capability, prediksi dokumen dan ringkasan bukti | Output terstruktur divalidasi server; bukan verdict teknis atau keputusan izin |
| Pemeriksaan lab | Pertahankan jalur produk BAC-08, XSS-08 dan UP-04 yang sudah ada | Subtype/fixture tetap, dipicu melalui tindakan eksplisit pengguna dan policy lama; bukan dukungan umum semua BAC/XSS/upload |
| Model dan worker | Integrasi model tahap awal hanya teks; tanpa tool calling atau dispatch worker dari model | Tidak mengubah PoC bebas menjadi script, payload atau rangkaian eksploitasi otomatis |
| Bukti | Evidence dari aplikasi tetap terpisah dari prediksi/ringkasan model | Upload rekaman yang konsisten tidak membuktikan dampak/asal/izin aktor |
| Business logic | Pesan belum didukung untuk validasi lab; review rekaman lama tetap berlabel | Tidak menjadi salah satu kategori benchmark biner aktif |
| Distribusi | Paket lokal di repo GitHub, video, slide dan gambar | Tidak membuat live web/cloud; publikasi baru bukan bagian batch dokumentasi ini |

UI harus memperlihatkan model/provider aktual, mode mock/live/replay, status target, hasil verifier dan teks AI secara terpisah. Bila AI aktif tetapi planner pemeriksaan tetap deterministik, sebutkan tepat demikian. Klaim “agent memilih dan mengeksekusi eksploitasi secara mandiri” tidak termasuk scope ini.

## 3. Evaluasi submission

- Protokol baru `functional-v2`: target **20 teks laporan, 10 VALID dan 10 INVALID** setelah GT manual.
- Alokasi kerja: 8 BAC, 8 XSS, 4 upload, terbatas pada tiga jalur produk di atas. Pembagian lama 8/8/2/2 diarsipkan, bukan dipenuhi lewat label palsu pada BUSINESS_LOGIC.
- Kasus berasal dari mekanisme yang sudah digunakan development. Ini benchmark fungsional skenario yang dikenal, **bukan held-out akar masalah baru**. Jumlah laporan, skenario, akar masalah dan kondisi harus dilaporkan terpisah.
- A membaca report + scope/aturan; B membaca konteks yang sama + bukti tersanitasi yang tersedia. Perbandingan mengukur kontribusi konteks bukti, bukan otonomi agent. Output model dan verifier dilaporkan terpisah.
- Jumlah 20/10/10 tidak menjamin GT tersedia. Jika klaim di luar subtype, bukti tidak cukup atau label belum sah, jangan mengisi INVALID untuk mengejar kuota. Laporkan kekurangan dan jangan mengklaim eksperimen lengkap.
- GT, peta bug dan katalog tidak masuk konteks model. Report teks final tidak dipakai untuk tuning setelah freeze, meskipun mekanisme development memang sudah dikenal.

## 4. M6 asli dan gate lama

Target 24 titik **dipindahkan menjadi backlog dan tidak dikerjakan untuk submission ini**, bukan diturunkan seolah semua persyaratan sudah terpenuhi. Status pekerjaan M6 asli DEFERRED; catatan teknis historis tetap 13/24, 11 PLANNED, validator BUSINESS_LOGIC belum ada dan konflik grup development/evaluasi tetap tercatat.

`evaluator/catalog.json`, `evaluator/development_history.py`, manifest M5 dan `catalog_audit --require-ready` tidak diubah untuk meluluskan submission. Exit 2 tetap berarti protokol lama belum siap. Pemeriksaan kesiapan `functional-v2` kelak terpisah dan harus memeriksa kapabilitas produk, label/binding bukti, freeze dan akses model yang nyata; pada keputusan ini belum ada runner/gate v2.

Rencana ketat sebelumnya disimpan di [evaluation-v1.md](evaluation-v1.md). Dokumen verifikasi M1–M6f dan riwayat grup dipertahankan. Bila proyek kelak melanjutkan M6 asli, terapkan checkpoint aslinya; keberhasilan submission sempit tidak mencentang M6.

## 5. Urutan dan syarat berhenti

**Instruksi terbaru pengguna:** kerjakan seluruh bagian yang independen sampai paket konkret siap direview sekaligus. Urutan di bawah menjadi checkpoint internal, bukan batas satu turn atau permintaan izin rutin. Bila GT/key/bukti belum ada, tuntaskan kode, tes terarah dan bahan submission yang dapat dibuat. Siapkan usulan/referensi review terpisah tanpa mengisi GT final atau mengatasnamakan penerimaan manusia. Gunakan [prompt berkelanjutan](execution-prompt.md) dan laporkan satu `docs/final-review.md` di akhir.

READY_FOR_REVIEW berarti paket bisa ditinjau, bukan seluruh klaim telah terbukti. Jika prasyarat nyata masih pending, beri status READY_FOR_REVIEW_WITH_PENDING_INPUTS. Status live/freeze/evaluasi tetap terpisah. Video/slide/thumbnail/screenshot yang tersedia diberi lokasi nyata; draft/naskah bukan video final atau tautan publik. Publikasi repo/release, upload eksternal dan submit formulir menunggu review pengguna. Tidak membeli akses untuk menghilangkan status pending.

1. **R1: CODE_TESTED.** Adapter/triage tersedia menurut [hasil R1](r1-verification.md). LIVE_VERIFIED masih CONFIGURATION_REQUIRED; tidak mengulang implementasi atau tesnya tanpa perubahan terkait.
2. **R2: CODE_TESTED dan QA lokal lulus.** UI triage dan ringkasan observasi terstruktur aplikasi, dengan enforcement serta pemisahan model/verifier. [Hasil R2](r2-verification.md). Tidak ada workflow lab baru, inference ringkasan tambahan atau pembaruan service aktif.
3. **R3: persiapan R3a CODE_TESTED, belum lulus keseluruhan.** [Peta capability/bukti](r3-capability-map.md), 20 kandidat/CSV GT kosong, jadwal NOT_STARTED dan scorer offline tersedia. Berikutnya review GT pengguna, projection B, integrasi prediksi/runner A/B, freeze dan live. Tanpa GT/live/evidence yang sesuai, benchmark belum dimulai. [Hasil R3a](r3-verification.md).
4. **R4: paket submission.** Quick start yang diuji dari kondisi bersih, hasil aktual/keterbatasan, video maksimal 10 menit, slide publik, thumbnail 1200x630 maksimal 500 KB dan maksimal lima screenshot.

Key belum tersedia bukan alasan kembali mengerjakan auditor bisnis: tuntaskan kode adapter/tes konfigurasi dan checkpoint yang independen, lalu laporkan input yang benar-benar dibutuhkan. Tidak membeli kredit atau mengaktifkan billing/cloud, tidak membaca/menampilkan secret yang tidak diperlukan, tidak reset data/ledger, dan tidak otomatis commit/push/release.

Pemeriksaan hemat: satu suite terarah untuk perubahan batch dan satu QA flow baru bila UI berubah. Setelah lulus, lanjut checkpoint; retest/perluas hanya karena perubahan, kegagalan atau risiko regresi konkret. Jangan mengulang seluruh suite historis atau membuat tes administratif tambahan untuk M6 yang sudah DEFERRED. Ini bukan menghapus tes keamanan yang relevan atau mengklaim fitur lulus tanpa bukti.

Deadline dokumen lomba tetap 15 November 2026 pukul 23:59 WIB. Ini prioritas kerja, bukan jaminan selesai. Bila akses model nyata tetap belum ada, laporkan bahwa fitur AI belum terbukti; jangan menggantikannya dengan mock tanpa label.
