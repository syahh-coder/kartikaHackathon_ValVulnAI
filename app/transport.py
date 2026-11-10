"""App-owned handoff with authorization per action, shared by workflow and operator."""
import asyncio
import hashlib
import json
from pathlib import Path
import time
from uuid import UUID

from app.agent.workflow import Workflow
from app.api.routes import bindings_for
from app.common import AppError, audit, packed, uid
from app.policy.targets import check_action
from app.schemas import Claim
from app.storage.db import Database, one
from app.storage.files import write_private
from app.storage.quota import check_storage
from boundary.contracts import ActionEnvelope, BrowserArguments, UploadArguments, Control, HttpArguments, canonical, observation_from, signed, verified
from boundary.files import read_json, write_json


class Handoff:
    def __init__(self,db: Database,config,inbox=Path("/handoff/inbox"),outbox=Path("/handoff/outbox"),key=None):
        self.db,self.config,self.inbox,self.outbox=db,config,inbox,outbox
        self.key=key if key is not None else bytes.fromhex(config.transport_key_file.read_text().strip())
        if len(self.key)!=32:
            raise ValueError("Invalid handoff key")
        self.workflow=Workflow(db,config)

    def heartbeat(self):
        value=verified(read_json(self.outbox,"heartbeat.json",16384),self.key)
        now=time.time()
        UUID(value["boot_id"])
        if not now-5 <= value["captured_at"] <= now+1 or value["status"] not in {"IDLE","BUSY"}:
            raise AppError(503,"WORKER_NOT_READY","Heartbeat worker tidak valid/kedaluwarsa.")
        return value

    def control(self,kind,*,run_id=None,action_id=None,snapshot_id=None):
        now=time.time()
        record=Control(control_id=uid(),kind=kind,run_id=run_id,action_id=action_id,snapshot_id=snapshot_id,issued_at=now,expires_at=now+30)
        write_json(self.inbox,str(record.control_id)+".control.json",signed(record.model_dump(mode="json"),self.key),16384)
        return str(record.control_id)

    async def issue(self,run_id: str,args: HttpArguments | BrowserArguments | UploadArguments):
        async with self.db.transaction() as conn:
            run=await one(conn,"SELECT * FROM runs WHERE run_id=?",(run_id,))
            if not run or run["queue_status"]!="LEASED" or run["tool_execution_mode"]!="LAB":
                raise AppError(409,"RUN_NOT_AUTHORIZED","Run bukan lease tool lab yang aktif.")
            problem=await self.workflow.authorized(conn,run)
            if problem:
                raise AppError(409,problem,"Otorisasi run telah berubah.")
            heartbeat=self.heartbeat()
            if heartbeat["boot_id"]!=run["worker_boot_id"] or heartbeat["snapshot_id"]!=run["target_snapshot_id"]:
                raise AppError(409,"WORKER_CHANGED","Worker/snapshot telah berubah; jangan replay aksi.")
            if heartbeat["dirty"] and heartbeat["dirty_run_id"]!=run_id:
                raise AppError(409,"TARGET_DIRTY","Target memerlukan reset evaluator.")
            revision=await one(conn,"SELECT claim_json FROM report_revisions WHERE revision_id=?",(run["report_revision_id"],))
            scope=await one(conn,"SELECT rules_json FROM scope_versions WHERE scope_version_id=? AND state='ACTIVE'",(run["scope_version_id"],))
            rules=json.loads(scope[0]) if scope else {}
            bindings=await bindings_for(conn,run["program_id"])
            claim=Claim.model_validate_json(revision[0])
            check_action(claim,rules,bindings[claim.asset_alias],method=args.method,path=args.relative_path,account_alias=args.account_alias)
            counters=json.loads(run["counters_json"])
            browser = isinstance(args, BrowserArguments)
            if browser and counters.get("browser_actions", 0)+5 > 30:
                raise AppError(429,"BROWSER_LIMIT","Batas aksi browser tercapai.")
            if 16777216-counters.get("artifact_bytes",0)<4096:
                raise AppError(413,"ARTIFACT_LIMIT","Sisa ruang artefak tidak cukup untuk aksi baru.")
            if counters.get("network_reserved",0)+2>40:
                raise AppError(429,"NETWORK_LIMIT","Batas 40 dispatch jaringan tercapai.")
            if await one(conn,"SELECT 1 FROM handoff_actions WHERE run_id=? AND status='ISSUED'",(run_id,)):
                raise AppError(409,"ACTION_OUTSTANDING","Masih ada aksi yang belum diketahui hasilnya.")
            now=time.time()
            expires=min(now+(30 if browser else 10),run["started_at"]+180)
            if expires<=now:
                raise AppError(409,"RUN_TIMEOUT","Batas waktu run tercapai.")
            sequence=(await one(conn,"SELECT count(*)+1 FROM actions WHERE run_id=?",(run_id,)))[0]
            action_id=uid()
            def scoped(source):
                return [{"path_template":r["path_template"],"methods":r["methods"]} for r in source if r["asset_alias"]==claim.asset_alias]
            envelope=ActionEnvelope(run_id=run_id,action_id=action_id,action_seq=sequence,program_id=run["program_id"],
                                    scope_version_id=run["scope_version_id"],authorization_epoch=run["authorization_epoch"],
                                    target_snapshot_id=run["target_snapshot_id"],validated_arguments=args,
                                    tool_name="browser_probe" if browser else "upload_fixture" if isinstance(args, UploadArguments) else "http_request",
                                    allowed_rules=scoped(rules["in_scope_rules"]),excluded_rules=scoped(rules["out_of_scope_rules"]),
                                    issued_at=now,expires_at=expires,network_remaining=40-counters.get("network_reserved",0),
                                    artifact_remaining=16777216-counters.get("artifact_bytes",0))
            payload=envelope.model_dump(mode="json")
            fingerprint=hashlib.sha256(canonical(payload)).hexdigest()
            await conn.execute("INSERT INTO actions(action_id,run_id,tool_name,arguments_json,account_alias,policy_result,policy_reason,started_at) "
                               "VALUES (?,?,?,?,?,'ALLOW','SCOPED_LAB',?)",(action_id,run_id,envelope.tool_name,packed(args.model_dump(mode="json")),args.account_alias,now))
            await conn.execute("INSERT INTO handoff_actions VALUES (?,?,?,?,?,'ISSUED',NULL,?)",(action_id,run_id,sequence,packed(payload),fingerprint,expires))
            counters["network_reserved"]=counters.get("network_reserved",0)+2
            if browser:
                counters["browser_actions"] = counters.get("browser_actions", 0)+5
            await conn.execute("UPDATE runs SET counters_json=?,lease_expires_at=? WHERE run_id=?",(packed(counters),now+10,run_id))
            if args.method in {"DELETE", "POST"} or browser:
                await conn.execute("UPDATE target_bindings SET dirty=1,dirty_run_id=? WHERE target_id=?",(run_id,run["target_id"]))
        await asyncio.to_thread(write_json,self.inbox,action_id+".job.json",signed(payload,self.key),65536)
        return action_id

    async def wait(self,run_id: str,action_id: str):
        async with self.db.connect() as conn:
            outstanding=await one(conn,"SELECT * FROM handoff_actions WHERE action_id=? AND run_id=?",(action_id,run_id))
        if not outstanding:
            raise AppError(404,"ACTION_NOT_FOUND","Aksi tidak ditemukan.")
        if outstanding["status"]=="RECEIVED":
            return json.loads(outstanding["observation_json"])
        while time.time()<outstanding["expires_at"]+2:
            try:
                document=await asyncio.to_thread(read_json,self.outbox,action_id+".result.json",2*1048576)
                return await self.import_result(run_id,action_id,document)
            except FileNotFoundError:
                pass
            heartbeat=self.heartbeat()
            async with self.db.transaction() as conn:
                run=await one(conn,"SELECT * FROM runs WHERE run_id=?",(run_id,))
                problem = await self.workflow.authorized(conn,run)
                if run["queue_status"]!="LEASED" or problem:
                    self.control("CANCEL",run_id=run_id)
                    raise AppError(409,problem or "RUN_STOPPED","Run dihentikan.")
                if heartbeat["boot_id"]!=run["worker_boot_id"]:
                    break
                await conn.execute("UPDATE runs SET lease_expires_at=? WHERE run_id=?",(time.time()+10,run_id))
            await asyncio.sleep(0.1)
        await self.fail(run_id,"ACTION_OUTCOME_UNKNOWN")
        raise AppError(409,"ACTION_OUTCOME_UNKNOWN","Hasil aksi ambigu; reset evaluator diperlukan.")

    async def import_result(self,run_id: str,action_id: str,document: dict):
        observation=observation_from(verified(document,self.key))
        async with self.db.transaction() as conn:
            action=await one(conn,"SELECT * FROM handoff_actions WHERE action_id=? AND run_id=?",(action_id,run_id))
            run=await one(conn,"SELECT * FROM runs WHERE run_id=?",(run_id,))
            if not action or not run:
                raise AppError(422,"OBSERVATION_MISMATCH","Observasi tidak cocok dengan aksi outstanding.")
            if action["status"]=="RECEIVED":
                return json.loads(action["observation_json"])
            envelope=ActionEnvelope.model_validate_json(action["envelope_json"])
            browser = envelope.tool_name == "browser_probe"
            if (observation.model_dump().get("tool_name") == "browser_probe") != browser:
                raise AppError(422,"OBSERVATION_MISMATCH","Jenis observasi tidak cocok dengan tool.")
            upload = envelope.tool_name == "upload_fixture"
            if (observation.model_dump().get("tool_name") == "upload_fixture") != upload:
                raise AppError(422,"OBSERVATION_MISMATCH","Jenis observasi upload tidak cocok.")
            if upload and observation.status == "OK":
                from boundary.uploads import UploadedFile, filename
                value = UploadedFile.model_validate_json(observation.body)
                args = envelope.validated_arguments
                if str(value.request_id) != args.relative_path.split('/')[3] or value.filename != filename(args.fixture, args.nonce):
                    raise AppError(422,"OBSERVATION_MISMATCH","Objek/fixture upload tidak cocok.")
            if browser and observation.status == "OK":
                from boundary.browser import BrowserCapture
                capture = BrowserCapture.model_validate_json(observation.body)
                if (capture.nonce != envelope.validated_arguments.nonce or capture.fixture != envelope.validated_arguments.fixture
                        or capture.path != envelope.validated_arguments.relative_path):
                    raise AppError(422,"OBSERVATION_MISMATCH","Fixture/nonce browser tidak cocok.")
            if (str(observation.run_id)!=run_id or str(observation.action_id)!=action_id or
                    observation.action_seq!=envelope.action_seq or observation.envelope_hash!=action["envelope_hash"] or
                    str(observation.target_snapshot_id)!=run["target_snapshot_id"] or str(observation.boot_id)!=run["worker_boot_id"] or
                    observation.actor_alias!=envelope.validated_arguments.account_alias or
                    observation.method!=envelope.validated_arguments.method or observation.relative_path!=envelope.validated_arguments.relative_path or
                    not envelope.issued_at-1<=observation.captured_at<=envelope.expires_at+1):
                raise AppError(422,"OBSERVATION_MISMATCH","Provenance observasi tidak sah.")
            if run["queue_status"]!="LEASED":
                raise AppError(409,"RUN_STOPPED","Run telah berakhir; observasi memerlukan review.")
            problem = await self.workflow.authorized(conn, run)
            if problem:
                self.control("CANCEL", run_id=run_id)
                raise AppError(409, problem, "Otorisasi run telah dicabut.")
            body=observation.model_dump(mode="json")
            data=canonical(body)
            counters=json.loads(run["counters_json"])
            if browser and observation.status == "OK":
                counters["denied_attempts"] = counters.get("denied_attempts",0)+capture.denied_requests+capture.websocket_blocks+capture.popup_blocks+capture.download_blocks
            if len(data)+counters.get("artifact_bytes",0)>16777216:
                raise AppError(413,"ARTIFACT_LIMIT","Batas artefak run tercapai.")
            await asyncio.to_thread(check_storage,self.config,len(data))
            evidence_id=uid()
            path=self.config.data_dir/"evidence"/run_id/(evidence_id+".json")
            await asyncio.to_thread(write_private,self.config.data_dir,path,data,16777216)
            provenance={"source":"worker_browser" if browser else "worker_upload" if upload else "worker_http","mode":"lab_tools","run_id":run_id,"action_id":action_id,
                        "evidence_id":evidence_id,"worker_boot_id":run["worker_boot_id"],"envelope_hash":action["envelope_hash"],"snapshot_id":run["target_snapshot_id"]}
            await conn.execute("INSERT INTO evidence(evidence_id,run_id,action_id,kind,captured_at,artifact_path,sha256,actor_alias,target_alias,summary,provenance_json) "
                               "VALUES (?,?,?,?,?,?,?,?,?,?,?)",(evidence_id,run_id,action_id,"BROWSER_PROBE" if browser else "UPLOAD_EXCHANGE" if upload else "HTTP_EXCHANGE",observation.captured_at,
                                 str(path.relative_to(self.config.data_dir)),hashlib.sha256(data).hexdigest(),observation.actor_alias,"portal",
                                 "Observasi browser lab aktual; belum merupakan verdict." if browser else "Observasi HTTP lab aktual; belum merupakan verdict.",packed(provenance)))
            await conn.execute("UPDATE handoff_actions SET status='RECEIVED',observation_json=? WHERE action_id=?",(packed(body),action_id))
            await conn.execute("UPDATE actions SET finished_at=? WHERE action_id=?",(time.time(),action_id))
            counters["target_requests"]=counters.get("target_requests",0)+observation.request_attempts
            counters["responses_received"]=counters.get("responses_received",0)+observation.responses_received
            counters["artifact_bytes"]=counters.get("artifact_bytes",0)+len(data)
            await conn.execute("UPDATE runs SET counters_json=?,lease_expires_at=? WHERE run_id=?",(packed(counters),time.time()+10,run_id))
            await audit(conn,None,"WORKER_OBSERVATION_IMPORTED",{"evidence_id":evidence_id},run_id)
        self.control("ACK",run_id=run_id,action_id=action_id)
        (self.inbox/(action_id+".job.json")).unlink(missing_ok=True)
        return body

    async def fail(self,run_id,code):
        self.control("CANCEL",run_id=run_id)
        async with self.db.transaction() as conn:
            await conn.execute("UPDATE target_bindings SET dirty=1,dirty_run_id=NULL WHERE target_id='portal-lab'")
            await conn.execute("UPDATE handoff_actions SET status='UNKNOWN' WHERE run_id=? AND status='ISSUED'",(run_id,))
            run=await one(conn,"SELECT queue_status FROM runs WHERE run_id=?",(run_id,))
            if run and run[0] in {"QUEUED","LEASED"}:
                await self.workflow._stop(conn,run_id,"FAILED",code)
