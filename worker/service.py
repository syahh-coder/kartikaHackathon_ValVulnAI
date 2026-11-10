import asyncio
import hashlib
import json
import os
from pathlib import Path
import time
from uuid import uuid4

from boundary.contracts import ActionEnvelope, BrowserObservation, UploadObservation, Control, Observation, canonical, observation_from, signed, verified
from boundary.files import read_json, write_json
from worker.http_tool import HttpTool


class Worker:
    def __init__(self,inbox: Path,outbox: Path,key: bytes,accounts: dict,tool=None):
        self.inbox,self.outbox,self.key=inbox,outbox,key
        self.boot_id=str(uuid4())
        from worker.browser_tool import ToolRouter
        self.tool=tool or ToolRouter(accounts)
        self.task=None
        self.current=None
        try:
            self.state=read_json(outbox,"worker-state.json",20*1048576)
        except FileNotFoundError:
            self.state={"snapshot_id":None,"dirty":True,"dirty_run_id":None,"seen":{},"sequences":{},"counters":{},"active":None,"controls":{}}
        self.state.setdefault("cancelled_runs",{})
        self.stop=False

    def save(self):
        write_json(self.outbox,"worker-state.json",self.state,20*1048576)

    def publish(self,result: Observation):
        write_json(self.outbox,str(result.action_id)+".result.json",signed(result.model_dump(mode="json"),self.key),2*1048576)

    def recover(self):
        active=self.state.get("active")
        if active:
            e=ActionEnvelope.model_validate(active["envelope"])
            cls = BrowserObservation if e.tool_name == "browser_probe" else UploadObservation if e.tool_name == "upload_fixture" else Observation
            result=cls(run_id=e.run_id,action_id=e.action_id,action_seq=e.action_seq,envelope_hash=active["hash"],
                               target_snapshot_id=e.target_snapshot_id,boot_id=self.boot_id,status="ACTION_OUTCOME_UNKNOWN",
                               error_code="ACTION_OUTCOME_UNKNOWN",actor_alias=e.validated_arguments.account_alias,
                               method=e.validated_arguments.method,relative_path=e.validated_arguments.relative_path,
                               body="",body_sha256=hashlib.sha256(b"").hexdigest(),request_attempts=2,responses_received=0,captured_at=time.time())
            self.state["seen"][str(e.action_id)]={"hash":active["hash"],"expires":e.expires_at,"result":result.model_dump(mode="json")}
            self.state["dirty"],self.state["dirty_run_id"],self.state["active"]=True,None,None
            self.save()
            self.publish(result)

    def heartbeat(self):
        now=time.time()
        payload={"schema_version":1,"boot_id":self.boot_id,"captured_at":now,"active_run_id":str(self.current.run_id) if self.current else None,
                 "snapshot_id":self.state["snapshot_id"],"dirty":self.state["dirty"],"dirty_run_id":self.state["dirty_run_id"],"status":"BUSY" if self.task else "IDLE"}
        write_json(self.outbox,"heartbeat.json",signed(payload,self.key),16384)

    async def controls(self):
        for path in sorted(self.inbox.glob("*.control.json")):
            try:
                control=Control.model_validate(verified(read_json(self.inbox,path.name,16384),self.key))
                now=time.time()
                if control.issued_at>now+1 or control.expires_at<=now or str(control.control_id) in self.state["controls"]:
                    continue
                if control.kind=="RESET_RELEASE":
                    if self.task or control.issued_at<=self.state.get("last_release_at",0):
                        continue
                    self.state.update(snapshot_id=str(control.snapshot_id),dirty=False,dirty_run_id=None,last_release_at=control.issued_at)
                    self.state["sequences"],self.state["counters"]={},{}
                    # Old signed jobs cannot run against the new snapshot.
                elif control.kind=="CANCEL":
                    self.state["cancelled_runs"][str(control.run_id)]=now+300
                    if self.current and str(self.current.run_id)==str(control.run_id):
                        self.task.cancel()
                    if self.state["dirty"]:
                        self.state["dirty_run_id"]=None
                elif control.kind=="ACK":
                    seen=self.state["seen"].get(str(control.action_id))
                    if seen and str(seen["result"]["run_id"])==str(control.run_id):
                        (self.outbox/(str(control.action_id)+".result.json")).unlink(missing_ok=True)
                        seen["acked"]=True
                self.state["controls"][str(control.control_id)]=control.expires_at
                self.save()
            except (ValueError,OSError,KeyError):
                continue

    async def accept(self,path: Path):
        document=read_json(self.inbox,path.name,65536)
        payload=verified(document,self.key)
        envelope=ActionEnvelope.model_validate(payload)
        if path.name!=str(envelope.action_id)+".job.json":
            raise ValueError("FILENAME_MISMATCH")
        envelope.authorize()
        fingerprint=hashlib.sha256(canonical(payload)).hexdigest()
        run,action=str(envelope.run_id),str(envelope.action_id)
        if self.state["snapshot_id"]!=str(envelope.target_snapshot_id):
            raise ValueError("SNAPSHOT_STALE")
        if self.state["cancelled_runs"].get(run,0)>time.time():
            raise ValueError("RUN_CANCELLED")
        seen=self.state["seen"].get(action)
        if seen:
            if seen["hash"]!=fingerprint:
                raise ValueError("ACTION_REPLAY_MISMATCH")
            if not seen.get("acked"):
                self.publish(observation_from(seen["result"]))
            return
        if self.task:
            return
        if self.state["dirty"] and self.state["dirty_run_id"]!=run:
            raise ValueError("TARGET_DIRTY")
        if envelope.action_seq!=self.state["sequences"].get(run,0)+1:
            raise ValueError("ACTION_SEQUENCE")
        reserved=self.state["counters"].get(run,0)
        if reserved+2>40 or envelope.network_remaining<2:
            raise ValueError("NETWORK_LIMIT")
        self.state["counters"][run]=reserved+2  # Reserve both login and action before I/O.
        self.state["sequences"][run]=envelope.action_seq
        if envelope.validated_arguments.method in {"DELETE", "POST"} or envelope.tool_name == "browser_probe":
            self.state["dirty"],self.state["dirty_run_id"]=True,run
        self.state["active"]={"envelope":payload,"hash":fingerprint}
        self.save()  # Crash before/after I/O is never a reason to replay a mutation.
        self.current=envelope
        self.task=asyncio.create_task(self.tool.execute(envelope,fingerprint,self.boot_id))

    async def finish(self):
        if self.task and self.task.done():
            try:
                result=self.task.result()
            except asyncio.CancelledError:
                # Cancellation can arrive before HttpTool starts its own try block.
                # Keep the worker alive and publish an ambiguous bounded outcome.
                e = self.current
                status = "ACTION_OUTCOME_UNKNOWN" if e.validated_arguments.method in {"DELETE", "POST"} else "CANCELLED"
                cls = BrowserObservation if e.tool_name == "browser_probe" else UploadObservation if e.tool_name == "upload_fixture" else Observation
                result = cls(run_id=e.run_id, action_id=e.action_id, action_seq=e.action_seq,
                    envelope_hash=self.state["active"]["hash"], target_snapshot_id=e.target_snapshot_id, boot_id=self.boot_id,
                    status=status, error_code=status, actor_alias=e.validated_arguments.account_alias,
                    method=e.validated_arguments.method, relative_path=e.validated_arguments.relative_path,
                    body="", body_sha256=hashlib.sha256(b"").hexdigest(), request_attempts=0, responses_received=0,
                    captured_at=time.time())
            except BaseException:
                # Retain active journal for fail-closed recovery, no automatic replay.
                self.state["dirty"],self.state["dirty_run_id"]=True,None
                self.save()
                raise
            action=str(result.action_id)
            self.state["seen"][action]={"hash":result.envelope_hash,"expires":self.current.expires_at,"result":result.model_dump(mode="json")}
            self.state["active"]=None
            if result.status in {"CANCELLED","ACTION_OUTCOME_UNKNOWN"}:
                self.state["dirty"],self.state["dirty_run_id"]=True,None
            self.save()
            self.publish(result)
            self.task,self.current=None,None

    async def run(self):
        self.recover()
        last=0
        try:
            while not self.stop:
                await self.controls()
                await self.finish()
                for path in sorted(self.inbox.glob("*.job.json")):
                    try:
                        await self.accept(path)
                    except (ValueError,OSError,KeyError):
                        # Invalid input never reaches a transport. No attacker-controlled logging.
                        pass
                now=time.time()
                if now-last>=2:
                    self.heartbeat(); last=now
                    # Only expired, acknowledged transient state may be removed.
                    self.state["seen"]={k:v for k,v in self.state["seen"].items() if v["expires"]>now or not v.get("acked")}
                    self.state["controls"]={k:v for k,v in self.state["controls"].items() if v>now}
                    self.state["cancelled_runs"]={k:v for k,v in self.state["cancelled_runs"].items() if v>now}
                    self.save()
                await asyncio.sleep(0.1)
        finally:
            if self.task:
                self.task.cancel()
                await self.finish_after_cancel()

    async def finish_after_cancel(self):
        try:
            await self.task
        except BaseException:
            return
        await self.finish()


async def main():
    import fcntl
    outbox=Path("/handoff/outbox")
    # One worker owns the channel. Lock is advisory for application code and released on death.
    with (outbox/"worker.lock").open("a+b") as lock:
        fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        key=bytes.fromhex(Path("/run/secrets/job_key").read_text().strip())
        accounts=json.loads(Path("/run/secrets/lab_accounts").read_text())
        if len(key)!=32 or set(accounts)!={"requester-a","requester-b"}:
            raise ValueError("Invalid worker configuration")
        await Worker(Path("/handoff/inbox"),outbox,key,accounts).run()


if __name__=="__main__":
    asyncio.run(main())
