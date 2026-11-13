"""Opt-in loopback access for an operator-owned manual lab copy."""
from pathlib import Path
from urllib.parse import urlsplit

from fastapi.responses import HTMLResponse


def validate_manual_origin(value: str) -> str | None:
    if not value:
        return None
    try:
        parsed = urlsplit(value)
        valid = (parsed.scheme == "http" and parsed.hostname in {"127.0.0.1", "localhost"}
                 and parsed.port is not None and 1024 <= parsed.port <= 65535
                 and parsed.username is None and parsed.password is None
                 and not parsed.path and not parsed.query and not parsed.fragment
                 and value == f"http://{parsed.hostname}:{parsed.port}")
    except ValueError:
        valid = False
    if not valid:
        raise ValueError("LAB_MANUAL_ORIGIN must be an exact HTTP loopback origin with a port")
    return value


def register_manual_home(app, origin: str | None) -> None:
    if origin is None:
        return

    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    async def manual_home():
        return HTMLResponse(Path(__file__).with_name("manual.html").read_text(encoding="utf-8"))
