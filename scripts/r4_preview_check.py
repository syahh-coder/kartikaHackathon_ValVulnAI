"""Exercise the packaged app-only MOCK Compose on an isolated project; preserve the active project."""
import argparse
import json
import secrets
import socket
import subprocess
import time
from pathlib import Path

import httpx

from scripts.r4_container_check import ROOT, active_snapshot


def main(output):
    if output.exists(): raise ValueError("Output exists")
    project = "valvuln-review-check-"+secrets.token_hex(5)
    base = ["docker", "compose", "-p", project, "-f", "compose.preview.yaml"]
    def call(args, stdin=None):
        p = subprocess.run(base+args, cwd=ROOT, text=True, input=stdin, capture_output=True, timeout=120)
        if p.returncode: raise RuntimeError("Disposable Compose command failed: "+args[0])
        return p.stdout
    assert not call(["ps", "-q"]).strip()
    # Check the exact preview port before creating anything; never displace another listener.
    with socket.socket() as s: s.bind(("127.0.0.1", 8010))
    before = active_snapshot()
    result = {"status":"FAIL","active_before":before,"project":project,"provider_requests":0,"target_requests":0}
    try:
        call(["up", "-d", "--build"])
        with httpx.Client(base_url="http://127.0.0.1:8010",trust_env=False,timeout=2) as c:
            for _ in range(60):
                try:
                    r=c.get("/api/health")
                    if r.status_code==200: break
                except httpx.TransportError: pass
                time.sleep(0.2)
            else: raise RuntimeError("Disposable preview did not become healthy")
            ready=c.get("/api/readiness").json()
            assert ready["triage_mode"]=="mock" and ready["lab_planner_mode"]=="mock"
            result.update(status="PASS",health=r.json(),triage_mode=ready["triage_mode"],port=8010)
    finally:
        # Only the randomly named, previously absent test project and its freshly created volume.
        call(["down", "--volumes"])
        after=active_snapshot()
        result.update(active_after=after,active_preserved=before==after,disposable_resources_removed=True)
        if before!=after: result["status"]="FAIL"
        output.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":result["status"],"active_preserved":result["active_preserved"],"output":str(output)}))


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--output",type=Path,required=True)
    main(p.parse_args().output)
