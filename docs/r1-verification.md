# R1: provider dan triage teks

Tanggal **7 November 2026**. Scope: [submission-scope.md](submission-scope.md), [arsip prompt R1](execution-prompt-r1.md), [functional-v2](evaluation.md). **R1 CODE_TESTED**; pengujian aktual dan batasnya dicatat di bawah. **LIVE_VERIFIED belum terpenuhi: CONFIGURATION_REQUIRED.** Tidak ada panggilan provider nyata atau target dari batch ini. Service Compose aktif tidak diperbarui.

## Perubahan dan kontrak

| Berkas | Perilaku |
| --- | --- |
| `app/providers/openrouter.py` | HTTP async nyata ke origin OpenRouter tetap, non-streaming, model/provider tetap, JSON Schema, normalisasi respons/error/usage/biaya, tanpa tools/redirect/fallback |
| `app/providers/triage_contracts.py`, `redaction.py` | Schema saran terbatas, prompt teks versi v1, penolakan field tambahan, redaksi credential umum dan key yang dikonfigurasi |
| `app/agent/text_triage.py`, `app/api/triage.py` | Intake draf/lampiran -> konteks publik terversi -> triage independen, status/poll/cancel, idempotency, pemeriksaan ulang izin dan projection owner/admin |
| `app/config.py`, `.env.example`, `app/main.py` | Mode triage dan key server-side terpisah dari planner lab; startup/recovery/shutdown; readiness konfigurasi tidak menyatakan live terverifikasi |
| `app/storage/migrations/005_text_triage.sql` | Tabel `text_triages`; ledger/attempt lama diperluas agar terikat tepat satu `run_id` atau `triage_id`, tanpa membuat run lab untuk inference |
| `app/agent/ledger.py`, `app/providers/engine.py`, `app/agent/workflow.py` | Budget bersama, insert kolom eksplisit untuk kompatibilitas schema, recovery planner terpisah dari recovery triage |
| `tests/test_text_triage.py`, `tests/test_triage_persistence.py`, `tests/test_bootstrap.py` | HTTP simulasi pada adapter asli, enforcement/biaya/recovery/migrasi dan pembaruan ekspektasi schema |

Triage menerima teks draf dan lampiran yang sudah dimiliki sesi pengguna, beserta guideline/rules publik versi aktif. Tidak membaca katalog/evaluator, jawaban lab, GT, rekaman bisnis atau bukti privat. Konteks dan hash dibuat aplikasi. Model memberi `primary_claim`, `category`, `subtype`, `missing_information`, `scope_suggestion`, `capability_suggestion`, `reason`. BAC-08/XSS-08/UP-04 merupakan subtype sempit yang dapat disarankan; kategori saja tidak membuktikan dukungan. BUSINESS_LOGIC tidak menjadi GT INVALID.

Semua saran tetap data. Respons API menyatakan `suggestion_only=true`, `target_execution_allowed=false`, `model_dispatch_allowed=false`, `verdict=null`. Tidak ada perubahan ke role, scope, target binding, klaim snapshot, planner, assessment atau worker berdasarkan output AI. Ini bukan prediksi A/B atau keputusan izin. `Saran AI`/`Saran simulasi MOCK` sudah tersedia di projection API; tombol dan penempatan label pada UI dikerjakan di R2.

`VALVULN_TRIAGE_MODE=live` hanya mengaktifkan jalur teks; `VALVULN_EXECUTION_MODE=mock` tetap mode planner lama. Mock memiliki output tetap berlabel, bukan AI nyata. Replay belum dikonfigurasi dan gagal jelas. Live tanpa profil/key yang lengkap tidak membuat inference dan tidak kembali ke mock. Readiness mengembalikan `triage_mode`, `text_provider` dan `lab_planner_mode`; `CONFIGURED_NOT_VERIFIED` hanya menunjukkan kelengkapan konfigurasi. Field readiness `live_provider` lama tetap merujuk planner lama yang belum live.

## API intake

Gunakan session cookie platform, Origin yang benar dan `X-CSRF-Token` untuk mutasi. Draf dibuat lewat API intake yang sudah tersedia; chat/upload sendiri tetap tidak memanggil model.

