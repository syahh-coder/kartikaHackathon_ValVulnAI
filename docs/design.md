# Desain UI ValVuln AI

**Pembaruan arah visual 13 November 2026 ("SEGEL"):** arah visual diperbarui menjadi sistem desain editorial **SEGEL** (mode terang default: Bone `#EEEAE0`, Chalk `#F7F5EF`, Ink `#111114`, aksen Cobalt `#1B35E8`, serta mode gelap seimbang; warna status hanya pada data verdict nyata). Seluruh kontrak keamanan, pemisahan label `MOCK`/`LIVE`, batas worker/API, serta alur review/publikasi pada R2–R4 tetap berlaku tanpa perubahan. Pada R2 tambahkan label model/provider aktual, mode inference, mode pemeriksaan lab, prediksi/saran AI dan hasil verifier secara terpisah. Dukungan aktif hanya subtype BAC-08/XSS-08/UP-04; business logic tetap belum didukung untuk validasi lab. Saran model tidak menjadi tombol eksekusi baru atau keputusan izin. Tidak membangun UI besar/review bisnis baru. Ini spesifikasi belum diimplementasikan; [cakupan aktif](submission-scope.md).

Status 5 November 2026: baseline grafit + sage diterima pengguna pada 4 November. UI M3 memakai session/API aktual; M4b menambah pemilih BAC/XSS pratinjau, label browser aktual/planner mock serta review/ringkasan aman. [Hasil M4b](m4b-verification.md), [M3](m3-verification.md). Model live dan widget PNG mentah belum tersedia. Prototipe tetap simulasi; spesifikasi lanjutan belum seluruhnya diimplementasikan.

Rujukan: [architecture.md](architecture.md), [user-flow.md](user-flow.md), [security-review.md](security-review.md), dan [implementation.md](implementation.md).

## 1. Arah desain

Antarmuka utama berupa percakapan seperti ChatGPT: daftar percakapan di kiri, chat dan lampiran di tengah, detail pemeriksaan dapat dibuka di kanan. Tidak memakai form panjang atau tabel dashboard sebagai halaman pertama. Satu percakapan menangani satu laporan utama; chat membantu melengkapi informasi, sedangkan kartu pemeriksaan memperlihatkan proses dan bukti aktual.

Dua role platform memakai aplikasi yang sama: **Bug hunter** dan **Admin program**. Keduanya bisa chat serta mengunggah laporan. Admin mempunyai menu terpisah untuk laporan program dan guideline. Role ditentukan server saat login, bukan tombol pilihan untuk menjadi admin.

MVP memiliki satu program: **Portal Pengadaan & Logistik — Lab Demo**. Tetap ada layar pilih program untuk menunjukkan konteks izin; tidak ada tombol membuat program atau input alamat target bebas. Akun requester/approver adalah identitas uji target dan tidak tampil sebagai role login platform.

## 2. Tampilan dan token

Arah visual aktif ("SEGEL"): homepage menceritakan alur klaim disegel melewati Scope Gate, Worker Sandbox, dan Target Lab dengan satu kanvas WebGL Three.js minimal (serta fallback bertingkat hingga SVG statis), bidang warna utuh per layar (`Bone → Cobalt → Ink → Bone → Cobalt`), tipografi kontras tinggi, dan ruang kerja pasca-login yang tenang berbasis garis tipis tanpa kartu bersarang atau dekorasi AI generik. Konten dinamis tetap ditampilkan inert melalui `.textContent`. Spec visual tetap fleksibel untuk penyempurnaan tanpa mengunci kelas HTML non-fungsional di luar kontrak selektor QA.

| Token | Nilai | Penggunaan |
| --- | --- | --- |
| Latar | `#191C1A` | Halaman dan sidebar |
| Surface | `#202421` | Composer, kartu, drawer |
| Surface aktif | `#282D29` | Item terpilih dan hover |
| Teks utama | `#E6E9E4` | Judul/isi |
| Teks sekunder | `#A5ADA4` | Petunjuk/metadata |
| Border | `#343C34` | Pemisah |
| Aksen | `#B1C9A9` | Tombol/tindakan utama |
| Perhatian | `#E2C58D` | Klaim terbukti/perlu review |
| Kontrol selesai | `#B1C9A9` | Langkah berhasil; bukan aplikasi aman |
| Error | `#EFACA2` | Gagal/diblokir |

