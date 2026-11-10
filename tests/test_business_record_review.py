"""Product review tests using synthetic uploaded records; no target transport."""
from copy import deepcopy
import hashlib
import json

import pytest

from app.storage.db import all_rows, one
from conftest import SCOPE, activate, report_for
from test_business_trace_audit import record


RULES = {**SCOPE, "business_rules_version": "procurement-controls-v1",
         "business_rules": "DRAFT -> SUBMITTED -> APPROVED -> FULFILLED. Kuantitas 1-1000, stok tidak negatif, satu pemenuhan."}
CLAIM = {"category": "BUSINESS_LOGIC", "asset_alias": "portal", "path": "/api/requests/recorded",
         "method": "POST", "primary_claim": "Pemenuhan harus mengikuti persetujuan dan bersifat idempotent", "account_aliases": []}


async def setup(env, scope=RULES, claim=None):
    app, program, hunter, other, admin = env
    await activate(admin, program, scope)
    conversation, report_id, revision = await report_for(hunter, program, claim or CLAIM)
    return conversation, report_id, revision


async def upload(admin, report_id, revision, value=None, raw=None, **kwargs):
    raw = raw if raw is not None else json.dumps(value if value is not None else record()).encode()
    return await admin.post(f"/api/reports/{report_id}/revisions/{revision}/business-records",
                            files={"file": ("untrusted-name.json", raw, "application/json")}, **kwargs)


async def counts(app):
    async with app.state.db.connect() as conn:
        return {table: (await one(conn, f"SELECT count(*) FROM {table}"))[0]
                for table in ("business_record_reviews", "runs", "actions", "evidence", "ledger", "provider_attempts")}


async def test_report_import_review_publish_withdraw_and_private_original(env):
    app, program, hunter, other, admin = env
    cid, rid, revision = await setup(env)
    conversation = (await admin.get(f"/api/conversations/{cid}")).json()
    assert conversation["latest_report_revision_id"] == revision
    raw = json.dumps(record(), indent=2).encode()
    response = await upload(admin, rid, revision, raw=raw)
    assert response.status_code == 201, response.text
    row = response.json()
    review_id = row["review_id"]
    assert row["result"]["status"] == "CONSISTENT"
    assert row["vulnerability_verdict"] is None and row["ground_truth"] is None
    assert row["record_sha256"] == hashlib.sha256(raw).hexdigest()
    assert row["provenance"]["source"] == "ADMIN_UPLOADED_UNATTESTED_RECORD"
    assert row["provenance"]["report_revision_id"] == revision
    assert row["provenance"]["target_requests"] == row["provenance"]["model_calls"] == 0
    assert (await hunter.get(f"/api/reports/{rid}/business-records")).json() == []
    assert (await other.get(f"/api/reports/{rid}/business-records")).status_code == 404
    original = await admin.get(f"/api/business-records/{review_id}/record")
    assert original.content == raw
    assert original.headers["content-disposition"] == 'attachment; filename="business-record.json"'
    assert (await hunter.get(f"/api/business-records/{review_id}/record")).status_code == 404
    assert (await hunter.post(f"/api/business-records/{review_id}/review", json={"reviewer_note": "no"})).status_code == 404
    assert (await admin.post(f"/api/business-records/{review_id}/publish")).status_code == 409
    duplicate = await upload(admin, rid, revision, raw=raw)
    assert duplicate.json()["review_id"] == review_id
    assert (await counts(app))["business_record_reviews"] == 1
    note = "INTERNAL_SECRET <img src=x onerror=alert(1)>"
    assert (await admin.post(f"/api/business-records/{review_id}/review", json={"reviewer_note": note})).status_code == 200
    assert (await admin.post(f"/api/business-records/{review_id}/publish")).status_code == 200
    public = (await hunter.get(f"/api/reports/{rid}/business-records")).json()
    assert len(public) == 1 and public[0]["mode"] == "MANUAL_RECORD_REVIEW"
    assert "bukan pengujian langsung target" in public[0]["summary"]
    for secret in ("INTERNAL_SECRET", "provenance", "record_sha256", "actor_id", "reviewer_note", "CONSISTENT"):
        assert secret not in json.dumps(public)
    for actor in record()["phases"][0]["trace"]["actors"]:
        assert actor["actor_id"] not in json.dumps(public)
    private = (await admin.get(f"/api/reports/{rid}/business-records")).json()[0]
    assert private["reviewer_note"] == note and private["result"] == row["result"]
    assert (await admin.post(f"/api/business-records/{review_id}/review", json={"reviewer_note": "Periksa ulang sumber"})).status_code == 200
    assert (await hunter.get(f"/api/reports/{rid}/business-records")).json() == []
    assert (await admin.get(f"/api/business-records/{review_id}/record")).content == raw
    assert await counts(app) == {"business_record_reviews": 1, "runs": 0, "actions": 0, "evidence": 0, "ledger": 0, "provider_attempts": 0}
    async with app.state.db.connect() as conn:
        events = await all_rows(conn, "SELECT event_type FROM audit_events WHERE event_type LIKE 'BUSINESS_RECORD_%'")
    assert [row[0] for row in events] == ["BUSINESS_RECORD_IMPORTED", "BUSINESS_RECORD_REVIEWED", "BUSINESS_RECORD_PUBLISHED", "BUSINESS_RECORD_REVIEWED"]


