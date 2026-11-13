"""Compatibility entry point; uses the app API/shared ledger, never direct generation."""
from scripts.smoke_text_provider import main


if __name__ == "__main__":
    raise SystemExit(main())

