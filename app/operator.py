"""Operator-only seed, never imported as an API route or a model tool."""
import asyncio
import getpass
import os

from app.auth import passwords
from app.common import packed, uid
from app.config import Settings
from app.policy.targets import INITIAL_PROFILE
from app.storage.db import Database, one


async def seed(db: Database, password: str):
    if not 12 <= len(password) <= 128:
        raise ValueError("Demo password must contain 12-128 characters")
    await db.migrate()
    hashed = await asyncio.to_thread(passwords.hash, password)
    async with db.transaction() as conn:
        program = await one(conn, "SELECT program_id FROM programs LIMIT 1")
        program_id = program[0] if program else uid()
        if not program:
            await conn.execute("INSERT INTO programs(program_id,display_name) VALUES (?,?)",
                               (program_id, "Portal Pengadaan Lab"))
        for name, role in [("hunter-a", "BUG_HUNTER"), ("hunter-b", "BUG_HUNTER"), ("admin", "PROGRAM_ADMIN")]:
            user = await one(conn, "SELECT user_id FROM users WHERE login_name=?", (name,))
            user_id = user[0] if user else uid()
            if not user:
                await conn.execute("INSERT INTO users VALUES (?,?,?,1)", (user_id, name, hashed))
            await conn.execute("INSERT OR IGNORE INTO memberships VALUES (?,?,?,1)", (user_id, program_id, role))
        await conn.execute("INSERT OR IGNORE INTO target_bindings(target_id,program_id,asset_alias,fixed_origin,profile_json,ready,dirty) VALUES (?,?,?,?,?,0,0)",
                           ("portal-lab", program_id, "portal", "http://lab:8001", packed(INITIAL_PROFILE)))
    return program_id


async def main():
    # Do not log the credential. For automation the operator may supply this env variable.
    password = os.environ.get("VALVULN_SEED_PASSWORD") or getpass.getpass("Kata sandi demo lokal (12-128 karakter): ")
    settings = Settings()
    program_id = await seed(Database(settings.db_path), password)
    print(f"Seed selesai: program {program_id}; akun hunter-a, hunter-b, admin. Scope tetap belum aktif.")


if __name__ == "__main__":
    asyncio.run(main())
