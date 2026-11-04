# ValVuln AI: Agen Validasi Laporan Kerentanan

Purwarupa untuk Kartika Cyber Hackathon 2026 oleh tim solo **ukas and codex vs everbody**.

ValVuln AI adalah nama kerja untuk draf formulir. Rekomendasi kategori setelah membaca rulebook: **Penindakan**, karena fungsi utamanya adalah pengujian aktif/reproduksi klaim kerentanan. Pada 3 November 2026 pengguna menyatakan pendaftaran program diterima; asisten tidak mengirim formulir atau memverifikasi platform langsung. Pada 4 November 2026 pengguna menerima UI saat ini sebagai **baseline fix untuk mulai backend**, dengan perbaikan UI yang masih boleh menyusul. Handoff siap untuk M1 di chat baru; backend belum dimulai dan persetujuan UI bukan kelulusan keamanan runtime.

Tujuan: memeriksa scope laporan, mereproduksi klaim terhadap portal pengadaan/logistik lab, dan menyajikan bukti yang dapat ditinjau analis.

## Status saat ini

Repositori berisi dokumentasi dan [prototipe UI lokal](ui-prototype/README.md). Buka [halaman prototipe](ui-prototype/dist/index.html) untuk review; seluruh data/hasil adalah simulasi. Source backend FastAPI, autentikasi server, container target, dataset berlabel, prompt runtime dan benchmark belum dibuat. Tidak ada perintah menjalankan backend yang dinyatakan tersedia.

