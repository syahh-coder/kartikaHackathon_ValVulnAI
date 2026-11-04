# Dataset, ground truth, dan evaluasi

Status: rancangan eksperimen. Dataset, label manual, dan hasil model live belum tersedia. Tidak ada angka performa produk yang dapat dipublikasikan saat ini.

Keputusan pengguna **4 November 2026** mengurangi rancangan dari 40 menjadi **20 laporan utama: 10 valid dan 10 tidak valid** untuk membatasi beban GT/evaluasi. Jumlah/metrik ini merupakan rancangan evaluasi tim, bukan kewajiban dari rulebook. Rubrik lomba tetap mengikuti [penyelarasan aturan](rules-alignment.md). Peran model AI perlu diperlihatkan dengan eksekusi nyata dan hasil aktual; benchmark mock tidak memenuhi bukti tersebut.

## 1. Pertanyaan eksperimen

Apakah agent dengan akses pengujian HTTP/browser membuat keputusan validasi yang lebih benar dan berbukti daripada model yang hanya membaca report serta konteks aplikasi?

Pertanyaan tambahan: berapa banyak kasus yang dapat diputuskan, berapa biaya/waktu, dan seberapa sering proses gagal atau ditolak model? Deteksi penulis AI bukan sasaran pengukuran.

## 2. Batas kerja dan biaya

- Pengembang solo, sekitar 30 jam keseluruhan.
- Budget API total maksimal Rp50.000; key belum tersedia.
- Adapter mock digunakan untuk memeriksa plumbing, metrik, dan penanganan error. Hasilnya tidak disajikan sebagai kemampuan Qwen/Gemini.
- Prioritas live adalah satu model/provider yang sama pada baseline A versus B dengan tools (pilihan awal Qwen). Gemini direct Free Tier dapat dipilih sebelum freeze bila lebih layak dalam budget dan lolos probe. Model pembanding dan pengulangan tambahan opsional.
- Minimum pembelian kredit provider diperiksa terpisah dari estimasi token. Ketersediaan akses live belum dianggap terpenuhi.
- Jika live belum tersedia, laporan evaluasi menyatakan eksperimen model belum dilakukan. Demo worker manual/mock tidak menggantikan eksperimen model.

## 3. Dataset utama

| Kategori utama | Kasus | VALID | INVALID |
| --- | ---: | ---: | ---: |
| BAC / IDOR | 8 | 4 | 4 |
| XSS | 8 | 4 | 4 |
| File upload | 2 | 1 | 1 |
| Business logic | 2 | 1 | 1 |
| Total sasaran | 20 | 10 | 10 |

Dua puluh laporan adalah **20 teks report berbeda**, masing-masing dengan satu klaim utama dan kondisi target yang jelas. Menjalankan teks yang sama dua kali tidak menambah jumlah laporan. Dataset seimbang adalah pilihan eksperimen; hasilnya tidak menunjukkan prevalensi bug atau nilai precision pada distribusi laporan nyata secara otomatis.

Target aplikasi tetap lebih dari 20 titik kerentanan: rancangan awal **24 titik**, terdiri dari 8 BAC, 8 XSS, 4 upload, 4 business logic. Peta fitur dan klaimnya ada di [lab-vulnerabilities.md](lab-vulnerabilities.md). Sepuluh area menjadi dasar 10 laporan valid dan 10 laporan keliru yang dapat dibantah; empat titik untuk development, sepuluh lainnya tidak masuk benchmark utama. Pengurangan laporan tidak mengurangi target lab tanpa keputusan baru. Aplikasi yang masih mempunyai 24 bug dapat menerima laporan tidak valid tentang jalur/field aman atau perilaku yang memang diperbolehkan. Jangan membuat seluruh target bersih hanya untuk menghasilkan 10 negatif.

Jumlah 20 adalah target utama terbaru, menggantikan target lama 40. Jika jumlah/GT belum terpenuhi, laporkan kekurangannya dan perbarui scope secara eksplisit sebelum freeze. Kasus ambigu, unsupported atau out-of-scope tidak dipakai sebagai pengisi label tidak valid.

Pembagian 8/8/2/2 memprioritaskan BAC/XSS. Upload dan business logic masing-masing hanya satu pasangan positif/negatif, sehingga metrik kategori itu bersifat deskriptif pada kasus yang diuji. Satu keputusan mengubah strict accuracy kategori dua kasus sebesar 50 poin persentase. Jangan menyebut hasilnya validasi luas kemampuan kategori atau akurasi industri.

### 3.1 Penyusunan 20 laporan oleh asisten

