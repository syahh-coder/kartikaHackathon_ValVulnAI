# Pelaksanaan bertahap dan checkpoint

Status sekarang: **UI diterima pengguna sebagai baseline fix untuk mulai backend pada 4 November 2026**, dengan kemungkinan perbaikan berikutnya. Pendaftaran dinyatakan diterima 3 November. Prototipe UI tetap simulasi; backend, portal, 24 titik lab dan 20 laporan belum dibuat. Gate UI sudah terpenuhi dan M1 siap dikerjakan di chat baru tanpa konfirmasi UI ulang. Dokumen ini memecah implementasi menjadi tahap yang dapat diperiksa; persetujuan UI tidak meluluskan M1-M10 atau mengotorisasi API live.

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
| M1 | 1 | Fondasi API, session/ownership, schema chat/program/scope, policy dan mock | Gate UI terpenuhi; eksekusi di chat baru sesuai prompt | Belum dimulai |
| M2 | 2 | Portal dan BAC development cadangan | M1 | Belum dimulai |
| M3 | 3 | BAC end-to-end dan UI minimum | M1-M2 | Belum dimulai |
| M4 | 4 | XSS dan bukti browser | M3 | Belum dimulai |
| M5 | 5 | File upload dan bukti dampak | M3-M4 | Belum dimulai |
| M6 | 6 | Business logic dan kelengkapan 24 titik | M3; validator lain sesuai kebutuhan | Belum dimulai |
| M7 | 7 | Draf 20 laporan, GT dan grouping | Fitur aktual dan bukti manual | Belum dimulai |
| M8 | 8 | Model live dan freeze | Akses API sesuai budget, development siap | Belum dimulai |
| M9 | 9 | Benchmark A/B dan analisis | M7-M8 | Belum dimulai |
| M10 | 10 | Dokumentasi hasil, visual dan submission | Fungsi/hasil aktual yang tersedia | Belum dimulai |

Model adapter live dapat dikerjakan lebih awal bila key/akses siap, menggunakan probe development. Freeze tetap menunggu M7, dan 20 laporan utama tidak dipakai untuk tuning. Key belum tersedia tidak menghalangi fondasi, lab dan worker dalam mode pengembangan yang berlabel.

## 4. Checkpoint per milestone

### M1 - Fondasi

- [ ] Buat struktur proyek, dependensi dan konfigurasi contoh tanpa secret.
- [ ] Ikuti `../prd.md`: pin dependensi app/worker/lab sesuai Python 3.11; SQLite aplikasi melalui aiosqlite, migrasi SQL terversi dan satu proses app/dispatcher. Instal browser worker baru pada tahap terkait.
- [ ] Siapkan Compose app dan image minimal, env.example tanpa secret, migrasi serta seed operator terpisah. Verifikasi startup/restart mempertahankan data dan tidak memanggil model/target. M1 tidak membuat worker/lab dummy; perintah tiga service baru lulus setelah komponen nyata tersedia.
- [ ] Mulai riwayat Git lokal untuk menelusuri kontribusi/versi; tidak berarti publikasi repo.
- [ ] Periksa jalur akses model, syarat akun dan minimum checkout terhadap Rp50.000 sejak awal; tanpa pembelian/panggilan berbayar pada pemeriksaan ini. Usia 18+ telah dikonfirmasi pengguna.
- [ ] Implementasikan schema membership/session, conversation/message/attachment, scope version dan report/run/action/evidence/assessment.
- [ ] Seed dua bug hunter serta satu admin demo; role bukan input client. Tes AUTH-01/02/03 dan DATA-01 yang relevan.
- [ ] Guideline draf/aktivasi dan binding operator; SCOPE-01/02 memblok OOS/UNKNOWN tanpa worker job.
- [ ] Reservasi job/budget dan idempotency diperiksa; LIMIT-01 awal tanpa API berbayar.
- [ ] Kunci kontrak antrean/error API, token/data quota dan ledger sesuai `runtime.md`; simulasikan expiry, crash dan biaya tidak diketahui.
- [ ] Tambahkan registry target dan policy tindakan yang bisa diperiksa.
- [ ] Storage memisahkan report dan run; run berulang tidak menimpa hasil sebelumnya.
- [ ] Adapter mock serta live yang belum terkonfigurasi memberi status yang jelas.
- [ ] Definisikan ProviderProfile/ProviderResult dan event per dispatch; simulasi gangguan sementara -> cadangan, quota habis -> gratis saja, cap bersama, refusal/config error tidak fallback, provider terkunci setelah respons pertama, dan benchmark tanpa routing otomatis. Ini simulasi kontrak, bukan uji provider live.
- [ ] Pemeriksaan schema, transisi yang relevan dan batas target dijalankan.

**Siap lanjut:** satu report dapat disimpan dan workflow mock dapat diproses dengan provenance yang jelas. Ini belum bukti reproduksi bug.

