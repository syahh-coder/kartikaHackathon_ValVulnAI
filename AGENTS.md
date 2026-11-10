# Instruksi pengembangan repositori

## Steering provider7 November2026

Pengguna memilih Azure Foundry lewat akun pelajar. Adapter Azure teks, wiring triage/readiness/evaluator dan konfigurasi privat telah diimplementasikan serta diuji148 kasus simulasi/regresi; LIVE_VERIFIED tetap false. Ikuti `docs/azure-setup.md` dan `docs/azure-verification.md`. Preview8010 tetap MOCK sampai `.env.azure` lengkap dan overlay diaktifkan secara eksplisit pada project/volume/ledger preview yang sama. Key/endpoint/deployment, kredit/kuota/harga dan kompatibilitas model belum terverifikasi. Azure tidak memberi tagihan aktual per respons pada kontrak ini; tahan reservasi COST_UNKNOWN, jangan menyamakannya dengan nol atau estimasi tarif. Jangan mengaktifkan PAYG/provisioning, mereset budget/data atau mengulang M6. Ketentuan keamanan TEXT-ONLY dan review sebelum publikasi tetap berlaku.


Berlaku untuk pekerjaan di seluruh repositori ini. Ikuti instruksi pengguna dan instruksi tingkat lebih tinggi. Dokumen ini mengatur asisten coding; prompt agent produk dibuat terpisah saat implementasi.

## Keputusan aktif 7 November 2026

**Hasil jalur review terbaru:** kode independen R3b–R3f dan persiapan R4 telah dikerjakan; gunakan `docs/final-review.md`, `docs/r3-r4-verification.md` dan `docs/r3-runbook.md` sebagai checkpoint. Paket berstatus READY_FOR_REVIEW_WITH_PENDING_INPUTS, bukan benchmark/submission selesai. Source schema006 dan profil evaluator opsional diuji terpisah; service/data/ledger aktif tetap dipertahankan. GT pengguna, bukti terikat kandidat, konfigurasi/smoke live, freeze/eksperimen nyata, lisensi dan video/link final masih pending. Jangan mengulang kode yang selesai atau mengejar M6. Publikasi/submit tetap menunggu review/otorisasi pengguna.

**Instruksi paling baru: selesaikan seluruh pekerjaan jalur submission yang dapat dikerjakan, lalu pengguna mereview paket konkret sekaligus.** Ikuti prompt berkelanjutan pada `docs/execution-prompt.md` dari sisa R3 sampai persiapan R4. Checkpoint tetap diperiksa dan dicatat secara berurutan, tetapi bukan alasan mengakhiri pekerjaan atau meminta izin lanjut di tiap tahap. Instruksi lama “satu potongan lalu berhenti/laporkan tahap berikutnya” digantikan keputusan ini; jangan mengerjakan seluruh kode tanpa checkpoint internal.

Jika GT manusia, bukti, key/akses atau keputusan eksternal belum tersedia, lanjutkan semua pekerjaan independen. Jangan memalsukan GT/penerimaan pengguna, inferensi live, metrik atau artefak final. Akhiri dengan `docs/final-review.md` dan paket READY_FOR_REVIEW, atau READY_FOR_REVIEW_WITH_PENDING_INPUTS bila masih ada prasyarat nyata. Publikasi/submit menunggu review pengguna; sekarang siapkan file serta draftnya. Status “siap review” bukan “benchmark/submission selesai”.

**Checkpoint terbaru setelah R2/R3a:** R1/R2 sudah CODE_TESTED dan tidak diulang. R3a persiapan CODE_TESTED menurut `docs/r3-verification.md`: peta kemampuan, 20 kandidat privat/GT kosong, worksheet/import dan scorer offline. R3 keseluruhan belum selesai; lanjut R3b sesuai `docs/execution-prompt.md`, dengan GT pengguna, bukti B, integrasi prediksi/runner serta freeze/live tetap pending. Jangan menganggap kandidat/GT metadata/scorer offline sebagai benchmark. Catatan prioritas R2 di bawah adalah riwayat yang sudah dieksekusi.

