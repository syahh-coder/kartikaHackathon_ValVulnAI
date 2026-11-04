# Pemilihan referensi UI

Tanggal baca: 3 November 2026. Lingkup: README seluruh repository dan halaman resmi yang dikirim pengguna; SKILL.md/playbook terkait dibaca lebih lanjut untuk panduan yang dipilih. Ini penilaian kesesuaian proyek, bukan benchmark kualitas tool. Tidak ada plugin eksternal yang diinstal, akun layanan dibuat, atau paket berbayar dibeli.

## Keputusan untuk ValVuln AI

Gunakan **prinsip Impeccable untuk UI kerja**, **panduan aksesibilitas Jakub**, dan **prinsip interaksi Emil**. UI pertama dibuat langsung sebagai HTML/CSS/JavaScript lokal sehingga mudah ditinjau dan kemudian diintegrasikan dengan FastAPI. Pengguna memilih **gelap grafit + hijau sage**; bentuk utama tetap chat seperti keputusan sebelumnya. Ini bukan menjalankan seluruh workflow/CLI dari tiga paket sekaligus.

Skill Sites yang tersedia di lingkungan dipakai pada jalur prototipe lokal tanpa deployment. Tidak memakai hosting Sites, Cloudflare, model AI atau integrasi aplikasi eksternal sebagai bagian dari prototipe ini. Tidak menambah React/Next.js hanya untuk desain dasar.

## Perbandingan 11 referensi

