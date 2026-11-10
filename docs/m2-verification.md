# Hasil M2 lokal — 4 November 2026

**M2 fondasi lab BAC-08 dan worker HTTP selesai secara teknis.** Reproduksi dilakukan melalui operator dengan langkah yang ditentukan sebelumnya, bukan perencanaan model AI. UI chat, verifier otomatis, model live dan benchmark belum dikerjakan. Target 24 titik tetap; baru **satu titik development** yang direproduksi, dengan kontrol perbaikan.

## Hasil aktual

| Pemeriksaan | Hasil |
| --- | --- |
| Lab/API awal | Empat tes awal lulus: dua akun sintetis, read ownership, mutasi lintas pemilik, kontrol pemilik, reset/session dan restart |
| Handoff dan HTTP | 21 tes M2 awal lulus sebelum runtime; termasuk DTO, HMAC, expiry, redirect, redaksi, sequence/deduplikasi, jurnal crash, provenance dan larangan reset saat run aktif |
| Suite kumulatif | **111 passed in 58.71s**, tanpa skip; M1 tetap diuji bersama tes M2 |
| Docker | Tiga service nyata app/worker/lab berjalan; dua SQLite terpisah dan empat named volume |
| BAC-08 rentan | Status enam aksi **200, 200, 404, 200, 200, 404**; B dapat membaca lampirannya sebelum A menghapusnya, lalu B mendapat 404; kontrol hapus milik A berhasil |
| Kontrol perbaikan | Status **200, 404, 200, 200, 200, 404**; hapus lintas pemilik ditolak dan objek B tetap tersedia; pemilik A tetap dapat menghapus objeknya |
| Jaringan run | **12 dispatch per run** = enam login terisolasi + enam aksi. Tidak ada retry target otomatis, panggilan model atau API berbayar |
| Duplicate DELETE | Pengiriman envelope identik tidak menambah DELETE pada access log lab; ID/hasil lama dipertahankan |
| Dirty target | Setelah mutasi, permintaan run baru ditolak sampai evaluator reset, health/assertion dan release snapshot baru |
| Crash aktual | Mutasi dikonfirmasi melalui state lab ketika respons sengaja ditahan; proses worker dibunuh SIGKILL. Restart menghasilkan **ACTION_OUTCOME_UNKNOWN**, tanpa replay otomatis; run berikutnya tetap diblokir sampai reset |
| Persistensi | Restart worker/lab tidak mereset objek lab. Reset lab tidak menghapus report, evidence atau ledger app |

Urutan langkah operator untuk kedua kondisi: `GET B sebagai B -> DELETE B sebagai A -> GET B sebagai B -> GET A sebagai A -> DELETE A sebagai A -> GET A sebagai A`. `GET` lampiran selalu menerapkan ownership; celah M2 hanya pemeriksaan pemilik pada DELETE. Penyimpanan memakai soft-delete pada SQLite; dampak yang dibuktikan adalah hilangnya akses normal pemilik melalui API, bukan penghapusan fisik disk.

Hasil mentah lokal: `artifacts/m2/verification.json` dan `artifacts/m2/crash-check.json` (diabaikan Git). Run reproduksi: `0c1337d9-d010-444a-9ca1-55849980d980` dan `76462b35-74ba-482f-ae4f-14f9e0b2d320`; uji crash: `694ffb33-0250-4d45-9a66-8579c8acd48b`. Capture HTTP ada pada storage privat app, dengan run/action/evidence ID, hash, snapshot dan boot ID worker. Assessment run operator tetap **null**; tidak menyajikan hasil ini sebagai verdict model.

Pemeriksaan database akhir menemukan dua run operator COMPLETED dan satu FAILED dengan `WORKER_LOST`, 12 evidence HTTP, nol assessment operator, nol provider attempt untuk run M2, tiga akun platform tetap ada, serta ledger settled Rp0. Probe akhir disimpan pada `artifacts/m2/network-check.json`, konfigurasi runtime terpilih pada `artifacts/m2/runtime-manifest.json`; keduanya tidak berisi nilai secret. Image akhir berhasil dibangun dengan versi langsung iptables/util-linux dipin sesuai inventaris. App/lab healthy, worker IDLE dan lab OPERATOR_VERIFIED setelah reset fixed eksplisit. Sampel RAM idle: app 43,89 MiB, worker 28,21 MiB, lab 35,59 MiB; bukan ukuran beban puncak/browser.

## Pemisahan dan jaringan yang diperiksa

