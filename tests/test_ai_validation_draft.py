"""Provider HTTP is intercepted; confirmation/policy/run linkage uses the real API."""
import json

import httpx
import pytest

from app.common import packed, uid
from app.providers.azure import AzureTransport
from app.providers.openrouter import OpenRouterTransport
from app.storage.db import all_rows, one
from conftest import activate
from test_azure_text import azure_config, completion as azure_completion
from test_text_triage import HttpScript, SUGGESTION, completion, finished, live_config, submit
from test_m3_bac import runtime

RID = "10000000-0000-4000-8000-000000000001"
PATHS = {
    "BAC": ("BAC-08", "/api/attachments/victim", "/api/attachments/control"),
    "XSS": ("XSS-08", "/notifications/preview", None),
    "UPLOAD": ("UP-04", f"/requests/{RID}/attachments", None),
}
RULES = [{"asset_alias": "portal", "path_template": path, "methods": methods, "capabilities": [kind]}
         for path, methods, kind in [("/api/attachments/{id}", ["GET", "DELETE"], "BAC"),
            ("/notifications/preview", ["GET"], "XSS"),
            ("/requests/{id}/attachments", ["GET"], "UPLOAD"),
            ("/requests/{id}/attachment-labels", ["GET"], "UPLOAD"),
            ("/api/requests/{id}/attachments", ["POST"], "UPLOAD")]]


async def case(env, provider="openrouter", kind="BAC", *, fields_update=None, suggestion_update=None,
               text=None, denied=False, denied_reads=False, expect_error=None):
    app, program, hunter, other, admin = env
    async with app.state.db.transaction() as conn:
        target = await one(conn, "SELECT profile_json FROM target_bindings WHERE asset_alias='portal'")
        profile = json.loads(target[0]) | {"route_templates": [r["path_template"] for r in RULES],
                                         "methods": ["GET", "DELETE", "POST"], "capabilities": list(PATHS)}
        await conn.execute("UPDATE target_bindings SET profile_json=?", (packed(profile),))
    scope = {"source_text": "Program sintetis, satu klaim dan dua akun uji.", "in_scope_rules": RULES}
    if denied:
        scope["out_of_scope_rules"] = [RULES[0] | {"methods": ["DELETE"]}]
    if denied_reads:
        scope["out_of_scope_rules"] = [RULES[0] | {"methods": ["GET"]}]
    await activate(admin, program, scope)
    subtype, path, control = PATHS[kind]
    fields = {"asset_alias": "portal", "path": path, "control_path": control,
              "account_aliases": ["requester-a", "requester-b"], "claim_count": 1} | (fields_update or {})
    suggestion = SUGGESTION | {"category": kind, "subtype": subtype, "missing_information": [],
        "scope_suggestion": "IN_SCOPE", "capability_suggestion": "AVAILABLE", "validation_fields": fields} | (suggestion_update or {})
    response = await hunter.post(f"/api/programs/{program}/conversations")
    cid = response.json()["conversation_id"]
    response = await hunter.post(f"/api/conversations/{cid}/messages", json={"expected_draft_version": 0,
        "body": text or f"Laporan {kind} pada portal, requester-a dan requester-b. Path {path} kontrol {control or 'tidak ada'}."})
    assert response.status_code == 201, response.text
    config = (azure_config if provider == "azure" else live_config)(data_dir=app.state.config.data_dir, min_free_bytes=0)
    body = (azure_completion if provider == "azure" else completion)(choices=[{
        "finish_reason": "stop", "message": {"content": packed(suggestion)}}])
    script = HttpScript([body])
    app.state.text_triage.config = config
    cls = AzureTransport if provider == "azure" else OpenRouterTransport
    app.state.text_triage.transport = cls(config, http_transport=httpx.MockTransport(script))
    response = await submit(hunter, cid)
    assert response.status_code == 202, response.text
    tid = response.json()["triage_id"]
    result = await finished(app, hunter, tid)
    if expect_error:
        assert result["status"] == "FAILED" and result["error_code"] == expect_error, result
    else:
        assert result["status"] == "SUCCEEDED", result
    return app, hunter, other, admin, cid, tid, script


