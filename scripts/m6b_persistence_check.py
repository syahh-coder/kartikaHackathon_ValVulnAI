"""Two safe normal-workflow phases across disposable containers and one test volume.

No Compose service, project volume, operator secret, provider or worker job is
accessed. Only a newly labelled test volume is eligible for automatic cleanup.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import secrets
import subprocess
import re
from uuid import uuid4


IMAGE = "valvuln-lab:m6a-controls-check"
LABEL = "com.valvuln.check=m6b-safe-controls"


def command(args: list[str], data: bytes | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(["docker", *args], input=data, capture_output=True, timeout=60)


def cleanup(volume: str) -> str:
    if not re.fullmatch(r"valvuln-m6b-check-[a-f0-9]{32}", volume):
        return "FAIL"
    container = volume+"-container"
    try:
        active = command(["container", "inspect", container])
        if active.returncode == 0:
            info = json.loads(active.stdout)[0]
            if info["Config"].get("Labels", {}).get("com.valvuln.check") != "m6b-safe-controls":
                return "FAIL"
            if command(["container", "rm", "-f", container]).returncode:
                return "FAIL"
        inspection = command(["volume", "inspect", volume])
        if inspection.returncode != 0:
            return "FAIL"
        info = json.loads(inspection.stdout)[0]
        if info.get("Name") != volume or info.get("Labels", {}).get("com.valvuln.check") != "m6b-safe-controls":
            return "FAIL"
        return "PASS" if command(["volume", "rm", volume]).returncode == 0 else "FAIL"
    except (OSError, ValueError, KeyError, TypeError, IndexError, subprocess.SubprocessError):
        return "FAIL"


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    source = (root/"scripts/m6b_persistence_probe.py").read_text(encoding="utf-8")
    volume = "valvuln-m6b-check-"+uuid4().hex
    container = volume+"-container"
    report = {"status": "RUNNING", "mode": "safe ASGI; independent containers; dedicated persisted test volume",
              "volume": volume, "image": IMAGE, "network": "none", "phases": [], "cleanup": "PENDING"}
    directory = root/"artifacts/m6b"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory/(datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")+"-persistence.json")

    def save():
        path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    created = False
    try:
        image = command(["image", "inspect", IMAGE, "--format", "{{.Id}}"])
        if image.returncode:
            raise ValueError("CHECK_IMAGE_REQUIRED")
        report["image_id"] = image.stdout.decode().strip()
        result = command(["volume", "create", "--label", LABEL, volume])
        if result.returncode or result.stdout.decode().strip() != volume:
            raise ValueError("TEST_VOLUME_NOT_CREATED")
        created = True
        password, staff_password = secrets.token_urlsafe(24), secrets.token_urlsafe(24)
        previous = None
        for phase in ("initialize", "restart"):
            payload = {"phase": phase, "password": password, "staff_password": staff_password, "expected": previous}
            args = ["run", "--rm", "-i", "--name", container, "--label", LABEL, "--network", "none", "--read-only",
                    "--tmpfs", "/tmp:rw,size=64m,mode=1777", "--mount", f"type=volume,src={volume},dst=/data",
                    "--user", "10001:10001", "--cap-drop", "ALL", "--security-opt", "no-new-privileges:true",
                    "--memory", "256m", "--pids-limit", "64", "--entrypoint", "python", IMAGE, "-c", source]
            completed = command(args, json.dumps(payload).encode())
            try:
                observed = json.loads(completed.stdout)
            except ValueError:
                observed = {"status": "FAIL", "error_type": "INVALID_PROBE_OUTPUT"}
            report["phases"].append({"exit_code": completed.returncode, "result": observed})
            save()
            if completed.returncode or observed.get("status") != "PASS" or observed.get("uid") != 10001:
                raise ValueError("PERSISTENCE_PHASE_FAILED")
            if not all(hashlib.sha256((root/name).read_bytes()).hexdigest() == h for name, h in observed["source_sha256"].items()):
                raise ValueError("IMAGE_SOURCE_MISMATCH")
            previous = observed
        report["status"] = "PASS"
    except Exception as error:
        report.update(status="FAIL", error_type=type(error).__name__)
    finally:
        if created:
            # Cleanup identity comes from this invocation, never a record or CLI input.
            report["cleanup"] = cleanup(volume)
            if report["cleanup"] != "PASS":
                report["status"] = "FAIL"
        else:
            report["cleanup"] = "NOT_CREATED"
        report["checked_at_utc"] = datetime.now(timezone.utc).isoformat()
        report["probe_sha256"] = hashlib.sha256(source.encode()).hexdigest()
        save()
    print(json.dumps({"artifact": str(path.relative_to(root)), **report}, indent=2))
    raise SystemExit(report["status"] != "PASS")


if __name__ == "__main__":
    main()
