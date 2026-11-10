# M6b - Konteks simulasi, persistensi dan audit katalog, 6 November 2026

Status: **bagian defensif M6b selesai; M6 keseluruhan belum selesai**. **145 tes terarah lulus dalam 91,66 detik**, tanpa skip. Pemeriksaan persistensi Docker lulus. Gate katalog mengembalikan exit code **2** sesuai kondisi yang belum siap: 13 titik dengan status reproduksi tercatat, 11 PLANNED dan satu konflik development/evaluasi. Tidak menambah hitungan kerentanan atau mengklaim hasil model live.

## Konteks aturan terikat versi

`ScopeDraft` menambah label opsional `business_rules_version`. Jalur mock tanpa tool menyusun `SimulationContext` dari **scope_version_id milik run**, bukan aturan aktif terbaru, teks report, source lab, manifest evaluator atau secret. Konteks berisi teks/versi/hash aturan, identitas run/program/scope dan `target_requests_allowed=false`; daftar tools kosong. Versi prompt simulasi `m6-simulation-context-v1`. Builder menolak LAB/live/replay dan scope hilang/rusak.

Hash konteks serta scope ID dicatat pada audit `SIMULATION_CONTEXT_BOUND` dan hasil mentah admin. Projection hunter tidak mendapat hash/internal output. Model mock tetap deterministik, hasil INCONCLUSIVE dan nol request target. Scope baru membatalkan run lama; rekonstruksi konteks lama tetap memakai versi asal. Ini membuktikan plumbing simulasi, belum penalaran model atau dukungan validator BUSINESS_LOGIC. Jalur planner/tools LAB tidak diperluas.

## Persistensi dua container

`scripts/m6b_persistence_check.py` membuat volume baru berlabel khusus, menjalankan dua container terpisah memakai image lokal M6a yang telah diverifikasi, lalu membersihkan hanya sumber daya yang dibuatnya. Container UID 10001, root filesystem read-only, jaringan none, capability dropped, no-new-privileges, RAM 256 MiB dan 64 PID. Volume uji di `/data`, tmpfs `/tmp`; tidak memasang volume proyek atau secret operator.

Fase pertama menyiapkan lab baru pada database uji yang belum ada, menjalankan alur bisnis normal untuk tujuh barang, dan menyimpan hasil. Fase restart memeriksa isi volume sebelum/sesudah startup, login kembali dan mengulang pemenuhan yang sama. Hasil kedua fase identik: stok 93, request FULFILLED versi 4, empat event, satu fulfillment dengan ID yang sama dan snapshot tetap. Hash enam source lab cocok dengan host. Script menolak reset database yang sudah ada, database hilang atau state yang berbeda. Secret sintetis dibuat di memori, dikirim melalui stdin, dan tidak dimasukkan artefak.

Cleanup memeriksa prefix/nama UUID dan label milik pemeriksaan sebelum penghapusan. Tes memeriksa penolakan nama volume proyek, label/nama berbeda dan timeout. Pemeriksaan final cleanup PASS, tidak tersisa volume dengan label uji. Service Compose proyek tetap berjalan (app/lab healthy); tidak di-rebuild, di-reset atau diprovision. Uji ini membuktikan persistensi volume pada dua proses ASGI, belum traffic TCP, worker business logic, browser atau aktivasi source baru pada Compose.

## Katalog dan grouping

`evaluator/catalog.json` memuat tepat 24 ID, kategori, alokasi, status, grup sementara dan referensi dokumen sebelumnya. Tidak berisi payload atau tool runtime; file evaluator dikecualikan dari image. Status merupakan catatan historis, bukan reproduksi baru atau GT manusia.

`python -m evaluator.catalog_audit --require-ready` memeriksa schema, duplikasi/ID hilang, komposisi alokasi, reference dan overlap grup. Metadata saat ini VALID; gate readiness menolak kelulusan dengan exit 2. Sebelas titik yang belum direproduksi: BAC-01..07 dan BL-01..04. Development UP-04 berbagi `html-element-output` dengan evaluasi XSS-01..04. Alokasi tersebut belum boleh diklaim held-out independen. Tidak mengubah alokasi atau membuat grup baru hanya untuk meluluskan gate. `benchmark_ready` tidak pernah ditetapkan dari metadata ini.