1. `POST /api/conversations/{id}/triages`, body `{"expected_draft_version":1}`, header `Idempotency-Key` unik. Respons 202 berisi `triage_id` dan projection. Mode/model/budget bukan input client. Pemilik draf saja dapat memulai; admin dapat memulai pada drafnya sendiri.
2. `GET /api/triages/{triage_id}` untuk status dan saran. Owner serta admin program dapat membaca; hunter lain tidak mendapat akses. `is_current` membedakan hasil lama setelah perubahan draf/scope. Mengirim ulang key yang sama tidak menagih ulang; perubahan binding dengan key lama ditolak.
3. `POST /api/triages/{triage_id}/cancel` menghentikan pekerjaan yang masih aktif. Admin program juga boleh membatalkan. Hasil yang sudah selesai dipertahankan.

Sesi/membership/status akun/program, scope epoch dan versi draf diperiksa sebelum attempt dan selama menunggu HTTP, juga sebelum menerbitkan hasil. Pencabutan/expiry atau perubahan binding menghentikan transport lokal dan mencegah retry/hasil baru. Pembatalan HTTP tidak menjamin provider belum memproses/menagih request yang telah terkirim. Attempt tersebut tetap dicatat; biaya yang belum diketahui mempertahankan reservasi.

## Batas dan ledger

- Satu triage aktif untuk app, maksimal tiga permintaan baru per akun per jam; maksimal 1.000 riwayat tanpa penghapusan otomatis. Draf tetap memakai batas intake lama.
- Input maksimal 8.192 token menurut **batas konservatif UTF-8 bytes + 1.024 framing**, mencakup system prompt/schema/konteks. Jalur live menuntut operator memverifikasi bahwa tokenizer/model yang dipilih memenuhi batas tersebut. Ini bukan tokenizer universal; jangan mengaktifkan flag jika kompatibilitas belum diketahui. Input yang tidak muat ditolak, tidak dipotong diam-diam.
- Output API dibatasi 1.024 token; envelope HTTP dibaca maksimal 64 KiB dan teks hasil maksimal 32.000 karakter. JSON duplikat/NaN/Infinity, schema salah, tool/function call, respons terpotong, serta drift model/provider ditolak. Envelope terlalu besar menyimpan prefix teredaksi dengan tanda truncation, bukan respons lengkap.
- Deadline total default 30 detik, maksimum konfigurasi 60 detik. Retry default **mati**. Jika operator menyalakannya, hanya satu retry untuk 429 dengan Retry-After, 5xx atau timeout sebelum output sukses dikonsumsi, dalam deadline dan reservasi bersama. 429 ambigu, refusal, auth/quota/policy/schema/drift tidak diulang. Tidak ada routing ke provider lain. Benchmark harus mempertahankan retry/fallback/routing sesuai freeze; default ini tidak mengaktifkan retry.
- Reservasi setiap dispatch masuk **ledger yang sama** dengan provider planner lama. Status gagal/cancel tetap memiliki attempt. Usage/biaya yang hilang menjadi `COST_UNKNOWN`, bukan nol; nol hanya dicatat bila respons eksplisit mengembalikan nol atau pada mock berlabel. Biaya USD yang dilaporkan dikonversi dengan kurs operator terversi lalu dibulatkan ke atas dalam IDR; ini rekonsiliasi estimasi IDR, bukan bukti tagihan bank/fee pembelian.
- Jika biaya terlapor melebihi reservasi, nilai terlapor dipertahankan pada metadata, reservasi menjadi unknown dan dispatch berikutnya diblok `COST_REVIEW_REQUIRED` sampai rekonsiliasi operator. Tidak menyembunyikan pelanggaran cap sebagai biaya nol.

Input yang sudah direduksi, config/prompt/schema version/hash, requested/resolved model, provider inference aktual, provider request ID, usage/cost dan respons mentah teredaksi disimpan privat pada SQLite aplikasi. Owner menerima saran tervalidasi serta metadata, admin juga dapat membaca respons teredaksi; raw error provider tidak diproyeksikan ke hunter. Database/WAL, sisa disk dan kuota diperiksa sebelum penerimaan. Redaksi pola bukan jaminan penghapusan semua data rahasia; gunakan laporan development sintetis dan jangan memasukkan kredensial nyata dalam report. Tidak ada secret di source, browser atau worker.

Migrasi 005 memindahkan seluruh baris ledger/attempt lama dengan ID dan nilai yang sama, lalu memperluas binding. Tes upgrade memakai schema 004 asli dan membandingkan seluruh tabel lama setelah migrasi dua kali serta `foreign_key_check`. Tes restart menutup/membuka lifecycle app ASGI pada database sementara, mempertahankan hash/reservasi dan menandai pekerjaan terputus tanpa replay. Ini bukan restart proses/container/TCP. Database/volume/kuota/ledger aktif tidak digunakan untuk pengujian.

