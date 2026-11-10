"""Check a clean extraction using existing host dependencies, two real HTTP process lifecycles, no tools/model."""
import argparse
import hashlib
import json
import os
import secrets
import site
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from zipfile import ZipFile

import httpx


def snapshot(db):
    with sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True) as c:
        result = {}
        for table in ("users", "conversations", "messages", "reports", "runs", "actions", "evidence", "ledger", "provider_attempts", "text_triages", "evaluation_jobs"):
            rows = sorted(c.execute("SELECT * FROM "+table).fetchall(), key=repr)
            result[table] = {"count": len(rows), "sha256": hashlib.sha256(json.dumps(rows).encode()).hexdigest()}
        return result


def check(archive: Path, output: Path):
    if output.exists(): raise ValueError("Output exists")
    result = {"status": "FAIL", "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
              "dependency_install_from_scratch": False, "provider_requests": 0, "target_requests": 0,
              "full_three_service_cold_start": False}
    with tempfile.TemporaryDirectory(prefix="valvuln-clean-source-", ignore_cleanup_errors=True) as temporary:
        extraction = Path(temporary).resolve()
        assert extraction.is_relative_to(Path(tempfile.gettempdir()).resolve())
        with ZipFile(archive) as z:
            if len(z.infolist()) > 2000 or sum(f.file_size for f in z.infolist()) > 150*1024**2:
                raise ValueError("Archive limit")
            for name in z.namelist():
                if not (extraction/name).resolve().is_relative_to(extraction): raise ValueError("Unsafe archive path")
            manifest = json.loads(z.read("valvuln-ai/PACKAGE-MANIFEST.json"))
            for name, value in manifest["files"].items():
                assert hashlib.sha256(z.read("valvuln-ai/"+name)).hexdigest() == value["sha256"]
            z.extractall(extraction)
        root = extraction/"valvuln-ai"
        env = {k:v for k,v in os.environ.items() if not k.startswith("VALVULN_") and k != "PYTHONPATH"}
        data = extraction/"disposable-data"
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]
        origin = f"http://127.0.0.1:{port}"
        env.update(VALVULN_DATA_DIR=str(data), VALVULN_PUBLIC_ORIGIN=origin, VALVULN_DISPATCHER_ENABLED="false",
                   VALVULN_TRIAGE_MODE="mock", VALVULN_MIN_FREE_BYTES="0")
        # Windows venv python.exe is a redirector: terminating it may leave the actual server alive.
        # Launch the real interpreter with the same installed dependencies, so Popen owns the server PID.
        server_python = getattr(sys, "_base_executable", sys.executable)
        env["PYTHONPATH"] = os.pathsep.join(site.getsitepackages())
        password = secrets.token_urlsafe(24)
        setup = "import asyncio,json,sys;from app.config import Settings;from app.storage.db import Database;from app.operator import seed;asyncio.run(seed(Database(Settings().db_path),json.loads(sys.stdin.read())['password']))"
        subprocess.run([sys.executable, "-c", setup], cwd=root, env=env, input=json.dumps({"password":password}), text=True, capture_output=True, check=True, timeout=30)
        origin_check = subprocess.run([sys.executable,"-c","import app,evaluator;print(app.__file__);print(evaluator.__file__)"],cwd=root,env=env,text=True,capture_output=True,check=True)
        assert all(Path(line).resolve().is_relative_to(root.resolve()) for line in origin_check.stdout.splitlines())
        result["imports_from_extracted_source"] = True
        with httpx.Client(base_url=origin, trust_env=False, headers={"Origin":origin}, timeout=4) as client:
            processes = []
            try:
                def start():
                    p = subprocess.Popen([server_python,"-m","uvicorn","app.main:create_app","--factory","--host","127.0.0.1","--port",str(port),"--no-access-log"],cwd=root,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
                    processes.append(p)
                    for _ in range(100):
                        if p.poll() is not None: raise RuntimeError("Extracted app exited")
                        try:
                            response = client.get("/api/health")
                            if response.status_code == 200: return response.json()
                        except httpx.TransportError: pass
                        time.sleep(0.1)
                    raise RuntimeError("Extracted app timeout")
                first = start()
                csrf = client.get("/api/auth/csrf").json()["csrf_token"]
                login = client.post("/api/auth/login", json={"login_name":"hunter-a","password":password}, headers={"X-CSRF-Token":csrf})
                assert login.status_code == 200
                client.headers["X-CSRF-Token"] = login.json()["csrf_token"]
                program = client.get("/api/programs").json()[0]["program_id"]
                conversation = client.post(f"/api/programs/{program}/conversations").json()["conversation_id"]
                saved = client.post(f"/api/conversations/{conversation}/messages",json={"body":"Clean archive synthetic draft, no validation requested.","expected_draft_version":0})
                assert saved.status_code == 201
                before = snapshot(data/"valvuln.sqlite3")
                processes[-1].terminate(); processes[-1].wait(timeout=15)
                second = start()
                restored = client.get(f"/api/conversations/{conversation}")
                assert restored.status_code == 200 and restored.json()["draft_version"] == 1
                after = snapshot(data/"valvuln.sqlite3")
                assert before == after
                assert all(after[t]["count"] == 0 for t in ("runs","actions","evidence","ledger","provider_attempts","text_triages","evaluation_jobs"))
                result.update(status="PASS", first_health=first, restart_health=second, stored_draft_restored=True,
                              before=before, after=after, lifecycles=2, server_bound_to="127.0.0.1")
            finally:
                for p in processes:
                    if p.poll() is None: p.terminate(); p.wait(timeout=15)
    result["disposable_directory_removed"] = True
    output.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":result["status"],"output":str(output),"dependency_install_from_scratch":False}))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("archive",type=Path);p.add_argument("--output",type=Path,required=True)
    a = p.parse_args();check(a.archive.resolve(),a.output)
