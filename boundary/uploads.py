"""Repository-owned bounded fixtures. No report-supplied file, script or URL."""
import hashlib
from uuid import UUID
from typing import Literal
from pydantic import Field
from boundary.contracts import Strict


def filename(fixture: str, nonce: UUID) -> str:
    if fixture == "inert-v1":
        return f"Kontrol inert ValVuln {nonce}.txt"
    if fixture != "marker-v1":
        raise ValueError("UNKNOWN_FIXTURE")
    return f'<svg onload="window.__vvMarker(\'{nonce}\')">'


CONTENT = b"Lampiran sintetis ValVuln; bukan dokumen pengguna."
CONTENT_SHA256 = hashlib.sha256(CONTENT).hexdigest()


class UploadedFile(Strict):
    upload_id: UUID
    request_id: UUID
    filename: str = Field(max_length=256)
    media_type: Literal["text/plain"]
    content_sha256: Literal[CONTENT_SHA256]
    size: Literal[len(CONTENT)]
