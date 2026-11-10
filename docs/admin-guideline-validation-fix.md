# Perbaikan validasi guideline admin — 7 November 2026

Pengguna melaporkan `SCHEMA_ERROR` saat **Simpan draf guideline** pada preview8010. Login admin tercatat berhasil dan belum ada guideline tersimpan. Nilai permintaan asli tidak dicatat, sehingga field persis yang salah pada percobaan pengguna tidak diklaim diketahui. Konfigurasi contoh yang diberikan berhasil disimpan201 dan diaktifkan secara eksplisit pada app disposable.

Masalah yang ditemukan: respons validasi selalu generik dan field_errors kosong. Form juga belum menandai kedua textarea sebagai wajib, sehingga JSON saja atau aturan in-scope kosong menghasilkan pesan yang tidak membantu.

Perbaikan source:

- Form menandai Teks guideline serta Aturan scope terstruktur sebagai wajib, menolak teks whitespace, memberi petunjuk JSON rusak dan menjelaskan bahwa kedua kolom harus diisi.
- Backend menolak guideline yang hanya berisi whitespace. Error422 tetap `SCHEMA_ERROR`, sekarang menyertakan maksimal8 field/message aman dengan label formulir. Tidak mengirim Pydantic input, context, pesan mentah atau nama field tambahan yang tidak dikenal.
- UI menampilkan detail aman tersebut melalui textContent. Validasi schema, profil operator, role, origin/CSRF serta aktivasi terpisah tetap berlaku.

**11 tes terarah lulus dalam6,31detik**, mencakup field wajib, jenis data, aturan kosong, format versi, data tidak tersimpan saat invalid, tidak membocorkan input/password dan batas delapan error. Regresi role/kepemilikan, scope serta CSRF/rotasi/logout yang relevan lulus. QA Chromium1366/390px lulus untuk required field, whitespace, JSON rusak, detail server, JSON+teks contoh menyimpan201, dan aktivasi eksplisit. Tidak ada page error, request luar, model atau target.

Preview8010 diperbarui setelah nol triage aktif. Pemeriksaan runtime mengonfirmasi JS baru serta error field `source_text`/`in_scope_rules`; akun uji hunter-b digunakan agar sesi admin pengguna tidak dirotasi. Semua hash/count tabel bisnis preview tetap sama. App8000, worker, lab dan data/ledger aslinya tetap sama; tidak ada schema SQL baru atau reset/seed ulang.

Bukti privat: `artifacts/admin-schema-error/targeted.xml`, `browser-result.json`, `preview-before.json`, `preview-update-result.json`. ZIP reviewv3 dan ringkasannya adalah baseline sebelum fix ini; source terbaru dikemas terpisah pada reviewv4. Materi gambar/video lama tetap berlabel MOCK dan tidak dianggap bukti model live. LIVE_VERIFIED/FROZEN/EVALUATED tetap false; tidak ada publikasi.

Cara mencoba: buka http://127.0.0.1:8010, muat ulang dengan Ctrl+Shift+R, login admin bila diminta, lalu isi dua kolom Guideline program. Salin `artifacts/demo-preview-8010/admin-guideline.txt` ke **Teks guideline**, dan `admin-scope.json` ke **Aturan scope terstruktur (JSON)**. Simpan draf, kemudian aktifkan versi draf yang diinginkan. Jika masih ditolak, pesan baru menyebut field yang perlu diperbaiki tanpa meminta password atau isi sensitif.
