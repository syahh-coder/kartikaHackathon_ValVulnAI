"""Explicit M2 operator checks, including lab reset. No provider/model dispatch.

Usage: python -m evaluator.m2 verify
       python -m evaluator.m2 reset --condition fixed
"""
import argparse
import json
from pathlib import Path
import subprocess
import time

ROOT=Path(__file__).resolve().parents[1]


def compose(*args,input=None):
    result=subprocess.run(["docker","compose",*args],cwd=ROOT,input=input,capture_output=True,text=True)
    if result.returncode:
        # Values from secret files and login payloads are never logged.
        message=result.stdout.strip()
        if message.startswith("{"):
            raise RuntimeError(message)
        raise RuntimeError("Docker/operator step failed; inspect service logs locally")
    return result.stdout


def cli(service,module,*args,payload=None):
    return json.loads(compose("exec","-T","--user","10001:10001",service,"python","-m",module,*args,input=json.dumps(payload or {})))


def operator(operation,payload=None):
    return cli("app","app.m2_operator",operation,payload=payload)


def ready():
    for _ in range(30):
        try:
            heartbeat=operator("heartbeat")
            if heartbeat["status"]=="IDLE": return heartbeat
        except RuntimeError:
            pass
        time.sleep(0.2)
    raise RuntimeError("Worker heartbeat unavailable")


def reset(condition,*,arm_delay=False,xss_condition="fixed"):
    ready()
    operator("maintenance_enter")
    snapshot=cli("lab","lab.maintenance","reset","--condition",condition,"--xss-condition",xss_condition)
    assertion=cli("lab","lab.maintenance","inspect")
    assert assertion["snapshot_id"]==snapshot["snapshot_id"]
    assert len(assertion["attachments"])==2 and all(not a["deleted"] for a in assertion["attachments"])
    health=json.loads(compose("exec","-T","--user","10001:10001","lab","python","-c",
        "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8001/api/health',timeout=3).read().decode())"))
    assert health=={"status":"ok","seeded":True}
    if arm_delay:
        cli("lab","lab.maintenance","arm-delay")
    operator("maintenance_release",{"snapshot_id":snapshot["snapshot_id"]})
    return snapshot


