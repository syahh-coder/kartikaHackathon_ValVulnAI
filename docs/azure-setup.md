# Mengaktifkan chat AI dengan Azure Foundry

Permintaan pengguna 7 November 2026: gunakan Microsoft Azure Foundry lewat akun pelajar. Adapter Azure untuk **triage teks** dan prediksi evaluator tersedia di source. **CODE_TESTED**, bukan LIVE_VERIFIED. Tidak ada resource/subscription/billing Azure yang dibuat atau diubah asisten.

## Yang perlu Anda lakukan

1. Daftar/aktifkan [Azure for Students](https://azure.microsoft.com/en-us/free/students/) memakai akun sendiri dan verifikasi email kampus. Microsoft menawarkan US$100 selama 12 bulan tanpa kartu kredit untuk mahasiswa eligible; saldo/kelayakan akun Anda belum diperiksa. Kredit tidak dapat dipakai untuk penawaran Marketplace. Langkah akun ada di [panduan pelajar](azure-students.md).
2. Di [Azure portal](https://portal.azure.com/), buka **Subscriptions**. Pastikan subscription Students aktif, lalu periksa sisa kredit, masa berlaku dan spending limit. Ini bukan upgrade PAYG. Jika subscription/model meminta pembelian atau upgrade, jangan lanjut hanya demi menjalankan demo.
3. Buka [Microsoft Foundry](https://ai.azure.com/), pilih tenant/subscription Students tersebut. Pada resource/project, buka daftar **Models / Deployments**; nama menu dapat berbeda antarversi portal. Pilih deployment chat teks yang memang tersedia dengan kuota positif dan tarif per token yang tercakup kredit. Aplikasi ini memakai OpenAI **v1 Chat Completions**, API-key, `temperature=0`, `max_completion_tokens` dan strict JSON schema. Pilih deployment **non-reasoning** yang mendukung semuanya serta tokenizer byte-BPE yang diketahui. Agent Service, project endpoint, Responses-only, model partner dengan kontrak lain, dan Entra-only belum didukung adapter ini. Tidak perlu VM/GPU atau hosted agent.
4. Dari deployment, catat **deployment name**, **model/version**, region, tarif input/output per sejuta token dan jenis deployment. Ketersediaan harus dilihat pada akun; saldo kredit tidak menjamin semua model atau kuota. Jangan menyimpulkan kuota Students dari tabel Batch: kolom Students N/A pada Batch bukan bukti seluruh inference chat dilarang.
5. Untuk key: **Azure portal -> resource Foundry/Azure OpenAI yang memiliki deployment -> Resource Management -> Keys and Endpoint -> KEY 1 atau KEY 2**. Bisa juga melalui halaman deployment **View code / Consume** jika portal menampilkan key dan endpoint resource. Key berasal dari resource tersebut, bukan password Azure, student ID, subscription ID atau ChatGPT. Jangan tempel key di chat.
6. Salin **endpoint inference resource** yang sesuai: `https://NAMA-RESOURCE.openai.azure.com` atau `https://NAMA-RESOURCE.services.ai.azure.com`, boleh diakhiri `/openai/v1/`. Jangan pakai `/api/projects/...`, URL Playground, atau URL lengkap `/chat/completions`. Identitas response `model` dapat berbeda dari deployment name; lihat model/version pada deployment dan contoh respons di View code. Isikan identitas persis yang diharapkan. Jika respons aktual berbeda, aplikasi gagal dengan PROVIDER_DRIFT; tinjau versi sebelum memperbarui konfigurasi.

Referensi kontrak: [endpoint/deployment resmi](https://learn.microsoft.com/en-us/azure/foundry/foundry-models/concepts/endpoints), [REST v1 dan autentikasi](https://learn.microsoft.com/en-us/rest/api/microsoft-foundry/azureopenai/chat), [structured outputs dan contoh identitas model](https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/structured-outputs), [kuota](https://learn.microsoft.com/en-us/azure/foundry/openai/quotas-limits). Portal privat akun pengguna belum diinspeksi.

## Tempat memasukkan konfigurasi

File privat di laptop: **`D:\BelajarCyberSec\kartikaHackathon\.env.azure`**. File ini sudah dibuat bila sebelumnya belum ada; tidak ditimpa bila sudah ada. Tidak dimasukkan Git, image build atau source ZIP. Template publik: [`.env.azure.example`](../.env.azure.example).

Di PowerShell dari folder proyek:

```powershell
notepad .env.azure
```

Isi field berikut sesuai akun sendiri:

| Field | Isi |
| --- | --- |
| `VALVULN_AZURE_API_KEY` | KEY 1/KEY 2 resource |
| `VALVULN_AZURE_ENDPOINT` | Endpoint resource, sesuai langkah di atas |
| `VALVULN_TRIAGE_MODEL` | **Deployment name** persis, bukan nama katalog jika berbeda |
| `VALVULN_AZURE_EXPECTED_MODEL` | Identitas model/version yang diharapkan pada respons |
| `VALVULN_TRIAGE_PRICE_SNAPSHOT` | Catatan bertanggal: region, deployment, versi, tarif dan status kredit; tanpa secret |
| `VALVULN_TRIAGE_PROMPT_USD_PER_MILLION` | Tarif penuh input USD/sejuta token; hapus `#` di awal baris |
| `VALVULN_TRIAGE_COMPLETION_USD_PER_MILLION` | Tarif output USD/sejuta token; hapus `#` |
| `VALVULN_TRIAGE_USD_TO_IDR` | Kurs konservatif USD/IDR yang Anda periksa; hapus `#` |
| `VALVULN_TRIAGE_RESERVATION_IDR` | Minimal hasil pemeriksaan lokal di bawah, positif dan <=budget |
| `VALVULN_TRIAGE_ACCESS_VERIFIED` | `true` sesudah kredit, kuota dan jalur pembayaran diperiksa |
| `VALVULN_TRIAGE_TOKEN_BOUND_VERIFIED` | `true` sesudah tokenizer byte-BPE dipastikan |
| `VALVULN_AZURE_API_CAPABILITIES_VERIFIED` | `true` sesudah kontrak chat non-reasoning/JSON di atas dipastikan |

Template sudah memilih provider `azure`, tier `PROMO_CREDIT`, budget Rp50.000 dan retry mati. Jangan isi tarif nol hanya karena memakai kredit hibah. Angka fixture tes bukan tarif Azure. Key **saja** belum mencukupi; endpoint, deployment dan kelayakan akses juga diperlukan.

Periksa tanpa memanggil Azure atau menampilkan nilai key:

```powershell
.venv\Scripts\python.exe -m scripts.check_azure_config
```

Saat tarif/kurs sudah diisi, output `minimum_reservation_idr` menghitung pembulatan ke atas biaya maksimum 8192 input +1024 output token. Isi reservasi setidaknya sebesar hasil itu. Pemeriksaan mengembalikan `CONFIGURATION_REQUIRED` bila ada field/bukti konfigurasi belum lengkap (exit 2), `CONFIGURATION_INVALID` jika tipe/nama field salah, atau `CONFIGURED_NOT_VERIFIED` bila konfigurasi lokal lengkap. Ini **nol request cloud**, bukan uji key, kuota, kredit atau model. Jangan menyetel semua flag true hanya agar pesan hilang. Hindari environment PowerShell `VALVULN_*` lama yang dapat menimpa file saat pemeriksaan host.

## Menyalakan pada web yang sedang dipakai

Saat ini web pada **http://127.0.0.1:8010** tetap MOCK. Setelah checker lengkap, tunggu triage aktif selesai, lalu jalankan:

```powershell
docker compose -p valvuln-review -f compose.preview.yaml -f compose.azure.yaml up -d --build app
```

Overlay ini memakai **project, volume dan ledger preview yang sama**, `valvuln-review_preview_data`; tidak membuat database baru untuk menghapus biaya. Hanya app menerima key. Worker/lab dan instalasi lama pada8000 tidak diperbarui. Planner tetap mock dan dispatcher target mati. Jangan mengganti project name, mereset volume, atau menjalankan `down -v`. Jangan jalankan provider lain pada database berbeda sebagai cara menambah budget; seluruh penggunaan proyek harus tetap diperhitungkan.

Refresh Brave, login **hunter-a**, pilih/buat percakapan, kirim teks laporan, lalu klik **Minta saran AI**. Tombol itu memanggil Azure secara eksplisit melalui ledger. Menyimpan guideline, membuka Ringkasan observasi, refresh, startup dan restart **tidak** memanggil AI. Ringkasan observasi tetap dibuat aplikasi dari bukti tersimpan; saran AI muncul pada triage percakapan. Saran AI tidak mengubah verdict atau menjalankan worker.

Readiness lokal bisa dibaca tanpa secret:

```powershell
Invoke-RestMethod http://127.0.0.1:8010/api/readiness
```

Sesudah overlay, `triage_mode=live`, `triage_provider=azure`; konfigurasi lengkap berstatus `CONFIGURED_NOT_VERIFIED`. `CONFIGURATION_REQUIRED` berarti field masih belum sah, tanpa fallback ke mock. Restart tidak menghasilkan bukti live; hanya respons aktual yang berhasil dan rekaman attempt/usage terkait dapat membuktikan integrasi live. Readiness memang tidak otomatis menjamin key/model aktif.

Jika ingin kembali ke simulasi setelah seluruh request selesai:

```powershell
docker compose -p valvuln-review -f compose.preview.yaml up -d app
```

Riwayat dan cadangan biaya live tetap ada. Perubahan mode tidak melepaskan biaya unknown atau mengulang request lama.

## Biaya dan batas evaluasi

Azure v1 memberi token usage; adapter tidak menganggap field biaya tambahan atau perkalian tarif sebagai tagihan aktual Azure. Respons tetap `COST_UNKNOWN`, seluruh reservasi ditahan pada ledger. Timeout, penolakan, error dan pembatalan juga tidak dianggap nol biaya. Saat total reservasi/pemakaian mencapai batas, dispatch berhenti. Kredit hibah dan pengeluaran rupiah pribadi tetap hal berbeda; batas proyek tidak dinaikkan otomatis.

Evaluator teks sudah memakai pemilihan provider dan redaksi key Azure yang sama. Profil menyimpan endpoint dan model yang diharapkan supaya perubahan terdeteksi saat freeze. **Freeze/jadwal A/B tetap terhalang biaya smoke yang belum direkonsiliasi**, serta GT/bukti manusia yang belum tersedia. Tidak ada rekonsiliasi tagihan otomatis atau klaim Azure benchmark selesai. Gunakan ledger aplikasi yang benar bila melanjutkan evaluator; Compose evaluator default pada instalasi8000 menggunakan volume berbeda dari preview8010. Jangan menjadikannya ledger live kedua. [Runbook R3](r3-runbook.md).

Hasil tes dan lokasi artefak: [verifikasi Azure](azure-verification.md); seluruh kebutuhan review: [final-review.md](final-review.md).
