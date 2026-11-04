# Draf formulir pendaftaran

Status: arsip draf isian. Pada 3 November 2026 pengguna menyatakan pendaftaran program diterima; tidak diverifikasi langsung ke platform dan tidak dikirim melalui asisten. Nama produk ValVuln AI adalah nama kerja yang diusulkan; nama tim sudah ditetapkan pengguna.

Rujukan: formulir yang ditempel pengguna, [rulebook](https://drive.google.com/file/d/1IN7FukytvtJBIbw2yPoSprEaTrZdbfMM/view) Bagian B-E, dan [S&K](https://drive.google.com/file/d/1PWLGVasB0OahUCd5gL_UCElK8cnFdK4l/view) Pasal 3-6. Rincian pembandingan di [rules-alignment.md](rules-alignment.md).

## 1. Pendaftaran tim

| Field | Isian/petunjuk |
| --- | --- |
| Nama Tim | `ukas and codex vs everbody` |
| Panjang nama | 26 karakter termasuk spasi; memenuhi batas 30 pada formulir |
| Ketua | Akun CODEPOLITAN yang sedang dipakai; sapaan formulir menunjukkan Ukasyah |
| Anggota Tim | Solo; tidak menambahkan anggota lain dan tidak menggandakan ketua yang sudah tercatat otomatis |
| Nomor WhatsApp | Isi langsung pada platform dengan nomor aktif sendiri dalam format angka internasional, misalnya prefix 62; jangan menggunakan nomor contoh sebagai data nyata |
| Alamat Lengkap | Isi alamat sebenarnya langsung pada platform |
| Provinsi dan Kota/Kabupaten | Pilih sesuai alamat sebenarnya |
| Pekerjaan | Isi status aktual pengguna; belum diketahui asisten |
| Instansi/Komunitas/Sekolah/Universitas | Isi afiliasi aktual. Jika tidak ada, ikuti opsi/kebijakan formulir; jangan mengarang institusi |

Nomor WhatsApp, alamat, dan data identitas tidak disimpan dalam dokumen ini. Pengguna sudah mengonfirmasi berusia 17 tahun atau lebih. WNI dan keikutsertaan satu tim tetap dikonfirmasi sendiri sesuai fakta.

## 2. Pengajuan ide karya

### Nama Karya

```text
ValVuln AI: Agen Validasi Laporan Kerentanan
```

Tidak ditemukan batas panjang nama karya dalam teks formulir yang diberikan. Jika UI memberlakukan batas tambahan, gunakan nama singkat `ValVuln AI` dan tempatkan penjelasan fungsi pada deskripsi.

### Deskripsi siap salin

ValVuln AI merupakan agen AI yang dirancang untuk membantu tim keamanan menghadapi penumpukan laporan bug hunter seiring meningkatnya penggunaan AI dalam penemuan dan penyusunan laporan kerentanan. Sistem membantu mengurangi beban pemeriksaan manual dengan memeriksa kesesuaian scope dan konteks aset, kemudian menyusun serta menjalankan langkah pengujian PoC pada lingkungan uji internal yang diizinkan. Setiap klaim dinilai berdasarkan bukti teknis dan dampak yang berhasil direproduksi. Hasilnya berupa status validasi, bukti request/response atau browser, serta rekomendasi tindak lanjut untuk ditinjau analis. Purwarupa difokuskan pada IDOR/broken access control, XSS, file upload, dan business logic menggunakan portal pengadaan/logistik dummy dengan data sintetis. Tujuannya mempercepat pemeriksaan dan membantu memprioritaskan temuan berbukti untuk mendukung pengamanan aplikasi IT di lingkungan satuan. Keandalannya akan dievaluasi menggunakan dataset berlabel manual, precision, recall, dan cakupan keputusan.

### Versi lebih pendek jika field membatasi panjang

ValVuln AI adalah agen AI untuk membantu tim keamanan menghadapi penumpukan laporan bug hunter seiring meningkatnya penggunaan AI. Sistem mengecek scope, menyusun pengujian PoC, menjalankan reproduksi terkontrol di lab internal, lalu menyajikan bukti teknis dan rekomendasi untuk analis. Purwarupa memakai portal pengadaan/logistik dummy dengan data sintetis, mencakup BAC/IDOR, XSS, file upload, dan business logic. Tujuannya mengurangi beban validasi manual dan membantu memprioritaskan temuan berbukti. Hasil akan dievaluasi memakai label manual, precision, recall, dan cakupan keputusan.

### Kategori

```text
Penindakan
```

Alasan: inti karya adalah pengujian aktif/reproduksi klaim kerentanan. Rulebook Bagian B memasukkan tool pengujian kerentanan otomatis berbasis AI pada Penindakan. Sebelumnya Core Infra/Dukungan Teknologi diusulkan karena sisi workflow operasional; setelah contoh pada rulebook dibaca, Penindakan menjadi rekomendasi yang lebih dekat. Ini pertimbangan positioning, bukan konfirmasi kategori dari panitia.

## 3. Pernyataan pada formulir

- WNI: pengguna mencentang jika sesuai status sebenarnya. Asisten belum memverifikasi kewarganegaraan.
- Telah membaca S&K: pengguna perlu membaca dan menyetujui sendiri dokumen tertaut sebelum mencentang. Ringkasan asisten tidak mengubah pernyataan pribadi tersebut.
- Satu peserta hanya satu tim; data pendaftaran harus akurat.
- Jangan mengisi pendaftaran seolah produk sudah selesai atau sudah dipakai TNI AD.

## 4. Yang sengaja tidak dijanjikan dalam deskripsi

- Validasi seluruh jenis kerentanan atau jaminan report pasti benar/salah.
- Persentase akurasi atau penghematan waktu yang belum diukur.
- Sistem sepenuhnya offline ketika menggunakan model API eksternal.
- Kemampuan pengujian OT yang belum diimplementasikan.
- Adopsi atau akses ke sistem asli TNI AD.

Empat kategori bug adalah sasaran MVP dalam [rencana](../plan.md), bukan pernyataan semua validator sudah dibuat. Jika scope akhir berubah material, sesuaikan deskripsi, dokumentasi dan submission secara konsisten.