## Konfigurasi yang masih diperlukan

Pemeriksaan lokal hanya menemukan **tidak ada `.env` dan tidak ada environment process `VALVULN_OPENROUTER_API_KEY`**; nilai secret lain tidak dicari/dicetak. Belum ada bukti akses model, tier, saldo/kuota, harga atau tokenizer terverifikasi. Hasil simulasi tidak membuktikan kelayakan model nyata.

Kebutuhan berikutnya adalah **satu profil OpenRouter privat lengkap pada app**, dengan key lokal dan model/provider yang telah diperiksa. Gunakan variabel yang dicontohkan sebagai komentar pada [.env.example](../.env.example):

| Variabel | Nilai yang harus disediakan operator |
| --- | --- |
| `VALVULN_TRIAGE_MODE` | `live`; pertahankan `VALVULN_EXECUTION_MODE=mock` |
| `VALVULN_OPENROUTER_API_KEY` | Key API server-side di environment/`.env` privat; jangan dikirim di chat |
| `VALVULN_TRIAGE_MODEL` | ID model kanonis yang benar-benar dapat diakses; resolved model harus sama persis, tanpa router/preset/`:online` |
| `VALVULN_TRIAGE_PROVIDER_SLUG`, `VALVULN_TRIAGE_PROVIDER_NAME` | Slug routing dan nama provider inference yang diharapkan pada respons/metadata, keduanya diverifikasi |
| `VALVULN_TRIAGE_ACCESS_TIER`, `VALVULN_TRIAGE_ACCESS_VERIFIED` | FREE_TIER/PROMO_CREDIT/PAID dan `true` hanya sesudah akses/kuota/pendanaan layak; tidak membeli/top-up otomatis |
| `VALVULN_TRIAGE_TOKEN_BOUND_VERIFIED` | `true` hanya jika batas input konservatif kompatibel dengan model/tokenizer dan chat/schema framing |
| `VALVULN_TRIAGE_PRICE_SNAPSHOT` | Tanggal/sumber harga, kurs dan pemeriksaan tier aktual; bukan harga simulasi pada tes |
| `VALVULN_TRIAGE_PROMPT_USD_PER_MILLION`, `VALVULN_TRIAGE_COMPLETION_USD_PER_MILLION` | Batas harga USD per sejuta token yang diperiksa; harga tak diketahui memblok konfigurasi |
| `VALVULN_TRIAGE_USD_TO_IDR`, `VALVULN_TRIAGE_RESERVATION_IDR` | Kurs konservatif positif dan reservasi positif per attempt, mencukupi ceil((8192 × harga input + 1024 × harga output) / 1.000.000 × kurs) |
| `VALVULN_BUDGET_IDR` | Cap bersama maksimal 50000, dengan ledger lama tetap diperhitungkan |
| `VALVULN_TRIAGE_TIMEOUT_SECONDS`, `VALVULN_TRIAGE_RETRY_ENABLED` | Default 30 dan `false`; jangan mengubah selama eksperimen yang sudah freeze |

Source host membaca variabel ini melalui `Settings`, mengikuti perintah Uvicorn host pada README. **Compose aktif dan mapping environment Compose tidak diubah pada R1.** Menambahkan `.env` host saja belum menyalurkan variabel baru ke container app lama. Aktivasi kelak perlu konfigurasi app saja dan maintenance yang mempertahankan database/ledger otoritatif; jangan memakai database baru untuk menghindari reservasi/biaya lama. Worker/lab tidak membutuhkan atau menerima key.

Sesudah profil dan akses tersedia, smoke development cukup satu permintaan teks sintetis melalui API triage ini pada app/ledger yang otoritatif. Catat respons aktual/usage/biaya dan konfigurasi tanpa secret sebelum menyatakan `LIVE_VERIFIED`. Tidak memerlukan reset target, tools atau dataset/GT final. Minimum pembelian dan fee tetap diperiksa terhadap total budget Rp50.000 sebelum layanan berbayar digunakan.

