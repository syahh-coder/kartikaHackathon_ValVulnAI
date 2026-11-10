"""Independent intake inference. Never imports workflow, worker or evaluator."""
import asyncio
import json
import time
from contextlib import suppress

from app.agent.ledger import reconcile, reserve
from app.auth import owned
from app.common import AppError, digest, packed, rate_limit, uid
from app.config import Settings
from app.providers.contracts import ProviderFailure, ProviderResult
from app.providers.openrouter import TextFailure, TextReply, strict_json
from app.providers.text_provider import (expected_model as resolved_model, input_token_bound, profile, require_configuration,
                                         secret, transport)
from app.providers.redaction import redact_text, redact_value
from app.providers.triage_contracts import (MAX_INPUT_TOKENS, PROMPT_VERSION, SCHEMA_VERSION,
                                           TriageSuggestion)
from app.storage.db import Database, all_rows, one
from app.storage.quota import check_storage


class MockTriageTransport:
    async def dispatch(self, call_id: str, prompt: str) -> TextReply:
        suggestion = TriageSuggestion(
            primary_claim="Simulasi triage; klaim belum diekstrak oleh model nyata.", category="UNKNOWN",
            subtype="UNKNOWN", missing_information=["Tinjau klaim dan prasyarat secara manual."],
            scope_suggestion="UNKNOWN", capability_suggestion="NEEDS_INFO",
            reason="ADAPTER MOCK: respons tetap, bukan inferensi AI atau hasil validasi target.")
        text = suggestion.model_dump_json()
        return TextReply(ProviderResult(call_id=call_id, provider_id="mock", requested_model_id="mock-triage-v1",
                                       resolved_model_id="mock-triage-v1", inference_provider="mock",
                                       text=text, usage={"input_tokens": 0, "output_tokens": 0},
                                       cost_status="KNOWN", actual_cost_idr=0), text, "0")


