# Review rekaman bisnis di produk

Status 6 November 2026: **alur manual dan workflow langkah admin tersedia di app/UI lokal**. Pelapor menyimpan snapshot, admin mengunggah rekaman, memeriksa hasil dan langkah berikutnya, menulis review dan membagikan ringkasan. **172 tes terarah serta QA Chromium desktop/mobile lulus**. App Compose diperbarui dan health/UI diperiksa; 37 riwayat run dan ledger tetap utuh, worker/lab tidak diganti.

Ini review konsistensi **rekaman unggahan**, bukan pengujian langsung target atau validator kerentanan otomatis. Asal rekaman, identitas/izin aktor dan kecocokannya dengan kondisi target belum disahkan. `vulnerability_verdict` dan `ground_truth` tetap null. M6 keseluruhan tetap sebagian: 13/24 titik, 11 PLANNED, grouping belum siap dan model live/GT belum tersedia.

## Cara memakai

1. Buka `http://127.0.0.1:8000`, login sebagai pelapor, buat laporan lalu tekan **Kirim**.
2. Pilih **Siapkan review bukti bisnis**, lengkapi satu klaim dan fitur yang dilaporkan, lalu **Simpan snapshot untuk review**. Tidak ada worker/model yang dipanggil. Jika klaim snapshot lama perlu diganti, kirim revisi teks terlebih dahulu agar versi draf bertambah.
3. Admin membuka **Guideline** dan memastikan aturan bisnis aktif mempunyai teks yang relevan serta `business_rules_version` bernilai `procurement-controls-v1`. Tambahkan field ini pada JSON guideline tanpa menghapus aturan scope lain; simpan draf dan aktifkan setelah ditinjau. Label versi diperiksa untuk kompatibilitas format, bukan sebagai bukti bahwa aturan/data unggahan asli.
4. Admin membuka laporan dari daftar program, lalu **Unggah rekaman JSON**. Format saat ini adalah rekaman kontrol normal empat event CREATE/SUBMIT/APPROVE/FULFILL pada dua lifecycle, maksimal 128 KiB. Log bebas, EDIT dan rekaman dengan format lain belum didukung.
5. Buka **Lihat rekaman unggahan**, periksa hasil, sumber dan versi snapshot. Pilih **Tinjau rekaman**, tulis catatan internal, lalu **Bagikan ringkasan rekaman**. Pelapor mendapat ringkasan tetap dan ekspornya; data mentah, hash, identitas aktor serta catatan admin tetap privat.
6. Review ulang menarik publikasi sebelumnya. Rekaman asli dan hasil konsistensi tidak ditimpa; bagikan kembali setelah review siap.

Pada rekaman, admin juga dapat memilih **Langkah berikutnya**. Sistem menampilkan bukti yang masih diperlukan dan urutan peninjauan. **Ekspor konteks review** menyediakan konteks terstruktur yang terikat ke rekaman/laporan/aturan; catatan review internal dan data aktor mentah tidak disalin ke konteks ini. Konteks memuat klaim dan aturan, sehingga akses serta ekspornya tetap khusus admin. Tidak ada pengiriman ke model.

Untuk pemeriksaan development, `.\.venv\Scripts\python.exe -m scripts.m6e_trace_check` menghasilkan rekaman kontrol normal di `artifacts/m6e/`. Script memakai database sementara/ASGI, bukan service lab proyek. Rekaman sintetis tersebut dapat dipakai mencoba UI; bukan GT atau bukti kerentanan. Hash source yang tercantum dalam unggahan diperlakukan sebagai metadata yang belum disahkan, bukan dibaca sebagai path oleh app.

## Kontrak dan perlindungan

- Metadata pada tabel app `business_record_reviews` melalui migrasi 004; file asli immutable di `/data/evidence/manual-business/<review_id>.json`, termasuk kuota storage aplikasi. Maksimal 20 rekaman per laporan, lima impor per menit per admin. Duplikasi byte identik pada revisi yang sama mengembalikan review yang sudah ada.
- ID review, binding report/revision/content hash, versi/hash aturan dan penerima unggahan dibuat app. Nama file, role dan identitas pemilik dari client tidak dipakai menentukan storage/izin. Provenance berlabel `ADMIN_UPLOADED_UNATTESTED_RECORD`; tidak masuk tabel evidence worker, assessment, antrean atau ledger model.
- Parsing membatasi byte aktual, menolak kunci JSON duplikat, NaN/Infinity, field asing dan schema tidak sesuai. Error tidak menampilkan nilai input mentah. File diperiksa ukuran/hash sebelum ditampilkan, direview, dipublikasikan atau dikembalikan sebagai duplikat; file hilang/berubah memblok tindakan.
- Session/Origin/CSRF, membership dan admin role diperiksa server. Akses lintas pemilik/program ditolak. Pelapor hanya melihat rekaman yang dipublikasikan pada laporannya sendiri. Ekspor admin dan pelapor mengikuti projection yang sama dengan layar.
- Validator murni berada di `boundary/business_types.py` dan `boundary/business_trace.py`. App tidak mengimpor evaluator/GT atau lab. CLI evaluator tetap kompatibel sebagai wrapper. Tidak ada eksekusi script/URL/path dari unggahan.

