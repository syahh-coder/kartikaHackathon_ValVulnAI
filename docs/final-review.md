# Paket review ValVuln AI

**Update cakupan mode14 November2026:** reset admin sekarang mengatur seluruh13 titik existing termasuk pencarian katalog; validasi otomatis tetap3 subtype.23 tes terarah lulus dan smoke UI fixed lalu vulnerable memeriksa13 flag, snapshot bersama serta escaping teks inert katalog. Kondisi akhir vulnerable dengan sesi manual aktif.14 tabel aplikasi termasuk68 baris ledger identik terhadap backup sebelum deploy; worker IDLE/health OK. Tidak menjalankan exploit/model atau mengesahkan GT. [Kontrak dan bukti terbaru](lab-reset-ui.md). Catatan mode akhir di bawah adalah hasil batch sebelumnya; belum push/rilis.

**Update target manual bersama14 November2026:** port8001 kini lab asli dengan sesi eksklusif admin; salinan lama disimpan berhenti/opsional8002.28 tes lulus, smoke UI dua mode dan dua akun membuktikan snapshot/objek sama serta sink sesuai mode.14 tabel aplikasi yang diperiksa termasuk68 baris ledger identik; health worker pinnedIP OK dan egress lab diblok. Kondisi akhir fixed dengan sesi manual aktif/target maintenance dan worker IDLE untuk pengguna mencoba; reset mengakhiri sesi sebelum validasi agent. Tidak menjalankan payload exploit, inferensi atau mengesahkan GT. [Kontrak/bukti](manual-lab.md). Arsip/push belum diperbarui.

**Update dua mode UI14 November2026:** admin kini memilih Lab rentan/Lab kontrol diperbaiki.18 tes terarah lulus; smoke UI menerapkan fixed lalu vulnerable dengan flag DB cocok dan snapshot sinkron, hunter API403, desktop/mobile tanpa overflow.14 tabel yang diperiksa termasuk68 baris ledger identik. Kondisi akhir vulnerable/ready/dirty=false, worker IDLE. Tidak menjalankan exploit atau inferensi model dan tidak menguji ulang perbedaan verdict. [Kontrak/bukti](lab-reset-ui.md). Catatan vulnerable-only di bawah adalah riwayat versi awal; arsip/publikasi belum diperbarui.

**Update reset UI14 November2026:** tombol admin sudah terpasang dan satu reset melalui Chromium sukses.19 tes unik terarah lulus (subset anti-duplikasi diperiksa ulang), hunter API403, desktop1366/mobile390 tanpa overflow. BAC-08/XSS-08/UP-04 vulnerable, worker IDLE, dirty=false dan snapshot sinkron setelah reset.14 tabel yang diperiksa termasuk66 baris ledger identik; audit/login/binding berubah sesuai operasi. Tidak menjalankan exploit, validasi kerentanan baru atau model. [Kontrak/artefak](lab-reset-ui.md). Arsip review-v6 tetap baseline sebelum Groq/reset UI; belum dibuat ulang atau dipublikasikan.

**Update14 November2026: Groq direct terhubung.** [Groq setup/hasil](groq-setup.md) mencatat85 tes terarah dengan hasil terakhir lulus dan **satu triage LIVE_VERIFIED** pada `openai/gpt-oss-120b`,1225 input/302 output token, tanpa request target. Prioritas aktif Groq→OpenRouter→Azure, tanpa fallback otomatis. Ledger59→60 dengan seluruh59 baris lama identik; reservasi baruRp100 COST_UNKNOWN, bukan biaya nol. GT/freeze/benchmark/submission tetap pending. Arsip review-v6 di bawah adalah snapshot13 November sebelum adapter Groq; gunakan working tree/commit baru untuk source Groq. Rincian13 November berikut adalah baseline historis.

**Checkpoint terbaru: integrasi AI-ke-validasi, 13 November 2026.** Provider prioritas **OpenRouter → Azure Foundry**, dipilih eksplisit oleh operator. Kode menghubungkan hasil ekstraksi AI ke draf klaim, konfirmasi pemilik, policy backend, worker fixture, verifier serta review/publikasi admin. Lihat [hasil/batas integrasi](ai-validation-integration.md).

