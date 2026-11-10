# R3a: persiapan kandidat, GT dan metrik

**7 November 2026 — persiapan CODE_TESTED; R3 keseluruhan belum selesai.** Model live, GT final, freeze, konteks bukti B dan benchmark belum diverifikasi. Batch ini hanya filesystem/offline pada host; tidak mengakses target/provider, app/database/ledger aktif atau service Compose. R1/R2 tidak diulang.

## Hasil konkret

- [Peta capability/bukti](r3-capability-map.md) berdasarkan source BAC-08/XSS-08/UP-04, termasuk kesenjangan projection R2 untuk input B.
- `evaluator/r3_drafts.py`: membuat paket **baru** dengan 20 kandidat teks, manifest/hash privat, CSV GT kosong dan 40 slot A/B NOT_STARTED. Paket di `artifacts/r3/candidates-v1/`, diabaikan Git. Semua 20 kandidat belum diterima manusia; semua GT kosong. Variasi dikelompokkan, bukan dianggap 20 skenario/bug independen.
- Import CSV manusia menolak ID/hash salah, duplikat, GT tanpa penerimaan, label operasional sebagai biner, atau label tanpa alasan/snapshot/aturan/referensi bukti. EXCLUDE tidak menjadi INVALID. Import menulis manifest baru dan tidak mengubah draf/hasil lama. Validasi metadata tidak membuktikan bahwa bukti/asersi manusia autentik atau cukup.
- `evaluator/functional_v2.py`: schema prediksi dengan referensi input terbatas, pemeriksaan draf, jadwal dan **scorer rekaman offline**. Semua kasus terjadwal tetap dalam denominator; abstention/error/NOT_STARTED dipisah menurut GT. Biaya/usage tidak diketahui tetap null/unknown, bukan nol. A/B harus memiliki set kasus yang sama. Scorer tidak memanggil model atau menggantikan ledger.
- Scorer selalu berlabel `OFFLINE_RECORD_SCORING`, `benchmark_claim_allowed=false`, `live_verified=false`. Worksheet lengkap sendiri juga tidak membuat `benchmark_ready=true`. Tidak ada command freeze/dispatch model pada batch ini.

Pemeriksaan paket menghasilkan `PREPARATION_ONLY`, 20 teks (8/8/4), **0 diterima, 0 GT**, 3 grup akar masalah, 4 grup variasi/skenario rancangan, `metrics=null` dan `benchmark_ready=false`. Angka grup bukan jumlah snapshot aktual. Exit check 2 adalah status pending GT yang disengaja, terpisah dari gate katalog lama.

## Tes dan artefak

**26 tes terarah lulus dalam 2,05 detik**, `artifacts/r3/targeted-initial.xml`. Contoh manual protokol diuji: TP=8, FP=1, TN=7, FN=1, abstain positif=1/negatif=2 menghasilkan precision 8/9, recall 8/10, accuracy 15/20, coverage 17/20 dan F1 16/19. Ini **aritmetika sintetis**, bukan hasil model/dataset pengguna.

Cakupan lain: nol denominator, tidak ada prediksi, semua salah, error/NOT_STARTED dalam denominator, biaya/usage unknown, schedule hilang/duplikat/kasus asing, input JSON/schema/ref yang salah, GT kosong, import GT manusia, exclusion, hash laporan berubah dan larangan overwrite. Fixture tes memblok HTTP nyata. Tidak ada UI baru sehingga QA browser dan suite historis tidak diulang.

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_functional_v2.py
.\.venv\Scripts\python.exe -m evaluator.functional_v2 check artifacts/r3/candidates-v1
```

Hasil/readiness dan hash source disimpan pada `artifacts/r3/`. Tidak ada skor atas kandidat dengan GT pending; penghitungan semacam itu ditolak. Dataset/GT final tidak dibekukan atau dipublikasikan.

## Review yang diperlukan dari pengguna

Buka `artifacts/r3/candidates-v1/reports/` dan **`gt-review.csv`** bersama manifest untuk mengetahui subtype/grup setiap ID. Untuk tiap kandidat:

1. Tentukan apakah teks memuat satu klaim yang sesuai subtype dan cukup berbeda/layak. Biarkan `PENDING` bila belum siap. Gunakan `EXCLUDE` plus reviewer/alasan jika tidak layak; jangan mengisi GT biner untuk kasus operasional/unsupported.
2. Pilih `ACCEPT` hanya setelah peninjauan manusia. Isi `gt` dengan VALID atau INVALID, `reviewer`, `rationale`, `target_snapshot`, `condition_reference`, `scope_version`, `rules_version` dan `evidence_reference`. Label wajib sesuai klaim/dampak/kontrol pada snapshot yang dirujuk; kondisi fixed sendiri bukan bantahan yang cukup.
3. Jangan ubah `report_id` atau `report_sha256`. Jika teks perlu direvisi, buat versi kandidat baru sebelum freeze; jangan mengesahkan label atas hash teks lama. CSV berisi metadata privat dan tidak dikirim ke model.

Import ke **nama file baru** dalam paket:

```powershell
.\.venv\Scripts\python.exe -m evaluator.r3_drafts import-review artifacts/r3/candidates-v1 --review artifacts/r3/candidates-v1/gt-review.csv --output artifacts/r3/candidates-v1/manifest.reviewed-v1.json
.\.venv\Scripts\python.exe -m evaluator.functional_v2 check artifacts/r3/candidates-v1 --manifest artifacts/r3/candidates-v1/manifest.reviewed-v1.json
```

Target 10 VALID/10 INVALID dan 4/4 BAC, 4/4 XSS, 2/2 upload tetap target, bukan instruksi mengubah label agar seimbang. Jika kandidat ditolak atau label tidak memenuhi target, laporkan kekurangan dan revisi kandidat secara eksplisit.

Untuk menyiapkan ulang setelah revisi source teks, pilih folder paket baru. Command `prepare` menolak folder yang sudah ada; jangan menghapus paket sebelumnya. Command `score` memerlukan manifest GT eksplisit dan rekaman outcomes lengkap A/B; hanya untuk menghitung rekaman impor, bukan membuktikan provider/GT/bukti/biaya.

## Checkpoint R3b

Review/GT manusia ini diperlukan sebelum keputusan dataset final. Selanjutnya: kurasi bukti per kasus dan projection B yang relevan dengan binding/redaksi server, sambungkan schema prediksi ke adapter/ledger yang sama tanpa tools, kemudian freeze privat dan satu eksperimen A/B sesudah model live/pendanaan terverifikasi. **Runner dispatch A/B belum tersedia**; jangan memakai triage R1 sebagai pengganti prediksi eksperimen. Semua hasil tetap disimpan sebelum koreksi manusia. Tidak ada perubahan ke worker, katalog/gate lama atau manifest historis.
