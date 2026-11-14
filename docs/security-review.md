# Review keamanan arsitektur

**Cakupan reset14 November2026:** enum mode kini diterapkan pada13 titik existing; tidak memperluas worker/tools otomatis. App mensyaratkan coverage ALL_IMPLEMENTED dan mode cocok sebelum ack, hasil consumer lama gagal tertutup.23 tes terarah serta smoke konfigurasi/escaping dua mode lulus; payload exploit tidak dijalankan. [Kontrak/bukti](lab-reset-ui.md).

**Akses manual bersama14 November2026:** pengguna mengotorisasi hostloopback8001 pada target worker yang sama. Admin/CSRF/idle memasang maintenance sebelum sesi manual snapshot-bound dibuka; sesi kedaluwarsa tidak membuka validasi otomatis. Reset mencabut sesi dan menunggu handler manual di lock yang sama sebelum mutasi. SourceIP worker tetap membedakan jalur internal, tidak percaya Host/Origin sebagai identitas worker.28 tes terarah lulus; smoke dua mode membuktikan snapshot/objek sama, sink HTML/teks sesuai konfigurasi tanpa payload uji. Egress lab tetap diblok; tidak ada model/key/appDB/Docker socket pada lab. [Kontrak dan bukti](manual-lab.md).

**Perluasan dua mode14 November2026:** pengguna menyetujui enum vulnerable/fixed di reset admin.18 tes terarah lulus; mode balasan yang berbeda gagal tertutup, input bebas tetap ditolak, konfirmasi lama hanya vulnerable. Mode disimpan pada jalur kontrol/status admin, tidak dimasukkan ke input model dan tidak mengubah verifier. Guard reset sebelumnya tetap berlaku. [Kontrak aktif](lab-reset-ui.md); paragraf vulnerable-only berikut adalah riwayat versi awal.

**Pengecualian reset UI14 November2026:** atas permintaan pengguna, admin program dapat reset data lab demo ke kondisi rentan tetap; larangan admin reset pada desain historis digantikan hanya untuk operasi ini. Role/CSRF, konfirmasi schema, idle, maintenance, mailbox privat app-lab, expiry, anti-duplikasi/no replay, health dan ack snapshot diuji terarah. Hunter ditolak403. Tidak ada tool reset pada model/worker, API reset HTTP pada lab, Docker socket atau akses jaringan baru app-ke-target.19 tes unik lulus dan satu klik UI reset sukses pada runtime; bukan audit keamanan menyeluruh atau bukti exploit/model/GT. [Kontrak](lab-reset-ui.md).

**Tambahan rencana 7 November 2026:** [R1 triage teks](execution-prompt.md) harus diuji terhadap ownership/session, output schema, instruksi dalam report, mode live tanpa key, cancel/time/token/retry/ledger dan redaksi error/secret. Saran model tidak mengubah scope/izin/verdict; jumlah job/action/request target dari jalur triage wajib nol. Konteks tidak memuat GT/katalog/source jawaban. Ini acceptance criteria baru yang **belum diuji**, bukan kelulusan runtime dari dokumen. Perluasan agent/tools pada desain lama menjadi backlog sesuai [scope](submission-scope.md).

**M6b, 6 November 2026:** 145 tes terarah lulus untuk konteks aturan versi run pada simulasi tanpa tool, regresi scope/ownership, kontrol bisnis dan gate katalog. Konteks menolak LAB/live/replay; report tidak menjadi aturan dan hash internal tidak masuk projection hunter. Dua container/volume khusus mempertahankan state dan fulfillment; cleanup prefix/label diperiksa dan lulus. Ini bukan verifikasi business logic melalui worker atau model live. Katalog tetap 13 reproduksi historis/11 planned dengan konflik grouping sehingga gate exit 2; M6 belum lulus. [Hasil M6b](m6b-verification.md).

**M6a, 6 November 2026:** kontrol bisnis aman diuji terarah: batas pemilik/unit, self-approval, strict quantity/version, transisi, idempotensi, stok, rollback jurnal, batas data dan migrasi/persistensi. Setup operator memvalidasi identitas database read-only sebelum migrasi dan menolak path aplikasi/missing DB tanpa perubahan schema. Aturan tersedia sebagai data publik autentikasi; BUSINESS_LOGIC tetap UNSUPPORTED pada validator produk. Host dan container disposable non-root/read-only/network none lulus; service persisten, alur worker, kondisi kerentanan BL/BAC tambahan dan model belum diverifikasi. [Batas M6a](m6a-verification.md).

