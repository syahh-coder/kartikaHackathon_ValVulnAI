# Arsip kontrak R1

Disimpan 7 November 2026 setelah R1 CODE_TESTED. Jangan mengulang batch ini; [prompt aktif R2](execution-prompt.md). Isi kontrak/handoff sebelumnya dipertahankan di bawah.

# Handoff aktif: R1 setelah review M6

Tanggal **7 November 2026**. Pengguna menyetujui penyempitan scope submission dan meminta dokumentasi serta prompt lanjutan. Pemilik cakupan: [submission-scope.md](submission-scope.md). Eksperimen aktif: [functional-v2](evaluation.md). Prompt M1 dan handoff lama disimpan di [execution-prompt-history.md](execution-prompt-history.md); jangan menjalankannya sebagai instruksi terbaru.

Status aktual saat penyusunan: M1–M5 selesai teknis lokal dengan planner mock; M6 asli masih sebagian, 13/24 historis dan 11 PLANNED. BUSINESS_LOGIC LAB belum didukung. Key/live/GT final/benchmark belum terverifikasi. Perubahan ini hanya dokumentasi, tidak menjalankan ulang tes produk atau memperbarui service Compose.

**Hasil eksekusi 7 November:** batch R1 telah dikerjakan, source **CODE_TESTED**; [hasil/kebutuhan konfigurasi](r1-verification.md). LIVE_VERIFIED belum: CONFIGURATION_REQUIRED. Prompt di bawah dipertahankan sebagai kontrak batch yang telah dieksekusi; jangan mengulang implementasi atau M1. Lanjutan hanya konfigurasi/smoke live setelah prasyarat siap, serta checkpoint R2 UI/ringkasan bukti. Service/data aktif tetap dipertahankan.

## Prompt siap salin