## Pemeriksaan dan artefak

- 145 tes terarah: 95 regresi sebelumnya ditambah konteks, workflow simulasi, audit katalog, probe persistensi dan cleanup. Transport jaringan nyata diblokir pada suite. Suite penuh lintas seluruh reproduksi lab tidak dijalankan.
- Pemeriksaan awal konteks/workflow: satu gagal/28 lulus akibat query tes memakai kolom `kind` alih-alih `event_type`; query diperbaiki tanpa perubahan enforcement. Setelah audit katalog ditambahkan, 41 tes lulus; empat tes probe persistensi juga lulus sebelum suite final.
- Dua pemeriksaan persistensi bertimestamp lulus; pemeriksaan kedua memakai guard cleanup final. Artefak privat di `artifacts/m6b/`, termasuk `20261106T025450873654Z-persistence.json` dan `20261106T025451731967Z-catalog-audit.json`. Ringkasan verifikasi mencatat hash source baru, hasil tes dan referensi artefak. Hasil sebelumnya dipertahankan.

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_simulation_context.py tests/test_catalog_audit.py tests/test_business_persistence_probe.py tests/test_persistence_cleanup.py tests/test_workflow.py -q
.\.venv\Scripts\python.exe -m scripts.m6b_persistence_check
.\.venv\Scripts\python.exe -m evaluator.catalog_audit
# Exit 2 saat metadata belum memenuhi syarat katalog, bukan gangguan runner:
.\.venv\Scripts\python.exe -m evaluator.catalog_audit --require-ready
```

Runner persistensi memerlukan Docker dan image lokal `valvuln-lab:m6a-controls-check` yang digunakan pada M6a. Tidak melakukan pull/build atau membuat environment production. Tidak commit/push/deploy, membeli kredit, memanggil model live, mengubah kuota/ledger atau dataset utama.

## Sisa checkpoint M6

Tambahan audit rekaman (6 November, M6c defensif): `evaluator.business_record_audit` membaca JSON persistensi M6b yang sudah ada, maksimum 16 MiB. Schema ketat menolak field tidak dikenal, bool/string/float untuk kuantitas integer dan nilai non-finite. Pemeriksaan meliputi jumlah/stok, aritmetika pengurangan, binding request/fulfillment/versi, jumlah fulfillment, batas jurnal, kesamaan state/snapshot/source reference dan hasil replay. Tidak mengimpor lab/worker, mengakses jaringan atau mengeksekusi instruksi dalam data.

**25 tes auditor baru lulus dalam 0,32 detik**; dua artefak persistensi M6b yang tersimpan menghasilkan CONSISTENT. Tidak mengulang suite 145 tes atau eksekusi target. Output CONSISTENT/INCONSISTENT/INCOMPLETE/INVALID merupakan penilaian rekaman, dengan vulnerability_verdict dan ground_truth tetap null. Capture tidak ditandatangani; kesamaan metadata tidak membuktikan keaslian origin, permission/unit aktor atau urutan approval individual yang tidak tersedia dalam rekaman agregat. Missing trace/control tidak dipromosikan menjadi verdict teknis. Artefak audit/input/source hash disimpan privat pada `artifacts/m6c/`.

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_business_record_audit.py -q
.\.venv\Scripts\python.exe -m evaluator.business_record_audit artifacts/m6b/20261106T025450873654Z-persistence.json
```

Auditor ini belum terhubung ke assessment/UI/worker produk dan tidak menambah titik lab. Return code CLI 0 berarti rekaman konsisten; 2 berarti tidak konsisten/tidak lengkap/tidak sah, bukan CONFIRMED/REFUTED.

M6 tetap sebagian: kelengkapan 24 titik belum terpenuhi, konflik grouping belum diselesaikan, dan validator/assessment/UI business logic belum tersedia. Integrasi konteks hanya simulasi NONE; tidak ada agent business logic yang memakai tools. Kontrol aman, jumlah endpoint atau kelulusan tes tidak menggantikan bukti reproduksi 11 mekanisme yang masih PLANNED. GT manusia dan model live/benchmark tetap tahap berikutnya. Pekerjaan ini tidak mengubah target 24 titik atau komposisi 20 laporan.