Status paket: **READY_FOR_REVIEW_WITH_PENDING_INPUTS**. Kode yang dapat dikerjakan selesai pada scope ini; verifikasi kerentanan/GT manual ditempatkan pada review terakhir, sesuai instruksi pengguna. Tidak menyatakan model live, benchmark, video atau submission selesai.

| Bagian | Hasil |
| --- | --- |
| OpenRouter/Azure | Adapter dan alur integrasi diuji dengan HTTP simulasi; default OpenRouter |
| Alur AI ke run | Draf `triage-v2` terikat versi/scope/owner; konfirmasi dicatat di audit tanpa migrasi |
| Lab/verifier | Tiga subtype produk tetap; planner deterministik, tanpa script laporan |
| Live | Belum terverifikasi; tidak ada inferensi cloud pada batch integrasi ini |
| GT/freeze/evaluasi | 20 kandidat, GT manusia belum diisi; 40 slot nyata belum dijalankan |
| Data/ledger | Dipertahankan; reservasi unknown historis tidak dihapus |
| Publikasi | Repo sudah ada; release/video/slide publik/submit final masih pending |
| Lisensi | Keputusan lisensi kode asli menunggu pengguna |

## Mulai review

1. [README](../README.md) untuk menjalankan dan memahami batas produk.
2. [Panduan provider](provider-setup.md): checker lokal, OpenRouter pertama/Azure kedua, pergantian pada ledger yang sama, dan smoke live saat siap.
3. [Integrasi AI dan hasil tes](ai-validation-integration.md), [flowchart](backend-flow.md), [OpenAPI](api/openapi.json).
4. [Review manual terakhir](manual-final-review.md): tiga alur produk, role/scope, GT, smoke dan kelengkapan juri.

## Paket dan materi

Paket source batch ini disiapkan pada `artifacts/r4/review-v6-20261113/valvuln-ai-review-source.zip`, beserta checksum dan inventaris. Ini kandidat lokal untuk review; tidak memuat key, DB/ledger atau GT privat. Arsip review-v3/v4/v5 tetap riwayat, bukan versi source terbaru. Source ZIP tidak membundel image Docker; build awal memerlukan internet. Hasil ekstraksi dan batas instalasi dicatat pada dokumen integrasi.

- [Slide HTML](../submission/slides.html), [PDF](../submission/slides.pdf): lokal, belum link slide publik.
- [Thumbnail](../submission/thumbnail.png): 1200×630, di bawah500KB.
- [Screenshot](../submission/screenshots): maksimal5 gambar, MOCK/sintetis diberi label.
- [Preview video MOCK](../submission/demo-preview-MOCK.webm): draf tanpa narasi; bukan video submission final.
- [Storyboard](../submission/demo-storyboard.md), [draft formulir](../submission/form-draft.md), [draft release](../submission/release-draft.md).

Bukti tes dan QA batch ini tersimpan privat di `artifacts/ai-bridge-20261113/`. Tautan artefak privat pada dokumentasi historis hanya berlaku di workspace pengembangan; jangan menganggapnya tersedia bagi juri dari clone GitHub.

## Yang masih memerlukan input nyata

- Isi konfigurasi provider ketika key/deployment/akses tersedia; jalankan satu smoke melalui API aplikasi. Key tidak dikirim melalui chat. Verifikasi biaya unknown secara terpisah; tidak diasumsikan nol.
- Tinjau manual kandidat di `artifacts/r3/candidates-v1/gt-review.csv` dan bukti terikat masing-masing kasus; label bukan keputusan otomatis asisten.
- Sesudah prasyarat nyata lolos, jalankan freeze dan40 slot A/B lewat [runbook](r3-runbook.md). Metrik tetap kosong sebelum eksperimen.
- Pilih lisensi, tinjau atribusi, rekam demo final dan sediakan tautan publik video/slide. Otorisasi publikasi/submit tetap keputusan pengguna.

Tes HTTP simulasi membuktikan integrasi kode, bukan akses akun cloud atau akurasi dunia nyata. Verifikasi lokal yang sudah ada tidak perlu diulang seluruhnya; ulang hanya bagian yang berubah atau kasus manual yang membutuhkan bukti baru.
