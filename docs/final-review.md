# Paket review ValVuln AI

**Update terbaru: Azure Foundry untuk akun pelajar (7 November).** Adapter Azure teks, wiring triage/readiness/evaluator, checker privat dan overlay preview sudah **CODE_TESTED:148 tes lulus/95,70 detik**, termasuk40 tes Azure baru; [JUnit](../artifacts/azure-setup/targeted-tests.xml), [hasil/batas](azure-verification.md). **LIVE_VERIFIED=false, CONFIGURATION_REQUIRED.** Tidak ada request Azure/target atau provisioning/billing. Preview **http://127.0.0.1:8010** sudah memakai source terbaru dan tetap MOCK; seluruh16 tabel bisnis preview serta data/ID container instalasi asli dipertahankan ([bukti runtime](../artifacts/azure-setup/preview-update-result.json)).

**Tindakan pengguna berikutnya:** buka **`D:\BelajarCyberSec\kartikaHackathon\.env.azure`**, file privat yang sudah disiapkan. Isi key dari Azure resource **Keys and Endpoint**, endpoint resource, deployment name, identitas model/version, tarif/kurs/reservasi serta konfirmasi kredit/kuota/kompatibilitas. Key saja belum cukup. [Langkah portal dan cara menyalakan](azure-setup.md), [template publik](../.env.azure.example). Jalankan checker tanpa jaringan, lalu overlay pada project/volume/ledger preview yang sama. Gunakan **Minta saran AI** pada percakapan hunter; Ringkasan observasi admin tetap dibuat aplikasi. Biaya Azure per respons tetap COST_UNKNOWN dengan reservasi penuh; gate freeze/benchmark tidak dilonggarkan. GT/bukti manusia, rekonsiliasi biaya smoke dan review artefak/submission tetap pending.

**ZIP source terbaru untuk review ini: [reviewv5](../artifacts/r4/review-v5/valvuln-ai-review-source.zip)**, [checksum](../artifacts/r4/review-v5/valvuln-ai-review-source.zip.sha256), [inventaris](../artifacts/r4/review-v5/package-manifest.json), [pemeriksaan ekstraksi](../artifacts/azure-setup/archive-check.json). File privat `.env.azure`, DB/ledger dan key dikecualikan. Versiv3/v4 di bawah adalah baseline historis; tidak dioverwrite. Tidak ada publikasi/push/submit sebelum review pengguna.

**Update setelah percobaan pengguna:** [perbaikan form guideline admin](admin-guideline-validation-fix.md) tersedia di source dan preview8010. Konfigurasi contoh teruji menyimpan201, 11 tes terarah dan QA browser lulus. Data preview dan instalasi asli dipertahankan. ZIP terbaru untuk perubahan ini: [reviewv4](../artifacts/r4/review-v4/valvuln-ai-review-source.zip), [checksum](../artifacts/r4/review-v4/valvuln-ai-review-source.zip.sha256), [inventaris](../artifacts/r4/review-v4/package-manifest.json), [pemeriksaan ekstraksi](../artifacts/admin-schema-error/archive-check.json). ZIPv3 dan verification-summary pada tabel di bawah tetap baseline sebelum fix; tidak dioverwrite. Status AI live/freeze/evaluasi tidak berubah.

**READY_FOR_REVIEW_WITH_PENDING_INPUTS — 7 November 2026.** Seluruh pekerjaan kode/paket independen sisa R3 dan persiapan R4 sudah disiapkan. Ini paket review lokal; belum benchmark lengkap atau submission. Tidak ada push, release, hosting, upload YouTube/slide atau pengiriman formulir.

| Status | Hasil aktual |
| --- | --- |
| CODE_TESTED | Ya, projection/runner teks, schema/ledger006, freeze gate, scorer, simulasi dan pengemasan lokal |
| LIVE_VERIFIED | **False — CONFIGURATION_REQUIRED**, key/profil live belum tersedia |
| FROZEN | **False**, GT/bukti kandidat dan smoke nyata belum terpenuhi |
| EVALUATED | **False**, jadwal nyata40 slot NOT_STARTED; metrik produk null |
| PUBLISHED / SUBMITTED | **False**, menunggu review/otorisasi pengguna |

## Yang dapat ditinjau dan dicoba