Tipografi self-hosted (`app/static/fonts/`, `font-display: swap`): Display `Newsreader` (variable opsz, 300–500 + italic terbatas), UI/Body `Schibsted Grotesk` (17px, line-height 1.6; minimum fungsional 14px), dan Mono bukti/ID/hash `Spline Sans Mono` (400/500, >= 14px, tanpa letter-spacing). Sidebar sekitar 248 px, konten chat maksimal sekitar 800 px, drawer bukti 360–440 px jika ruang cukup. Pada laptop 1366 × 768, drawer dapat menutup sebagian area chat; pada layar kecil menjadi panel layar penuh. Composer tetap mudah dijangkau tanpa menutupi pesan terakhir. Gunakan focus state, label input dan ikon beserta teks. Kontras dan akses keyboard perlu diverifikasi saat UI dibangun.

## 3. Login dan pilihan program

Layar login: nama produk, username, password, tombol **Masuk**. Tidak ada pilihan role, pendaftaran publik, atau kredensial yang ditulis langsung pada halaman. Error login bersifat umum dan tidak membedakan akun ada/tidak. Jika session habis, minta login ulang; jangan memindahkan draft sensitif ke localStorage.

Sesudah login, kartu program memperlihatkan nama, label **Lab demo · data sintetis**, role pengguna dan versi guideline aktif. Tombol **Buka program** masuk ke chat. Jika guideline belum aktif, bug hunter dapat membaca informasi yang tersedia dan menyiapkan draft; validasi target belum bisa dimulai. Admin mendapat tindakan **Siapkan guideline**.

## 4. Shell chat bug hunter

```text
+----------------------+--------------------------------------------------+
| ValVuln AI            | Portal Pengadaan & Logistik · Lab Demo           |
| [Laporan baru]        | [Lihat guideline vN]            [Mode: Simulasi]  |
|                      +--------------------------------------------------+
| Laporan saya         |                                                  |
| <percakapan aktual>   |              Validasi laporan kerentanan         |
|                      |       Tulis laporan atau lampirkan TXT/MD.       |
|                      |                                                  |
|                      | <pesan pengguna dan kartu lampiran>              |
|                      | <klarifikasi / kartu pemeriksaan aktual>         |
|                      |                                                  |
|                      | [Ringkasan scope] [Status] [Hasil per klaim]      |
|                      |                                                  |
|                      | [Lampirkan] Tulis pesan...             [Kirim]   |
| Ukasyah · Bug hunter  | TXT/MD · maks. 128 KiB · batas teks ditampilkan   |
| [Keluar]             |               [Validasi laporan]                 |
+----------------------+--------------------------------------------------+
```

- Empty state mengajak menulis/unggah laporan; tidak menampilkan jumlah temuan atau riwayat palsu.
- Upload menampilkan nama, ukuran, status parsing, cuplikan teks aman dan tombol hapus sebelum dikirim. PDF/OCR/DOCX/arsip belum didukung; jelaskan format yang diterima sebelum memilih file.
- **Kirim** menambah pesan/menyusun draft. **Validasi laporan** mengunci snapshot dan memulai pemeriksaan scope; tidak berarti target sudah diakses. Pesan baru tidak otomatis membuat pengujian berulang.
- Bila beberapa klaim ditemukan, tampilkan pilihan klaim utama. Klaim lain ditandai belum diperiksa.
- Guideline aktif hanya-baca. Scope yang diklaim dalam report tidak mengubah aturan program.
- Mode dipilih/dikonfigurasi operator/admin untuk demo dan terlihat jelas; bug hunter tidak dapat mengaktifkan pengeluaran/provider bebas. Live tanpa konfigurasi memberi error, tidak berganti ke mock diam-diam.
- Nama model tampil di samping mode pada header. Prototipe memakai `Simulasi · Qwen3-Coder`; klik nama model membuka ID `qwen/qwen3-coder`, akses rencana OpenRouter dan status belum terhubung. Pada ponsel keduanya tersusun dua baris. Saat backend tersedia, identitas harus berasal dari konfigurasi/run aktual; label prototipe tidak menjadi bukti model live.
- Rencana multi-provider 4 November: detail run menampilkan provider/model aktual, tier akses dan kejadian fallback beserta alasan tersanitasi. Tampilkan misalnya perpindahan OpenRouter ke Gemini ketika benar-benar terjadi; tidak menyebut Gemini/Grok/OpenAI gratis hanya karena provider dipilih. Bug hunter tidak dapat mengganti key/provider atau mengaktifkan paid tier. Belum ada perubahan kontrol prototipe; data server mengikuti prd.md dan architecture.md.
- Daftar/hasil hanya laporan sendiri. Bug hunter tidak menerima data laporan orang lain dari API, termasuk melalui pencarian, polling, lampiran atau ekspor.