Repo GitHub: [syahh-coder/kartikaHackathon_ValVulnAI](https://github.com/syahh-coder/kartikaHackathon_ValVulnAI). Pada 4 November 2026 pengguna mengotorisasi push awal dokumentasi dan UI; versi ini belum merupakan paket aplikasi atau release submission.

Pemeriksaan lingkungan membaca Python 3.11.9, Docker CLI 29.7.2, serta Git 2.55.0.windows.2. Chromium/playwright-core yang sudah tersedia dipakai untuk QA UI; ini bukan pemasangan atau verifikasi browser worker produk. Docker daemon dan dependensi backend belum terverifikasi. Docker CLI menampilkan peringatan akses konfigurasi pengguna.

Preflight 4 November 2026 kembali membaca Python 3.11.9, Docker CLI 29.7.2, Compose v5.3.1 dan Git 2.55.0.windows.2. Koneksi ke named pipe docker_engine gagal karena pipe tidak ditemukan; daemon belum terjangkau dari sesi ini. Peringatan akses `.docker/config.json` masih muncul. Ini bukan bukti Docker rusak; periksa Docker Desktop/engine/context saat mulai eksekusi. Belum ada source/Compose untuk diuji.

Target paket nanti: setelah setup konfigurasi/seed, menjalankan aplikasi normal cukup `docker compose up -d --build`. Perintah tersebut **belum tersedia/terverifikasi pada repo sekarang**. Reset lab dan evaluator/scoring terpisah; detail kontrak ada pada runtime.md.

## Batas yang sudah dikonfirmasi

| Bagian | Pilihan |
| --- | --- |
| Pengembang | Solo, sekitar 3 jam/hari selama 10 hari kerja |
| Stack | Python + FastAPI |
| Target | Portal pengadaan/logistik buatan sendiri, data sintetis |
| UI/platform | Chat dan upload TXT/MD; satu program; role bug hunter/admin dari server |
| Scope | Guideline admin terversi; gate backend sebelum worker mengakses Docker internal |
| Kapabilitas sasaran | BAC/IDOR, XSS, file upload, business logic |
| Model awal | Qwen3-Coder melalui OpenRouter |
| Provider cadangan rencana | Gemini direct Free Tier; OpenAI Platform API dan xAI/Grok opsional, akses/billing belum siap |
| Budget total API | Maksimal Rp50.000; key belum tersedia |
| Pengembangan awal | Adapter mock yang diberi label jelas |
| Dataset evaluasi utama | 20 laporan berbeda, 10 valid dan 10 tidak valid setelah verifikasi manual |
| Target kerentanan lab | 24 titik yang dipetakan per fitur; semua masih spesifikasi |
| Pembuat laporan | Asisten menyusun 20 draf setelah lab siap; GT diverifikasi pengguna |

Model utama diakses lewat API dan tidak dijalankan di laptop. Koneksi API eksternal berarti aplikasi belum sepenuhnya offline. Setiap hasil mock akan diberi label dan tidak dihitung sebagai benchmark model live.

## Dokumen pengembangan

- [Rencana dan milestone](plan.md)
- [PRD, tech stack, container dan database](prd.md)
- [Daftar Azure for Students dan cek akses Foundry](docs/azure-students.md)
- [Aturan kerja asisten coding](AGENTS.md)
- [Arsitektur dan kontrak komponen](docs/architecture.md)
- [Runtime, antrean, penyimpanan dan batas resource](docs/runtime.md)
- [Hasil audit dokumentasi dan dependensi terbuka](docs/documentation-audit.md)
- [Prompt handoff dan eksekusi M1 di chat baru](docs/execution-prompt.md)
- [Review keamanan dan pengujian yang belum dijalankan](docs/security-review.md)
- [Desain UI dan label hasil](docs/design.md)
- [Pemilihan 11 referensi desain](docs/design-references.md)
- [Review UI, pemeriksaan browser dan status persetujuan](docs/ui-review.md)
- [Prototipe UI lokal dan cara membuka](ui-prototype/README.md)
- [Alur pengguna dan kondisi gagal](docs/user-flow.md)
- [Implementasi bertahap dan checkpoint](docs/implementation.md)
- [Spesifikasi portal lab](docs/lab-spec.md)
- [Peta 24 titik kerentanan dan fitur](docs/lab-vulnerabilities.md)
- [Dataset, ground truth, dan evaluasi](docs/evaluation.md)
- [Draf isian pendaftaran](docs/registration.md)
- [Penyelarasan rulebook dan S&K](docs/rules-alignment.md)
- [Checklist submission](docs/submission-checklist.md)
- [Rencana distribusi GitHub tanpa live web](docs/distribution.md)
- [Deklarasi komponen dan atribusi](docs/third-party.md)
- [Sumber PDF dan provenance](docs/sources/README.md)

`AGENTS.md` mengatur pekerjaan pada repositori. Instruksi agent dalam produk akan disimpan terpisah saat implementasi.

## Alur produk yang dituju

1. Bug hunter/admin login, memilih satu program dan chat/unggah report TXT/MD.
2. Guideline aktif ditetapkan admin terpisah dari report; backend memeriksa scope, izin dan prasyarat. OOS/UNKNOWN tanpa akses target.
3. Setelah lolos, agent merencanakan HTTP/browser dan kontrol pada portal Docker internal yang sudah berjalan.
4. Worker menjalankan tindakan yang lolos policy per aksi; tidak membuat container target baru per report.
5. Verifier memeriksa dampak/kontrol untuk `CONFIRMED`, `REFUTED`, atau `INCONCLUSIVE`.
6. Admin meninjau bukti internal dan membagikan hasil tersanitasi. Bug hunter hanya melihat laporan sendiri; ekspor mengikuti izin yang sama.

Keberhasilan menjalankan PoC tidak otomatis membuktikan dampak. Kegagalan reproduksi atau penolakan model juga tidak otomatis membuat report tidak valid.

## Budget dan akses model

Biaya token yang rendah berbeda dari minimum pembelian kredit. [Terms OpenRouter](https://openrouter.ai/terms), diperiksa 3 November 2026, mencantumkan minimum pembelian USD 5 per transaksi. Biaya rupiah checkout dan fee aktual perlu diperiksa terhadap batas Rp50.000 sebelum mengaktifkan pemakaian berbayar.

Terms tersebut juga mensyaratkan usia minimal 18 tahun; pengguna sudah mengonfirmasi 18+ pada 3 November 2026. Ini menyelesaikan syarat usia, bukan kesiapan key atau budget. Target A/B adalah 40 run untuk 20 laporan, dengan kemungkinan banyak panggilan model per run B; perhitungan biaya mengikuti [rancangan evaluasi](docs/evaluation.md).

Tier gratis tidak menjamin model pilihan tersedia atau kuotanya cukup. Pengembangan mock tetap dapat dilanjutkan tanpa key; benchmark model live menunggu akses yang benar-benar tersedia. Tidak ada pembelian atau pemanggilan model berbayar yang dilakukan pada tahap dokumentasi.

Rencana provider diperluas pada 4 November 2026 di [PRD](prd.md): Gemini direct menjadi kandidat cadangan gratis; OpenAI Platform API dan xAI/Grok tetap opsional dengan billing yang diperiksa sendiri. Plus/Codex tidak otomatis memberi kredit Platform API. Sign in with ChatGPT merupakan jalur resmi lain untuk plan pengguna yang eligible dan memerlukan integrasi/consent tersendiri; belum tersedia pada produk. Status akses bersumber pada dokumentasi primer yang ditautkan PRD, bukan pemeriksaan akun privat.

Fallback dicatat dan hanya boleh sebelum respons sukses pertama/aksi target; setelah itu provider terkunci. Quota/kredit habis hanya dialihkan ke profil gratis terverifikasi yang sudah dikonfigurasi, tanpa otomatis berbayar. Benchmark mematikan fallback agar hasil model/provider tidak tercampur. Jumlah container tetap tiga.

## Urutan implementasi

Mulai dari kontrak data dan satu alur BAC lengkap: target lab, dua akun, kondisi rentan/perbaikan, worker HTTP, kontrol, evidence, serta hasil yang dapat diperiksa. Integrasi model live menyusul setelah alur tools berfungsi dan akses API siap.

Saat source aplikasi sudah tersedia, README ini diperbarui dengan instalasi, variabel konfigurasi tanpa secret, cara seed/reset, perintah menjalankan, pemeriksaan yang relevan, dan demo dari kondisi bersih. Perintah yang belum diimplementasikan tidak disajikan sebagai perintah yang sudah bekerja.

## Hasil evaluasi

Belum tersedia. Akurasi, precision, recall, coverage, biaya, dan penghematan waktu akan diisi dari eksperimen aktual sesuai [prosedur evaluasi](docs/evaluation.md).

## Kelengkapan lomba

Keputusan submission: **Link Karya berupa repo GitHub publik**, berisi source/paket versi rilis, petunjuk menjalankan lokal dan tautan video/slide. Tidak membuat live web, GitHub Pages atau VPS untuk jalur ini. Repo publik sudah tersedia pada URL di atas; push awal diotorisasi untuk dokumentasi dan UI. Release aplikasi belum dibuat. Video YouTube, slide publik, thumbnail serta screenshot tetap diisi terpisah pada platform.

Deadline dari kedua PDF adalah **15 November 2026 pukul 23:59 WIB**. Paket submission menyiapkan link karya yang dapat dicoba, thumbnail 1200 x 630 px maksimal 500 KB, screenshot maksimal lima, video YouTube maksimal 10 menit, slide, serta dokumentasi teknis. AI merupakan bagian tema/rubrik; kemampuan model perlu ditunjukkan secara nyata, sementara mock selalu diberi label. Daftar lengkap dan perbedaan dokumen ada pada checklist di atas.