**Instruksi terbaru pengguna: skip pekerjaan M6 yang belum dapat diselesaikan dan lanjut checkpoint berikutnya, dengan tes terarah.** Status pekerjaan M6 asli **DEFERRED untuk submission**, tidak lagi blocker. Jangan mengerjakan BAC-01..07/BL-01..04 atau mengejar gate 24 titik pada jalur aktif. Catatan historis/katalog tetap dipertahankan. R1 sudah CODE_TESTED menurut `docs/r1-verification.md`, live masih CONFIGURATION_REQUIRED; berikutnya R2 pada `docs/execution-prompt.md`. Jangan mengulang R1 atau meminta izin skip/UI lagi.

Jalankan pemeriksaan yang diperlukan untuk perubahan aktif, lalu lanjut setelah lulus. Jangan mengulang semua suite historis tanpa perubahan terkait; kegagalan diperbaiki dan diuji pada subset terdampak, diperluas hanya jika ada alasan konkret. Laporkan hasil R2 dan checkpoint berikutnya; M6 DEFERRED hanya disebut bila relevan, bukan sebagai hambatan rutin setiap akhir batch.

Pengguna menyetujui penyempitan scope setelah review M6 dan meminta dokumentasi/prompt lanjutan. Ikuti `docs/submission-scope.md`, `docs/evaluation.md` (functional-v2) dan `docs/execution-prompt.md` terbaru. Target 24 titik menjadi backlog, M6 DEFERRED; BUSINESS_LOGIC LAB belum didukung. R1 adapter/triage teks sudah CODE_TESTED; prioritas berikutnya R2 UI/ringkasan bukti, lalu R3 GT/evaluasi fungsional dan R4 paket submission. Jangan menambah auditor/review bisnis sebagai pengganti atau mengulang M1/R1.

Integrasi model aktif direncanakan TEXT-ONLY, tanpa tool calling atau model-to-worker dispatch; backend tetap menentukan scope/izin dan verifier tetap terpisah dari prediksi AI. Pertahankan tiga jalur produk BAC-08/XSS-08/UP-04 tanpa memperluas otomasi eksploitasi. Target evaluasi 20 teks 10/10, alokasi kerja 8 BAC/8 XSS/4 upload; bukan held-out akar masalah baru. BUSINESS_LOGIC/OOS/unsupported bukan GT INVALID. Protokol ketat lama dan riwayat development tetap diarsipkan; katalog/status/grup/manifest serta gate lama tidak diubah agar lulus.

Keputusan ini menggantikan cakupan submission serta dependensi/alokasi lama yang bertentangan di bawah, bukan hasil verifikasi atau bukti model live sudah tersedia. Kontrak keamanan, budget Rp50.000, GT manusia dan larangan klaim palsu tetap berlaku. Batch dokumentasi tidak mengotorisasi push baru, deployment, pembelian atau reset service/data.

## Konteks yang sudah dikonfirmasi

