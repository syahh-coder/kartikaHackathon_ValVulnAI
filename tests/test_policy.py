import pytest

from app.common import AppError
from app.policy.targets import INITIAL_PROFILE, canonical_path, check_action, check_redirect, gate, validate_scope
from app.schemas import Claim, ScopeDraft
from conftest import CLAIM, SCOPE

BINDING = {"target_id": "portal-lab", "profile": INITIAL_PROFILE}


@pytest.mark.parametrize("path", [
    "http://lab:8001/api/attachments/a", "//lab/api/attachments/a", "/api/attachments/../reset",
    "/api/attachments/%2e%2e", "/api/attachments/%252f", "/api//attachments/a",
    "/api/attachments/a?url=http://evil.invalid", "/api/attachments/a#x", "/api/attachments/a\\b",
    "/api/attachments/.", "/api/attachments/a/", "/api/attachments/a\n", "/api/attachments/é",
])
def test_ambiguous_paths_denied(path):
    with pytest.raises(AppError):
        canonical_path(path)


def test_policy_action_identity_and_exclusions():
    claim = Claim(**CLAIM)
    check_action(claim, SCOPE | {"out_of_scope_rules": []}, BINDING,
                 method="GET", path="/api/attachments/a", account_alias="requester-a")
    for args in [
        {"path": "/reset"}, {"method": "POST"}, {"account_alias": "platform-admin"},
        {"headers": {"Authorization": "secret"}}, {"headers": {"Host": "external"}}, {"body": b"x"*131073},
    ]:
        with pytest.raises(AppError):
            check_action(claim, SCOPE | {"out_of_scope_rules": []}, BINDING,
                         **({"method": "GET", "path": "/api/attachments/a", "account_alias": "requester-a"} | args))
    denied = SCOPE | {"out_of_scope_rules": SCOPE["in_scope_rules"]}
    assert gate(claim, denied, {"portal": BINDING})[0] == "OUT_OF_SCOPE"
    with pytest.raises(AppError):
        validate_scope(ScopeDraft(**denied), {"portal": BINDING})


@pytest.mark.parametrize("location", [
    "http://169.254.169.254/latest", "http://host.docker.internal:8000/api/health", "https://lab:8001/api/attachments/a",
    "http://lab:8002/api/attachments/a", "http://user:pass@lab:8001/api/attachments/a", "/%2e%2e/reset", "//evil.invalid/path",
])
def test_redirect_policy_denies_other_origins(location):
    with pytest.raises(AppError):
        check_redirect("http://lab:8001", location)


def test_redirect_allowed_path_still_needs_action_gate():
    assert check_redirect("http://lab:8001", "http://lab:8001/api/attachments/a") == "/api/attachments/a"
