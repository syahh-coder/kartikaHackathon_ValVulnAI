"""Offline CLI compatibility wrapper for the shared trace consistency validator."""
import argparse
import json
from pathlib import Path

from boundary.business_trace import (SNAPSHOT_FIELDS, RULES_VERSION, OPERATIONS, STATES,
                                    Snapshot, Actor, Event, Trace, Phase, TraceRecord, audit, _output)
from evaluator.business_record_audit import read_json_record

def read_and_audit(path: Path) -> dict:
    try:
        return audit(read_json_record(path))
    except (OSError, ValueError, RecursionError):
        return _output("INVALID", ["TRACE_READ_ERROR"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path)
    result = read_and_audit(parser.parse_args().record)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["status"] == "CONSISTENT" else 2)


if __name__ == "__main__":
    main()
