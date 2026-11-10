"""Bounded development planner and verifier. No evaluator labels or lab database access."""
import hashlib
import json

from app.common import AppError
from app.schemas import Claim
from app.policy.targets import canonical_path
from app.storage.db import all_rows, one
from boundary.contracts import HttpArguments, Observation, canonical


def plan(claim: Claim) -> list[HttpArguments]:
    if claim.category != "BAC" or claim.method != "DELETE":
        raise AppError(422, "UNSUPPORTED", "M3 hanya mendukung klaim penghapusan lampiran lintas akun.")
    if not claim.control_path:
        raise AppError(422, "NEEDS_INFO", "Path lampiran kontrol milik akun penguji diperlukan.")
    if (claim.claim_count != 1 or len(claim.account_aliases) != 2 or
            set(claim.account_aliases) != {"requester-a", "requester-b"} or
            claim.control_path == claim.path):
        raise AppError(422, "NEEDS_INFO", "Satu klaim, dua akun berbeda dan dua objek berbeda diperlukan.")
    for path in (claim.path, claim.control_path):
        if not path or not canonical_path(path).startswith("/api/attachments/") or len(path.split("/")) != 4:
            raise AppError(422, "UNSUPPORTED", "Gunakan endpoint lampiran lab terdaftar.")
    attacker, owner = claim.account_aliases
    steps = [("GET", claim.path, owner), ("GET", claim.path, attacker),
             ("GET", claim.control_path, attacker), ("DELETE", claim.control_path, attacker),
             ("GET", claim.control_path, attacker), ("DELETE", claim.path, attacker),
             ("GET", claim.path, owner)]
    return [HttpArguments(method=m, relative_path=p, account_alias=a) for m, p, a in steps]


async def verify(conn, run_id: str) -> dict:
    run = await one(conn, "SELECT * FROM runs WHERE run_id=?", (run_id,))
    result = {"verdict": "INCONCLUSIVE", "reasoning": "Bukti dampak dan kontrol belum lengkap.",
              "supporting_evidence_ids": [], "contradicting_evidence_ids": [], "controls_performed": [],
              "missing_prerequisites": [], "limitations": ["Planner mock; bukan hasil model live.",
                  "Hanya klaim utama penghapusan lampiran pada snapshot ini; bukan verdict seluruh kerentanan."],
              "next_action": "Admin meninjau bukti; operator mereset target sebelum run berikutnya."}
    if not run or run["tool_execution_mode"] != "LAB":
        return result
    revision = await one(conn, "SELECT claim_json FROM report_revisions WHERE revision_id=?", (run["report_revision_id"],))
    claim = Claim.model_validate_json(revision[0])
    try:
        expected = plan(claim)
    except AppError:
        return result
    rows = await all_rows(conn, "SELECT h.*,e.evidence_id,e.sha256,e.provenance_json,e.actor_alias,a.arguments_json "
                          "FROM handoff_actions h JOIN actions a USING(action_id,run_id) "
                          "JOIN evidence e USING(action_id,run_id) WHERE h.run_id=? ORDER BY h.action_seq", (run_id,))
    if len(rows) != len(expected):
        return result
    observations = []
    for index, (row, args) in enumerate(zip(rows, expected), 1):
        if row["status"] != "RECEIVED":
            return result
        obs = Observation.model_validate_json(row["observation_json"])
        provenance = json.loads(row["provenance_json"])
        if (obs.status != "OK" or obs.truncated or obs.error_code or obs.request_attempts != 2 or obs.responses_received != 2 or
                row["action_seq"] != index or obs.action_seq != index or
                str(obs.run_id) != run_id or str(obs.action_id) != row["action_id"] or
                obs.envelope_hash != row["envelope_hash"] or str(obs.target_snapshot_id) != run["target_snapshot_id"] or
                str(obs.boot_id) != run["worker_boot_id"] or row["actor_alias"] != args.account_alias or
                (obs.method, obs.relative_path, obs.actor_alias) != (args.method, args.relative_path, args.account_alias) or
                json.loads(row["arguments_json"]) != args.model_dump() or provenance.get("source") != "worker_http" or
                row["sha256"] != hashlib.sha256(canonical(obs.model_dump(mode="json"))).hexdigest()):
            return result
        observations.append(obs)
    def object_matches(index, path, owner):
        try:
            body = json.loads(observations[index].body)
            return body["attachment_id"] == path.rsplit("/", 1)[1] and body["owner_alias"] == owner
        except (ValueError, KeyError, TypeError):
            return False
    def deleted_matches(index, path):
        try:
            body = json.loads(observations[index].body)
            return body["attachment_id"] == path.rsplit("/", 1)[1] and body["deleted"] is True
        except (ValueError, KeyError, TypeError):
            return False
    attacker, owner = claim.account_aliases
    statuses = [o.http_status for o in observations]
    prerequisites = (statuses[:5] == [200, 404, 200, 200, 404] and
                     object_matches(0, claim.path, owner) and object_matches(2, claim.control_path, attacker) and
                     deleted_matches(3, claim.control_path))
    if not prerequisites:
        result["missing_prerequisites"] = ["Kepemilikan awal, isolasi baca atau kontrol penghapusan normal tidak terbukti."]
        return result
    result["controls_performed"] = ["Pemilik membaca objek korban sebelum aksi", "Akun penguji tidak dapat membaca objek korban",
                                     "Penghapusan objek sendiri berhasil dan akses sesudahnya hilang"]
    ids = [r["evidence_id"] for r in rows]
    if statuses[5:] == [200, 404] and deleted_matches(5, claim.path):
        result.update(verdict="CONFIRMED", reasoning="Akun lain berhasil menghapus lampiran; pemilik kehilangan akses setelah aksi. Kontrol normal berhasil.",
                      supporting_evidence_ids=ids)
    elif statuses[5:] in ([403, 200], [404, 200]) and object_matches(6, claim.path, owner):
        result.update(verdict="REFUTED", reasoning="Aksi lintas akun ditolak dan objek tetap dapat dibaca pemilik; kontrol penghapusan sendiri berhasil.",
                      contradicting_evidence_ids=ids)
    return result
