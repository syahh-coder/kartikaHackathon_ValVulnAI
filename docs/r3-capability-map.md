# R3: peta klaim dan bukti produk

7 November 2026. Pemetaan source, **bukan reproduksi ulang, GT atau hasil model**. Tujuan eksperimen mengikuti [functional-v2](evaluation.md). Tidak memperluas validator/worker.

| Subtype | Klaim yang benar-benar dicakup | Prasyarat dan bukti minimum yang harus ditinjau | Di luar cakupan |
| --- | --- | --- | --- |
| BAC-08 | Penghapusan satu lampiran milik akun lain, dengan dampak pada akses pemilik | Satu klaim; dua akun uji berbeda; objek laporan dan kontrol berbeda; kepemilikan/akses awal, kontrol operasi pada objek sendiri, respons operasi lintas akun serta keadaan objek pemilik sesudahnya. Tujuh observasi terikat objek/aktor/run/snapshot dan tidak terpotong. Penolakan tanpa kontrol lengkap tetap tidak cukup untuk membantah. | Kebocoran isi umum, perubahan pemilik, semua IDOR/BAC atau seluruh fitur portal |
| XSS-08 | Eksekusi marker fixture terdaftar di frame utama pratinjau notifikasi, pada dua akun | Empat observasi browser: pembanding inert dan probe pada masing-masing akun; JavaScript aktif, context/storage baru, screenshot, marker terikat nonce/origin/frame/rute. Refleksi teks atau tidak adanya callback saat kontrol gagal tidak cukup. | Skrip/payload bebas dari report, persistensi, eksfiltrasi, semua halaman/semua XSS |
| UP-04 | Metadata **nama** fixture upload A saat daftar dibaca B yang ditugaskan | Dua upload berkas teks tetap dengan ID berbeda serta tiga observasi browser: pembanding nama, probe nama dan label aman. Identitas permintaan/pembaca, ukuran/hash/metadata fixture, kontrol browser serta binding run/snapshot harus cocok. Upload sukses sendiri bukan dampak. | Eksekusi isi file, penimpaan, arbitrary upload, server code execution, semua subtype upload |

Referensi source: [BAC plan](../app/agent/bac.py#L12) dan [verifier](../app/agent/bac.py#L32); [XSS prerequisites](../app/agent/xss.py#L15), [verifier](../app/agent/xss.py#L30) dan [kontrol pasangan](../app/agent/xss.py#L98); [upload prerequisites](../app/agent/upload.py#L16) dan [verifier](../app/agent/upload.py#L46). Referensi line hanya penunjuk source, bukan bukti target saat ini.

## Implikasi untuk kandidat laporan

Paket `artifacts/r3/candidates-v1/` memuat **20 kandidat teks**: 8 BAC, 8 XSS dan 4 upload. Tidak ada label GT atau kondisi target yang ditetapkan asisten. Penilaian diterima/tidaknya kandidat wajib mendahului freeze.

Ini variasi penyajian klaim yang mekanismenya sudah dikenal: dua arah akun pada BAC serta satu pola klaim XSS dan satu pola nama upload. Manifest mempertahankan tiga grup akar masalah historis dan empat grup variasi/skenario **rancangan**, bukan empat snapshot yang telah dijalankan. Delapan teks XSS tidak berarti delapan celah atau mekanisme. Nama file dan ID netral; kategori/grup, kondisi dan GT hanya berada pada metadata operator privat. Laporan tidak menyertakan payload atau urutan request untuk dieksekusi.

Sebagian variasi terutama berbeda dalam penjelasan kontrol/batas klaim. Pengguna perlu menolak atau merevisi kandidat yang tidak memberi variasi teks yang layak, mengandung ambiguitas, atau belum dapat diikat ke bukti. Jangan mempertahankannya hanya agar jumlah menjadi 20. Jika jumlah diterima atau GT 10/10 tidak tercapai, catat kekurangan; jangan mengisi INVALID untuk OOS/unsupported/ambigu. Menguji teks yang sama pada dua kondisi tetap dua percobaan dari satu teks, bukan dua teks baru.

Grup yang dipertahankan: `attachment-delete-owner-check`, `dom-fragment-innerhtml`, `html-element-output`. Riwayat development/overlap UP-04 dengan grup HTML lain tetap berlaku; tidak diklaim held-out atau observasi independen. Katalog dan manifest historis tidak diubah.

## Kesenjangan input B yang masih nyata

[Ringkasan R2](r2-verification.md) hanya menampilkan urutan/tool/metode/status/jumlah respons/truncation. Projection itu aman untuk review, tetapi tidak cukup untuk setiap klaim benchmark: belum menunjukkan hubungan kepemilikan/objek pada BAC, kontrol/kejadian marker terikat pada XSS, atau hubungan upload/pembaca/nama/label aman pada UP-04.

Sebelum input B disiapkan, aplikasi harus mengikat **kasus, report/revision, scope/aturan dan snapshot** ke observasi yang benar. Fakta yang relevan kelak dapat berupa peran/objek yang dipseudonimkan, perubahan akses, status kontrol, atribut marker yang terikat, serta metadata fixture yang perlu; bukan body HTML, kredensial, narasi jawaban atau label kondisi. Ekspor tersebut harus melalui redaksi/allowlist dan kontrol akses yang sesuai. Endpoint/context builder ini **belum dibuat pada R3a**.

Jangan menyalin `CONFIRMED/REFUTED`, alasan verifier, override/catatan admin, GT, nama kondisi atau katalog ke prompt A/B. Jangan menggunakan ulang bukti kasus lain hanya karena subtype sama. Bila rekaman yang sama kelak memang relevan untuk beberapa variasi, ikat dan nyatakan penggunaannya secara eksplisit; itu bukan pengujian target baru per laporan. Bukti kosong/kurang tetap dicatat sebagai belum siap.

R1 menghasilkan **saran triage**, bukan prediksi biner eksperimen. Schema prediksi VALID/INVALID/ABSTAIN dan validasi referensi sudah disiapkan pada `evaluator/functional_v2.py`, tetapi belum dihubungkan ke dispatcher provider. A/B dispatch runner, bukti B tervalidasi, freeze privat dan model nyata masih bagian kelanjutan R3.
