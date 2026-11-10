# R2: UI triage dan ringkasan observasi

**7 November 2026 — CODE_TESTED dan QA lokal lulus. LIVE_VERIFIED belum; konfigurasi live tetap pekerjaan terpisah.** Scope mengikuti [arsip prompt R2](execution-prompt-r2.md). Tidak mengulang R1 atau mengerjakan M6.

## Perubahan

- UI memakai endpoint R1 untuk **Minta saran AI**, polling, cancel dan status. Chat/upload tidak memanggil model. Key idempotensi dipertahankan bila POST gagal/tidak pasti; double-click dibatasi. Hasil terakhir dapat ditemukan kembali setelah reload lewat `latest_triage_id` pada projection conversation yang sudah berizin.
- `app/static/triage.js` menangani lifecycle terpisah dari polling run, navigasi/logout, hasil lama, draf belum dikirim serta konfigurasi/model/provider. Mode konfigurasi dibedakan dari mode hasil tersimpan. Semua teks model memakai `textContent`; saran tidak disalin ke claim, scope atau form validasi.
- Tombol **Ringkasan observasi** membaca `GET /api/runs/{id}/observations-summary`. Ini **ringkasan terstruktur buatan aplikasi, bukan ringkasan AI**: urutan, jenis tool, metode, status HTTP/observasi, jumlah respons dan truncation, dengan evidence ID terverifikasi untuk admin. Tidak ada inference tambahan atau biaya baru untuk ringkasan.
- `app/agent/observation_summary.py` memeriksa file/hash, journal/envelope, report/revision/run, scope/epoch, target snapshot/boot, argumen dan provenance sebelum projection. Tidak menampilkan body, screenshot, path target, identitas, free-form summary, catatan admin, output model mentah atau label evaluator. Respons tidak memberi verdict. Snapshot lama diberi penanda; bukti hilang/tidak cocok tidak diisi atau dijalankan ulang.
- Admin memperoleh observasi internal yang lolos binding. Owner memperoleh pesan menunggu publikasi atau ringkasan tetap yang sudah dibagikan admin melalui aturan lama; tidak mendapat evidence ID/binding privat. Hunter lain ditolak. Review ulang menarik kembali projection publik. Tampilan verifier tetap terpisah.

Tidak ada migrasi baru: source schema tetap 005. Berkas utama lain yang berubah: `workspace.html`, `app.js`, `workspace.css`, `app/api/routes.py`, `app/api/runs.py`, serta field model/provider pada readiness `app/main.py`. R1 adapter/ledger tidak diimplementasikan ulang. Service Compose, data/ledger/kuota aktif dan artefak lama dipertahankan.

## Pemeriksaan aktual

**13 tes terarah lulus dalam 19,77 detik**, artefak `artifacts/r2/targeted-initial.xml`. Cakupan: projection tiga jenis observasi tersimpan, kepemilikan, redaksi berbasis allowlist, scope/snapshot/file/provenance/journal yang salah, publikasi/penarikan, stale draf/scope, bukti kosong/simulasi serta discovery triage setelah reload. Pembacaan ringkasan tidak memutasi run/action/handoff/evidence/assessment/ledger/attempt. Satu regresi upload/ownership yang terpengaruh juga disertakan; suite historis R1/M6 tidak diulang.

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_r2_projection.py tests/test_auth_reports.py::test_upload_inert_ownership_limits
```

QA browser Chromium pada **1366×900 dan 390×900**:

| Artefak privat di `artifacts/r2/` | Hasil |
| --- | --- |
| `20261107T030901771Z/result.json` | Gagal saat runner terlalu cepat mengisi draf sebelum navigasi selesai; dipertahankan |
| `20261107T031027093Z/result.json` | Flow R2 lulus: explicit-only, double-click, reload, teks model di-escape, admin/owner/publication, stale draf, cancel, konfigurasi hilang dan responsif |
| `20261107T031231466Z/result.json` | Pemeriksaan tambahan khusus label konfigurasi LIVE/CONFIGURATION_REQUIRED, panel status tanpa inference, dan responsif; lulus |

Runner diperbaiki untuk menunggu percakapan baru dan versi draf tersimpan. State refresh UI juga diperbaiki agar tidak tertahan `pending` ketika status diperbarui saat POST belum selesai. Setelah review screenshot, label konfigurasi dan hasil lama diperjelas; yang diulang hanya pemeriksaan label tersebut. Tidak ada page error, request eksternal atau overflow horizontal pada QA yang lulus.

QA memakai app/database disposable, dua dispatch **MOCK**, dan satu observasi tersimpan **sintetis** dari fixture host. Tidak menjalankan worker/lab atau provider nyata. Jumlah run/action/handoff/evidence/assessment tetap sama dengan baseline fixture; hanya riwayat triage/mock ledger yang bertambah. QA konfigurasi menghasilkan nol dispatch. Database sementara dibersihkan; semua artefak gagal dipertahankan. Ini bukti flow/projection UI, bukan reproduksi target atau validasi model live.

Runner lokal memakai modul `playwright-core`/Chromium yang sudah tersedia; set `VALVULN_PLAYWRIGHT_CORE` dan `VALVULN_CHROMIUM` ke lokasi lokal bila diperlukan, tanpa instalasi baru:

```powershell
node scripts/r2_ui_smoke.cjs
# Subset khusus label, hanya bila label tersebut berubah:
node scripts/r2_ui_smoke.cjs --configuration-only
```

Syntax JavaScript/Python dan link/fence dokumentasi diperiksa terpisah. Sesudah pemeriksaan lulus, tidak mengulang suite historis atau menambahkan batch pengujian lain.

## Batas dan checkpoint berikutnya

UI R2 tersedia pada **source lokal**; service aktif belum diperbarui. Triage live masih membutuhkan profil/key/akses/biaya/tokenizer terverifikasi menurut [R1](r1-verification.md). Ringkasan R2 tidak diklaim sebagai penalaran AI, format input B benchmark atau bukti cukup untuk setiap klaim. Tidak ada dataset/GT final atau hasil A/B pada batch ini.

Berikutnya **R3**: petakan subtype dan bukti yang benar-benar relevan, susun draf teks 8 BAC/8 XSS/4 upload, minta GT pengguna sebelum freeze, lalu evaluasi functional-v2 setelah akses model nyata siap. Unsupported/OOS bukan INVALID. Tidak ada push/release/deploy, reset data, pembelian atau perluasan worker pada R2.
