# Reset data lab melalui admin

Keputusan terbaru pengguna14 November2026: tambahkan pilihan **Lab rentan / Lab kontrol diperbaiki** agar laporan yang sama bisa dibandingkan pada dua kondisi target. Ini menggantikan batas vulnerable-only pada versi awal tombol. Mode fixed adalah konfigurasi kontrol negatif yang sudah disiapkan, bukan kemampuan AI memperbaiki celah. Tidak menambah fitur remediasi otomatis.

## Penggunaan dan kontrak FE

Login sebagai admin program, buka **Reset data lab**, pilih kondisi target lalu klik **Terapkan kondisi & reset data lab**. Tunggu status lab siap dan periksa kondisi terpasang/cakupan ALL_IMPLEMENTED sebelum memulai validasi. Hunter tidak mempunyai tombol/hak reset. Port8001 target worker yang sama; untuk uji manual klik **Aktifkan pengujian manual** lalu tautan lab. Pilihan vulnerable/fixed sekarang mengatur13 titik existing BAC-08/XSS-01..08/UP-01..04. Ini memperbaiki cakupan awal hanya3 titik produk. Validasi otomatis tetap BAC-08/XSS-08/UP-04. Label fixed tidak berarti seluruh aplikasi telah dinyatakan aman.

- `GET /api/programs/{program_id}/lab-reset`: status reset terakhir, configured, target.ready/dirty/maintenance/snapshot_id, condition/coverage permintaan, applied_condition/applied_coverage yang terikat snapshot sukses, available_conditions dan ID objek baru. Cakupan baru ALL_IMPLEMENTED; reset lama tanpa coverage tidak dianggap mencakup13 titik dan UI meminta terapkan ulang. Mode yang tidak cocok snapshot menghasilkan applied_condition null.
- `POST /api/programs/{program_id}/lab-reset`: body `{"confirm":"RESET_DEMO_LAB","condition":"vulnerable"}` atau condition `fixed`; memakai session, Origin dan X-CSRF-Token yang sama dengan API produk. Balasan202 dengan request_id/status RUNNING/condition.
- Kompatibilitas: `{"confirm":"RESET_VULNERABLE_DEMO"}` tetap berarti vulnerable. Konfirmasi lama dengan condition fixed ditolak; mode kontrol membutuhkan konfirmasi baru. Field command/path dan condition lain ditolak schema.
- Poll GET sampai SUCCEEDED/FAILED. RUN_ACTIVE/WORKER_BUSY menolak reset tanpa mutasi; RESET_BUSY menolak permintaan bersamaan. Kegagalan/hasil ambigu menjaga target maintenance/dirty. Jangan retry otomatis.
- Operasi reset data/konfigurasi13 titik lab existing dengan dua nilai enum. Tidak menambah titik/validator otomatis baru. Laporan, scope, evidence, review dan ledger tetap tersimpan. Path BAC/upload perlu ID baru setelah reset. Reset tidak membuat run, assessment, verdict atau inferensi AI.
- `POST /api/programs/{program_id}/lab-manual-session` dengan body `{"confirm":"OPEN_SHARED_MANUAL_LAB"}`: admin/CSRF dan idle guard, aktifkan maintenance sebelum memberi sesi manual1jam terikat snapshot. Tidak reset data/kondisi. GET lab-reset menambah manual_available/manual_active/manual_url. Selama sesi manual agent ditolak TARGET_DIRTY; reset mencabut akses manual sebelum seed dan menunggu handler manual selesai.

## Alur video dengan laporan yang sama

