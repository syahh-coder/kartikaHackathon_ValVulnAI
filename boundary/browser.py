"""Fixed local fixtures and bounded browser observations; never report-supplied script."""
import base64
import hashlib
from typing import Literal
from urllib.parse import urlsplit
from uuid import UUID

from pydantic import Field, model_validator

from boundary.contracts import BrowserArguments, ORIGIN, Strict


def fixture_text(args: BrowserArguments) -> str:
    if args.operation == "upload_list_probe":
        from boundary.uploads import filename
        return filename(args.fixture, args.nonce)
    if args.fixture == "inert-v1":
        return "Kontrol inert ValVuln " + str(args.nonce)
    # No URL, cookie access, network callback or script from the submitted report.
    return '<img src="data:image/png;base64,AA==" onerror="window.__vvMarker(\'' + str(args.nonce) + '\')">'


def allowed_browser_url(url: str, args: BrowserArguments) -> bool:
    try:
        parsed = urlsplit(url)
        return (parsed.scheme == "http" and parsed.hostname == "lab" and parsed.port == 8001
                and not parsed.username and not parsed.password and not parsed.query
                and parsed.path == args.relative_path)
    except ValueError:
        return False


class MarkerEvent(Strict):
    nonce: UUID
    origin: Literal["http://lab:8001"]
    path: str = Field(pattern=r"^(?:/notifications/preview|/requests/[a-f0-9-]{36}/(?:attachments|attachment-labels))$")
    frame: Literal["main"]


class BrowserCapture(Strict):
    fixture: Literal["inert-v1", "marker-v1"]
    nonce: UUID
    origin: Literal["http://lab:8001"] = ORIGIN
    path: str = Field(default="/notifications/preview", pattern=r"^(?:/notifications/preview|/requests/[a-f0-9-]{36}/(?:attachments|attachment-labels))$")
    browser_version: str = Field(max_length=64)
    sandbox_requested: Literal[True] = True
    fresh_context: Literal[True] = True
    initial_storage_empty: bool = False
    js_control: bool = False
    payload_visible_as_text: bool = False
    marker_events: list[MarkerEvent] = Field(default_factory=list, max_length=1)
    denied_requests: int = Field(default=0, ge=0, le=40)
    websocket_blocks: int = Field(default=0, ge=0, le=40)
    popup_blocks: int = Field(default=0, ge=0, le=40)
    download_blocks: int = Field(default=0, ge=0, le=40)
    dom_excerpt: str = Field(default="", max_length=8192)
    screenshot_base64: str = Field(default="", max_length=349528)
    screenshot_sha256: str = Field(default="", max_length=64)

    @model_validator(mode="after")
    def screenshot(self):
        if self.screenshot_base64:
            data = base64.b64decode(self.screenshot_base64, validate=True)
            if (len(data) > 262144 or not data.startswith(b"\x89PNG\r\n\x1a\n") or
                    hashlib.sha256(data).hexdigest() != self.screenshot_sha256):
                raise ValueError("SCREENSHOT_INVALID")
        elif self.screenshot_sha256:
            raise ValueError("SCREENSHOT_MISSING")
        if any(event.nonce != self.nonce for event in self.marker_events):
            raise ValueError("MARKER_NONCE_MISMATCH")
        if any(event.path != self.path for event in self.marker_events):
            raise ValueError("MARKER_PATH_MISMATCH")
        return self
