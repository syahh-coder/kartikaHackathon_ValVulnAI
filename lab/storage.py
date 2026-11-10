from contextlib import asynccontextmanager
from pathlib import Path

import aiosqlite




@asynccontextmanager
async def connect(path: Path):
    async with aiosqlite.connect(path, timeout=5) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA foreign_keys=ON")
        await db.execute("PRAGMA busy_timeout=5000")
        yield db


async def one(db, sql, args=()):
    async with db.execute(sql, args) as cursor:
        return await cursor.fetchone()


async def migrate(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    async with connect(path) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("CREATE TABLE IF NOT EXISTS schema_versions(version INTEGER PRIMARY KEY)")
        await db.commit()
        for migration in sorted((Path(__file__).parent/"migrations").glob("*.sql")):
            version=int(migration.name.split("_")[0])
            if not await one(db,"SELECT 1 FROM schema_versions WHERE version=?",(version,)):
                await db.executescript("BEGIN IMMEDIATE;\n"+migration.read_text(encoding="utf-8")+
                                       f"\nINSERT INTO schema_versions VALUES ({version});\nCOMMIT;")