1. Gunakan laporan XSS-08 yang memang mengklaim eksekusi marker melalui fragment pada `/notifications/preview`, dengan dua akun uji. Laporan teks inert yang sengaja salah bukan pengganti klaim ini.
2. Pilih Lab rentan, terapkan/reset, lalu pengguna menjalankan validasi laporan. Jika bukti dan kontrol lengkap, hasil yang diharapkan CONFIRMED.
3. Sebagai admin, pilih Lab kontrol diperbaiki dan terapkan/reset. Jalankan kembali laporan/claim XSS yang sama; triage yang masih current dapat dipakai tanpa inferensi ulang. Dengan marker tampil sebagai teks dan kontrol berhasil, hasil yang diharapkan REFUTED untuk fixture ini.
4. Tampilkan perbedaan bukti dan batas klaim. Mode dipilih operator untuk mengubah target, bukan mengisi jawaban model/verifier. Verifier existing tetap menilai observasi; timeout atau kontrol gagal tidak otomatis REFUTED. Setelah demo, pilih kondisi yang diinginkan untuk sesi berikutnya.

Reset mengganti ID objek: untuk BAC/upload, perbarui binding objek di laporan ke snapshot baru. XSS memakai path tetap sehingga paling praktis untuk demo laporan identik. Ini demonstrasi mekanisme yang dikenal, bukan metrik kemampuan menilai semua laporan palsu/benar.

## Jalur internal

Tiga container tetap app/worker/lab. Volume lab_control hanya pada app/lab. Port host127.0.0.1:8001 kini dipublikasikan dari target asli lewat network lab_manual_access; firewall egress/forward tetap ditolak. Tidak menambah jaringan app-ke-target, Docker socket, model tool atau shell dari report. Konfigurasi app VALVULN_SHARED_LAB_MANUAL dan lab LAB_SHARED_MANUAL/LAB_MANUAL_ORIGIN mengaktifkan sesi manual bersama; tanpa konfigurasi itu API manual gagal tertutup. Salinan lama dipertahankan berhenti dengan compose opsional8002. [Operasi manual](manual-lab.md).

App memeriksa membership admin/CSRF dan idle, memasang maintenance melalui operator existing, menyimpan mode/cakupan pada status dan menulis request UUID berumur maksimal30 detik ke mailbox privat. Consumer memindahkan request menjadi claimed sebelum mutasi, membuat backup SQLite, reset all_supported13 titik ke enum yang dipilih, memeriksa seed/health lalu mengembalikan snapshot, condition dan coverage ALL_IMPLEMENTED. App memeriksa condition dan coverage sebelum ack worker. Reset evaluator individual lama tetap sempit secara default; helper reset demo operator kini eksplisit --all-supported. JSON dibatasi ukuran/schema/nama/expiry; input report tidak digunakan. Duplikat/result existing tidak diputar ulang, claimed pasca-crash tetap UNKNOWN. Tidak ada reset saat startup atau jawaban mode ke model/verifier.

Status aplikasi tersimpan di app_data/lab-reset/status.json; mailbox dan backup memerlukan pengelolaan disk operator jika dipakai berulang dalam waktu panjang. Backup tidak dibagikan pada UI. Startup normal tetap `docker compose up -d --build` setelah setup existing.

## Verifikasi

### Cakupan seluruh titik existing, 14 November 2026

23 tes terarah lulus dalam27,45detik: reset13 flag pada kedua mode, kegagalan health/mode/coverage tetap terkunci, sesi manual bersama, serta reset evaluator individual tetap sempit. CI menyertakan tes cakupan baru. Artefak `artifacts/all-lab-points-20261114/targeted.xml`.

App/lab diperbarui setelah backup/maintenance pada volume existing; worker tidak diganti. Smoke Chromium melalui tombol admin menerapkan fixed lalu vulnerable dengan coverage ALL_IMPLEMENTED dan seluruh13 flag cocok. Login manual pada port8001 membaca snapshot yang sama. GET pencarian katalog memakai teks inert `Kontrol < 2`: viewer result melakukan escaping pada fixed dan memakai sink HTML pada vulnerable, sedangkan view=text tetap escaped pada kedua mode. Tidak menjalankan payload executable atau menguji ulang exploit13 titik; ini verifikasi konfigurasi/routing/escaping, bukan GT atau benchmark.

