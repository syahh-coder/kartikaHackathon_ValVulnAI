"""Explicit admin maintenance, separate from report triage and validation tools."""
import asyncio
from contextlib import suppress
import time

from app.auth import member
from app.common import AppError, audit, uid
from app.storage.db import one
from boundary.files import read_json, write_json
from boundary.lab_reset import LabCondition, ResetRequest, ResetResult


class LabReset:
    def __init__(self, db, config):
        self.db, self.config = db, config
        self.task = None
        self.lock = asyncio.Lock()
        self.status_path = config.data_dir / "lab-reset"

    def stored(self):
        try:
            return read_json(self.status_path, "status.json", 32768)
        except FileNotFoundError:
            return {"status": "NOT_STARTED"}

    def save(self, value):
        self.status_path.mkdir(parents=True, exist_ok=True)
        write_json(self.status_path, "status.json", value, 32768)

    def control_ready(self):
        root = self.config.lab_reset_control_dir
        if root is None:
            raise AppError(503, "RESET_NOT_CONFIGURED", "Reset UI belum diaktifkan pada lab ini.")
        try:
            beat = read_json(root, "heartbeat.json", 4096)
            if not time.time() - 5 <= beat["captured_at"] <= time.time() + 1:
                raise ValueError("STALE")
        except (OSError, ValueError, KeyError) as exc:
            raise AppError(503, "RESET_NOT_READY", "Kanal reset lab belum siap.") from exc
        if beat["status"] != "IDLE":
            raise AppError(409, "RESET_BUSY", "Reset lab masih aktif atau perlu pemeriksaan operator.")
        return root

    async def status(self, user, program_id):
        async with self.db.connect() as conn:
            await member(conn, user, program_id, admin=True)
            target = await one(conn, "SELECT ready,dirty,maintenance,snapshot_id FROM target_bindings WHERE target_id='portal-lab' AND program_id=?", (program_id,))
        if not target:
            raise AppError(404, "NOT_FOUND", "Lab program tidak ditemukan.")
        configured = self.config.lab_reset_control_dir is not None
        value = self.stored()
        manual = {"active": False}
        if self.config.shared_lab_manual and self.config.lab_reset_control_dir:
            try:
                manual = read_json(self.config.lab_reset_control_dir, "manual-session.json", 4096)
            except FileNotFoundError:
                pass
        manual_active = (manual.get("active") is True and manual.get("expires_at", 0) > time.time()
                         and manual.get("snapshot_id") == target["snapshot_id"] and bool(target["maintenance"]))
        applied = value.get("condition") if (value["status"] == "SUCCEEDED" and
                    value.get("snapshot_id") == target["snapshot_id"]) else None
        return {**value, "configured": configured, "target": dict(target), "applied_condition": applied,
                "applied_coverage": value.get("coverage") if applied else None,
                "available_conditions": ["vulnerable", "fixed"], "manual_active": manual_active,
                "manual_available": bool(self.config.shared_lab_manual and configured),
                "manual_url": "http://127.0.0.1:8001/" if self.config.shared_lab_manual else None}

    async def open_manual(self, user, program_id):
        from app.m2_operator import execute
        from app.transport import Handoff
        async with self.lock:
            async with self.db.connect() as conn:
                await member(conn, user, program_id, admin=True)
                target = await one(conn, "SELECT snapshot_id FROM target_bindings WHERE target_id='portal-lab' AND program_id=?", (program_id,))
            if not target:
                raise AppError(404, "NOT_FOUND", "Lab program tidak ditemukan.")
            if not self.config.shared_lab_manual or not target["snapshot_id"]:
                raise AppError(503, "MANUAL_NOT_CONFIGURED", "Akses manual target worker belum siap.")
            if self.task and not self.task.done():
                raise AppError(409, "RESET_BUSY", "Tunggu reset selesai sebelum pengujian manual.")
            root = await asyncio.to_thread(self.control_ready)
            handoff = await asyncio.to_thread(Handoff, self.db, self.config)
            await execute("maintenance_enter", {}, self.db, self.config, handoff)
            now = time.time()
            write_json(root, "manual-session.json", {"active": True, "session_id": uid(),
                       "snapshot_id": target["snapshot_id"], "expires_at": now+3600}, 4096)
            async with self.db.transaction() as conn:
                await audit(conn, user.user_id, "SHARED_LAB_MANUAL_OPENED", {"snapshot_id": target["snapshot_id"]})
            return {"manual_active": True, "manual_url": "http://127.0.0.1:8001/",
                    "snapshot_id": target["snapshot_id"]}

    async def start(self, user, program_id, condition: LabCondition = "vulnerable"):
        from app.m2_operator import execute
        from app.transport import Handoff
        async with self.lock:
            async with self.db.connect() as conn:
                await member(conn, user, program_id, admin=True)
                target = await one(conn, "SELECT 1 FROM target_bindings WHERE target_id='portal-lab' AND program_id=?", (program_id,))
            if not target:
                raise AppError(404, "NOT_FOUND", "Lab program tidak ditemukan.")
            if self.task and not self.task.done():
                raise AppError(409, "RESET_BUSY", "Reset lab sedang berjalan.")
            root = await asyncio.to_thread(self.control_ready)
            handoff = await asyncio.to_thread(Handoff, self.db, self.config)
            await execute("maintenance_enter", {}, self.db, self.config, handoff)
            # Revoke manual access before enqueueing; the lab consumer waits for
            # any in-flight manual handler to finish before resetting data.
            write_json(root, "manual-session.json", {"active": False, "expires_at": 0}, 4096)
            request_id = uid()
            now = time.time()
            record = {"status": "RUNNING", "request_id": request_id, "started_at": now, "condition": condition, "coverage": "ALL_IMPLEMENTED"}
            # Persist before enqueueing. Crash recovery never creates a new reset.
            self.save(record)
            async with self.db.transaction() as conn:
                await audit(conn, user.user_id, "ADMIN_LAB_RESET_REQUESTED", {"request_id": request_id, "condition": condition})
            request = ResetRequest(request_id=request_id, operation="RESET_DEMO_LAB", condition=condition, issued_at=now, expires_at=now+30)
            write_json(root, f"{request_id}.request.json", request.model_dump(mode="json"), 4096)
            self.task = asyncio.create_task(self.finish(user, program_id, record, root, handoff))
            return record

    async def finish(self, user, program_id, record, root, handoff):
        from app.m2_operator import execute
        result_record = {**record, "status": "FAILED", "error_code": "RESET_FAILED"}
        try:
            deadline = time.monotonic() + 40
            while True:
                try:
                    result = ResetResult.model_validate(read_json(root, f"{record['request_id']}.result.json", 16384))
                    break
                except FileNotFoundError:
                    if time.monotonic() >= deadline:
                        raise ValueError("RESET_TIMEOUT")
                    await asyncio.sleep(0.2)
            if (str(result.request_id) != record["request_id"] or result.status != "SUCCEEDED" or
                    not result.snapshot_id or result.condition != record["condition"] or result.coverage != "ALL_IMPLEMENTED"):
                raise ValueError("RESET_FAILED")
            async with self.db.connect() as conn:
                await member(conn, user, program_id, admin=True)
            await execute("maintenance_release", {"snapshot_id": str(result.snapshot_id)}, self.db, self.config, handoff)
            result_record = {**record, **result.model_dump(mode="json"), "status": "SUCCEEDED"}
        except asyncio.CancelledError:
            result_record["error_code"] = "RESET_OUTCOME_UNKNOWN"
            raise
        except Exception:
            # Maintenance/dirty stays set after any unknown or failed reset.
            pass
        finally:
            result_record["finished_at"] = time.time()
            self.save(result_record)
            async with self.db.transaction() as conn:
                await audit(conn, user.user_id, "ADMIN_LAB_RESET_FINISHED", {
                    "request_id": record["request_id"], "status": result_record["status"],
                    "condition": record.get("condition"), "error_code": result_record.get("error_code")})

    async def recover(self):
        record = self.stored()
        if record["status"] == "RUNNING":
            self.save({**record, "status": "FAILED", "error_code": "RESET_OUTCOME_UNKNOWN"})

    async def close(self):
        if self.task and not self.task.done():
            self.task.cancel()
            with suppress(asyncio.CancelledError):
                await self.task
