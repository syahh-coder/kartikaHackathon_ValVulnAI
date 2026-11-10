"""Safe ASGI persistence probe for a dedicated test database, never a worker tool."""
from contextlib import AsyncExitStack
import asyncio
import hashlib
import json
import os
from pathlib import Path
import sys

from httpx import ASGITransport, AsyncClient

from lab.business_setup import provision
from lab.main import create_app
from lab.maintenance import reset
from lab.storage import connect, one


async def core_state(path: Path) -> dict:
    async with connect(path) as db:
        async with db.execute("SELECT request_id,quantity,state,version FROM business_requests ORDER BY request_id") as cursor:
            requests = [dict(row) for row in await cursor.fetchall()]
        return {"snapshot_id": (await one(db, "SELECT value FROM settings WHERE key='snapshot_id'"))[0],
                "stock": (await one(db, "SELECT stock FROM business_items"))[0], "requests": requests,
                "events": (await one(db, "SELECT count(*) FROM business_events"))[0],
                "fulfillments": (await one(db, "SELECT count(*) FROM business_fulfillments"))[0],
                "schema_version": (await one(db, "SELECT max(version) FROM schema_versions"))[0]}


async def check(payload: dict, path: Path) -> dict:
    phase = payload["phase"]
    if phase not in {"initialize", "restart"}:
        raise ValueError("PHASE_DENIED")
    if phase == "initialize":
        if path.exists():
            raise ValueError("EXISTING_DATABASE_NOT_RESET")
        accounts = {name: {"password": payload["password"]} for name in ("requester-a", "requester-b")}
        await reset(path, accounts, "fixed")
        setup = await provision(path, payload["staff_password"])
    else:
        if not path.is_file():
            raise ValueError("PERSISTED_DATABASE_MISSING")
        before = await core_state(path)
        if before != payload["expected"]["state"]:
            raise ValueError("PERSISTED_STATE_MISMATCH")
    app = create_app(path)
    async with app.router.lifespan_context(app):
        if phase == "restart" and await core_state(path) != before:
            raise ValueError("STARTUP_CHANGED_BUSINESS_DATA")
        async with AsyncExitStack() as stack:
            clients = []
            for alias, password in (("requester-a", payload["password"]), ("approver_a", payload["staff_password"])):
                client = await stack.enter_async_context(AsyncClient(transport=ASGITransport(app=app), base_url="http://lab:8001", headers={"Origin": "http://lab:8001"}))
                response = await client.post("/api/auth/login", json={"login_name": alias, "password": password})
                if response.status_code != 200:
                    raise ValueError("PERSISTED_LOGIN_FAILED")
                client.headers["X-CSRF-Token"] = response.json()["csrf_token"]
                clients.append(client)
            owner, staff = clients
            if phase == "initialize":
                response = await owner.post("/api/requests", json={"title": "Kontrol persistensi sintetis", "item_id": setup["item_id"], "quantity": 7})
                if response.status_code != 201:
                    raise ValueError("CREATE_FAILED")
                row = response.json()
                rid = row["request_id"]
                route = f"/api/requests/{rid}"
                for client, operation in ((owner, "submit"), (staff, "approve")):
                    response = await client.post(route+"/"+operation, json={"expected_version": row["version"]})
                    if response.status_code != 200:
                        raise ValueError("NORMAL_TRANSITION_FAILED")
                    row = response.json()
                expected_version = row["version"]
            else:
                rid = payload["expected"]["request_id"]
                route = f"/api/requests/{rid}"
                expected_version = payload["expected"]["expected_version"]
            fulfilled = await staff.post(route+"/fulfill", json={"expected_version": expected_version})
            if fulfilled.status_code != 200:
                raise ValueError("FULFILLMENT_FAILED")
            state = await core_state(path)
            if state["stock"] != 93 or state["events"] != 4 or state["fulfillments"] != 1:
                raise ValueError("BUSINESS_STATE_FAILED")
            if phase == "restart" and (state != before or fulfilled.json() != payload["expected"]["fulfillment"]):
                raise ValueError("RESTART_REPLAY_CHANGED_STATE")
    return {"status": "PASS", "phase": phase, "request_id": rid, "expected_version": expected_version,
            "fulfillment": fulfilled.json(), "state": state}


def main() -> None:
    try:
        payload = json.load(sys.stdin)
        result = asyncio.run(check(payload, Path("/data/m6b-controls.sqlite3")))
        result["uid"] = os.getuid()
        names = ["lab/business.py", "lab/business_setup.py", "lab/main.py", "lab/maintenance.py", "lab/storage.py", "lab/migrations/004_business_controls.sql"]
        result["source_sha256"] = {name: hashlib.sha256(Path(name).read_bytes()).hexdigest() for name in names}
    except Exception as error:
        result = {"status": "FAIL", "error_type": type(error).__name__}
    print(json.dumps(result))
    raise SystemExit(result["status"] != "PASS")


if __name__ == "__main__":
    main()
