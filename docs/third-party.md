# Deklarasi komponen, sumber, dan atribusi

**QA integrasi13 November2026:** Playwright Core1.65.0 (Apache-2.0, metadata paket) dipakai hanya untuk QA Chromium host pada artefak privat; tidak menambah dependensi runtime app. Source paket: https://github.com/microsoft/playwright . CI backend baru memakai runner Python3.11 tanpa key model; workflow belum dijalankan di GitHub pada batch lokal ini. Inventaris historis di bawah tidak menyatakan hasil live terbaru.

**Tambahan R3/R4 7 November:** runner teks/evaluator dan script paket tidak menambah library runtime. Memakai HTTPX/Pydantic/aiosqlite serta stdlib yang sudah dipin. Slide/thumbnail adalah HTML/CSS asli proyek, font sistem, dirender oleh playwright-core/Chromium QA host yang sudah tersedia; binary QA tidak disertakan dalam source ZIP. Screenshot/video merekam app disposable MOCK dengan data sintetis dan banner capture. Inventaris M1/M2/M4 serta notice seccomp disertakan; kandidat ZIP tidak memuat image/binary OS/browser. Lisensi source asli tetap keputusan pengguna yang pending; tidak membuat LICENSE sepihak atau mengklaim inventaris sebagai audit hukum. Build image review terpisah hanya lokal, tidak didistribusikan. [Materi](../submission/README.md), [hasil/batas](r3-r4-verification.md).

Status: prototipe UI lokal dibuat tanpa dependensi npm/runtime aplikasi tambahan. Dependensi app M1 sudah dipasang dan dipin; worker HTTP/lab M2 memakai pin Python yang sama; M4a memasang Playwright/Chromium worker melalui lock terpisah. Provider live belum tersedia. Versi/lisensi metadata langsung dan transitif tercatat pada [dependencies-m1.json](dependencies-m1.json), diambil dari distribusi terpasang, bukan tebakan atau audit keamanan dependensi.

Dasar: rulebook Bagian G dan S&K Pasal 5.3-5.4 memperbolehkan penggunaan komponen pihak ketiga dengan hak penggunaan yang sah, atribusi, serta deklarasi dasar pre-existing. Dokumen ini harus diperbarui berdasarkan komponen yang benar-benar digunakan.

## 1. Kontribusi yang direncanakan tim

- Workflow validasi report dan kontrak tools.
- Policy gate, evidence linkage, dan tampilan review analis.
- Portal pengadaan/logistik sintetis dan skenario pengujian.
- Draf 20 report sintetis disusun asisten berdasarkan lab, GT diverifikasi manual pengguna; prosedur benchmark dan analisis hasil dicatat terpisah dari draf.

Daftar ini merupakan rencana, bukan klaim seluruh kontribusi sudah selesai. Bantuan AI dalam penyusunan kode/dokumentasi dicatat secara jujur; keaslian kontribusi tim tidak berarti mengklaim model atau framework pihak ketiga dibuat sendiri.

## 2. Kandidat dependensi dan layanan

