"""Explicit operator setup of safe synthetic business controls, never startup.

Run only during evaluator maintenance with no active jobs. Release a new verified
snapshot separately afterwards. Does not reset existing records or grant worker access.
"""
import argparse
import asyncio
from getpass import getpass
import json
from pathlib import Path
from uuid import uuid4

import aiosqlite
from pwdlib import PasswordHash

from lab.storage import connect, migrate, one


async def provision(path: Path, password: str) -> dict:
    if not 12 <= len(password) <= 128:
        raise ValueError("Password must contain 12–128 characters")
    if not path.is_file():
        raise ValueError("Existing operator-seeded lab required")
    # Validate identity read-only before migration; an app database must not acquire
    # lab tables if the operator supplies the wrong path.
    async with aiosqlite.connect(path.resolve().as_uri()+"?mode=ro", uri=True) as db:
        columns = {row[1] for row in await db.execute_fetchall("PRAGMA table_info(users)")}
        if not {"id", "alias", "unit", "password_hash"} <= columns:
            raise ValueError("Expected lab database, not an application database")
        try:
            seeded = await db.execute_fetchall("SELECT value FROM settings WHERE key='snapshot_id'")
        except aiosqlite.OperationalError:
            raise ValueError("Existing operator-seeded lab required") from None
        if not seeded:
            raise ValueError("Existing operator-seeded lab required")
    await migrate(path)
    password_hash = await asyncio.to_thread(PasswordHash.recommended().hash, password)
    async with connect(path) as db:
        await db.execute("BEGIN IMMEDIATE")
        owner = await one(db, "SELECT id,unit FROM users WHERE alias='requester-a'")
        snapshot = await one(db, "SELECT value FROM settings WHERE key='snapshot_id'")
        if not owner or not snapshot:
            raise ValueError("Existing operator-seeded lab required")
        existing = await one(db, "SELECT u.id,u.unit,s.unit staff_unit FROM users u LEFT JOIN business_staff s ON s.user_id=u.id WHERE u.alias='approver_a'")
        if existing:
            if existing["unit"] != owner["unit"] or existing["staff_unit"] != owner["unit"]:
                raise ValueError("Operator account conflict; no permission/password changes made")
            item = await one(db, "SELECT id FROM business_items ORDER BY id LIMIT 1")
            if not item:
                raise ValueError("Incomplete setup; manual inspection required")
            return {"changed": False, "snapshot_id": snapshot[0], "item_id": item[0], "staff_alias": "approver_a"}
        if (await one(db, "SELECT count(*) FROM business_items"))[0]:
            raise ValueError("Existing business data; manual inspection required")
        uid, item_id, snapshot_id = (str(uuid4()) for _ in range(3))
        await db.execute("INSERT INTO users(id,alias,unit,password_hash,display_name) VALUES (?,?,?,?,?)",
                         (uid, "approver_a", owner["unit"], password_hash, "Petugas sintetis unit A"))
        await db.execute("INSERT INTO business_staff VALUES (?,?)", (uid, owner["unit"]))
        await db.execute("INSERT INTO business_items VALUES (?,?,?)", (item_id, "Barang sintetis", 100))
        await db.execute("UPDATE settings SET value=? WHERE key='snapshot_id'", (snapshot_id,))
        await db.commit()
    return {"changed": True, "snapshot_id": snapshot_id, "item_id": item_id, "staff_alias": "approver_a"}


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True, help="Explicit lab SQLite path, not the app database")
    args = parser.parse_args()
    result = await provision(args.database, getpass("Kata sandi petugas sintetis (12–128 karakter): "))
    print(json.dumps(result))


if __name__ == "__main__":
    asyncio.run(main())
