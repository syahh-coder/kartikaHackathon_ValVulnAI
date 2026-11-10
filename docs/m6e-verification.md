# M6e - Rekaman event kontrol alur bisnis normal, 6 November 2026

Status: **potongan defensif M6e selesai lokal; M6 keseluruhan tetap sebagian**. Suite terarah **97 tes lulus dalam 33,47 detik**: 33 auditor/parser, 32 trace baru, empat probe persistensi dan 28 kontrol bisnis. Transport HTTP nyata diblokir oleh fixture tes. Tidak menjalankan suite penuh lintas reproduksi lab.

`evaluator.business_trace_audit` memeriksa rekaman terstruktur untuk fixture empat event `CREATE -> SUBMIT -> APPROVE -> FULFILL`, aturan `procurement-controls-v1`. Schema membatasi ukuran daftar/field dan menolak field asing, integer tidak ketat, versi format berbeda serta nilai non-finite. Pembacaan file menggunakan parser M6d dengan batas 16 MiB dan penolakan kunci duplikat/konstanta JSON nonstandar. Auditor tidak mengimpor lab, menghubungi target atau menjalankan instruksi dalam record.

Pemeriksaan mencakup ID event unik, request/actor binding, state sebelum/sesudah yang bersambung, versi dan urutan, kestabilan barang/jumlah/unit pada fixture tanpa EDIT, metadata owner/staff-unit, larangan approval sendiri, approved_by, pengurangan stok, binding fulfillment serta state agregat. Kedua fase harus mempunyai trace dan snapshot yang sama. EDIT/variasi alur lain belum didukung auditor ini. Metadata aktor hilang/versi aturan belum didukung/trace kurang menghasilkan INCOMPLETE; kontradiksi rekaman menghasilkan INCONSISTENT. Output tidak menyalin nilai input mentah.

## Pemeriksaan alur aktual

`scripts.m6e_trace_check` membuat database baru dalam direktori sementara, memakai probe alur normal M6b via ASGI, membaca jurnal dan metadata aktor/unit yang relevan dalam satu transaksi baca, kemudian mengulang lifecycle aplikasi dan pemenuhan yang sama. Tidak menerima URL/database proyek dari command line. Password sintetis dibuat di memori; ekspor memilih field jurnal/state/ID dan metadata unit, tanpa password/hash/session/CSRF. Database uji dibersihkan oleh TemporaryDirectory.

Hasil runner dan CLI offline masing-masing exit 0, CONSISTENT:

- Empat event dan ID sama pada kedua fase; owner membuat/mengirim, petugas berbeda menyetujui/memenuhi.
- Stok 100 -> 93 untuk tujuh barang, request FULFILLED versi 4, satu fulfillment; replay tidak menambah event atau fulfillment.
- Rekaman `artifacts/m6e/20261106T051819793903Z-normal-trace.json` dengan SHA-256 `f5ee46fb37cab59771888383a4600b14efce7968c19d25d20c2f209795f58e4f`.
- Ringkasan `artifacts/m6e/20261106T051819793903Z-audit.json`; hash sepuluh source ada pada record. Hasil tes pada `artifacts/m6e/20261106T0517285585845Z-tests.txt`.

Pemeriksaan akhir lulus: sintaks lima file Python, link lokal/fence tujuh dokumen, whitespace source dan `git diff --check`, kesesuaian hash record serta seluruh sepuluh hash source, dan pemeriksaan field credential/session pada ekspor. Hasil di `artifacts/m6e/20261106T051819793903Z-final-checks.json`. Pemeriksa whitespace awal sempat menolak spasi hard-break Markdown yang sah di plan.md; pemeriksa diperbaiki tanpa menghapus format dokumen.

Ini **dua lifecycle ASGI dalam proses host yang sama**, bukan traffic TCP atau restart proses/container. Bukti persistensi dua container tetap hasil historis M6b; tidak diulang batch ini. Tidak mengubah service Compose aktif dari M5, data/volume/ledger/kuota proyek atau manifest operator terdahulu. Tidak memanggil model live, commit/push/deploy atau membuat label GT.

## Riwayat kegagalan dan batas

Suite pertama menghasilkan 96 passed/1 failed dalam 20,85 detik. Mock generator secret pada tes integrasi mengembalikan token identik, sehingga login akun kedua gagal dengan `UNIQUE constraint failed: sessions.token_hash`. Fixture diperbaiki agar setiap token unik; aturan/session aplikasi tidak diubah. Ringkasan kegagalan dipertahankan pada `artifacts/m6e/initial-test-failure.txt`.

CONSISTENT membuktikan kecocokan rekaman kontrol normal yang diamati. Capture dan metadata aktor/unit tidak ditandatangani; hasil ini tidak mengesahkan keaslian origin, penegakan izin pada aksi lain, atau dampak kerentanan. `vulnerability_verdict` dan `ground_truth` selalu null. Auditor tetap evaluator host dan belum terhubung ke worker/assessment/UI BUSINESS_LOGIC produk.

Gate katalog ulang tetap **VALID, exit 2 saat --require-ready**: 13 OPERATOR_REPRODUCED historis, 11 PLANNED dan konflik UP-04 development dengan XSS-01..04 evaluasi. Status/grup katalog tidak diubah. M6 belum lulus dan M7/model live/benchmark belum dimulai.

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_business_record_audit.py tests/test_business_trace_audit.py tests/test_business_persistence_probe.py tests/test_lab_business_controls.py -q
.\.venv\Scripts\python.exe -m scripts.m6e_trace_check
.\.venv\Scripts\python.exe -m evaluator.business_trace_audit artifacts/m6e/20261106T051819793903Z-normal-trace.json
.\.venv\Scripts\python.exe -m evaluator.catalog_audit --require-ready
# Exit 2 di atas berarti katalog belum siap.
```

Langkah berikutnya: tinjau pemisahan development/evaluasi berdasarkan akar masalah sebelum freeze. Kelengkapan 24 titik dan validator BUSINESS_LOGIC produk tetap pekerjaan terpisah; audit normal ini tidak menaikkan hitungan kerentanan.