- Asisten menyusun draf setelah endpoint, akun alias, aturan bisnis dan skenario lab tersedia. Saat ini 20 file report belum dibuat.
- Setiap draf memuat judul, target/fitur, klaim, prasyarat, akun alias, langkah reproduksi, hasil yang diklaim, hasil yang diharapkan menurut aturan dan dampak yang diklaim.
- Sepuluh draf positif harus sesuai bug yang benar-benar terbukti; sepuluh draf negatif mengandung klaim spesifik yang dapat dibantah dengan kontrol/bukti, bukan sekadar report tidak lengkap.
- Pasangan positif/negatif tetap dua narasi berbeda dan berada dalam grup yang sama. Jangan hanya mengganti label pada teks identik.
- Gunakan ID publik netral yang tidak mengungkap label; acak ID dan urutan terhadap label. Hindari nama file `valid`, `invalid`, atau pola nomor ganjil/genap yang mengkodekan label.
- Seimbangkan panjang, kualitas bahasa dan detail PoC di kedua kelas. Jangan membuat semua positif rapi dan semua negatif terlihat seperti AI slop.
- Asisten memberikan rancangan label sebagai `draft_expected_label`; `ground_truth` tetap kosong sampai pengguna melakukan verifikasi manual.
- Report sintetis bukan bukti observasi. Jangan membuat log/screenshot sintetis yang dipresentasikan sebagai evidence pengujian aktual.
- Simpan teks input agent terpisah dari manifest jawaban dan peta bug. Manifest memetakan report -> fitur/bug -> bukti manual -> label final.
- Jika label rencana tidak sesuai hasil manual, perbaiki/ganti draf sebelum freeze sambil mempertahankan 10/10; jangan memaksakan label.

Asisten pembuat lab dan report mengetahui rancangan jawaban, sehingga dataset ini sintetis dengan keterbatasan bias desain. Runtime agent tidak mendapat pengetahuan tersebut. Jangan mengklaim review label independen tanpa reviewer lain yang benar-benar terlibat.

## 4. Identitas dan label kasus

Manifest evaluator minimum:

```text
case_id, report_id, primary_claim, primary_category, secondary_tags
scenario_id, root_cause_group, report_variant_group
target_build, condition_id, seed_id
draft_expected_label: VALID | INVALID
verification_status: DRAFT | MANUALLY_VERIFIED | UNCERTAIN
ground_truth: null | VALID | INVALID | UNCERTAIN
ground_truth_reason, manual_evidence_refs, precondition_assertions
split: development | held_out
reviewed_at, dataset_version
```

Agent mendapat report, konteks target dan aturan bisnis yang relevan. Agent tidak mendapat `ground_truth`, alasan GT, kondisi target, catatan pembuat bug, atau bukti jawaban evaluator.

`INVALID` memerlukan dasar: perilaku sesuai aturan, klaim dampak terbantahkan, atau prasyarat klaim memang tidak terpenuhi setelah diperiksa. PoC gagal, model menolak, atau informasi kurang tidak cukup menjadi label `INVALID`.

`UNCERTAIN` dikeluarkan dari set biner sebelum freeze, dengan jumlah/alasan tetap dilaporkan. Kasus kurang informasi, out-of-scope, dan unsupported masuk set operasional terpisah.

## 5. Ground truth dan kualitas label

1. Tetapkan aturan akses/bisnis dan klaim spesifik.
2. Buat seed serta verifikasi kondisi target.
3. Reproduksi manual dampak dan kontrol/perbaikan.
4. Simpan bukti yang menghubungkan aktor, tindakan dan dampak.
5. Tetapkan label dengan alasan dan evidence reference.
6. Buat assertion untuk mendeteksi kondisi lab yang berubah.
7. Tinjau ulang label dan kasus ambigu sebelum freeze.

Pembuat target merangkap evaluator sehingga review tidak independen. Nyatakan keterbatasan tersebut; review eksternal hanya boleh diklaim setelah benar-benar dilakukan.

Untuk XSS/file upload, bukti perlu menunjukkan dampak sesuai klaim. Untuk business logic, aturan harus tersedia bagi agent; label tidak boleh bergantung pada aturan rahasia.

## 6. Group split dan pencegahan kebocoran

