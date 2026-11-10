import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from collections.abc import AsyncIterator

import aiosqlite


class Database:
    def __init__(self, path: Path):
        self.path = path
        self.write_lock = asyncio.Lock()

    @asynccontextmanager
    async def connect(self) -> AsyncIterator[aiosqlite.Connection]:
        async with aiosqlite.connect(self.path, timeout=5) as conn:
            conn.row_factory = aiosqlite.Row
            await conn.execute("PRAGMA foreign_keys=ON")
            await conn.execute("PRAGMA busy_timeout=5000")
            yield conn

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[aiosqlite.Connection]:
        async with self.write_lock:
            async with self.connect() as conn:
                await conn.execute("BEGIN IMMEDIATE")
                try:
                    yield conn
                    await conn.commit()
                except BaseException:
                    await conn.rollback()
                    raise

    async def migrate(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        async with self.connect() as conn:
            await conn.execute("PRAGMA journal_mode=WAL")
            await conn.execute("CREATE TABLE IF NOT EXISTS schema_versions(version TEXT PRIMARY KEY)")
            await conn.commit()
            for path in sorted((Path(__file__).parent / "migrations").glob("*.sql")):
                exists = await one(conn, "SELECT 1 FROM schema_versions WHERE version=?", (path.name,))
                if not exists:
                    # Only repository-owned SQL is executed here; never report content.
                    sql = path.read_text(encoding="utf-8")
                    await conn.executescript(
                        "BEGIN IMMEDIATE;\n" + sql +
                        f"\nINSERT INTO schema_versions VALUES ('{path.name}');\nCOMMIT;"
                    )


async def one(conn: aiosqlite.Connection, sql: str, params: tuple = ()) -> aiosqlite.Row | None:
    async with conn.execute(sql, params) as cursor:
        return await cursor.fetchone()


async def all_rows(conn: aiosqlite.Connection, sql: str, params: tuple = ()) -> list[aiosqlite.Row]:
    async with conn.execute(sql, params) as cursor:
        return await cursor.fetchall()
