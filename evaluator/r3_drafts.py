"""Create NEW private R3 candidate packets and import explicit human review CSV.

No GT is inferred from text, verifier output or target condition. No network.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path

from evaluator.functional_v2 import DraftCase, DraftManifest, EvaluationError, GroundTruth, GROUPS, read_manifest, readiness, schedule, write_new

# Text-quality variants of known claims, not independent vulnerabilities or GT.
# No report contains an executable payload or a request sequence.
BAC = [
    ("a-to-b", "Saya melaporkan bahwa penguji A dapat menghapus lampiran milik B pada portal pengadaan lab. Dampaknya harus berupa hilangnya akses pemilik ke lampiran itu, bukan sekadar pesan sukses. Klaim ini hanya menyangkut satu lampiran pada snapshot kasus."),
    ("b-to-a", "Pada portal pengadaan lab, penguji B diduga dapat menghapus lampiran milik A. Saya meminta penilaian atas dampak kehilangan lampiran oleh pemiliknya; keberhasilan operasi pada lampiran milik penguji sendiri hanya pembanding."),
    ("a-to-b", "Klaim utama saya adalah penghapusan lampiran lintas pemilik, dengan A sebagai penguji dan B sebagai pemilik objek laporan. Batas izin yang dipersoalkan adalah perubahan objek B oleh A. Lampiran pembanding A harus dibedakan dari objek laporan B."),
    ("b-to-a", "Lampiran milik A dilaporkan dapat dihapus oleh B yang tidak memilikinya. Perubahan status daftar saja belum cukup: dampak yang saya klaim ialah A tidak lagi dapat membaca objek laporan yang sebelumnya tersedia."),
    ("a-to-b", "Laporan ini menyatakan lampiran B hilang setelah tindakan akun A, walaupun A bukan pemiliknya. Fokus penilaian adalah hubungan tindakan lintas akun dengan hilangnya objek, bukan kemampuan melihat nama file di daftar."),
    ("b-to-a", "Saya melaporkan penghapusan lampiran A oleh akun B pada satu snapshot portal lab. Untuk klaim ini, akses awal pemilik dan fungsi normal pada lampiran pembanding perlu ditinjau agar kegagalan biasa tidak disamakan dengan dampak lintas akun."),
    ("a-to-b", "Akun A dilaporkan bisa mengubah ketersediaan lampiran milik B melalui penghapusan tanpa kepemilikan. Ruang klaim hanya penghapusan tersebut; saya tidak mengklaim kebocoran isi, perubahan identitas pemilik atau gangguan seluruh portal."),
    ("b-to-a", "Klaim saya: batas kepemilikan lampiran tidak mencegah B menghapus objek milik A. Kehilangan akses oleh A terhadap objek laporan adalah dampak yang perlu dinilai pada snapshot yang sama, terpisah dari objek kontrol B."),
]
XSS = [
    "Saya melaporkan eksekusi marker lokal pada pratinjau notifikasi portal lab, bukan sekadar tampilnya teks masukan. Klaim dibatasi pada frame utama pratinjau dan fixture produk yang tersedia, dengan pembanding inert dan pemeriksaan pada dua akun uji.",
    "Klaim utama laporan ini adalah marker notifikasi dieksekusi pada halaman pratinjau untuk kedua akun uji. Tampilan karakter khusus saja tidak menjadi bukti; hasilnya perlu dibedakan dari kontrol teks inert pada konteks browser baru.",
    "Pratinjau notifikasi diduga memperlakukan fixture marker sebagai konten yang dieksekusi di browser. Saya tidak mengklaim persistensi setelah navigasi atau dampak pada halaman lain. Fokusnya adalah eksekusi lokal pada dua akun dalam snapshot kasus.",
    "Saya melaporkan bahwa halaman pratinjau notifikasi memicu marker lokal di frame utamanya. Batas laporan hanya perilaku fixture terdaftar. Dukungan JavaScript dan kontrol inert perlu diperhatikan agar browser yang gagal tidak dianggap menolak klaim.",
    "Laporan ini menyatakan ada eksekusi marker, bukan hanya refleksi nama atau isi notifikasi, pada pratinjau portal lab. Klaim berlaku untuk pasangan akun uji yang diperiksa pada snapshot yang sama dan tidak mencakup pembacaan cookie atau pengiriman data.",
    "Pada fitur pratinjau notifikasi, fixture marker dilaporkan aktif sementara teks pembanding tetap inert. Saya meminta penilaian atas klaim eksekusi di kedua akun; hasil pada satu akun saja belum mendukung keseluruhan klaim ini.",
    "Klaim kerentanan saya berada pada frame utama pratinjau notifikasi: konten fixture dilaporkan mengeksekusi marker lokal. Kemunculan kata marker di cuplikan halaman bukan dampak yang diklaim, dan bukti lintas halaman tidak termasuk kasus ini.",
    "Saya melaporkan masalah eksekusi pada pratinjau notifikasi dengan batas fixture produk. Dampak yang diklaim ialah marker lokal benar-benar teramati pada dua sesi uji baru. Saya tidak mengklaim penyimpanan permanen, navigasi ke situs lain, atau eksekusi skrip bebas.",
]
UPLOAD = [
    "Saya melaporkan bahwa nama lampiran fixture yang diunggah A dapat mengeksekusi marker lokal saat daftar lampiran dibaca B yang ditugaskan pada permintaan itu. Klaim hanya menyangkut penyajian metadata nama file, bukan eksekusi isi berkas atau penimpaan file lain.",
    "Klaim utama laporan ini adalah eksekusi marker melalui nama lampiran pada halaman daftar permintaan lab, dengan pengunggah A dan pembaca B yang sah. Upload berhasil saja tidak membuktikan klaim; pembanding nama inert dan tampilan label aman perlu dibedakan.",
    "Nama lampiran pada daftar permintaan dilaporkan diperlakukan sebagai konten aktif ketika B membaca hasil unggahan fixture A. Batas dampak adalah marker lokal pada frame utama daftar, bukan isi dokumen, akses lintas permintaan, atau perubahan berkas lain.",
    "Saya melaporkan eksekusi marker dari metadata nama lampiran yang dibuat A dan dilihat B pada permintaan tempat B ditugaskan. Penilaian dibatasi fixture nama file dan snapshot kasus, dengan pembanding inert serta jalur label aman; tidak ada klaim server menjalankan isi file.",
]

CSV_FIELDS = ["report_id", "report_sha256", "decision", "gt", "reviewer", "rationale", "target_snapshot", "condition_reference", "scope_version", "rules_version", "evidence_reference"]


def prepare(directory: Path) -> DraftManifest:
    # mkdir without exist_ok is deliberate: never overwrite an earlier packet/GT.
    directory.mkdir(parents=True, exist_ok=False)
    (directory / "reports").mkdir()
    entries = []
    for i in range(8):
        direction, text = BAC[i]
        entries.append(("BAC-08", "attachment-delete-" + direction, "bac-claim-" + direction, text))
        entries.append(("XSS-08", "notification-preview-two-accounts", "notification-dom-claim", XSS[i]))
        if i % 2 == 0:
            entries.append(("UP-04", "upload-name-assigned-reader", "upload-name-claim", UPLOAD[i//2]))
    cases = []
    for index, (subtype, scenario, variant, text) in enumerate(entries, 1):
        report_id = f"RPT-{index:03d}"
        raw = (text + "\n").encode("utf-8")
        (directory / "reports" / (report_id + ".txt")).write_bytes(raw)
        cases.append(DraftCase(report_id=report_id, report_file=f"reports/{report_id}.txt", report_sha256=hashlib.sha256(raw).hexdigest(),
                               subtype=subtype, scenario_id=scenario, root_cause_group=GROUPS[subtype], report_variant_group=variant))
    manifest = DraftManifest(dataset_version="r3-candidates-v1", cases=cases)
    write_new(directory / "manifest.draft.json", manifest.model_dump())
    write_new(directory / "schedule.not-started.json", schedule(manifest).model_dump())
    write_new(directory / "readiness.initial.json", readiness(manifest))
    with (directory / "gt-review.csv").open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for c in manifest.cases:
            writer.writerow({"report_id": c.report_id, "report_sha256": c.report_sha256, "decision": "PENDING"})
    (directory / "README.md").write_text(
        "# Kandidat R3 — belum diterima/freeze\n\n"
        "20 variasi teks, bukan 20 skenario/bug independen. BAC 8, XSS 8, upload 4; semua GT kosong.\n"
        "Baca docs/r3-capability-map.md dan docs/r3-verification.md pada repo sebelum review.\n\n"
        "Isi gt-review.csv: decision ACCEPT dengan gt VALID/INVALID hanya setelah verifikasi manusia atas klaim dan bukti kasus.\n"
        "Cantumkan reviewer, rationale, target_snapshot, condition_reference, scope_version, rules_version dan evidence_reference.\n"
        "Gunakan EXCLUDE serta reviewer/rationale untuk kandidat yang tidak layak; gunakan PENDING bila belum cukup bukti.\n"
        "Jangan memberi INVALID pada OOS/unsupported/ambigu atau memakai kondisi fixed saja sebagai alasan.\n"
        "CSV dan manifest privat tidak menjadi prompt model. Jangan menilai kualitas/kelayakan hanya dari jumlah teks.\n"
        "Case binding app/run/revision dan observasi B belum disiapkan; schedule hanya NOT_STARTED.\n"
        "Import menghasilkan file baru; tidak mengubah manifest draf atau GT lama.\n", encoding="utf-8")
    return manifest


def import_review(packet: Path, review: Path) -> DraftManifest:
    manifest = read_manifest(packet)
    with review.open(encoding="utf-8-sig", newline="") as stream:
        # Bound input before CSV parsing; no formula evaluation or spreadsheet execution.
        content = stream.read(1_048_577)
    if len(content) > 1_048_576:
        raise EvaluationError("REVIEW_LIMIT")
    import io
    reader = csv.DictReader(io.StringIO(content))
    if reader.fieldnames != CSV_FIELDS:
        raise EvaluationError("REVIEW_COLUMNS")
    rows = list(reader)
    lookup = {row.get("report_id"): row for row in rows}
    if len(lookup) != len(rows) or set(lookup) != {c.report_id for c in manifest.cases}:
        raise EvaluationError("REVIEW_CASES")
    result = []
    for case in manifest.cases:
        row = lookup[case.report_id]
        if None in row or any(value is None for value in row.values()) or row["report_sha256"] != case.report_sha256:
            raise EvaluationError("REVIEW_BINDING")
        decision = row["decision"].strip()
        update = {"accepted_by_human": False, "exclusion_reason": None, "ground_truth": None}
        if decision == "ACCEPT":
            gt = GroundTruth.model_validate({k: row[k].strip() for k in GroundTruth.model_fields if k != "label"} | {"label": row["gt"].strip()})
            update = {"accepted_by_human": True, "exclusion_reason": None, "ground_truth": gt.model_dump()}
        elif decision == "EXCLUDE":
            if row["gt"].strip() or not row["reviewer"].strip() or not row["rationale"].strip():
                raise EvaluationError("EXCLUSION_REQUIRES_REASON_NOT_GT")
            update["exclusion_reason"] = row["reviewer"].strip() + ": " + row["rationale"].strip()
        elif decision != "PENDING" or row["gt"].strip():
            raise EvaluationError("REVIEW_DECISION")
        result.append(DraftCase.model_validate(case.model_dump() | update))
    return DraftManifest(dataset_version=manifest.dataset_version, cases=result)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["prepare", "import-review"])
    parser.add_argument("packet", type=Path)
    parser.add_argument("--review", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.operation == "prepare":
            manifest = prepare(args.packet)
        else:
            if not args.review or not args.output:
                raise EvaluationError("REVIEW_AND_NEW_OUTPUT_REQUIRED")
            if not args.output.resolve().is_relative_to(args.packet.resolve()):
                raise EvaluationError("OUTPUT_MUST_STAY_IN_PACKET")
            manifest = import_review(args.packet, args.review)
            write_new(args.output, manifest.model_dump())
        print(json.dumps(readiness(manifest), ensure_ascii=False, indent=2))
        return 0
    except (ValueError, TypeError, OSError, csv.Error):
        print(json.dumps({"status": "ERROR", "error_code": "DRAFT_PREPARATION_OR_REVIEW_INVALID"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