## 5. Kartu scope, proses dan hasil

Satu balasan pemeriksaan berisi kartu bertahap. Urutannya:

1. **Scope**: program, versi guideline, aset alias, klaim utama dan alasan singkat.
2. **Pengujian**: menunggu/berjalan/selesai, langkah yang benar-benar terjadi, tombol **Hentikan** saat relevan.
3. **Hasil klaim**: terbukti/terbantahkan/belum dapat dipastikan, batas kesimpulan dan tindak lanjut.
4. **Bukti yang dibagikan**: ringkasan tersanitasi yang telah disetujui admin, jika ada.

Jika `OUT_OF_SCOPE`, tampilkan **Di luar scope — pengujian internal tidak dijalankan** dan rujukan aturan publik. Jika `UNKNOWN`, tampilkan pertanyaan spesifik dan **Pengujian belum dimulai**. Jangan menampilkan timeline koneksi Docker pada dua kondisi tersebut.

Bug hunter melihat status proses dan hasil teknis tersanitasi. Sebelum detail bukti dipublikasikan, tampilkan **Bukti detail menunggu tinjauan admin**. Jangan mengisi request/response internal ke DOM lalu menyembunyikannya. Pesan yang menyebut layanan internal memakai alias, bukan hostname/IP/credential.

Timeline menggunakan event aktual dari server; tidak memakai persentase palsu berdasarkan waktu. Ringkasan rencana berbeda dari hasil observasi. Pesan model bukan bukti sistem, dan tidak menampilkan chain-of-thought; cukup alasan keputusan, tindakan terstruktur serta rujukan bukti.

## 6. Tampilan admin program

Admin memakai shell chat yang sama dengan tambahan navigasi:

- **Laporan saya** untuk percakapan yang dibuat sendiri.
- **Laporan program** untuk antrean semua laporan pada program, dengan filter proses/verdict/pemilik.
- **Guideline program** untuk draf, review dan aktivasi versi.

Laporan program adalah tampilan tambahan, bukan pengganti chat utama. Saat membuka laporan, admin melihat percakapan, ringkasan hasil dan drawer **Bukti internal**. Drawer menghubungkan action/evidence ID, akun alias, request/response teredaksi, kontrol pembanding serta batas pengujian. Screenshot/DOM mentah hanya admin, tetap tanpa secret saat capture. Artefak aktif selalu ditampilkan inert dan tidak dirender pada origin UI.

Panel review berisi hasil agent asli, keputusan admin, alasan dan rujukan bukti. Tombol **Bagikan ringkasan ke pelapor** menerbitkan projection tersanitasi. Koreksi tidak menimpa hasil agent mentah. Admin program tidak diberi UI reset evaluator, daftar 24 jawaban, pemilihan kondisi rentan/perbaikan, atau Docker control.

## 7. Guideline program

Guideline tidak dicampur ke composer report. Layar admin dibagi menjadi:

```text
Guideline program                       Aktif: vN

[Unggah TXT/MD]  [Isi manual]
Sumber: <nama file, hash, waktu>          Status: Draf

Aset terdaftar       <pilih alias dari binding operator>
In-scope            <fitur/metode/kategori yang diizinkan>
Out-of-scope        <pengecualian>
Aturan bisnis       <hak akses dan prasyarat>

[Pratinjau aturan publik] [Bandingkan versi] [Aktifkan versi]
```

Ekstraksi AI, bila dipakai, diberi label **Usulan — belum aktif**. Admin dapat memperbaiki draf sebelum mengaktifkan. Backend menolak aset tak terdaftar dan aturan bertentangan. Tindakan aktivasi menampilkan dampak konkret: job versi lama yang antre dibatalkan dan tindakan run aktif dihentikan; setelah itu hanya run baru memakai versi baru. Ini tindakan konfigurasi khusus, bukan permintaan izin berulang untuk setiap langkah pengujian.