- Set utama adalah 20 laporan final. Development memakai titik cadangan BAC-08, XSS-08, UP-04 dan BL-04 dengan contoh/probe terpisah; tidak mengambil sebagian dari 20 laporan untuk tuning.
- Sepuluh area evaluasi awal adalah BAC-01..04, XSS-01..04, UP-01 dan BL-01. Setiap area menyumbang satu positif dan satu negatif, total 20 teks laporan.
- Sepuluh titik non-benchmark adalah BAC-05..07, XSS-05..07, UP-02..03 dan BL-02..03. Tetap bagian rancangan lab 24 titik, bukan tambahan kasus utama atau cadangan yang boleh dipilih setelah melihat hasil. Perubahan alokasi wajib sebelum freeze dengan grouping akar masalah diperiksa ulang.
- Semua kondisi rentan/perbaikan, variasi objek/akun dan parafrasa dari akar masalah yang sama berada pada split yang sama.
- Penggunaan jalur kode/pemeriksaan akses bersama dapat mengharuskan beberapa skenario masuk satu `root_cause_group`.
- Alokasi ID adalah rancangan awal. Jika titik development dan evaluasi berbagi akar masalah implementasi, revisi alokasi atau implementasinya sebelum freeze. Jangan mengklaim held-out independen hanya berdasarkan ID berbeda.
- Kasus upload-XSS yang berasal dari akar masalah sama tidak dipisahkan hanya karena tag kategorinya berbeda.
- Jika kuota per kategori bertentangan dengan grouping, utamakan grouping dan laporkan jumlah aktual.
- Minimal ada grup development dan grup held-out untuk setiap kategori yang dievaluasi; bila tidak tersedia, jangan klaim generalisasi held-out kategori itu.
- Sembunyikan nama kondisi, header debug, scoreboard, source evaluator, dan label dari konteks model.
- Buat snapshot/hash dataset sebelum live held-out; simpan versi prompt, tools, target, model dan provider.

Parafrasa menilai ketahanan terhadap format, bukan menambah bukti independen. Laporkan jumlah kasus, jumlah grup bug, dan jumlah pengulangan secara terpisah.

## 7. Konfigurasi eksperimen

| ID | Konfigurasi | Penggunaan |
| --- | --- | --- |
| A | Model/provider dibekukan (awal Qwen) + report + scope + aturan/prasyarat; tanpa hasil eksekusi | Baseline keputusan dokumen |
| B | Model/provider dan konteks yang sama dengan A + tools HTTP/browser | Sistem utama |
| C | Model pembanding + konteks/tools/batas setara B | Opsional jika waktu/budget cukup |

Pada development, mulai empat smoke probe dari empat titik cadangan; tambah kontrol negatif pada titik yang sama jika biaya memungkinkan. Probe development tidak dimasukkan ke angka 20 laporan utama. Tidak perlu menguji semua kandidat model sebelum satu alur dapat berjalan.

Prioritas held-out adalah satu run A dan satu run B per kasus. Pengulangan tambahan menggunakan daftar kasus yang dipilih sebelumnya dan dilaporkan terpisah. Model ID/provider dan setiap perpindahannya dicatat; jangan mencampur hasil berbagai konfigurasi tanpa label.

Fallback multi-provider untuk demo mengikuti prd.md, tetapi **dimatikan pada benchmark**, termasuk provider routing otomatis gateway. A dan B memakai model/provider yang sama pada seluruh set terjadwal. Jika memilih Gemini sebagai primary sebelum freeze, gunakan Gemini pada kedua arm; jangan melaporkannya sebagai hasil Qwen. Outage/limit saat benchmark tetap error/nondecision pada percobaan terjadwal, bukan dialihkan diam-diam. Eksperimen konfigurasi baru dilaporkan terpisah; pergantian model tidak menambah jatah 20 kasus utama atau menghapus hasil gagal.

A diberi konteks bisnis yang sama, tetapi tidak diberi evidence hasil B. B tidak membaca label atau bukti manual GT. Perbandingan A/B mengukur tambahan akses eksekusi dan workflow, bukan membuktikan bahwa model dasarnya berubah lebih pintar.

### 7.1 Pisahkan prediksi baseline dari verdict teknis

Baseline A tidak mempunyai observasi pengujian. Karena itu output A adalah `DocumentPrediction`, **bukan** `Assessment` teknis dengan label CONFIRMED/REFUTED. Jangan memaksa A melewati verifier bukti eksekusi lalu menilai semua jawabannya gagal; hal itu membuat perbandingan tidak adil.

```text
DocumentPrediction:
run_id, claim_id, predicted_label: VALID | INVALID | ABSTAIN
reasoning, missing_information, execution_evidence_available: false
model_id, inference_provider, prompt_version, usage, error_code
```