- Tim solo: **ukas and codex vs everbody**.
- Pada 3 November 2026 pengguna menyatakan pendaftaran program diterima. Pada 4 November 2026 pengguna menyatakan **UI fix sebagai baseline untuk mulai backend**, dengan kemungkinan perbaikan berikutnya. Gate UI sudah terpenuhi; jangan meminta persetujuan UI ulang untuk M1. Eksekusi M1 diminta dilakukan di chat baru sesuai docs/execution-prompt.md. Persetujuan UI tidak membuktikan backend/worker/model aman atau berfungsi, dan tidak mengotorisasi live API/cloud. Pengguna kemudian mengotorisasi push awal dokumentasi dan UI ke repo GitHub di bawah; ini tidak memulai M1 atau deployment.
- Nama kerja untuk draf pendaftaran: **ValVuln AI: Agen Validasi Laporan Kerentanan**. Rekomendasi kategori terbaru **Penindakan**, menggantikan usulan Core Infra sebelumnya setelah membaca rulebook. Jangan menyatakan formulir sudah dikirim.
- Python + FastAPI; target portal pengadaan/logistik milik sendiri. UI chat dengan login bug hunter/admin program, satu program MVP; role server-side, guideline draf/aktivasi oleh admin dan versi scope per run. Worker baru boleh mengakses portal Docker yang sudah berjalan setelah scope/prasyarat/izin lolos backend; tidak membuat target baru per report.
- Stack MVP dirangkum di `prd.md`: tiga container tetap (app, worker, lab), SQLite aplikasi dan lab terpisah, UI Jinja2/JavaScript disajikan app, Chromium di worker; evaluator CLI pada host. M1 fondasi app/Compose/dependensi sudah diimplementasikan dan diuji lokal pada 4 November 2026; hasil pada `docs/m1-verification.md`. M2 worker HTTP/lab BAC-08 sudah dibuat dan diuji; hasil di `docs/m2-verification.md`. M3 alur BAC/UI backend dan verifier juga selesai teknis lokal pada 5 November 2026, dengan 125 tes, smoke API Docker dan QA browser host; hasil di `docs/m3-verification.md`. Planner tetap mock, HTTP lab aktual. M4a browser worker sandbox dan XSS-08 development kini diuji operator pada 5 November 2026; 145 tes, dua kondisi/kontrol, jaringan/cancel serta UI evidence, hasil di `docs/m4-verification.md`. M4b workflow/verifier/assessment/UI XSS-08 dan ringkasan hunter selesai teknis lokal pada 5 November 2026: 156 tes, API dua kondisi, cancel/network ulang dan QA UI, hasil di `docs/m4b-verification.md`. Cleanup mempertahankan routing sampai context tertutup dan menyelesaikan route dibatalkan dengan abort. Pada akhir M4b, M4 masih sebagian; tujuh titik tambahan kemudian diselesaikan M4c di bawah. Planner mock dan fixture tetap, tanpa script report.
- Target startup normal setelah setup/seed: satu perintah `docker compose up -d --build`. Startup/restart tidak mereset data/ledger atau memanggil model/target otomatis; evaluator terpisah. M1 memulai Compose app saja, bukan worker/lab dummy. Preflight awal 4 November gagal menjangkau daemon; pemeriksaan M1 berikutnya berhasil melalui context desktop-linux, termasuk build/health/restart/stop-start app. M2 kemudian menambahkan worker/lab nyata dan probe HTTP/isolasi/crash; M4a kemudian menambah pratinjau notifikasi/browser, dan M4b menghubungkan validasi XSS-08 ke workflow/UI.
- Waktu sekitar 3 jam/hari selama 10 hari kerja, sekitar 30 jam total.
- Budget total API maksimal **Rp50.000**; key belum tersedia.
- Model awal `qwen/qwen3-coder` melalui OpenRouter. Akses live belum aktif.
- Rencana provider diperluas 4 November 2026: Gemini direct (kandidat gemini-3.5-flash-lite Free Tier) sebagai cadangan prioritas; OpenAI Platform API dan xAI/Grok opsional, bukan diasumsikan gratis. Plus/Codex tidak otomatis memberi kredit Platform API; jalur Sign in with ChatGPT masih opsi lanjutan yang belum terintegrasi. Kontrak fallback di prd.md/architecture.md: sebelum respons sukses pertama, cap bersama, tidak untuk refusal, dan mati selama benchmark. Quota/kredit habis hanya dialihkan ke cadangan FREE_TIER yang terverifikasi dan dipilih operator, tanpa eskalasi otomatis ke paid.
- Pengguna mengonfirmasi sudah berusia 18 tahun atau lebih pada audit 3 November 2026; syarat usia OpenRouter yang diperiksa terpenuhi. Key dan kelayakan biaya akses belum terpenuhi.
- Pada 4 November 2026 pengguna menyatakan mahasiswa aktif dengan email kampus. Azure for Students/Foundry ditambahkan sebagai kandidat kredit, belum aktivasi/balance/quota/model yang terverifikasi; panduan di docs/azure-students.md. Jangan menganggap hibah sudah diterima atau melakukan upgrade PAYG/pemindahan lab ke cloud.
- Kapabilitas sasaran BAC/IDOR, XSS, file upload dan business logic. DoS/race dan script execution umum ditunda.
- Riwayat keputusan 4 November 2026: dataset dikurangi menjadi 20 teks 10/10 dengan alokasi awal 8/8/2/2. Pada 7 November, alokasi submission functional-v2 menjadi 8 BAC/8 XSS/4 upload pada subtype produk tersedia; 24 titik tetap target backlog. Draf asisten bukan label final otomatis; GT pengguna wajib sebelum benchmark.
- Riwayat M6c defensif, 6 November 2026: **M6 sebagian**, bagian defensif M6a/b selesai pada source; 145 tes terarah, konteks aturan terikat versi pada mock NONE dan persistensi dua container/volume khusus beserta cleanup lulus. Hasil di `docs/m6b-verification.md`. Service Compose aktif tetap M5. BUSINESS_LOGIC LAB/tools/verifier/UI belum tersedia; context builder menolak LAB/live/replay. Katalog `evaluator/catalog.json` berisi 24 ID/status; gate offline exit 2 karena 13 reproduksi historis/11 PLANNED dan konflik grup UP-04 dengan XSS-01..04. Jangan mengubah status/grup atau manifest M5 hanya untuk meluluskan checkpoint. M6 belum selesai. Tambahan auditor rekaman business logic offline lulus 25 tes terpisah dan dua artefak M6b CONSISTENT, tanpa eksekusi target baru. Hasilnya hanya konsistensi rekaman, vulnerability_verdict/ground_truth null; belum validator produk atau bukti keaslian/izin aktor. Artefak di `artifacts/m6c/`, batas di bagian tambahan `docs/m6b-verification.md`.
- Lab diminta mempunyai lebih dari 20 titik kerentanan nyata; rancangan 24 titik dan pemetaan fitur ada di `docs/lab-vulnerabilities.md`. BAC-08, XSS-01..08 dan UP-01..04 memiliki bukti operator, total 13 titik; 11 mekanisme kerentanan BAC/business logic belum diimplementasikan/diverifikasi. Daftar tidak diberikan ke runtime agent; GT dataset manusia tetap pending. UP-01/02 satu grup konten aktif; development UP-04 berbagi `html-element-output` dengan XSS-01..05 sehingga split harus direvisi/ditinjau sebelum freeze. XSS-07/08 satu grup DOM; ID berbeda tidak diklaim grup independen.
- Laptop RAM 16 GB; satu job/worker aktif. VPS bukan prasyarat.
- Jalur submission: Link Karya berupa repo GitHub publik dengan paket/rilis dan panduan menjalankan lokal. Repo publik tersedia di https://github.com/syahh-coder/kartikaHackathon_ValVulnAI; pada 4 November 2026 pengguna mengotorisasi push awal dokumentasi dan UI. Paket/release aplikasi belum dibuat. Tidak membuat live web, GitHub Pages, tunnel laptop atau VPS untuk submission. Video YouTube, slide publik, thumbnail dan screenshot tetap field terpisah.
- Repo skill eksternal belum ditentukan; jangan menganggap skill pentest sudah diinstal.
- Riwayat 6 November 2026: M6d parser dan M6e rekaman event kontrol normal selesai defensif lokal. **97 tes terarah lulus dalam 33,47 detik**, termasuk 33 parser dan 32 trace baru; dua artefak M6b tetap CONSISTENT. Runner ASGI baru memakai database sementara dan dua lifecycle host, bukan restart proses/container/TCP; empat event, stok 93 dan satu fulfillment tetap sama. Audit owner/staff-unit/approval/state hanya konsistensi metadata rekaman, bukan attestation izin atau verdict kerentanan/GT. Hasil di `docs/m6d-verification.md`, `docs/m6e-verification.md`, artefak privat `artifacts/m6e/`. Hambatan eksekusi turn sebelumnya teratasi lewat jalur berizin. M6 tetap sebagian, 13/24 dan gate katalog exit 2; worker/assessment/UI BUSINESS_LOGIC belum tersedia, katalog/grouping/manifest M5 serta service Compose tidak diubah.

