# Audit dokumentasi sebelum backend

## Penyesuaian scope setelah M6 - 7 November 2026

Pengguna meminta solusi M6 lalu menyetujui rekomendasi penyempitan dan pembaruan dokumentasi/prompt. [Scope submission](submission-scope.md) kini memisahkan target 24 titik/M6 asli sebagai backlog dari R1 adapter/triage teks, R2 UI/ringkasan bukti, R3 functional-v2 dan R4 paket. BUSINESS_LOGIC LAB tetap unsupported dan hitungan historis tetap 13/24. Fitur review bisnis tidak dijadikan pengganti kelengkapan M6.

`evaluation.md` kini protokol fungsional 20 teks 10/10, alokasi 8/8/4 pada BAC-08/XSS-08/UP-04, A dokumen versus B dokumen+observasi. Model tidak memicu worker. Paparan mekanisme development diungkap; tidak mengklaim held-out akar masalah baru. Prediksi model dibanding GT, hasil verifier terpisah. Protokol lama disimpan di [evaluation-v1.md](evaluation-v1.md), handoff lama di [execution-prompt-history.md](execution-prompt-history.md). Gate katalog/riwayat grup/manifest lama dipertahankan, bukan dilonggarkan agar lulus.

`execution-prompt.md` diganti dengan satu batch R1 yang konkret, termasuk schema/error/redaksi/ownership/ledger dan nol aksi target. Root AGENTS/plan/PRD/README serta dokumen arsitektur/runtime/security/flow/desain/lab/distribusi/checklist mendapat penunjuk keputusan aktif. Ini perubahan rencana/dokumentasi saja: tidak mengubah source produk, data/Compose, status GT, konfigurasi model, pemanggilan API, commit/push atau deployment. Pemeriksaan format/link/konsistensi dilakukan setelah edit; hasilnya dilaporkan terpisah dari tes aplikasi historis.

Pemeriksaan dokumen 7 November lulus: 41 Markdown terbaca UTF-8, 320 link lokal tanpa target hilang dan tidak ada fence terbuka/karakter pengganti. Contoh alokasi 20/10/10 dan F1 16/19 diperiksa secara aritmetika. Hash sebelum/sesudah sama untuk katalog, riwayat development, source gate katalog dan Compose; status tetap 13 OPERATOR_REPRODUCED/11 PLANNED. `git diff --check` lulus dengan pengecualian spasi hard break Markdown yang disengaja. Tidak menjalankan tes aplikasi/target/model karena perubahan hanya dokumentasi; hasil tes historis tidak disebut pengujian ulang.

## Riwayat audit sebelum perubahan scope

**Pembaruan M4c, 5 November 2026:** M1-M4 selesai teknis lokal; 180 tes dan tujuh titik XSS tambahan/kontrol Chromium lulus. Total sembilan dari 24 titik direproduksi operator; 15 titik lain pending. [Hasil M4c](m4c-verification.md). Cakupan planner/UI tetap BAC/XSS-08 mock, data GT/model live/benchmark belum tersedia. Sumber status di README, plan/PRD, implementation, peta lab dan handoff diselaraskan; audit sebelum implementasi di bawah tetap riwayat.

Tanggal: **3 November 2026**. Lingkup: seluruh Markdown proyek, status prototipe, konsistensi arsitektur/evaluasi dan kesiapan rencana submission. Tidak membangun backend/lab, menghubungi target, membeli kredit atau menjalankan model live.

**Pembaruan setelah M2, 4 November 2026:** lab BAC-08, worker HTTP/handoff/isolasi dan crash setelah mutasi sudah direproduksi operator; lihat [hasil M2](m2-verification.md). Model live/benchmark/GT manusia belum tersedia. Catatan audit lama di bawah tetap riwayat.

**Pembaruan setelah eksekusi M1, 4 November 2026:** fondasi app lokal selesai dengan mock dan 86 tes, termasuk smoke Docker/persistensi. Lihat [hasil M1](m1-verification.md). Audit di bawah adalah riwayat sebelum implementasi.

