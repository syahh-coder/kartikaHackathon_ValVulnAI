# Rencana distribusi karya melalui GitHub

Status: keputusan kanal pada 3 November 2026, diperbarui 4 November 2026. **Link Karya menggunakan repository GitHub publik; tidak membuat live web, GitHub Pages, atau menyewa VPS untuk submission ini.** Repo publik tersedia di [syahh-coder/kartikaHackathon_ValVulnAI](https://github.com/syahh-coder/kartikaHackathon_ValVulnAI). Pengguna mengotorisasi push awal dokumentasi dan prototipe UI pada 4 November. Paket/release aplikasi dan kelengkapan submission belum dibuat; push awal ini tidak memulai backend.

## 1. Jalur penilaian yang dipilih

Formulir yang ditempel pengguna menerima link download/repository atau bentuk akses lain yang memungkinkan juri mencoba dan mengevaluasi karya. Karena itu, pilihan tim adalah repo publik dengan paket yang dapat dijalankan secara lokal. Ini penerapan opsi pada formulir, bukan konfirmasi tambahan dari panitia atau jaminan kelulusan.

Urutan bagi juri:

1. Buka halaman utama repo tanpa meminta akses.
2. Baca ringkasan manfaat, fitur yang benar-benar tersedia dan keterbatasannya.
3. Buka video demo serta slide dari tautan yang terlihat di awal README.
4. Unduh release atau clone source pada versi submission yang ditandai.
5. Ikuti setup yang sudah diuji dari kondisi bersih, buka aplikasi pada loopback laptop dan coba report contoh.
6. Lihat mode, bukti, hasil mentah dan dokumentasi sesuai kebutuhan penilaian.

Repo menjadi pintu masuk. Source yang belum dapat dijalankan tidak dianggap memenuhi target kesiapan ini. Jika juri tidak dapat memasang Docker, video dan screenshot membantu penilaian; keduanya tidak diklaim menggantikan pengalaman menjalankan aplikasi.

## 2. Pemetaan field formulir

| Field | Artefak rencana | Status saat ini |
| --- | --- | --- |
| Link Karya / Project | URL utama repo GitHub publik, dengan tautan release dan quick start | [URL repo ditetapkan](https://github.com/syahh-coder/kartikaHackathon_ValVulnAI); push awal dokumentasi/UI diotorisasi; release dan quick start aplikasi belum tersedia |
| Video demo YouTube | Video yang dapat diakses publik, maksimal 10 menit | Belum dibuat/diunggah |
| Slide penjelasan | Slide publik, ditautkan juga dari README; PDF dapat dilampirkan pada release | Belum dibuat/diunggah |
| Thumbnail | Upload JPG/PNG/WebP 1200 x 630 px, maksimal 500 KB | Belum dibuat |
| Screenshot | Upload maksimal lima gambar dari karya aktual | Preview UI awal tersedia; bukan screenshot final validasi nyata |

Memakai repo untuk field Link Karya tidak menghapus empat field lainnya. Video tetap di YouTube, slide tetap harus bisa diakses juri, dan file gambar diunggah sesuai field platform.

## 3. Isi README pada versi submission

Rencanakan susunan berikut; jangan mengganti status sekarang menjadi seolah fitur tersebut telah selesai:

- Nama karya, tim, masalah dan manfaat dalam paragraf singkat.
- Tautan yang jelas: video, slide, unduh release dan dokumentasi teknis.
- Screenshot karya aktual dan penjelasan singkat alur report -> scope -> worker -> evidence -> assessment.
- Status fitur: sudah diuji, belum tersedia, serta mock/replay/live.
- Prasyarat OS/arsitektur, Docker/Compose, browser jika diperlukan, RAM/disk dan kebutuhan jaringan berdasarkan verifikasi aktual.
- Quick start dari kondisi bersih: unduh/clone, konfigurasi tanpa secret, build/start, seed akun sintetis dan URL aplikasi lokal.
- Cara mencoba satu report contoh, hasil yang bisa diharapkan pada kondisi demo yang dipilih, cara reset evaluator, dan cara menghentikan layanan tanpa menghapus hasil secara tidak sengaja.
- Konfigurasi model/provider, ketersediaan mode tanpa key, biaya/keterbatasan serta pemecahan masalah.
- Arsitektur, metode evaluasi, hasil aktual, lisensi/atribusi dan deklarasi pre-existing.

Perintah produk baru boleh disebut bekerja setelah diuji. Perintah membuka prototipe statis yang saat ini tersedia tetap terpisah pada [ui-prototype/README.md](../ui-prototype/README.md); bukan quick start backend yang belum ada.

## 4. Paket lokal yang direncanakan

Tujuan kemudahan setup: satu konfigurasi Compose untuk komponen yang dibutuhkan aplikasi lokal, tanpa orkestrasi cloud. Schema, pemisahan worker, policy dan jaringan tetap dimiliki [architecture.md](architecture.md). Jangan membangun Compose pada tahap perencanaan ini.

Topologi, handoff volume dan batas worker dirinci di [runtime.md](runtime.md). Ini spesifikasi yang harus diuji saat implementasi, bukan klaim paket Compose sudah tersedia.

Target pengalaman setelah prasyarat/config/seed awal siap adalah satu perintah `docker compose up -d --build` untuk menjalankan aplikasi normal. App, worker dan lab tidak memerlukan server Python/npm host terpisah; evaluator/scoring masih alat operator host di luar startup normal. Target ini baru boleh disebut bekerja sesudah cold start/restart diuji pada paket nyata.

| Bagian paket | Kebutuhan |
| --- | --- |
| Source aplikasi dan lab | Versi submission dapat ditelusuri ke tag/commit yang sama |
| Konfigurasi | Contoh konfigurasi tanpa secret; nilai default demo diberi label |
| Akun/seed | Identitas sintetis platform terpisah dari akun target; instruksi login/reset tersedia |
| Report contoh | Probe development/demo yang tidak mencemari held-out; bukan seluruh 20 report final sebagai bahan tuning |
| Evidence contoh | Hasil autentik yang sudah direduksi bila tersedia; fixture/replay diberi asal dan mode |
| Dependensi/image | Versi yang dikunci; jelaskan unduhan awal dan apakah build butuh internet |
| Arsip release | ZIP paket versi tertentu dan checksum; bukan salinan cache, database runtime atau seluruh folder kerja |
| Dokumen | Quick start, penggunaan, troubleshooting, arsitektur, atribusi dan hasil evaluasi aktual |

Hanya UI/API lokal yang perlu diakses browser pengguna. Portal rentan serta kontrol evaluator tidak dipublikasikan ke internet. Manifest GT/peta jawaban dan source jawaban tidak menjadi mount/context runtime agent, termasuk ketika source disediakan untuk review juri. Source code publik tidak dianggap sebagai izin runtime untuk membaca jawaban.

Sediakan paket source yang bisa dibangun dahulu. Prebuilt image hanya bila membantu setup dan benar-benar diuji; jangan membuat registry tambahan sebagai syarat sebelum satu alur lokal berfungsi. Catat platform build, ukuran dan kebutuhan ruang disk dari hasil nyata.

## 5. Akses model untuk juri

Tidak memasukkan key milik tim ke repo, arsip, screenshot atau seed. Repo publik tidak berarti menyediakan kuota API publik bersama.

| Mode | Pengalaman juri | Batas klaim |
| --- | --- | --- |
| Mock pengembangan | Memeriksa plumbing jika adapter sudah dibuat | Bukan AI live atau bukti reproduksi |
| Replay trace autentik | Memeriksa jejak run tersimpan jika capture/replay sudah dibuat | Harus diberi label rekaman; tidak menguji ulang target/model |
| Live dengan key pengguna | Menjalankan validasi sebenarnya sesuai kemampuan yang tersedia | Memerlukan konfigurasi, endpoint dan budget sendiri; live tanpa key gagal dengan pesan jelas |

Ketiga mode adalah rancangan, bukan fitur yang sudah tersedia pada backend. Video submission harus menunjukkan integrasi model nyata setelah dibangun, dengan data sintetis dan bukti aktual. Mock/replay berguna untuk akses tanpa key tetapi tidak menggantikan bukti fungsi AI. Akses live tim tetap tunduk pada budget Rp50.000; pembaca repo tidak otomatis memperoleh atau menghabiskan budget tim.

Provider pilihan mengikuti prd.md: Gemini direct Free Tier dapat menjadi pilihan live lokal bila key/quota/tools pengguna tersedia. OpenAI Platform API dan Grok membutuhkan akses/kreditnya sendiri; tidak membagikan langganan Plus/Codex pengembang kepada juri. Integrasi resmi ChatGPT plan/OAuth merupakan opsi lanjutan yang belum dibangun. Paket hanya mendokumentasikan adapter/mode yang benar-benar tersedia dan diuji, bukan semua kandidat sebagai fitur selesai.

## 6. Pemeriksaan kesiapan rilis pada M10

- [ ] UI telah dinyatakan fix oleh pengguna dan milestone implementasi yang dibutuhkan benar-benar tersedia.
- [ ] Tag/commit submission, paket release serta dokumentasi menunjuk versi yang sama.
- [ ] Lisensi kode asli proyek dipilih pengguna; LICENSE dan notice/atribusi aktual disertakan. Belum ada lisensi proyek yang otomatis dipilih oleh audit ini.
- [ ] URL repo, file release, video dan slide dapat dibuka tanpa akses akun tim.
- [ ] Quick start dijalankan dari folder/lingkungan bersih tanpa path/cache laptop pengembang; hambatan yang masih ada dicatat.
- [ ] Skenario demo nyata berfungsi; kemampuan model live dibedakan dari mock/replay dan kebutuhan key jelas.
- [ ] Instruksi setup/seed/reset/stop telah dicoba; hanya layanan yang dimaksud dibuka pada loopback.
- [ ] Satu perintah startup menyalakan app/worker/lab nyata, readiness tepat, dan restart menjaga data/ledger tanpa reset atau model call otomatis.
- [ ] Tidak ada secret/credential aktif, database runtime atau artefak privat evaluator pada paket yang tidak semestinya.
- [ ] Thumbnail dan maksimal lima screenshot menunjukkan kondisi produk yang benar-benar ada.
- [ ] Seluruh field formulir terisi terpisah; URL Link Karya adalah repo publik yang telah diverifikasi.

Setup lokal memberi juri langkah tambahan dibanding aplikasi hosted. Kurangi hambatan melalui paket yang rapi, video yang jelas dan petunjuk singkat; jangan menjanjikan one-click atau sepenuhnya offline sebelum itu terbukti.

## 7. Urutan kerja dan batas otorisasi

1. Sekarang: push awal dokumentasi dan UI ke repo yang diberikan pengguna; tanpa deployment atau release aplikasi.
2. UI baseline sudah dinyatakan fix oleh pengguna pada 4 November 2026; perbaikan boleh menyusul, tanpa konfirmasi UI ulang untuk M1.
3. Mulai M1 lokal di chat baru sesuai [implementation.md](implementation.md) dan prompt handoff; kategori, model live/evaluasi serta rilis tetap mengikuti dependensi dan batas otorisasi masing-masing.
4. Pada M10, susun paket, video, slide serta gambar dari hasil aktual dan lakukan pemeriksaan rilis.
5. Setelah paket siap ditinjau, publikasi release dan pengisian platform mengikuti otorisasi pengguna. Otorisasi push awal tidak berarti paket submission sudah siap atau platform sudah diisi.

Cloud deployment, domain, tunnel laptop, GitHub Pages dan VPS tidak masuk jalur submission yang dipilih. Perubahan kebutuhan tersebut harus menjadi keputusan baru yang dicatat, bukan dependensi tersembunyi.
