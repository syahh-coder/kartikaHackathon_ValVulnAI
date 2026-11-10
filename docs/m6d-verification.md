# M6d - Penguatan input auditor rekaman, 6 November 2026

Status: **penguatan parser M6d selesai dan diverifikasi lokal**. M6 tetap sebagian. Batch ini tidak menambah titik lab; rekaman event individual kemudian ditambahkan pada [M6e](m6e-verification.md).

Auditor `evaluator.business_record_audit` kini membaca maksimum 16 MiB + 1 byte dari stream biner sebelum decoding UTF-8. Batas berlaku pada data yang benar-benar dibaca, termasuk file yang ukurannya berubah setelah pemeriksaan metadata. JSON dengan kunci duplikat pada tingkat mana pun atau konstanta nonstandar NaN/Infinity ditolak sebelum validasi schema/status upstream. Pesan gagal tetap tidak mengulang isi input; verdict kerentanan dan GT tetap null.

Ditambahkan delapan kasus tes untuk batas byte persis/kelebihan satu byte, ukuran pembacaan stream, kunci duplikat top-level/nested, tiga konstanta nonstandar dan UTF-8/JSON rusak. **33 tes auditor lulus dalam 0,64 detik** pada pemeriksaan pertama 6 November. Kedua artefak M6b `20261106T025141274504Z-persistence.json` dan `20261106T025450873654Z-persistence.json` diperiksa ulang dan CONSISTENT, verdict/GT null. CLI masing-masing exit 0.

Riwayat hambatan: terminal sandbox gagal membuat proses dengan `helper_unknown_error: setup refresh had errors`, dan review eskalasi sebelumnya gagal akibat batas penggunaan. Pada turn lanjutan, eksekusi berizin kembali berhasil. Hambatan verifikasi M6d sudah teratasi; tidak menjalankan ulang target/container/provider untuk pemeriksaan dua artefak lama.

Perintah pemeriksaan yang dijalankan:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_business_record_audit.py -q
.\.venv\Scripts\python.exe -m evaluator.business_record_audit artifacts/m6b/20261106T025450873654Z-persistence.json
git -c safe.directory=D:/BelajarCyberSec/kartikaHackathon diff --check
```

M6e mengekstrak pembaca JSON menjadi `read_json_record`, digunakan kembali oleh auditor trace. Suite akhir **97 tes terarah lulus dalam 33,47 detik**, termasuk seluruh 33 tes parser; hasil di `artifacts/m6e/20261106T0517285585845Z-tests.txt`. `git diff --check` lulus pada pemeriksaan sebelum pembaruan dokumentasi. Keaslian capture, validator BUSINESS_LOGIC produk, sebelas titik PLANNED dan grouping evaluasi tetap outstanding. Tidak mengubah alokasi/status katalog atau manifest M5.