**Status saat handoff 4 November 2026:** pengguna sudah menyatakan UI fix sebagai baseline untuk mulai backend, sambil membolehkan perbaikan berikutnya. Gate UI pada catatan audit lama di bawah sudah terselesaikan; prompt handoff M1 tidak perlu meminta persetujuan UI ulang. Backend tetap belum dimulai pada turn konfirmasi/dokumentasi ini.

**Catatan perubahan 4 November 2026:** angka 40 laporan/80 run pada catatan audit 3 November di bawah adalah snapshot lama. Target aktif telah dikurangi pengguna menjadi **20 laporan (10 valid/10 tidak valid), 40 run A/B**, dengan batas awal hingga 260 panggilan model sebelum development/chat. Target lab 24 titik belum diubah. Rancangan aktif mengikuti evaluation.md dan plan.md; catatan historis ini tidak menggantikannya.

Kesimpulan: struktur dokumentasi sudah mencakup kebutuhan untuk memulai M1 secara bertahap setelah gate UI/arahan mulai terpenuhi. Audit menemukan kontrak penting yang belum eksplisit dan memperbaikinya di dokumen pemilik. Ini bukan pernyataan keamanan runtime, kelulusan milestone, atau jaminan seluruh scope muat dalam 30 jam.

## Temuan dan perbaikan

| Temuan | Perbaikan | Dokumen pemilik |
| --- | --- | --- |
| Baseline tanpa tools berisiko dipaksa menghasilkan verdict yang mensyaratkan bukti eksekusi | A memakai DocumentPrediction, B memakai assessment terverifikasi; mapping scoring terpisah, output mentah/koreksi manusia tetap tersimpan | [evaluation.md](evaluation.md) |
| F1 melalui precision dapat menjadi N/A walaupun F1 semestinya nol | Rumus langsung TP/FP/FN, contoh abstention dan denominator nol | [evaluation.md](evaluation.md) |
| 40 laporan mudah disalahartikan sebagai 40 panggilan model | Satu A dan B per laporan berarti 80 run; batas awal hingga 520 panggilan sebelum development/chat, biaya diukur dan dibatasi ledger | [evaluation.md](evaluation.md), [plan.md](../plan.md) |
| Handoff app-worker, crash, acknowledgment mutasi dan target terkontaminasi belum rinci | Dua volume JSON sempit; app-only SQLite; lease/heartbeat; tanpa auto-replay mutasi; TARGET_DIRTY sampai reset evaluator | [runtime.md](runtime.md) |
| Batas data/token/disk, persistensi dan biaya tidak diketahui belum lengkap | Kuota awal, input terlalu besar ditolak, capture terpotong diberi status, draft server, reservasi COST_UNKNOWN dan reset data dipisah | [runtime.md](runtime.md) |
| Sambungan UI simulasi ke backend dan respons API belum dikunci | Adapter API, server-owned role/mode/model, penghapusan kontrol simulasi, polling/idempotency/error DTO | [architecture.md](architecture.md) |
| Contoh awal invoice bertentangan dengan BAC-08 sebagai development | BAC-08 menjadi potongan pertama dan demo development; contoh invoice tidak dipakai untuk tuning held-out | [lab-spec.md](lab-spec.md), [plan.md](../plan.md) |
| Status transaksi dan status QA browser belum sama antar dokumen | Empat state bisnis sesuai lab; QA browser prototipe dibedakan dari browser worker produk yang belum diuji | [plan.md](../plan.md) |
| Usia akses provider dan lisensi kode asli proyek belum tercatat | Pengguna mengonfirmasi 18+; lisensi proyek tetap keputusan sebelum rilis, tanpa otomatis memilih lisensi | [plan.md](../plan.md), [third-party.md](third-party.md) |

Kontrak di atas masih harus diimplementasikan dan diuji. Poin yang menyangkut keselamatan eksekusi ditautkan ke acceptance criteria RUN-01/STORE-01 serta pemeriksaan yang sudah ada di [security-review.md](security-review.md).

## Cakupan pembacaan

