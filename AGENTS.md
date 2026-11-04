# Instruksi pengembangan repositori

Berlaku untuk pekerjaan di seluruh repositori ini. Ikuti instruksi pengguna dan instruksi tingkat lebih tinggi. Dokumen ini mengatur asisten coding; prompt agent produk dibuat terpisah saat implementasi.

## Konteks yang sudah dikonfirmasi

- Tim solo: **ukas and codex vs everbody**.
- Pada 3 November 2026 pengguna menyatakan pendaftaran program diterima. Pada 4 November 2026 pengguna menyatakan **UI fix sebagai baseline untuk mulai backend**, dengan kemungkinan perbaikan berikutnya. Gate UI sudah terpenuhi; jangan meminta persetujuan UI ulang untuk M1. Eksekusi M1 diminta dilakukan di chat baru sesuai docs/execution-prompt.md. Persetujuan UI tidak membuktikan backend/worker/model aman atau berfungsi, dan tidak mengotorisasi live API/cloud. Pengguna kemudian mengotorisasi push awal dokumentasi dan UI ke repo GitHub di bawah; ini tidak memulai M1 atau deployment.
- Nama kerja untuk draf pendaftaran: **ValVuln AI: Agen Validasi Laporan Kerentanan**. Rekomendasi kategori terbaru **Penindakan**, menggantikan usulan Core Infra sebelumnya setelah membaca rulebook. Jangan menyatakan formulir sudah dikirim.
- Python + FastAPI; target portal pengadaan/logistik milik sendiri. UI chat dengan login bug hunter/admin program, satu program MVP; role server-side, guideline draf/aktivasi oleh admin dan versi scope per run. Worker baru boleh mengakses portal Docker yang sudah berjalan setelah scope/prasyarat/izin lolos backend; tidak membuat target baru per report.
- Stack MVP dirangkum di `prd.md`: tiga container tetap (app, worker, lab), SQLite aplikasi dan lab terpisah, UI Jinja2/JavaScript disajikan app, Chromium di worker; evaluator CLI pada host. Belum ada Compose/dependensi backend yang dipasang atau diuji.
- Target startup normal setelah setup/seed: satu perintah `docker compose up -d --build`. Startup/restart tidak mereset data/ledger atau memanggil model/target otomatis; evaluator terpisah. M1 memulai Compose app saja, bukan worker/lab dummy. Preflight 4 November menemukan CLI/Compose tersedia tetapi daemon belum terjangkau; cek ulang saat eksekusi.
- Waktu sekitar 3 jam/hari selama 10 hari kerja, sekitar 30 jam total.
- Budget total API maksimal **Rp50.000**; key belum tersedia.
- Model awal `qwen/qwen3-coder` melalui OpenRouter. Akses live belum aktif.
- Rencana provider diperluas 4 November 2026: Gemini direct (kandidat gemini-3.5-flash-lite Free Tier) sebagai cadangan prioritas; OpenAI Platform API dan xAI/Grok opsional, bukan diasumsikan gratis. Plus/Codex tidak otomatis memberi kredit Platform API; jalur Sign in with ChatGPT masih opsi lanjutan yang belum terintegrasi. Kontrak fallback di prd.md/architecture.md: sebelum respons sukses pertama, cap bersama, tidak untuk refusal, dan mati selama benchmark. Quota/kredit habis hanya dialihkan ke cadangan FREE_TIER yang terverifikasi dan dipilih operator, tanpa eskalasi otomatis ke paid.
- Pengguna mengonfirmasi sudah berusia 18 tahun atau lebih pada audit 3 November 2026; syarat usia OpenRouter yang diperiksa terpenuhi. Key dan kelayakan biaya akses belum terpenuhi.
- Pada 4 November 2026 pengguna menyatakan mahasiswa aktif dengan email kampus. Azure for Students/Foundry ditambahkan sebagai kandidat kredit, belum aktivasi/balance/quota/model yang terverifikasi; panduan di docs/azure-students.md. Jangan menganggap hibah sudah diterima atau melakukan upgrade PAYG/pemindahan lab ke cloud.
- Kapabilitas sasaran BAC/IDOR, XSS, file upload dan business logic. DoS/race dan script execution umum ditunda.
- Keputusan 4 November 2026 mengurangi dataset utama dari 40 menjadi 20 teks laporan berbeda: 10 valid dan 10 tidak valid setelah GT manual. Pembagian awal 8 BAC, 8 XSS, 2 upload, 2 business logic; asisten menyusun draf setelah lab siap, bukan label final otomatis. Perubahan ini tidak mengurangi target 24 titik lab.
- Lab diminta mempunyai lebih dari 20 titik kerentanan nyata; rancangan 24 titik dan pemetaan fitur ada di `docs/lab-vulnerabilities.md`. Daftar belum diimplementasikan/diverifikasi dan tidak diberikan ke runtime agent.
- Laptop RAM 16 GB; satu job/worker aktif. VPS bukan prasyarat.
- Jalur submission: Link Karya berupa repo GitHub publik dengan paket/rilis dan panduan menjalankan lokal. Repo publik tersedia di https://github.com/syahh-coder/kartikaHackathon_ValVulnAI; pada 4 November 2026 pengguna mengotorisasi push awal dokumentasi dan UI. Paket/release aplikasi belum dibuat. Tidak membuat live web, GitHub Pages, tunnel laptop atau VPS untuk submission. Video YouTube, slide publik, thumbnail dan screenshot tetap field terpisah.
- Repo skill eksternal belum ditentukan; jangan menganggap skill pentest sudah diinstal.

