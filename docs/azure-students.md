# Daftar Azure for Students dan cek akses Microsoft Foundry

Diperiksa **4 November 2026** dari sumber resmi Microsoft. Pengguna menyatakan mahasiswa aktif dengan email kampus, dan sebelumnya sudah mengonfirmasi usia 18+. Ini sesuai syarat dasar; verifikasi/aktivasi Microsoft tetap menentukan hasil. Akun Azure, kredit, deployment dan API pengguna **belum diperiksa atau dibuat** oleh asisten.

## 1. Program yang didaftarkan

Daftar **Azure for Students**, lalu gunakan Microsoft Foundry sebagai tempat memilih/deploy model yang tersedia pada subscription itu. Bukan satu program terpisah yang menjamin semua model Foundry gratis.

Azure for Students menawarkan kredit **US$100 untuk 12 bulan**, tanpa kartu kredit saat daftar, bagi mahasiswa penuh waktu pada institusi pendidikan tinggi yang memenuhi syarat. Status akademik diverifikasi lewat email institusi; satu subscription per pelanggan eligible. Sumber: [penjelasan program](https://learn.microsoft.com/en-us/azure/education-hub/about-azure-for-students) dan [halaman pendaftaran](https://azure.microsoft.com/en-us/free/students/).

Kredit adalah saldo pemakaian layanan yang dicakup, bukan uang tunai atau token tak terbatas. Tidak diasumsikan bisa dipindahkan ke OpenRouter, Gemini atau OpenAI Platform. Pilihan provider proyek tetap pada [PRD](../prd.md).

## 2. Langkah apply

1. Buka [Azure for Students](https://azure.microsoft.com/en-us/free/students/) lalu pilih **Start free**. Tautan resmi saat pemeriksaan mengarah ke [verifikasi student](https://signup.azure.com/studentverification?offerType=1).
2. Masuk dengan akun Microsoft yang ingin digunakan. Jika perlu membuat akun, ikuti alur Microsoft. Gunakan identitas sendiri; email kampus dipakai untuk verifikasi akademik sesuai form.
3. Isi data yang diminta secara benar, pilih negara sesuai keadaan sebenarnya dan selesaikan verifikasi yang ditampilkan. Jangan mencatat nomor identitas, password atau OTP di repo/chat.
4. Masukkan email kampus pada tahap verifikasi mahasiswa, lalu buka inbox kampus dan selesaikan tautan/kode konfirmasinya. Nama dan urutan field dapat berubah; form setelah login tidak diinspeksi asisten.
5. Tinjau offer dan ketentuannya, lalu selesaikan aktivasi **Azure for Students**. Jika alur berubah menjadi akun trial umum/PAYG yang meminta kartu, periksa kembali offer; jangan menganggap itu langkah wajib program Students.
6. Buka [Azure portal](https://portal.azure.com/), cari **Subscriptions**, dan pastikan subscription **Azure for Students** berstatus aktif. Belum dianggap berhasil hanya karena sudah punya login Microsoft.
7. Periksa saldo kredit dan tanggal berlakunya. FAQ Microsoft menunjuk [Azure Sponsorships](https://www.microsoftazuresponsorships.com/) untuk melihat saldo; gunakan akun yang terkait subscription. Simpan catatan status nonsecret untuk melanjutkan setup.

Panduan ini tidak mengisi/mengirim formulir atau menyatakan pendaftaran disetujui. Sumber benefit/billing dan saldo: [FAQ Azure for Education](https://learn.microsoft.com/en-us/azure/education-hub/faq).

## 3. Sesudah aktif: cek Foundry

Langkah berikut dilakukan pengguna pada akun aktif; bukan instruksi bahwa deployment sudah tersedia atau semua pilihan dapat dibeli dengan kredit Students.

1. Buka [Microsoft Foundry](https://ai.azure.com/) memakai akun/tenant yang memiliki subscription Students.
2. Buat project baru; pilih **Azure for Students** saat subscription diminta. Nama contoh proyek `valvuln-ai`, resource group `rg-valvuln-ai`; ini usulan nama, bukan resource yang sudah dibuat.
3. Periksa region dan model yang diizinkan subscription. Jangan memilih region hanya karena contoh tutorial memakai region tertentu; policy/capacity akun bisa berbeda.
4. Pada portal baru, jalur dokumentasi saat diperiksa adalah **Build -> Models -> Deploy -> Deploy a base model**. Pilih model teks yang dapat digunakan, periksa harga, jenis deployment, kuota serta dukungan function calling/output terstruktur sebelum deploy. Tidak menetapkan model tertentu tanpa melihat akses aktual.
5. Untuk proyek ini, utamakan inference on-demand berbayar per pemakaian yang tercakup kredit. Tidak membutuhkan VM/GPU, reserved/provisioned capacity atau Foundry-hosted agent; workflow dan tools tetap milik aplikasi lokal.
6. Setelah deployment siap, catat **deployment name, model/version, region, endpoint inference dan metode autentikasi** dari halaman deployment/View code yang sesuai. Project endpoint dan inference endpoint tidak boleh dianggap selalu sama. API key bila digunakan disimpan hanya pada konfigurasi privat app; jangan ditempel ke chat/repo.
7. Uji kecil model/tools dilakukan ketika integrasi sudah diotorisasi dan cakupan kredit dipastikan, lalu cek pemakaian aktual. Sebelum itu status provider tetap pending, bukan fallback aktif.

Urutan portal/project/deploy merujuk [quickstart Foundry](https://learn.microsoft.com/en-us/azure/foundry/tutorials/quickstart-create-foundry-resources). Kuota model/subscription diperiksa melalui [quota Foundry/OpenAI](https://learn.microsoft.com/en-us/azure/foundry/openai/quotas-limits), bukan diasumsikan dari saldo US$100.

## 4. Batas kredit dan model

**Kredit tersedia tidak menjamin akses semua model.** Penawaran Azure for Students mengecualikan Azure Marketplace dan produk tertentu; subscription Student tidak dapat membeli SaaS Marketplace yang dibutuhkan sebagian model partner. Utamakan mengecek model yang dijual langsung oleh Azure dan lihat ketentuan billing aktualnya; label Azure saja bukan bukti seluruh pilihan tercakup kredit. Sumber: [offer details, Exclusions](https://azure.microsoft.com/en-us/pricing/offers/ms-azr-0170p), [model partner/Marketplace](https://learn.microsoft.com/en-us/azure/foundry/foundry-models/concepts/models-from-partners) dan [model sold by Azure](https://learn.microsoft.com/en-us/azure/foundry/foundry-models/concepts/models-sold-directly-by-azure).

Pertahankan subscription Students dan pembatas pengeluaran yang melekat pada offer. Ketika kredit habis, offer menyebut subscription dinonaktifkan; jangan mengubahnya ke PAYG atau memasukkan biaya pribadi untuk melewati batas proyek. Dana pribadi proyek tetap maksimal Rp50.000. Kredit hibah, biaya pemakaian USD dan uang yang benar-benar dibayar dicatat terpisah.

## 5. Jika menemui hambatan

| Kondisi | Langkah berikutnya |
| --- | --- |
| Email/status akademik tidak diterima | Periksa email dan status aktif institusi, ikuti opsi verifikasi/dukungan resmi yang muncul; belum dianggap eligible terverifikasi |
| Subscription tidak muncul di Foundry | Periksa akun, direktori/tenant dan filter subscription; status aktif dicek di Azure portal |
| Region/resource diblokir policy | Pilih hanya region/resource yang memang diizinkan; catat kode error dan resource tanpa secret |
| Quota nol/model tidak tersedia | Periksa model/region yang didukung serta quota subscription; tidak menjanjikan kuota tambahan atau meng-upgrade ke PAYG otomatis |
| Marketplace purchase tidak diizinkan | Bukan alasan membeli offer lain; cek model dengan jalur billing yang tercakup Students |
| Kredit habis | Hentikan provider Azure; cadangan gratis terverifikasi mengikuti kontrak fallback. Tidak auto-top-up/upgrade |

Keputusan proyek setelah akun siap: Azure bisa menjadi kandidat primary sebelum freeze jika kredit/model/tools benar-benar layak. Tidak memakai Azure sebagai fallback otomatis saat ini. Aplikasi, database, worker dan portal lab tetap lokal; jumlah container tetap tiga. Belum ada perubahan source/Compose atau pemanggilan API.