| Kelompok | Dokumen |
| --- | --- |
| Keputusan dan kondisi aktual | AGENTS.md, README.md, plan.md |
| Kontrak dan batas sistem | architecture.md, runtime.md, security-review.md |
| Tampilan dan perjalanan pengguna | design.md, user-flow.md, ui-review.md, design-references.md, ui-prototype/README.md |
| Target dan eksperimen | lab-spec.md, lab-vulnerabilities.md, evaluation.md |
| Pelaksanaan | implementation.md |
| Aturan dan submission | registration.md, rules-alignment.md, submission-checklist.md, distribution.md |
| Sumber dan hak penggunaan | third-party.md, sources/README.md |

Audit ini menambahkan runtime.md dan catatan audit ini; jumlah akhir **22 file Markdown proyek**. Dokumen desain/referensi yang tidak memerlukan perubahan tetap dipertahankan. Peta jawaban evaluator tidak menjadi konteks runtime model meskipun tersedia sebagai dokumentasi proyek.

## Dependensi yang masih terbuka

1. **UI dan awal backend:** prototipe tersedia, tetapi belum ada pernyataan eksplisit pengguna bahwa UI fix dan backend mulai. Audit ini tidak melewati instruksi tersebut.
2. **Akses model dalam budget:** usia 18+ sudah terjawab. Key belum tersedia; minimum pembelian, checkout rupiah, dukungan tools, token cap dan kuota endpoint harus cocok dengan Rp50.000. Periksa sejak M1, lakukan probe development lebih awal ketika akses siap. Tidak membeli kredit atau mengganti provider secara otomatis.
3. **Runtime lokal:** Docker daemon, jaringan worker/target, ruang disk, resource browser dan setup produk belum terbukti. M2 harus membuktikan batas akses sebelum worker dibuka melalui UI.
4. **Kelayakan waktu:** 24 titik nyata, GT manual 40 laporan dan 80 run A/B adalah scope besar untuk 30 jam solo. M3/M6 menjadi checkpoint kelayakan; jangan mengurangi target atau mengisi hasil fiktif untuk mengejar jadwal. Jika perlu perubahan scope, catat keputusan secara eksplisit sebelum freeze.
5. **Rilis:** nama/URL repo publik, lisensi kode asli, paket teruji dari kondisi bersih, video, slide, thumbnail dan screenshot final belum tersedia. Semuanya pekerjaan rilis, bukan alasan menunda fondasi lokal setelah diotorisasi.

## Pemeriksaan audit

- Pemeriksaan akhir **22 file Markdown dan 117 link lokal**: seluruh target link ditemukan, fence berpasangan, decoding UTF-8 berhasil dan tidak ada karakter replacement. Pemeriksaan ini tidak membuktikan URL publik/release sudah tersedia.
- Hitung ulang contoh metrik menggunakan pecahan eksak: contoh delapan kasus, tanpa prediksi positif, seluruh prediksi salah, seluruh prediksi benar dan denominator nol. Lima kasus aritmetika lulus; ini bukan tes modul aplikasi yang belum ada.
- Periksa penjumlahan rancangan dataset 14+14+6+6=40, positif 7+7+3+3=20, serta lab 8+8+4+4=24. Ini memeriksa rancangan, bukan keberadaan bug/report.
- Hash SHA-256 kedua PDF lokal cocok dengan [catatan sumber](sources/README.md). Audit tidak mengunduh ulang atau mengklaim ada versi PDF baru.
- Model ID/harga, terms usia/minimum kredit OpenRouter serta sumber teknis Docker/SQLite diperiksa melalui sumber primer. Angka checkout rupiah dan kemampuan live akun belum diverifikasi. Rujukan ada di dokumen pemilik.
- Seluruh acceptance criteria backend/worker tetap **BELUM DIUJI**; tidak menjalankan ulang QA browser hanya untuk perubahan dokumentasi.

Langkah teknis berikutnya adalah M1 pada [implementation.md](implementation.md), setelah gate UI/arahan mulai terpenuhi. Tidak membutuhkan dokumen desain baru lagi sebelum potongan pertama; schema konkret, prompt dan konfigurasi dibuat bersama implementasi lalu diverifikasi.

## Pemeriksaan revisi 4 November 2026