## Baca sesuai pekerjaan

- `plan.md`: tujuan, scope, anggaran, dan milestone.
- `prd.md`: kebutuhan produk, keputusan tech stack, tiga container, database/volume dan kriteria penerimaan MVP.
- `docs/azure-students.md`: tutorial apply Azure for Students, cek Foundry dan batas kredit/model; akun/deployment belum diaktifkan asisten.
- `docs/architecture.md`: schema, state, tools, policy, dan kontrak komponen.
- `docs/runtime.md`: topologi container, handoff worker, antrean/recovery, penyimpanan, kuota dan ledger biaya; seluruhnya rancangan yang belum diuji runtime.
- `docs/documentation-audit.md`: temuan audit dokumentasi, perubahan dan dependensi yang masih terbuka.
- `docs/execution-prompt.md`: handoff chat baru dan prompt M1 setelah persetujuan baseline UI; bukan bukti kelulusan tahap atau backend sudah dimulai.
- `docs/security-review.md`: temuan desain, matriks izin dan acceptance criteria keamanan; belum merupakan hasil pengujian runtime.
- `docs/design.md`: tampilan, susunan layar dan label; gaya visual masih asumsi awal yang dapat ditinjau.
- `docs/design-references.md`: pembacaan 11 referensi, pilihan panduan dan provenance; tidak berarti plugin eksternal sudah diinstal.
- `docs/ui-review.md`: hasil QA prototipe dan status review pengguna; bukan verifikasi autentikasi/keamanan backend.
- `ui-prototype/README.md`: cara membuka prototipe, batas simulasi dan perilaku penyimpanan lokal.
- `docs/user-flow.md`: urutan pengguna/sistem dan kondisi gagal.
- `docs/implementation.md`: milestone M1-M10, dependensi, checkpoint dan format kemajuan per batch. Selesaikan/verifikasi satu potongan sebelum melanjutkan, bukan seluruh aplikasi dalam satu batch.
- `docs/lab-spec.md`: aktor, aturan bisnis, kondisi target dan GT manual.
- `docs/lab-vulnerabilities.md`: daftar 24 titik, fitur, kontrol dan mapping evaluator; jangan dimasukkan ke konteks model validator.
- `docs/evaluation.md`: dataset, split, baseline serta perhitungan metrik.
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
