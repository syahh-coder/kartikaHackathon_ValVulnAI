# Evaluasi fungsional ValVuln AI

**Status terbaru R3b–R4:** builder konteks A/B, schema prediksi terhubung adapter, dispatch ledger bersama, freeze gate, runner/export/recover dan laporan tersedia serta CODE_TESTED dengan simulasi. [Runbook](r3-runbook.md), [hasil/batas](r3-r4-verification.md), [review akhir](final-review.md). Target20 kandidat tetap GT0; bukti kasus, live/smoke/freeze dan benchmark nyata belum ada. Status R3a dan kalimat “runner belum dibuat” di bawah mencatat tahap persiapan sebelumnya; bukan status source terbaru. Scorer worksheet/offline tetap tidak mengesahkan benchmark.

Protokol aktif **functional-v2, 7 November 2026**, mengikuti [scope submission](submission-scope.md). **R3a persiapan CODE_TESTED:** [peta subtype/bukti](r3-capability-map.md), 20 kandidat teks/CSV GT kosong, jadwal NOT_STARTED, schema prediksi dan scorer rekaman offline tersedia. [Hasil/batas R3a](r3-verification.md). Belum ada dataset/GT final, projection konteks B, runner dispatch A/B, freeze, model live atau hasil benchmark. Protokol ketat sebelumnya tetap di [evaluation-v1.md](evaluation-v1.md); gate lama tidak dinyatakan lulus.

## 1. Pertanyaan dan batas klaim

Pada skenario lab terkontrol yang mekanismenya sudah dikenal saat development, apakah tambahan bukti yang relevan membantu model menilai klaim dibanding membaca dokumen saja?

Ini evaluasi fungsional dalam tiga jalur produk yang tersedia: BAC-08, XSS-08 dan UP-04. Tidak mengukur kemampuan menemukan kerentanan baru, generalisasi akar masalah, kualitas seluruh report dunia nyata, deteksi tulisan AI, atau eksekusi agent otonom. Nama kategori tidak berarti semua subtype dalam kategori didukung.

Model awal hanya memproses teks. Model tidak memilih tindakan jaringan, menjalankan PoC atau mengirim instruksi ke worker. Bukti B diperoleh dari pemeriksaan produk yang dipicu secara eksplisit/operator sesuai kontrol yang sudah ada; tidak dibuat dari jawaban model. Rekaman administratif CONSISTENT sendiri bukan bukti kerentanan.

## 2. Dataset dan GT

| Jalur produk | Target teks | GT VALID | GT INVALID |
| --- | ---: | ---: | ---: |
| BAC-08 | 8 | 4 | 4 |
| XSS-08 | 8 | 4 | 4 |
| UP-04 | 4 | 2 | 2 |
| Total target | 20 | 10 | 10 |

Alokasi 8/8/4 menggantikan alokasi kategori lama 8/8/2/2 khusus submission functional-v2. Business logic, OOS, UNKNOWN, unsupported dan klaim ambigu berada pada set operasional terpisah; tidak dihitung sebagai GT INVALID.

1. Sebelum membuat draf, petakan field/klaim yang benar-benar bisa diperiksa tiap validator dan bukti yang diperlukan. Jangan menganggap menjalankan fixture yang sama membuktikan setiap variasi klaim.
2. Asisten menyusun 20 teks berbeda setelah peta tersebut tersedia. GT belum final hanya karena asisten menulis label draf. Parafrasa bukan skenario/akar masalah baru.
3. Pengguna menetapkan GT per klaim terhadap kondisi/snapshot target dan bukti relevan, termasuk pembanding. Label VALID memerlukan dampak sesuai klaim; INVALID memerlukan bantahan/kontrol yang memadai. Kondisi fixed saja tanpa bukti terkait klaim tidak otomatis cukup.
4. Jika satu teks dijalankan pada dua kondisi, catat sebagai dua percobaan dari teks yang sama; jangan menghitungnya sebagai dua teks berbeda. Berikan ID report netral dan kelompokkan varian terkait.
5. Jika tidak tersedia 20 teks yang layak dengan GT 10/10, jangan menciptakan variasi kosong untuk memenuhi kuota. Catat kekurangan; perubahan target berikutnya perlu dinyatakan sebelum freeze.

