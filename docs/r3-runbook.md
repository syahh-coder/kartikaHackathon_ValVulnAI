# R3 — alur operator teks dan evaluasi privat

**Azure Foundry tersedia di source:** provider eksplisit `azure` memakai deployment/model pin, endpoint resource dan redaksi key yang sama dengan triage. [Setup](azure-setup.md). Azure memberi usage tetapi biaya aktual tetap COST_UNKNOWN; freeze/jadwal tetap berhenti sesuai gate biaya yang sudah ada. Command Compose evaluator di bawah memakai ledger instalasi produk8000, sedangkan overlay Azure pengguna memakai ledger preview8010. Jangan menjalankan live pada keduanya sebagai dua budget atau membuat database kosong. Pilih ledger otoritatif sebelum dispatch; batch ini tidak menjalankan evaluator live.

Runner hanya membaca laporan/observasi tersimpan dan memanggil provider teks. Tidak membuat run lab, job worker, payload atau target request. Hasil prediksi tidak mengubah assessment/verdict produk. [Protokol](evaluation.md), [batas klaim](r3-capability-map.md), [status aktual](final-review.md).

## Input privat yang diperlukan

1. Review 20 teks di `artifacts/r3/candidates-v1/reports/`. Catatan `artifacts/r3/review-v1/proposals.private.json` berlabel PROPOSED_NOT_GT dan semua label null. Sumber historis/peta capability bukan bukti bagi teks kandidat. Isi CSV manusia hanya sesudah meninjau bukti klaim, dampak dan kontrol pada snapshot terkait. EXCLUDE bukan INVALID. [Cara import tanpa overwrite](r3-verification.md).
2. Sediakan binding setiap kandidat ke run produk yang memang sudah memiliki observasi terkait teks tersebut. Isi salinan `bindings.template.private.json` dengan run UUID. Jangan menautkan run dari report lain. Runner menuntut body revision sama persis dengan teks kandidat, attachment kosong, owner/membership, revision/draft/scope/epoch current, snapshot/boot/envelope/provenance/hash file/journal cocok, serta jumlah rekaman 7/4/5 sesuai subtype. Ini pemeriksaan integritas rekaman, bukan attestation izin aktor atau pengganti review kecukupan bukti. Tidak ada command pengumpulan/eksekusi target baru dalam runner ini.
3. Field GT `target_snapshot` dan `scope_version` memakai UUID dari binding; `rules_version` memakai business_rules_version bila ada, selain itu nomor versi scope sebagai string. `condition_reference` serta rationale/evidence_reference privat tidak masuk prompt. Jika laporan masih ambigu atau bukti kurang, biarkan pending dan revisi kandidat ke versi baru bila diperlukan.
4. Isi konfigurasi OpenRouter di `.env` privat berdasarkan akses akun aktual. Template ada di `.env.example`: mode live, key, model tetap, inference provider slug/name, tier dan akses terverifikasi, byte-BPE token-bound terverifikasi, snapshot harga input/output per sejuta token USD, kurs USD/IDR, reservasi IDR dan timeout. Jangan menyalin angka harga fixture tes. Reservasi minimal harus mencakup 8192 input/4096 output pada harga/kurs terverifikasi. Total budget tetap <=Rp50.000, termasuk pemanggilan UI/smoke/attempt gagal. Pembelian minimum, saldo/kuota dan fee perlu ditinjau operator; tidak ada top-up/upgrade otomatis.

## Database dan perintah

Schema source terbaru **006**. Service aktif pada pekerjaan pengemasan ini sengaja tidak diperbarui. Terapkan migrasi melalui startup app saat pengguna siap memperbarui service, bukan menjalankan evaluator terhadap DB baru demi memperoleh budget kosong. Backup operasi/data mengikuti prosedur operator. Migrasi 004→006 diuji mempertahankan seluruh kolom/rekaman lama pada database disposable.

Jika aplikasi berjalan pada Docker, gunakan profil operator `evaluation`, yang memakai **volume app_data yang sama** dan bind folder privat `artifacts/r3` ke `/evaluation`. Contoh prefix:

```powershell
docker compose --profile evaluation build evaluator
docker compose --profile evaluation run --rm --no-deps evaluator --help
```

Perintah berikut ditulis untuk Python host **hanya bila `.env` VALVULN_DATA_DIR menunjuk DB otoritatif yang sama**. Untuk app Docker, ganti prefix `python -m evaluator.text_benchmark` dengan prefix `docker compose --profile evaluation run --rm --no-deps evaluator`, dan path `artifacts/r3/...` menjadi `/evaluation/...`. Jangan menyalin DB Docker ke host untuk dispatch berbayar. Admin diminta memasukkan password lokal melalui prompt tersembunyi; key/password tidak dicetak. Profil evaluator tidak memberi model akses file/GT atau jaringan lab.