- Status terkini 6 November 2026: review rekaman bisnis dan **workflow langkah admin/konteks terstruktur** tersedia di produk. 172 tes terarah lulus dalam 68,82 detik (20 workflow baru), QA Chromium 1366/390 px termasuk dialog/ekspor konteks lulus. Endpoint GET workflow khusus admin memeriksa ulang file, hasil/provenance dan binding, memakai klaim/aturan asal, menandai versi current dan menghasilkan phase/next actions administratif tetap. Klaim tidak berotoritas instruksi, catatan review tidak masuk konteks; target_execution_allowed/model_dispatch_allowed false, verdict/GT null. Bukan agentic live atau tools BUSINESS_LOGIC LAB. App Compose saja diperbarui setelah nol job aktif; seluruh agregat data/ledger dan 37 riwayat run sama, ID worker/lab tetap, workflow/JS container cocok host. Tidak ada migrasi baru pada update workflow, schema app tetap 004. Katalog 13/24 dan grouping belum siap; target/status/alokasi/manifest tidak diubah. Panduan/bukti di `docs/business-record-review.md`, artefak tambahan `artifacts/business-workflow/`; QA memakai app/database disposable dan folder gagal dipertahankan.

## Baca sesuai pekerjaan

Riwayat review 6 November 2026: review/gate grouping **M6f selesai lokal**, 21 tes lulus dalam 0,39 detik; M6 keseluruhan tetap sebagian. `evaluator/development_history.py` mencatat development sistem BAC-08/XSS-08/UP-04, bukan paparan model live. Gate `catalog_audit` menolak konflik historis/perubahan grup development meskipun alokasi dipindah, memeriksa kuota kategori, dan menampilkan inventaris kandidat tanpa mengubah katalog. Hanya XSS-06 kandidat XSS tercatat di luar grup development; target empat area belum terpenuhi. Keputusan belum freeze, tetap 13/24 dan gate exit 2. Tidak mengubah status/grup/alokasi katalog, manifest M5, target 20 laporan/24 titik, runtime atau provider. Hasil di `docs/m6f-verification.md`; artefak privat `artifacts/m6f/`. Revisi mekanisme perlu review bukti dan riwayat grup lama tetap disimpan.