@pytest.mark.parametrize("kind", ["inconsistent", "incomplete"])
async def test_weak_or_contradictory_record_never_becomes_a_vulnerability_verdict(env, kind):
    app, program, hunter, other, admin = env
    _, rid, revision = await setup(env)
    value = record()
    if kind == "inconsistent":
        value["phases"][1]["trace"]["events"][2]["actor_id"] = value["phases"][1]["trace"]["owner_id"]
    else:
        value["phases"][1]["trace"]["events"].pop(2)
    response = await upload(admin, rid, revision, value)
    assert response.status_code == 201, response.text
    result = response.json()
    assert result["result"]["status"] == ("INCONSISTENT" if kind == "inconsistent" else "INCOMPLETE")
    assert result["result"]["vulnerability_verdict"] is None
    review_id = result["review_id"]
    assert (await admin.post(f"/api/business-records/{review_id}/review", json={"reviewer_note": "Dampak belum dibuktikan", "analyst_override": "CONFIRMED"})).status_code == 422


async def test_role_csrf_and_revision_binding_are_enforced(env):
    app, program, hunter, other, admin = env
    _, rid, revision = await setup(env)
    assert (await upload(hunter, rid, revision)).status_code == 403
    assert (await upload(other, rid, revision)).status_code == 404
    assert (await upload(admin, rid, revision, headers={"X-CSRF-Token": "wrong"})).status_code == 403
    _, other_report, other_revision = await report_for(other, program, CLAIM)
    assert (await upload(admin, rid, other_revision)).status_code == 404
    assert (await counts(app))["business_record_reviews"] == 0


@pytest.mark.parametrize("scope,claim,code", [
    (SCOPE, CLAIM, "BUSINESS_RULES_MISMATCH"),
    ({**RULES, "business_rules_version": "unsupported"}, CLAIM, "BUSINESS_RULES_MISMATCH"),
    (RULES, {**CLAIM, "category": "BAC"}, "BUSINESS_CLAIM_REQUIRED"),
    (RULES, {**CLAIM, "claim_count": 2}, "BUSINESS_CLAIM_REQUIRED"),
])
async def test_rules_and_claim_prerequisites_block_import(env, scope, claim, code):
    app, program, hunter, other, admin = env
    _, rid, revision = await setup(env, scope, claim)
    response = await upload(admin, rid, revision)
    assert response.status_code == 409 and response.json()["error_code"] == code
    assert (await counts(app))["business_record_reviews"] == 0


@pytest.mark.parametrize("damage", ["duplicate", "secret_field", "nonfinite", "oversized", "extra_form_field"])
async def test_untrusted_input_is_bounded_and_errors_do_not_echo_data(env, damage):
    app, program, hunter, other, admin = env
    _, rid, revision = await setup(env)
    raw = json.dumps(record()).encode()
    kwargs = {}
    if damage == "duplicate":
        raw = raw.replace(b'"format_version": 1', b'"format_version": 0, "format_version": 1')
    elif damage == "secret_field":
        value = record(); value["credentials"] = "SECRET_DO_NOT_ECHO"
        raw = json.dumps(value).encode()
    elif damage == "nonfinite":
        raw = raw.replace(b'12345.0', b'NaN', 1)
    elif damage == "oversized":
        raw = b" " * 131073
    else:
        kwargs["data"] = {"owner_id": "SECRET_DO_NOT_ECHO"}
    response = await upload(admin, rid, revision, raw=raw, **kwargs)
    expected = 400 if damage == "extra_form_field" else 413 if damage == "oversized" else 422
    assert response.status_code == expected, response.text
    assert "SECRET_DO_NOT_ECHO" not in response.text
    assert (await counts(app))["business_record_reviews"] == 0


