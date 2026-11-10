import json

import pytest

from app.common import packed, uid
from app.storage.db import all_rows, one
from scripts.r2_qa_fixtures import attach_observation
from conftest import activate, report_for


@pytest.fixture
async def records(env):
    app, program, hunter, other, admin = env
    scope = await activate(admin, program)
    cid, report, rev = await report_for(hunter, program)
    response = await hunter.post(f"/api/reports/{report}/runs", json={"report_revision_id": rev}, headers={"Idempotency-Key": uid()})
    assert response.status_code == 202, response.text
    run = response.json()["run_id"]
    yield app, program, hunter, other, admin, cid, report, rev, run, scope


async def snapshot(db):
    async with db.connect() as conn:
        return {t: [tuple(r) for r in await all_rows(conn, f"SELECT * FROM {t}")] for t in
                ("runs", "actions", "handoff_actions", "evidence", "assessments", "ledger", "provider_attempts")}


@pytest.mark.parametrize("kind", ["HTTP_EXCHANGE", "BROWSER_PROBE", "UPLOAD_EXCHANGE"])
async def test_admin_summary_allowlist_binding_and_no_mutation(records, kind):
    app, _, a, b, admin, _, _, rev, run, scope = records
    item = await attach_observation(app, run, kind)
    before = await snapshot(app.state.db)
    response = await admin.get(f"/api/runs/{run}/observations-summary")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["status"] == "AVAILABLE" and data["verdict"] is None and data["is_current"]
    assert data["binding"]["report_revision_id"] == rev and data["binding"]["scope_version_id"] == scope
    fact = data["observations"][0]
    assert fact["evidence_id"] == item["evidence_id"] and fact["http_status"] == 200
    for hidden in ("INTERNAL_NOTE", "PRIVATE_MODEL", "PRIVATE_DOM", "PRIVATE_EVALUATOR_LABEL", "secret-only-fixture", "PRIVATE_SUMMARY", "requester-a", "body", "arguments_json"):
        assert hidden not in response.text
    assert not data["target_execution_allowed"] and not data["model_dispatch_allowed"]
    assert (await b.get(f"/api/runs/{run}/observations-summary")).status_code == 404
    owner = (await a.get(f"/api/runs/{run}/observations-summary")).json()
    assert owner["status"] == "AWAITING_PUBLICATION" and owner["observations"] == []
    assert item["evidence_id"] not in packed(owner)
    assert await snapshot(app.state.db) == before


@pytest.mark.parametrize("field", ["scope", "snapshot", "artifact", "file", "provenance", "journal"])
async def test_wrong_evidence_binding_fails_closed(records, field):
    app, _, _, _, admin, _, _, _, run, _ = records
    item = await attach_observation(app, run)
    async with app.state.db.transaction() as conn:
        if field == "scope":
            # Envelope is immutable; mismatch the run epoch rather than bypassing its trigger.
            await conn.execute("UPDATE runs SET authorization_epoch=authorization_epoch+1 WHERE run_id=?", (run,))
        elif field == "snapshot":
            await conn.execute("UPDATE runs SET target_snapshot_id=? WHERE run_id=?", (uid(), run))
        elif field == "artifact":
            await conn.execute("UPDATE evidence SET artifact_path=?", (f"evidence/{uid()}/{item['evidence_id']}.json",))
        elif field == "provenance":
            await conn.execute("UPDATE evidence SET provenance_json='{}'")
        elif field == "journal":
            await conn.execute("UPDATE handoff_actions SET observation_json='{}'")
    if field == "file":
        item["path"].write_text('{"changed":true}', encoding="utf-8")
    response = await admin.get(f"/api/runs/{run}/observations-summary")
    assert response.status_code == 409 and response.json()["error_code"] == "EVIDENCE_BINDING_INVALID"
    assert "secret-only-fixture" not in response.text


async def test_publication_review_withdrawal_and_stale_snapshot(records):
    app, program, a, _, admin, cid, _, _, run, _ = records
    item = await attach_observation(app, run)
    await admin.post(f"/api/runs/{run}/review", json={"reviewer_note": "INTERNAL_NOTE_NEW"})
    await admin.post(f"/api/runs/{run}/publish")
    owner = (await a.get(f"/api/runs/{run}/observations-summary")).json()
    assert owner["status"] == "PUBLISHED" and owner["observations"] == []
    assert owner["summary"] == (await a.get(f"/api/runs/{run}")).json()["assessment"]["summary"]
    for hidden in (item["evidence_id"], "INTERNAL_NOTE_NEW", "PRIVATE_MODEL", "secret-only-fixture"):
        assert hidden not in packed(owner)
    await a.post(f"/api/conversations/{cid}/messages", json={"body": "Perubahan draf", "expected_draft_version": 1})
    stale = (await admin.get(f"/api/runs/{run}/observations-summary")).json()
    assert not stale["is_current"] and stale["status"] == "AVAILABLE"
    await activate(admin, program)
    assert not (await admin.get(f"/api/runs/{run}/observations-summary")).json()["is_current"]
    await admin.post(f"/api/runs/{run}/review", json={"reviewer_note": "Review ulang"})
    assert (await a.get(f"/api/runs/{run}/observations-summary")).json()["status"] == "AWAITING_PUBLICATION"


async def test_absent_and_simulation_records_do_not_fabricate_evidence(records):
    app, _, _, _, admin, _, _, _, run, _ = records
    assert (await admin.get(f"/api/runs/{run}/observations-summary")).json()["status"] == "NO_TARGET_EVIDENCE"
    async with app.state.db.transaction() as conn:
        await conn.execute("UPDATE runs SET tool_execution_mode='LAB' WHERE run_id=?", (run,))
    before = await snapshot(app.state.db)
    result = (await admin.get(f"/api/runs/{run}/observations-summary")).json()
    assert result["status"] == "NO_EVIDENCE" and result["observations"] == []
    assert await snapshot(app.state.db) == before


async def test_triage_discovery_reload_and_draft_staleness(env):
    app, program, a, b, admin = env
    await activate(admin, program)
    cid, _, _ = await report_for(a, program)
    before = await snapshot(app.state.db)
    response = await a.post(f"/api/conversations/{cid}/triages", json={"expected_draft_version": 1}, headers={"Idempotency-Key": uid()})
    tid = response.json()["triage_id"]
    task = app.state.text_triage.tasks.get(tid)
    if task:
        await task
    assert (await a.get(f"/api/conversations/{cid}")).json()["latest_triage_id"] == tid
    assert (await b.get(f"/api/conversations/{cid}")).status_code == 404
    assert (await admin.get(f"/api/triages/{tid}")).json()["mode"] == "mock"
    await a.post(f"/api/conversations/{cid}/messages", json={"body": "Tambahan", "expected_draft_version": 1})
    assert not (await a.get(f"/api/triages/{tid}")).json()["is_current"]
    after = await snapshot(app.state.db)
    for table in ("runs", "actions", "handoff_actions", "evidence", "assessments"):
        assert after[table] == before[table]