- `plan.md`: tujuan, scope, anggaran, dan milestone.
- `docs/submission-scope.md`: cakupan submission aktif 7 November, jalur R1-R4 dan pemisahan M6 backlog dari eksperimen fungsional.
- `prd.md`: kebutuhan produk, keputusan tech stack, tiga container, database/volume dan kriteria penerimaan MVP.
- `docs/azure-students.md`: tutorial apply Azure for Students, cek Foundry dan batas kredit/model; akun/deployment belum diaktifkan asisten.
- `docs/architecture.md`: schema, state, tools, policy, dan kontrak komponen.
- `docs/runtime.md`: topologi container, handoff worker, antrean/recovery, penyimpanan, kuota dan ledger biaya; hasil app M1 dan HTTP/handoff/isolasi M2 sudah diuji; bagian browser/provider live masih rancangan.
- `docs/documentation-audit.md`: temuan audit dokumentasi, perubahan dan dependensi yang masih terbuka.
- `docs/execution-prompt.md`: prompt aktif batch R1; prompt M1/handoff lama berada di `docs/execution-prompt-history.md` dan bukan perintah mengulang implementasi.
- `docs/security-review.md`: temuan desain, matriks izin dan acceptance criteria keamanan; belum merupakan hasil pengujian runtime.
- `docs/design.md`: tampilan, susunan layar dan label; gaya visual masih asumsi awal yang dapat ditinjau.
- `docs/design-references.md`: pembacaan 11 referensi, pilihan panduan dan provenance; tidak berarti plugin eksternal sudah diinstal.
- `docs/ui-review.md`: hasil QA prototipe dan status review pengguna; bukan verifikasi autentikasi/keamanan backend.
- `ui-prototype/README.md`: cara membuka prototipe, batas simulasi dan perilaku penyimpanan lokal.
- `docs/user-flow.md`: urutan pengguna/sistem dan kondisi gagal.
- `docs/implementation.md`: milestone M1-M10, dependensi, checkpoint dan format kemajuan per batch. Selesaikan/verifikasi satu potongan sebelum melanjutkan, bukan seluruh aplikasi dalam satu batch.
- `docs/lab-spec.md`: aktor, aturan bisnis, kondisi target dan GT manual.
- `docs/lab-vulnerabilities.md`: daftar 24 titik, fitur, kontrol dan mapping evaluator; jangan dimasukkan ke konteks model validator.
- `docs/evaluation.md`: protokol functional-v2 aktif, GT, prediksi A dokumen/B dokumen+bukti dan metrik. `docs/evaluation-v1.md` mengarsipkan protokol ketat lama; gate katalog lama tidak menjadi gate v2.
- `README.md`: kondisi aktual dan perintah menjalankan yang sudah diverifikasi.
- `docs/registration.md`: draf formulir tanpa data pribadi.
- `docs/rules-alignment.md` dan `docs/submission-checklist.md`: ketentuan PDF, sumber/page, perbedaan aturan, dan kelengkapan submission.
- `docs/third-party.md`: komponen, sumber, versi, lisensi, atribusi, dan deklarasi pre-existing.
- `docs/distribution.md`: keputusan GitHub tanpa live web, URL repo dan otorisasi push awal, paket lokal, akses model juri dan pemeriksaan rilis. Push awal bukan rilis aplikasi atau izin deployment.

