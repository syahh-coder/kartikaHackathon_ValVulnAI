"""Trusted operator CLI for M2 tests. Never mounted in worker or exposed as a route/tool."""
import asyncio
import json
import sys
import time
from uuid import UUID

from app.agent.workflow import Workflow
from app.auth import Principal
from app.common import AppError, audit, digest, packed, uid
from app.config import Settings
from app.schemas import Claim, RunInput, ScopeDraft
from app.storage.db import Database, all_rows, one
from app.transport import Handoff
from boundary.contracts import BrowserArguments, HttpArguments


async def execute(operation: str,payload: dict,db: Database,config,handoff: Handoff):
    if operation=="heartbeat":
        return handoff.heartbeat()
    if operation in {"register_browser", "register_upload"}:
        # Explicit operator action, never migration/startup or a model tool.
        from app.policy.targets import validate_scope
        async with db.transaction() as conn:
            if await one(conn,"SELECT 1 FROM runs WHERE queue_status IN ('QUEUED','LEASED')"):
                raise AppError(409,"RUN_ACTIVE","Hentikan run sebelum mengubah profil/scope.")
            target = await one(conn,"SELECT * FROM target_bindings WHERE target_id='portal-lab'")
            program = await one(conn,"SELECT * FROM programs WHERE program_id=?",(target["program_id"],))
            admin = await one(conn,"SELECT u.user_id FROM users u JOIN memberships m USING(user_id) WHERE u.login_name='admin' AND m.program_id=? AND m.role='PROGRAM_ADMIN' AND m.enabled=1 AND u.enabled=1",(program["program_id"],))
            if not admin: raise AppError(409,"ADMIN_SEED_REQUIRED","Seed admin diperlukan.")
            profile = json.loads(target["profile_json"])
            upload = operation == "register_upload"
            paths = ["/api/requests/{id}/attachments", "/requests/{id}/attachments", "/requests/{id}/attachment-labels"] if upload else ["/notifications/preview"]
            capability = "UPLOAD" if upload else "XSS"
            profile["route_templates"] = sorted(set(profile["route_templates"] + paths))
            profile["capabilities"] = sorted(set(profile["capabilities"] + [capability]))
            if upload:
                profile["methods"] = sorted(set(profile["methods"] + ["POST"]))
            await conn.execute("UPDATE target_bindings SET profile_json=? WHERE target_id='portal-lab'",(packed(profile),))
            old = await one(conn,"SELECT rules_json FROM scope_versions WHERE scope_version_id=?",(program["active_scope_version_id"],))
            rules = json.loads(old[0]) if old else {"in_scope_rules":[],"out_of_scope_rules":[],"business_rules":""}
            for path in paths:
                rule = {"asset_alias":"portal","path_template":path,"methods":["POST" if path.startswith('/api/requests/') else "GET"],"capabilities":[capability]}
                if rule not in rules["in_scope_rules"]: rules["in_scope_rules"].append(rule)
            rules["source_text"] = rules.get("source_text","") + ("\nOperator mengizinkan upload fixture teks tetap oleh A dan pembacaan nama/label oleh reviewer B yang ditugaskan; tanpa script laporan." if upload else "\nOperator mengizinkan probe browser development pratinjau notifikasi, fixtures tetap tanpa callback jaringan.")
            draft = ScopeDraft.model_validate(rules)
            validate_scope(draft,{"portal":{"profile":profile}})
            scope_id = uid()
            version=(await one(conn,"SELECT coalesce(max(version),0)+1 FROM scope_versions WHERE program_id=?",(program["program_id"],)))[0]
            await conn.execute("UPDATE scope_versions SET state='RETIRED' WHERE program_id=? AND state='ACTIVE'",(program["program_id"],))
            await conn.execute("INSERT INTO scope_versions(scope_version_id,program_id,version,state,rules_json,source_text,source_hash,activated_by,activated_at) VALUES (?,?,?,'ACTIVE',?,?,?,?,?)",
                (scope_id,program["program_id"],version,packed(draft.model_dump()),draft.source_text,digest(draft.source_text),admin[0],time.time()))
            await conn.execute("UPDATE programs SET active_scope_version_id=?,authorization_epoch=authorization_epoch+1 WHERE program_id=?",(scope_id,program["program_id"]))
            await audit(conn,admin[0],"OPERATOR_UPLOAD_PROFILE_ACTIVATED" if upload else "OPERATOR_BROWSER_PROFILE_ACTIVATED",{"scope_version_id":scope_id,"tool":"upload_fixture" if upload else "notification_probe"})
        return {"scope_version_id":scope_id,"browser_ui":"NOT_CONNECTED","profile_registered":True}
    if operation=="configure_scope":
        async with db.transaction() as conn:
            admin=await one(conn,"SELECT u.* FROM users u JOIN memberships m USING(user_id) WHERE u.login_name='admin' AND m.role='PROGRAM_ADMIN' AND m.enabled=1 AND u.enabled=1")
            program=await one(conn,"SELECT * FROM programs WHERE enabled=1 LIMIT 1")
            if not admin or not program:
                raise AppError(409,"PLATFORM_SEED_REQUIRED","Seed platform dahulu.")
            if program["active_scope_version_id"]:
                return {"scope_version_id":program["active_scope_version_id"],"changed":False}
            draft=ScopeDraft(source_text="Lab lokal development. Izin eksplisit GET/DELETE lampiran dengan dua akun sintetis.",
                             in_scope_rules=[{"asset_alias":"portal","path_template":"/api/attachments/{id}","methods":["GET","DELETE"],"capabilities":["BAC"]}])
            scope_id=uid()
            version=(await one(conn,"SELECT coalesce(max(version),0)+1 FROM scope_versions WHERE program_id=?",(program["program_id"],)))[0]
            await conn.execute("INSERT INTO scope_versions(scope_version_id,program_id,version,state,rules_json,source_text,source_hash,activated_by,activated_at) VALUES (?,?,?,'ACTIVE',?,?,?,?,?)",
                               (scope_id,program["program_id"],version,packed(draft.model_dump()),draft.source_text,digest(draft.source_text),admin["user_id"],time.time()))
            await conn.execute("UPDATE programs SET active_scope_version_id=?,authorization_epoch=authorization_epoch+1 WHERE program_id=?",(scope_id,program["program_id"]))
            await audit(conn,admin["user_id"],"OPERATOR_SCOPE_ACTIVATED",{"scope_version_id":scope_id})
        return {"scope_version_id":scope_id,"changed":True}
    if operation=="maintenance_enter":
        heartbeat=handoff.heartbeat()
        if heartbeat["active_run_id"] or heartbeat["status"]!="IDLE":
            raise AppError(409,"WORKER_BUSY","Worker masih aktif; reset ditolak.")
        async with db.transaction() as conn:
            if await one(conn,"SELECT 1 FROM runs WHERE queue_status IN ('QUEUED','LEASED')"):
                raise AppError(409,"RUN_ACTIVE","Hentikan run sebelum reset.")
            await conn.execute("UPDATE target_bindings SET maintenance=1,ready=0,dirty=1,dirty_run_id=NULL WHERE target_id='portal-lab'")
            await audit(conn,None,"TARGET_MAINTENANCE_ENTER",{})
        return {"maintenance":True}
    if operation=="maintenance_release":
        snapshot_id=str(UUID(payload["snapshot_id"]))
        async with db.connect() as conn:
            target=await one(conn,"SELECT maintenance FROM target_bindings WHERE target_id='portal-lab'")
        if not target or not target[0]:
            raise AppError(409,"MAINTENANCE_REQUIRED","Masuk maintenance dahulu.")
        handoff.control("RESET_RELEASE",snapshot_id=snapshot_id)
        for _ in range(60):
            heartbeat=handoff.heartbeat()
            if heartbeat["snapshot_id"]==snapshot_id and not heartbeat["dirty"] and heartbeat["status"]=="IDLE":
                break
            await asyncio.sleep(0.1)
        else:
            raise AppError(503,"RESET_NOT_ACKNOWLEDGED","Worker belum mengakui snapshot baru.")
        async with db.transaction() as conn:
            await conn.execute("UPDATE target_bindings SET maintenance=0,ready=1,dirty=0,dirty_run_id=NULL,snapshot_id=? WHERE target_id='portal-lab'",(snapshot_id,))
            await audit(conn,None,"TARGET_MAINTENANCE_RELEASE",{"snapshot_id":snapshot_id})
        return {"ready":True,"snapshot_id":snapshot_id}
    if operation in {"begin", "begin_browser"}:
        heartbeat=handoff.heartbeat()
        browser = operation == "begin_browser"
        claim=Claim(asset_alias="portal",path="/notifications/preview" if browser else payload["path"],method="GET" if browser else "DELETE",category="XSS" if browser else "BAC",
                    account_aliases=["requester-a","requester-b"],primary_claim="Uji development marker DOM pada pratinjau notifikasi." if browser else "Uji development penghapusan lampiran lintas akun.")
        async with db.transaction() as conn:
            if await one(conn,"SELECT 1 FROM runs WHERE queue_status IN ('QUEUED','LEASED')"):
                raise AppError(409,"RUN_ACTIVE","Masih ada run pending.")
            target=await one(conn,"SELECT * FROM target_bindings WHERE target_id='portal-lab'")
            if (not target or target["dirty"] or target["maintenance"] or not target["ready"] or heartbeat["dirty"] or
                    heartbeat["status"]!="IDLE" or heartbeat["snapshot_id"]!=target["snapshot_id"]):
                raise AppError(409,"TARGET_DIRTY","Reset/health evaluator diperlukan.")
            admin=await one(conn,"SELECT u.user_id,u.login_name,m.program_id FROM users u JOIN memberships m USING(user_id) WHERE login_name='admin' AND m.role='PROGRAM_ADMIN' AND m.enabled=1 AND u.enabled=1")
            if not admin:
                raise AppError(409,"ADMIN_SEED_REQUIRED","Seed admin diperlukan.")
            c,r,revision=uid(),uid(),uid()
            body="OPERATOR M2: reproduksi development terkontrol; bukan dataset atau hasil model."
            await conn.execute("INSERT INTO conversations(conversation_id,program_id,owner_user_id,draft_title,draft_body,draft_version,created_at) VALUES (?,?,?,'Development operator M2',?,1,?)",(c,admin["program_id"],admin["user_id"],body,time.time()))
            await conn.execute("INSERT INTO reports VALUES (?,?,?,?)",(r,admin["program_id"],admin["user_id"],c))
            await conn.execute("INSERT INTO report_revisions VALUES (?,?,1,1,'Development operator M2',?,NULL,'',?,?,?)",(revision,r,body,digest(body+packed(claim.model_dump())),packed(claim.model_dump()),time.time()))
            report=await one(conn,"SELECT * FROM reports WHERE report_id=?",(r,))
            run_id=await Workflow(db,config).create_run(conn,Principal(admin["user_id"],admin["login_name"],""),report,
                                                       RunInput(report_revision_id=revision,execution_mode="mock"),uid(),operator=True)
            run=await one(conn,"SELECT * FROM runs WHERE run_id=?",(run_id,))
            if run["queue_status"]!="QUEUED":
                raise AppError(409,"GATE_DENIED","Scope/prasyarat tidak memberi izin worker.")
            await conn.execute("UPDATE runs SET process_status='RUNNING',queue_status='LEASED',tool_execution_mode='LAB',target_snapshot_id=?,worker_boot_id=?,started_at=?,lease_expires_at=? WHERE run_id=?",
                               (target["snapshot_id"],heartbeat["boot_id"],time.time(),time.time()+10,run_id))
            await audit(conn,admin["user_id"],"OPERATOR_LAB_RUN_STARTED",{},run_id)
        return {"run_id":run_id,"report_id":r,"model_calls":0,"tool_execution_mode":"LAB"}
    if operation in {"action","issue_only", "browser_action"}:
        run_id=str(UUID(payload["run_id"]))
        args=(BrowserArguments.model_validate(payload["arguments"] | {"nonce":uid()}) if operation == "browser_action"
              else HttpArguments.model_validate(payload["arguments"]))
        action_id=await handoff.issue(run_id,args)
        if operation=="issue_only":
            return {"run_id":run_id,"action_id":action_id}
        try:
            result=await handoff.wait(run_id,action_id)
        except Exception:
            await handoff.fail(run_id,"ACTION_OUTCOME_UNKNOWN")
            raise
        if result["status"]!="OK":
            await handoff.fail(run_id,result["error_code"] or "WORKER_ERROR")
            raise AppError(409,"WORKER_ERROR","Worker gagal; bukti dan alasan disimpan untuk review.")
        return result
    if operation=="journal_status":
        from boundary.contracts import Observation,verified
        from boundary.files import read_json
        action_id=str(UUID(payload["action_id"]))
        result=Observation.model_validate(verified(read_json(handoff.outbox,action_id+".result.json",2*1048576),handoff.key))
        return {"status":result.status,"error_code":result.error_code,"run_id":str(result.run_id),"action_id":str(result.action_id)}
    if operation=="finish":
        run_id=str(UUID(payload["run_id"]))
        async with db.transaction() as conn:
            run=await one(conn,"SELECT * FROM runs WHERE run_id=?",(run_id,))
            if not run or run["queue_status"]!="LEASED" or run["tool_execution_mode"]!="LAB":
                raise AppError(409,"RUN_STOPPED","Run bukan lease operator aktif.")
            if await one(conn,"SELECT 1 FROM handoff_actions WHERE run_id=? AND status='ISSUED'",(run_id,)):
                raise AppError(409,"ACTION_OUTSTANDING","Aksi belum selesai.")
            await conn.execute("UPDATE runs SET process_status='COMPLETED',queue_status='FINISHED',finished_at=? WHERE run_id=?",(time.time(),run_id))
            await conn.execute("UPDATE target_bindings SET dirty_run_id=NULL WHERE target_id=?",(run["target_id"],))
            await conn.execute("UPDATE ledger SET status='SETTLED',actual_idr=0 WHERE run_id=? AND provider_attempt_id IS NULL AND status='RESERVED'",(run_id,))
            await audit(conn,None,"OPERATOR_LAB_RUN_FINISHED",{"assessment":None},run_id)
        return {"run_id":run_id,"process_status":"COMPLETED","assessment":None,"target_reset_required":True}
    if operation=="duplicate_check":
        # Test an identical delivery, never create a new action or change its arguments.
        from boundary.files import write_json
        from boundary.contracts import signed
        async with db.connect() as conn:
            row=await one(conn,"SELECT * FROM handoff_actions WHERE action_id=? AND status='RECEIVED'",(str(UUID(payload["action_id"])),))
        if not row:
            raise AppError(404,"ACTION_NOT_FOUND","Observasi terimpor diperlukan.")
        name=row["action_id"]+".job.json"
        write_json(handoff.inbox,name,signed(json.loads(row["envelope_json"]),handoff.key),65536)
        await asyncio.sleep(0.5)
        (handoff.inbox/name).unlink(missing_ok=True)
        return {"identical_delivery_tested":True}
    if operation=="fail":
        await handoff.fail(str(UUID(payload["run_id"])),"OPERATOR_INTERRUPTED")
        return {"status":"FAILED","target_reset_required":True}
    raise ValueError("Unknown operator operation")


async def main():
    config=Settings()
    db=Database(config.db_path)
    await db.migrate()
    payload=json.loads(sys.stdin.read(65537) or "{}")
    if len(packed(payload).encode())>65536:
        raise ValueError("Operator input too large")
    try:
        result=await execute(sys.argv[1],payload,db,config,Handoff(db,config))
        print(packed(result))
    except AppError as exc:
        print(packed({"error_code":exc.code,"message":exc.message}))
        raise SystemExit(1)


if __name__=="__main__":
    asyncio.run(main())
