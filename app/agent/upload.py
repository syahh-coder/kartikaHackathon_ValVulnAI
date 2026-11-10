"""Development upload filename validator; no lab source, condition or report script."""
import hashlib
import json
import re
from uuid import UUID, uuid4

from app.common import AppError
from app.schemas import Claim
from app.storage.db import all_rows, one
from app.agent.xss import verify_pair
from boundary.browser import BrowserCapture
from boundary.contracts import ActionEnvelope, BrowserArguments, UploadArguments, canonical, observation_from
from boundary.uploads import UploadedFile, filename


def prerequisites(claim: Claim) -> str:
    match = re.fullmatch(r"/requests/([a-f0-9-]{36})/attachments", claim.path or "")
    if claim.category != "UPLOAD" or claim.method != "GET" or not match:
        raise AppError(422, "UNSUPPORTED", "Upload development hanya mendukung label lampiran permintaan dengan fixture tetap.")
    try:
        rid = str(UUID(match[1]))
    except ValueError:
        raise AppError(422, "NEEDS_INFO", "ID permintaan lab diperlukan.")
    if claim.claim_count != 1 or claim.account_aliases != ["requester-a", "requester-b"]:
        raise AppError(422, "NEEDS_INFO", "Satu klaim, pengunggah A dan pembaca B yang ditugaskan diperlukan.")
    if claim.control_path not in {None, f"/requests/{rid}/attachment-labels"}:
        raise AppError(422, "UNSUPPORTED", "Kontrol label lampiran memakai rute terdaftar.")
    return rid


def steps(rid: str, inert: UUID, marker: UUID) -> list[UploadArguments | BrowserArguments]:
    upload_path, view = f"/api/requests/{rid}/attachments", f"/requests/{rid}/attachments"
    result = []
    for fixture, nonce in (("inert-v1", inert), ("marker-v1", marker)):
        result.extend([UploadArguments(relative_path=upload_path, fixture=fixture, nonce=nonce),
            BrowserArguments(operation="upload_list_probe", relative_path=view, account_alias="requester-b", fixture=fixture, nonce=nonce)])
    result.append(BrowserArguments(operation="upload_list_probe", relative_path=f"/requests/{rid}/attachment-labels",
        account_alias="requester-b", fixture="marker-v1", nonce=marker))
    return result


def plan(claim: Claim) -> list[UploadArguments | BrowserArguments]:
    return steps(prerequisites(claim), uuid4(), uuid4())


