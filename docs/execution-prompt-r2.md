# Handoff aktif: R2 UI triage dan ringkasan bukti

Keputusan pengguna **7 November 2026**: lewati pekerjaan M6 yang belum dapat diselesaikan dan lanjutkan checkpoint berikutnya; batasi pengulangan tes. M6 asli berstatus **DEFERRED untuk submission**, bukan selesai. BAC-01..07 dan BL-01..04 tidak dikejar pada jalur aktif. Catatan katalog/grup/gate dan bukti lama tetap dipertahankan.

Status saat prompt ini disusun: R1 **CODE_TESTED** menurut [hasil R1](r1-verification.md); LIVE_VERIFIED belum, CONFIGURATION_REQUIRED. Hasil 77 tes R1 dan 86 regresi berasal dari batch R1, tidak diulang pada perubahan handoff ini. Kontrak R1 disimpan pada [arsip prompt R1](execution-prompt-r1.md). R2 pada prompt berikut telah dieksekusi; status terbaru dicatat di bawah.

**Hasil eksekusi R2 7 November:** [CODE_TESTED dan QA lokal lulus](r2-verification.md). Prompt di bawah dipertahankan sebagai kontrak batch yang sudah dikerjakan; jangan mengulang R1/R2. Checkpoint berikutnya R3 peta subtype/bukti, draf teks dan GT pengguna, dengan live/freeze sebelum benchmark. Tidak ada klaim LIVE_VERIFIED atau pembaruan service aktif.

## Prompt siap salin

```text
Lanjutkan ValVuln AI di D:\BelajarCyberSec\kartikaHackathon.

Baca AGENTS.md terbaru, docs/submission-scope.md, docs/execution-prompt.md, docs/r1-verification.md dan bagian aktif docs/implementation.md. Baca kontrak architecture/runtime/evaluation sesuai perubahan yang benar-benar diperlukan; jangan audit ulang seluruh repo atau riset provider tanpa kebutuhan konkret.

Pengguna memutuskan SKIP pekerjaan M6 tersisa dari submission. Statusnya DEFERRED, bukan lulus atau report INVALID. Jangan mengerjakan BAC-01..07/BL-01..04, mengejar angka 24, memperbaiki gate katalog lama, atau menambah auditor/parser/review bisnis. Jangan meminta persetujuan skip/UI ulang. R1 CODE_TESTED sudah tersedia; belum live. Mulai R2 sekarang.

Kerjakan satu batch R2: UI triage dan ringkasan observasi tersanitasi.
1. Gunakan endpoint dan projection R1 yang sudah ada. Periksa app/api/triage.py, app/agent/text_triage.py, kontrak output, app/templates/workspace.html dan app/static/app.js serta CSS terkait. Pertahankan baseline UI.
2. Tambahkan tindakan eksplisit meminta saran AI pada draf milik pengguna, status/poll/cancel, penanganan idempotensi dan hasil lama setelah draf/scope berubah. Chat/upload sendiri tidak memanggil inference otomatis. Sesuaikan dengan API R1 aktual; jangan membuat endpoint intake/provider duplikat.
3. Tampilkan provider/model aktual, mode triage, mode planner lab, saran/kekurangan dan status konfigurasi. Label MOCK, CONFIGURATION_REQUIRED dan CONFIGURED_NOT_VERIFIED harus jujur. Tombol/check informasi tidak membuat pemanggilan berulang. Saran AI terpisah dari hasil verifier dan tidak mengubah scope/izin/claim/target atau menjalankan worker.
4. Buat ringkasan observasi yang SUDAH tersedia dengan binding report/revision/run/snapshot/scope yang benar. Kontrol owner/admin dan publikasi tetap berlaku; tidak membocorkan bukti mentah privat, credential, GT/katalog/source jawaban, label evaluator atau catatan privat admin ke konteks/hunter. Tidak membuat bukti palsu atau menganggap rekaman CONSISTENT sebagai konfirmasi kerentanan.
5. Jika ringkasan AI memakai provider, gunakan adapter/ledger/batas input/output/retry R1. Pemanggilan eksplisit, schema ringkasan terbatas dan referensi evidence ID yang diverifikasi server. Ringkasan model tidak menciptakan atau menimpa verdict. Model tetap TEXT-ONLY, tanpa tools, target request, payload/script atau model-to-worker dispatch. Jika bukti yang cocok belum tersedia, tampilkan belum ada bukti; jangan mengembangkan validator atau menjalankan target untuk mengisi kartu UI.
6. Key belum tersedia tidak menghalangi R2: gunakan transport simulasi dan app/database disposable dengan label mock; konfigurasi live yang belum siap gagal jelas. Jangan membuat riset/key/harga/tokenizer sebagai pekerjaan utama lagi. Live smoke tetap pekerjaan terpisah sesudah konfigurasi dan pendanaan terverifikasi, bukan gate UI R2.
7. Pemeriksaan hemat: jalankan satu suite terarah pada perilaku R2 yang berubah dan regresi yang benar-benar terpengaruh. Cakup binding/ownership/projection/redaksi, stale result, state/cancel, serta nol job/action/request target dari triage/ringkasan. Pakai satu QA browser terfokus desktop dan mobile pada flow baru, dengan provider simulasi dan tanpa target/network/provider nyata. Jangan mengulang seluruh 77 tes R1 dan 86 regresi karena angka historis belum berubah. Jika ada kegagalan, perbaiki dan retest subset terdampak; perluas hanya bila ada alasan regresi/keamanan konkret. Tidak menambah tes yang hanya meniru implementasi atau mengulang audit M6.
8. Pertahankan source/data/ledger/migrasi aktif dan perubahan pengguna; jangan reset/seed, menghapus volume/artefak gagal, memperbarui service Compose, membeli kredit, memanggil provider berbayar, push/release atau deploy. Jangan memasang skill/framework baru. Kerjakan sendiri tanpa sub-agent.

Setelah pemeriksaan yang relevan lulus, hentikan pengulangan tes dan laporkan hasil R2. Buat docs/r2-verification.md ringkas dan perbarui status aktif README/docs/implementation. Akhiri dengan: bagian R2 selesai, tes/QA aktual, batas live yang masih pending dan pekerjaan R3 berikutnya. Jangan kembali melaporkan M6 13/24 sebagai blocker; cukup sebut M6 DEFERRED di luar scope aktif bila relevan. Jangan menandai R3/GT/model live sudah selesai.

Target R3 tetap functional-v2 20 teks 10 valid/10 tidak valid, alokasi 8 BAC/8 XSS/4 upload pada subtype produk tersedia. GT pengguna dan live tetap wajib sebelum klaim benchmark; unsupported/OOS/BUSINESS_LOGIC bukan INVALID. Jangan menyusun benchmark final pada R2.
```

## Penerimaan R2

- Triage R1 dapat dipakai dari UI dengan state, label model/mode dan kegagalan konfigurasi yang benar.
- Ringkasan hanya memakai observasi yang sesuai izin/binding, tanpa menaikkan klaim verifier atau membuka data privat.
- Jalur triage/ringkasan tidak membuat job/action/request target.
- Tes terarah dan QA flow baru lulus; live tidak diklaim dari mock.
- Status setelah eksekusi: R2 CODE_TESTED dan QA lokal lulus; kode berubah lokal, service produk aktif tidak diperbarui. [Hasil aktual](r2-verification.md).
