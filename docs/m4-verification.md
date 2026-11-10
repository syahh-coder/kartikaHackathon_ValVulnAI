# Hasil M4a lokal - 5 November 2026

**Status terbaru:** M4 ditutup teknis lokal setelah M4c melengkapi tujuh titik XSS/kontrol; [hasil M4c](m4c-verification.md). Catatan M4a di bawah adalah riwayat batch.

**Pembaruan M4b:** integrasi produk tersedia; [hasil terbaru](m4b-verification.md). Dokumen M4a ini riwayat. Tes cancel lama belum menghitung log request setelah cleanup; M4b memperbaiki pelepasan navigasi saat unroute dan future route yang tertinggal, lalu menguji ulang log aktual.

**M4 sebagian: fondasi browser dan XSS-08 development sudah direproduksi operator.** M4 belum selesai seluruhnya. Browser belum terhubung ke workflow assessment/UI validasi XSS; tujuh titik XSS lain belum dibuat. Tidak melanjutkan M5 pada batch ini.

## Hasil aktual

| Pemeriksaan | Hasil |
| --- | --- |
| Suite kumulatif akhir | **145 passed in 105.80s**, tanpa skip. Sebelumnya 58 regresi M2/M3 serta 19 tes awal browser lulus; satu tes recovery tambahan kemudian melengkapi suite |
| Sandbox Chromium | Chromium **156.0.8078.4 / build 1248**, Playwright Python **1.64.1**, Python 3.11. Halaman diagnostik menunjukkan namespace PID/network dan Seccomp-BPF aktif; renderer UID 10001, Seccomp 2, NoNewPrivs 1, tanpa `--no-sandbox` |
| XSS-08 rentan | Dua akun, masing-masing kontrol inert dan fixture marker. Callback nonce unik dari main frame/origin terdaftar diamati; verifier pasangan observasi menghasilkan CONFIRMED |
| Kondisi perbaikan | Fixture marker tampil sebagai teks, tanpa callback; kontrol JavaScript dan rendering tetap berhasil. Kedua akun menghasilkan REFUTED untuk klaim development spesifik ini |
| Request/evidence | Masing-masing kondisi delapan request (empat login + empat dokumen), empat evidence BROWSER_PROBE dan empat PNG terikat action ID |
| Jaringan browser | Lima request terlarang, satu WebSocket, satu popup dan satu download diblokir pada probe keamanan. Log lab hanya berisi login dan preview: empat request untuk dua aksi, tanpa jalur lain |
| Isolasi context | Setiap aksi memakai browser/context baru. Cookie sebelum login kosong; storage diperiksa sebelum script target. Local/session storage yang ditulis fixture sebelumnya tidak terbawa ke context berikutnya |
| Cancel aktual | Cancel melalui API saat navigasi tertahan menghentikan Chromium/context; satu evidence sebelumnya tetap tersimpan, assessment null, nol proses Chromium dan nol error callback worker sesudah perbaikan cleanup |
| Recovery unit | Crash journal browser menghasilkan ACTION_OUTCOME_UNKNOWN, pengiriman identik mengembalikan unknown tanpa transport ulang, dan aksi baru diblokir dirty gate. SIGKILL browser aktual belum diuji; hasil SIGKILL HTTP M2 tetap terpisah |
| NET-03 ulang | Probe jaringan/mount M2 diulang pada worker baru: target positif; metadata/TEST-NET/gateway/app/port lain/DNS/IPv6 ditolak; Python UID 10001, capability nol, NoNewPrivs; app tidak menjangkau lab |
| UI evidence aktual | Admin membuka bukti XSS sebagai teks inert, termasuk HTML dan base64 PNG; tidak membuat node img/script. Hunter ditolak pada evidence/ekspor run admin. Nol page error/request eksternal; tidak membuat run atau request target baru |
| Dependensi | `pip check` worker lulus. Paket worker baru dan 217 paket OS diinventarisasi pada [dependencies-m4.json](dependencies-m4.json); metadata lisensi bukan audit keamanan/legal |

Pemeriksaan penutup: 20 tes kontrak browser lulus dalam 2,67 detik setelah penambahan kasus hash/screenshot/counter; 28 Markdown, 209 link lokal dan fence lulus. Sintaks Python/JavaScript serta `git diff --check` lulus. Perubahan tetap lokal, tanpa commit/push/release/deployment.