Dasar HTTP/schema/error/routing diperiksa pada dokumentasi primer OpenRouter tanggal 7 November: [Chat Completions](https://openrouter.ai/docs/api/api-reference/chat/create-a-chat-completion), [provider routing dan max_price](https://openrouter.ai/docs/guides/routing/provider-selection), [error/Retry-After](https://openrouter.ai/docs/api_reference/errors-and-debugging). Implementasi meminta routing metadata lewat `X-OpenRouter-Metadata: enabled`; tidak memakai endpoint account atau generation tambahan untuk menyamarkan usage yang hilang. Dokumentasi publik tidak memverifikasi akses akun/model pengguna.

## Pemeriksaan aktual

**Suite R1 final: 77 passed dalam 87,09 detik**, termasuk upgrade/persistensi, shared ledger dan redaksi credential dalam JSON escape. **86 kasus regresi lama juga lulus** pada suite gabungan sebelumnya. Total 163 kasus unik terverifikasi lintas run; ini bukan satu run suite penuh 163 kasus. Hasil final R1: `artifacts/r1/20261107T020700Z/final-r1.xml`; hash source pada `source-hashes.json`, agregat pada `verification-summary.json`.

Riwayat suite gabungan source/regresi: **161 passed, 1 failed dalam 128,73 detik**. Kegagalan `test_triage_cannot_bypass_legacy_unknown_reservations` berasal dari selector assertion `SELECT status FROM ledger` yang mengambil reservasi run lama bernilai nol, bukan attempt provider. Assertion budget bersama dan penolakan dispatch sudah lulus. Selector diperbaiki menjadi `WHERE provider_attempt_id IS NOT NULL`; **retest satu kasus passed dalam 1,48 detik**, tanpa perubahan kode produk. Sesudah itu peninjauan redaksi menemukan bahwa secret dalam JSON escape perlu didekode sebelum snapshot disanitasi; transport diperkuat dan satu tes ditambahkan. Suite R1 yang terdampak kemudian diulang dan lulus seluruhnya seperti di atas; regresi lama tidak diulang. Artefak gagal `artifacts/r1/20261107T020700Z/tests.xml` dan retest `retest.xml` dipertahankan terpisah.

Suite memakai database disposable dan HTTP MockTransport pada adapter asli, sementara fixture tes memblok transport HTTP nyata. Cakupan: respons valid, JSON/schema/envelope salah, refusal, HTTP timeout/429/5xx, batas retry/deadline/biaya, konfigurasi/key tidak lengkap, drift model/provider, injeksi sebagai data, redaksi, ownership/session/CSRF, pencabutan scope/membership, cancel/shutdown/recovery, upgrade schema dan shared ledger lama. Fixture triage memeriksa nol baris run/action/handoff/evidence/assessment setelah tiap kasus; tes kompatibilitas lama memakai run mock terpisah yang memang sudah ada. Tidak ada model/target live atau reproduksi ulang lab. Suite aplikasi penuh, browser UI dan container tidak dijalankan untuk R1.

Pemeriksaan awal: 39 tes bootstrap/auth/provider lulus; suite R1 awal 51 lulus; suite upgrade/R1 berikutnya 56 lulus; regresi sebelum perbaikan terakhir 155 lulus dalam 136,81 detik. Ini riwayat bertahap, bukan angka yang dijumlahkan sebagai tes unik. Tidak ada hasil gagal yang dihapus.

Pemeriksaan statis: 13 berkas Python dapat diparse, `.env.example` memakai mock tanpa key, delapan berkas Markdown memiliki fence seimbang dan 169 link lokal tersedia; `git diff --check` lulus (hanya peringatan normalisasi LF/CRLF pada `.gitignore` existing).

Perintah suite akhir:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_text_triage.py tests/test_triage_persistence.py tests/test_bootstrap.py tests/test_auth_reports.py tests/test_provider_contract.py tests/test_provider_persistence.py tests/test_workflow.py tests/test_policy.py tests/test_recovery_verifier.py tests/test_storage_files.py --junitxml=artifacts/r1/20261107T020700Z/tests.xml
```

Perintah final setelah penguatan redaksi (gunakan folder artefak baru jika mengulang, agar hasil lama tidak tertimpa):

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_text_triage.py tests/test_triage_persistence.py --junitxml=artifacts/r1/20261107T020700Z/final-r1.xml
```

## Checkpoint berikutnya

R2: hubungkan tombol/label triage pada UI yang sudah disetujui, tampilkan provider/model/mode dan keterbaruan hasil, lalu ringkas observasi yang sudah tersedia dengan binding/redaksi yang benar. Model tetap tidak memicu worker. R2 boleh memakai mock berlabel, sedangkan R3 menunggu model nyata, bukti relevan, GT pengguna dan freeze. M6 tetap sebagian 13/24, BUSINESS_LOGIC LAB tetap unsupported; katalog/group/gate lama, manifest M5 dan data aktif dipertahankan. Tidak ada dataset final, benchmark, pembelian, push/release/deploy atau pembaruan service pada batch ini.
