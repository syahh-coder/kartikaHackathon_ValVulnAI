# Review keamanan arsitektur

Tanggal: 3 November 2026. Lingkup: review dokumen dan trust boundary, bukan pentest aplikasi. Prototipe UI simulasi kini tersedia dan diperiksa terpisah pada [ui-review.md](ui-review.md). Backend, autentikasi/otorisasi server, container dan integrasi model belum diimplementasikan/dijalankan. Seluruh pemeriksaan runtime di bawah berstatus **BELUM DIUJI**.

## 1. Keputusan review

**Rancangan dapat dilanjutkan ke desain UI dengan kontrol wajib pada [architecture.md](architecture.md). Belum ada dasar menyatakan aplikasi aman atau siap menerima laporan instansi.**

Pembaruan 4 November 2026: pengguna menerima UI sebagai baseline fix untuk mulai backend M1 di chat baru, dengan perbaikan visual berikutnya tetap boleh. Gate UI terpenuhi; hasil review keamanan tidak berubah dan seluruh pemeriksaan runtime masih BELUM DIUJI.

Desain sebelumnya berpusat pada satu analis lokal. Penambahan login bug hunter/admin, chat dan akses internal menimbulkan batas baru yang sebelumnya belum cukup tertulis. Review ini memperbaiki spesifikasi; tidak membuktikan kontrol sudah bekerja. Keamanan runtime harus diuji pada milestone terkait sebelum validasi dibuka kepada pengguna lain.

Pengguna menyatakan pendaftaran program telah diterima. Ini bukan bukti aplikasi lolos penjurian akhir atau telah diadopsi instansi.

## 2. Aset dan batas kepercayaan

- Laporan/chat/lampiran milik pelapor, termasuk input berbahaya yang sengaja dikirim.
- Scope terstruktur aktif dan binding aset ke portal internal milik operator.
- Session, membership, credential target dan key provider.
- Evidence internal, assessment mentah, hasil yang dipublikasikan dan ledger biaya.
- GT, kondisi rentan/perbaikan dan reset evaluator yang tidak boleh diketahui agent.

Browser pengguna -> API berotorisasi -> intake tanpa tools target -> scope gate -> job terikat izin -> policy per tindakan -> worker terbatas -> portal Docker yang sudah berjalan. Provider model eksternal hanya menerima context sintetis minimum teredaksi; bukan bagian dari jaringan target. Target rentan juga diperlakukan sebagai sumber berbahaya, bukan layanan tepercaya.

## 3. Temuan desain dan perbaikannya

Prioritas di bawah adalah prioritas implementasi, bukan skor CVSS atau bukti eksploitasi.

| ID | Prioritas | Kekurangan rancangan lama / risiko | Keputusan kontrak terbaru |
| --- | --- | --- | --- |
| A01 | Wajib sebelum akses user lain | Satu analis tidak mendefinisikan kepemilikan objek; laporan/evidence bisa terbuka antaruser | Session + membership + program + ownership diperiksa pada setiap route, polling, lampiran, evidence dan ekspor; default tolak |
| A02 | Wajib sebelum worker | Scope dapat ditafsirkan sebagai teks chat/upload atau keputusan model | Guideline terpisah milik admin, draf -> review -> aktivasi terstruktur; mapping origin ditetapkan operator; LLM tidak memberi izin |
| A03 | Wajib sebelum worker | In-scope saja tidak cukup; model dapat mengusulkan host/redirect lain | Intake tanpa koneksi target; job hanya setelah izin/prasyarat/capability lolos; policy + egress aktual per tindakan |
| A04 | Wajib sebelum berbagi hasil | Evidence internal mungkin terbuka melalui detail/export/HTML | Projection server; screenshot/DOM internal hanya admin; bukti pelapor tersanitasi dan dipublikasikan setelah review; semua tampilan inert |
| A05 | Wajib sebelum live | Chat, retry, double-click dan antrean bisa menghabiskan budget | Snapshot, idempotency, satu job aktif, quota, cap token dan reservasi biaya atomik pada ledger global |
| A06 | Wajib sebelum worker | Scope berubah atau cancel tetapi job lama tetap jalan | Pin versi; cek pencabutan sebelum tiap tindakan; cancel queued job dan hentikan I/O aktif; tidak auto-resume setelah crash |
| A07 | Wajib sebelum upload | File/path/tautan dapat menjadi parser attack, stored XSS atau SSRF | TXT/MD UTF-8 inert dengan batas; storage privat nama acak; tidak mengambil URL/memuat media eksternal; tidak menjalankan lampiran |
| A08 | Wajib sebelum browser | Portal XSS atau file upload menyerang UI/worker, bukan hanya menjadi objek uji | Browser/session target terpisah dari platform; sandbox tetap aktif; tanpa privileged/host mount/secret; target dan worker tanpa internet bebas |
| A09 | Wajib sebelum login publik | Role bisa dipilih client atau session bocor/CSRF | Akun demo disiapkan operator; role dari server; cookie/session, expiry/revoke, CSRF, origin check dan rate limit |
| A10 | Wajib sebelum klaim penggunaan instansi | API eksternal menerima informasi internal | MVP hanya data sintetis teredaksi; tidak mengklaim siap data rahasia/offline/production |