class TextTriage:
    def __init__(self, db: Database, config: Settings):
        self.db, self.config = db, config
        self.transport = transport(config) if config.triage_mode == "live" else MockTriageTransport()
        self.tasks: dict[str, asyncio.Task] = {}

    def secret(self) -> str:
        return secret(self.config)

    def configuration(self) -> dict:
        c = self.config
        return {"provider": c.triage_provider if c.triage_mode == "live" else c.triage_mode,
                "requested_model": c.triage_model if c.triage_mode == "live" else "mock-triage-v1",
                "provider_slug": c.triage_provider_slug, "provider_name": c.triage_provider_name,
                "access_tier": c.triage_access_tier, "price_snapshot": c.triage_price_snapshot,
                "prompt_usd_per_million": str(c.triage_prompt_usd_per_million),
                "completion_usd_per_million": str(c.triage_completion_usd_per_million),
                "usd_to_idr": str(c.triage_usd_to_idr), "reservation_idr": c.triage_reservation_idr,
                "timeout_seconds": c.triage_timeout_seconds, "retry_enabled": c.triage_retry_enabled,
                "max_attempts": 2 if c.triage_retry_enabled else 1, "input_tokens": 8192, "output_tokens": 1024,
                "token_bound": "operator-verified-utf8-byte-bpe-plus-1024", "tools": [], "fallbacks": [], **profile(c)}

    async def create(self, user, conversation_id: str, version: int, key: str) -> str:
        if not key or len(key) > 128 or not key.isascii() or not all(33 <= ord(c) <= 126 for c in key):
            raise AppError(422, "IDEMPOTENCY_REQUIRED", "Gunakan Idempotency-Key 1-128 karakter ASCII.")
        triage_id = uid()
        async with self.db.transaction() as conn:
            convo, _ = await owned(conn, "conversations", "conversation_id", conversation_id, user, owner_only=True)
            if convo["draft_version"] != version:
                raise AppError(409, "DRAFT_STALE", "Muat ulang versi draf terbaru.")
            program = await one(conn, "SELECT * FROM programs WHERE program_id=?", (convo["program_id"],))
            scope = await one(conn, "SELECT * FROM scope_versions WHERE scope_version_id=? AND state='ACTIVE'",
                              (program["active_scope_version_id"],))
            previous = await one(conn, "SELECT * FROM text_triages WHERE requested_by=? AND conversation_id=? AND idempotency_key=?",
                                 (user.user_id, conversation_id, key))
            if previous:
                if (previous["draft_version"] != version or previous["scope_version_id"] != program["active_scope_version_id"] or
                        previous["authorization_epoch"] != program["authorization_epoch"] or previous["mode"] != self.config.triage_mode):
                    raise AppError(409, "IDEMPOTENCY_CONFLICT", "Kunci sudah digunakan untuk konteks berbeda.")
                return previous["triage_id"]
            try:
                require_configuration(self.config)
            except ProviderFailure as exc:
                raise AppError(503, exc.code, "Triage teks memerlukan konfigurasi operator; mode tidak dialihkan.") from None
            attachment = await one(conn, "SELECT extracted_text FROM attachments WHERE conversation_id=?", (conversation_id,))
            if not convo["draft_body"].strip() and not attachment:
                raise AppError(422, "REPORT_EMPTY", "Isi laporan diperlukan.")
            source = {"report": {"title": convo["draft_title"], "text": convo["draft_body"],
                                 "attachment_text": attachment[0] if attachment else "", "draft_version": version},
                      "public_scope": {"scope_version_id": scope["scope_version_id"], "version": scope["version"],
                                       "rules": json.loads(scope["rules_json"])} if scope else None,
                      "data_authority": "UNTRUSTED_DATA_ONLY", "target_execution_allowed": False}
            # Redact individual strings before JSON encoding, retaining a valid JSON data boundary.
            prompt = packed(redact_value(source, self.secret()))
            if input_token_bound(self.config, prompt) > MAX_INPUT_TOKENS:
                raise AppError(413, "CONTEXT_LIMIT", "Teks/guideline melebihi batas konteks triage; ringkas input.")
            if await one(conn, "SELECT 1 FROM text_triages WHERE status IN ('PENDING','RUNNING')"):
                raise AppError(409, "TRIAGE_ACTIVE", "Satu triage teks masih aktif.")
            if await one(conn, "SELECT 1 FROM evaluation_jobs WHERE status='DISPATCHED'"):
                raise AppError(409, "EVALUATION_ACTIVE", "Evaluasi teks aktif atau memerlukan rekonsiliasi operator.")
            if (await one(conn, "SELECT count(*) FROM text_triages"))[0] >= 1000:
                raise AppError(503, "STORAGE_LIMIT", "Kapasitas riwayat triage memerlukan pemeriksaan operator.")
            await rate_limit(conn, "triage:" + user.user_id, 3, 3600)
            # DB/WAL now contain private bounded response snapshots too.
            db_bytes = sum(path.stat().st_size for path in
                           (self.db.path, self.db.path.with_name(self.db.path.name + "-wal"),
                            self.db.path.with_name(self.db.path.name + "-shm")) if path.exists())
            await asyncio.to_thread(check_storage, self.config, 200_000 + db_bytes)
            await conn.execute(
                "INSERT INTO text_triages(triage_id,conversation_id,program_id,owner_user_id,requested_by,session_hash,"
                "draft_version,scope_version_id,authorization_epoch,mode,status,idempotency_key,input_hash,prompt_version,"
                "schema_version,input_json,config_json,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,'PENDING',?,?,?,?,?,?,?)",
                (triage_id, conversation_id, convo["program_id"], convo["owner_user_id"], user.user_id, user.session_hash,
                 version, program["active_scope_version_id"], program["authorization_epoch"], self.config.triage_mode,
                 key, digest(prompt), PROMPT_VERSION, SCHEMA_VERSION, prompt, packed(self.configuration()), time.time()))
        task = asyncio.create_task(self._run(triage_id))
        self.tasks[triage_id] = task
        task.add_done_callback(lambda _: self.tasks.pop(triage_id, None))
        return triage_id

    async def _check(self, conn, row):
        current = await one(conn, "SELECT status FROM text_triages WHERE triage_id=?", (row["triage_id"],))
        if not current or current[0] not in {"PENDING", "RUNNING"}:
            raise ProviderFailure("TRIAGE_STOPPED")
        session = await one(conn, "SELECT s.*,u.enabled FROM sessions s JOIN users u USING(user_id) WHERE session_id_hash=?",
                            (row["session_hash"],))
        if not session or not session["enabled"] or session["revoked_at"] or session["expires_at"] <= time.time():
            raise ProviderFailure("SESSION_REVOKED")
        for user_id in {row["owner_user_id"], row["requested_by"]}:
            member = await one(conn, "SELECT 1 FROM memberships m JOIN users u USING(user_id) "
                               "WHERE m.user_id=? AND m.program_id=? AND m.enabled=1 AND u.enabled=1",
                               (user_id, row["program_id"]))
            if not member:
                raise ProviderFailure("MEMBERSHIP_REVOKED")
        program = await one(conn, "SELECT * FROM programs WHERE program_id=?", (row["program_id"],))
        if (not program["enabled"] or program["active_scope_version_id"] != row["scope_version_id"] or
                program["authorization_epoch"] != row["authorization_epoch"]):
            raise ProviderFailure("SCOPE_REVOKED")
        convo = await one(conn, "SELECT draft_version FROM conversations WHERE conversation_id=?", (row["conversation_id"],))
        if convo[0] != row["draft_version"]:
            raise ProviderFailure("DRAFT_STALE")

    async def _guarded_dispatch(self, row, call_id, deadline):
        async with self.db.connect() as conn:
            await self._check(conn, row)
        task = asyncio.create_task(self.transport.dispatch(call_id, row["input_json"]))
        try:
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise ProviderFailure("TRANSPORT_TIMEOUT")
                async with self.db.connect() as conn:
                    await self._check(conn, row)
                done, _ = await asyncio.wait([task], timeout=min(0.1, remaining))
                if done:
                    return task.result()
        finally:
            if not task.done():
                task.cancel()
            with suppress(asyncio.CancelledError, Exception):
                await task

    async def _infer(self, row):
        deadline = time.monotonic() + self.config.triage_timeout_seconds
        call_id = uid()
        for number in range(2 if self.config.triage_retry_enabled else 1):
            attempt_id, reply, error, failure = uid(), None, None, None
            async with self.db.transaction() as conn:
                await self._check(conn, row)
                if time.monotonic() >= deadline:
                    raise ProviderFailure("TRANSPORT_TIMEOUT")
                maximum = self.config.triage_reservation_idr if row["mode"] == "live" else 0
                entry_id = await reserve(conn, None, maximum, self.config.budget_idr, attempt_id, triage_id=row["triage_id"])
                await conn.execute("INSERT INTO provider_attempts(provider_attempt_id,call_id,provider_id,model_id,status,"
                                   "fallback_reason,created_at,triage_id) VALUES (?,?,?,?,'DISPATCHED',?,?,?)",
                                   (attempt_id, call_id, self.config.triage_provider if row["mode"] == "live" else "mock",
                                    self.config.triage_model if row["mode"] == "live" else "mock-triage-v1",
                                    "RETRY" if number else None, time.time(), row["triage_id"]))
            raw, cost, output = None, None, None
            metadata = {"input_hash": row["input_hash"], "prompt_version": PROMPT_VERSION, "schema_version": SCHEMA_VERSION}
            try:
                reply = await self._guarded_dispatch(row, call_id, deadline)
                result = reply.result
                raw, cost = reply.redacted_response, result.actual_cost_idr
                metadata.update({"provider": result.provider_id, "requested_model": result.requested_model_id,
                                 "resolved_model": result.resolved_model_id, "inference_provider": result.inference_provider,
                                 "provider_request_id": result.provider_request_id, "finish_reason": result.finish_reason,
                                 "usage": result.usage, "cost_usd": reply.cost_usd, "cost_status": result.cost_status,
                                 "reported_actual_cost_idr": result.actual_cost_idr})
                if cost is not None and cost > maximum:
                    raise ProviderFailure("COST_EXCEEDS_RESERVATION")
                expected_provider = self.config.triage_provider if row["mode"] == "live" else "mock"
                expected_model = self.config.triage_model if row["mode"] == "live" else "mock-triage-v1"
                expected_inference = self.config.triage_provider_name if row["mode"] == "live" else "mock"
                if (result.call_id != call_id or result.provider_id != expected_provider or
                        result.requested_model_id != expected_model or result.resolved_model_id != (resolved_model(self.config) if row["mode"] == "live" else expected_model) or
                        result.inference_provider != expected_inference):
                    raise ProviderFailure("PROVIDER_DRIFT")
                if result.refusal:
                    raise ProviderFailure("PROVIDER_REFUSED")
                if result.finish_reason != "stop":
                    raise ProviderFailure("INCOMPLETE_RESPONSE")
                parsed = strict_json(result.text)
                output = TriageSuggestion.model_validate(parsed, strict=True)
                # No raw provider text is ever projected as executable HTML.
                output = TriageSuggestion.model_validate(redact_value(output.model_dump(), self.secret()), strict=True)
                async with self.db.connect() as conn:
                    await self._check(conn, row)
            except asyncio.CancelledError:
                error = "TRIAGE_CANCELLED"
                raise
            except ProviderFailure as exc:
                error, failure = exc.code, exc
                if isinstance(exc, TextFailure):
                    raw = exc.raw
                if error == "COST_EXCEEDS_RESERVATION":
                    cost = None
            except (ValueError, TypeError, RecursionError):
                error, failure = "SCHEMA_ERROR", ProviderFailure("SCHEMA_ERROR")
            except Exception:
                error, failure = "ADAPTER_ERROR", ProviderFailure("ADAPTER_ERROR")
            finally:
                async with self.db.transaction() as conn:
                    await reconcile(conn, entry_id, cost)
                    await conn.execute("UPDATE provider_attempts SET status=?,error_code=?,usage_json=?,metadata_json=?,"
                                       "redacted_response=?,finished_at=? WHERE provider_attempt_id=?",
                                       ("FAILED" if error else "SUCCEEDED", error,
                                        packed(reply.result.usage) if reply else None, packed(redact_value(metadata, self.secret())),
                                        redact_text(raw, self.secret()) if raw is not None else None, time.time(), attempt_id))
            if not failure:
                return output
            if (not self.config.triage_retry_enabled or number or
                    failure.code not in {"TEMPORARY_429", "SERVER_ERROR", "TRANSPORT_TIMEOUT"}):
                raise failure
            if time.monotonic() + failure.retry_after >= deadline:
                raise ProviderFailure("TRANSPORT_TIMEOUT")
            if failure.retry_after:
                await asyncio.sleep(failure.retry_after)
        raise AssertionError("bounded inference loop exhausted")

    async def _run(self, triage_id):
        try:
            async with self.db.transaction() as conn:
                row = await one(conn, "SELECT * FROM text_triages WHERE triage_id=?", (triage_id,))
                await self._check(conn, row)
                await conn.execute("UPDATE text_triages SET status='RUNNING' WHERE triage_id=?", (triage_id,))
            output = await self._infer(row)
            async with self.db.transaction() as conn:
                await self._check(conn, row)
                await conn.execute("UPDATE text_triages SET status='SUCCEEDED',output_json=?,finished_at=? WHERE triage_id=?",
                                   (output.model_dump_json(), time.time(), triage_id))
        except asyncio.CancelledError:
            await self._fail(triage_id, "TRIAGE_CANCELLED", "CANCELLED")
        except (ProviderFailure, AppError) as exc:
            await self._fail(triage_id, exc.code)
        except Exception:
            await self._fail(triage_id, "ADAPTER_ERROR")

    async def _fail(self, triage_id, code, status="FAILED"):
        async with self.db.transaction() as conn:
            await conn.execute("UPDATE text_triages SET status=?,error_code=?,finished_at=? "
                               "WHERE triage_id=? AND status IN ('PENDING','RUNNING')", (status, code, time.time(), triage_id))

    async def get(self, user, triage_id):
        async with self.db.connect() as conn:
            row = await one(conn, "SELECT * FROM text_triages WHERE triage_id=?", (triage_id,))
            if not row:
                raise AppError(404, "NOT_FOUND", "Objek tidak ditemukan.")
            convo, role = await owned(conn, "conversations", "conversation_id", row["conversation_id"], user)
            program = await one(conn, "SELECT * FROM programs WHERE program_id=?", (row["program_id"],))
            attempts = await all_rows(conn, "SELECT p.*,l.status cost_status,l.reserved_idr,l.actual_idr "
                                      "FROM provider_attempts p JOIN ledger l USING(provider_attempt_id) "
                                      "WHERE p.triage_id=? ORDER BY p.created_at", (triage_id,))
        config = json.loads(row["config_json"])
        return {"triage_id": triage_id, "conversation_id": row["conversation_id"], "draft_version": row["draft_version"],
                "scope_version_id": row["scope_version_id"], "mode": row["mode"], "status": row["status"],
                "error_code": row["error_code"], "provider": config["provider"], "requested_model": config["requested_model"],
                "prompt_version": row["prompt_version"], "schema_version": row["schema_version"], "input_hash": row["input_hash"],
                "is_current": convo["draft_version"] == row["draft_version"] and
                program["active_scope_version_id"] == row["scope_version_id"] and
                program["authorization_epoch"] == row["authorization_epoch"],
                "suggestion_only": True, "label": "Saran AI" if row["mode"] == "live" else "Saran simulasi MOCK",
                "target_execution_allowed": False, "model_dispatch_allowed": False, "verdict": None,
                "suggestion": json.loads(row["output_json"]) if row["output_json"] else None,
                "attempts": [{"attempt_id": a["provider_attempt_id"], "status": a["status"], "error_code": a["error_code"],
                              "cost_status": a["cost_status"], "reserved_idr": a["reserved_idr"], "actual_idr": a["actual_idr"],
                              "metadata": json.loads(a["metadata_json"]) if a["metadata_json"] else None,
                              **({"redacted_response": a["redacted_response"]} if role == "PROGRAM_ADMIN" else {})}
                             for a in attempts]}

    async def cancel(self, user, triage_id):
        await self.get(user, triage_id)
        await self._fail(triage_id, "TRIAGE_CANCELLED", "CANCELLED")
        task = self.tasks.get(triage_id)
        if task:
            task.cancel()
            await task

    async def recover(self):
        async with self.db.transaction() as conn:
            await conn.execute("UPDATE text_triages SET status='FAILED',error_code='PROCESS_INTERRUPTED',finished_at=? "
                               "WHERE status IN ('PENDING','RUNNING')", (time.time(),))
            await conn.execute("UPDATE ledger SET status='COST_UNKNOWN' WHERE triage_id IS NOT NULL AND status='RESERVED'")
            await conn.execute("UPDATE provider_attempts SET status='FAILED',error_code='PROCESS_INTERRUPTED',finished_at=? "
                               "WHERE triage_id IS NOT NULL AND status='DISPATCHED'", (time.time(),))

    async def close(self):
        tasks = list(self.tasks.values())
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