async def verify(conn, run_id: str) -> dict:
    result = {"verdict": "INCONCLUSIVE", "reasoning": "Bukti upload, pembaca dan kontrol browser belum lengkap.",
        "supporting_evidence_ids": [], "contradicting_evidence_ids": [], "controls_performed": [], "missing_prerequisites": [],
        "limitations": ["Planner mock; bukan hasil model live.", "Terbatas pada metadata nama fixture, permintaan dan dua akun ini; isi upload, SVG/HTML, penimpaan dan payload lain tidak diuji."],
        "next_action": "Admin meninjau bukti dan operator mereset lab sebelum run berikutnya."}
    run = await one(conn, "SELECT * FROM runs WHERE run_id=?", (run_id,))
    if not run or run["tool_execution_mode"] != "LAB":
        return result
    try:
        revision = await one(conn, "SELECT claim_json FROM report_revisions WHERE revision_id=?", (run["report_revision_id"],))
        rid = prerequisites(Claim.model_validate_json(revision[0]))
        rows = await all_rows(conn, "SELECT h.*,e.evidence_id,e.kind,e.sha256,e.provenance_json,e.actor_alias,a.arguments_json,a.tool_name "
            "FROM handoff_actions h JOIN actions a USING(action_id,run_id) JOIN evidence e USING(action_id,run_id) WHERE h.run_id=? ORDER BY h.action_seq", (run_id,))
        if len(rows) != 5:
            return result
        envelopes = [ActionEnvelope.model_validate_json(r["envelope_json"]) for r in rows]
        expected = steps(rid, envelopes[0].validated_arguments.nonce, envelopes[2].validated_arguments.nonce)
        if expected[0].nonce == expected[2].nonce:
            return result
        observations = []
        upload_ids = []
        for index, (row, envelope, args) in enumerate(zip(rows, envelopes, expected), 1):
            envelope.authorize(now=envelope.issued_at)
            obs = observation_from(json.loads(row["observation_json"]))
            browser = isinstance(args, BrowserArguments)
            tool = "browser_probe" if browser else "upload_fixture"
            provenance = json.loads(row["provenance_json"])
            if (envelope.validated_arguments != args or envelope.tool_name != tool or row["tool_name"] != tool or
                    row["status"] != "RECEIVED" or row["kind"] != ("BROWSER_PROBE" if browser else "UPLOAD_EXCHANGE") or
                    envelope.action_seq != index or row["action_seq"] != index or str(envelope.run_id) != run_id or str(envelope.action_id) != row["action_id"] or
                    str(envelope.target_snapshot_id) != run["target_snapshot_id"] or str(envelope.scope_version_id) != run["scope_version_id"] or
                    str(envelope.program_id) != run["program_id"] or envelope.target_id != run["target_id"] or envelope.authorization_epoch != run["authorization_epoch"] or
                    hashlib.sha256(canonical(envelope.model_dump(mode="json"))).hexdigest() != row["envelope_hash"] or json.loads(row["arguments_json"]) != args.model_dump(mode="json") or
                    obs.model_dump().get("tool_name") != tool or obs.status != "OK" or obs.error_code or obs.truncated or obs.http_status != 200 or
                    obs.request_attempts != 2 or obs.responses_received != 2 or obs.action_seq != index or str(obs.run_id) != run_id or str(obs.action_id) != row["action_id"] or
                    obs.envelope_hash != row["envelope_hash"] or str(obs.target_snapshot_id) != run["target_snapshot_id"] or str(obs.boot_id) != run["worker_boot_id"] or
                    not envelope.issued_at-1 <= obs.captured_at <= envelope.expires_at+1 or
                    (obs.method, obs.relative_path, obs.actor_alias) != (args.method, args.relative_path, args.account_alias) or row["actor_alias"] != args.account_alias or
                    provenance != {"source": "worker_browser" if browser else "worker_upload", "mode": "lab_tools", "run_id": run_id, "action_id": row["action_id"],
                        "evidence_id": row["evidence_id"], "worker_boot_id": run["worker_boot_id"], "envelope_hash": row["envelope_hash"], "snapshot_id": run["target_snapshot_id"]} or
                    row["sha256"] != hashlib.sha256(canonical(obs.model_dump(mode="json"))).hexdigest()):
                return result
            if browser:
                cap = BrowserCapture.model_validate_json(obs.body)
                if cap.nonce != args.nonce or cap.fixture != args.fixture or cap.path != args.relative_path:
                    return result
            else:
                value = UploadedFile.model_validate_json(obs.body)
                if str(value.request_id) != rid or value.filename != filename(args.fixture, args.nonce):
                    return result
                upload_ids.append(value.upload_id)
            observations.append(obs.model_dump(mode="json"))
        if len(set(upload_ids)) != 2:
            return result
        safe = BrowserCapture.model_validate_json(observations[4]["body"])
        if (not safe.js_control or not safe.initial_storage_empty or not safe.payload_visible_as_text or
                safe.marker_events or not safe.screenshot_base64):
            return result
        verdict = verify_pair(observations[1], observations[3])
        if verdict not in {"CONFIRMED", "REFUTED"}:
            return result
        result.update(verdict=verdict, reasoning=("Nama fixture yang diunggah A mengeksekusi marker pada daftar lampiran ketika dibaca B; jalur label aman tetap inert."
            if verdict == "CONFIRMED" else "Nama fixture tampil sebagai teks tanpa marker pada daftar lampiran dan jalur label aman, dengan kontrol browser lengkap."),
            controls_performed=["Dua upload fixture teks tetap dengan ID berbeda oleh A, dibaca B yang ditugaskan pada permintaan tersebut.",
                "Context/storage baru, JavaScript aktif, kontrol nama inert dan jalur label aman menampilkan teks tanpa callback.",
                "Marker terikat nonce, frame utama dan origin/rute aktual; bukan sekadar upload berhasil."])
        result["supporting_evidence_ids" if verdict == "CONFIRMED" else "contradicting_evidence_ids"] = [r["evidence_id"] for r in rows]
    except (AppError, ValueError, KeyError, TypeError, AttributeError):
        pass
    return result