Model/provider dan konteks awal A/B sama; keduanya menerima snapshot klaim/aturan yang sama tanpa hasil parse run lain atau GT. A memakai satu respons klasifikasi terstruktur tanpa tools target. B boleh memakai loop terbatas, sehingga tambahan komputasi, biaya dan waktu harus dilaporkan; ini perbandingan sistem dengan/tanpa eksekusi, bukan ablation komputasi setara. Satu run A dan satu run B pada 20 report berarti **40 run**, bukan 40 panggilan API. B dapat memerlukan banyak panggilan; cap 12 panggilan/run pada 20 B dan satu panggilan/run pada 20 A berarti batas awal hingga 260 panggilan, sebelum development/chat. Retry tetap di dalam cap run, bukan tambahan di luarnya.

Normalisasi scoring pada masing-masing arm:

| Arm/output | Keputusan evaluasi | Label pada laporan/UI |
| --- | --- | --- |
| A `VALID` | POSITIVE | Prediksi dokumen: valid, belum direproduksi |
| A `INVALID` | NEGATIVE | Prediksi dokumen: tidak valid, belum direproduksi |
| A `ABSTAIN`/error/refusal/tanpa output valid | NONDECISION | Belum dapat diprediksi / sebab proses |
| B `CONFIRMED` setelah verifier | POSITIVE | Klaim terbukti dengan bukti yang dirujuk |
| B `REFUTED` setelah verifier | NEGATIVE | Klaim terbantahkan dengan kontrol/bukti |
| B `INCONCLUSIVE`/error/refusal/verdict null | NONDECISION | Belum dapat dipastikan / sebab proses |

Hitung metrik A dan B terpisah dengan denominator 20 per arm; jangan menjumlahkannya menjadi satu hasil 40 kasus independen. Tampilkan juga matriks native masing-masing arm agar prediksi A tidak disamarkan sebagai bukti. Untuk B, simpan respons model mentah dan assessment hasil verifier terpisah; metrik utama adalah sistem B setelah verifier, metrik output model mentah hanya tambahan berlabel jelas. Koreksi admin tidak mengganti keduanya.

## 8. Prosedur run

1. Pastikan dataset dan konfigurasi telah dibekukan.
2. Pilih urutan kasus dengan seed pengacakan yang dicatat.
3. Reset target, akun/session dan browser; periksa health serta prasyarat.
4. Mulai satu run dan simpan input persis yang diterima model.
5. Catat tool calls, observasi, evidence, usage, biaya dan status.
6. Simpan assessment mentah model serta hasil verifikasi aplikasi.
7. Normalisasi status menjadi matriks keluaran tanpa menghapus kegagalan.
8. Jalankan pemeriksaan evaluator; catat kontaminasi atau masalah lingkungan.
9. Hitung metrik setelah seluruh batch yang direncanakan selesai.

GT dan assertion tidak diberikan kembali ke agent selama run. Setelah held-out dilihat untuk tuning, tandai data sudah terpakai dan sediakan test baru atau ungkap bahwa hasilnya bukan held-out murni lagi.

## 9. Metrik dengan abstention

Utamakan set in-scope, kategori yang dideklarasikan didukung, prasyarat lengkap dan GT biner. Agent yang salah menganggap kasus tersebut unsupported tetap dihitung sebagai nondecision; tidak mengeluarkan kasus itu dari denominator.

```text
TP = GT VALID dan keputusan POSITIVE
FP = GT INVALID dan keputusan POSITIVE
FN = seluruh GT VALID yang tidak mendapat POSITIVE
TN = GT INVALID dan keputusan NEGATIVE

precision = TP / (TP + FP)
recall = TP / (TP + FN)
F1 = 2 * TP / (2 * TP + FP + FN)
strict_accuracy = (TP + TN) / N_kasus_utama
coverage = N_dengan_POSITIVE_atau_NEGATIVE / N_kasus_utama
```

Jika 20 label telah diverifikasi sesuai komposisi, `N_kasus_utama=20` dan jumlah GT valid=10. Maka recall=`TP/10`, strict accuracy=`(TP+TN)/20`, dan coverage=`N_diputuskan/20`. Precision tetap `TP/(TP+FP)`; pembaginya tidak otomatis 10. Satu keputusan salah mengubah strict accuracy 5 poin persentase. Target seimbang mempermudah pembacaan hitungan, tetapi tidak menghilangkan abstention dan error.

`FN` adalah miss untuk tujuan mendeteksi temuan valid dan mencakup hasil belum pasti serta kegagalan proses pada GT valid. GT invalid yang belum diputuskan bukan TN. Tampilkan matriks native per arm: A terhadap VALID/INVALID/ABSTAIN/error; B terhadap CONFIRMED/REFUTED/INCONCLUSIVE/status tanpa verdict. Jangan memaksakan empat hitungan di atas menjadi matriks biner penuh.

