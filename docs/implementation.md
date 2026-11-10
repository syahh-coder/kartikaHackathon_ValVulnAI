# Pelaksanaan bertahap dan checkpoint

**Checkpoint Azure atas permintaan pengguna:** adapter Foundry teks serta wiring triage/readiness/evaluator, checker privat dan overlay preview tersedia;148 tes terkait lulus. Konfigurasi akun belum lengkap, sehingga tidak ada smoke live. Lanjutkan [setup Azure](azure-setup.md), bukan mengulang milestone lama. [Bukti](azure-verification.md).

## Jalur aktif R1-R4 - keputusan 7 November 2026

**Perbaikan setelah review pengguna:** form Guideline program kini memberi required field/petunjuk JSON dan pesan SCHEMA_ERROR yang menyebut field aman. 11 tes terarah dan QA browser lulus; hanya preview8010 diperbarui, tabel bisnis preview serta app/worker/lab/data asli dipertahankan. [Bukti dan batas](admin-guideline-validation-fix.md). Tidak mengubah status GT/live/freeze/benchmark atau mengulang milestone lama.

**Checkpoint paket review:** [final-review.md](final-review.md) merangkum pekerjaan independen R3b–R3f dan persiapan R4 yang sudah CODE_TESTED. Runner/projection/prediksi, ledger schema006, gate freeze, laporan pending dan bahan submission lokal tersedia. GT/bukti kandidat/live/freeze/eksperimen nyata belum terpenuhi; bukan R3 benchmark selesai. Paket READY_FOR_REVIEW_WITH_PENDING_INPUTS; berikutnya review pengguna atas input/berkas konkret, kemudian pekerjaan bergantung input tersebut. Hasil dan batas pada [verifikasi R3/R4](r3-r4-verification.md). Checkpoint R3a di bawah adalah riwayat.

**Mode kerja terbaru:** pengguna meminta semua pekerjaan yang dapat diselesaikan dikerjakan sampai paket siap review sekaligus. Lanjutkan sisa R3 -> pengemasan/artefak R4 tanpa berhenti meminta izin tiap sub-tahap. Verifikasi dan pembaruan checkpoint tetap dilakukan internal. R3b konteks/runner, R3c review GT, R3d akses live, R3e freeze/eksperimen dan R3f hasil adalah pembagian kerja; lalu R4a paket, R4b artefak dan R4c persiapan publikasi. Pekerjaan independen berjalan meskipun GT/key/bukti masih pending. [Prompt aktif](execution-prompt.md).

Hasil akhir pekerjaan ini adalah satu `docs/final-review.md` dengan file review nyata, pemeriksaan aktual dan daftar input pengguna yang masih dibutuhkan. Jangan mengesahkan GT manusia atau membuat benchmark palsu agar tahap tampak selesai. Status READY_FOR_REVIEW_WITH_PENDING_INPUTS digunakan bila akses/GT/bukti/rekaman final belum tersedia. R4c publikasi/submit sesungguhnya tetap sesudah review dan otorisasi pengguna; draft/checklist disiapkan sekarang. R1/R2/R3a/M6 tidak diulang.

**Status terbaru:** M6 DEFERRED untuk submission. R1/R2 tetap CODE_TESTED; **R3a persiapan CODE_TESTED**, selanjutnya R3b review GT, bukti B dan runner/freeze/live. [Hasil R3a](r3-verification.md). Jalankan tes terarah sesuai perubahan; R1/R2/M6 tidak diulang.

Ikuti [scope submission](submission-scope.md) dan [handoff aktif R3b](execution-prompt.md). M6 asli tidak dipaksakan selesai dengan tes pendukung. M1-M5 tidak diulang. Milestone asli di bawah disimpan untuk riwayat/backlog; gate 24 titik dan split akar masalah baru bukan gate jalur submission sempit. Kontrak keamanan tetap berlaku.

| Batch | Fokus | Dependensi | Penerimaan | Status |
| --- | --- | --- | --- | --- |
| R1 | Satu adapter provider dan triage teks | Fondasi app yang ada; live smoke memerlukan key/akses/budget | Konfigurasi/key server-side, schema/error/ledger/redaksi dan tes; nol job/tool/request target dari triage; CODE_TESTED dan LIVE_VERIFIED terpisah | CODE_TESTED; LIVE_VERIFIED belum, CONFIGURATION_REQUIRED; [bukti](r1-verification.md) |
| R2 | Label model/mode dan ringkasan observasi | R1 CODE_TESTED; bukti yang relevan dan binding yang aman | Prediksi AI terpisah dari verifier, UI mempertahankan role/scope; model tidak memicu worker; unsupported jujur | CODE_TESTED dan QA lokal lulus; live belum; [bukti](r2-verification.md) |
| R3 | GT dan benchmark functional-v2 | Persiapan dapat offline; benchmark memerlukan model nyata, bukti/GT/freeze | Target20 teks10/10 alokasi8/8/4; A/B, seluruh raw/error/biaya dipertahankan | Kode independen CODE_TESTED; runner/freeze gate tersedia, 20 kandidat/0GT, bukti/live/eksperimen pending; [hasil](r3-r4-verification.md) |
| R4 | Paket dan artefak submission | Fungsi/hasil aktual yang tersedia | Source/checksum, quick start, slide/gambar/demo dan draft publikasi | Persiapan lokal siap review; video YouTube/link publik/lisensi/submit pending; [indeks](final-review.md) |

R1 CODE_TESTED berarti source adapter digunakan jalur triage dan tes transport simulasi lulus; tidak berarti model hidup. LIVE_VERIFIED memerlukan respons provider nyata dan pencatatan usage/biaya yang layak. Key belum siap: selesaikan bagian kode/tes independen, laporkan kebutuhan konfigurasi konkret, jangan kembali menambah auditor bisnis. R2 boleh dikembangkan tanpa live dengan label mock; R3 hasil model tetap menunggu live/GT.

**Hasil R3a 7 November:** peta batas klaim/bukti tiga subtype; 20 kandidat teks privat dikelompokkan sebagai variasi mekanisme dikenal, tanpa GT otomatis; CSV review/import immutable, jadwal 40 slot NOT_STARTED dan scorer offline dengan denominator/abstention/error/unknown cost. 26 tes terarah lulus dalam 2,05 detik. Check persiapan pending GT menghasilkan exit 2, metrics null, benchmark_ready false; bukan gate katalog lama. Kesenjangan B R2, integrasi schema prediksi dengan adapter, dispatch A/B, GT pengguna/freeze/live tetap outstanding. Tidak menjalankan target/provider, mengubah app/worker/data/ledger/service atau menyatakan R3 selesai. [Review konkret pengguna](r3-verification.md).