def crash_check():
    snapshot=reset("vulnerable",arm_delay=True)
    victim=snapshot["objects"]["requester-b"]["attachment_id"]
    run=operator("begin",{"path":"/api/attachments/"+victim})
    issued=operator("issue_only",{"run_id":run["run_id"],"arguments":{"method":"DELETE","relative_path":"/api/attachments/"+victim,"account_alias":"requester-a"}})
    try:
        # Observe the actual committed mutation while its response is deliberately pending.
        for _ in range(20):
            state=cli("lab","lab.maintenance","inspect")
            if any(x["id"]==victim and x["deleted"] for x in state["attachments"]): break
            time.sleep(0.1)
        else: raise RuntimeError("Did not observe the pre-crash mutation")
        worker_id=compose("ps","-q","worker").strip()
        subprocess.run(["docker","kill","--signal","KILL",worker_id],capture_output=True,check=True)
        # Restart policy is not a job replay: recovery must publish an unknown outcome.
        compose("up","-d","worker")
        ready()
        journal=operator("journal_status",{"action_id":issued["action_id"]})
        assert journal["status"]=="ACTION_OUTCOME_UNKNOWN"
        count=delete_count()
        time.sleep(0.3)
        assert delete_count()==count
        operator("fail",{"run_id":run["run_id"]})
        try:
            operator("begin",{"path":"/api/attachments/"+victim})
        except RuntimeError as exc: assert "TARGET_DIRTY" in str(exc)
        else: raise AssertionError("Crash did not block the next run")
    except BaseException:
        operator("fail",{"run_id":run["run_id"]})
        raise
    reset("fixed")
    result={"status":"PASS","run_id":run["run_id"],"actual_mutation_before_crash":True,
            "recovered_outcome":"ACTION_OUTCOME_UNKNOWN","automatic_replay":False,"dirty_gate":"PASS","model_calls":0}
    directory=ROOT/"artifacts"/"m2"
    directory.mkdir(parents=True,exist_ok=True)
    (directory/"crash-check.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps(result,indent=2))


def network_checks():
    for _ in range(60):
        lab_id=compose("ps","-q","lab").strip()
        if lab_id:
            state=json.loads(subprocess.check_output(["docker","inspect",lab_id],text=True))[0]["State"]
            if state.get("Health",{}).get("Status")=="healthy": break
        time.sleep(0.2)
    else: raise RuntimeError("Lab did not become healthy")
    app_id=compose("ps","-q","app").strip()
    app_info=json.loads(subprocess.check_output(["docker","inspect",app_id],text=True))[0]
    app_ip=next(iter(app_info["NetworkSettings"]["Networks"].values()))["IPAddress"]
    reports={}
    for service in ("worker","lab"):
        targets=[("metadata","169.254.169.254",80),("reserved_external","198.51.100.10",443),
                 ("host_gateway","172.30.74.1",8000),("app_control",app_ip,8000),("other_lab_port","172.30.74.3",80)]
        # TEST-NET and metadata probes are rejected in the namespace before any packet leaves.
        code="""import socket,json,os,pathlib
targets=TARGETS
result={'uid':os.getuid(),'probes':{},'forbidden_paths':{}}
for name,host,port in targets:
 s=socket.socket();s.settimeout(.4)
 try:
  result['probes'][name]={'connected':s.connect_ex((host,port))==0}
 except OSError: result['probes'][name]={'connected':False}
 finally: s.close()
s=socket.socket();s.settimeout(.5)
try: result['positive_target']=s.connect_ex(('172.30.74.3' if SERVICE=='worker' else '127.0.0.1',8001))==0
finally: s.close()
ipv6=socket.socket(socket.AF_INET6);ipv6.settimeout(.3)
try: result['ipv6_external_connected']=ipv6.connect_ex(('2001:db8::1',443))==0
except OSError: result['ipv6_external_connected']=False
finally: ipv6.close()
udp=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);udp.settimeout(.3)
try:
 udp.connect(('127.0.0.11',53));udp.send(b'\\x00'*12);udp.recv(100)
 result['docker_dns_replied']=True
except OSError: result['docker_dns_replied']=False
finally: udp.close()
for path in ['/var/run/docker.sock','/data/valvuln.sqlite3','/opt/valvuln/evaluator','/opt/valvuln/app','/opt/valvuln/.env','/run/secrets/job_key']:
 result['forbidden_paths'][path]=pathlib.Path(path).exists()
if SERVICE=='worker':
 try:
  pathlib.Path('/handoff/inbox/forbidden-write').write_text('test')
  result['inbox_read_only']=False
 except OSError: result['inbox_read_only']=True
result['provider_key_env_present']=any(k.endswith('API_KEY') for k in os.environ)
for status in pathlib.Path('/proc').glob('[0-9]*/status'):
 try:
  cmd=(status.parent/'cmdline').read_bytes()
  if (SERVICE=='worker' and b'worker.service' in cmd) or (SERVICE=='lab' and b'uvicorn' in cmd):
   values=dict(line.split(':',1) for line in status.read_text().splitlines() if ':' in line)
   if values['Name'].strip() in ('python','uvicorn'):
    result['service_uid']=values['Uid'].split()[0]
    result['service_cap_eff']=values['CapEff'].strip()
    result['service_cap_prm']=values['CapPrm'].strip()
    result['service_cap_bnd']=values['CapBnd'].strip()
    result['service_no_new_privs']=values['NoNewPrivs'].strip()
 except (OSError,KeyError): pass
print(json.dumps(result))
""".replace("TARGETS",repr(targets)).replace("SERVICE",repr(service))
        report=json.loads(compose("exec","-T","--user","10001:10001",service,"python","-",input=code))
        assert report["uid"]==10001 and report["positive_target"]
        assert all(not p["connected"] for p in report["probes"].values())
        assert not report["docker_dns_replied"] and not report["provider_key_env_present"]
        assert not report["ipv6_external_connected"]
        assert report["service_uid"]=="10001" and int(report["service_cap_eff"],16)==0 and int(report["service_cap_bnd"],16)==0 and int(report["service_cap_prm"],16)==0
        assert report["service_no_new_privs"]=="1"
        if service=="worker":
            assert report["inbox_read_only"]
            assert not any(report["forbidden_paths"][p] for p in report["forbidden_paths"] if p!="/run/secrets/job_key")
        else:
            assert not any(report["forbidden_paths"].values())
        reports[service]=report
    # The app has no network membership in the lab, and cannot connect to its TCP listener.
    code="import socket; s=socket.socket();s.settimeout(.4);print(s.connect_ex(('172.30.74.3',8001)))"
    assert int(compose("exec","-T","app","python","-c",code).strip())!=0
    reports["app_to_lab_blocked"]=True
    name="operator-symlink-probe.json"
    code="from pathlib import Path; Path('/handoff/outbox/"+name+"').symlink_to('/handoff/outbox/heartbeat.json')"
    compose("exec","-T","--user","10001:10001","worker","python","-c",code)
    try:
        code="""from pathlib import Path
from boundary.files import read_json
try: read_json(Path('/handoff/outbox'),'operator-symlink-probe.json')
except ValueError: print('SYMLINK_REJECTED')
else: raise RuntimeError('Symlink was accepted')
try: Path('/handoff/outbox/forbidden-write').write_text('test')
except OSError: print('OUTBOX_READ_ONLY')
else: raise RuntimeError('App can write outbox')
"""
        output=compose("exec","-T","app","python","-",input=code)
        assert "SYMLINK_REJECTED" in output and "OUTBOX_READ_ONLY" in output
    finally:
        compose("exec","-T","--user","10001:10001","worker","python","-c","from pathlib import Path; Path('/handoff/outbox/"+name+"').unlink()")
    reports["symlink_rejected_and_app_outbox_read_only"]=True
    return reports


def delete_count():
    code="import sqlite3; c=sqlite3.connect('/data/lab.sqlite3'); print(c.execute(\"SELECT count(*) FROM access_log WHERE method='DELETE'\").fetchone()[0])"
    return int(compose("exec","-T","--user","10001:10001","lab","python","-c",code).strip())


def verify():
    ready()
    network=network_checks()
    operator("configure_scope")
    cases=[]
    for condition in ("vulnerable","fixed"):
        snapshot=reset(condition)
        a=snapshot["objects"]["requester-a"]["attachment_id"]
        b=snapshot["objects"]["requester-b"]["attachment_id"]
        run=operator("begin",{"path":"/api/attachments/"+b})
        observations=[]
        steps=[("GET",b,"requester-b"),("DELETE",b,"requester-a"),("GET",b,"requester-b"),
               ("GET",a,"requester-a"),("DELETE",a,"requester-a"),("GET",a,"requester-a")]
        try:
            for index,(method,aid,actor) in enumerate(steps):
                obs=operator("action",{"run_id":run["run_id"],"arguments":{"method":method,"relative_path":"/api/attachments/"+aid,"account_alias":actor}})
                observations.append(obs)
                if index==1:
                    before=delete_count()
                    operator("duplicate_check",{"action_id":obs["action_id"]})
                    assert delete_count()==before,"Duplicate delivery repeated a DELETE"
            statuses=[o["http_status"] for o in observations]
            assert statuses==([200,200,404,200,200,404] if condition=="vulnerable" else [200,404,200,200,200,404]),statuses
            first=json.loads(observations[0]["body"])
            assert first["attachment_id"]==b and first["owner_alias"]=="requester-b"
            inspected=cli("lab","lab.maintenance","inspect")
            removed={x["owner"]:x["deleted"] for x in inspected["attachments"]}
            assert removed["requester-b"]==(condition=="vulnerable") and removed["requester-a"]
            finished=operator("finish",{"run_id":run["run_id"]})
            assert finished["assessment"] is None
            # A mutation, even a rejected one, requires evaluator reset before the next run.
            try:
                operator("begin",{"path":"/api/attachments/"+b})
            except RuntimeError as exc:
                assert "TARGET_DIRTY" in str(exc)
            else:
                raise AssertionError("Dirty target allowed another run")
            cases.append({"condition":condition,"run_id":run["run_id"],"http_statuses":statuses,"cross_owner_deleted":removed["requester-b"],
                          "owner_control_deleted":removed["requester-a"],"network_dispatches":sum(o["request_attempts"] for o in observations),
                          "duplicate_delete_replayed":False,"dirty_gate":"PASS","assessment":None})
        except BaseException:
            operator("fail",{"run_id":run["run_id"]})
            raise
    # Verify restart is idle and retains lab state/app evidence/ledger.
    before=cli("lab","lab.maintenance","inspect")
    compose("restart","worker","lab")
    ready()
    assert cli("lab","lab.maintenance","inspect")==before
    reset("fixed")
    result={"status":"PASS","cases":cases,"network":network,"restart_no_reset":"PASS","model_calls":0,
            "verification_kind":"operator-controlled development reproduction; not held-out or human GT approval"}
    directory=ROOT/"artifacts"/"m2"
    directory.mkdir(parents=True,exist_ok=True)
    (directory/"verification.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps(result,indent=2))


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation",choices=["verify","reset","network","crash-check"])
    parser.add_argument("--condition",choices=["vulnerable","fixed"])
    parser.add_argument("--xss-condition",choices=["vulnerable","fixed"],default="fixed")
    args=parser.parse_args()
    if args.operation=="verify": verify()
    elif args.operation=="network":
        result=network_checks()
        directory=ROOT/"artifacts"/"m2"
        directory.mkdir(parents=True,exist_ok=True)
        (directory/"network-check.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
        print(json.dumps(result,indent=2))
    elif args.operation=="crash-check": crash_check()
    else:
        if not args.condition: parser.error("reset requires an explicit --condition")
        print(json.dumps(reset(args.condition,xss_condition=args.xss_condition),indent=2))
