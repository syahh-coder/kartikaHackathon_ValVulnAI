# Hasil M3 lokal - 5 November 2026

**M3 selesai teknis lokal.** Lingkup: alur BAC-08 development dari chat/snapshot ke policy, worker HTTP, evidence, verifier serta review/publikasi admin. Planner deterministik berlabel **mock**; request HTTP ke lab aktual. Ini bukan hasil model live, dataset utama, GT manusia atau benchmark.

## Pemeriksaan

- Suite awal: 123 tes lulus dalam 123,81 detik. Regresi M3: 14 tes lulus dalam 54,35 detik. Suite kumulatif akhir sesudah publikasi bukti tersanitasi: **125 passed in 218.43s**, tanpa skip. Suite sebelumnya juga 125 lulus dalam 149,39 detik; variasi waktu bukan benchmark kinerja.
- Docker API: kondisi rentan **CONFIRMED**, kondisi perbaikan **REFUTED**, masing-masing tujuh evidence/14 request. Idempotency, akses silang, review/publikasi/ekspor lulus. OOS/UNKNOWN menghasilkan nol request aktual berdasarkan log lab. Cancel sesudah commit mutasi objek kontrol mempertahankan tiga evidence tanpa melanjutkan DELETE objek korban.
- Browser Chromium host **156.0.8078.4**: login/chat/upload/snapshot/worker/review/ekspor lulus, termasuk report/response inert, draft server sesudah reload, teks belum dikirim saat navigasi, tema/modal, sidebar mobile dan viewport 320/390/768/1366/1440 tanpa horizontal overflow. Tiga screenshot, nol page error dan nol request eksternal.
- Regresi browser: respons pembuatan percakapan yang ditahan tidak menimpa pilihan terbaru; polling usang ditolak; respons evidence admin yang ditahan melewati logout/login hunter tidak membuka panel atau mengisi DOM. Panel privat dibersihkan saat logout. Pemeriksaan terakhir memakai run selesai, nol run/request target baru.
- Publikasi akhir pada dua run Docker yang sudah selesai: ringkasan kontrol/dampak tanpa identitas/objek privat tersedia bagi hunter; raw assessment tetap identik. Nol run/request target tambahan.
- Build ulang app Docker berhasil tanpa menghapus volume. Sintaks JavaScript, `pip check` host dan `git diff --check` lulus.
- Pemeriksaan dokumentasi: 26 Markdown, 183 link lokal dan fence lulus. Riwayat M1/M2 tetap diberi konteks tahapnya; checkpoint/handoff terbaru menunjuk M4.

## Perilaku yang tersedia

Login memakai session/CSRF dan role membership server. UI Jinja2/JavaScript memakai API aktual, tanpa pemilih role atau skenario fixture produk. Kirim menyimpan draf; Validasi mengunci revisi dan memulai run eksplisit. Pesan tersimpan dapat dimuat ulang dari backend; teks yang belum dikirim hanya disimpan dalam memori tab per percakapan dan dibersihkan saat logout. Polling berhenti setelah run terminal atau tab tersembunyi. Respons polling yang sudah usang dan respons dari sesi sebelum logout diabaikan.

Satu klaim utama diisi terstruktur pada dialog Validasi: aset, path korban/kontrol dan arah dua akun. Teks bebas atau TXT/MD belum diekstrak model. Planner hanya mendukung penghapusan lampiran lintas akun, satu klaim dan dua objek berbeda. Kategori lain, prasyarat kurang, scope ambigu atau aset di luar scope ditolak sebelum job/akses target.

Urutan tujuh aksi: pemilik membaca objek korban; akun penguji gagal membacanya; akun penguji membaca, menghapus dan memeriksa hilangnya objek sendiri; akun penguji mencoba menghapus objek korban; pemilik memeriksa objek korban sesudahnya. Setiap aksi memakai login target baru, sehingga total **14 request target** pada run lengkap. Kondisi rentan harus menunjukkan dampak hilangnya akses pemilik dan kontrol normal; kondisi perbaikan harus menunjukkan penolakan lintas akun serta objek tetap tersedia bagi pemilik. HTTP 200 saja tidak cukup.

Verifier mengikat observasi tersimpan ke run/action/sequence, akun, objek, snapshot, boot worker, envelope/hash dan kontrol. Evidence tidak lengkap/terpotong, objek tidak cocok atau outcome ambigu tidak membuktikan klaim. Kegagalan worker menghentikan run dengan assessment null. Perubahan scope, pencabutan membership dan cancel diuji pada I/O aktif melalui fixture ASGI; pembatalan setelah commit mutasi juga diuji lewat Docker. Tidak menjanjikan pembatalan mengembalikan mutasi yang sudah terjadi.