**Hasil R2 7 November:** UI triage eksplisit dengan discovery/poll/cancel/stale/configuration/provider; ringkasan observasi terstruktur aplikasi read-only dengan binding/file hash dan projection admin/owner. 13 tes terarah lulus dalam 19,77 detik; QA Chromium 1366/390 px lulus pada app disposable dengan provider simulasi dan rekaman sintetis. Runner QA awal terlalu cepat setelah navigasi, diperbaiki; artefak gagal dipertahankan. Label konfigurasi diperjelas dari hasil lama, lalu hanya subset label diuji ulang. Tidak ada request target/provider nyata atau migrasi baru; service/data aktif dipertahankan. Ringkasan bukan AI/format B benchmark atau verdict baru. Berikutnya R3 peta subtype/bukti dan draf, GT pengguna/freeze/live sebelum benchmark. [Rincian R2](r2-verification.md).

Hasil batch 7 November: adapter HTTP asli dan endpoint triage independen tersedia, dengan migrasi app 005 yang diuji pada data sementara. **77 tes R1 final lulus dalam 87,09 detik**, termasuk penguatan redaksi JSON escape; **86 tes regresi lama lulus** pada suite gabungan sebelumnya. Suite gabungan sebelumnya berisi 162 kasus dengan 161 lulus/1 gagal pada selector assertion tes; selector diperbaiki dan retest satu kasus lulus dalam 1,48 detik. Setelah penguatan redaksi, suite R1 yang terdampak diulang, regresi lama tidak diulang. Total 163 kasus unik terverifikasi lintas run; artefak gagal tetap disimpan. Mode triage terpisah dari planner lab, tanpa job/action/request target. Tidak ada `.env` atau key process OpenRouter; key/profil harga/akses/tokenizer yang diverifikasi masih diperlukan. Compose/data/ledger aktif, katalog/gate dan manifest lama dipertahankan. Berikutnya R2 UI dan ringkasan observasi tersanitasi; rincian di [verifikasi R1](r1-verification.md).

Protokol [functional-v2](evaluation.md) menggantikan alokasi 8/8/2/2 dengan 8 BAC/8 XSS/4 upload untuk submission ini. Tiga subtype produk yang sudah dikenal bukan 20 bug independen. Katalog/status/grup dan gate lama tetap; exit 2 bukan alasan memoles metadata atau menandai M6 selesai. R1 tidak menjalankan target, membuat dataset final, memperluas worker/lab atau memperbarui service Compose. Selesaikan satu batch dan laporkan bukti sebelum pindah batch.

## Riwayat rencana lengkap sebelum penyempitan