Jika keputusan kontrak berubah, perbarui dokumen pemiliknya dan ringkas dampaknya di rencana. Hindari menyalin seluruh spesifikasi ke setiap file.

## Urutan implementasi

1. Schema, profil target, policy, storage, dan adapter mock.
2. Lab BAC dengan dua akun, kondisi rentan/perbaikan serta reset evaluator.
3. Alur report -> scope -> worker -> evidence -> assessment.
4. XSS, file upload dan business logic setelah alur pertama berfungsi.
5. Model live saat akses/budget siap, lalu evaluasi dan submission.

Ikuti checkpoint di `docs/implementation.md`. Checkpoint merupakan pemeriksaan teknis, bukan permintaan konfirmasi baru untuk setiap file ketika pekerjaan sudah diotorisasi. Pertahankan status tahap yang benar dan jangan menganggap mock lulus tahap model live.

Jangan memulai framework multi-agent, fine-tuning, vector database, orkestrasi cloud, atau UI besar tanpa kebutuhan baru dari pengguna. Pekerjaan tidak didelegasikan ke sub-agent kecuali diizinkan instruksi yang berlaku.

## Aturan kode dan kontrak

- Gunakan Python 3.11 sebagai baseline awal, type hints, schema Pydantic dan fungsi yang mudah diuji.
- Pisahkan API/UI, workflow, provider, policy, tools worker, storage, lab dan evaluator.
- Gunakan operasi async ketika menunggu jaringan/browser; jangan memblok event loop untuk polling panjang.
- Validasi setiap argumen tool sebelum tindakan; scope tidak hanya dicek saat intake.
- Setiap observasi memiliki run/action/evidence ID dan provenance yang dibuat aplikasi.
- Bedakan status proses, scope, capability dan verdict teknis.
- `CONFIRMED` harus didukung dampak; timeout/refusal/gagal reproduksi tidak otomatis menjadi `REFUTED`.
- Multi-claim report tidak diberi verdict keseluruhan dari satu klaim tanpa penjelasan.
- Batasi retry, token, waktu, request/browser action, ukuran data, serta resource.