| Komponen | Peran rencana | Sumber | Versi/commit/lisensi aktual | Status |
| --- | --- | --- | --- | --- |
| Python | Runtime | https://www.python.org/ | Python terpasang 3.11.9; catat ketentuan distribusi saat packaging | Terdeteksi pada host |
| FastAPI | API dan dashboard | https://fastapi.tiangolo.com/ | 0.162.0 / MIT (metadata distribusi; detail notice pada inventaris) | Dipakai dan diuji pada M1 app; HTTPX provider nyata belum aktif |
| Uvicorn | Server app dan lab | https://www.uvicorn.org/ | 0.54.0 / BSD-3-Clause (metadata distribusi; detail notice pada inventaris) | Dipakai dan diuji pada M1 app; HTTPX provider nyata belum aktif |
| Pydantic | Schema/validasi | https://docs.pydantic.dev/ | 2.14.2 / MIT (metadata distribusi; detail notice pada inventaris) | Dipakai dan diuji pada M1 app; HTTPX provider nyata belum aktif |
| SQLite | Database app; lab menyusul | https://www.sqlite.org/ | Host 3.45.1; image 3.40.1; engine bawaan Python, notice image tetap diperiksa sebelum rilis | App M1 diuji; DB lab belum dibuat |
| aiosqlite | Akses SQLite async | https://aiosqlite.omnilib.dev/en/stable/ | 0.22.1 / MIT License (metadata distribusi; detail notice pada inventaris) | Dipakai dan diuji pada M1 app; HTTPX provider nyata belum aktif |
| python-multipart | Parsing form/upload teks | https://fastapi.tiangolo.com/tutorial/request-files/ | 0.0.33 / Apache-2.0 (metadata distribusi; detail notice pada inventaris) | Dipakai dan diuji pada M1 app; HTTPX provider nyata belum aktif |
| pwdlib dengan Argon2 | Hash password platform | https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/ | 0.3.1 / MIT License (metadata distribusi; detail notice pada inventaris) | Dipakai dan diuji pada M1 app; HTTPX provider nyata belum aktif |
| HTTPX | HTTP worker | https://www.python-httpx.org/ | 0.28.1 / BSD-3-Clause (metadata distribusi; detail notice pada inventaris) | Dipakai dan diuji pada M1 app; HTTPX provider nyata belum aktif |
| Playwright/Chromium | Browser worker | https://playwright.dev/python/ | Catat versi paket dan browser, serta notice masing-masing | Direncanakan |
| Jinja2 | Template UI chat dan halaman program | https://jinja.palletsprojects.com/ | 3.1.6 / BSD License (metadata distribusi; detail notice pada inventaris) | Dipakai dan diuji pada M1 app; HTTPX provider nyata belum aktif |
| Docker/Compose | Packaging lokal | https://docs.docker.com/compose/ | Engine 29.7.2 / Compose v5.3.1; image Python 3.11.18 dengan digest pada Dockerfile | App M1 build/health/restart lulus; worker/lab belum ada |
| Qwen3-Coder | Penalaran model | https://qwenlm.github.io/blog/qwen3-coder/ | Catat model ID, inference provider, dan ketentuan endpoint | Belum dipanggil live |
| OpenRouter | Akses API model | https://openrouter.ai/terms | Terms dan biaya diperiksa; key belum tersedia | Belum diaktifkan |
| Gemini Developer API | Cadangan direct Free Tier; opsi primary/comparator sebelum freeze | https://aistudio.google.com/docs/pricing | Kandidat gemini-3.5-flash-lite; key, quota, ketentuan data dan tools akun belum diuji | Rencana adapter, belum dipakai |
| OpenAI Platform API | Provider opsional, terpisah dari Plus/Codex | https://developers.openai.com/api/docs/guides/chatgpt-api-credits | Model/key/kredit/biaya diverifikasi sebelum aktivasi; bukan dianggap gratis dari Plus | Rencana adapter, default nonaktif |
| xAI/Grok API | Provider opsional berbasis usage/kredit aktual | https://x.ai/api | Model/key/kredit/biaya belum ditetapkan; Playground bukan free tier API yang terkonfirmasi | Rencana adapter, default nonaktif |
| Azure for Students / Microsoft Foundry | Kandidat kredit pendidikan dan inference model Azure | https://azure.microsoft.com/en-us/free/students/ | Aktivasi hibah, saldo, cakupan produk, deployment/model/version dan quota belum diverifikasi | Panduan apply tersedia, profil default nonaktif |
| Sign in with ChatGPT | Opsi lanjutan plan usage pengguna eligible | https://developers.openai.com/siwc/token-sharing-open-source | Consent, registrasi, model/tool dan cap output belum diverifikasi; bukan kuota bersama backend | Belum masuk integrasi MVP awal |
| pytest / pytest-asyncio | Pemeriksaan development | https://docs.pytest.org/ ; https://pytest-asyncio.readthedocs.io/ | 9.2.0 MIT / 1.4.1.post1 Apache-2.0; metadata distribusi | 86 tes M1 lulus; tidak dipasang pada runtime image |

Tabel tidak menyatakan semua komponen berlisensi sama atau semua kandidat telah menjadi dependensi. Catat lisensi versi aktual, notice, URL dan modifikasi sebelum menyalin/mendistribusikan komponen. Library runtime, browser binary, model weights dan layanan API mempunyai objek hak/ketentuan yang berbeda.

Ringkasan stack dipilih pada 4 November 2026 di [prd.md](../prd.md). Tabel sudah diperbarui untuk dependensi app aktual M1; komponen worker/browser dan layanan model tetap rencana. Requirements runtime/dev mengunci versi transitif, termasuk Argon2 bindings dan dependensi framework. Daftar file LICENSE/NOTICE relatif pada distribusi dicatat pada inventaris; paket tetap membawa notice upstream. Setuptools 84.2.1 dipin sebagai build backend, bukan runtime image. Distribusi/rilis masih perlu pemeriksaan notice Python/Debian/image dan pilihan lisensi kode asli proyek.

## 3. Skill pentest dari GitHub

Belum ada repo yang dipilih, diunduh sebagai skill, atau dipasang. Implementasi awal memakai tools dasar yang dirancang untuk lab.

Untuk setiap skill yang akhirnya dipakai, catat nama, URL repository, commit, file yang diambil, lisensi, modifikasi, fungsi dalam produk, dan tanggal pengambilan. Hindari deklarasi seolah seluruh panduan pentest eksternal adalah karya tim. Instruksi skill tidak dapat memperluas target atau izin runtime.