| Referensi resmi | Fungsi yang dibaca | Keputusan untuk tahap UI |
| --- | --- | --- |
| [Matt Pocock](https://github.com/mattpocock/skills) | Kumpulan skill engineering dan produktivitas, termasuk prototyping, TDD dan pemodelan domain | Simpan untuk proses engineering berikutnya. Tidak perlu mengganti plan/checkpoint yang sudah ada atau menjalankan seluruh setup untuk membuat shell chat |
| [Taste Skill](https://github.com/leonxlnx/taste-skill) | Art direction, jalur app screens dan pemeriksaan browser; mempunyai skrip/workflow sendiri | Alternatif bagus. Tidak digabungkan sebagai workflow utama karena brief sudah menetapkan chat dan palet; mengambil prinsip antarmuka kerja yang tenang sebagai pertimbangan, tanpa mengklaim menjalankan skrip Taste |
| [Jakub Krehel](https://github.com/jakubkrehel/skills) | Panduan UI, layout, writing, tipografi, warna dan aksesibilitas yang terpisah | Pilih sebagai referensi keyboard, label, dialog native, focus dan narrow state. Tidak mengklaim audit lengkap semua domain atau screen reader |
| [Emil Kowalski](https://github.com/emilkowalski/skills) | Design engineering, keputusan animasi dan detail komponen | Pilih sebagai referensi feedback singkat, tidak menganimasikan interaksi rutin dan menghormati reduced motion. Tidak memasang library animasi |
| [Impeccable](https://impeccable.style/) / [repo](https://github.com/pbakaus/impeccable) | Panduan desain dan review, membedakan mode Operate dari halaman promosi | Panduan utama: hierarki, warna semantik, komponen konsisten, empty/error states dan review render. CLI, live editing dan detector tidak diaktifkan |
| [Awesome DESIGN.md](https://github.com/VoltAgent/awesome-design-md) | Kumpulan analisis sistem desain berbagai produk | Referensi format dokumentasi, bukan design system yang disalin. `docs/design.md` tetap pemilik keputusan agar tidak ada dua spesifikasi bertentangan |
| [Paper](https://paper.design/) | Canvas berbasis HTML/CSS dan koneksi agent/code melalui MCP | Tunda sebagai tool tambahan. Untuk tahap ini review langsung pada browser sudah cukup; tidak membuat akun/mengunduh aplikasi |
| [Pencil / tautan pen.dev](https://www.pen.dev/) | Halaman yang diberikan saat dibaca menampilkan pen.dev, agentic canvas, import dan export HTML | Tunda canvas tambahan. Catat identitas dari URL aktual; tidak menyamakan setiap produk bernama Pencil tanpa verifikasi |
| [OpenDesign](https://github.com/nexu-io/open-design) | Workspace desain, prototipe HTML, design systems dan integrasi agent | Tunda instalasi workspace karena proyek cukup dikerjakan dari repo yang ada. Lisensi open source tidak berarti semua API/model tambahannya tanpa biaya |
| [Aura](https://www.aura.build/templates) / [FAQ](https://www.aura.build/learn/faq) | Galeri/template, editing visual dan export front-end | Inspirasi saja; tidak membeli, menyalin template, atau membuat ketergantungan pada layanan. Homepage tidak memberi teks terbaca, maka yang dipakai adalah halaman resmi templates/FAQ |
| [Hallmark](https://github.com/nutlope/hallmark) | Skill tema desain, self-contained HTML, lint/browser review | Alternatif, bukan workflow tambahan. Theme dealing dan setup terpisah tidak diperlukan untuk chat yang sudah ditetapkan |

Penilaian biaya/waktu tambahan di atas merupakan pertimbangan proyek solo, bukan klaim bahwa suatu tool lambat/jelek secara umum. Harga/kuota layanan tidak dipakai sebagai fakta tanpa checkout aktual.

## Snapshot sumber yang benar-benar dibaca

Hash adalah Git blob SHA file yang diterima connector GitHub, bukan SHA commit repository. Branch dapat berubah; pin ulang commit bila menyalin/mendistribusikan kode di kemudian hari.

| File | Git blob SHA |
| --- | --- |
| `mattpocock/skills: README.md` | `f7038f139299985eea6c3e18398dbafb379a0010` |
| `leonxlnx/taste-skill: README.md` | `8efa355f7d03ada51edccea568dccf26e628b511` |
| `leonxlnx/taste-skill: skills/taste-skill/SKILL.md` | `d8444f13b76be100b3b088dfdae738e85288d6b6` |
| `jakubkrehel/skills: README.md` | `4a98833328ce2fbcf3338ece1fb4a9459121bc58` |
| `jakubkrehel/skills: skills/better-accessibility/SKILL.md` | `5e9ab11b4c109d56c435731198ed23ba0267e529` |
| `emilkowalski/skills: README.md` | `eb13e61d196401244b3c2061f322943c42313078` |
| `emilkowalski/skills: skills/emil-design-eng/SKILL.md` | `dc063c2a861922c1c9f2412b824b0862746304f5` |
| `pbakaus/impeccable: README.md` | `555fd9a67de957c750950e62bf1baad167f61b00` |
| `pbakaus/impeccable: plugin/skills/impeccable/SKILL.md` | `ded40d5a56c19f6118dba7694a1decf84a11ac7c` |
| `pbakaus/impeccable: skill/reference/operate.md` | `5e4666de08f63f55c832c7bb2511cc9ad8068744` |
| `pbakaus/impeccable: skill/reference/craft-floor.md` | `3331f4845d00756869e48edc0277ba8bc8e5826e` |
| `VoltAgent/awesome-design-md: README.md` | `dbaa687886f117cc665a08502ead71099af783ae` |
| `nexu-io/open-design: README.md` | `bf8b42df35f25e6aa865928233d9bfe152b9ea04` |
| `nutlope/hallmark: README.md` | `2568bb6f51284bc3feeea6a3098d31f6743ec623` |

File pendukung Jakub `better-interface` dan `better-ui`, serta Impeccable `new-work`, juga dibaca untuk memahami batas penggunaan. Tidak mengklaim menjalankan orkestrator review tersebut. Launcher Impeccable tidak terpasang; context proyek dibaca dari `AGENTS.md`, `plan.md`, `docs/design.md` dan `docs/architecture.md` yang sudah ada. UI mengikuti brief chat yang dipilih pengguna; tidak menjalankan concept dealing atau live editor dari upstream.

## Lisensi dan batas pemakaian

LICENSE upstream yang diperiksa: Impeccable **Apache-2.0**, Jakub **MIT**, Emil **MIT**. Penerapan berupa panduan desain; source/template, font, foto dan script upstream tidak disalin ke prototipe. Icon SVG sederhana dan source UI dibuat untuk proyek ini. Prototipe tidak membutuhkan koneksi jaringan atau API key. Inventaris kontribusi dan status dependensi ada di [third-party.md](third-party.md).

## Batas tahap

Hasil tahap ini berupa UI untuk ditinjau, bukan hasil pentest/benchmark. Pada 4 November 2026 pengguna menerima UI sebagai baseline fix untuk mulai backend, dengan perbaikan berikutnya tetap boleh; gate UI tidak lagi pending. Membuka role admin pada kontrol pratinjau bukan implementasi login/otorisasi. Semua fixture bersifat ilustratif dan bukan bagian dari 20 laporan berlabel final.