@pytest.mark.parametrize("provider", ["openrouter", "azure"])
@pytest.mark.parametrize("kind", list(PATHS))
async def test_provider_to_draft_confirmation_run_and_provenance(env, provider, kind):
    app, hunter, _, _, cid, tid, script = await case(env, provider, kind)
    response = await hunter.post(f"/api/triages/{tid}/validation-draft")
    assert response.status_code == 200, response.text
    draft = response.json()
    assert draft["policy_status"] == "SCOPE_CHECKED", draft
    assert draft["requires_confirmation"] and not draft["target_execution_allowed"] and draft["verdict"] is None
    async with app.state.db.connect() as conn:
        for table in ("runs", "actions", "handoff_actions", "evidence", "assessments"):
            assert (await one(conn, "SELECT count(*) FROM " + table))[0] == 0
    snapshot_body = {"expected_draft_version": 1, "claim": draft["claim"], "source_triage_id": tid}
    snapshot = await hunter.post(f"/api/conversations/{cid}/reports", json=snapshot_body)
    assert snapshot.status_code == 201, snapshot.text
    again = await hunter.post(f"/api/conversations/{cid}/reports", json=snapshot_body)
    assert again.json() == snapshot.json()
    rev = snapshot.json()
    # NONE proves the handoff into Workflow without making a target request or claiming lab verification.
    response = await hunter.post(f"/api/reports/{rev['report_id']}/runs", headers={"Idempotency-Key": uid()},
                                json={"report_revision_id": rev["report_revision_id"], "tool_execution_mode": "NONE"})
    assert response.status_code == 202, response.text
    async with app.state.db.connect() as conn:
        events = await all_rows(conn, "SELECT details_json FROM audit_events WHERE event_type='AI_CLAIM_CONFIRMED'")
        assert len(events) == 1
        proof = json.loads(events[0][0])
        assert proof["source_triage_id"] == tid and proof["report_revision_id"] == rev["report_revision_id"]
        assert proof["provider"] == provider and len(proof["confirmed_claim_hash"]) == 64
        assert (await one(conn, "SELECT count(*) FROM actions"))[0] == 0
        ledger = await one(conn, "SELECT status,actual_idr FROM ledger WHERE triage_id=?", (tid,))
        assert ledger["status"] == ("COST_UNKNOWN" if provider == "azure" else "SETTLED")
        if provider == "azure":
            assert ledger["actual_idr"] is None
        else:
            assert ledger["actual_idr"] == 17
    assert len(script.requests) == 1


@pytest.mark.parametrize("change", ["draft", "scope", "membership", "failed", "old_schema"])
async def test_stale_or_revoked_source_cannot_prepare_or_confirm(env, change):
    app, hunter, _, admin, cid, tid, _ = await case(env)
    claim = (await hunter.post(f"/api/triages/{tid}/validation-draft")).json()["claim"]
    async with app.state.db.transaction() as conn:
        if change == "draft":
            await conn.execute("UPDATE conversations SET draft_version=draft_version+1 WHERE conversation_id=?", (cid,))
        elif change == "scope":
            await conn.execute("UPDATE programs SET authorization_epoch=authorization_epoch+1")
        elif change == "membership":
            await conn.execute("UPDATE memberships SET enabled=0 WHERE user_id=(SELECT owner_user_id FROM conversations WHERE conversation_id=?)", (cid,))
        elif change == "failed":
            await conn.execute("UPDATE text_triages SET status='FAILED',output_json=NULL WHERE triage_id=?", (tid,))
        else:
            await conn.execute("UPDATE text_triages SET schema_version='triage-v1' WHERE triage_id=?", (tid,))
    response = await hunter.post(f"/api/triages/{tid}/validation-draft")
    assert response.status_code in {404, 409}
    response = await hunter.post(f"/api/conversations/{cid}/reports", json={
        "expected_draft_version": 2 if change == "draft" else 1, "claim": claim, "source_triage_id": tid})
    assert response.status_code in {404, 409}


async def test_owner_and_conversation_binding(env):
    app, hunter, other, admin, cid, tid, _ = await case(env)
    assert (await other.post(f"/api/triages/{tid}/validation-draft")).status_code == 404
    assert (await admin.post(f"/api/triages/{tid}/validation-draft")).status_code == 403
    draft = (await hunter.post(f"/api/triages/{tid}/validation-draft")).json()
    program = env[1]
    another = (await hunter.post(f"/api/programs/{program}/conversations")).json()["conversation_id"]
    await hunter.post(f"/api/conversations/{another}/messages", json={"body": "Laporan berbeda", "expected_draft_version": 0})
    response = await hunter.post(f"/api/conversations/{another}/reports", json={
        "expected_draft_version": 1, "claim": draft["claim"], "source_triage_id": tid})
    assert response.status_code == 409 and response.json()["error_code"] == "TRIAGE_CONTEXT_MISMATCH"