| Berkas | Lokasi | Keterangan |
| --- | --- | --- |
| Source ZIP | [valvuln-ai-review-source.zip](../artifacts/r4/review-v3/valvuln-ai-review-source.zip) | Kandidat lokal; mengecualikan key, DB/ledger, GT/kandidat privat, cache dan binary image |
| Checksum / inventaris | [SHA256](../artifacts/r4/review-v3/valvuln-ai-review-source.zip.sha256), [manifest per file](../artifacts/r4/review-v3/package-manifest.json) | Versi working tree review; belum commit/tag rilis |
| Quick start | [review-quickstart.md](review-quickstart.md) | Preview app-only MOCK terpisah pada8010; panduan topologi produk, konfigurasi dan troubleshooting |
| Evaluator teks | [r3-runbook.md](r3-runbook.md) | Contexts/smoke/freeze/run/export/recover; memakai ledger aplikasi yang sama untuk live |
| Slide lokal | [HTML9 halaman](../submission/slides.html), [PDF](../submission/slides.pdf) | Bisa dibuka lokal; belum tautan slide publik |
| Thumbnail | [PNG](../submission/thumbnail.png), [sumber HTML](../submission/thumbnail.html) | **1200×630 px, 153445 byte**, di bawah500KB |
| Screenshot1 | [Triage MOCK](../submission/screenshots/01-triage-MOCK.png) | UI aktual pada app disposable, respons tetap berlabel |
| Screenshot2 | [Hunter mobile MOCK](../submission/screenshots/02-hunter-mobile-MOCK.png) | Viewport390px |
| Screenshot3 | [Observasi sintetis admin](../submission/screenshots/03-observations-SYNTHETIC.png) | Rekaman sintetis, tanpa reproduksi target/model nyata; total3 gambar |
| Preview demo | [WebM MOCK](../submission/demo-preview-MOCK.webm) | Draf UI singkat tanpa narasi; **bukan video submission final/YouTube** |
| Naskah demo | [Storyboard8:30](../submission/demo-storyboard.md) | Bagian yang memerlukan bukti nyata dinyatakan pending |
| Draft publikasi | [Release](../submission/release-draft.md), [isian/formulir](../submission/form-draft.md) | Lisensi, commit/tag dan tautan publik final belum diisi |

Mulai dengan slide/PDF, lalu gambar/preview. Untuk mencoba source, ekstrak ZIP ke folder baru dan ikuti quick start. Preview selalu MOCK dan tanpa worker/lab/key; bukan cara mengganti DB untuk memperoleh budget baru. Jangan menunjuk evaluator live ke volume preview. Instalasi produk yang sudah ada tetap tidak diubah.

Tautan `artifacts/` pada indeks ini berlaku di workspace review dan sengaja tidak disertakan ZIP source. Slide/gambar/preview dan source aplikasinya disertakan. Sebelum publikasi, tautan review privat perlu diganti dengan file/link rilis yang sudah disetujui.

## Hasil pemeriksaan

Tes terarah unik lintas run dicatat pada [verification-summary.json](../artifacts/r4/verification-summary.json). Rangkaian akhir runner/paket/configuration: **43 lulus dalam21,37detik**; pemeriksaan tambahan konflik UI/evaluasi, jalur triage default dan worksheet: **3 lulus dalam2,03detik**. Bootstrap/migrasi-preservasi terdampak juga lulus pada rangkaian awal. Tidak mengulang suite M6 atau seluruh R1/R2.