Manifest privat minimal: report_id, report_hash, capability/subtype, scenario_id, root_cause_group, report_variant_group, target_snapshot/condition, scope/rules version, GT, alasan dan evidence_reference manual. Kondisi/GT evaluator, katalog dan nama file yang mengkodekan label tidak diberikan kepada model.

## 3. Pemisahan data dan freeze

Mekanisme pada set ini sudah dipakai development sistem. Riwayat BAC-08, XSS-08 dan UP-04, termasuk overlap HTML UP-04/XSS, tetap disimpan. **Tidak memakai istilah held-out independen untuk set ini.** Jangan mengganti nama grup agar tampak baru.

Contoh pengembangan teks/prompt dipisahkan dari 20 teks final menurut report_variant_group sejauh tersedia; catat persinggungan yang tidak dapat dihindari. Pemisahan teks ini tidak menghapus paparan mekanisme. Laporkan jumlah teks, kondisi, skenario dan grup aktual; beberapa laporan per grup tidak dianggap observasi independen untuk klaim statistik.

Sebelum evaluasi: bekukan manifest/hash laporan dan GT privat, aturan/scope, bukti yang akan diterima B, versi source/tool/verifier, prompt/schema, model/provider aktual, parameter generasi, urutan, batas waktu/token/biaya dan kebijakan error. Koreksi setelah melihat hasil dicatat sebagai eksperimen development baru, bukan menggantikan hasil utama.

## 4. A dan B

| Bagian | A: dokumen | B: dokumen + bukti |
| --- | --- | --- |
| Input bersama | Report, scope/aturan terversi, konteks publik minimum | Input A yang sama |
| Tambahan | Tidak ada bukti target | Observasi relevan yang sudah disanitasi dan terikat kasus |
| Output model | VALID / INVALID / ABSTAIN, alasan dan referensi input | Schema yang sama, dengan referensi bukti bila tersedia |
| Transport dari model | Tidak ada | Tidak ada |

GT dan jawaban akhir verifier/admin tidak dimasukkan ke prompt A/B. Input B harus berupa observasi, bukan kolom label kondisi, verdict, alasan GT atau narasi operator yang membocorkan jawaban. Server memeriksa kepemilikan, binding report/snapshot/aturan dan redaksi sebelum membangun konteks. Jika B belum mempunyai bukti yang sesuai, jangan mengambil bukti kasus lain atau membuatnya; catat NOT_STARTED sebelum percobaan atau ABSTAIN/error bila percobaan sudah berjalan sesuai protokol freeze.

Metrik utama v2 membandingkan **prediksi model A dan B** terhadap GT yang sama. Hasil verifier produk disajikan terpisah dengan mode dan asal bukti; output model tidak menimpa CONFIRMED/REFUTED. Ini perubahan dari metrik sistem B protokol lama. Jika dua respons memakai bukti yang sama, jelaskan bahwa ini evaluasi penalaran atas rekaman terkontrol, bukan pengujian ulang target per respons.

Rencana minimum satu respons terjadwal per arm per report: 40 respons sukses untuk 20 report bila lengkap. Ini bukan jaminan 40 panggilan: attempt gagal/retry, smoke development dan ringkasan UI dihitung di ledger yang sama. B bukan loop agent 12 panggilan protokol lama. Satu retry maksimum per respons hanya untuk gangguan sementara, sebelum respons sukses dikonsumsi, tunduk pada cap run/deadline/anggaran yang sudah ada. Tidak retry refusal/schema/policy untuk mencari jawaban lebih baik. Catat semua attempt; respons utama dipilih menurut aturan sebelum melihat hasil.