Ini hasil operator dan verifier deterministik, **bukan penalaran model AI**, GT manusia dataset utama atau benchmark. Assessment produk pada run operator tetap null. Dua kondisi satu mekanisme tetap dihitung sebagai **satu titik development**; lab kini memiliki BAC-08 dan XSS-08 yang direproduksi operator, 22 titik lainnya masih direncanakan.

## Jalur eksekusi dan batas

Worker menerima `BrowserArguments` untuk satu operasi `notification_probe`: path tetap `/notifications/preview`, alias akun terdaftar, fixture `inert-v1`/`marker-v1` dan UUID nonce yang dibuat aplikasi. Tidak menerima URL bebas, script/eval dari report, locator bebas atau fixture kiriman pelapor. Dua request per aksi adalah login dan dokumen; kelima operasi logis probe dipesan pada cap 30 aksi browser. Validitas aksi browser maksimum 30 detik, run tetap 180 detik dan cap jaringan 40 bersama HTTP. Pemeriksaan di browser bukan izin untuk membuka seluruh route portal.

Semua request browser diintersep sebelum diteruskan melalui HTTPX ke IP lab literal. Hanya satu GET dokumen utama yang diizinkan; subresource/navigasi tambahan, iframe jaringan, popup, redirect, WebSocket dan download ditolak. Respons dibatasi 1 MiB, hanya encoding identity; service worker disetel `block`. Origin HTTP lab saat ini juga tidak menyediakan secure context untuk registrasi service worker; ini bukan uji escape service worker pada origin HTTPS. Namespace firewall tetap menjadi batas egress tambahan, termasuk koneksi latar browser/WebRTC.

Marker memanggil binding lokal, tanpa exfiltration/callback jaringan. Worker mencatat nonce, origin, path dan main frame dari callback aktual. Teks yang sekadar menyebut nonce tidak diterima sebagai eksekusi. Verifier juga memerlukan kontrol inert, JavaScript aktif, storage baru, PNG dan kaitan run/snapshot/boot/akun yang cocok; ketiadaan callback saja tidak membuktikan REFUTED. REFUTED memerlukan fixture marker yang benar-benar tampil sebagai teks.

Capture berisi event, cuplikan teks DOM maksimal 8.192 karakter dan PNG viewport 800x600 maksimal 256 KiB (lebih ketat dari batas umum 2 MiB). JSON dan PNG/hash diimpor ke storage privat dengan run/action/evidence ID. UI hanya menyajikannya sebagai JSON teks bagi admin; belum ada widget screenshot atau publikasi bukti XSS bagi hunter. Browser access baru dari UI masih ditolak oleh planner BAC M3 sebagai unsupported.

Runtime tetap tiga service. Worker kini diberi maksimum 1 GiB RAM, 256 PID, tmpfs 256 MiB dan shared memory privat 128 MiB; tidak memakai host IPC, privileged atau SYS_ADMIN. Python/bootstrap mempertahankan mekanisme drop UID/capability M2. Profil seccomp turunan Playwright memperbolehkan syscall namespace dan chroot agar sandbox Chromium dapat bekerja setelah capability container dihapus; tidak mematikan sandbox atau membuat profil unconfined.

## Perintah yang diperiksa

Sesudah setup/seed M1-M3, startup normal tetap:

```powershell
docker compose up -d --build
```

Browser dipasang hanya pada image worker melalui `requirements-worker.lock`; app/lab dan environment test host tidak membutuhkan Playwright Python. Build awal mengunduh paket/browser dan memerlukan waktu serta ruang disk tambahan. Startup hanya idle, tanpa reset target, model, probe browser atau evaluasi otomatis.

Reproduksi operator, ketika tidak ada run lain:

```powershell
.\.venv\Scripts\python.exe -m evaluator.m4
# Ulangi hanya bagian cancel jika dua kondisi/jaringan sudah diperiksa:
.\.venv\Scripts\python.exe -m evaluator.m4 --cancel-only
.\.venv\Scripts\python.exe -m evaluator.m2 network
```