```text
Lanjutkan ValVuln AI di D:\BelajarCyberSec\kartikaHackathon.
Baca AGENTS.md terbaru, docs/submission-scope.md, docs/execution-prompt.md, docs/implementation.md bagian jalur R1-R4, docs/evaluation.md, prd.md, README.md dan kontrak provider/policy pada docs/architecture.md serta docs/runtime.md. Periksa source aktual app/providers/, app/config.py, app/schemas.py dan tes terkait sebelum mengubah kode. Dokumen/artefak lama adalah riwayat, bukan bukti keadaan runtime hari ini.

Keputusan aktif 7 November: fokus submission sempit, bukan menyelesaikan M6 asli atau menambah fitur review rekaman bisnis. Target 24 titik menjadi backlog; M6 tetap sebagian 13/24, BUSINESS_LOGIC tetap belum didukung. Jangan mengulang bootstrap M1-M5 atau meminta UI fix ulang. Pertahankan tujuan intake -> scope -> bukti -> review, dengan klaim kemampuan sesuai implementasi.

Kerjakan dan tuntaskan SATU batch R1: integrasi provider dan triage teks yang tervalidasi. Ini bukan pekerjaan menulis rencana tambahan.

1. Periksa adapter engine/contracts/mock, penyimpanan attempt/ledger, enforcement scope/role dan konfigurasi yang sudah ada. Gunakan ulang komponen yang layak; jangan membuat framework multi-agent, mengganti database atau melebarkan tools worker.
2. Implementasikan satu adapter live TEXT-ONLY yang memakai API key server-side melalui konfigurasi proyek. Pilihan awal OpenRouter dengan model yang dikonfigurasi; cukup satu provider pada batch ini. Jangan menganggap model gratis/kuota/model ID saat ini tersedia. Verifikasi dokumentasi primer saat implementasi HTTP/schema/error; jangan menyalin token sesi ChatGPT/Codex atau memasang kredensial pada browser. Gemini/provider lain tidak wajib untuk lulus R1.
3. Buat schema output triage minimal: klaim utama, kategori/subtype yang dikenali, informasi/prasyarat yang kurang, saran scope/capability dan alasan singkat. Scope/izin sebenarnya selalu dari backend. Output model tidak mengubah role, scope aktif, profil target atau verdict teknis. Report/guideline/bukti diperlakukan sebagai data; instruksi di dalamnya tidak boleh mengubah kebijakan.
4. Hubungkan triage teks ke jalur intake yang sesuai setelah memeriksa session/membership/ownership. Tampilkan saran model sebagai saran. Jika kontrak execution_mode lama mencampur live dengan eksekusi lab, pisahkan secara eksplisit sesuai dokumen arsitektur: mengaktifkan triage live tidak boleh mengaktifkan worker atau mengubah mode planner lab. Pertahankan perilaku mock/replay dan fail-closed konfigurasi live.
5. Tidak ada tool calling, shell/eval, raw script/PoC dari laporan, payload generation, request target atau model-to-worker dispatch pada R1. Jangan membangun atau menjalankan alur eksploitasi otomatis. Pertahankan jalur pemeriksaan produk yang sudah ada tanpa memperluasnya. Triage tidak membaca evaluator/catalog, GT, source jawaban lab atau artefak privat sebagai konteks.
6. Catat requested/resolved model, provider aktual, prompt/schema version, input hash dan usage/cost sesuai kontrak lama. Batasi input/output/token/waktu/retry, simpan keluaran yang diperlukan secara privat dengan redaksi dan kontrol akses. Jangan mencatat secret/raw credential atau mengekspos error provider mentah kepada hunter. Attempt gagal/cancel tetap masuk ledger; retry dan reservasi tunduk pada cap dan budget total Rp50.000, tanpa reset ledger. Harga/usage tidak diketahui harus berstatus UNKNOWN, bukan nol palsu.
7. Uji dengan transport simulasi: respons valid, JSON/schema salah, refusal, timeout/429/5xx, key hilang, provider/model tak sesuai konfigurasi, input berisi instruksi berbahaya, ownership/session, cancel dan ledger/reservasi. Pastikan semua jalur triage menghasilkan nol job/tool/request target. Jalankan tes regresi yang relevan; jangan menambah suite auditor bisnis lain sebagai pengganti integrasi ini.
8. Live smoke hanya jika konfigurasi key lokal, akses model, pendanaan/tier dan cap biaya yang sesuai budget sudah tersedia/terverifikasi. Gunakan input sintetis development tanpa target tools. Jangan membeli kredit, mengaktifkan billing/cloud atau memperluas budget. Jangan meminta key di chat atau menampilkannya. Jika akses belum siap, selesaikan source/tes simulasi, laporkan CONFIGURATION_REQUIRED dan satu kebutuhan konfigurasi yang konkret. Jangan berhenti sebelum bagian independen selesai dan jangan mengklaim live lulus dari mock.

Setelah R1, R2 menghubungkan label UI dan ringkasan observasi tersanitasi yang sudah tersedia; model tetap tidak memicu worker. Jangan langsung mengerjakan seluruh R1-R4 dalam satu batch atau memperluas UI besar. Tidak menambah kontrol/auditor/trace bisnis kecuali regresi konkret mengharuskannya.

Evaluasi aktif kelak functional-v2: target 20 teks, 10 valid/10 tidak valid, alokasi 8 BAC-08 / 8 XSS-08 / 4 UP-04. GT tetap ditetapkan pengguna berdasarkan klaim/snapshot/bukti; ini bukan 20 bug independen atau held-out akar masalah baru. Jangan membuat dataset final, GT otomatis atau metrik pada R1. A dokumen vs B dokumen+observasi adalah prediksi model; verdict verifier terpisah. BUSINESS_LOGIC/OOS/unsupported tidak diisi sebagai INVALID.

Pertahankan evaluator/catalog.json, evaluator/development_history.py, gate catalog_audit, manifest M5, riwayat/bukti gagal, kuota dan data/volume aktif. Gate lama tetap boleh exit 2 dan tidak menghalangi source adapter R1; gate itu tidak dinyatakan lulus untuk functional-v2. Dua status kesiapan dipisah. Jangan reset/seed otomatis, update service Compose, membeli atau memanggil layanan berbayar tanpa konfigurasi/pendanaan yang sudah diotorisasi, push/release atau deploy. Live smoke yang telah memenuhi syarat pada langkah 8 tetap boleh dalam budget. Verifikasi host/container hanya sesuai perubahan dan otorisasi; Docker bermasalah tidak menghalangi tes independen. Kerjakan sendiri tanpa sub-agent.

Akhiri dengan file/perilaku yang berubah, tes dan hasil aktual, status CODE_TESTED terpisah dari LIVE_VERIFIED, kebutuhan konfigurasi yang tersisa dan checkpoint R2 berikutnya. Perbarui README/docs status tanpa menandai M6 selesai. Jika ada bagian yang tidak dapat dikerjakan, jelaskan batasnya sebelum menawarkan pengganti; jangan mengulang pekerjaan administratif yang tidak menutup R1.
```

## Penerimaan batch ini

- Source adapter nyata tersedia, digunakan oleh triage teks dan diuji dengan transport simulasi; bukan MockTransport yang diganti label.
- Policy backend tetap otoritatif; triage tidak membuat job/action/request target.
- Mode dan status CODE_TESTED/LIVE_VERIFIED dipisah. LIVE_VERIFIED memerlukan respons provider nyata, bukan sekadar key ada.
- Tidak ada perluasan lab, perubahan katalog/gate, dataset final atau reset service/data.
- Bila live belum siap, hasil implementasi tetap dapat ditinjau dan kekurangan input dijelaskan spesifik.