## 5. Metrik dan kegagalan

Untuk setiap arm pisahkan TP, FP, TN, FN, abstention pada GT positif/negatif, error, NOT_STARTED, biaya/token/waktu. Simpan keluaran mentah sebelum koreksi manusia. Jangan membuang timeout, refusal, parse error atau hasil tidak menguntungkan.

- Precision = TP / (TP + FP), N/A jika denominator nol.
- Recall end-to-end = TP / seluruh GT positif terjadwal. Jika 10 positif, denominator 10; abstention/error positif tidak dihitung TP dan tidak boleh menghilang dari denominator.
- Strict accuracy = (TP + TN) / seluruh kasus terjadwal; target lengkap denominator 20 per arm.
- Coverage = jumlah prediksi VALID/INVALID yang sah / seluruh kasus terjadwal.
- F1 = harmonic mean precision dan recall end-to-end jika terdefinisi. Jika precision atau recall tidak terdefinisi, F1 N/A; jika keduanya terdefinisi dan nol, F1 nol.

FN pada confusion matrix prediksi tegas berarti prediksi INVALID pada GT positif. Untuk rumus F1 langsung 2TP/(2TP+FP+FN_effective), FN_effective harus memasukkan seluruh GT positif yang tidak menghasilkan TP, termasuk abstention/error; jangan mencampur FN tegas dengan recall end-to-end. Tampilkan hitungan abstention/error secara terpisah agar denominator dapat diperiksa.

Satu kasus mengubah strict accuracy 5 poin persentase pada N=20. Contoh manual: TP=8, FP=1, TN=7, FN tegas=1, abstain positif=1 dan abstain negatif=2. Jumlah=20; precision=8/9, recall=8/10, strict accuracy=15/20, coverage=17/20, FN_effective=2 dan F1=16/19. Periksa pula kasus tanpa prediksi, nol GT positif dan semua prediksi salah sebelum memakai runner. Jangan mengklaim signifikansi statistik atau precision populasi nyata dari dataset seimbang kecil ini.

Laporkan kasus belum dimulai dan persentase kelengkapan. Jangan menyebut hasil 20 kasus selesai bila belum seluruhnya dimulai/diselesaikan; skor konservatif terhadap jadwal boleh ditampilkan dengan label jelas. Perbandingan A/B menggunakan report/GT yang sama, bukan subset terbaik untuk setiap arm.

## 6. Keamanan, budget dan kesiapan

Set operasional terpisah mencakup OOS/UNKNOWN/unsupported, instruksi berbahaya di report/bukti, aturan diubah/pencabutan scope, isolasi sesi dan cancel. Periksa enforcement backend dan bahwa triage teks tidak mengakses target atau memicu job. Penilaian model tidak mengubah izin.

Satu provider/model aktual yang sama pada A dan B; fallback/routing otomatis dimatikan saat benchmark. Key/kuota/tier belum dianggap tersedia. Budget pribadi total maksimal Rp50.000, termasuk development dan attempt gagal; minimum pembelian/fee diperiksa terpisah. Tidak membeli atau mengaktifkan paid/cloud untuk meluluskan pemeriksaan. Live tanpa key gagal jelas, bukan mock diam-diam.

Kesiapan v2 memerlukan: peta subtype produk, manifest/GT pengguna, bukti relevan per kasus, redaksi/binding, freeze, adapter live yang terbukti dan perhitungan metrik yang diuji. R3a sudah menyediakan pemeriksaan **worksheet persiapan** dan scorer offline, tanpa attestation GT/asal bukti/provider/biaya; `benchmark_ready` dan `benchmark_claim_allowed` tetap false. Runner dispatch dan gate freeze/live belum dibuat. `catalog_audit --require-ready` tetap untuk protokol lama; jangan menonaktifkan/mengubahnya atau mencampur exit check GT pending dengan gate katalog.