Scope dataset diselaraskan pada rencana, evaluasi, mapping lab, alur, desain, checklist dan instruksi repositori. Komposisi baru 8+8+2+2=20; positif/negatif masing-masing 4+4+1+1=10. Lab tetap 24 titik: 10 area benchmark + 4 development + 10 non-benchmark. Dua arm pada 20 laporan menghasilkan 40 run, dengan cap 20*1 + 20*12 = 260 panggilan sebelum development/chat. Rumus utama sekarang recall=TP/10 dan strict accuracy=(TP+TN)/20; satu keputusan mengubah strict accuracy 5 poin persentase.

Perubahan ini memperkecil GT/evaluasi, tanpa menjamin kecukupan 30 jam atau mengurangi beban lab. Belum ada laporan final, GT, benchmark atau komponen backend yang dibangun. Pemeriksaan revisi lulus: 22 Markdown UTF-8, 117 link lokal tanpa target hilang/fence terbuka, jumlah tabel dataset pada plan/evaluation, mapping 24 ID lab menjadi 10 evaluasi/4 development/10 non-benchmark, serta aritmetika metrik dan jumlah run/panggilan. Ini pemeriksaan dokumentasi, bukan tes aplikasi atau hasil benchmark.

## Penambahan PRD - 4 November 2026

Atas permintaan pengguna, [prd.md](../prd.md) menambahkan satu ringkasan kebutuhan produk dan pemilik keputusan stack. Pilihan MVP: tiga container app/worker/lab, UI pada app, Chromium pada worker, dua file SQLite terpisah melalui aiosqlite, empat named volume dan evaluator CLI di host. Default port, maintenance dan pemisahan storage diselaraskan pada runtime; dependensi baru dicatat sebagai rencana pada third-party. Tidak membangun source/Compose atau memasang dependensi. Pemeriksaan lulus pada 23 Markdown dan 131 link lokal: UTF-8/fence/target link valid, tabel PRD tepat tiga service dan empat volume, dua DB terpisah serta target 20 laporan/40 run konsisten. Ini pemeriksaan dokumentasi, bukan verifikasi runtime atau kompatibilitas paket.

## Provider cadangan - 4 November 2026

Permintaan pengguna menambah rencana adapter Gemini direct, OpenAI Platform API dan xAI/Grok di samping OpenRouter. Gemini 3.5 Flash-Lite tercantum memiliki Free Tier dan function calling; quota/access project belum diperiksa. Grok API ditagih per token, tanpa menganggap Playground sebagai kuota API gratis. Plus/Codex pengguna bukan kredit Platform API otomatis; jalur resmi Sign in with ChatGPT untuk plan pengguna eligible dicatat terpisah sebagai opsi lanjutan dengan consent/registrasi dan batas preview yang belum dipenuhi integrasi MVP. Sumber primer ditautkan pada PRD dan diperiksa saat revisi, tanpa membaca credential/balance privat.

Kontrak fallback: sebelum respons sukses pertama/aksi target, maksimal dua dispatch per langkah berupa retry atau fallback dalam cap/ledger/deadline yang sama; sesudah respons pertama provider dikunci. Quota/kredit habis hanya dialihkan ke FREE_TIER terverifikasi; refusal/config/schema/policy error tidak memicu fallback. Benchmark mematikan fallback/auto-routing dan memakai model/provider yang sama pada A/B. PRD, kontrak API/runtime, rencana, flow/desain, checkpoint dan inventaris layanan diselaraskan; tiga container dan dataset 20 laporan tetap. Tidak mengimplementasikan adapter, mengubah prototipe, mengunduh SDK, membeli kredit atau melakukan live API call. Acceptance PROVIDER-01 tetap BELUM DIUJI. Pemeriksaan lulus pada 23 Markdown dan 134 link lokal: decoding UTF-8, pasangan fence dan target link tanpa temuan; kontrak provider/fallback ditinjau konsistensinya. Ini bukan verifikasi key, quota, kemampuan adapter atau saldo provider.

## Kandidat Azure for Students - 4 November 2026