- App hanya pada `app_net`, host `127.0.0.1:8000`. Worker `172.30.74.2` dan lab `172.30.74.3` pada `lab_internal` subnet `172.30.74.0/29`. Lab/worker tidak mempunyai port host. Koneksi app langsung ke lab ditolak.
- Worker memakai IP literal terdaftar untuk socket HTTP, Host/Origin tetap `lab:8001`; tidak memakai resolver dari report atau proxy environment. Redirect tidak diikuti. Tujuan, metode, path dan alias dibatasi DTO dan scope per aksi.
- Probe aktual worker/lab menolak TCP metadata, TEST-NET eksternal, gateway host, API app, port lab lain, DNS Docker serta IPv6 TEST-NET. Probe positif worker -> lab:8001 dan health loopback lab berhasil. Ini pengujian pada Docker Desktop host ini, bukan jaminan semua konfigurasi host atau browser.
- Firewall dipasang dalam namespace container oleh bootstrap root, lalu `setpriv` menurunkan Python ke UID/GID **10001**, menghapus effective/permitted/bounding capability dan memakai `no_new_privs`. Compose memberi capability bootstrap NET_ADMIN/SETUID/SETGID/SETPCAP, tanpa `privileged` atau Docker socket. Docker init dan bootstrap bukan proses agent; semua probe tool dijalankan sebagai UID 10001. Operator host tetap mempunyai Docker CLI, di luar threat boundary worker.
- Worker mendapat inbox read-only, outbox read-write, job signing key dan dua kredensial lab minimum. Worker tidak mempunyai app source/SQLite, evaluator/GT, `.env`, model key atau Docker socket pada path/mount yang diperiksa. Lab tidak mendapat job key. App outbox read-only terverifikasi.
- Symlink di outbox ditolak oleh pembaca app pada Linux aktual. File parsial, size limit, signature/provenance salah dan kuota diuji pada suite. O_NOFOLLOW dipakai pada pembukaan file Linux; nama kanal dibuat aplikasi.
- Job dan kontrol bertanda HMAC, expiry, run/action/sequence, scope epoch, snapshot target dan deadline. App menyimpan envelope immutable sebelum publish; worker menjurnal klaim aksi sebelum I/O. ACK membersihkan hasil sementara yang sudah diimpor. Hasil ambigu tetap dipertahankan untuk review; tidak ditebak sebagai sukses/gagal reproduksi.

## Kegagalan yang ditemukan dan diperbaiki

Tes fixture redirect awal memakai respons HTTPX yang sudah dikonsumsi; fixture diganti dengan stream agar menguji jalur capture yang benar. Probe pertama menemukan DNS Docker masih membalas saat aturan ESTABLISHED didahulukan; penolakan eksplisit `127.0.0.11` dipasang sebelum aturan tersebut. Probe sesudah recreate sempat mendahului listener lab; evaluator kini menunggu health sebelum probe. Seluruh pemeriksaan terkait kemudian lulus. Tidak mengubah firewall host, mereset Docker atau menghapus volume.

## Menjalankan ulang

Setelah setup secret, seed platform dan `docker compose up -d --build`, dari root repo:

```powershell
.\.venv\Scripts\python.exe -m evaluator.m2 verify
.\.venv\Scripts\python.exe -m evaluator.m2 crash-check
.\.venv\Scripts\python.exe -m evaluator.m2 network
.\.venv\Scripts\python.exe -m evaluator.m2 reset --condition fixed
```

Evaluator memanggil maintenance CLI melalui Docker sebagai operator, bukan route HTTP atau tool model. Reset mengharuskan antrean kosong dan worker idle, memasang maintenance gate, mereset lab saja, memeriksa prasyarat/health dan baru melepas dirty state menggunakan snapshot netral. Perintah verify/crash-check sengaja melakukan reset dan membuat riwayat baru; startup biasa tidak menjalankannya. Fixture crash hanya dapat diaktifkan lewat maintenance CLI dan menahan satu respons maksimal delapan detik setelah commit; tidak dihitung sebagai kerentanan tambahan.

## Batas dan checkpoint berikutnya

- Ini reproduksi operator berbasis skrip dan observasi aktual. Review/label GT manusia untuk dataset utama tetap belum dilakukan; tidak membuat 20 laporan final, split atau angka metrik.
- BAC-08 development direproduksi, 23 titik lain masih rencana. Invoice/held-out tidak dipakai untuk tuning M2.
- Browser/Chromium, subresource/WebSocket, XSS/upload/business logic dan pembatasan browser belum diuji. Tidak mengklaim NET-02 lulus.
- Tidak ada model live, tokenizer/billing aktual, prompt resistance, penggunaan data instansi, push, release atau deployment.
- `execution_mode` tetap mode model; run operator M2 memakai **tool_execution_mode=LAB**, tanpa dispatch model atau assessment otomatis. Workflow mock API biasa tetap tidak mengakses lab. Integrasi run lab dari UI dan pengambilan verdict nyata menunggu **M3**.

Checkpoint berikutnya: satu alur BAC report -> policy -> worker -> evidence -> verifier, lalu UI API tanpa kontrol simulasi. Jangan mengganti bukti capture dengan harapan report atau menganggap scope sesuai sebagai klaim terbukti.