@pytest.mark.parametrize("variant,expected", [("oos", "OUT_OF_SCOPE"), ("hallucinated", "NEEDS_INFO"),
    ("missing", "NEEDS_INFO"), ("multi", "NEEDS_INFO"), ("unsupported", "UNSUPPORTED"), ("control_denied", "POLICY_BLOCKED")])
async def test_ai_cannot_authorize_paths_controls_or_capability(env, variant, expected):
    kwargs = {}
    if variant == "oos": kwargs["denied"] = True
    elif variant == "hallucinated": kwargs["fields_update"] = {"path": "/api/attachments/invented"}
    elif variant == "missing": kwargs["fields_update"] = {"path": None, "account_aliases": []}
    elif variant == "multi": kwargs["fields_update"] = {"claim_count": 2}
    elif variant == "unsupported": kwargs["suggestion_update"] = {"category": "BUSINESS_LOGIC", "subtype": "UNSUPPORTED", "capability_suggestion": "UNSUPPORTED", "validation_fields": None}
    else: kwargs["denied_reads"] = True
    app, hunter, _, _, _, tid, _ = await case(env, **kwargs)
    response = await hunter.post(f"/api/triages/{tid}/validation-draft")
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["policy_status"] == expected, result
    assert not result["target_execution_allowed"]
    async with app.state.db.connect() as conn:
        assert (await one(conn, "SELECT count(*) FROM runs"))[0] == 0


@pytest.mark.parametrize("provider", ["openrouter", "azure"])
async def test_malformed_validation_fields_fail_before_proposal(env, provider):
    _, hunter, _, _, _, tid, _ = await case(env, provider, fields_update={"path": "x" * 2049}, expect_error="SCHEMA_ERROR")
    response = await hunter.post(f"/api/triages/{tid}/validation-draft")
    assert response.status_code == 409 and response.json()["error_code"] == "TRIAGE_NOT_READY"


@pytest.mark.parametrize("provider", ["openrouter", "azure"])
@pytest.mark.parametrize("condition,verdict", [("vulnerable", "CONFIRMED"), ("fixed", "REFUTED")])
async def test_ai_to_worker_verifier_admin_and_hunter(env, tmp_path, monkeypatch, provider, condition, verdict):
    # Real local ASGI lab and HTTP worker, intercepted model, no cloud or external target.
    async with runtime(env, tmp_path, monkeypatch, condition) as (claim, worker, handoff):
        fields = {k: claim[k] for k in ("asset_alias", "path", "control_path", "account_aliases")}
        text = f"portal requester-a requester-b; korban {claim['path']}; kontrol {claim['control_path']}."
        app, hunter, _, admin, cid, tid, script = await case(env, provider, fields_update=fields, text=text)
        draft = (await hunter.post(f"/api/triages/{tid}/validation-draft")).json()
        assert draft["policy_status"] == "SCOPE_CHECKED", draft
        snapshot = (await hunter.post(f"/api/conversations/{cid}/reports", json={
            "expected_draft_version": 1, "claim": draft["claim"], "source_triage_id": tid})).json()
        response = await hunter.post(f"/api/reports/{snapshot['report_id']}/runs", headers={"Idempotency-Key": uid()},
            json={"report_revision_id": snapshot["report_revision_id"], "tool_execution_mode": "LAB"})
        assert response.status_code == 202, response.text
        run_id = response.json()["run_id"]
        await app.state.workflow.tick()
        private = (await admin.get(f"/api/runs/{run_id}")).json()
        assert private["process_status"] == "COMPLETED", private
        assert private["claim_origin"]["source_triage_id"] == tid
        assert private["assessment"]["system_verified"]["verdict"] == verdict
        before = (await hunter.get(f"/api/runs/{run_id}")).json()
        assert before["assessment"] is None
        assert (await admin.post(f"/api/runs/{run_id}/review", json={"reviewer_note": "Review integrasi sintetis."})).status_code == 200
        assert (await admin.post(f"/api/runs/{run_id}/publish")).status_code == 200
        public = (await hunter.get(f"/api/runs/{run_id}")).json()
        assert public["claim_origin"]["human_confirmed"] and public["claim_origin"]["provider"] == provider
        assert public["assessment"]["verdict"] == verdict
        assert "reviewer_note" not in public["assessment"]
        assert public["counters"]["target_requests"] == 14
        assert len(script.requests) == 1
