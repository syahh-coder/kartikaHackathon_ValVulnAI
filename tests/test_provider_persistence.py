import asyncio

import pytest

from app.common import digest
from app.providers.contracts import ProviderFailure
from app.providers.engine import ProviderSession
from app.storage.db import one
from test_provider_contract import ScriptedTransport, profile, provider_env, result_for


async def test_provider_lock_survives_session_recreation(provider_env):
    db, run_id = provider_env
    first = ScriptedTransport([None])
    await ProviderSession(db, run_id, profile("primary"), [], first, 50_000).call("first", 10)
    second = ScriptedTransport([])
    with pytest.raises(ProviderFailure, match="PROVIDER_LOCKED"):
        await ProviderSession(db, run_id, profile("different"), [], second, 50_000).call("second", 10)
    assert second.calls==[]
    third = ScriptedTransport([ProviderFailure("SERVER_ERROR", cost_idr=0)])
    restored = ProviderSession(db, run_id, profile("different"), [profile("primary")], third, 50_000)
    with pytest.raises(ProviderFailure):
        await restored.call("third", 10)
    assert third.calls==["primary"]


async def test_cancel_during_provider_wait_retains_reservation(provider_env):
    db, run_id = provider_env
    started, release = asyncio.Event(), asyncio.Event()
    class WaitingTransport:
        async def dispatch(self, p, call_id, prompt):
            started.set()
            await release.wait()
            return result_for(p, call_id)
    session = ProviderSession(db, run_id, profile("primary"), [profile("free", "FREE_TIER")], WaitingTransport(), 50_000)
    task = asyncio.create_task(session.call("synthetic", 10))
    await started.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    async with db.connect() as conn:
        assert (await one(conn, "SELECT count(*) FROM provider_attempts WHERE run_id=?", (run_id,)))[0]==1
        assert (await one(conn, "SELECT status FROM ledger WHERE provider_attempt_id IS NOT NULL"))[0]=="COST_UNKNOWN"