Evaluator mendaftarkan route/capability browser dan scope development melalui operasi operator eksplisit, kemudian reset kondisi sintetis dan melakukan probe. Tidak menimpa aturan lama; menambahkan izin GET preview melalui versi scope baru. Ini bukan tool model atau endpoint reset. Run operator tidak menggunakan kuota start pengguna atau panggilan model. Password platform lokal hanya dibaca untuk pengujian API cancel dan QA UI; tidak dicetak.

Sesudah reproduksi, QA host opsional:

```powershell
$env:VALVULN_PLAYWRIGHT_CORE='C:/path/to/node_modules/playwright-core'
$env:VALVULN_CHROMIUM='C:/path/to/chrome.exe'
node scripts/m4_ui_evidence_check.cjs
```

QA membaca run selesai dari artefak operator, tanpa reset atau request target baru. Browser QA host terpisah dari browser produk di worker.

## Artefak dan kegagalan yang dipertahankan

Artefak privat lokal di `artifacts/m4/`, diabaikan Git:

- `sandbox-probe.json`: status sandbox aktual dari container probe tanpa network, secret atau volume.
- `verification.json`: hasil dua kondisi dan jaringan **lulus**, tetapi runner lengkap awal berstatus FAILED karena client HTTPX dibuka dua kali sebelum cancel. Kegagalan dan hasil sebelumnya dipertahankan, bukan diubah menjadi PASS.
- `cancel-verification.json`: bagian cancel yang diulang sesudah perbaikan client/cleanup, **PASS**. Uji pertama menemukan callback route menulis TargetClosedError setelah context ditutup; cleanup sekarang melepas route, membatalkan callback dan menutup context/browser. Regresi terakhir memeriksa log worker baru tanpa error callback.
- `ui-evidence-verification.json` dan `admin-evidence-ui.png`: pemeriksaan rendering/privasi aktual.
- PNG bernama action ID, `runtime-manifest.json` dan `final-state.json`. Capture asli/ledger tetap di volume app. Reset akhir dilakukan sesudah handler uji lama selesai; BAC/XSS fixed, worker IDLE, lab OPERATOR_VERIFIED, nol proses browser/log akses lab setelah reset.
- `network-check.json`: salinan hasil NET-03 yang diulang melalui runner M2 pada worker M4a.

Run rentan: `1a3e59f5-5fd1-4b79-bb2b-bf029b039f2e`; perbaikan: `f931c848-c3dd-4fc5-bbd8-f0e290e69363`; jaringan: `4d4c0b02-1321-4e99-8d1c-9d8d1f725743`; cancel regresi cleanup: `3ca230bc-a45e-4e29-9afe-bb445b0971bc`. Run gagal/percobaan awal juga tetap tersimpan di aplikasi.

Kegagalan lingkungan awal: profil Docker bawaan menolak unshare; profil resmi Playwright memerlukan izin chroot tambahan pada capability nol; Chromium penuh memerlukan XDG config/cache pada tmpfs karena root filesystem read-only. Headless-shell tidak menyediakan halaman diagnostik chrome://sandbox, sehingga produk memakai channel Chromium penuh. Seluruh perubahan berada di konfigurasi/container proyek, tanpa mengubah firewall atau konfigurasi keamanan host.

## Yang tersisa

M4b perlu menghubungkan klaim XSS terstruktur ke workflow/verifier/assessment/UI, meninjau projection/publikasi bukti XSS milik hunter dan menyelesaikan tujuh titik XSS lain bertahap. General navigate/fill/click, banyak halaman/resource dan widget screenshot belum tersedia; profil M4a sengaja hanya satu probe tetap. OS inventory dicatat, tetapi mirror apt belum dibekukan untuk build identik di masa depan; packaging/freeze M8-M10 harus mengunci artefak/image yang digunakan.

GT manusia untuk 20 laporan, 22 titik lain secara keseluruhan, kategori upload/business logic, model live dan benchmark tetap pending. M4a tidak meluluskan seluruh M4 atau menyatakan aplikasi aman untuk data instansi.

Sumber implementasi: [Playwright Docker/sandbox](https://playwright.dev/python/docs/docker), [routing context dan batas service worker](https://playwright.dev/python/docs/api/class-browsercontext), [profil upstream v1.64.1](https://github.com/microsoft/playwright/blob/v1.64.1/utils/docker/seccomp_profile.json). Lisensi dan modifikasi dicatat di [third-party.md](third-party.md).