## 4. Karya pre-existing

Saat ini belum ada source aplikasi terdahulu yang dinyatakan digunakan sebagai dasar proyek. Ini status pengetahuan saat dokumentasi dibuat, bukan sertifikasi bahwa tidak ada komponen pihak ketiga. Jika memakai template, target latihan, potongan kode, dataset, atau modul lama, tambahkan asal, tanggal/periode, dan bagian baru yang dikerjakan selama program.

Model AI dan framework bukan kontribusi asli tim. Penggunaan legal dan atribusi harus tetap dicatat meskipun dibayar melalui API atau dipasang melalui package manager.

## 5. Sumber aturan dan data masalah

- Rulebook dan S&K disediakan panitia; tautan/hash ada di [sources/README.md](sources/README.md). Salinan PDF lokal disimpan untuk pemeriksaan, bukan diklaim sebagai dokumen buatan tim.
- Statistik curl/HackerOne dalam [plan.md](../plan.md) merupakan pernyataan sumber eksternal dengan periode dan batas interpretasi.
- Dataset utama akan dibuat dari lab sintetis dan bukti manual tim. Report pihak ketiga baru ditambahkan setelah hak penggunaan, relevansi dan penanganan datanya diperiksa.

Sebelum submission, ganti status kandidat dengan inventaris aktual. Jangan meninggalkan nomor versi atau lisensi tebakan sebagai fakta.

Lisensi untuk kode asli proyek belum dipilih pengguna; belum ada file LICENSE proyek. Tentukan dan sertakan ketentuannya sebelum repo/release publik. Lisensi kode proyek tidak menggantikan lisensi dependensi, hak asset, atau terms API. Ini pekerjaan persiapan rilis, bukan syarat untuk audit dokumen atau pengembangan lokal.

## 6. Referensi desain untuk prototipe UI