Prompt injection tidak dianggap selesai dengan menyaring kata tertentu. Model tetap dapat salah menafsirkan data. Target desainnya: instruksi berbahaya tidak memperoleh izin, jaringan, secret atau tools tambahan; verifier juga menolak klaim bukti yang tidak tersimpan.

## 4. Matriks izin platform

Semua izin mensyaratkan membership program aktif; report/run/evidence harus berada pada program tersebut.

| Tindakan | Bug hunter | Admin program | Operator/evaluator |
| --- | --- | --- | --- |
| Chat/upload report dan mulai run | Milik sendiri | Milik sendiri; dapat memulai ulang report program dengan audit | Runner eksperimen terpisah |
| Baca report/chat/status | Milik sendiri | Seluruh report program | Akses development terkendali |
| Baca hasil teknis tersanitasi | Milik sendiri | Seluruh report program | Sesuai kebutuhan evaluasi |
| Evidence internal/redaksi saat capture | Tidak | Ya, programnya | Evaluasi terpisah |
| Baca guideline publik aktif | Ya | Ya | Ya |
| Ubah/aktifkan guideline | Tidak | Ya, hanya binding yang sudah terdaftar | Menyiapkan binding |
| Review/koreksi/publikasi hasil | Tidak | Ya | Tidak mengubah hasil mentah benchmark |
| Ganti role/binding target | Tidak | Tidak melalui UI program | Operator; bukan tool model |
| GT/reset/kondisi target | Tidak | Tidak melalui UI program | Ya, di luar runtime agent |

## 5. Pemeriksaan wajib saat implementasi

Tidak menambah test suite aplikasi pada tahap dokumentasi ini. Tabel berikut adalah acceptance criteria yang harus dibuktikan menggunakan aplikasi/worker aktual nanti, bukan tes yang dinyatakan lulus.