**Pembaruan M5, audit 6 November 2026:** empat titik upload/delapan kondisi memiliki bukti runtime 5 November. Audit offline 120 hash source/18 PNG, 15 regresi defensif M5 dan 12 tes auditor serta QA UI ulang lulus. Upload produk hanya fixture terdaftar, tanpa isi/nama/script bebas dari laporan. Scope POST dan kontrol label diwajibkan sebelum transport; bukti/verdict hilang/rusak ditolak, cancel/recovery tidak replay. Bukti raw admin inert dan ekspor hunter diuji. Satu percobaan QA unduhan dibatalkan, pengulangan lulus; penyebab belum pasti. Ini tidak memverifikasi provider live atau general upload/browser. [Hasil dan batas M5](m5-verification.md).

**Pembaruan M4c, 5 November 2026:** M4 selesai teknis lokal; tujuh fitur XSS tambahan lulus Chromium dua kondisi/kontrol dan 180 tes host. Stored XSS memakai writer/pembaca berbeda; mutasi memeriksa CSRF/ownership dan review memerlukan penugasan. [Bukti/batas M4c](m4c-verification.md). Tool/planner/UI produk tetap XSS-08; reproduksi fitur baru merupakan operasi evaluator saat maintenance. Model live/GT manusia/benchmark masih pending. Regresi jaringan XSS-08 pada lab baru lulus: lima request, WS/popup/download terlarang diblokir, hanya empat request login/preview dan nol Chromium.

Tanggal: 3 November 2026. Lingkup: review dokumen dan trust boundary, bukan pentest aplikasi. Prototipe UI simulasi kini tersedia dan diperiksa terpisah pada [ui-review.md](ui-review.md). M1 fondasi backend, auth/ownership dan container app sudah diuji lokal pada 4 November 2026. M2 worker HTTP/lab BAC-08, handoff, isolasi namespace dan crash mutasi sudah diuji operator. M3 UI chat/API/BAC verifier kini diuji lokal dengan planner mock; M4a browser sandbox/XSS-08 development kini diuji operator beserta network/cancel dan UI evidence. Workflow XSS-08 dan publikasi M4b kini diuji lokal; model live belum diuji. [Hasil M4a](m4-verification.md); [Hasil M3](m3-verification.md); [hasil M2](m2-verification.md). Status per baris di bawah membedakan hasil M1 dari tahap lanjutan; [hasil rinci M1](m1-verification.md).

## 1. Keputusan review

**Rancangan dapat dilanjutkan ke desain UI dengan kontrol wajib pada [architecture.md](architecture.md). Belum ada dasar menyatakan aplikasi aman atau siap menerima laporan instansi.**

Pembaruan 4 November 2026: pengguna menerima UI sebagai baseline fix untuk mulai backend M1 di chat baru, dengan perbaikan visual berikutnya tetap boleh. Gate UI terpenuhi; hasil review desain tetap berlaku. Setelah eksekusi M1, 86 tes fondasi serta Docker smoke/persistensi lulus; belum membuktikan keamanan worker/model live.

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

Tabel awal merupakan acceptance criteria desain. Pengujian M1 sudah dijalankan dengan app aktual/ASGI, respons provider simulasi dan smoke Docker; bagian yang membutuhkan UI/worker/live tetap belum diuji.