Perubahan terbaru: **workflow langkah admin dan konteks bukti bisnis tersedia; M6 tetap sebagian**. [Hasil/panduan](business-record-review.md#workflow-bukti-dan-konteks-terstruktur): 172 tes dan QA desktop/mobile lulus, app Compose diperbarui, 37 riwayat run/ledger utuh. Phase dan next actions administratif terikat versi/hash, tanpa dispatch target/model; bukan agentic live atau validator BUSINESS_LOGIC LAB. Katalog tetap 13/24 dan split belum siap.

Riwayat batch M6a-c: **M6 sebagian; M6a/b serta audit rekaman M6c defensif selesai lokal, 6 November 2026**. [Hasil dan batas](m6b-verification.md): M6b lulus 145 tes terarah; auditor rekaman baru lulus 25 tes terpisah dan dua rekaman tersimpan CONSISTENT. Audit baru tidak mengulang eksekusi target/suite penuh. Katalog 24 ID VALID, gate kesiapan exit 2: 13 titik dengan reproduksi tercatat, 11 PLANNED dan konflik grouping UP-04/XSS-01..04. Compose aktif masih M5; auditor offline tidak menjadi validator BUSINESS_LOGIC produk. M1–M5 tetap selesai; model live, GT manusia dan benchmark pending. M6 belum boleh dinyatakan selesai.

Sumber keputusan: [plan.md](../plan.md). Tampilan: [design.md](design.md). Perjalanan pengguna: [user-flow.md](user-flow.md). Kontrak data/tools tetap di [architecture.md](architecture.md).

## 1. Cara menjalankan pekerjaan

1. Tentukan satu milestone aktif dan baca spesifikasi yang relevan.
2. Bangun satu potongan yang dapat dijalankan/diperiksa dengan dependensinya.
3. Jalankan pemeriksaan sesuai perubahan; catat hasil nyata.
4. Perbaiki kegagalan yang menghambat potongan tersebut.
5. Perbarui status, file yang berubah, bukti pemeriksaan dan pekerjaan berikutnya.
6. Lanjut ke milestone berikutnya jika dependensinya sudah terpenuhi.

Checkpoint adalah verifikasi teknis dan pembaruan status, bukan permintaan izin baru untuk setiap file. Ketika implementasi sudah diotorisasi pengguna, kerjakan langkah yang jelas secara berkelanjutan. Hentikan pekerjaan yang bergantung pada input/akses yang memang belum tersedia dan lanjutkan bagian independen yang masih berada dalam scope.

Jangan membuat seluruh portal, semua validator, UI penuh dan benchmark dalam satu batch tanpa hasil antara. Jangan menggabungkan perubahan tidak terkait hanya untuk mengejar status milestone.

## 2. Hubungan dokumen dan pemilik keputusan

| Dokumen | Menjawab |
| --- | --- |
| `plan.md` | Mengapa, scope, biaya, jadwal dan keputusan pengguna |
| `prd.md` di root | Kebutuhan MVP dan keputusan stack/container/database |
| `architecture.md` | Komponen, schema, tools, state dan batas akses |
| `runtime.md` | Topologi, handoff, antrean/recovery, storage, kuota dan biaya |
| `documentation-audit.md` | Temuan audit dan dependensi yang masih terbuka |
| `security-review.md` | Temuan desain, matriks izin dan pengujian keamanan yang belum dijalankan |
| `design.md` | Tampilan, label, susunan layar dan UI states |
| `user-flow.md` | Urutan tindakan pengguna/sistem serta kondisi gagal |
| `lab-spec.md` | Aktor, aturan dan perilaku target |
| `lab-vulnerabilities.md` | Peta privat 24 titik dan kontrol |
| `evaluation.md` | GT, 20 laporan 10/10, split dan metrik |
| Dokumen ini | Urutan implementasi, dependensi, checkpoint dan catatan kemajuan |

Hindari mengulang seluruh schema atau rumus pada checklist. Jika kontrak berubah, perbarui dokumen pemiliknya dan catat dampak pada milestone.

## 3. Milestone dan anggaran waktu

Sepuluh sesi, masing-masing sekitar tiga jam, mengikuti rencana 30 jam. Angka waktu adalah target, bukan hasil pengukuran atau jaminan bahwa seluruh scope selesai. Persiapan dokumentasi saat ini tidak dinyatakan sebagai sepuluh sesi implementasi yang sudah dijalankan.

| ID | Sesi | Fokus | Dependensi | Status sekarang |
| --- | ---: | --- | --- | --- |
| M0 | Persiapan | Kontrak, desain, alur dan daftar kerja | Keputusan pengguna | UI baseline disetujui 4 November; handoff siap, belum menguji backend |
| M1 | 1 | Fondasi API, session/ownership, schema chat/program/scope, policy dan mock | Gate UI terpenuhi; eksekusi lokal sesuai prompt | Selesai fondasi mock; 86 tes + Docker smoke/persistensi |
| M2 | 2 | Portal dan BAC development cadangan | M1 | Selesai teknis: BAC-08, HTTP/handoff/isolasi/crash; 111 tes kumulatif |
| M3 | 3 | BAC end-to-end dan UI minimum | M1-M2 | Selesai teknis lokal; planner mock + HTTP aktual, 125 tes/API/browser QA |
| M4 | 4 | XSS dan bukti browser | M3 | Selesai teknis lokal: delapan titik XSS/kontrol, browser M4a dan workflow/UI XSS-08 M4b; 180 tes |
| M5 | 5 | File upload dan bukti dampak | M3-M4 | Selesai teknis lokal; empat titik/delapan kondisi tersimpan, audit dan QA UI ulang 6 November lulus |
| M6 | 6 | Business logic dan kelengkapan 24 titik | M3; validator lain sesuai kebutuhan | DEFERRED untuk submission atas instruksi pengguna 7 November; catatan historis 13/24 dipertahankan, bukan gate R2-R4 |
| M7 | 7 | Draf 20 laporan, GT dan grouping | Fitur aktual dan bukti manual | Belum dimulai |
| M8 | 8 | Model live dan freeze | Akses API sesuai budget, development siap | Belum dimulai |
| M9 | 9 | Benchmark A/B dan analisis | M7-M8 | Belum dimulai |
| M10 | 10 | Dokumentasi hasil, visual dan submission | Fungsi/hasil aktual yang tersedia | Belum dimulai |

Model adapter live dapat dikerjakan lebih awal bila key/akses siap, menggunakan probe development. Freeze tetap menunggu M7, dan 20 laporan utama tidak dipakai untuk tuning. Key belum tersedia tidak menghalangi fondasi, lab dan worker dalam mode pengembangan yang berlabel.

## 4. Checkpoint per milestone

### M1 - Fondasi

- [x] Buat struktur proyek, dependensi dan konfigurasi contoh tanpa secret.
- [x] Ikuti `../prd.md`: pin dependensi app M1 sesuai Python 3.11 (worker/lab/browser dipin pada tahapnya); SQLite aplikasi melalui aiosqlite, migrasi SQL terversi dan satu proses app/dispatcher. Instal browser worker baru pada tahap terkait.
- [x] Siapkan Compose app dan image minimal, env.example tanpa secret, migrasi serta seed operator terpisah. Verifikasi startup/restart mempertahankan data dan tidak memanggil model/target. M1 tidak membuat worker/lab dummy; perintah tiga service baru lulus setelah komponen nyata tersedia.
- [x] Riwayat Git lokal sudah ada (baseline 0773f04); perubahan M1 masih working tree, tanpa commit/push/publikasi.
- [x] Tinjau status akses/provider dan batas Rp50.000 dari dokumen: key/checkout rupiah/tier aktual belum siap; mock dahulu, live CONFIGURATION_REQUIRED. Tidak membeli/memanggil API atau mengulang riset provider; pemeriksaan checkout aktual tetap prasyarat M8. Usia 18+ sudah dikonfirmasi.
- [x] Implementasikan schema membership/session, conversation/message/attachment, scope version dan report/run/action/evidence/assessment.
- [x] Seed dua bug hunter serta satu admin demo; role bukan input client. Tes AUTH-01/02/03 dan DATA-01 yang relevan.
- [x] Guideline draf/aktivasi dan binding operator; SCOPE-01/02 memblok OOS/UNKNOWN tanpa worker job.
- [x] Reservasi job/budget dan idempotency diperiksa; LIMIT-01 awal tanpa API berbayar.
- [x] Kunci kontrak antrean/error API, token/data quota dan ledger sesuai `runtime.md`; simulasikan expiry, crash dan biaya tidak diketahui.
- [x] Tambahkan registry target dan policy tindakan yang bisa diperiksa.
- [x] Storage memisahkan report dan run; run berulang tidak menimpa hasil sebelumnya.
- [x] Adapter mock serta live yang belum terkonfigurasi memberi status yang jelas.
- [x] Definisikan ProviderProfile/ProviderResult dan event per dispatch; simulasi gangguan sementara -> cadangan, quota habis -> gratis saja, cap bersama, refusal/config error tidak fallback, provider terkunci setelah respons pertama, dan benchmark tanpa routing otomatis. Ini simulasi kontrak, bukan uji provider live.
- [x] Pemeriksaan schema, transisi yang relevan dan batas target dijalankan.

**Siap lanjut:** satu report dapat disimpan dan workflow mock dapat diproses dengan provenance yang jelas. Hasil M1 memenuhi checkpoint fondasi ini. Ini belum bukti reproduksi bug, isolasi worker atau model live.

Potongan M1 berurutan: (a) bootstrap/config/storage dan Compose app; (b) session/membership/ownership serta scope/report snapshot; (c) state/queue/idempotency/ledger, mock/error contracts dan pemeriksaan batas yang relevan. Periksa setiap potongan sebelum lanjut, tanpa menganggap sub-batch pertama meluluskan seluruh M1. Waktu tiga jam merupakan target lama, bukan estimasi terukur untuk seluruh rincian ini.

### M2 - Lab BAC development

- [x] Verifikasi Docker daemon atau catat hambatan sebenarnya.
- [x] Buat target minimum, dua akun, objek uji dan aturan kepemilikan.
- [x] Gunakan SQLite lab terpisah dari database platform; seed/reset oleh maintenance operator tanpa GT/API key atau route reset di runtime agent.
- [x] Mulai dari BAC-08 development sesuai peta; bila diganti, perbarui peta sebelum freeze.
- [x] Evaluator dapat seed/reset dan memeriksa kondisi target.
- [x] Reproduksi terkontrol operator pada satu celah serta kondisi perbaikan/kontrol pemilik, dengan HTTP/state aktual tersimpan. Review/label GT manusia dataset utama tetap prasyarat M7.
- [x] Worker menjangkau target yang diizinkan dan menolak tujuan lain.
- [x] Verifikasi handoff inbox/outbox tanpa API key, SQLite, GT, Docker socket atau jaringan eksternal pada worker; target dirty memblok run berikutnya sampai reset evaluator.

**Siap lanjut:** target dapat direproduksi dan direset; jawaban evaluator tidak tersedia kepada worker.

### M3 - Alur vertikal BAC dan UI minimum

- [x] Intake -> scope -> plan -> policy -> HTTP worker -> evidence -> assessment.
- [x] Login, pilih satu program dan UI chat/upload TXT/MD menampilkan data backend aktual; Kirim berbeda dari Validasi snapshot.
- [x] Ganti adapter fixture dengan API; hapus pemilih role/login/skenario simulasi dari UI produk. Polling, draft persistence dan status model mengikuti kontrak backend.
- [x] Projection hunter/admin, publikasi bukti dan ekspor memenuhi AUTH/DATA; OOS/UNKNOWN dibuktikan nol request target.
- [x] Perubahan versi/revoke/cancel menghentikan antrean serta I/O aktif; cek SCOPE-03, NET-01/03 dan LIMIT-01 sebelum akses user lain.
- [x] Bukti mengikat akun, objek, request/response dan klaim.
- [x] Kegagalan/timeout tidak menjadi refutation otomatis.
- [x] Pembatalan menghentikan kerja lanjutan dan mempertahankan trace.
- [x] Review/ekspor dasar menjaga hasil mentah serta redaksi secret.
- [x] Bila key dan budget siap, lakukan probe model pada BAC development lebih awal; jika belum siap, catat hambatan dan jangan mengklaim agent live berfungsi.

**Siap lanjut:** alur BAC development dari input sampai review/publikasi telah diuji pada planner mock dengan HTTP aktual. Key/budget live belum siap; pemeriksaan itu tetap M8. Bukti internal hanya admin, publikasi M3 berupa ringkasan tetap. Detail dan batas pada [hasil M3](m3-verification.md).

### M4 - XSS

- [x] Tambahkan browser worker dengan scope seluruh navigasi/subresource.
- [x] Buat titik XSS development dan kontrol inert terlebih dahulu.
- [x] Marker lokal unik membuktikan eksekusi pada origin yang diperiksa.
- [x] Tangkap event/screenshot dan hubungkan ke tindakan.
- [x] Lengkapi titik XSS rencana secara bertahap dengan pemeriksaan operator tiap titik: XSS-01..07 dua kondisi/kontrol Chromium; manifest privat M4c. GT manusia dataset utama tetap M7.
- [x] Pastikan UI tidak mengeksekusi report/artefak aktif; NET-02/03 dan DATA-02 dibuktikan pada browser/hasil aktual.

- [x] M4b: workflow/verifier/assessment/UI XSS-08 dan publikasi ringkasan hunter setelah review; [hasil](m4b-verification.md).

**Status M4: selesai teknis lokal.** XSS-08 dibedakan dari pantulan teks; M4b menambah assessment/UI/publikasi ringkasan aman. M4c melengkapi tujuh titik lab dengan bukti origin/frame/nonce, perbaikan dan kontrol inert/aman; stored XSS memakai akun pembaca terpisah. Rute tambahan tetap jalur operator, bukan perluasan planner produk atau model live. [Fondasi M4a](m4-verification.md), [M4b](m4b-verification.md), [M4c](m4c-verification.md).

### M5 - File upload

- [x] Gunakan fixture lab terdaftar dan batas ukuran.
- [x] Uji dampak penyajian/penimpaan sesuai klaim, bukan hanya upload berhasil; artefak operator dua kondisi tiap titik tersimpan.
- [x] Kontrol attachment/inert atau penyimpanan aman punya evidence.
- [x] Petakan overlap XSS/BAC pada `root_cause_group`; konflik UP-04/XSS HTML dicatat, penyelesaian split tetap wajib sebelum freeze.
- [x] Catat status implementasi/verifikasi tiap titik upload.

**Siap lanjut:** M5 selesai untuk fixture/route terdaftar dengan planner mock. Workflow/verifier/UI hanya UP-04; titik lain operator, bukan dukungan produk umum. [Bukti dan audit M5](m5-verification.md).

### M6 - Business logic dan katalog lab

- [ ] Aturan yang relevan tersedia pada context agent. M6b membuktikan scope/rules terikat versi pada simulasi NONE saja; agent/tools business logic belum tersedia.
- [x] Simpan state sebelum/sesudah dan kontrol alur normal; M6a jurnal transaksi lab pada database sementara, belum evidence workflow produk.
- [x] Pengujian berulang sekuensial tidak diklaim sebagai race condition; M6a memeriksa idempotensi pemenuhan lokal.
- [ ] Lengkapi 8 BAC, 8 XSS, 4 upload dan 4 business logic yang direncanakan.
- [x] Tiap titik diberi status aktual: `evaluator/catalog.json` memuat 24 ID, 13 OPERATOR_REPRODUCED berdasarkan dokumen terdahulu dan 11 PLANNED; belum GT manusia dataset.
- [ ] Tinjau apakah development berbagi akar masalah dengan calon evaluasi dan perbaiki pembagiannya. Review/gate riwayat M6f selesai; perbaikan pembagian tetap outstanding, tanpa relabel katalog untuk meluluskan checkpoint.

**Siap lanjut:** lebih dari 20 titik kerentanan nyata terverifikasi, target rancangan 24, dengan mapping fitur dan bukti. Banyak route atau flag belum otomatis memenuhi jumlah itu.

### M7 - Laporan dan GT

- [ ] Asisten menyusun 20 teks report berbeda berdasarkan endpoint/aturan aktual.
- [ ] Komposisi 8 BAC, 8 XSS, 2 upload, 2 business logic.
- [ ] Pengguna memverifikasi 10 valid dan 10 tidak valid dengan evidence manual.
- [ ] Label jawaban, peta bug dan artefak GT terpisah dari input agent.
- [ ] ID/nama file, gaya bahasa dan urutan tidak membocorkan label.
- [ ] Pasangan/variasi satu akar masalah tetap satu grup.

**Siap lanjut:** 20 laporan benar-benar berlabel manual, bukan hanya mempunyai label rancangan dari asisten. Kasus ambigu diganti/diselesaikan sebelum freeze.

### M8 - Model live dan freeze

- [ ] Key dan akses endpoint tersedia tanpa melampaui budget total Rp50.000.
- [ ] Prioritaskan satu jalur yang siap sesuai PRD (awal OpenRouter/Gemini); jangan mewajibkan seluruh kandidat live untuk meluluskan MVP. OpenAI API/xAI opsional. Azure Foundry kandidat setelah kredit Students/deployment/quota terverifikasi; semuanya nonaktif sampai akses/pendanaan siap. OAuth plan ChatGPT belum masuk integrasi awal.
- [ ] Verifikasi tier gratis/kuota project sebelum mencatat biaya nol. Kunci model/provider awal respons, normalisasi tool/schema dan ledger termasuk provider gagal; fallback tidak memutar ulang tool/mutasi.
- [ ] Periksa minimum pembelian dan fee bila perlu; jangan menaikkan budget otomatis.
- [ ] Jalankan smoke probe development, catat tool success, refusal, waktu dan token.
- [ ] Live mode benar-benar menggunakan model; tidak menyamarkan mock/replay.
- [ ] Kunci model/provider, prompt, tools, batas run, target dan dataset.
- [ ] Nonaktifkan fallback/gateway auto-routing untuk benchmark; jika primary dipilih Gemini sebelum freeze, gunakan konfigurasi yang sama pada A dan B serta nama hasil yang benar.

**Siap lanjut:** integrasi model nyata terbukti dan konfigurasi eksperimen dapat direproduksi. Jika belum ada akses live, benchmark model belum siap meskipun UI/worker berfungsi.

### M9 - Benchmark

- [ ] Jalankan A/B pada 20 laporan final dengan reset setiap run.
- [ ] Gunakan DocumentPrediction untuk A dan assessment terverifikasi untuk B; 40 run dijadwalkan, denominator 20 per arm, biaya loop/retry tercatat.
- [ ] Simpan keputusan mentah, evidence, error, refusal, token dan biaya.
- [ ] Periksa perhitungan metrik dengan contoh manual serta abstention.
- [ ] Hitung hasil per kategori dan keseluruhan dari data aktual.
- [ ] Jangan menghapus kegagalan atau memasukkan koreksi manusia sebagai keputusan agent.

**Siap lanjut:** hasil dapat diaudit dan batas sampel/bias dijelaskan. Pengulangan atau pembanding lain hanya jika ada alasan, waktu dan budget.

### M10 - Artefak submission

- [ ] Ikuti [distribution.md](distribution.md): repo publik sebagai Link Karya, paket/rilis yang dapat dijalankan lokal; tidak ada dependensi live web/VPS.
- [ ] Perintah setup/demo telah dicoba dari kondisi bersih.
- [ ] Paket dan petunjuk rilis sesuai tag/commit; akses tanpa key diberi mode yang jujur dan live memakai konfigurasi pengguna.
- [ ] Rapikan UI dan buat thumbnail serta screenshot sesuai ketentuan.
- [ ] Buat slide, video YouTube maksimal 10 menit, ringkasan/proposal dan dokumentasi hasil.
- [ ] Periksa atribusi, data sensitif, akses link dan konsistensi deskripsi.
- [ ] Gunakan [submission-checklist.md](submission-checklist.md) untuk kelengkapan final.

**Siap submit:** artefak aktual dapat dinilai dan semua batasan material terlihat. Pengiriman ke platform mengikuti instruksi pengguna; dokumen ini tidak menyatakan submission sudah dilakukan.

## 5. Aturan perpindahan tahap

- Jika checkpoint gagal, perbaiki penyebab terkait sebelum menyatakan tahap selesai.
- Jika kegagalan membutuhkan akses/key yang belum ada, tulis dependensinya dan kerjakan bagian independen yang tetap diotorisasi.
- Jangan memakai mock sebagai pengganti kelulusan checkpoint live.
- Jangan mengurangi 20 laporan, komposisi 10/10 atau syarat lab lebih dari 20 titik secara diam-diam.
- Login dua role, scope versioning dan projection bukti menambah kerja; jangan menganggap estimasi lama otomatis mencukupi.
- Jadwal 30 jam cukup ketat untuk scope ini; bila realisasi melebihi target, catat sisa pekerjaan dan kompromi yang diperlukan sebelum freeze.
- Fokus satu tahap aktif, tetapi perbaikan bug dari tahap sebelumnya dapat dilakukan jika memengaruhi tahap sekarang.

## 6. Catatan kemajuan per batch

Gunakan format singkat ini setelah implementasi dimulai:

```text
Milestone aktif:
Lingkup batch:
File/fitur yang berubah:
Pemeriksaan yang dijalankan dan hasil:
Evidence/artefak:
Status checkpoint: belum / sebagian / selesai
Hambatan nyata:
Langkah berikutnya:
```

Batch M1 aktual dicatat di bawah dan pada [m1-verification.md](m1-verification.md). Catatan prototipe/dokumentasi sebelumnya tetap riwayat; bukan status terbaru backend.

## Catatan review/desain 3 November 2026

Pengguna menyatakan pendaftaran diterima. Arsitektur, matriks izin, gate scope, versioning, evidence projection dan desain chat dua role diperbarui. Pemeriksaan pada tahap ini hanya dokumentasi; tidak ada source aplikasi, worker, live API atau milestone M1-M10 yang dinyatakan selesai. Desain layar ada di `design.md`; acceptance criteria runtime di `security-review.md` masih BELUM DIUJI.

## Batch prototipe UI v0.1 - 3 November 2026

Lingkup: UI lokal grafit + sage, chat/upload, pratinjau login/program/role, guideline, scope, evidence dan variasi status dengan fixture. Pemeriksaan browser dan dokumentasi hasil ada di [ui-review.md](ui-review.md). Status saat batch 3 November: siap ditinjau, belum disetujui. Pengguna kemudian menerima baseline pada 4 November sebagaimana catatan terbaru di bawah. Batch prototipe tidak meluluskan M1-M10; backend, target, model live dan dataset belum dimulai.

## Audit dokumentasi - 3 November 2026

Kontrak baseline/metrik, runtime dan integrasi UI diperjelas tanpa membangun backend. Temuan, pemeriksaan dan dependensi dicatat di [documentation-audit.md](documentation-audit.md). Review dokumen tidak meluluskan checkpoint runtime atau mengubah status M1-M10.

## Pengurangan laporan - 4 November 2026

Pengguna mengurangi dataset dari 40 ke 20 laporan. Target aktif: 10 valid/10 tidak valid, komposisi 8 BAC/8 XSS/2 upload/2 business logic, 40 run A/B. Lab 24 titik tetap target sebelumnya: sepuluh area benchmark, empat development dan sepuluh non-benchmark. Ini revisi scope dokumen, bukan pembuatan report, GT atau backend. Pengurangan lab memerlukan keputusan terpisah; beban lab 24 titik masih menjadi risiko waktu.

## Persetujuan UI baseline - 4 November 2026

Pengguna menyatakan UI fix, dengan kemungkinan perbaikan nanti. Persetujuan ini memenuhi gate untuk memulai backend M1 di chat baru; tidak memerlukan konfirmasi UI ulang atau menyelesaikan semua polish visual lebih dahulu. Tahap M1 tetap BELUM DIMULAI pada turn dokumentasi ini. Revisi UI yang relevan boleh dilakukan saat implementasi, dengan pemeriksaan sesuai perubahan, tanpa menganggap persetujuan visual sebagai bukti auth/worker/model aman.


## M1 lokal selesai ? 4 November 2026

- Milestone aktif: M1, selesai untuk fondasi mock; M2 belum dimulai.
- Lingkup batch: M1a bootstrap/config/storage/Compose -> 7 tes; M1b auth/scope/draft/snapshot -> 19 tes kumulatif; M1c queue/ledger/provider/mock -> 86 tes kumulatif.
- File/fitur: `app/`, migrasi SQL, `tests/`, `scripts/m1_smoke.py`, pyproject/lock/env/Docker/Compose dan status dokumen. `ui-prototype/` dipertahankan.
- Pemeriksaan: 86 passed; pip check host/container bersih; Docker cold build/start/health, smoke concurrency/ownership serta restart/stop-start lulus; isi 15 tabel identik setelah restart. Tidak ada target/provider live yang dipanggil.
- Evidence/artefak: [hasil M1](m1-verification.md), [inventaris dependensi](dependencies-m1.json), suite tests dan smoke yang dapat dijalankan ulang. Data/password smoke privat di luar Git; bukan dataset/GT.
- Status checkpoint: selesai M1 lokal, bukan seluruh acceptance criteria worker/browser/live.
- Hambatan nyata: helper sandbox gagal; eksekusi lokal melalui eskalasi diterima. Docker kini siap. Masalah lock Windows dan readiness smoke sudah diperbaiki; tidak ada pengujian wajib fondasi M1 tersisa yang terhalang lingkungan.
- Perubahan kontrak: startup mengakhiri QUEUED dan LEASED yang tertinggal sebagai PROCESS_INTERRUPTED untuk mencegah inference otomatis. Dampak dicatat di runtime.md; pengguna mengirim run baru secara eksplisit.
- Langkah berikutnya: M2 BAC-08 development, database lab terpisah, maintenance seed/reset evaluator, reproduksi manual/kontrol dan handoff/isolasi worker. Key/billing/tokenizer/model nyata tetap checkpoint M8, UI chat API pada M3.


## M2 lokal selesai ? 4 November 2026

- Lingkup batch: lab API/SQLite/maintenance -> empat tes; handoff/worker -> 21 tes awal M2; pengujian kumulatif akhir **111 passed in 58.71s** tanpa skip.
- Perubahan: `lab/`, `worker/`, `boundary/`, `evaluator/m2.py`, `app/transport.py`, CLI operator M2, migrasi 003, setup secret, Docker/Compose dan tes/dokumentasi. UI prototype tetap dipertahankan.
- Hasil Docker: tiga service nyata dan empat volume; dua kondisi BAC-08 memberi dampak/kontrol yang diharapkan, 12 dispatch per run; duplicate DELETE tidak diulang; dirty gate/reset/health dan restart lulus. Crash SIGKILL setelah commit menghasilkan ACTION_OUTCOME_UNKNOWN tanpa auto-replay.
- Jaringan: koneksi positif worker-lab dan health loopback berhasil; metadata/TEST-NET/gateway/app/port lain/DNS/IPv6 ditolak. App tidak menjangkau lab. Proses Python non-root dengan capability nol; RO mount dan penolakan symlink diuji aktual.
- Evidence: [hasil M2](m2-verification.md), raw lokal `artifacts/m2/`, HTTP capture privat app, [inventaris OS](dependencies-m2.json). Bukan dataset 20 laporan atau hasil model.
- Status checkpoint: M2 selesai teknis; penetapan GT manusia, browser, model dan UI lengkap tetap tahap masing-masing.
- Hambatan/perbaikan: fixture stream HTTPX, DNS Docker dan readiness probe diperbaiki. Helper sandbox masih gagal; jalur eksekusi lokal yang diterima digunakan. Tidak mengubah firewall host, menghapus volume atau memanggil model.
- Kontrak diperjelas: mode model terpisah dari tool_execution_mode; M2 operator LAB tanpa model/verdict. Dirty run boleh menyelesaikan kontrol dalam run yang sama; run berikutnya perlu reset evaluator/snapshot baru. Bootstrap firewall root kemudian drop UID/capability, diuji per proses.
- Berikutnya M3: report -> policy -> worker -> evidence -> verifier BAC dan UI chat API. Jangan langsung menambahkan 23 titik/20 laporan atau model live pada batch ini.

## M3 lokal selesai - 5 November 2026

- Milestone aktif: M3, selesai teknis lokal; belum memulai M4.
- Lingkup: meninjau implementasi M3 yang sudah ada pada working tree, melengkapi regresi/QA dan memperbaiki respons UI dari polling/sesi/navigasi yang sudah usang.
- File/fitur: planner/verifier BAC, workflow/handoff, API review/publikasi/projection dan UI backend; regresi pada `tests/test_m3_bac.py`, evaluator API dan `scripts/m3_ui_smoke.cjs`.
- Pemeriksaan: 125 tes lulus dalam 218,43 detik; build app, smoke API Docker dan QA Chromium host, sintaks JS, pip check dan whitespace. Hasil rinci/riwayat kegagalan pada [m3-verification.md](m3-verification.md).
- Evidence/artefak: hasil dan tiga screenshot lokal di `artifacts/m3/`; capture HTTP privat app. Tidak masuk benchmark/GT manusia.
- Status checkpoint: selesai untuk satu BAC development dengan planner mock dan HTTP aktual. Tidak ada model live/browser worker atau ekspor bukti mentah bagi hunter.
- Hambatan/perbaikan: helper sandbox masih memerlukan jalur eksekusi lokal yang diterima. Timeout persiapan test dipisah dari batas pembatalan; judul fixture dibuat unik; locator bukti JSON di-escape diperbaiki. Kuota start produk dipertahankan.
- Langkah berikutnya: M4 browser worker dan NET-02/03 sebelum XSS development/kontrol inert. Tidak push, deploy, membuat dataset utama atau mengaktifkan provider live.

## M4a lokal - 5 November 2026

- Milestone aktif: M4 sebagian; potongan browser foundation dan XSS-08 development selesai teknis.
- Perubahan: requirements-worker.lock, image/Compose/seccomp/notice; kontrak BrowserArguments/BrowserObservation, ToolRouter, probe DOM/screenshot/marker, lab preview dan reset terpisah kondisi XSS, handoff/provenance privat, verifier pasangan observasi serta evaluator/QA.
- Pemeriksaan: 145 passed in 105.80s; dua kondisi/delapan request per kondisi, dua akun; network browser dan NET-03 ulang; cancel menyisakan satu bukti tanpa assessment/browser/error callback; evidence UI inert hanya admin. [Hasil M4a](m4-verification.md).
- Evidence: artifacts/m4 privat, capture app dan dependencies-m4.json. Kegagalan runner HTTPX awal dan error cleanup callback dipertahankan/dijelaskan; kondisi dan jaringan lulus tidak diulang tanpa kebutuhan.
- Batas: operator saja, tidak memakai model. Scope profil satu route/fixtures tetap; tidak mengklaim general browser tools atau seluruh keluarga XSS. Dua dari 24 titik direproduksi operator; GT manusia tetap pending.
- Langkah berikutnya: M4b workflow/verifier/assessment/UI XSS dan publikasi bukti, lalu tujuh titik XSS lain bertahap. Belum M5, live API, benchmark, push atau deploy.


## M4b lokal - 5 November 2026

- Lingkup: workflow XSS-08 empat probe/dua akun, verifier bukti tersimpan, assessment privat, review/publikasi ringkasan tetap dan pemilih kemampuan UI.
- Pemeriksaan: 156 tes penuh dan 31 tes terarah akhir lulus. API dua kondisi memberi CONFIRMED/REFUTED; cancel/network aktual diulang sesudah fix cleanup. QA UI/ekspor/responsif lulus; [hasil dan riwayat gagal](m4b-verification.md).
- Evidence: artifacts/m4b privat, network regression artifacts/m4/network-verification.json dan capture app; riwayat/ledger/kuota tetap dipertahankan.
- Status checkpoint: M4b selesai teknis lokal, M4 tetap sebagian; planner mock bukan AI/model live, verdict hanya fixture/rute pratinjau.
- Perbaikan: intercept bertahan sampai context ditutup; route dibatalkan diselesaikan dengan abort. Helper sandbox tetap memakai jalur eskalasi lokal yang diterima.
- Berikutnya: tujuh titik XSS lain secara bertahap dengan kontrol tiap titik; bukan M5/live/GT/benchmark/push/deploy.

## M4c lokal - 5 November 2026

- Lingkup: tujuh titik XSS lab, migrasi/seed/penugasan reviewer, mutasi HTTP autentik dengan CSRF dan kontrol aman tiap fitur; evaluator operator terpisah dari planner development.
- Pemeriksaan: 180 tes host lulus; 14 kondisi Chromium/42 capture/138 request, marker origin/frame/nonce dan stored XSS lintas akun; [hasil, artefak dan kegagalan awal](m4c-verification.md).
- Evidence: artifacts/m4c privat, manifest tujuh titik dengan hash source/image; hasil gagal dan raw capture dipertahankan. Ledger/riwayat/kuota aplikasi tidak dihapus.
- Status checkpoint: M4 selesai teknis lokal; total sembilan dari 24 titik direproduksi operator. GT manusia dataset dan model live tetap pending; cakupan UI XSS tetap XSS-08.
- Berikutnya: M5 file upload; belum dimulai pada batch ini. Tidak commit/push/deploy/rilis atau benchmark.


## M5 audit dan penutupan lokal - 6 November 2026

- Lingkup: meninjau source M5/artefak yang sudah ada, menutup verifikasi dan menyinkronkan status; tidak menjalankan ulang reproduksi upload.
- Perubahan: auditor offline `scripts/audit_m5_artifacts.py` dengan 12 tes; runner QA kini menampilkan error; dokumentasi status, kontrak, katalog dan grouping diperbarui.
- Pemeriksaan: 15 tes defensif M5 (9,88 detik), 12 tes auditor (1,97 detik), delapan kondisi tersimpan, 120 hash source dan 18 signature/hash PNG lulus. QA UI ulang lima viewport/pemisahan role/ekspor lulus, nol run/request target baru. Suite penuh sebelumnya 205 tes tidak diulang pada audit ini.
- Kegagalan: satu unduhan QA canceled, percobaan berikutnya lulus; penyebab belum dipastikan dan artefak gagal dipertahankan. SQLite lab dibaca dengan UID pemilik setelah percobaan root read-only ditolak. Helper sandbox masih memerlukan jalur eskalasi yang diterima.
- Kondisi akhir: app/lab healthy, worker idle/bersih; app ready, maintenance mati; snapshot app/worker/lab cocok, seluruh kondisi lab fixed. Riwayat/ledger/kuota tidak direset.
- Status: M5 selesai teknis lokal berdasarkan bukti runtime 5 November yang dicocokkan dengan source saat audit. Total 13 dari 24 titik; bukan GT manusia atau hasil model.
- Berikutnya: M6 business logic dan tujuh BAC tersisa. UP-04 development berbagi grup HTML dengan XSS-01..05; split belum siap freeze. Model live/GT/benchmark/push/deploy belum dilakukan. [Rincian M5](m5-verification.md).


## M6a kontrol bisnis aman - 6 November 2026

- Milestone aktif: M6 sebagian; M6a selesai untuk fondasi kontrol aman, tanpa titik kerentanan tambahan.
- Perubahan: migrasi 004, lab/business.py, setup operator eksplisit dengan guard identitas database, registrasi route/listing, urutan cleanup reset, 28 tes M6a dan script pemeriksaan disposable. Dokumen kontrak/status diperbarui.
- Pemeriksaan akhir: 95 tes terarah lulus dalam 70,52 detik; kontrol host dan container non-root/read-only/network none tanpa volume/secret lulus dengan hash source yang cocok. Stok 100 -> 93 untuk tujuh barang; replay tetap 93 dengan fulfillment yang sama.
- Kegagalan: helper async tes awal diperbaiki; build Dockerfile dengan network none gagal saat instalasi dependensi. Container check memakai image turunan lab lokal, bukan bukti clean build baru. Tidak mengubah dependensi atau service Compose aktif.
- Artefak: artifacts/m6a bertimestamp untuk state sebelum/sesudah, source hash dan image ID. Tidak mereset app/lab aktif, kuota, evidence atau ledger; tidak melakukan pemanggilan model atau reproduksi kerentanan baru.
- Status checkpoint: M6a selesai lokal; service Compose aktif tetap M5. BUSINESS_LOGIC tetap UNSUPPORTED, aturan publik belum diintegrasikan ke context model. Hitungan tetap 13/24; sebelas mekanisme BAC/BL tetap planned.
- Berikutnya: integrasi context aturan dan verifikasi runtime persisten dengan maintenance/snapshot, peninjauan grouping sebelum freeze. M6/M7/model live/benchmark belum selesai; tanpa commit/push/deploy. [Hasil M6a](m6a-verification.md).


## M6b konteks simulasi, persistensi dan katalog - 6 November 2026

- Milestone aktif: M6 tetap sebagian; bagian defensif M6b selesai.
- Perubahan: label business_rules_version, SimulationContext pada mock NONE saja, audit/hash konteks, katalog 24 ID dan gate offline, probe/runner persistensi serta cleanup berlabel, tes dan status dokumen.
- Pemeriksaan akhir: 145 tes terarah lulus dalam 91,66 detik. Dua fase container memakai volume khusus mempertahankan stok 93, satu fulfillment dan empat event; source cocok host, cleanup PASS. Compose app/lab tetap healthy, tidak ada volume uji berlabel yang tersisa.
- Kegagalan awal: satu query tes memakai kolom audit kind alih-alih event_type; diperbaiki. Gate katalog exit 2 memang hasil yang diharapkan: 13 OPERATOR_REPRODUCED historis/11 PLANNED, konflik UP-04 development dengan XSS-01..04 evaluasi.
- Artefak: artifacts/m6b bertimestamp untuk persistensi, katalog dan ringkasan/hash. Tidak membaca secret operator, memperluas tools/planner LAB, mengeksekusi celah baru atau mengubah data/ledger/kuota proyek.
- Status checkpoint: aturan tersedia pada simulasi tanpa tool; agent/verifier/UI business logic LAB belum tersedia. Katalog tiap ID selesai dicatat; kelengkapan 24 titik dan grouping belum selesai. M6 tidak ditandai lulus.
- Berikutnya: bukti yang masih kurang dan keputusan grouping tetap outstanding sebelum M6/M7/freeze; GT manusia/model live/benchmark terpisah. Target 24 titik/20 laporan tidak dikurangi. [Hasil M6b](m6b-verification.md).


## M6c audit rekaman offline - 6 November 2026

- Milestone aktif: M6 tetap sebagian; tambahan audit rekaman defensif selesai.
- Perubahan: evaluator/business_record_audit.py, tests/test_business_record_audit.py dan dokumentasi kontrak/batas. Tidak mengubah lab, worker, provider atau alur produk.
- Pemeriksaan: 25 tes baru lulus dalam 0,32 detik; dua artefak persistensi M6b tersimpan CONSISTENT. Suite 145 tes sebelumnya tidak diulang; tidak ada eksekusi target baru.
- Kontrak: schema/ukuran input dibatasi; stok, quantity, binding ID/versi, jurnal agregat, source reference dan replay diperiksa. Hasil konsistensi tidak memberi verdict/GT atau bukti origin/permission/approval per aksi. Missing trace/control tidak menjadi refutation.
- Artefak: artifacts/m6c bertimestamp, mencatat hash input/source dan hasil sebelum keputusan status. Data/volume Compose, kuota/ledger serta artefak lama dipertahankan.
- Checkpoint: tetap 13/24; sebelas mekanisme PLANNED, grouping dan validator business logic produk belum selesai. Tidak mengurangi target atau menandai M6 selesai. [Batas tambahan audit](m6b-verification.md).

## M6d penguatan input auditor - 6 November 2026

- Milestone aktif: M6 sebagian; penguatan parser M6d selesai dan diverifikasi lokal pada turn lanjutan.
- Lingkup: batas pembacaan byte aktual pada auditor offline; penolakan kunci JSON duplikat dan konstanta nonstandar sebelum validasi schema/status.
- Perubahan: evaluator/business_record_audit.py dan delapan kasus tes tambahan. Tidak menambah event trace, tools atau validator produk.
- Pemeriksaan: 33 tes parser lulus dalam 0,64 detik; dua artefak historis M6b CONSISTENT. Parser masuk suite akhir M6e 97 tes lulus. Hambatan terminal/review sebelumnya teratasi lewat eksekusi berizin; tidak mengulang reproduksi target.
- Checkpoint: M6d selesai defensif, tetap 13/24, katalog/grouping tidak diubah. [Hasil M6d](m6d-verification.md).
- Berikutnya: rekaman event individual kontrol normal, diselesaikan pada M6e di bawah.

## M6e event kontrol normal - 6 November 2026

- Milestone aktif: M6 sebagian; potongan defensif M6e selesai lokal.
- Perubahan: auditor trace empat event dan runner ASGI/database sementara, metadata owner/staff-unit, binding approval/fulfillment/state serta 32 tes baru; tanpa perubahan lab/worker/assessment/UI.
- Pemeriksaan: 97 tes terarah lulus dalam 33,47 detik; runner dan CLI record tersimpan CONSISTENT. Empat event, stok 93 dan satu fulfillment tetap sama setelah lifecycle ASGI ulang. Bukan restart proses/container/TCP. Suite penuh tidak dijalankan.
- Riwayat gagal: 96 passed/1 failed karena fixture token konstan; diperbaiki menjadi unik tanpa mengubah aturan aplikasi. Artefak, hash source/input dan ringkasan gagal di artifacts/m6e; [hasil/batas](m6e-verification.md).
- Checkpoint: hasil hanya konsistensi rekaman normal, verdict/GT null; M6 tetap 13/24. Gate katalog ulang exit 2 dengan 11 PLANNED dan konflik UP-04/XSS-01..04. Service Compose tidak diperbarui.
- Berikutnya: review pemisahan akar masalah development/evaluasi sebelum freeze; kelengkapan lab/validator produk/model live/GT tetap terpisah.

## M6f review grouping dan riwayat development - 6 November 2026

- Milestone aktif: M6 sebagian; potongan review/gate M6f selesai, pembagian final belum selesai.
- Perubahan: riwayat development sistem versi v1 pada evaluator, gate konflik historis/perubahan grup/kuota kategori dan inventaris kandidat; katalog/manifest/runtime tidak diubah.
- Pemeriksaan: 21 tes lulus dalam 0,39 detik; CLI katalog VALID dengan exit 2 yang diharapkan. Hash katalog sebelum/sesudah identik, artefak/hash source di artifacts/m6f. Suite/reproduksi target terdahulu tidak diulang.
- Keputusan: jangan freeze split; pindah label UP-04 tidak menghapus grup HTML yang sudah dipakai development. Hanya XSS-06 kandidat tercatat di luar grup development, belum cukup bagi empat area XSS. [Review dan batas](m6f-verification.md).
- Checkpoint: tetap 13/24 dan 20 laporan sasaran; 11 PLANNED, konflik HTML, GT manusia/model live/validator produk masih outstanding. Review bukan kelulusan grouping atau benchmark.
- Berikutnya: dukungan produk business logic dan kelengkapan bukti tetap pekerjaan terpisah; penetapan split menunggu mekanisme/GT aktual dan review revisi yang mempertahankan riwayat development.

## Alur review rekaman bisnis di produk - 6 November 2026

- Hasil: snapshot laporan -> impor JSON admin -> konsistensi -> catatan review -> publikasi/ekspor pelapor -> penarikan saat review ulang, tersedia pada UI/API. Tidak menambah checkpoint audit baru atau menyatakan M6 selesai.
- Perubahan: core konsistensi bersama di boundary, wrapper CLI, router/migrasi app 004, binding nomor/hash revisi dan scope/aturan, storage file immutable/kuota, projection role, UI dan QA disposable.
- Verifikasi: 152 tes terarah lulus dalam 58,40 detik; QA Chromium 1366/390 px lulus dengan nol page error/request eksternal. Uji persistensi dua lifecycle app, penolakan mutasi file sebelum review/publish, CSRF/ownership, input/kuota serta kerahasiaan catatan/ekspor lulus.
- Runtime: hanya app Compose diperbarui setelah nol job aktif. Health/migrasi/JS cocok source; 37 riwayat run dan agregat ledger tetap, ID worker/lab tidak berubah. Tidak membuat record uji pada data Compose aktif. [Panduan, bukti dan riwayat kegagalan](business-record-review.md).
- Batas: review manual hanya konsistensi unggahan; tidak mengesahkan origin/izin aktor, tidak memanggil worker/model atau menetapkan verdict/GT. BUSINESS_LOGIC LAB tetap unsupported, katalog 13/24 dan grouping belum siap; 11 titik serta otomasi eksploitasi tidak dikerjakan. M6 tetap sebagian, tidak ada perubahan target/alokasi/manifest atau klaim kelulusan baru.

## Workflow langkah admin dari bukti bisnis - 6 November 2026

- Perubahan: phase kelengkapan bukti dan next actions tetap, konteks schema/hash/versi, endpoint GET admin serta dialog/ekspor Langkah berikutnya. Tidak ada dispatch target/model atau migrasi baru.
- Pemeriksaan: 172 tes terarah lulus dalam 68,82 detik, termasuk 20 workflow baru; QA desktop/mobile dengan dialog dan download konteks lulus. Percobaan QA awal gagal pada locator ringkasan, diperbaiki tanpa perubahan produk; artefak gagal tetap ada.
- Bukti: contexts memakai revisi/aturan asal, flag versi current berubah saat ada revisi baru, hasil dihitung ulang dan binding diperiksa, catatan review tidak masuk konteks, akses hunter tetap ditolak sesudah publikasi. Semua phase tetap membutuhkan review manusia; verdict/GT null.
- Runtime: app saja diperbarui setelah cek nol job aktif; 37 riwayat dan seluruh agregat data/ledger tetap, worker/lab sama, source/JS tersaji cocok host. [Panduan dan artefak](business-record-review.md#workflow-bukti-dan-konteks-terstruktur).
- Status: kontrak workflow administratif selesai untuk jalur ini, bukan agentic live atau dukungan BUSINESS_LOGIC LAB. M6 tetap sebagian, katalog 13/24 dan grouping belum siap; target/alokasi/manifest tidak diubah.
