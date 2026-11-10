"""Local maintenance CLI only. No GT manifest/scoring and no HTTP reset route."""
import argparse
import asyncio
import json
import os
from pathlib import Path
import uuid

from pwdlib import PasswordHash

from lab.storage import connect, migrate, one
from lab.xss_catalog import POINTS
from lab.uploads import POINTS as UPLOAD_POINTS


async def reset(path: Path, accounts: dict, condition: str, *, xss_condition: str = "fixed",
                xss_point: str | None = None, point_condition: str = "fixed",
                upload_point: str | None = None, upload_condition: str = "fixed"):
    if condition not in {"vulnerable", "fixed"} or xss_condition not in {"vulnerable", "fixed"} or set(accounts) != {"requester-a", "requester-b"}:
        raise ValueError("Invalid operator configuration")
    if (xss_point is not None and xss_point not in POINTS) or point_condition not in {"vulnerable", "fixed"}:
        raise ValueError("Invalid XSS point configuration")
    if (upload_point is not None and upload_point not in UPLOAD_POINTS) or upload_condition not in {"vulnerable", "fixed"}:
        raise ValueError("Invalid upload point configuration")
    await migrate(path)
    hashes = {alias: await asyncio.to_thread(PasswordHash.recommended().hash, data["password"]) for alias,data in accounts.items()}
    snapshot_id = str(uuid.uuid4())
    objects = {}
    async with connect(path) as db:
        await db.execute("BEGIN IMMEDIATE")
        # This reset is explicit and affects only the lab database; app ledger is unreachable.
        for table in ("business_events", "business_fulfillments", "business_requests", "business_staff", "business_items", "uploads", "upload_blobs", "comments", "request_reviewers", "request_details", "catalog_items", "suppliers", "sessions", "attachments", "requests", "users", "access_log", "settings"):
            await db.execute("DELETE FROM "+table)
        await db.executemany("INSERT INTO settings VALUES (?,?)", [("delete_owner_check", "0" if condition=="vulnerable" else "1"), ("snapshot_id", snapshot_id)])
        await db.execute("INSERT INTO settings VALUES ('notification_dom_html',?)", ("1" if xss_condition == "vulnerable" else "0",))
        await db.executemany("INSERT INTO settings VALUES (?,?)",
            [(key, "1" if point == xss_point and point_condition == "vulnerable" else "0") for point, key in POINTS.items()])
        await db.executemany("INSERT INTO settings VALUES (?,?)",
            [(key, "1" if point == upload_point and upload_condition == "vulnerable" else "0") for point, key in UPLOAD_POINTS.items()])
        for index,alias in enumerate(sorted(accounts)):
            user, request, attachment = (str(uuid.uuid4()) for _ in range(3))
            await db.execute("INSERT INTO users(id,alias,unit,password_hash,display_name) VALUES (?,?,?,?,?)",
                (user, alias, "unit-"+str(index+1), hashes[alias], "Pemohon sintetis "+str(index+1)))
            await db.execute("INSERT INTO requests VALUES (?,?,?)", (request, user, "Permintaan sintetis "+str(index+1)))
            await db.execute("INSERT INTO attachments VALUES (?,?,?,?,?,0)", (attachment,request,user,"dokumen.txt","Lampiran sintetis privat "+str(index+1)))
            item, supplier = str(uuid.uuid4()), str(uuid.uuid4())
            await db.execute("INSERT INTO catalog_items VALUES (?,?,?,?)", (item,user,"Catatan sintetis","Deskripsi sintetis"))
            await db.execute("INSERT INTO request_details VALUES (?,?)", (request,"Alasan sintetis"))
            await db.execute("INSERT INTO suppliers VALUES (?,?,?,?)", (supplier,user,"Pemasok sintetis","SUP-"+str(index+1)))
            objects[alias] = {"user_id": user, "request_id": request, "attachment_id": attachment,
                "item_id": item, "supplier_id": supplier}
        await db.execute("INSERT INTO request_reviewers VALUES (?,?)",
            (objects["requester-a"]["request_id"], objects["requester-b"]["user_id"]))
        await db.commit()
    return {"snapshot_id": snapshot_id, "objects": objects}


async def inspect(path: Path):
    async with connect(path) as db:
        snapshot = await one(db, "SELECT value FROM settings WHERE key='snapshot_id'")
        async with db.execute("SELECT a.id,a.deleted,u.alias,a.content FROM attachments a JOIN users u ON a.uploader_id=u.id ORDER BY u.alias") as cur:
            rows = await cur.fetchall()
        started = await one(db, "SELECT 1 FROM settings WHERE key='operator_browser_delay_started'")
        return {"snapshot_id": snapshot[0] if snapshot else None, "browser_delay_started": bool(started),
                "attachments": [{"id": r["id"], "owner": r["alias"], "deleted": bool(r["deleted"])} for r in rows]}


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=["reset", "inspect", "arm-delay", "arm-browser-network", "arm-browser-delay"])
    parser.add_argument("--condition", choices=["vulnerable", "fixed"])
    parser.add_argument("--xss-condition", choices=["vulnerable", "fixed"], default="fixed")
    parser.add_argument("--xss-point", choices=sorted(POINTS))
    parser.add_argument("--point-condition", choices=["vulnerable", "fixed"], default="fixed")
    parser.add_argument("--upload-point", choices=sorted(UPLOAD_POINTS))
    parser.add_argument("--upload-condition", choices=["vulnerable", "fixed"], default="fixed")
    args = parser.parse_args()
    path = Path(os.environ.get("LAB_DATA_DIR", "/data")) / "lab.sqlite3"
    if args.operation=="reset":
        if not args.condition:
            parser.error("reset needs an explicit condition")
        accounts = json.loads(Path(os.environ.get("LAB_ACCOUNTS_FILE", "/run/secrets/lab_accounts")).read_text())
        result = await reset(path, accounts, args.condition, xss_condition=args.xss_condition,
                             xss_point=args.xss_point, point_condition=args.point_condition,
                             upload_point=args.upload_point, upload_condition=args.upload_condition)
    elif args.operation=="inspect":
        result = await inspect(path)
    elif args.operation == "arm-delay":
        async with connect(path) as db:
            await db.execute("INSERT OR REPLACE INTO settings VALUES ('operator_delay_next_delete','8')")
            await db.commit()
        result={"fault_fixture":"armed","maximum_seconds":8}
    else:
        key = "operator_browser_network" if args.operation == "arm-browser-network" else "operator_browser_delay"
        async with connect(path) as db:
            await db.execute("INSERT OR REPLACE INTO settings VALUES (?, '1')", (key,))
            await db.commit()
        result = {"fault_fixture": "armed", "kind": args.operation}
    print(json.dumps(result))


if __name__=="__main__":
    asyncio.run(main())