| ID tes | Skenario dan hasil wajib | Tahap | Status |
| --- | --- | --- | --- |
| AUTH-01 | Hunter A tidak bisa membaca/mengubah chat/report/run/attachment/evidence/export Hunter B, meski ID diketahui | M1/M3 | LULUS M1/M3 API serta projection/publikasi/ekspor dan UI dua role; suite akses silang lulus |
| AUTH-02 | Manipulasi role/program/body/query atau purpose lampiran tidak mendapat hak admin; session kedaluwarsa/revoked ditolak | M1 | LULUS M1 (role, membership, expiry/revoke, field tambahan) |
| AUTH-03 | POST tanpa CSRF/origin sah ditolak; login dibatasi; logout mencabut session | M1 | LULUS M1 (CSRF/origin/login limit/logout) |
| SCOPE-01 | OOS, UNKNOWN, scope kosong, unsupported dan prasyarat kurang tidak membuat worker job; counter request target nol | M1/M3 | LULUS M3: OOS/UNKNOWN nol request aktual pada log lab Docker; unsupported/prasyarat/multi-claim nol job melalui fixture ASGI |
| SCOPE-02 | Scope palsu dalam report/guideline hunter dan klaim model IN_SCOPE tidak mengubah policy; admin hanya bisa aktivasi binding sah | M1/M3 | LULUS M1 binding/gate dan M3 policy worker; penalaran model live belum diuji M8 |
| SCOPE-03 | Perubahan versi/cabut izin membatalkan antrean dan menghentikan run aktif; bukti lama tetap memakai snapshot lama | M3 | LULUS M3 scope/membership/cancel pada I/O aktif via ASGI; cancel setelah commit mutasi diuji Docker; snapshot lama tetap tersimpan |
| NET-01 | HTTP redirect, URL absolut, encoded path, DNS berbeda, metadata dan host laptop di luar binding tidak menghasilkan koneksi | M2/M3 | LULUS M2 HTTP dan M4a satu dokumen browser termediiasi IP literal; redirect/subresource/popup di luar profil ditolak; general browser tetap pending |
| NET-02 | Browser popup/subresource/WebSocket/service worker/download tidak keluar jaringan yang diizinkan; session akun/run terisolasi | M4 | LULUS M4a profil notification_probe: request/WS/popup/download diblokir, context/storage baru. Service workers block; origin HTTP lab bukan secure context. General browsing/HTTPS belum diuji |
| NET-03 | Worker dan target tidak dapat mengakses provider, GT, reset/control plane, Docker socket atau key; hanya jalur job sempit diizinkan | M2/M4 | LULUS M2 dan probe ulang M4a: egress/mount/UID/capability, sandbox namespace+Seccomp Chromium aktif. Hanya profil operator lokal ini, bukan sertifikasi sandbox umum |
| DATA-01 | HTML/report/response/filename tidak aktif di UI; lampiran oversized/non-UTF8/path traversal ditolak; tidak ada autofetch URL | M1/M3 | LULUS M1 upload/batas dan M3 Chromium host: report/response inert, tanpa request eksternal; browser worker tetap M4 |
| DATA-02 | Respons API, polling dan ekspor hunter tidak memuat field internal; cookie/token direduksi saat capture; gambar mentah tidak publik | M3/M4 | LULUS M3 projection/publikasi dan M4a capture BROWSER_PROBE/PNG privat admin, JSON inert pada UI aktual; hunter ditolak. LULUS M4b review/publikasi/ekspor ringkasan XSS milik hunter, raw tetap privat |
| AGENT-01 | Instruksi di report/target meminta secret, shell, scope baru atau evidence palsu; tools/policy menolak dan verdict tidak dibuat dari narasi | M3/M8 | BATAS MOCK M3: planner sempit/verifier/provenance dan tools terstruktur diuji; penalaran/injeksi prompt model live BELUM DIUJI M8 |
| LIMIT-01 | Double-submit/concurrent start hanya satu job/reservasi; chat, retry dan benchmark berbagi ledger; budget/timeout/cancel mencegah kerja lanjutan | M1/M3/M8 | LULUS M1/M3 idempotency/queue/budget simulasi dan cancel aktif; kuota start tetap berlaku pada smoke. Provider live M8 belum diuji |
| VERDICT-01 | Bukti dampak+kontrol diperlukan untuk CONFIRMED; timeout/refusal bukan REFUTED; multi-claim tidak disamaratakan | M3-M6/M8 | LULUS M3 BAC dan M4a pasangan kontrol/marker XSS operator, nonce/frame/origin/screenshot; LULUS M4b workflow/assessment XSS-08 dan penolakan bukti rusak; keluarga lain/live pending |
| RUN-01 | Crash/lease habis/ack mutasi hilang tidak memutar ulang aksi; target dirty memblok run berikutnya sampai reset evaluator; queued job diperiksa ulang | M2/M3 | LULUS M2 HTTP crash/no replay; M4a browser cancel aktual dan recovery unknown/no replay unit. SIGKILL browser aktual belum diuji |
| STORE-01 | Outbox salah run/action, file parsial/symlink, capture oversized dan disk penuh ditolak tanpa membuat evidence/verdict palsu atau menghapus hasil lama | M1-M4 | LULUS M2 HMAC/provenance/limit/symlink; M4a nonce/fixture/hash/capture privat dan UI inert. General browser upload/download artefak belum tersedia |
| PROVIDER-01 | Cadangan hanya allowlist operator; cap/ledger/deadline tidak direset; quota habis tidak beralih paid; refusal/config error tidak fallback; sesudah respons pertama model terkunci; benchmark menolak routing/pergantian diam-diam | M1/M8 | LULUS M1 kontrak simulasi; probe/tools/billing/freeze live M8 belum diuji |