```powershell
# Satu smoke development, bukan salah satu kandidat benchmark; belum dijalankan live pada paket ini.
python -m evaluator.text_benchmark smoke --program-id PROGRAM_UUID --output artifacts/r3/smoke-v1.private.json

# Setelah bukti dan CSV manusia siap, gunakan manifest baru hasil import.
python -m evaluator.text_benchmark contexts --packet artifacts/r3/candidates-v1 --manifest artifacts/r3/candidates-v1/manifest.reviewed-v1.json --bindings artifacts/r3/bindings-reviewed.private.json --output artifacts/r3/contexts-v1.private.json
python -m evaluator.text_benchmark freeze --packet artifacts/r3/candidates-v1 --manifest artifacts/r3/candidates-v1/manifest.reviewed-v1.json --contexts artifacts/r3/contexts-v1.private.json --output artifacts/r3/freeze-v1.private.json
python -m evaluator.text_benchmark run --packet artifacts/r3/candidates-v1 --freeze artifacts/r3/freeze-v1.private.json --output artifacts/r3/results-v1
```

Freeze menolak GT/kuota belum lengkap, konteks berubah, token bound terlampaui, smoke schema/identity/usage/cost belum sukses pada kontrak/source/profil sama, atau sisa budget tidak cukup untuk reservasi konservatif seluruh 40 slot. Paket frozen menyimpan manifest/GT privat, konteks A/B, kontrak/prompt/schema, hash source app/boundary/evaluator+SQL+locks, model/provider, harga/kurs/limit, urutan dan kebijakan error. Hash ini integritas lokal, bukan tanda tangan/attestation eksternal.

A dan B berisi report serta aturan publik yang sama. B menambah fakta allowlist: status/respons dan relasi objek/pemilik pada HTTP; kontrol JavaScript/storage/screenshot serta hitungan marker terikat pada browser; metadata/hash/ukuran upload. Tidak ada raw body/HTML, DOM, screenshot bytes, filename aktif, GT, label kondisi, narasi reviewer atau verdict. Referensi input `REPORT`, `RULES`, `OBS-01` dst; model wajib memakai referensi yang tersedia. Menilai kecukupan kontrol tetap bagian penalaran dan review, bukan kesimpulan otomatis projection.

Satu attempt per slot, tanpa retry/fallback; lebih konservatif daripada batas protokol maksimum dua attempt. Reservasi dibuat sebelum dispatch di ledger yang sama dengan run/triage. Respons gagal/refusal/schema, raw tereduksi, biaya/usage unknown dan slot belum dimulai tetap tersimpan. Timeout/cancel/revocation membatalkan transport dan menyisakan biaya unknown secara konservatif. Biaya melampaui reservasi memblok dispatch selanjutnya untuk rekonsiliasi. Unknown cost menghentikan jadwal agar operator memeriksa tagihan; tidak disamakan nol.

## Hasil, interupsi dan simulasi

Folder hasil berisi `outcomes.json`, `raw-records.private.json`, `report.json`. Database aplikasi tetap sumber ledger/attempt. Scorer tidak membuang kasus gagal atau mengoreksi output model. Semua slot tetap dalam denominator. `benchmark_claim_allowed=false` sampai reviewer memeriksa provenance, GT, kelengkapan dan rekonsiliasi aktual. Membuka kembali run dengan freeze yang sama hanya mengirim slot yang belum pernah didispatch; respons/attempt yang sudah ada tidak dimainkan ulang.

Jika proses mati setelah dispatch, reservasi tetap terhitung. Tunggu timeout frozen +60 detik dan pastikan proses lama berhenti, lalu:

```powershell
python -m evaluator.text_benchmark recover --output artifacts/r3/recovery-v1.private.json
python -m evaluator.text_benchmark export --freeze artifacts/r3/freeze-v1.private.json --output artifacts/r3/export-v1
```

Recover hanya menutup rekaman DISPATCHED yang kedaluwarsa menjadi ERROR dan ledger COST_UNKNOWN; tidak melepas biaya atau mengirim ulang. Tidak ada perintah otomatis menghapus/mengurangi tagihan. Perubahan source/profil setelah freeze ditolak; simpan versi source frozen untuk menjalankan/mengekspor sesuai eksperimen itu.

Tanpa GT/key/bukti, dry-run offline yang aman:

```powershell
python -m evaluator.text_benchmark simulate --packet artifacts/r3/candidates-v1 --output artifacts/r3/simulation-v2
```

Ini respons ABSTAIN tetap **SIMULATION_ONLY**, bukan inferensi, freeze atau benchmark. Tidak menyentuh DB/ledger aktif dan metrik null. Pilih output baru; CLI menolak overwrite. Laporan nyata saat ini tetap `artifacts/r3/review-v1/report.pending.json` dan jadwal 40 NOT_STARTED; hasil simulasi disimpan terpisah.