| API | Akses / hasil |
| --- | --- |
| GET `/api/reports/{id}/business-records` | Admin: metadata internal; pemilik: ringkasan yang sudah dipublikasikan |
| POST `/api/reports/{id}/revisions/{revision}/business-records` | Admin: satu multipart field `file`, record JSON maksimal 128 KiB |
| GET `/api/business-records/{id}/record` | Admin: file asli dengan pemeriksaan integritas, JSON attachment |
| GET `/api/business-records/{id}/workflow` | Admin: status langkah berikutnya, binding versi/hash dan konteks terstruktur; tanpa dispatch |
| POST `/api/business-records/{id}/review` | Admin: `reviewer_note`, tanpa override verdict; publikasi ditarik |
| POST `/api/business-records/{id}/publish` | Admin: setelah review; hanya ringkasan milik aplikasi yang dibagikan |

Record dapat CONSISTENT, INCONSISTENT atau INCOMPLETE; status tersebut bukan CONFIRMED/REFUTED. Label versi/snapshot memperjelas bahwa review revisi pertama tidak menjadi review klaim pada revisi berikutnya. Scope yang disimpan adalah versi aktif saat impor; fitur ini tidak memberikan izin transport target.

## Hasil verifikasi awal alur manual

Suite awal **152 passed in 58.40s**: review produk (17 tes), parser/trace, katalog, bootstrap/migrasi, auth/report, mock workflow, konteks simulasi dan storage. Fixture tes memblok transport HTTP nyata; suite reproduksi kerentanan tidak dijalankan. Dua lifecycle app ASGI membuktikan record, review, publikasi dan file asli bertahan setelah startup ulang pada database uji.

QA Chromium pada app loopback/database disposable lulus: pembuatan snapshot, penolakan JSON salah, impor, file privat, review, publikasi, ekspor tersanitasi, penarikan publikasi, escaping dan lebar 1366/390 px. Nol page error dan nol request di luar app uji. Setelah QA, database sementara dibersihkan; hanya satu manual review, nol run/action/evidence/ledger/provider attempt.

Pembaruan runtime memakai `docker compose up -d --build --no-deps app` setelah preflight nol job aktif. Health menunjukkan empat migrasi, file JS yang disajikan cocok hash source, seluruh agregat tabel riwayat/ledger sebelum/sesudah identik. Container worker/lab tetap memiliki ID yang sama. Pemeriksaan image app membuktikan paket evaluator dan lab tidak tersedia. Tidak membuat record uji pada data Compose aktif atau menjalankan validasi target lewat Compose. Pemeriksaan ujung ke ujung dilakukan pada app disposable host; ini bukan klaim verifikasi semua jalur worker/container.

Artefak privat:

- `artifacts/business-review/20261106T0550386725965Z-tests.txt`: suite akhir.
- `artifacts/business-review/20261106T055038989Z/result.json`: QA akhir, screenshot dan ekspor pelapor berada pada folder yang sama.
- `artifacts/business-review/compose-before.json` dan `compose-after.json`: agregat persistensi, health dan isolasi image, tanpa credential.

