"""Prepare private review aids without setting GT or claiming evidence/model execution."""
import argparse
import os
from pathlib import Path

from evaluator.functional_v2 import read_manifest, schedule, write_new


def prepare(packet: Path, output: Path):
    manifest = read_manifest(packet)
    output.mkdir(parents=True, exist_ok=False)
    proposals = []
    needs = {
        "BAC-08": "Kepemilikan dua objek, dua akun, kontrol operasi normal, respons lintas akun dan akses pemilik sesudahnya.",
        "XSS-08": "Kontrol inert/JavaScript/storage baru dan marker terikat origin/rute/frame pada kedua akun.",
        "UP-04": "Dua metadata upload terikat permintaan/pembaca, kontrol nama inert, marker dan label aman; bukan isi file."
    }
    for case in manifest.cases:
        proposals.append({"report_id": case.report_id, "report_sha256": case.report_sha256, "status": "PROPOSED_NOT_GT",
                          "proposed_label": None, "accepted_by_human": False, "subtype": case.subtype,
                          "review_question": "Apakah teks memuat satu klaim yang sesuai, cukup jelas dan layak dibanding varian lain?",
                          "required_evidence": needs[case.subtype],
                          "available_reference": "docs/r3-capability-map.md (peta source/historis; bukan bukti kasus ini)",
                          "case_bound_evidence": None, "reason": "Belum ada run/revision/snapshot yang terikat persis pada teks kandidat; label tidak diusulkan tanpa bukti."})
    write_new(output/"proposals.private.json", {"status": "PROPOSED_NOT_GT", "cases": proposals})
    write_new(output/"bindings.template.private.json", {case.report_id: None for case in manifest.cases})
    write_new(output/"outcomes.pending.json", schedule(manifest).model_dump())
    write_new(output/"report.pending.json", {"protocol": "functional-v2", "status": "NOT_STARTED", "scheduled_per_arm": 20,
              "human_gt": 0, "case_bound_contexts": 0, "live_verified": False, "frozen": False, "evaluated": False,
              "arms": {a: {"started": 0, "successful_responses": 0, "precision": None, "recall_end_to_end": None,
                           "strict_accuracy": None, "coverage": None, "f1": None, "cost_idr": None,
                           "input_tokens": None, "output_tokens": None, "elapsed_seconds": None} for a in ("A", "B")},
              "required_inputs": ["Human report acceptance and GT worksheet", "Exact report-to-run bindings and relevant stored observations",
                                  "Verified live access/profile/prices/token bound and authoritative ledger", "Successful development smoke and private freeze"]})
    lines = ["# Review kandidat privat", "", "**PROPOSED_NOT_GT. Semua label tetap kosong.** Tidak ada prediksi model atau bukti kasus yang dibuat.", "",
             "Tinjau teks dan kesesuaian klaim, lalu bukti snapshot terkait sebelum mengisi CSV manusia. EXCLUDE bukan INVALID.", "",
             "| ID | Subtype | Teks | Bukti yang harus ditinjau |", "| --- | --- | --- | --- |"]
    for case in manifest.cases:
        reference = os.path.relpath(packet/case.report_file, output).replace("\\", "/")
        lines.append(f"| {case.report_id} | {case.subtype} | [Buka teks]({reference}) | {needs[case.subtype]} |")
    (output/"review-guide.md").write_text("\n".join(lines)+"\n", encoding="utf-8")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--packet", type=Path, default=Path("artifacts/r3/candidates-v1"))
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    prepare(args.packet, args.output)