Potongan M1 berurutan: (a) bootstrap/config/storage dan Compose app; (b) session/membership/ownership serta scope/report snapshot; (c) state/queue/idempotency/ledger, mock/error contracts dan pemeriksaan batas yang relevan. Periksa setiap potongan sebelum lanjut, tanpa menganggap sub-batch pertama meluluskan seluruh M1. Waktu tiga jam merupakan target lama, bukan estimasi terukur untuk seluruh rincian ini.

### M2 - Lab BAC development

- [ ] Verifikasi Docker daemon atau catat hambatan sebenarnya.
- [ ] Buat target minimum, dua akun, objek uji dan aturan kepemilikan.
- [ ] Gunakan SQLite lab terpisah dari database platform; seed/reset oleh maintenance operator tanpa GT/API key atau route reset di runtime agent.
- [ ] Mulai dari BAC-08 development sesuai peta; bila diganti, perbarui peta sebelum freeze.
- [ ] Evaluator dapat seed/reset dan memeriksa kondisi target.
- [ ] Verifikasi manual satu celah serta kontrol negatif, simpan evidence sebenarnya.
- [ ] Worker menjangkau target yang diizinkan dan menolak tujuan lain.
- [ ] Verifikasi handoff inbox/outbox tanpa API key, SQLite, GT, Docker socket atau jaringan eksternal pada worker; target dirty memblok run berikutnya sampai reset evaluator.

**Siap lanjut:** target dapat direproduksi dan direset; jawaban evaluator tidak tersedia kepada worker.

### M3 - Alur vertikal BAC dan UI minimum

- [ ] Intake -> scope -> plan -> policy -> HTTP worker -> evidence -> assessment.
- [ ] Login, pilih satu program dan UI chat/upload TXT/MD menampilkan data backend aktual; Kirim berbeda dari Validasi snapshot.
- [ ] Ganti adapter fixture dengan API; hapus pemilih role/login/skenario simulasi dari UI produk. Polling, draft persistence dan status model mengikuti kontrak backend.
- [ ] Projection hunter/admin, publikasi bukti dan ekspor memenuhi AUTH/DATA; OOS/UNKNOWN dibuktikan nol request target.
- [ ] Perubahan versi/revoke/cancel menghentikan antrean serta I/O aktif; cek SCOPE-03, NET-01/03 dan LIMIT-01 sebelum akses user lain.
- [ ] Bukti mengikat akun, objek, request/response dan klaim.
- [ ] Kegagalan/timeout tidak menjadi refutation otomatis.
- [ ] Pembatalan menghentikan kerja lanjutan dan mempertahankan trace.
- [ ] Review/ekspor dasar menjaga hasil mentah serta redaksi secret.
- [ ] Bila key dan budget siap, lakukan probe model pada BAC development lebih awal; jika belum siap, catat hambatan dan jangan mengklaim agent live berfungsi.

**Siap lanjut:** satu alur pengguna berfungsi dari input hingga hasil yang dapat ditinjau. Periksa kondisi rentan dan kontrol yang relevan. Tambahkan polish UI setelah fungsi ini stabil.

### M4 - XSS

- [ ] Tambahkan browser worker dengan scope seluruh navigasi/subresource.
- [ ] Buat titik XSS development dan kontrol inert terlebih dahulu.
- [ ] Marker lokal unik membuktikan eksekusi pada origin yang diperiksa.
- [ ] Tangkap event/screenshot dan hubungkan ke tindakan.
- [ ] Lengkapi titik XSS rencana secara bertahap dengan pemeriksaan manual tiap titik.
- [ ] Pastikan UI tidak mengeksekusi report/artefak aktif; NET-02/03 dan DATA-02 dibuktikan pada browser/hasil aktual.

**Siap lanjut:** XSS dapat dibedakan dari pantulan teks pada subtype yang benar-benar diuji.

### M5 - File upload

- [ ] Gunakan fixture lab terdaftar dan batas ukuran.
- [ ] Uji dampak penyajian/penimpaan sesuai klaim, bukan hanya upload berhasil.
- [ ] Kontrol attachment/inert atau penyimpanan aman punya evidence.
- [ ] Petakan overlap XSS/BAC pada `root_cause_group`.
- [ ] Catat status implementasi/verifikasi tiap titik upload.

**Siap lanjut:** worker dan verifier membuktikan dampak file upload spesifik serta kontrolnya.

### M6 - Business logic dan katalog lab

- [ ] Aturan yang relevan tersedia pada context agent.
- [ ] Simpan state sebelum/sesudah dan kontrol alur normal.
- [ ] Pengujian berulang sekuensial tidak diklaim sebagai race condition.
- [ ] Lengkapi 8 BAC, 8 XSS, 4 upload dan 4 business logic yang direncanakan.
- [ ] Tiap titik diberi status aktual: direncanakan, diimplementasikan atau diverifikasi manual.
- [ ] Tinjau apakah development berbagi akar masalah dengan calon evaluasi dan perbaiki pembagiannya.

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

Belum ada batch backend/lab M1-M10 yang dapat dicatat. Batch prototipe UI dicatat terpisah di bawah. Langkah pertama ketika implementasi backend mulai diotorisasi adalah M1; tidak langsung membuat seluruh portal dan 20 laporan sekaligus.

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
