# Arsip handoff R3b

Disimpan 7 November 2026 saat pengguna meminta pekerjaan berkelanjutan sampai paket siap review. Jangan memakai pembatasan satu potongan di bawah sebagai instruksi terbaru; gunakan [prompt aktif](execution-prompt.md).

# Handoff aktif: R3b setelah persiapan R3a

7 November 2026. R1/R2 sudah CODE_TESTED dan R2 QA lokal lulus. R3a persiapan CODE_TESTED, bukan R3 selesai atau hasil benchmark. Baca [hasil R3a](r3-verification.md), [peta subtype/bukti](r3-capability-map.md), [functional-v2](evaluation.md) dan AGENTS.md. Prompt R2 disimpan pada [arsip R2](execution-prompt-r2.md); jangan mengulangnya. M6 tetap DEFERRED di luar jalur aktif.

## Status konkret

- Paket privat `artifacts/r3/candidates-v1/`: 20 kandidat teks (8/8/4), 0 diterima manusia/GT, 40 slot A/B NOT_STARTED. Bukan 20 bug/skenario independen. CSV review belum diisi; semua GT tetap kosong.
- Source `evaluator/r3_drafts.py` dan `evaluator/functional_v2.py` menyediakan persiapan/import/check/scorer rekaman offline. 26 tes terarah lulus. Scorer tidak memanggil provider atau membuktikan asal data/biaya.
- R1 saat ini hanya schema triage; belum terhubung ke schema prediksi biner. R2 projection observasi mekanis belum cukup sebagai konteks B untuk setiap klaim. A/B dispatch runner dan gate freeze/live belum tersedia. Model live belum diverifikasi.

## Prompt lanjutan

```text
Lanjutkan ValVuln AI dari checkpoint R3a, bukan mengulang R1/R2/M6.

Baca AGENTS.md, docs/r3-verification.md, docs/r3-capability-map.md, docs/evaluation.md dan source evaluator/functional_v2.py serta evaluator/r3_drafts.py. Periksa paket privat yang sudah ada tanpa overwrite atau mengisi GT otomatis.

1. Jika pengguna telah mengisi review, import ke nama manifest baru. Verifikasi ID/hash, alasan, penerimaan kandidat, snapshot/kondisi/aturan dan referensi bukti; penerimaan/schema metadata bukan attestation kebenaran bukti. UNKNOWN/OOS/unsupported/ambigu tidak diisi INVALID. Target 20/10/10 bukan alasan mengubah label manusia. Jika review belum tersedia, jelaskan input yang masih diperlukan secara konkret, sambil mengerjakan kode persiapan yang memang independen.
2. Kerjakan satu potongan R3b: konteks A/B dan/atau integrasi prediksi teks sesuai ketergantungan yang benar-benar siap. B harus memakai observasi yang relevan dan terikat kasus/report/revision/scope/snapshot, bukan sekadar status HTTP atau ringkasan verifier. Projection server memeriksa ownership/binding/redaksi; jangan membocorkan GT/kondisi/katalog, narasi jawaban, catatan admin atau secret. Bukti kasus lain tidak dipinjam otomatis.
3. Prediksi VALID/INVALID/ABSTAIN memakai schema tersendiri dengan referensi input yang diverifikasi, terpisah dari triage dan CONFIRMED/REFUTED. Gunakan adapter/ledger/token/deadline yang sama dengan batas budget total Rp50.000, tanpa tools, target request atau dispatch worker. Jangan mengubah kondisi target, menjalankan PoC baru atau memperluas validator untuk mengisi bukti yang kosong.
4. Semua live/benchmark menunggu key, akses/tier/biaya terverifikasi, bukti/GT yang layak dan freeze privat. Jangan membeli kredit, menaikkan budget, membaca token sesi Codex atau memakai mock sebagai model nyata. Tanpa akses, tuntaskan source/tes simulasi yang independen; CODE_TESTED tidak menjadi LIVE_VERIFIED.
5. Runner kelak mempertahankan semua attempt dan raw output sebelum koreksi, mengunci model/provider/prompt/config dan mematikan fallback/routing otomatis. A/B memakai set/GT sama; kasus error/abstain/NOT_STARTED tidak dibuang dari denominator. Scorer offline yang ada bukan bukti dispatch aktual atau tagihan.
6. Periksa hanya subset yang berubah, jangan mengulang suite R1/R2/M6 atau benchmark tanpa alasan. Tidak ada UI besar, multi-agent, reset data, update service Compose, push/release/deploy. Kerjakan sendiri, simpan artefak gagal dan riwayat grup/manifest lama.

Laporkan potongan R3b yang benar-benar selesai, pengujian aktual, input/pekerjaan yang tersisa, serta status CODE_TESTED/LIVE_VERIFIED/FROZEN/EVALUATED yang terpisah. Jangan menyatakan R3 keseluruhan selesai hanya dari worksheet atau skor sintetis.
```
