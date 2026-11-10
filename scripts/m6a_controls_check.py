"""Safe business workflow check using a disposable SQLite database and ASGI.

Does not connect to running services, read operator secrets, reset an existing
lab, invoke a provider or start a validation job. No network transport is used.
"""
import argparse
import asyncio
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import secrets
from tempfile import TemporaryDirectory

from httpx import ASGITransport, AsyncClient

from lab.business import RULES_VERSION
from lab.business_setup import provision
from lab.main import create_app
from lab.maintenance import reset


async def check() -> dict:
    report = {"status": "RUNNING", "mode": "safe controls; disposable SQLite; ASGI only",
              "rules_version": RULES_VERSION, "checks": []}
    try:
        with TemporaryDirectory(prefix="valvuln-m6a-") as directory:
            path = Path(directory) / "lab.sqlite3"
            password, staff_password = secrets.token_urlsafe(24), secrets.token_urlsafe(24)
            await reset(path, {name: {"password": password} for name in ("requester-a", "requester-b")}, "fixed")
            setup = await provision(path, staff_password)
            app = create_app(path)
            async with app.router.lifespan_context(app):
                async with AsyncClient(transport=ASGITransport(app=app), base_url="http://lab:8001", headers={"Origin": "http://lab:8001"}) as owner, \
                           AsyncClient(transport=ASGITransport(app=app), base_url="http://lab:8001", headers={"Origin": "http://lab:8001"}) as staff:
                    for client, alias, secret in ((owner, "requester-a", password), (staff, "approver_a", staff_password)):
                        login = await client.post("/api/auth/login", json={"login_name": alias, "password": secret})
                        if login.status_code != 200:
                            raise ValueError("LOGIN_FAILED")
                        client.headers["X-CSRF-Token"] = login.json()["csrf_token"]
                    rules = await owner.get("/api/business-rules")
                    if rules.status_code != 200 or rules.json()["version"] != RULES_VERSION:
                        raise ValueError("RULES_FAILED")
                    report["checks"].append("public business rules")
                    created = await owner.post("/api/requests", json={"title": "Permintaan sintetis M6a", "item_id": setup["item_id"], "quantity": 7})
                    if created.status_code != 201:
                        raise ValueError("CREATE_FAILED")
                    row = created.json()
                    route = f"/api/requests/{row['request_id']}"
                    report["before"] = {k: row[k] for k in ("state", "quantity", "stock", "version")}
                    for client, operation, expected in ((owner, "submit", "SUBMITTED"), (staff, "approve", "APPROVED")):
                        response = await client.post(route+"/"+operation, json={"expected_version": row["version"]})
                        if response.status_code != 200 or response.json()["state"] != expected:
                            raise ValueError("NORMAL_TRANSITION_FAILED")
                        row = response.json()
                    body = {"expected_version": row["version"]}
                    first, second = await staff.post(route+"/fulfill", json=body), await staff.post(route+"/fulfill", json=body)
                    if first.status_code != 200 or second.status_code != 200 or first.json() != second.json():
                        raise ValueError("IDEMPOTENT_FULFILLMENT_FAILED")
                    final = (await owner.get(route)).json()
                    report["after"] = {k: final[k] for k in ("state", "quantity", "stock", "version")}
                    if report["after"] != {"state": "FULFILLED", "quantity": 7, "stock": 93, "version": 4}:
                        raise ValueError("FINAL_STATE_FAILED")
                    if [e["operation"] for e in final["events"]] != ["CREATE", "SUBMIT", "APPROVE", "FULFILL"]:
                        raise ValueError("JOURNAL_FAILED")
                    report["checks"] += ["normal state transitions", "single fulfillment on sequential replay", "stock and before/after journal"]
        report["status"] = "PASS"
    except Exception as error:
        report.update(status="FAIL", error_type=type(error).__name__)
        # Omit exception text: HTTP/library errors could include request material.
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stdout-only", action="store_true")
    args = parser.parse_args()
    report = asyncio.run(check())
    report["checked_at_utc"] = datetime.now(timezone.utc).isoformat()
    root = Path.cwd()
    names = ["lab/business.py", "lab/business_setup.py", "lab/main.py", "lab/maintenance.py", "lab/storage.py",
             "lab/migrations/004_business_controls.sql"]
    report["source_sha256"] = {name: hashlib.sha256((root/name).read_bytes()).hexdigest() for name in names}
    if not args.stdout_only:
        directory = root / "artifacts/m6a"
        directory.mkdir(parents=True, exist_ok=True)
        output = directory / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")+"-controls.json")
        output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    raise SystemExit(report["status"] != "PASS")


if __name__ == "__main__":
    main()
