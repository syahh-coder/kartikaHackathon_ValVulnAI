"""Form errors identify safe field labels without returning submitted values or private keys."""
from copy import deepcopy

import pytest
from fastapi.exceptions import RequestValidationError

from app.storage.db import one
from app.validation_errors import safe_field_errors
from conftest import SCOPE


@pytest.mark.parametrize("change,field", [
    ({"source_text": ""}, "source_text"),
    ({"source_text": " \n\t "}, "source_text"),
    ({"in_scope_rules": []}, "in_scope_rules"),
    ({"in_scope_rules": "PRIVATE_INPUT"}, "in_scope_rules"),
    ({"business_rules_version": "PRIVATE INPUT WITH SPACES"}, "business_rules_version"),
])
async def test_scope_errors_name_field_and_do_not_store_a_draft(env, change, field):
    app, program, _, _, admin = env
    response = await admin.post(f"/api/programs/{program}/scope-drafts", json={**deepcopy(SCOPE), **change})
    assert response.status_code == 422
    data = response.json()
    assert data["error_code"] == "SCHEMA_ERROR"
    assert any(e["field"] == field for e in data["field_errors"])
    assert "PRIVATE_INPUT" not in response.text and "PRIVATE INPUT" not in response.text
    async with app.state.db.connect() as conn:
        assert (await one(conn, "SELECT count(*) FROM scope_versions"))[0] == 0


async def test_valid_given_admin_example_saves_and_is_not_automatically_active(env):
    app, program, hunter, _, admin = env
    # Keep the application acceptance test standalone; this is the same supported schema as the demo file.
    example = {**deepcopy(SCOPE), "business_rules": "Setiap akun hanya boleh menghapus lampirannya sendiri.",
               "business_rules_version": "attachment-ownership-v1"}
    response = await admin.post(f"/api/programs/{program}/scope-drafts", json=example)
    assert response.status_code == 201
    assert (await hunter.get(f"/api/programs/{program}/guidelines")).json()["state"] == "NOT_CONFIGURED"
    async with app.state.db.connect() as conn:
        assert (await one(conn, "SELECT count(*) FROM scope_versions"))[0] == 1


def test_validation_feedback_never_echoes_input_context_message_or_unknown_key():
    secret = "PRIVATE_PASSWORD_OR_REPORT"
    exc = RequestValidationError([
        {"loc": ("body", "password"), "type": "string_too_long", "input": secret,
         "msg": secret, "ctx": {"value": secret}},
        {"loc": ("body", secret), "type": "extra_forbidden", "input": secret, "msg": secret},
    ])
    result = safe_field_errors(exc)
    assert result[0]["field"] == "password" and result[1]["field"] == "body"
    assert secret not in str(result)


def test_validation_feedback_is_bounded_and_nested_scope_labels_are_readable():
    exc = RequestValidationError([{"loc": ("body", "in_scope_rules", 0, "methods", 0), "type": "literal_error"}]*20)
    result = safe_field_errors(exc)
    assert len(result) == 8
    assert result[0]["field"] == "in_scope_rules.0.methods.0"
    assert "Metode HTTP" in result[0]["message"] and "GET" in result[0]["message"]