Kondisi akhir vulnerable dengan sesi manual aktif; target maintenance/dirty selama sesi itu dan worker IDLE/snapshot sinkron. Reset diperlukan untuk mengakhiri akses manual sebelum validasi otomatis.14 tabel aplikasi, termasuk68 baris ledger, identik terhadap backup sebelum deploy memakai metode count/hash yang sama pada kedua DB. Perbandingan awal dengan hash JSON lama tidak cocok karena serialisasi berbeda; perbandingan langsung backup/live menyelesaikannya tanpa mutasi data. Artefak privat `ui-smoke.json`, `preservation.json`, screenshot dan rekaman harness berada pada folder yang sama. Tidak ada inferensi model, push atau release pada batch ini.

### Riwayat dua mode dengan cakupan tiga titik

Versi dua mode:18 tes terarah lulus dalam17,36detik pada database sementara, termasuk vulnerable/fixed, health gagal pada kedua mode, balasan mode berbeda tetap terkunci, kompatibilitas lama, role/CSRF dan anti-replay. Artefak `artifacts/lab-modes-ui-20261114/targeted.xml`.

Smoke Chromium pada UI8000 berhasil menerapkan fixed lalu vulnerable. Setiap tahap mencapai SUCCEEDED dan flag DB aktual cocok untuk BAC-08/XSS-08/UP-04; snapshot backend/lab cocok. Hunter tidak melihat tombol dan API403. Screenshot1366/390px tanpa overflow, kondisi akhir vulnerable/ready/dirty=false dan worker IDLE dengan snapshot sinkron.14 tabel yang diperiksa termasuk68 baris ledger identik sebelum/sesudah; audit/login/binding/status reset berubah sesuai operasi. Tidak menjalankan exploit, verifikasi kerentanan baru atau inferensi model; perbedaan verdict belum diuji ulang pada batch tombol ini.

Artefak privat pada `artifacts/lab-modes-ui-20261114/`: targeted.xml, ui-smoke.json, screenshot, before.json dan preservation.json. Percobaan UI awal menghitung opsi sebelum panel async selesai dimuat dan gagal sebelum reset; retest menunggu elemen terlihat, rekaman kegagalan dipertahankan di ui-initial-failure.txt. OpenAPI diperbarui untuk FE. Perubahan belum di-push/rilis; source arsip review-v6 tetap baseline lama.

### Riwayat versi vulnerable-only

19 tes unik terarah mempunyai hasil terakhir lulus: izin/CSRF, schema tetap, tidak terkonfigurasi, worker sibuk, mailbox sukses/gagal health, duplikasi, expiry, no replay dan readiness/manual-access terkait. Run awal19 lulus10,56detik; subset11 lulus8,66detik setelah guard duplikasi ditambahkan. Tes menggunakan database sementara, bukan GT/model/benchmark.

Smoke Chromium pada app8000 sukses: hunter tidak melihat tombol dan API403; admin klik reset dan mencapai SUCCEEDED. Screenshot1366/390px tanpa overflow. Percobaan selector awal gagal sebelum aksi karena encoding teks tombol pada stdin; diperbaiki menjadi selector stabil, rekaman kegagalan dipertahankan. App/lab diperbarui pada volume existing setelah backup dan nol job aktif.14 tabel yang diperiksa termasuk66 baris ledger mempunyai count/hash sama sebelum/sesudah. Target ready/dirty=0/maintenance=0, worker IDLE/dirty=false dan snapshot app-worker-lab sinkron; ketiga kondisi rentan diperiksa aktif. Audit/login/binding berubah sesuai operasi. Tidak menjalankan exploit/validasi kerentanan atau inferensi model.

Artefak privat: `artifacts/lab-reset-ui-20261114/targeted.xml`, `retest.xml`, `ui-smoke.json`, `ui-initial-failure.txt`, screenshot, `before.json` dan `preservation.json`. Source arsip review-v6 belum diperbarui; perubahan ini belum di-push/rilis.
