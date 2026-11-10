from copy import deepcopy
import json

import pytest

from scripts.m6b_persistence_probe import check, core_state


def payload(phase, expected=None):
    return {"phase": phase, "password": "synthetic-requester-password", "staff_password": "synthetic-staff-password", "expected": expected}


async def test_normal_restart_preserves_state_and_replays_stored_fulfillment(tmp_path):
    path = tmp_path/"dedicated.sqlite3"
    first = await check(payload("initialize"), path)
    second = await check(payload("restart", first), path)
    assert first["status"] == second["status"] == "PASS"
    assert first["state"] == second["state"]
    assert first["fulfillment"] == second["fulfillment"]
    assert second["state"]["stock"] == 93 and second["state"]["events"] == 4
    for secret in ("synthetic-requester-password", "synthetic-staff-password", "csrf_token", "lab_session"):
        assert secret not in json.dumps(second)


async def test_initialize_refuses_to_reset_existing_file(tmp_path):
    path = tmp_path/"kept.sqlite3"
    path.write_bytes(b"keep existing evidence")
    with pytest.raises(ValueError, match="NOT_RESET"):
        await check(payload("initialize"), path)
    assert path.read_bytes() == b"keep existing evidence"


async def test_restart_refuses_missing_database_without_creating_it(tmp_path):
    path = tmp_path/"missing.sqlite3"
    with pytest.raises(ValueError, match="MISSING"):
        await check(payload("restart", {}), path)
    assert not path.exists()


async def test_restart_detects_state_mismatch_before_mutation(tmp_path):
    path = tmp_path/"dedicated.sqlite3"
    first = await check(payload("initialize"), path)
    altered = deepcopy(first)
    altered["state"]["stock"] = 94
    with pytest.raises(ValueError, match="MISMATCH"):
        await check(payload("restart", altered), path)
    assert await core_state(path) == first["state"]