Bug hunter hanya melihat versi publik: aset alias, in-scope, out-of-scope, aturan/prasyarat dan waktu aktivasi. Binding Docker dan rahasia akun tidak ditampilkan.

## 8. Label dan kondisi gagal

| Data | Label utama | Tindakan |
| --- | --- | --- |
| `IN_SCOPE` | Sesuai scope | Belum menyatakan bug valid |
| `OUT_OF_SCOPE` | Di luar scope | Rujuk aturan; tidak ada pengujian target |
| `UNKNOWN` / `NEEDS_INFO` | Informasi belum lengkap | Lengkapi jawaban; tidak ada pengujian target |
| `UNSUPPORTED` | Pengujian belum didukung | Review manual; bukan laporan palsu |
| `RUNNING` | Pengujian berjalan | Lihat langkah / hentikan |
| `COMPLETED` | Pemeriksaan selesai | Baca verdict terpisah |
| `CONFIRMED` | Klaim terbukti | Tampilkan dampak spesifik dan bukti |
| `REFUTED` | Klaim terbantahkan | Jelaskan bukti penyangkal dan kondisi |
| `INCONCLUSIVE` | Belum dapat dipastikan | Tampilkan informasi/kontrol yang kurang |
| `PROVIDER_REFUSED` | Model menolak permintaan | Bukan verdict teknis |
| `CONFIGURATION_REQUIRED` | Konfigurasi belum siap | Admin/operator memeriksa konfigurasi |
| `POLICY_BLOCKED` | Tindakan diblokir | Alasan aman untuk role terkait |
| `FAILED` | Proses gagal | Simpan draft/trace; ulangi eksplisit bila siap |
| `CANCELLED` | Dihentikan | Hasil lama tidak dihapus |

Tombol nonaktif disertai alasan dan tindakan prasyarat. Queue penuh, budget habis, upload gagal atau session habis tidak menghapus draft server. Tidak menampilkan skor AI slop, confidence tanpa kalibrasi, atau kesimpulan aplikasi aman.

## 9. Evaluasi dan kejujuran demo

Halaman evaluasi bukan menu bug hunter. Evaluator mengelola GT di luar runtime agent; admin hanya dapat melihat hasil agregat yang sudah diekspor/disetujui, bukan manifest jawaban. Sebelum eksperimen, tulis **Belum dijalankan**, metrik **N/A**. Sesudahnya tampilkan jumlah aktual, mode, konfigurasi, coverage, precision/recall/strict accuracy dan error. Batch sebagian tidak dianggap seluruh 20 kasus selesai.

Setiap fixture desain ditandai **Contoh tampilan — bukan hasil validasi**. Mode mock/replay selalu terlihat; tidak boleh menyerupai bukti model live. Program dan data portal diberi label demo/sintetis, tanpa klaim adopsi instansi.

## 10. Urutan pembuatan layar

1. Login, pilih program, shell chat, empty state dan guideline hanya-baca.
2. Composer TXT/MD, snapshot report dan kartu scope tanpa akses target.
3. Satu alur BAC development nyata: status, pembatalan, ringkasan dan drawer bukti admin.
4. Pengaturan guideline terversi, review/publikasi hasil dan ekspor sesuai role.
5. Bukti browser/keluarga bug lain dan hasil evaluasi aktual setelah backend tersedia.

Prototipe interaktif ada pada [ui-prototype/README.md](../ui-prototype/README.md). Pemilihan 11 referensi ada di [design-references.md](design-references.md). Gate UI sudah dipenuhi pengguna pada 4 November; mulai M1 di chat baru tanpa konfirmasi visual ulang. Pertahankan baseline yang diterima dan lakukan perbaikan UI yang relevan saat implementasi. Autentikasi/policy dan pengujian pada [security-review.md](security-review.md) tetap harus membuktikan batasnya sebelum demo membuka validasi internal kepada user lain. Penambahan dua role/scope management menambah beban terhadap target sekitar 30 jam; kerjakan alur minimum dahulu, hindari halaman statistik dan pengelolaan akun besar.
