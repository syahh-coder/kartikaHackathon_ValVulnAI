"""Best-effort credential redaction; callers must still use synthetic reports."""
import re


def redact_text(text: str, secret: str = "") -> str:
    if secret:
        text = text.replace(secret, "[REDACTED]")
    text = re.sub(r"(?i)\b(?:sk-or-v1-|sk-)[A-Za-z0-9_-]{8,}", "[REDACTED]", text)
    text = re.sub(r"(?i)\b(Bearer|Basic)\s+[A-Za-z0-9._~+/=-]+", r"\1 [REDACTED]", text)
    text = re.sub(r'''(?ix)(["']?(?:password|passwd|api[_-]?key|access[_-]?token|refresh[_-]?token|authorization|cookie|set-cookie|session[_-]?token)["']?\s*[:=]\s*)(?:"[^"\r\n]*"|'[^'\r\n]*'|[^\s,;}]+)''',
                  r'\1"[REDACTED]"', text)
    text = re.sub(r"(https?://)[^\s/@]+:[^\s/@]+@", r"\1[REDACTED]@", text)
    return text


def redact_value(value, secret: str = ""):
    if isinstance(value, str):
        return redact_text(value, secret)
    if isinstance(value, dict):
        return {k: redact_value(v, secret) for k, v in value.items()}
    if isinstance(value, list):
        return [redact_value(v, secret) for v in value]
    return value