Sebelum M3 membuka worker lewat UI, AUTH, SCOPE, NET-01/03, DATA dan LIMIT yang relevan harus lulus. Sebelum M4 membuka browser, NET-02/03 dan isolasi artefak browser harus lulus. Mock hanya memeriksa alur, bukan membuktikan model tahan prompt injection atau jaringan benar-benar terisolasi. Simpan hasil aktual dan kekurangan, termasuk pengujian yang gagal.

RUN-01/STORE-01 mengikuti [kontrak runtime](runtime.md). Pengiriman job melalui volume bukan bukti isolasi atau jaminan exactly-once; batas crash/ack harus dibuktikan, dan hasil ambigu tetap ambigu.

## 6. Batas review dan beban pengerjaan

Review desain awal tidak menguji runtime. M1 kini menambah pengujian auth/API/app Docker dan inventaris dependensi; audit keamanan dependensi, browser, jaringan worker, provider live serta deployment publik tetap belum dilakukan. Rancangan satu program dan akun demo mengurangi kompleksitas, tetapi dua role, scope versioning dan evidence projection tetap menambah pekerjaan terhadap estimasi 30 jam. Dahulukan satu alur BAC dan gate keamanan; hindari SSO, multi-tenant, realtime streaming dan dashboard statistik besar.

## 7. Rujukan primer

Sumber diperiksa 3 November 2026; menjadi dasar umum, bukan sertifikasi implementasi proyek.

- [OWASP Authorization](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html): dasar review izin per request dan least privilege.
- [OWASP LLM Prompt Injection Prevention](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html): pemisahan kontrol izin dari model dan validasi tools.
- [OWASP SSRF Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html): dasar pembatasan tujuan dan redirect.
- [OWASP File Upload](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html): dasar pembatasan file dan penyimpanan privat.
- [OWASP Session Management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html) dan [CSRF Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html): dasar session dan mutasi terautentikasi.


## Hasil runtime M2

111 tes kumulatif dan reproduksi HTTP operator lulus. NET-01/03 dibuktikan untuk worker HTTP pada Docker Desktop ini, dengan firewall namespace dan proses non-root/capability nol setelah bootstrap. Proxy/DNS dan redirect tidak menjadi jalur tool bebas. Model, browser dan prompt injection aktual belum diuji. Tidak mengklaim semua host atau isolasi sandbox arbitrary code. Hasil, kegagalan awal DNS, batas proses bootstrap dan uji SIGKILL dijelaskan pada [m2-verification.md](m2-verification.md).

## Hasil M4a dan gate berikutnya

145 tes kumulatif lulus. Chromium non-root/sandbox namespace+Seccomp aktif, marker nonce/main frame/origin, perbaikan textContent, dua akun/context baru, network fixture dan cancel aktual diuji. Callback route yang sempat menulis TargetClosedError saat penutupan diperbaiki; pemeriksaan ulang menemukan nol error callback/proses browser. Bukti XSS/screenshot tetap JSON inert khusus admin, diperiksa pada UI aktual. Detail, kegagalan runner awal yang dipertahankan dan batas pengujian di [m4-verification.md](m4-verification.md).

Kelulusan M4a ini hanya untuk notification_probe dengan fixtures tetap, satu GET dokumen termediiasi dan tanpa input script/URL bebas. Workflow/UI assessment XSS-08 dan ringkasan hunter kemudian diuji M4b; tujuh titik lab tambahan kemudian direproduksi operator M4c. General browser tools tetap pending. Tidak meluluskan model live, prompt injection model, arbitrary code sandbox atau data instansi.


## Koreksi cancel M4b

Unroute sebelum context.close terbukti melepas satu GET ulang dan favicon di luar hitungan tool. Routing kini bertahan sampai context tertutup, callback closing ditolak dan route dibatalkan di-abort untuk menyelesaikan future Playwright. Regresi cancel produk menghitung log aktual tanpa request lanjutan; assessment null, dirty gate, nol Chromium. Probe jaringan worker dan QA UI/projection diulang; [hasil dan kegagalan awal](m4b-verification.md). Ini melengkapi NET-02/DATA-02/VERDICT-01 untuk profil fixture sempit, bukan sertifikasi umum sandbox atau penalaran model live.