Denominator nol menjadi `N/A`, dengan jumlah mentah. F1 dihitung langsung dari TP/FP/FN, bukan melalui precision yang mungkin N/A: jika TP=FP=0 dan FN=10, precision=N/A, recall=0 dan F1=0. Jika TP=0, FP=2 dan FN=10, precision=recall=F1=0. F1 baru N/A jika `2*TP+FP+FN=0`. Run error/refusal/timeout tetap berkontribusi pada denominator strict accuracy dan coverage. Accuracy pada subset yang diputuskan boleh ditambahkan dengan nama yang jelas, bukan menggantikan hasil seluruh set.

Contoh pemeriksaan metrik buatan, **bukan hasil model**:

- GT valid: dua confirmed, satu refuted, satu inconclusive.
- GT invalid: satu confirmed, dua refuted, satu provider refusal.
- TP=2, FP=1, FN=2, TN=2, N=8.
- Precision=2/3, recall=1/2, F1=4/7, strict accuracy=4/8, coverage=6/8.

Perhitungan ini perlu diperiksa dengan tes kecil saat modul metrik dibuat.

Macro-F1 yang dilaporkan adalah rata-rata F1 positif per kategori utama, bukan rata-rata semua run atau akurasi kategori. Tampilkan keempat nilai kategori dan jumlah yang dapat dihitung; kategori N/A tidak diam-diam dibuang untuk menaikkan agregat. Pada target dataset lengkap, setiap kategori memiliki GT positif sehingga F1 tetap dapat dihitung walau tidak ada prediksi positif.

### 9.1 Run terputus dan gangguan lingkungan

Jika assertion pra-run gagal sebelum model/worker mulai, catat `NOT_STARTED`; perbaiki lingkungan lalu jalankan percobaan terjadwal. Jangan menyajikan metrik 20 kasus selesai bila masih ada yang belum dimulai. Setelah percobaan benar-benar mulai, timeout, crash, refusal dan gangguan target tetap menjadi hasil percobaan itu dan masuk denominator; tidak otomatis diulang sampai benar. Percobaan tambahan untuk diagnosis dipisahkan dari run utama yang sudah dipilih. Pemilihan run utama dilakukan sebelum melihat label/hasil, bukan memakai hasil terbaik dari banyak percobaan.

Set operasional terpisah minimum mencakup OOS, UNKNOWN/prasyarat kurang, kategori unsupported, instruksi prompt injection dan pencabutan scope/cancel. Ukur perilaku proses dan jumlah akses target yang terjadi; bukan mengisinya sebagai GT INVALID pada 20 report utama. Kasus keamanan tool/network lain mengikuti [security-review.md](security-review.md).

## 10. Pelaporan tambahan

- Angka mentah, precision/recall/F1, strict accuracy dan coverage per kategori serta keseluruhan.
- Jumlah grup akar masalah, distribusi label, dan pengulangan.
- Refusal pada tugas lab berizin, schema error, rate limit, timeout dan kegagalan tools/lingkungan, masing-masing terpisah.
- Waktu wall-clock, token input/output, biaya per run dan biaya per temuan benar.
- Mutu evidence: identitas aktor/objek, kriteria dampak, kontrol, referensi artefak dan keterbatasan.
- Percobaan keluar scope dan jumlah yang benar-benar dieksekusi.
- Jika menghitung interval ketidakpastian, unit sampling adalah grup akar masalah; jangan memperlakukan parafrasa/pengulangan sebagai independen.

Dengan sampel kecil, satu kesalahan bisa mengubah persentase banyak. Hindari klaim kemampuan seluruh aplikasi atau seluruh keluarga bug berdasarkan lab ini.

## 11. Waktu analis

Ukur waktu aktif manusia terpisah dari durasi inference. Catat membaca laporan, menyiapkan akun, menjalankan pengujian, memeriksa evidence, mengoreksi agent, dan menyusun hasil.

Gunakan kasus setara atau urutan yang diseimbangkan. Dokumentasikan bahwa pembuat lab mengenal bug dan dapat mengalami efek belajar. Penghematan tidak diisi sebelum diukur dan kualitas keputusan dibandingkan.

## 12. Artefak hasil

Rencanakan manifest dataset beku, `runs.jsonl`, matriks keluaran, ringkasan metrik CSV/JSON, konfigurasi eksperimen, ledger biaya, dan evidence tersanitasi. File tersebut dibuat ketika eksperimen tersedia; saat ini tidak ada hasil yang diisi.

Pisahkan hasil mock, replay dan live. Exporkan hasil mentah sebelum koreksi analis, lalu simpan koreksi sebagai lapisan tambahan. Jangan mengganti keputusan agent dengan jawaban manual lalu melaporkannya sebagai akurasi agent.
