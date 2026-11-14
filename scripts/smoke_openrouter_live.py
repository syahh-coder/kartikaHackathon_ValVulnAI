"""Compatibility entry point; uses the app API/shared ledger, never direct generation."""
from scripts.smoke_text_provider import main
import sys


if __name__ == "__main__":
    raise SystemExit(main(["--provider", "openrouter", *sys.argv[1:]]))

