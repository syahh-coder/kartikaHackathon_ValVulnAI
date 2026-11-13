# Paket review ValVuln AI

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