| ID tes | Skenario dan hasil wajib | Tahap | Status |
| --- | --- | --- | --- |
| AUTH-01 | Hunter A tidak bisa membaca/mengubah chat/report/run/attachment/evidence/export Hunter B, meski ID diketahui | M1/M3 | BELUM DIUJI |
| AUTH-02 | Manipulasi role/program/body/query atau purpose lampiran tidak mendapat hak admin; session kedaluwarsa/revoked ditolak | M1 | BELUM DIUJI |
| AUTH-03 | POST tanpa CSRF/origin sah ditolak; login dibatasi; logout mencabut session | M1 | BELUM DIUJI |
| SCOPE-01 | OOS, UNKNOWN, scope kosong, unsupported dan prasyarat kurang tidak membuat worker job; counter request target nol | M1/M3 | BELUM DIUJI |
| SCOPE-02 | Scope palsu dalam report/guideline hunter dan klaim model IN_SCOPE tidak mengubah policy; admin hanya bisa aktivasi binding sah | M1/M3 | BELUM DIUJI |
| SCOPE-03 | Perubahan versi/cabut izin membatalkan antrean dan menghentikan run aktif; bukti lama tetap memakai snapshot lama | M3 | BELUM DIUJI |
| NET-01 | HTTP redirect, URL absolut, encoded path, DNS berbeda, metadata dan host laptop di luar binding tidak menghasilkan koneksi | M2/M3 | BELUM DIUJI |
| NET-02 | Browser popup/subresource/WebSocket/service worker/download tidak keluar jaringan yang diizinkan; session akun/run terisolasi | M4 | BELUM DIUJI |
| NET-03 | Worker dan target tidak dapat mengakses provider, GT, reset/control plane, Docker socket atau key; hanya jalur job sempit diizinkan | M2/M4 | BELUM DIUJI |
| DATA-01 | HTML/report/response/filename tidak aktif di UI; lampiran oversized/non-UTF8/path traversal ditolak; tidak ada autofetch URL | M1/M3 | BELUM DIUJI |
| DATA-02 | Respons API, polling dan ekspor hunter tidak memuat field internal; cookie/token direduksi saat capture; gambar mentah tidak publik | M3/M4 | BELUM DIUJI |
| AGENT-01 | Instruksi di report/target meminta secret, shell, scope baru atau evidence palsu; tools/policy menolak dan verdict tidak dibuat dari narasi | M3/M8 | BELUM DIUJI |
| LIMIT-01 | Double-submit/concurrent start hanya satu job/reservasi; chat, retry dan benchmark berbagi ledger; budget/timeout/cancel mencegah kerja lanjutan | M1/M3/M8 | BELUM DIUJI |
| VERDICT-01 | Bukti dampak+kontrol diperlukan untuk CONFIRMED; timeout/refusal bukan REFUTED; multi-claim tidak disamaratakan | M3-M6/M8 | BELUM DIUJI |
| RUN-01 | Crash/lease habis/ack mutasi hilang tidak memutar ulang aksi; target dirty memblok run berikutnya sampai reset evaluator; queued job diperiksa ulang | M2/M3 | BELUM DIUJI |
| STORE-01 | Outbox salah run/action, file parsial/symlink, capture oversized dan disk penuh ditolak tanpa membuat evidence/verdict palsu atau menghapus hasil lama | M1-M4 | BELUM DIUJI |
| PROVIDER-01 | Cadangan hanya allowlist operator; cap/ledger/deadline tidak direset; quota habis tidak beralih paid; refusal/config error tidak fallback; sesudah respons pertama model terkunci; benchmark menolak routing/pergantian diam-diam | M1/M8 | BELUM DIUJI |

Sebelum M3 membuka worker lewat UI, AUTH, SCOPE, NET-01/03, DATA dan LIMIT yang relevan harus lulus. Sebelum M4 membuka browser, NET-02/03 dan isolasi artefak browser harus lulus. Mock hanya memeriksa alur, bukan membuktikan model tahan prompt injection atau jaringan benar-benar terisolasi. Simpan hasil aktual dan kekurangan, termasuk pengujian yang gagal.

RUN-01/STORE-01 mengikuti [kontrak runtime](runtime.md). Pengiriman job melalui volume bukan bukti isolasi atau jaminan exactly-once; batas crash/ack harus dibuktikan, dan hasil ambigu tetap ambigu.

## 6. Batas review dan beban pengerjaan

Review ini tidak mencakup audit dependency, runtime Docker/browser, implementasi auth, pemindaian jaringan, provider live atau deployment publik karena komponen tersebut belum ada/diuji. Rancangan satu program dan akun demo mengurangi kompleksitas, tetapi dua role, scope versioning dan evidence projection tetap menambah pekerjaan terhadap estimasi 30 jam. Dahulukan satu alur BAC dan gate keamanan; hindari SSO, multi-tenant, realtime streaming dan dashboard statistik besar.

## 7. Rujukan primer

Sumber diperiksa 3 November 2026; menjadi dasar umum, bukan sertifikasi implementasi proyek.

- [OWASP Authorization](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html): dasar review izin per request dan least privilege.
- [OWASP LLM Prompt Injection Prevention](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html): pemisahan kontrol izin dari model dan validasi tools.
- [OWASP SSRF Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html): dasar pembatasan tujuan dan redirect.
- [OWASP File Upload](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html): dasar pembatasan file dan penyimpanan privat.
- [OWASP Session Management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html) dan [CSRF Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html): dasar session dan mutasi terautentikasi.
