# Deklarasi komponen, sumber, dan atribusi

Status: prototipe UI lokal dibuat tanpa dependensi npm/runtime aplikasi tambahan. Backend dan dependensi runtime produk belum diimplementasikan/dipasang. Referensi desain dicatat di bawah; pengguna meminta tahap UI selesai dahulu.

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
| FastAPI | API dan dashboard | https://fastapi.tiangolo.com/ | Belum dipilih/diperiksa untuk versi yang akan digunakan | Direncanakan |
| Uvicorn | Server app dan lab | https://www.uvicorn.org/ | Versi/lisensi aktual belum dikunci/diperiksa | Dipilih dalam PRD, belum dipasang |
| Pydantic | Schema/validasi | https://docs.pydantic.dev/ | Major 2 direncanakan; minor/patch/lisensi versi aktual belum dikunci | Direncanakan |
| SQLite | Dua database lokal app/lab | https://www.sqlite.org/ | Catat versi engine bawaan build Python serta notice distribusinya saat packaging | Dipilih dalam PRD, DB produk belum dibuat |
| aiosqlite | Akses SQLite async | https://aiosqlite.omnilib.dev/en/stable/ | Versi/lisensi aktual belum dikunci/diperiksa | Dipilih dalam PRD, belum dipasang |
| python-multipart | Parsing form/upload teks | https://fastapi.tiangolo.com/tutorial/request-files/ | Versi/lisensi aktual belum dikunci/diperiksa | Dipilih dalam PRD, belum dipasang |
| pwdlib dengan Argon2 | Hash password platform | https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/ | Catat versi/lisensi paket serta dependensi Argon2 aktual | Dipilih dalam PRD, belum dipasang |
| HTTPX | HTTP worker | https://www.python-httpx.org/ | Belum dipilih/diperiksa | Direncanakan |
| Playwright/Chromium | Browser worker | https://playwright.dev/python/ | Catat versi paket dan browser, serta notice masing-masing | Direncanakan |
| Jinja2 | Template UI chat dan halaman program | https://jinja.palletsprojects.com/ | Belum dipilih/diperiksa | Direncanakan |
| Docker/Compose | Packaging lab | https://docs.docker.com/compose/ | CLI terdeteksi; daemon dan image belum diverifikasi | Rencana penggunaan |
| Qwen3-Coder | Penalaran model | https://qwenlm.github.io/blog/qwen3-coder/ | Catat model ID, inference provider, dan ketentuan endpoint | Belum dipanggil live |
| OpenRouter | Akses API model | https://openrouter.ai/terms | Terms dan biaya diperiksa; key belum tersedia | Belum diaktifkan |
| Gemini Developer API | Cadangan direct Free Tier; opsi primary/comparator sebelum freeze | https://aistudio.google.com/docs/pricing | Kandidat gemini-3.5-flash-lite; key, quota, ketentuan data dan tools akun belum diuji | Rencana adapter, belum dipakai |
| OpenAI Platform API | Provider opsional, terpisah dari Plus/Codex | https://developers.openai.com/api/docs/guides/chatgpt-api-credits | Model/key/kredit/biaya diverifikasi sebelum aktivasi; bukan dianggap gratis dari Plus | Rencana adapter, default nonaktif |
| xAI/Grok API | Provider opsional berbasis usage/kredit aktual | https://x.ai/api | Model/key/kredit/biaya belum ditetapkan; Playground bukan free tier API yang terkonfirmasi | Rencana adapter, default nonaktif |
| Azure for Students / Microsoft Foundry | Kandidat kredit pendidikan dan inference model Azure | https://azure.microsoft.com/en-us/free/students/ | Aktivasi hibah, saldo, cakupan produk, deployment/model/version dan quota belum diverifikasi | Panduan apply tersedia, profil default nonaktif |
| Sign in with ChatGPT | Opsi lanjutan plan usage pengguna eligible | https://developers.openai.com/siwc/token-sharing-open-source | Consent, registrasi, model/tool dan cap output belum diverifikasi; bukan kuota bersama backend | Belum masuk integrasi MVP awal |
| pytest / pytest-asyncio | Pemeriksaan pengembangan | https://docs.pytest.org/ ; https://pytest-asyncio.readthedocs.io/ | Versi/lisensi aktual belum dikunci/diperiksa; bukan service produksi | Direncanakan, belum dipasang untuk proyek |

Tabel tidak menyatakan semua komponen berlisensi sama atau semua kandidat telah menjadi dependensi. Catat lisensi versi aktual, notice, URL dan modifikasi sebelum menyalin/mendistribusikan komponen. Library runtime, browser binary, model weights dan layanan API mempunyai objek hak/ketentuan yang berbeda.

Ringkasan stack dipilih pada 4 November 2026 di [prd.md](../prd.md). Penambahan tabel ini hanya inventaris rencana; tidak menjalankan instalasi, mengunduh image/browser atau membuat container.

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
