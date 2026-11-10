from app.common import AppError

TERMINAL = {"COMPLETED", "NEEDS_INFO", "OUT_OF_SCOPE", "UNSUPPORTED", "POLICY_BLOCKED",
            "PROVIDER_REFUSED", "FAILED", "CANCELLED", "CONFIGURATION_REQUIRED"}
NEXT = {
    "RECEIVED": {"PARSED"}, "PARSED": {"SCOPE_CHECKED"}, "SCOPE_CHECKED": {"PLANNED"},
    "PLANNED": {"POLICY_CHECKED"}, "POLICY_CHECKED": {"RUNNING"},
    "RUNNING": {"VERIFYING"}, "VERIFYING": {"COMPLETED"},
}


def validate_transition(current: str, following: str):
    if current in TERMINAL or following not in NEXT.get(current, set()) | (TERMINAL - {"COMPLETED"}):
        raise AppError(409, "STATE_CONFLICT", "Transisi proses tidak diizinkan.")
