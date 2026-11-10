import asyncio
import sqlite3
from pathlib import Path

from app.agent.ledger import budget_used
from app.config import Settings
from app.main import create_app
from app.providers.engine import ProviderSession
from app.providers.contracts import ProviderFailure
import pytest
from app.storage.db import Database, all_rows, one
from conftest import PASSWORD, activate, logged_client, report_for
from app.operator import seed
from test_provider_contract import ScriptedTransport, profile, provider_env
from test_text_triage import completion, finished, install, live_config, submit


async def test_upgrade_004_preserves_every_existing_table_and_ledger(provider_env, tmp_path):
    db, run_id = provider_env
    await ProviderSession(db, run_id, profile("primary"), [], ScriptedTransport([None]), 50_000).call("synthetic", 10)
    legacy_path = tmp_path / "old-schema.sqlite3"
    # Build the genuine 004 schema and populate it with the existing app records.
    # Only this disposable database is modified; the active app database is untouched.
    legacy = sqlite3.connect(legacy_path)
    legacy.execute("CREATE TABLE schema_versions(version TEXT PRIMARY KEY)")
    for path in sorted(Path("app/storage/migrations").glob("*.sql"))[:4]:
        legacy.executescript(path.read_text(encoding="utf-8"))
        legacy.execute("INSERT INTO schema_versions VALUES (?)", (path.name,))
    tables = [r[0] for r in legacy.execute("SELECT name FROM sqlite_master WHERE type='table' AND name!='schema_versions'")]
    expected = {}
    async with db.connect() as conn:
        for table in tables:
            columns = [r[1] for r in legacy.execute(f"PRAGMA table_info({table})")]
            rows = [tuple(r) for r in await all_rows(conn, f"SELECT {','.join(columns)} FROM {table}")]
            expected[table] = (columns, rows)
            if rows:
                legacy.executemany(f"INSERT INTO {table}({','.join(columns)}) VALUES ({','.join('?' for _ in columns)})", rows)
    legacy.commit()
    legacy.close()
    migrated = Database(legacy_path)
    await migrated.migrate()
    await migrated.migrate()  # Upgrade is idempotent and does not reset history.
    async with migrated.connect() as conn:
        for table, (columns, rows) in expected.items():
            actual = [tuple(r) for r in await all_rows(conn, f"SELECT {','.join(columns)} FROM {table}")]
            assert actual == rows, table
        assert not await all_rows(conn, "PRAGMA foreign_key_check")
        assert (await one(conn, "SELECT count(*) FROM text_triages"))[0] == 0
        assert await budget_used(conn) == 10


async def test_restart_preserves_triage_unknown_budget_and_never_replays(tmp_path):
    settings = Settings(_env_file=None, data_dir=tmp_path, dispatcher_enabled=False, min_free_bytes=0)
    app = create_app(settings)
    async with app.router.lifespan_context(app):
        program = await seed(app.state.db, PASSWORD)
        hunter, admin = await logged_client(app, "hunter-a"), await logged_client(app, "admin")
        await activate(admin, program)
        cid, _, _ = await report_for(hunter, program)
        app.state.text_triage.config = live_config(data_dir=tmp_path, min_free_bytes=0)
        install(app, [completion(usage=None)])
        tid = (await submit(hunter, cid)).json()["triage_id"]
        result = await finished(app, hunter, tid)
        assert result["status"] == "SUCCEEDED"
        async with app.state.db.transaction() as conn:
            before = dict(await one(conn, "SELECT * FROM ledger"))
            input_hash = (await one(conn, "SELECT input_hash FROM text_triages"))[0]
            # Simulate state left by a process that died after dispatch.
            await conn.execute("UPDATE text_triages SET status='RUNNING',output_json=NULL")
            await conn.execute("UPDATE provider_attempts SET status='DISPATCHED'")
            await conn.execute("UPDATE ledger SET status='RESERVED'")
        await hunter.aclose()
        await admin.aclose()
    app2 = create_app(settings)
    async with app2.router.lifespan_context(app2):
        assert not app2.state.text_triage.tasks
        async with app2.state.db.connect() as conn:
            row = await one(conn, "SELECT * FROM text_triages")
            assert row["status"] == "FAILED" and row["error_code"] == "PROCESS_INTERRUPTED"
            assert row["input_hash"] == input_hash
            assert dict(await one(conn, "SELECT * FROM ledger")) == before
            assert await budget_used(conn) == 500
            attempt = await one(conn, "SELECT * FROM provider_attempts")
            assert attempt["status"] == "FAILED" and attempt["error_code"] == "PROCESS_INTERRUPTED"
            assert attempt["finished_at"] is not None
            for table in ("runs", "actions", "handoff_actions"):
                assert (await one(conn, f"SELECT count(*) FROM {table}"))[0] == 0


async def test_shutdown_cancels_inflight_and_retains_unknown_cost(env):
    app, program, hunter, _, admin = env
    await activate(admin, program)
    cid, _, _ = await report_for(hunter, program)
    service = app.state.text_triage
    service.config = live_config(data_dir=app.state.config.data_dir, min_free_bytes=0)
    started = asyncio.Event()
    async def waiting(request):
        started.set()
        await asyncio.Event().wait()
    script = install(app, [waiting])
    tid = (await submit(hunter, cid)).json()["triage_id"]
    await asyncio.wait_for(started.wait(), 3)
    await service.close()
    result = (await hunter.get(f"/api/triages/{tid}")).json()
    assert result["status"] == "CANCELLED" and result["attempts"][0]["cost_status"] == "COST_UNKNOWN"
    assert len(script.requests) == 1


async def test_triage_cannot_bypass_legacy_unknown_reservations(provider_env, env):
    db, run_id = provider_env
    with pytest.raises(ProviderFailure):
        await ProviderSession(db, run_id, profile("legacy"), [],
                              ScriptedTransport([ProviderFailure("TRANSPORT_TIMEOUT")]), 50_000,
                              benchmark=True).call("synthetic", 10)
    app, _, hunter, _, _ = env
    async with db.connect() as conn:
        cid = (await one(conn, "SELECT conversation_id FROM conversations"))[0]
    app.state.text_triage.config = live_config(data_dir=app.state.config.data_dir, min_free_bytes=0, budget_idr=500)
    script = install(app, [])
    tid = (await submit(hunter, cid)).json()["triage_id"]
    result = await finished(app, hunter, tid)
    assert result["error_code"] == "BUDGET_LIMIT" and not script.requests and not result["attempts"]
    async with db.connect() as conn:
        assert await budget_used(conn) == 100
        assert (await one(conn, "SELECT count(*) FROM runs"))[0] == 1
        assert (await one(conn, "SELECT status FROM ledger WHERE provider_attempt_id IS NOT NULL"))[0] == "COST_UNKNOWN"
