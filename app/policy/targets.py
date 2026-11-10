import re
from urllib.parse import urlsplit

from app.common import AppError
from app.schemas import Claim, ScopeDraft

# Operator allowlist for the M2 development route. Runtime readiness is set by maintenance.
INITIAL_PROFILE = {
    "route_templates": ["/api/attachments/{id}"],
    "methods": ["GET", "DELETE"], "capabilities": ["BAC"],
    "account_aliases": ["requester-a", "requester-b"],
}
SAFE_SEGMENT = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def canonical_path(path: str) -> str:
    if (not path.startswith("/") or path.startswith("//") or len(path)>2048 or
            any(c in path for c in ("%", "\\", "?", "#", ":")) or
            any(ord(c)<33 or ord(c)>126 for c in path)):
        raise AppError(422, "PATH_DENIED", "Path relatif harus kanonis, tanpa encoding ambigu.")
    parts = path.split("/")[1:]
    if not parts or any(not SAFE_SEGMENT.fullmatch(p) for p in parts):
        raise AppError(422, "PATH_DENIED", "Segmen path tidak sah.")
    return path


def matches(template: str, path: str) -> bool:
    a, b = template.split("/"), path.split("/")
    return len(a)==len(b) and all(x==y or (x=="{id}" and bool(SAFE_SEGMENT.fullmatch(y))) for x,y in zip(a,b))


def validate_scope(draft: ScopeDraft, bindings: dict[str, dict]):
    for rule in draft.in_scope_rules + draft.out_of_scope_rules:
        binding = bindings.get(rule.asset_alias)
        if not binding:
            raise AppError(422, "BINDING_REQUIRED", "Alias aset harus terdaftar oleh operator.")
        profile = binding["profile"]
        if (rule.path_template not in profile["route_templates"] or
                not set(rule.methods) <= set(profile["methods"]) or
                not set(rule.capabilities) <= set(profile["capabilities"])):
            raise AppError(422, "RULE_DENIED", "Aturan melampaui profil operator.")
    allowed = {r.model_dump_json() for r in draft.in_scope_rules}
    denied = {r.model_dump_json() for r in draft.out_of_scope_rules}
    if allowed & denied:
        raise AppError(422, "AMBIGUOUS_RULE", "Aturan izin dan pengecualian identik.")


def gate(claim: Claim, scope: dict | None, bindings: dict[str, dict]):
    if not scope or not claim.asset_alias or not claim.path:
        return "UNKNOWN", "UNKNOWN", "NEEDS_INFO", None
    binding = bindings.get(claim.asset_alias)
    if not binding:
        return "OUT_OF_SCOPE", "UNKNOWN", "OUT_OF_SCOPE", None
    try:
        path = canonical_path(claim.path)
    except AppError:
        return "OUT_OF_SCOPE", "UNKNOWN", "OUT_OF_SCOPE", binding["target_id"]
    def applies(rule):
        return (rule["asset_alias"]==claim.asset_alias and matches(rule["path_template"], path)
                and claim.method in rule["methods"])
    if any(applies(r) for r in scope["out_of_scope_rules"]):
        return "OUT_OF_SCOPE", "UNKNOWN", "OUT_OF_SCOPE", binding["target_id"]
    candidates = [r for r in scope["in_scope_rules"] if applies(r)]
    if not candidates:
        return "OUT_OF_SCOPE", "UNKNOWN", "OUT_OF_SCOPE", binding["target_id"]
    if not any(claim.category in r["capabilities"] for r in candidates):
        return "IN_SCOPE", "UNSUPPORTED", "UNSUPPORTED", binding["target_id"]
    if (not claim.primary_claim.strip() or claim.claim_count != 1 or
            len(set(claim.account_aliases)) < 2 or
            not set(claim.account_aliases) <= set(binding["profile"]["account_aliases"])):
        return "IN_SCOPE", "SUPPORTED", "NEEDS_INFO", binding["target_id"]
    return "IN_SCOPE", "SUPPORTED", "SCOPE_CHECKED", binding["target_id"]


def check_action(claim: Claim, scope: dict, binding: dict, *, method: str, path: str,
                 account_alias: str, headers: dict[str, str] | None = None, body: bytes = b""):
    canonical_path(path)
    if len(body)>131072:
        raise AppError(413, "BODY_LIMIT", "Body tindakan terlalu besar.")
    # Only inert content headers; credentials/identity always resolve through aliases.
    if any(h.lower() not in {"accept", "content-type"} for h in (headers or {})):
        raise AppError(403, "HEADER_DENIED", "Header tindakan tidak diizinkan.")
    if account_alias not in binding["profile"]["account_aliases"]:
        raise AppError(403, "ACCOUNT_DENIED", "Alias akun tidak diizinkan.")
    proposed = claim.model_copy(update={"path": path, "method": method})
    if gate(proposed, scope, {claim.asset_alias: binding})[2] != "SCOPE_CHECKED":
        raise AppError(403, "POLICY_BLOCKED", "Tindakan di luar scope.")


def check_redirect(origin: str, location: str) -> str:
    url = urlsplit(location)
    if url.scheme or url.netloc:
        base = urlsplit(origin)
        if (url.scheme, url.hostname, url.port or (443 if url.scheme=="https" else 80)) != (
                base.scheme, base.hostname, base.port or (443 if base.scheme=="https" else 80)) or url.username or url.password:
            raise AppError(403, "REDIRECT_DENIED", "Redirect keluar binding.")
        location = url.path + ("?"+url.query if url.query else "") + ("#"+url.fragment if url.fragment else "")
    return canonical_path(location)