Pengguna mengonfirmasi mahasiswa aktif dengan email kampus; usia 18+ sudah tercatat sebelumnya. Berdasarkan sumber Microsoft, tutorial apply dan pemeriksaan Foundry ditulis pada docs/azure-students.md. PRD menambah profil azure_foundry berstatus nonaktif/pending; aktivasi, saldo hibah, model/deployment, cakupan kredit, quota dan tools belum diverifikasi. Kredit pendidikan dibedakan dari free tier, dana pribadi, OpenAI Platform dan Plus. Marketplace/partner model tidak dianggap otomatis tercakup kredit. Tidak membuat akun/resource, upgrade PAYG, melakukan inference atau memindahkan lab ke cloud. Pemeriksaan dokumentasi lulus: 24 Markdown UTF-8, 138 link lokal, tidak ada target hilang atau fence terbuka. Pemeriksaan akun/adapter runtime tetap belum dilakukan.

## Audit handoff dan startup - 4 November 2026

Kesimpulan: dokumentasi cukup untuk M1 lokal bertahap setelah gate UI terpenuhi; belum ada dasar menyatakan runtime aman atau produk siap cloud. File docs/execution-prompt.md menyiapkan prompt dengan pembacaan dokumen, status awal, batas M1, pengujian dan laporan aktual. Prompt tidak mengasumsikan UI telah disetujui; konfirmasi pengguna diminta agar gate bisa diselesaikan tanpa berulang di chat baru.

Perbaikan audit: target startup satu perintah kini menjadi FR-12 dan kontrak runtime/distribusi, dengan setup/seed terpisah, readiness yang benar serta restart tanpa reset/inference otomatis. M1 dipecah menjadi sub-batch bootstrap/Compose app, auth/snapshot, lalu policy/state/ledger/mock. App M1 tidak mengklaim worker/lab sudah tersedia. UI review tidak lagi menyebut jumlah acceptance criteria lama. Salinan guidebook-kartika.pdf di root mempunyai hash identik dengan rulebook sumber dan dikecualikan dari publikasi default pada .gitignore; file tidak dihapus.

Preflight read-only aktual: Python 3.11.9, Docker CLI 29.7.2, Compose v5.3.1 dan Git 2.55.0.windows.2. Docker config pengguna memberi Access is denied dan koneksi named pipe docker_engine gagal karena tidak ditemukan. Daemon tidak terjangkau dari sesi audit; tidak menyimpulkan engine rusak/tidak terpasang, tidak melakukan reset/reinstall atau memulai service. Chat eksekusi memeriksa ulang dan tetap dapat mengerjakan fondasi/pemeriksaan independen sambil menandai container belum terverifikasi. Tidak ada source, Compose, model call, cloud resource, dataset final atau benchmark yang dibuat pada audit ini.

Verifikasi akhir lulus: 25 Markdown UTF-8 dan 139 link lokal tanpa target hilang/fence terbuka, jumlah tabel dataset 20/10/10 pada plan/evaluation, 24 ID lab dengan alokasi 10 evaluasi/4 development/10 non-benchmark, aritmetika 40 run/260 cap panggilan dan contoh F1/accuracy. `node --check ui-prototype/dist/app.js` juga lulus; ini hanya pemeriksaan sintaks ulang, bukan QA browser atau bukti backend. Status UI belum diubah oleh audit; prompt tetap menghormati konfirmasi yang sedang diminta.

## Konfirmasi baseline UI - 4 November 2026

Setelah audit, pengguna menyatakan UI fix dengan kemungkinan perbaikan nanti. Status aktif pada AGENTS, README, plan, PRD, design/ui-review, implementation, README prototipe dan prompt diselaraskan: M1 boleh dimulai di chat baru tanpa persetujuan UI ulang. Gate terselesaikan oleh jawaban pengguna, bukan oleh asumsi asisten atau hasil QA. M1-M10, auth/worker/model dan benchmark tidak dinyatakan selesai; turn ini hanya memperbarui dokumentasi, tanpa mengubah source prototipe atau memulai backend. Riwayat audit/QA sebelum persetujuan dipertahankan sebagai snapshot lama. Pemeriksaan dokumentasi mencakup 25 Markdown dan 139 link lokal tanpa temuan format/target; prompt tidak lagi memuat konfirmasi UI pending.