Hunter hanya mendapat report/run sendiri. Evidence internal tetap admin. Review menyimpan catatan dan keputusan analis terpisah dari hasil mentah; review ulang menarik publikasi. Publikasi menghasilkan ringkasan teks milik aplikasi sesuai verdict beserta bukti kontrol/dampak yang disamarkan menjadi akun penguji/pemilik dan objek kontrol/laporan, tanpa catatan bebas, alias akun, path, response mentah atau ID evidence. Koreksi analis dibedakan dari observasi verifier. Ekspor memakai projection izin yang sama; lampiran bebas pilihan admin belum tersedia.

## Artefak dan reproduksi

- `tests/test_m3_bac.py`, suite auth/policy/provider/handoff/limit/recovery yang sudah ada.
- `python -m evaluator.m3`: smoke API pada Docker, eksplisit reset lab sintetis, bukan startup normal.
- `node scripts/m3_ui_smoke.cjs`: QA browser host; memakai `VALVULN_PLAYWRIGHT_CORE` dan opsional `VALVULN_CHROMIUM`. Browser host QA tidak dipasang di worker produk.
- `node scripts/m3_ui_session_check.cjs`: sesudah QA utama, memakai run selesai dari artefak QA untuk memeriksa respons bukti admin yang terlambat melewati pergantian login, tanpa reset/run baru.
- Hasil privat lokal `artifacts/m3/api-verification.json`, `ui-verification.json`, `session-verification.json`, `publication-verification.json` dan tiga screenshot; diabaikan Git. Capture evidence tetap pada storage privat app.

Run API rentan: `382a7f5c-433e-4e48-a961-e834c190274e`; perbaikan: `2bc378b7-df1e-4c20-8445-bf40b8ff77d3`; cancel: `f9ed94ec-5d0f-4503-a8cd-454531bea247`. Run UI: `7661cfd9-6e80-4900-988a-80e2d6600370`. Akhir smoke API: worker IDLE, lab fixed/OPERATOR_VERIFIED, tanpa run aktif; app/worker/lab tetap berjalan. Perubahan M1-M3 tetap lokal, tanpa commit/push/release/deployment.

Jalankan saat tidak ada run lain. Runner memakai password demo lokal `.local-data/demo-password.txt`; tidak mencetak password/cookie. Batas tiga start per akun per jam tetap berlaku, termasuk smoke. Tunggu kuota pulih jika sudah digunakan; jangan menghapus rate event, data atau ledger agar tes lolos. Evaluator mengubah/reset lab saja dan mempertahankan riwayat aplikasi.

Pada pemeriksaan akhir, hunter-a dan hunter-b masing-masing sudah memakai tiga start dalam jendela satu jam; admin dua. Validasi baru hunter perlu menunggu kuota pulih. Login, baca hasil/review dan ekspor tetap tersedia. Ini keadaan lokal sesudah smoke, bukan batas baru yang ditambahkan M3.

## Kegagalan yang diperbaiki dan batas

Dua tes pembatalan sempat gagal ketika persiapan/aksi pertama belum mencapai event dalam lima detik. Waktu tunggu persiapan uji dipisah menjadi 15 detik; penghentian tetap wajib dalam lima detik, dan task test dibersihkan pada kegagalan. Deadline aksi/run produk tidak berubah. QA browser sempat gagal karena judul fixture bentrok dengan riwayat, locator tidak cocok dengan JSON ter-escape, serta Escape dikirim sebelum panel async terbuka. Fixture sekarang unik dan menunggu keadaan UI yang benar. QA juga menemukan race navigasi yang benar-benar mengosongkan teks belum dikirim; versi pilihan UI sekarang mengabaikan respons navigasi usang. Tidak menghapus riwayat lama atau melemahkan limit produk agar tes lolos.

Belum tersedia: model live/key/billing, ekstraksi/perencanaan/adaptasi berbasis AI, browser worker, XSS/upload/business logic, 23 titik lab lainnya, 20 laporan berlabel manusia dan benchmark. Pembuktian batas mock bukan bukti ketahanan penalaran model terhadap prompt injection. Langkah berikutnya M4: browser worker dengan pembatasan semua navigasi/subresource, lalu satu XSS development beserta kontrol inert; tidak menambah semua kategori sekaligus.
