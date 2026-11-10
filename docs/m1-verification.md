# Hasil M1 lokal — 4 November 2026

**M1 selesai untuk fondasi lokal dengan mock.** Ini bukan kelulusan M2-M10, reproduksi kerentanan, integrasi model nyata atau deployment. Source dan pengujian dikerjakan sendiri tanpa sub-agent; baseline `ui-prototype/` dipertahankan.

## Potongan dan hasil aktual

| Batch | Perubahan | Pemeriksaan aktual |
| --- | --- | --- |
| M1a | Python/FastAPI, konfigurasi Pydantic, aiosqlite, migrasi, image dan Compose app | 7 tes bootstrap lulus; `docker compose config --quiet`, cold build/start dan health HTTP 200 |
| M1b | Seed operator, tiga akun, Argon2, opaque session/CSRF, membership/ownership, guideline, draft/lampiran dan revisi immutable | 19 tes kumulatif lulus sebelum batch berikutnya; akses silang, role, origin/CSRF, logout/expiry, batas upload, scope draf/aktivasi |
| M1c | Gate konservatif, queue/state/lease/recovery, idempotency, ledger, mock, kontrak provider dan assessment | Suite akhir **86 passed in 50.03s**, tanpa skip; `pip check` host dan container bersih |
| Runtime akhir | API aktual pada app Docker, dispatcher tunggal dan persistensi volume | Smoke lima start bersamaan -> satu run; hunter lain mendapat 404; mock selesai `INCONCLUSIVE`, nol request target; restart dan stop/start mempertahankan count + SHA-256 isi **15 tabel** identik |

Perintah utama yang dijalankan:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pip check
docker compose config --quiet
docker compose up -d --build
.\.venv\Scripts\python.exe scripts/m1_smoke.py --seed --restart-check
.\.venv\Scripts\python.exe scripts/m1_smoke.py --restart-check --stop-start-check
docker compose exec -T app python -m pip check
```

Hasil akhir smoke kedua:

```json
{
  "status": "PASS",
  "mode": "mock",
  "verdict": "INCONCLUSIVE",
  "target_requests": 0,
  "idempotency": "PASS (5 concurrent requests)",
  "cross_hunter_access": "404",
  "restart_persistence": "PASS",
  "stop_start_persistence": "PASS",
  "tables_verified": 15,
  "live_provider_called": false
}
```

Tes ASGI memakai database/direktori sementara dan melarang transport HTTP nyata melalui fixture. Smoke Docker hanya menghubungi `127.0.0.1:8000` dan memakai Docker CLI lokal; tidak ada portal lab atau transport provider live pada M1. `provider_attempts` mock adalah event simulasi, bukan tagihan API. Smoke sengaja meninggalkan report/evidence berlabel simulasi dan ledger; tidak menghapus hasil.

## Lingkungan dan kegagalan yang diperbaiki

- Python host **3.11.9**, SQLite host tercatat pada [inventaris](dependencies-m1.json); image Python **3.11.18**, SQLite **3.40.1**. Image dasar dikunci digest pada `Dockerfile`; dependensi langsung dan transitif dikunci pada `pyproject.toml` dan dua lock file.
- Docker CLI/Engine **29.7.2**, Docker Desktop **4.86.0**, Compose **v5.3.1**, context **desktop-linux**, Linux containers. Daemon yang sebelumnya tidak terjangkau kini berhasil dibaca dan menjalankan app.
- Port host **127.0.0.1:8000**. Inspect aktual: UID/GID `10001:10001`, root filesystem read-only, satu mount `/data` pada named volume, hanya jaringan `app_net`, limit **512 MiB / 1 CPU / 128 PID**. Tidak ada worker/lab dummy, bind mount seluruh repo atau Docker socket.
- Sampel setelah smoke: RAM **43.18 MiB**, image inspect **55.266.301 byte**. Ini sampel app M1, bukan pengukuran beban puncak atau kelayakan tiga container/Chromium.
- Helper sandbox awal gagal membuat PowerShell (`setup refresh had errors`). Eksekusi lokal dilanjutkan melalui jalur eskalasi yang diterima; tidak mereset Docker atau mengubah konfigurasi global host. Git memerlukan `-c safe.directory=...` per perintah karena kepemilikan checkout berbeda; tidak menambah safe.directory global.
- Tes lock awal gagal pada pembacaan byte yang dikunci Windows; diperbaiki dengan pemeriksaan posisi akhir file sebelum penguncian. Suite akhir lulus. Smoke segera setelah recreate sempat mendahului kesiapan app; harness diperbaiki untuk menunggu health sebelum login, lalu restart dan stop/start lulus. Tidak mengulang mutasi secara otomatis untuk menutupi kegagalan.
- `pip check` container memberi peringatan cache pip tidak writable pada filesystem read-only; pemeriksaan dependensinya tetap lulus. Startup app tidak menggunakan pip.

## Batas kelulusan

- Registry awal hanya mendeskripsikan alias `portal`, rute rencana `/api/attachments/{id}`, GET/DELETE, dua alias requester dan capability **mock BAC**. Binding tetap `ready=0`. Tidak menyatakan endpoint/akun/celah tersebut sudah tersedia pada lab. Scope hanya aktif lewat tindakan admin eksplisit; seed tidak mengaktifkannya.
- Run OOS/UNKNOWN/unsupported/prasyarat kurang serta live/replay yang belum siap tetap `NOT_ENQUEUED`, tanpa reservasi/action/dispatch. Tidak ada fallback ke mock ketika live dipilih.
- Ledger memakai integer rupiah konservatif; timeout dispatch simulasi mempertahankan reservasi sebagai `COST_UNKNOWN`. Token, tier gratis, harga, cap dan fallback diuji dengan respons simulasi; tidak membuktikan tokenizer, billing, tools atau akses provider aktual. Tidak membaca key provider atau melakukan checkout/pembelian.
- Startup/restart membatalkan pekerjaan pending dengan `PROCESS_INTERRUPTED`; tidak auto-resume antrean maupun inference. Lease hilang/expiry/cancel/revoke menyimpan alasan tanpa verdict palsu. Dirty target memblok lease dalam simulasi; efek mutasi/handoff/heartbeat worker aktual menunggu M2-M3.
- Evidence M1 berjenis `SIMULATION`, ID/hash/provenance dibuat app. Verifier M1 hanya menerima `INCONCLUSIVE` dan menolak referensi palsu atau verdict dampak. Hunter tidak mendapat raw model/evidence; ringkasan tetap dari aplikasi. Review/publikasi bukti nyata menyusul M3.
- UI chat backend, QA browser server, isolasi egress/DNS/browser, outbox/ack, GT/reset evaluator, lab 24 titik, dataset 20 laporan, model live, benchmark, release, push dan cloud **belum dijalankan**. Ini bukan hambatan kelulusan fondasi M1; semuanya tetap checkpoint tahap masing-masing.

Berikutnya **M2**: portal BAC-08 development dengan dua akun, SQLite lab terpisah, maintenance evaluator, reproduksi manual/kontrol, lalu worker dan pemeriksaan handoff/isolasi. Belum mulai M2 pada batch ini.
