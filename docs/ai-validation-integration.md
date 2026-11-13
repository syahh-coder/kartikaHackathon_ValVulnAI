# Integrasi AI ke validasi —13 November2026

Status: **CODE_TESTED**, runtime app diperbarui; **LIVE_VERIFIED=false**. Pengguna meminta OpenRouter sebagai prioritas1, Azure Foundry2, integrasi diselesaikan dan verifikasi kerentanan manual ditempatkan terakhir. Scope produk tetap BAC-08/XSS-08/UP-04; M6 tidak dikerjakan ulang.

## Perilaku akhir

`Laporan tersimpan → Minta saran AI → draf klaim → konfirmasi pemilik → scope/readiness → worker → evidence/verifier → review admin → ringkasan hunter`.

Schema `triage-v2` menambah `validation_fields` nullable: alias aset, path, path kontrol, alias akun dan jumlah klaim. AI diminta mengekstrak dari laporan/lampiran; informasi yang hilang tetap null/kosong. Tidak ada field script, header, credential, URL target bebas atau tool call.

Endpoint baru `POST /api/triages/{triage_id}/validation-draft`:

- Memeriksa pemilik, membership, status SUCCEEDED, versi draf/scope/authorization epoch dan schema.
- Membuat objek Claim dari ekstraksi, lalu menjalankan gate scope dan pemeriksaan plan fixture/policy per aksi tanpa eksekusi.
- Menandai informasi hilang, identifier yang tidak ditemukan persis dalam laporan, subtype tidak didukung dan scope yang menolak.
- Tidak membuat run/job/action/evidence, tidak memanggil model lagi, serta selalu `target_execution_allowed=false` dan `requires_confirmation=true`.

UI mengisi form existing lewat **Siapkan validasi dari saran AI**. OOS/unsupported/policy-blocked menghentikan alur persiapan. Informasi kurang dapat dilengkapi pada form; jumlah klaim tetap dibawa agar multi-claim tidak diam-diam menjadi satu klaim.

Konfirmasi memakai `source_triage_id` opsional pada API snapshot. Backend memeriksa ulang binding; saran asli tetap tersimpan. Audit `AI_CLAIM_CONFIRMED` menghubungkan triage, revisi laporan, scope, hash input/saran/klaim, mode dan provider/model yang diminta. Edit pengguna bukan izin model. Run menampilkan asal klaim; Workflow tetap menjalankan seluruh gate scope/readiness dan policy worker yang sudah ada.

Tidak menambah migrasi. Draf/run manual lama tetap tersedia. Saran schema v1 tersimpan dan dapat dibaca, tetapi memerlukan triage baru sebelum dipakai untuk persiapan klaim v2.

## Provider dan akuntansi

- OpenRouter default; Azure dipilih eksplisit sebagai cadangan. Adapter lama lain tidak dihapus tetapi bukan prioritas.
- OpenRouter memakai `require_parameters=true`, fixed model/provider, fallback mati dan batas harga. Model/endpoint harus mendukung schema.
- Batas4096 output diselaraskan pada request, snapshot triage, konfigurasi evaluator, checker reservasi dan tes. Batas planner mock lama1024 adalah kontrak terpisah.
- Azure memakai kontrak resource v1 existing. Schema untuk cloud menghapus constraint yang tidak didukung; validasi lokal tetap lengkap.
- Smoke umum lewat API app dan ledger yang sama menggantikan smoke langsung tanpa ledger. Default smoke tanpa `--execute` adalah nol request.
- Tidak ada inferensi cloud pada batch ini. OpenRouter lokal `CONFIGURED_NOT_VERIFIED`; Azure lokal masih `CONFIGURATION_REQUIRED`.

## Hasil pemeriksaan

Bukti privat ada pada `artifacts/ai-bridge-20261113/`.

**215 kasus tes unik mempunyai hasil terakhir lulus**, dihitung berdasarkan nama kasus dari JUnit, bukan menjumlah pengulangan. Ringkasan pada `verification-summary.json`; failure awal tetap disimpan.

- Uji inti awal:132 lulus/1 gagal. Tes gagal memakai batas lama1025 sebagai overflow; diubah ke4097 dan subset6 kasus lulus. Kegagalan awal dipertahankan.
- Integrasi awal tambahan:10 lulus, termasuk empat alur BAC kondisi rentan/perbaikan dengan model HTTP simulasi; verifikasi provenance akhir4 lulus.
- Regresi evaluator/configuration/projection/auth:57 lulus.
- Regresi dispatcher/readiness:19 lulus; tes paket source2 kasus lulus. Checker Azure diperiksa ulang setelah rumus cap diselaraskan.
- Empat alur menyeluruh menguji masing-masing provider dengan worker HTTP ke **lab ASGI sementara**, hasil CONFIRMED/REFUTED, review/publikasi admin dan proyeksi hunter. Tidak ada target Docker pengguna yang di-reset atau diuji pada tes ini.
- QA Chromium1366px/390px lulus: prefill, konfirmasi, provenance, escape HTML, stale draft dan OOS. Empat dispatch MOCK, dua run simulasi NONE; action/evidence/assessment dan request cloud/target semuanya0. QA pertama memakai shortcut yang tidak tersedia; diperbaiki memakai tombol navigasi dan diulang. Artefak gagal tetap disimpan.
- Build app Docker lulus memakai cache dependensi. App diperbarui pada project/volume lama setelah backup dan nol pekerjaan aktif. **26 tabel mempunyai count dan hash isi identik** sebelum/sesudah; ID worker, lab asli dan lab manual sama.
- Readiness runtime kini melaporkan4096 output, `triage-v2`, prioritas OpenRouter/Azure dan konfirmasi manusia. Tidak ada perubahan key atau aktivasi Azure.
- Diagnostik dispatcher mencatat jenis error dan run ID tanpa raw exception message/credential. Seluruh source app pada host/container akhir dibandingkan hash-nya.

Tes tidak membuktikan akses model cloud, ground truth manusia, akurasi dunia nyata, atau instalasi semua dependensi dari cache kosong. Hasil GT/freeze/A-B tetap pending. Panduan [provider](provider-setup.md), [manual terakhir](manual-final-review.md), [paket review](final-review.md).