async def test_record_tampering_and_revoked_membership_fail_closed(env):
    app, program, hunter, other, admin = env
    _, rid, revision = await setup(env)
    response = await upload(admin, rid, revision)
    review_id = response.json()["review_id"]
    assert (await admin.post(f"/api/business-records/{review_id}/review", json={"reviewer_note": "Ditinjau sebelum perubahan file"})).status_code == 200
    async with app.state.db.connect() as conn:
        row = await one(conn, "SELECT record_path,imported_by FROM business_record_reviews WHERE review_id=?", (review_id,))
    path = app.state.config.data_dir / row["record_path"]
    path.write_bytes(b"SECRET_TAMPERED_RECORD")
    response = await admin.get(f"/api/business-records/{review_id}/record")
    assert response.status_code == 409 and "SECRET_TAMPERED_RECORD" not in response.text
    assert (await admin.post(f"/api/business-records/{review_id}/publish")).status_code == 409
    assert (await admin.post(f"/api/business-records/{review_id}/review", json={"reviewer_note": "Tidak boleh menimpa review"})).status_code == 409
    assert (await upload(admin, rid, revision)).status_code == 409
    async with app.state.db.transaction() as conn:
        await conn.execute("UPDATE memberships SET enabled=0 WHERE user_id=? AND program_id=?", (row["imported_by"], program))
    assert (await admin.get(f"/api/reports/{rid}/business-records")).status_code == 404
    assert (await admin.post(f"/api/business-records/{review_id}/publish")).status_code == 404


async def test_storage_limit_leaves_no_review_or_orphan_record(env):
    app, program, hunter, other, admin = env
    _, rid, revision = await setup(env)
    app.state.config.storage_limit_bytes = 1
    response = await upload(admin, rid, revision)
    assert response.status_code == 503 and response.json()["error_code"] == "STORAGE_LIMIT"
    assert (await counts(app))["business_record_reviews"] == 0
    assert not list((app.state.config.data_dir / "evidence").glob("manual-business/*.json"))


async def test_app_restart_preserves_record_review_publication_and_original(tmp_path):
    from app.config import Settings
    from app.main import create_app
    from app.operator import seed
    from conftest import PASSWORD, logged_client

    settings = Settings(data_dir=tmp_path, dispatcher_enabled=False, min_free_bytes=0, _env_file=None)
    first = create_app(settings)
    async with first.router.lifespan_context(first):
        program = await seed(first.state.db, PASSWORD)
        hunter, admin = [await logged_client(first, name) for name in ("hunter-a", "admin")]
        try:
            await activate(admin, program, RULES)
            _, report_id, revision = await report_for(hunter, program, CLAIM)
            row = (await upload(admin, report_id, revision)).json()
            review_id = row["review_id"]
            assert (await admin.post(f"/api/business-records/{review_id}/review", json={"reviewer_note": "Review persistensi"})).status_code == 200
            assert (await admin.post(f"/api/business-records/{review_id}/publish")).status_code == 200
        finally:
            await hunter.aclose(); await admin.aclose()
    second = create_app(settings)
    async with second.router.lifespan_context(second):
        admin = await logged_client(second, "admin")
        try:
            saved = (await admin.get(f"/api/reports/{report_id}/business-records")).json()[0]
            assert saved["publication_status"] == "PUBLISHED" and saved["reviewer_note"] == "Review persistensi"
            assert saved["record_sha256"] == row["record_sha256"] and saved["result"] == row["result"]
            raw = (await admin.get(f"/api/business-records/{review_id}/record")).content
            assert hashlib.sha256(raw).hexdigest() == row["record_sha256"]
            assert await counts(second) == {"business_record_reviews": 1, "runs": 0, "actions": 0, "evidence": 0, "ledger": 0, "provider_attempts": 0}
        finally:
            await admin.aclose()


async def test_new_snapshot_does_not_rebind_a_review_of_the_previous_snapshot(env):
    app, program, hunter, other, admin = env
    cid, report_id, revision = await setup(env)
    row = (await upload(admin, report_id, revision)).json()
    assert row["report_revision_number"] == 1
    response = await hunter.post(f"/api/conversations/{cid}/messages", json={
        "body": "Tambahan konteks untuk revisi berikutnya", "expected_draft_version": 1})
    assert response.status_code == 201
    updated = await hunter.post(f"/api/conversations/{cid}/reports", json={
        "expected_draft_version": 2, "claim": {**CLAIM, "primary_claim": "Klaim berbeda pada snapshot kedua"}})
    assert updated.status_code == 201
    assert updated.json()["report_revision_id"] != revision
    saved = (await admin.get(f"/api/reports/{report_id}/business-records")).json()[0]
    assert saved["report_revision_id"] == revision and saved["report_revision_number"] == 1
    assert saved["provenance"]["report_content_hash"] == row["provenance"]["report_content_hash"]
    assert saved["record_sha256"] == row["record_sha256"]
