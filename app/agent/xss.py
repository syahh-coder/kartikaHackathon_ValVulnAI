"""Narrow notification preview validator. No evaluator state or report-supplied script."""
import hashlib
import json
from uuid import uuid4

from pydantic import ValidationError

from app.common import AppError
from app.schemas import Claim
from app.storage.db import all_rows, one
from boundary.browser import BrowserCapture
from boundary.contracts import ActionEnvelope, BrowserArguments, BrowserObservation, canonical


def prerequisites(claim: Claim):
    if claim.category != "XSS" or claim.method != "GET" or claim.path != "/notifications/preview":
        raise AppError(422, "UNSUPPORTED", "XSS lab hanya mendukung pratinjau notifikasi dengan fixture tetap.")
    if claim.claim_count != 1 or set(claim.account_aliases) != {"requester-a", "requester-b"} or len(claim.account_aliases) != 2:
        raise AppError(422, "NEEDS_INFO", "Satu klaim dan dua akun uji berbeda diperlukan.")
    if claim.control_path:
        raise AppError(422, "UNSUPPORTED", "Kontrol XSS memakai rute yang sama; path kontrol tambahan tidak didukung.")


def plan(claim: Claim) -> list[BrowserArguments]:
    prerequisites(claim)
    return [BrowserArguments(account_alias=alias, fixture=fixture, nonce=uuid4())
            for alias in claim.account_aliases for fixture in ("inert-v1", "marker-v1")]