## Lab dan pemisahan data

- Gunakan target terdaftar, akun uji dan data sintetis.
- Sediakan tools HTTP/browser terstruktur; jangan menjalankan raw script kiriman report, terminal umum, `eval`, atau instalasi dari instruksi report.
- Worker tidak mendapat API key model, GT, source jawaban, reset evaluator, Docker socket, atau akses jaringan di luar profil.
- Kredensial diselesaikan lewat alias dan direduksi dari log/ekspor.
- Periksa redirect, subresource dan navigasi browser terhadap policy.
- Render report/response HTML sebagai konten yang di-escape pada dashboard.
- Perubahan mode dan seed target dilakukan evaluator, dengan label disembunyikan dari agent.

## Model dan pengeluaran

- Mulai dengan adapter mock yang berlabel jelas. Hasil mock/replay bukan hasil model live.
- Jangan melakukan pemanggilan berbayar, membeli kredit, atau menaikkan budget hanya untuk membuat pemeriksaan lolos.
- Begitu pengguna menyediakan konfigurasi live dalam batas budget, kerjakan integrasi yang sudah diotorisasi tanpa meminta konfirmasi berulang untuk tiap pemanggilan biasa.
- Baca secret hanya untuk konfigurasi yang dibutuhkan; jangan menampilkan key atau memasukkannya ke source/dokumen.
- Bedakan minimum pembelian provider dari biaya token. Periksa checkout aktual terhadap Rp50.000.
- Jangan menganggap endpoint gratis tertentu tersedia; periksa dukungan tools dan limit sebelum digunakan.
- Kunci dan catat model, provider, prompt serta konfigurasi selama benchmark.
- Live mode yang tidak memiliki key harus menampilkan error konfigurasi, bukan diam-diam memakai mock.

## Pemeriksaan yang relevan

- Perubahan dokumentasi: periksa konsistensi keputusan, link lokal, fence Markdown dan klaim status. Tidak memerlukan tes aplikasi yang belum tersedia.
- Policy/tool: uji kasus batas akses, redirect, session isolation dan penghentian run.
- Evidence/verdict: uji bukti dampak dan kontrol negatif yang relevan dengan perubahan.
- Evaluasi: uji perhitungan manual kecil, abstention, denominator nol dan grouping.
- Model adapter: gunakan respons simulasi untuk schema/error; live smoke test hanya jika key dan budget siap.
- Tema/rubrik mencakup AI. Sebelum mengklaim purwarupa agen AI berfungsi, tunjukkan integrasi model nyata; mock hanya membuktikan plumbing. Lisensi dan atribusi pihak ketiga dicatat, serta bahan pre-existing dideklarasikan.
- Jalankan pemeriksaan yang sesuai perubahan; jangan menambah pengulangan yang menghabiskan budget tanpa alasan.
- Jangan menyatakan aplikasi/container/benchmark berfungsi jika belum dijalankan. Catat kondisi yang gagal diverifikasi dan hasil aktual.

## Dokumentasi dan hasil

- Perbarui README ketika perintah instalasi/run benar-benar tersedia dan telah diperiksa.
- Pertahankan pemisahan development/held-out berdasarkan akar masalah, termasuk parafrasa dan kondisi perbaikan.
- Simpan hasil mentah agent sebelum koreksi analis; jangan memoles metrik dengan menghapus kegagalan.
- Tidak membuat klaim seluruh kerentanan, sepenuhnya offline, akurasi industri, penghematan waktu atau adopsi TNI AD tanpa bukti.
- Submission harus menyertakan thumbnail, maksimal lima screenshot, video YouTube maksimal 10 menit, slide, link karya yang dapat dicoba, serta dokumentasi teknis; deadline 15 November 2026 pukul 23:59 WIB. Gunakan checklist sumber dan jangan menganggap daftar awal tiga artefak sudah lengkap.
- Saat melapor, ringkas perubahan, pemeriksaan yang dilakukan, keterbatasan, dan langkah konkret berikutnya.
