"""Operator-side history of documented system development, not model training.

This records mechanisms already exercised while building the product. Moving a
catalog allocation must not erase that history. No payloads, GT or runtime tools.
Changes to mechanism identity require a documented revision review; retain the
old group in history even when an implementation is replaced.
"""

HISTORY_VERSION = "system-development-history-v1"

# point ID, conservative root cause group, existing development evidence document.
DEVELOPMENT_HISTORY = (
    ("BAC-08", "attachment-delete-owner-check", "docs/m2-verification.md"),
    ("XSS-08", "dom-fragment-innerhtml", "docs/m4b-verification.md"),
    ("UP-04", "html-element-output", "docs/m5-verification.md"),
)

# Area counts, not independent-group counts or manually verified report labels.
EVALUATION_AREAS = {"BAC": 4, "XSS": 4, "UPLOAD": 1, "BUSINESS_LOGIC": 1}