async def verify(conn, run_id: str) -> dict:
    result = {"verdict": "INCONCLUSIVE", "reasoning": "Kontrol browser dan bukti eksekusi belum lengkap.",
              "supporting_evidence_ids": [], "contradicting_evidence_ids": [], "controls_performed": [],
              "missing_prerequisites": [], "limitations": ["Planner mock; bukan hasil model live.",
                  "Hanya fixture tetap pada pratinjau notifikasi di dua akun/snapshot ini; payload, persistensi, eksfiltrasi dan klaim lain tidak diuji."],
              "next_action": "Admin meninjau bukti; operator mereset target sebelum run berikutnya."}
    run = await one(conn, "SELECT * FROM runs WHERE run_id=?", (run_id,))
    if not run or run["tool_execution_mode"] != "LAB":
        return result
    revision = await one(conn, "SELECT claim_json FROM report_revisions WHERE revision_id=?", (run["report_revision_id"],))
    try:
        claim = Claim.model_validate_json(revision[0])
        prerequisites(claim)
        rows = await all_rows(conn, "SELECT h.*,e.evidence_id,e.kind,e.sha256,e.provenance_json,e.actor_alias,a.arguments_json,a.tool_name "
                              "FROM handoff_actions h JOIN actions a USING(action_id,run_id) "
                              "JOIN evidence e USING(action_id,run_id) WHERE h.run_id=? ORDER BY h.action_seq", (run_id,))
        if len(rows) != 4:
            return result
        observations, nonces = [], set()
        for index, row in enumerate(rows, 1):
            envelope = ActionEnvelope.model_validate_json(row["envelope_json"])
            envelope.authorize(now=envelope.issued_at)
            args = envelope.validated_arguments
            obs = BrowserObservation.model_validate_json(row["observation_json"])
            cap = BrowserCapture.model_validate_json(obs.body)
            provenance = json.loads(row["provenance_json"])
            expected_alias = claim.account_aliases[(index-1)//2]
            expected_fixture = "inert-v1" if index % 2 else "marker-v1"
            if (row["status"] != "RECEIVED" or row["kind"] != "BROWSER_PROBE" or row["tool_name"] != "browser_probe" or
                    not isinstance(args, BrowserArguments) or args.operation != "notification_probe" or args.relative_path != claim.path or
                    args.account_alias != expected_alias or args.fixture != expected_fixture or
                    str(args.nonce) in nonces or cap.nonce != args.nonce or cap.fixture != args.fixture or
                    envelope.tool_name != "browser_probe" or str(envelope.run_id) != run_id or str(envelope.action_id) != row["action_id"] or
                    envelope.action_seq != index or str(envelope.target_snapshot_id) != run["target_snapshot_id"] or
                    str(envelope.scope_version_id) != run["scope_version_id"] or envelope.authorization_epoch != run["authorization_epoch"] or
                    str(envelope.program_id) != run["program_id"] or envelope.target_id != run["target_id"] or
                    hashlib.sha256(canonical(envelope.model_dump(mode="json"))).hexdigest() != row["envelope_hash"] or
                    json.loads(row["arguments_json"]) != args.model_dump(mode="json") or
                    obs.status != "OK" or obs.truncated or obs.error_code or obs.request_attempts != 2 or obs.responses_received != 2 or
                    row["action_seq"] != index or obs.action_seq != index or str(obs.run_id) != run_id or
                    str(obs.action_id) != row["action_id"] or obs.envelope_hash != row["envelope_hash"] or
                    not envelope.issued_at-1 <= obs.captured_at <= envelope.expires_at+1 or
                    str(obs.target_snapshot_id) != run["target_snapshot_id"] or str(obs.boot_id) != run["worker_boot_id"] or
                    (obs.method, obs.relative_path, obs.actor_alias) != (args.method, args.relative_path, args.account_alias) or
                    row["actor_alias"] != expected_alias or provenance.get("source") != "worker_browser" or
                    provenance.get("run_id") != run_id or provenance.get("action_id") != row["action_id"] or
                    provenance.get("evidence_id") != row["evidence_id"] or
                    provenance.get("worker_boot_id") != run["worker_boot_id"] or provenance.get("snapshot_id") != run["target_snapshot_id"] or
                    provenance.get("envelope_hash") != row["envelope_hash"] or
                    row["sha256"] != hashlib.sha256(canonical(obs.model_dump(mode="json"))).hexdigest()):
                return result
            nonces.add(str(args.nonce))
            observations.append(obs.model_dump(mode="json"))
        verdicts = [verify_pair(*observations[i:i+2]) for i in (0, 2)]
        if verdicts not in (["CONFIRMED"]*2, ["REFUTED"]*2):
            result["missing_prerequisites"] = ["Kedua akun harus memiliki kontrol lengkap dan hasil yang konsisten."]
            return result
        verdict = verdicts[0]
        result.update(verdict=verdict, controls_performed=["Dua akun terautentikasi, setiap aksi memakai konteks browser baru dan penyimpanan awal kosong.",
            "Kontrol JavaScript aktif dan teks inert tampil tanpa callback.", "Marker terikat nonce, origin, rute dan frame utama dari envelope aplikasi."],
            reasoning=("Marker fixture dieksekusi pada frame utama pratinjau di kedua akun; kontrol inert tidak mengeksekusi marker."
                       if verdict == "CONFIRMED" else "Fixture marker tampil sebagai teks tanpa eksekusi di kedua akun; kontrol JavaScript dan inert berhasil."))
        result["supporting_evidence_ids" if verdict == "CONFIRMED" else "contradicting_evidence_ids"] = [r["evidence_id"] for r in rows]
    except (AppError, ValueError, TypeError, KeyError):
        return result
    return result


def verify_pair(control: dict, probe: dict) -> str:
    try:
        a, b = BrowserObservation.model_validate(control), BrowserObservation.model_validate(probe)
        ca, cb = BrowserCapture.model_validate_json(a.body), BrowserCapture.model_validate_json(b.body)
        if (a.status != "OK" or b.status != "OK" or a.http_status != 200 or b.http_status != 200 or
                a.truncated or b.truncated or a.error_code or b.error_code or
                (a.run_id, a.target_snapshot_id, a.boot_id, a.actor_alias) !=
                (b.run_id, b.target_snapshot_id, b.boot_id, b.actor_alias) or
                a.action_id == b.action_id or a.action_seq >= b.action_seq or ca.nonce == cb.nonce or
                a.relative_path != ca.path or b.relative_path != cb.path or a.method != "GET" or b.method != "GET" or
                ca.fixture != "inert-v1" or cb.fixture != "marker-v1" or
                not ca.js_control or not cb.js_control or not ca.initial_storage_empty or not cb.initial_storage_empty or not ca.payload_visible_as_text or ca.marker_events or
                not ca.screenshot_base64 or not cb.screenshot_base64):
            return "INCONCLUSIVE"
        if len(cb.marker_events) == 1:
            return "CONFIRMED"
        if cb.payload_visible_as_text:
            return "REFUTED"
    except (ValueError, ValidationError):
        pass
    return "INCONCLUSIVE"
