"""Isolated app-only container startup/restart. No lab, worker, provider or active-data mutation."""
import argparse
import json
import secrets
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = '''import sqlite3,json,hashlib
c=sqlite3.connect('file:/data/valvuln.sqlite3?mode=ro',uri=True)
tables=['users','memberships','programs','conversations','messages','reports','runs','actions','evidence','assessments','ledger','provider_attempts','text_triages']
result={}
for t in tables:
 if not c.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",(t,)).fetchone():
  result[t]={'present':False}
  continue
 rows=sorted(c.execute('SELECT * FROM '+t).fetchall(),key=repr)
 result[t]={'count':len(rows),'sha256':hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest()}
print(json.dumps(result))'''
HEALTH = "import urllib.request,json;print(urllib.request.urlopen('http://127.0.0.1:8000/api/health',timeout=2).read().decode())"
SEED = '''import asyncio,json,sys
from app.config import Settings
from app.operator import seed
from app.storage.db import Database
asyncio.run(seed(Database(Settings().db_path),json.loads(sys.stdin.read())['password']))'''


def command(args, *, stdin=None, check=True):
    result = subprocess.run(args, cwd=ROOT, input=stdin, capture_output=True, text=True, timeout=90)
    if check and result.returncode:
        raise RuntimeError("Local container check command failed: "+args[0]+" "+args[1])
    return result


def active_snapshot():
    ids = {name: command(["docker", "compose", "ps", "-q", name]).stdout.strip() for name in ("app", "worker", "lab")}
    data = json.loads(command(["docker", "exec", ids["app"], "python", "-c", SNAPSHOT]).stdout) if ids["app"] else None
    return {"container_ids": ids, "data": data}


def main(output: Path, image: str):
    if output.exists():
        raise ValueError("Output already exists")
    name = "valvuln-review-check-"+secrets.token_hex(5)
    volume = name+"-data"
    before = active_snapshot()
    result = {"status": "FAIL", "image": image, "network": "none", "provider_requests": 0, "target_requests": 0,
              "active_before": before, "full_three_service_cold_start": False}
    created_container = created_volume = False
    try:
        command(["docker", "volume", "create", volume]); created_volume = True
        # Docker's fresh volume is root-owned. Initialize only this exact new volume, with no network.
        command(["docker", "run", "--rm", "--network", "none", "--user", "0:0", "--mount", f"type=volume,src={volume},dst=/data",
                 "--entrypoint", "chown", image, "10001:10001", "/data"])
        command(["docker", "run", "--detach", "--name", name, "--network", "none", "--read-only", "--cap-drop", "ALL",
                 "--security-opt", "no-new-privileges:true", "--tmpfs", "/tmp:size=32m,mode=1777",
                 "--mount", f"type=volume,src={volume},dst=/data", "--env", "VALVULN_DISPATCHER_ENABLED=false",
                 "--env", "VALVULN_DATA_DIR=/data", "--env", "VALVULN_TRIAGE_MODE=mock", "--env", "VALVULN_MIN_FREE_BYTES=0", image]); created_container = True
        def healthy():
            for _ in range(30):
                response = command(["docker", "exec", name, "python", "-c", HEALTH], check=False)
                if response.returncode == 0:
                    return json.loads(response.stdout)
                time.sleep(0.2)
            raise RuntimeError("Isolated app did not become healthy")
        result["first_health"] = healthy()
        command(["docker", "exec", "-i", name, "python", "-c", SEED], stdin=json.dumps({"password": secrets.token_urlsafe(24)}))
        initial = json.loads(command(["docker", "exec", name, "python", "-c", SNAPSHOT]).stdout)
        command(["docker", "restart", name])
        result["restart_health"] = healthy()
        final = json.loads(command(["docker", "exec", name, "python", "-c", SNAPSHOT]).stdout)
        assert initial == final
        assert initial["users"]["count"] == 3 and initial["ledger"]["count"] == initial["actions"]["count"] == 0
        result.update(status="PASS", isolated_before=initial, isolated_after=final, restart_preserved=True)
    finally:
        if created_container: command(["docker", "rm", "--force", name])
        if created_volume: command(["docker", "volume", "rm", volume])
        after = active_snapshot()
        result.update(active_after=after, active_preserved=after == before, disposable_resources_removed=True)
        if after != before: result["status"] = "FAIL"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "active_preserved": result["active_preserved"], "output": str(output)}))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--image", default="valvuln-review-app:20261107")
    a = p.parse_args()
    main(a.output, a.image)