Riwayat gagal dipertahankan: setelah pemindahan validator, wrapper CLI sempat tidak mengimpor helper error (_output), menghasilkan 64 passed/1 failed; diperbaiki. Tes multipart awal menghasilkan 79 passed/1 failed karena framework menolak extra field dengan 400 sementara tes mengharapkan 422; ekspektasi disesuaikan tanpa melonggarkan penolakan. QA pertama gagal karena locator judul cocok tiga elemen; locator dibatasi ke bubble laporan. Folder QA gagal tetap ada di `20261106T054650728Z`. Suite antara 150 tes lulus sebelum dua tes binding/persistensi ditambahkan; angka akhir 152 mencakup keduanya.

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_business_record_review.py tests/test_business_record_audit.py tests/test_business_trace_audit.py tests/test_catalog_audit.py tests/test_bootstrap.py tests/test_auth_reports.py tests/test_workflow.py tests/test_simulation_context.py tests/test_storage_files.py -q
# QA memakai playwright-core dan Chromium host yang sudah tersedia:
node scripts/business_review_ui_check.cjs
```

QA mendukung `VALVULN_PLAYWRIGHT_CORE`/`VALVULN_CHROMIUM` untuk lokasi instalasi lokal; tidak menginstal dependency atau menjalankan model. Tidak commit/push/rilis/cloud, mengurangi target, mengubah katalog/grup/status titik atau manifest M5. Otomasi eksploitasi dan 11 titik yang belum selesai tidak dikerjakan pada perubahan ini.

## Workflow bukti dan konteks terstruktur

Pembaruan berikutnya pada 6 November menambahkan `app/agent/business_evidence_workflow.py` dan endpoint GET khusus admin. Status ini terpisah dari proses run, scope, capability dan verdict. Tidak ada tabel atau migrasi baru.

| Kondisi | Phase workflow | Langkah pertama |
| --- | --- | --- |
| Versi laporan atau aturan aktif berbeda dari binding asal | NEEDS_SNAPSHOT_REVIEW | Tinjau versi snapshot; jangan memindahkan binding rekaman lama |
| Rekaman kurang lengkap | NEEDS_COMPLETE_RECORD | Minta rekaman kontrol normal lengkap |
| Rekaman tidak konsisten | NEEDS_RECORD_RECONCILIATION | Tinjau selisih terhadap sumber dan pertahankan rekaman lama |
| Rekaman konsisten | NEEDS_SOURCE_AND_IMPACT_EVIDENCE | Verifikasi sumber; lanjutkan kewenangan aktor, kecocokan klaim dan bukti dampak/kontrol |

Semua langkah memiliki `executor=PROGRAM_ADMIN` dan `automatic=false`. Konteks versi `business-evidence-workflow-v1` memakai schema Pydantic beku, tindakan administratif terbatas, `target_execution_allowed=false`, `model_dispatch_allowed=false`, verdict/GT null. Klaim ditandai `instruction_authority=NONE`; instruksi di klaim tidak diubah menjadi tindakan atau aturan. Ini belum pengujian prompt injection model nyata atau kontrak tool agent live.

Sebelum membangun konteks, app membaca ulang file dengan batas/hash check, menghitung ulang konsistensi, mencocokkan hasil tersimpan dan provenance, lalu mengambil klaim/aturan dari revisi/versi asal. Nomor/hash laporan, hash rekaman dan versi/hash aturan ikut diikat. Scope/laporan baru hanya mengubah flag current dan prioritas langkah; isi versi lama tidak diganti. Hash konteks mengikat byte konteks, bukan mengesahkan capture atau aktor.

**172 tes lulus dalam 68,82 detik**, termasuk 20 tes workflow baru; fixture jaringan tetap memblok transport HTTP nyata. Kasus mencakup semua phase, instruksi laporan tetap data, flag eksekusi tidak dapat disetel true, output stabil, catatan review tidak masuk konteks, akses admin saja walaupun ringkasan sudah publik, perubahan versi dan penolakan file/hasil/binding yang berubah. Tes 37 kasus workflow/review awal juga lulus; angka akhir 172 mencakup regresi yang relevan, bukan suite eksploitasi lab.

QA akhir `artifacts/business-review/20261106T065249387Z/result.json` lulus pada 1366/390 px, termasuk dialog langkah admin dan download `admin-workflow-context.json`, dengan nol page error/request eksternal. Database QA dibersihkan; nol run/action/evidence/ledger/provider attempt. Dua percobaan QA sebelumnya gagal pada locator ringkasan (cocok ke paragraf dan pratinjau JSON, kemudian selector direct-child terlalu sempit). Locator disesuaikan ke paragraf di dalam dialog tanpa perubahan perilaku produk. Artefak gagal `20261106T064854524Z` dan `20261106T065103267Z` dipertahankan.

App Compose diperbarui lagi setelah preflight ulang nol job aktif. `artifacts/business-workflow/compose-before-update.json` dan `compose-after.json` membuktikan seluruh agregat data/ledger sama, 37 riwayat run tetap, schema tidak berubah, ID worker/lab sama dan source workflow/JS dalam container cocok host. Tidak membuat data review pada Compose aktif; pemeriksaan alur lengkap menggunakan app disposable. Log suite akhir: `artifacts/business-workflow/20261106T0648556100922Z-tests.txt`.

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_business_evidence_workflow.py tests/test_business_record_review.py tests/test_business_record_audit.py tests/test_business_trace_audit.py tests/test_catalog_audit.py tests/test_bootstrap.py tests/test_auth_reports.py tests/test_workflow.py tests/test_simulation_context.py tests/test_storage_files.py -q
```

Workflow ini membuat kelengkapan bukti dan langkah review dapat dibaca sistem. Ia belum memberi tools BUSINESS_LOGIC LAB, validasi kerentanan otomatis atau integrasi model live. M6 tetap sebagian dan katalog tetap 13/24.