- [JUnit akhir](../artifacts/r3/runner-final.xml), [integrasi tambahan](../artifacts/r3/affected-integration.xml), [migrasi/awal](../artifacts/r3/runner-initial.xml), [retest projection](../artifacts/r3/context-retest.xml). Sembilan gagal awal adalah fixture yang ditolak profil/deadline; sudah diperbaiki dan retest lulus. Uji40 slot sempat gagal pada ID binding fixture null, kemudian [lulus](../artifacts/r3/runner-integration-retest.xml). Artefak gagal dipertahankan.
- [Simulasi40 slot](../artifacts/r3/simulation-v1/simulation.report.json): schema valid40, respons ABSTAIN tetap, tanpa provider/target request; metrics=null, live/frozen/evaluated=false. GT pada tes integrasi diberi label SIMULATED_TEST_ONLY dan tidak mengisi manifest/CSV pengguna.
- [Konfigurasi aktual](../artifacts/r3/provider-readiness.json): CONFIGURATION_REQUIRED, semua prasyarat live belum terisi. Dicek sekali tanpa mencetak secret; tidak melakukan panggilan berbayar atau membeli akses.
- [Container startup/restart](../artifacts/r4/container-check-retest.json): image app review terpisah, network none, volume baru, health/schema006, seed3 akun dan restart dengan data/hash sama. **Container aktif tetap sama, 37 run dan54 baris ledger beserta hash data tetap sama**. Resource disposable dibersihkan; [kegagalan awal](../artifacts/r4/container-check.json) dipertahankan.
- Image app dan evaluator review dibangun lokal dengan tag terpisah. Hash source evaluator di host dan image cocok. [Compose preview app-only](../artifacts/r4/preview-check.json) juga lulus build/start/health/readiness pada8010 dan cleanup project/volume baru; data aktif tetap sama. Image tidak dipublikasikan/dibundel. Percobaan build network-none gagal unduhan; build normal berhasil dengan layer cache. Bukan cold build dari cache kosong.
- [Pemeriksaan ZIP pada folder ekstrak baru](../artifacts/r4/archive-check.json): memeriksa hash/import dari arsip, HTTP startup, login/simpan draf dan restart dua proses. Interpreter/dependensi host yang sudah ada dipakai. Tidak mengklaim clean dependency install atau cold start terbaru ketiga service pada laptop juri.
- Pemeriksaan ZIP awal gagal saat cleanup karena redirector Python venv Windows meninggalkan child pemegang lock; script diperbaiki agar langsung memiliki PID interpreter server. ZIP awal tetap di `artifacts/r4/review-v1/`; v2 lulus sebelum penguatan gate biaya, kandidat final pada `review-v3/`. Kegagalan awal tidak dihitung sebagai bukti restart.
- Penguatan akhir: biaya smoke wajib settled sebelum freeze, biaya unknown lama menghalangi resume, ekspor memakai status/actual ledger dan fakta upload memakai referensi korelasi fixture tanpa nonce/filename aktif. [Retest gate/projection](../artifacts/r3/freeze-final.xml), [akuntansi](../artifacts/r3/accounting-final.xml), [smoke proof](../artifacts/r3/smoke-proof-final.xml) lulus pada subset terdampak.
- [Capture](../artifacts/r4/capture-result.json):3 screenshot,9 slide, thumbnail memenuhi dimensi/ukuran; page error/request luar0, satu dispatch MOCK dan target/provider nyata0. Banner penjelas hanya pada halaman capture. Capture awal disimpan privat di `artifacts/r4/capture-initial/`.

Rincian perubahan dan keterbatasan: [r3-r4-verification.md](r3-r4-verification.md). Model tetap teks saja; tidak ada target request, dispatch worker atau perubahan verdict dari runner. Schema source006 belum diterapkan ke app aktif. R1/R2 tetap CODE_TESTED historis; M6 DEFERRED.

## Satu daftar review/input Anda

1. **Kandidat dan GT/bukti:** buka [panduan20 kandidat](../artifacts/r3/review-v1/review-guide.md), [usulan PROPOSED_NOT_GT](../artifacts/r3/review-v1/proposals.private.json), [CSV manusia](../artifacts/r3/candidates-v1/gt-review.csv), dan [template binding](../artifacts/r3/review-v1/bindings.template.private.json). Saat ini20 kandidat/0 penerimaan/0GT/0 konteks kasus final. Tinjau kelayakan teks dan bukti snapshot terkait; isi ACCEPT+GT hanya jika cukup, EXCLUDE jika tidak layak, PENDING bila belum siap. Target10/10 tidak menjadi alasan mengubah label. Import ke manifest nama baru sesuai runbook. Bukti historis/peta source bukan bukti untuk kandidat berbeda.
2. **Akses model:** lengkapi `.env` privat sesuai [field runbook](r3-runbook.md), termasuk key, fixed model/provider, akses/tier/pendanaan, harga/kurs/token bound terverifikasi dan reservasi dalam totalRp50.000. Jangan kirim key di chat. Setelah service/source/schema siap pada DB otoritatif dan input kasus lengkap, alur smoke→freeze→40 slot nyata sudah tersedia; tidak ada pembelian atau aktivasi billing otomatis.
3. **Lisensi dan materi:** pilih lisensi kode asli proyek, tinjau deklarasi pihak ketiga/pre-existing serta isi slide/thumbnail/screenshot/deskripsi. Belum ada LICENSE proyek yang dipilih sepihak. [Laporan nyata pending](../artifacts/r3/review-v1/report.pending.json) dan [jadwal40 NOT_STARTED](../artifacts/r3/review-v1/outcomes.pending.json) tidak berisi angka akurasi palsu.
4. **Video dan publikasi:** setujui materi dan lengkapi narasi/rekaman final dengan hasil yang benar-benar ada. Link YouTube≤10menit, slide publik, commit/tag/release dan akses setara juri masih pending. Setelah review, berikan otorisasi untuk update/publikasi yang diinginkan; paket ini sendiri **tidak mengotorisasi push/upload/submit**.

Checkpoint berikutnya adalah review paket ini dan melengkapi input nyata di atas. Kode/pengemasan independen tidak menunggu izin sub-tahap lagi; benchmark dan publikasi tetap memerlukan prasyarat/bukti masing-masing.
