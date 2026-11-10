# M6f - Review grouping dan riwayat development, 6 November 2026

Status: **review dan gate riwayat selesai lokal; pembagian final belum selesai, M6 tetap sebagian**. **21 tes katalog/grouping lulus dalam 0,39 detik**. CLI `--require-ready` tetap exit 2: metadata VALID, 13 OPERATOR_REPRODUCED historis, 11 PLANNED, konflik HTML masih ada. Tidak mengubah status, grup atau alokasi `evaluator/catalog.json`, manifest M5, target 24 titik atau komposisi 20 laporan.

## Dasar keputusan

Source dibaca secara statis, tanpa eksekusi target baru. Nama upload pada `lab/uploads.py` disisipkan sebagai konten elemen HTML pada kondisi development UP-04, dengan kontrol escape; lima fitur HTML `lab/xss_catalog.py` memakai kelas konteks output yang sama. Dokumen operator [M5](m5-verification.md) dan [M4c](m4c-verification.md) sudah mencatat grup konservatif `html-element-output`. Tidak ada bukti baru untuk memisah grup tersebut hanya berdasarkan nama fitur atau handler yang berbeda.

`evaluator/development_history.py` menyimpan riwayat pengembangan sistem versi `system-development-history-v1`: BAC-08 dengan grup penghapusan lampiran, XSS-08 dengan DOM fragment, dan UP-04 dengan HTML elemen. Referensinya dokumen M2/M4b/M5. BL-04 belum dimasukkan karena mekanismenya masih PLANNED; kelompok yang belum diketahui tidak dihitung sebagai kandidat. Ini **riwayat development sistem**, bukan klaim model live pernah melihat atau mempelajari laporan.

Keputusan review: **jangan freeze split sekarang**. Mengubah UP-04 menjadi non-benchmark tidak menghapus pemakaian mekanisme HTML saat mengembangkan sistem. Mengganti nama grup atau ID tanpa dasar revisi mekanisme juga tidak membuktikan independensi. Perubahan identitas mekanisme memerlukan review revisi dan bukti yang sesuai; grup lama tetap tercatat dalam riwayat.

## Perubahan gate

`evaluator.catalog_audit` tetap memeriksa overlap alokasi saat ini, lalu menambahkan:

- Konflik evaluasi dengan grup yang tercatat dalam riwayat development, walaupun titik development dipindahkan alokasinya.
- Ketidakcocokan grup ID development dengan riwayatnya. Kelulusan katalog ditolak sampai revisi ditinjau, bukan diabaikan diam-diam.
- Komposisi kategori pada sepuluh area evaluasi (4 BAC, 4 XSS, 1 upload, 1 business logic) serta satu area development per kategori.
- Inventaris kandidat dari metadata reproduksi yang memiliki grup diketahui di luar grup development saat ini dan riwayatnya. Inventaris tidak memilih laporan atau mengubah alokasi.

Hasil inventaris saat review:

| Kategori | Target area | Kandidat tercatat di luar grup development | Grup konservatif | Kekurangan area |
| --- | ---: | --- | ---: | ---: |
| BAC | 4 | Belum ada | 0 | 4 |
| XSS | 4 | XSS-06 | 1 | 3 |
| Upload | 1 | UP-01, UP-02, UP-03 | 2 | 0 |
| Business logic | 1 | Belum ada | 0 | 1 |

Tiga ID upload hanya dua grup karena UP-01/02 berbagi mekanisme. Kandidat non-benchmark tidak otomatis dipromosikan menjadi evaluasi; dukungan tools/verifier produk, GT manusia dan bukti aktual tetap perlu ditinjau. Kolom kekurangan memakai **jumlah area**, bukan jumlah laporan atau grup independen. Tidak ada asumsi bahwa semua titik PLANNED mempunyai akar masalah baru yang independen.

Mempertahankan rancangan empat area XSS dengan pemisahan grup development belum dapat dipenuhi oleh kandidat yang tercatat saat ini. Target tidak diturunkan; kekurangan dicatat sebelum freeze. Mengganti kasus setelah melihat hasil model tidak diizinkan. Jika memilih perubahan cakupan di kemudian hari, keputusan itu harus dinyatakan eksplisit, bukan disamarkan sebagai perbaikan metadata.

## Pemeriksaan dan artefak

Suite 21 tes mencakup regresi metadata lama dan sembilan kasus baru: pemindahan alokasi saat seluruh metadata sintetis sudah lengkap, penggantian/penghapusan grup, penghitungan kandidat/kelompok tanpa mutasi input, pengecualian PLANNED, penyebaran development ke seluruh grup, komposisi kategori, dan referensi dokumen. Status sintetis hanya berada di memori tes; tidak ditulis ke katalog.

Artefak privat `artifacts/m6f/20261106T052907299139Z-grouping-review.json` menyimpan hasil CLI lengkap, exit 2, hasil tes yang diamati, sembilan hash input/source dan hash katalog sebelum/sesudah yang sama. Tidak mengulang suite M6e 97 tes atau reproduksi lab karena perubahan terbatas pada gate metadata. Tidak ada request target/model, perubahan service Compose, ledger, kuota, dataset/GT, commit/push/deploy.

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_catalog_audit.py -q
.\.venv\Scripts\python.exe -m evaluator.catalog_audit --require-ready
# Exit 2 berarti belum siap; bukan kegagalan runner.
```

M6 belum lulus: 11 mekanisme BAC/business logic, validator BUSINESS_LOGIC produk, pemisahan final, GT manusia dan model live tetap outstanding. Review grouping ini selesai sebagai pemeriksaan; ia tidak menyelesaikan kekurangan implementasi atau mengesahkan benchmark.