Panduan yang dibaca: [Impeccable](https://github.com/pbakaus/impeccable) (LICENSE Apache-2.0 diperiksa), [Jakub Krehel](https://github.com/jakubkrehel/skills) (MIT), [Emil Kowalski](https://github.com/emilkowalski/skills) (MIT). File dan Git blob SHA yang dibaca ada pada [design-references.md](design-references.md). Tidak memasang CLI/plugin upstream atau menyalin source/template/asset mereka; menerapkan prinsip secara manual. Delapan referensi lain dinilai dan diposisikan pada dokumen yang sama.

Source HTML/CSS/JS serta icon SVG sederhana dibuat untuk prototipe proyek ini. Font memakai system stack; tidak mengambil foto, webfont, template atau asset berbayar. Skill Sites bawaan dipakai sebagai panduan pembuatan prototipe lokal, tanpa hosting/registrasi Site. QA memakai Chromium dan playwright-core yang sudah tersedia pada host; bukan dependensi yang dibundel ke aplikasi. Versi aktual dan hasil QA dicatat di `ui-review.md`; ini tidak menyatakan Playwright worker produk sudah dipasang atau aman.


## 7. Komponen OS untuk isolasi M2

Worker/lab memakai image Python 3.11.18 dengan digest yang sama seperti M1. `iptables` 1.8.9-2 dan `util-linux` 2.38.1-5+deb12u3 (setpriv), beserta library sistem terkait, dipasang untuk bootstrap firewall namespace dan penurunan UID/capability. Versi aktual dan bagian lisensi dari file copyright terpasang ada pada [dependencies-m2.json](dependencies-m2.json). Paket ini memiliki lisensi campuran per file (antara lain GPL/LGPL/BSD/Artistic); tidak menyatakan semuanya MIT. File notice `/usr/share/doc/.../copyright` dipertahankan di image; kewajiban source/notice distribusi image diperiksa pada persiapan rilis M10. Belum ada paket/rilis image publik yang dibuat.

HTTPX/aiosqlite/Pydantic/FastAPI/Uvicorn/pwdlib di worker/lab memakai requirements.lock yang sama, bukan SDK model baru. Tidak menyalin target latihan pihak ketiga atau memasang skill pentest. Portal, kontrak dan evaluator M2 dibuat untuk proyek dengan bantuan Codex. Label GT dataset, model/provider dan browser tidak menjadi dependensi worker M2.

## Komponen UI/QA M3 - 5 November 2026

UI backend memakai Jinja2/JavaScript/CSS dan aset baseline proyek tanpa runtime npm baru; `ui-prototype/` dipertahankan terpisah. QA host memakai instalasi `playwright-core` 1.64.1, metadata lisensi Apache-2.0, serta Chromium lokal; versi browser aktual dicatat di `artifacts/m3/ui-verification.json`. Paket/binary QA tidak disalin dari proyek host lain ke source, tidak dibundel dan tidak dipasang pada worker produk. Path dependensi dikonfigurasi melalui environment script. Browser worker/notice distribusinya tetap checkpoint M4/rilis; jangan menganggap QA host meluluskannya. M3 tidak menambah dependensi Python; inventaris M1/M2 tetap berlaku.

## Komponen browser M4a - 5 November 2026

Worker menambah Playwright Python **1.64.1** (Apache-2.0), greenlet **3.5.6** (MIT AND PSF-2.0) dan pyee **13.0.1** (MIT), berdasarkan metadata distribusi Linux terpasang. Chromium **156.0.8078.4**, revision **1248**, dipasang melalui installer Playwright yang versinya dikunci. Manifest paket juga mencantumkan browser lain; itu bukan klaim Firefox/WebKit telah diinstal. Hanya Chromium dipakai produk. Inventaris paket/notice dan 217 paket OS aktual ada pada [dependencies-m4.json](dependencies-m4.json).

Profil `containers/chromium-seccomp.json` berasal dari [Microsoft Playwright v1.64.1](https://github.com/microsoft/playwright/blob/v1.64.1/utils/docker/seccomp_profile.json), Git blob `fddc05fb520affb145404e6f6f647ca96af8087d`, Apache-2.0, turunan default Docker. Modifikasi lokal menambahkan izin chroot untuk sandbox namespace setelah capability container dihapus. [Notice/provenance](../containers/CHROMIUM-SECCOMP-NOTICE.md) dan [lisensi upstream](../containers/PLAYWRIGHT-LICENSE) disertakan. Tidak mengklaim profil upstream sebagai karya tim, atau memakai seccomp unconfined/SYS_ADMIN/host IPC.

Library/binary tetap membawa notice upstream di image; pemeriksaan notice/source distribusi Chromium/Debian/image dan freeze apt masih prasyarat rilis M10. Versi paket/browser diuji, tetapi inventaris ini bukan audit keamanan dependensi atau opini legal. Tidak menambahkan API model, skill pentest eksternal, target latihan pihak ketiga atau deployment cloud. Hasil aktual dan batas operator/UI pada [m4-verification.md](m4-verification.md).

M4c (5 November) menambah tujuh fitur lab, migrasi, fixture dan evaluator lokal yang dibuat untuk proyek dengan bantuan Codex; tanpa target/payload pihak ketiga atau dependensi baru. Probe operator memakai Playwright/Chromium worker M4a yang sama. Inventaris paket M1/M2/M4a tetap berlaku; hash source dan ID image aktual dicatat privat pada artefak [M4c](m4c-verification.md). Source evaluator/manifest tidak disalin ke image produk.

## Pembaruan Aset Frontend (13 November 2026 — Arah "SEGEL")

- **Newsreader** (`@fontsource-variable/newsreader@5.3.0` normal `opsz,wght` dan `@fontsource/newsreader` 400 italic, [Fontsource](https://fontsource.org/)) — file WOFF2 lokal subset Latin (`app/static/fonts/newsreader-latin-opsz-normal.woff2`, `app/static/fonts/newsreader-latin-400-italic.woff2`), lisensi **SIL Open Font License 1.1 (OFL-1.1)**, disajikan self-hosted untuk mematuhi CSP `default-src 'self'`.
- **Schibsted Grotesk** (`@fontsource-variable/schibsted-grotesk@5.3.0`, [Fontsource](https://fontsource.org/)) — file WOFF2 lokal subset Latin (`app/static/fonts/schibsted-grotesk-latin-wght-normal.woff2`), lisensi **SIL Open Font License 1.1 (OFL-1.1)**, disajikan self-hosted untuk teks UI dan body.
- **Spline Sans Mono** (`@fontsource/spline-sans-mono@5.3.0`, [Fontsource](https://fontsource.org/)) — file WOFF2 lokal subset Latin weight `400` dan `500` (`app/static/fonts/spline-sans-mono-latin-400-normal.woff2`, `app/static/fonts/spline-sans-mono-latin-500-normal.woff2`), lisensi **SIL Open Font License 1.1 (OFL-1.1)**, disajikan self-hosted khusus ID bukti, hash SHA-256, JSON, dan kode jalur (`BAC-08`/`XSS-08`/`UP-04`).
- **Ikon SVG inline & Mark** (`app/static/icons.js`, `app/static/mark.svg`) — dibuat langsung sebagai SVG vektor stroke seragam 24×24 tanpa PNG, emoji, atau icon-font. Pedoman visual berada pada [design.md](design.md).
- **Rencana Tahap 2 (belum ditambahkan pada Tahap 1):** Three.js minimal self-hosted di `app/static/vendor/` untuk scene homepage "SEGEL".
