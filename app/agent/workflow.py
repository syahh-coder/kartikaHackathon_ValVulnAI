import asyncio
import json
import logging
import time

from app.agent.ledger import reserve
from app.agent.state import TERMINAL, validate_transition
from app.agent import simulation_context
from app.agent.verifier import AssessmentProposal, validate_assessment
from app.api.routes import bindings_for
from app.common import AppError, audit, digest, packed, rate_limit, uid
from app.config import Settings
from app.policy.targets import gate, check_action
from app.providers.contracts import ProviderFailure
from app.providers.engine import ProviderSession
from app.providers.mock import MOCK_PROFILE, MockTransport
from app.schemas import Claim, RunInput
from app.storage.db import Database, all_rows, one
from app.storage.quota import check_storage
from app.storage.files import write_private

LIMITS = {"model_calls": 12, "target_requests": 40, "browser_actions": 30, "active_seconds": 180,
          "queue_seconds": 300, "input_tokens": 8192, "output_tokens": 1024,
          "body_bytes": 131072, "response_bytes": 1048576, "screenshot_bytes": 2097152,
          "artifact_bytes": 16777216}
logger = logging.getLogger(__name__)


class Workflow:
    def __init__(self, db: Database, config: Settings):
        self.db, self.config = db, config
        self.tick_lock = asyncio.Lock()
        self.stop_event = asyncio.Event()
        self.wake = asyncio.Event()

    async def create_run(self, conn, user, report, request: RunInput, key: str, *, operator: bool = False) -> str:
        now = time.time()
        payload_hash = digest(packed({"report_id": report["report_id"], **request.model_dump()}))
        previous = await one(conn, "SELECT * FROM idempotency WHERE principal_id=? AND program_id=? AND operation='START_RUN' AND key=?",
                             (user.user_id, report["program_id"], key))
        if previous:
            if previous["payload_hash"] != payload_hash:
                raise AppError(409, "IDEMPOTENCY_CONFLICT", "Kunci sudah digunakan untuk payload berbeda.")
            return previous["run_id"]
        revision = await one(conn, "SELECT * FROM report_revisions WHERE revision_id=? AND report_id=?",
                             (request.report_revision_id, report["report_id"]))
        if not revision:
            raise AppError(404, "NOT_FOUND", "Revisi tidak ditemukan.")
        program = await one(conn, "SELECT * FROM programs WHERE program_id=?", (report["program_id"],))
        scope = await one(conn, "SELECT rules_json FROM scope_versions WHERE scope_version_id=? AND state='ACTIVE'",
                          (program["active_scope_version_id"],))
        scope_rules = json.loads(scope[0]) if scope else None
        scope_decision, capability, process, target_id = gate(
            Claim.model_validate_json(revision["claim_json"]), scope_rules, await bindings_for(conn, report["program_id"]))
        if request.execution_mode != "mock" or self.config.execution_mode != "mock":
            process = "CONFIGURATION_REQUIRED"
        heartbeat = None
        if request.tool_execution_mode == "LAB" and process == "SCOPE_CHECKED":
            from app.agent.lab_validation import validator_for
            claim = Claim.model_validate_json(revision["claim_json"])
            try:
                steps = validator_for(claim).plan(claim)
                binding = (await bindings_for(conn, report["program_id"]))[claim.asset_alias]
                for args in steps:
                    check_action(claim, scope_rules, binding, method=args.method, path=args.relative_path, account_alias=args.account_alias)
            except AppError as exc:
                process = exc.code if exc.code in {"UNSUPPORTED", "NEEDS_INFO"} else "POLICY_BLOCKED"
            if process == "SCOPE_CHECKED":
                if not self.config.transport_key_file:
                    raise AppError(503, "DEPENDENCY_NOT_READY", "Worker lab belum dikonfigurasi.")
                from app.transport import Handoff
                try:
                    heartbeat = await asyncio.to_thread(Handoff(self.db, self.config).heartbeat)
                except (OSError, ValueError, KeyError) as exc:
                    raise AppError(503, "WORKER_NOT_READY", "Worker lab belum siap.") from exc
                if binding["dirty"] or binding["maintenance"] or heartbeat["dirty"]:
                    raise AppError(409, "TARGET_DIRTY", "Operator perlu reset/health target sebelum validasi.")
                if not binding["ready"] or binding["snapshot_id"] != heartbeat["snapshot_id"]:
                    raise AppError(503, "DEPENDENCY_NOT_READY", "Snapshot lab belum diverifikasi operator.")
        queued = process == "SCOPE_CHECKED"
        if queued:
            if await one(conn, "SELECT 1 FROM runs WHERE owner_user_id=? AND queue_status IN ('QUEUED','LEASED')", (report["owner_user_id"],)):
                raise AppError(409, "RUN_ACTIVE", "Satu run per pemilik masih menunggu/aktif.")
            count = (await one(conn, "SELECT count(*) FROM runs WHERE queue_status='QUEUED'"))[0]
            if count >= self.config.queue_limit:
                raise AppError(429, "QUEUE_LIMIT", "Antrean penuh. Coba lagi nanti.", True)
            await asyncio.to_thread(check_storage, self.config)
        if not operator:
            await rate_limit(conn, "start:"+user.user_id, 3, 3600)
        run_id, claim_id = uid(), uid()
        await conn.execute("INSERT INTO runs(run_id,program_id,report_id,report_revision_id,owner_user_id,requested_by,"
                           "scope_version_id,authorization_epoch,target_id,primary_claim_id,execution_mode,process_status,"
                           "queue_status,scope_decision,capability_decision,limits_json,created_at,queue_expires_at,finished_at,error_code,counters_json) "
                           "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                           (run_id, report["program_id"], report["report_id"], revision["revision_id"], report["owner_user_id"], user.user_id,
                            program["active_scope_version_id"], program["authorization_epoch"], target_id, claim_id, request.execution_mode,
                            process, "QUEUED" if queued else "NOT_ENQUEUED", scope_decision, capability, packed(LIMITS), now,
                            now+300 if queued else None, None if queued else now, None if queued else process,
                            packed({"model_calls": 0, "target_requests": 0, "denied_attempts": 0, "browser_actions": 0})))
        await conn.execute("INSERT INTO idempotency VALUES (?,?,'START_RUN',?,?,?)",
                           (user.user_id, report["program_id"], key, payload_hash, run_id))
        await conn.execute("UPDATE runs SET tool_execution_mode=?,target_snapshot_id=?,worker_boot_id=?,prompt_version=? WHERE run_id=?",
                           (request.tool_execution_mode, heartbeat["snapshot_id"] if heartbeat else None,
                            heartbeat["boot_id"] if heartbeat else None,
                            {"XSS":"m4-xss-mock-v1", "UPLOAD":"m5-upload-mock-v1"}.get(Claim.model_validate_json(revision["claim_json"]).category,"m3-bac-mock-v1") if request.tool_execution_mode=="LAB" else simulation_context.PROMPT_VERSION, run_id))
        if queued:
            await reserve(conn, run_id, 0, self.config.budget_idr)
        await audit(conn, user.user_id, "RUN_CREATED", {"mode": request.execution_mode, "scope_decision": scope_decision,
                                                       "capability_decision": capability, "process_status": process}, run_id)
        self.wake.set()
        return run_id

    async def recover(self):
        # Never run inference or replay work during startup. A new explicit request is needed.
        async with self.db.transaction() as conn:
            interrupted = await all_rows(conn, "SELECT * FROM runs WHERE queue_status IN ('QUEUED','LEASED')")
            for run in interrupted:
                if run["queue_status"] == "LEASED" and (run["execution_mode"] != "mock" or run["tool_execution_mode"] == "LAB"):
                    await conn.execute("UPDATE target_bindings SET dirty=1 WHERE target_id=?", (run["target_id"],))
                await self._stop(conn, run["run_id"], "FAILED", "PROCESS_INTERRUPTED")
            # A dispatched attempt may have been charged; keep its full reservation.
            await conn.execute("UPDATE ledger SET status='COST_UNKNOWN' WHERE run_id IS NOT NULL AND status='RESERVED' AND provider_attempt_id IS NOT NULL")
            await conn.execute("UPDATE provider_attempts SET status='FAILED',error_code='PROCESS_INTERRUPTED' WHERE run_id IS NOT NULL AND status='DISPATCHED'")

    async def _stop(self, conn, run_id: str, process: str, code: str):
        run = await one(conn, "SELECT * FROM runs WHERE run_id=?", (run_id,))
        if not run or run["process_status"] in TERMINAL:
            return
        if run["tool_execution_mode"] == "LAB" and run["queue_status"] == "LEASED":
            if self.config.transport_key_file:
                from app.transport import Handoff
                try:
                    await asyncio.to_thread(Handoff(self.db, self.config).control, "CANCEL", run_id=run_id)
                except (OSError, ValueError):
                    pass  # Local expiry still stops I/O; dirty gate remains closed.
            await conn.execute("UPDATE target_bindings SET dirty=1,dirty_run_id=NULL WHERE target_id=?", (run["target_id"],))
            await conn.execute("UPDATE handoff_actions SET status='UNKNOWN' WHERE run_id=? AND status='ISSUED'", (run_id,))
        queue = "CANCELLED" if process=="CANCELLED" else "FINISHED"
        await conn.execute("UPDATE runs SET process_status=?,queue_status=?,error_code=?,finished_at=? WHERE run_id=?",
                           (process, queue, code, time.time(), run_id))
        await conn.execute("UPDATE ledger SET status='RELEASED' WHERE run_id=? AND status='RESERVED' AND provider_attempt_id IS NULL", (run_id,))
        await audit(conn, None, code, {}, run_id)

    async def cancel(self, conn, run):
        if run["process_status"] in TERMINAL:
            return
        await self._stop(conn, run["run_id"], "CANCELLED", "USER_CANCELLED")

    async def authorized(self, conn, run) -> str | None:
        program = await one(conn, "SELECT * FROM programs WHERE program_id=?", (run["program_id"],))
        if (not program or not program["enabled"] or program["active_scope_version_id"] != run["scope_version_id"] or
                program["authorization_epoch"] != run["authorization_epoch"]):
            return "SCOPE_REVOKED"
        for user_id in {run["owner_user_id"], run["requested_by"]}:
            member = await one(conn, "SELECT m.role FROM memberships m JOIN users u USING(user_id) WHERE m.user_id=? "
                                    "AND m.program_id=? AND m.enabled=1 AND u.enabled=1", (user_id, run["program_id"]))
            if not member or (user_id != run["owner_user_id"] and member[0] != "PROGRAM_ADMIN"):
                return "MEMBERSHIP_REVOKED"
        target = await one(conn, "SELECT dirty,ready,dirty_run_id,maintenance FROM target_bindings WHERE target_id=?", (run["target_id"],))
        if not target or target["maintenance"] or (target["dirty"] and target["dirty_run_id"]!=run["run_id"]):
            return "TARGET_DIRTY"
        if (run["execution_mode"] != "mock" or run["tool_execution_mode"] == "LAB") and not target["ready"]:
            return "DEPENDENCY_NOT_READY"
        return None

    async def lease_next(self):
        async with self.db.transaction() as conn:
            expired = await all_rows(conn, "SELECT * FROM runs WHERE queue_status='LEASED' AND lease_expires_at<=?", (time.time(),))
            for run in expired:
                if run["execution_mode"] != "mock" or run["tool_execution_mode"] == "LAB":
                    await conn.execute("UPDATE target_bindings SET dirty=1 WHERE target_id=?", (run["target_id"],))
                await self._stop(conn, run["run_id"], "FAILED", "WORKER_LOST")
                await conn.execute("UPDATE ledger SET status='COST_UNKNOWN' WHERE run_id=? AND status='RESERVED' AND provider_attempt_id IS NOT NULL", (run["run_id"],))
            if await one(conn, "SELECT 1 FROM runs WHERE queue_status='LEASED'"):
                return None
            rows = await all_rows(conn, "SELECT * FROM runs WHERE queue_status='QUEUED' ORDER BY created_at")
            for run in rows:
                code = "QUEUE_EXPIRED" if run["queue_expires_at"] <= time.time() else await self.authorized(conn, run)
                if code:
                    await self._stop(conn, run["run_id"], "FAILED", code)
                    continue
                await conn.execute("UPDATE runs SET queue_status='LEASED',started_at=?,lease_expires_at=? WHERE run_id=?",
                                   (time.time(), time.time()+10, run["run_id"]))
                return run["run_id"]
        return None

    async def transition(self, run_id: str, following: str):
        async with self.db.transaction() as conn:
            run = await one(conn, "SELECT * FROM runs WHERE run_id=?", (run_id,))
            if run["queue_status"] != "LEASED":
                raise ProviderFailure("RUN_STOPPED", cost_idr=0)
            code = await self.authorized(conn, run)
            if not code and time.time()-run["started_at"] >= 180:
                code = "RUN_TIMEOUT"
            if not code and run["lease_expires_at"] <= time.time():
                code = "WORKER_LOST"
            if code:
                await self._stop(conn, run_id, "FAILED", code)
            else:
                validate_transition(run["process_status"], following)
                await conn.execute("UPDATE runs SET process_status=?,lease_expires_at=? WHERE run_id=?", (following, time.time()+10, run_id))
                await audit(conn, None, "STATE_CHANGED", {"from": run["process_status"], "to": following}, run_id)
        if code:
            raise ProviderFailure(code, cost_idr=0)

    async def tick(self):
        async with self.tick_lock:
            run_id = await self.lease_next()
            if not run_id:
                return
            try:
                async with self.db.connect() as conn:
                    run = await one(conn, "SELECT tool_execution_mode FROM runs WHERE run_id=?", (run_id,))
                if run[0] == "LAB":
                    await self.execute_lab(run_id)
                else:
                    await self.execute_mock(run_id)
            except AppError as exc:
                async with self.db.transaction() as conn:
                    await self._stop(conn, run_id, "FAILED", exc.code)
            except ProviderFailure as exc:
                async with self.db.transaction() as conn:
                    run = await one(conn, "SELECT * FROM runs WHERE run_id=?", (run_id,))
                    if run["process_status"] not in TERMINAL:
                        await self._stop(conn, run_id, "PROVIDER_REFUSED" if exc.code=="PROVIDER_REFUSED" else "FAILED", exc.code)
            except asyncio.CancelledError:
                async with self.db.transaction() as conn:
                    run = await one(conn, "SELECT * FROM runs WHERE run_id=?", (run_id,))
                    if run["process_status"] not in TERMINAL:
                        await self._stop(conn, run_id, "FAILED", "PROCESS_INTERRUPTED")
                raise
            except Exception as exc:
                async with self.db.transaction() as conn:
                    await self._stop(conn, run_id, "FAILED", "INTERNAL_ERROR")
                logger.error("Workflow failure run_id=%s error_type=%s", run_id, type(exc).__name__)
                raise

    async def execute_lab(self, run_id: str):
        from app.agent.lab_validation import validator_for
        from app.transport import Handoff
        async with self.db.connect() as conn:
            run = await one(conn, "SELECT * FROM runs WHERE run_id=?", (run_id,))
            revision = await one(conn, "SELECT claim_json FROM report_revisions WHERE revision_id=?", (run["report_revision_id"],))
        claim = Claim.model_validate_json(revision[0])
        validator = validator_for(claim)
        steps = validator.plan(claim)
        await self.transition(run_id, "PLANNED")
        session = ProviderSession(self.db, run_id, MOCK_PROFILE, [], MockTransport(), self.config.budget_idr, deadline=run["started_at"]+180)
        result = await session.call(f"Bounded deterministic {claim.category} development planner; no live inference.", 0)
        async with self.db.transaction() as conn:
            current = await one(conn, "SELECT counters_json FROM runs WHERE run_id=?", (run_id,))
            counters = json.loads(current[0])
            counters["model_calls"] = 1
            await conn.execute("UPDATE runs SET counters_json=? WHERE run_id=?", (packed(counters), run_id))
        await self.transition(run_id, "POLICY_CHECKED")
        await self.transition(run_id, "RUNNING")
        handoff = Handoff(self.db, self.config)
        for args in steps:
            action_id = await handoff.issue(run_id, args)
            observation = await handoff.wait(run_id, action_id)
            if observation["status"] != "OK":
                raise AppError(409, observation["error_code"] or "WORKER_ERROR", "Worker gagal; hasil tidak menjadi refutation.")
        await self.transition(run_id, "VERIFYING")
        async with self.db.transaction() as conn:
            current = await one(conn, "SELECT * FROM runs WHERE run_id=?", (run_id,))
            problem = await self.authorized(conn, current)
            if current["queue_status"] != "LEASED" or problem:
                raise AppError(409, problem or "RUN_STOPPED", "Run telah dihentikan.")
            assessment = await validator.verify(conn, run_id)
            assessment = await validate_assessment(conn, run_id, AssessmentProposal(claim_id=run["primary_claim_id"], **assessment))
            raw = {"mode": "mock", "text": result.text, "planner": run["prompt_version"], "steps": [s.model_dump(mode="json") for s in steps]}
            await conn.execute("INSERT INTO assessments(run_id,claim_id,verdict,raw_model_json,system_verified_json) VALUES (?,?,?,?,?)",
                               (run_id, run["primary_claim_id"], assessment["verdict"], packed(raw), packed(assessment)))
            await conn.execute("UPDATE runs SET process_status='COMPLETED',queue_status='FINISHED',finished_at=? WHERE run_id=?", (time.time(), run_id))
            await conn.execute("UPDATE target_bindings SET dirty_run_id=NULL WHERE target_id=?", (run["target_id"],))
            await conn.execute("UPDATE ledger SET status='SETTLED',actual_idr=0 WHERE run_id=? AND status='RESERVED' AND provider_attempt_id IS NULL", (run_id,))
            await audit(conn, None, claim.category+"_VERIFIED", {"verdict": assessment["verdict"], "model_mode": "mock"}, run_id)

    async def execute_mock(self, run_id: str):
        async with self.db.connect() as conn:
            run = await one(conn, "SELECT * FROM runs WHERE run_id=?", (run_id,))
        if run["execution_mode"] != "mock":
            raise ProviderFailure("CONFIGURATION_REQUIRED", cost_idr=0)
        for following in ("PLANNED", "POLICY_CHECKED", "RUNNING"):
            await self.transition(run_id, following)
        async with self.db.transaction() as conn:
            context = await simulation_context.build(conn, run_id)
            context_hash = digest(packed(context.model_dump()))
            await audit(conn, None, "SIMULATION_CONTEXT_BOUND", {"scope_version_id": context.scope_version_id,
                        "business_rules_version": context.business_rules_version, "context_sha256": context_hash}, run_id)
        session = ProviderSession(self.db, run_id, MOCK_PROFILE, [], MockTransport(), self.config.budget_idr,
                                  deadline=run["started_at"]+180)
        result = await session.call(simulation_context.prompt(context), 0)
        await self.transition(run_id, "VERIFYING")
        await asyncio.to_thread(check_storage, self.config, 512)
        action_id, evidence_id = uid(), uid()
        content = packed({"mode": "mock", "target_requests": 0, "message": result.text}).encode()
        # IDs, paths, hashes and provenance are created by the app, never by the model.
        directory = self.config.data_dir / "evidence" / run_id
        path = directory / (evidence_id+".json")
        await asyncio.to_thread(write_private, self.config.data_dir, path, content, LIMITS["artifact_bytes"])
        async with self.db.transaction() as conn:
            current = await one(conn, "SELECT * FROM runs WHERE run_id=?", (run_id,))
            if current["queue_status"] != "LEASED":
                await asyncio.to_thread(path.unlink, missing_ok=True)
                return
            code = await self.authorized(conn, current)
            if code:
                await self._stop(conn, run_id, "FAILED", code)
                await asyncio.to_thread(path.unlink, missing_ok=True)
                return
            await conn.execute("INSERT INTO actions VALUES (?,?, 'mock_observation',1,'{}',NULL,NULL,'ALLOW','SIMULATION_ONLY',?,?)",
                               (action_id, run_id, time.time(), time.time()))
            provenance = {"source": "application_mock", "run_id": run_id, "action_id": action_id,
                          "evidence_id": evidence_id, "mode": "mock", "target_requests": 0}
            await conn.execute("INSERT INTO evidence(evidence_id,run_id,action_id,kind,captured_at,artifact_path,sha256,actor_alias,target_alias,summary,provenance_json) "
                               "VALUES (?,?,?,'SIMULATION',?,?,?,?,?,?,?)",
                               (evidence_id, run_id, action_id, time.time(), str(path.relative_to(self.config.data_dir)),
                                digest(content), "mock", "no-target", "Simulasi plumbing; bukan bukti kerentanan.", packed(provenance)))
            assessment = {"claim_id": run["primary_claim_id"], "verdict": "INCONCLUSIVE", "reasoning": "Simulasi tanpa tool; tidak ada pengujian target.",
                          "supporting_evidence_ids": [], "contradicting_evidence_ids": [], "controls_performed": [],
                          "missing_prerequisites": ["Tools tidak dijalankan pada mode simulasi ini"],
                          "limitations": ["Bukan hasil model live", "Hanya klaim utama; klaim lain belum diperiksa"],
                          "next_action": "Gunakan mode HTTP lab hanya setelah scope dan prasyarat operator siap"}
            assessment = await validate_assessment(conn, run_id, AssessmentProposal(**assessment))
            await conn.execute("INSERT INTO assessments(run_id,claim_id,verdict,raw_model_json,system_verified_json) VALUES (?,?,'INCONCLUSIVE',?,?)",
                               (run_id, run["primary_claim_id"], packed({"mode": "mock", "text": result.text,
                                "context_sha256": context_hash, "scope_version_id": context.scope_version_id}), packed(assessment)))
            validate_transition(current["process_status"], "COMPLETED")
            await conn.execute("UPDATE runs SET process_status='COMPLETED',queue_status='FINISHED',finished_at=?,counters_json=? WHERE run_id=?",
                               (time.time(), packed({"model_calls": 1, "target_requests": 0, "denied_attempts": 0, "browser_actions": 0}), run_id))
            await conn.execute("UPDATE ledger SET status='SETTLED',actual_idr=0 WHERE run_id=? AND status='RESERVED' AND provider_attempt_id IS NULL", (run_id,))
            await audit(conn, None, "MOCK_COMPLETED", {"evidence_id": evidence_id}, run_id)

    async def loop(self):
        while not self.stop_event.is_set():
            self.wake.clear()
            try:
                await self.tick()
            except Exception as exc:
                # Individual failure was persisted; keep the singleton dispatcher available.
                logger.error("Dispatcher iteration failed error_type=%s", type(exc).__name__)
                pass
            try:
                await asyncio.wait_for(self.wake.wait(), timeout=0.25)
            except TimeoutError:
                pass
