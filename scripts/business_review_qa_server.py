"""Disposable loopback app for host UI QA. Never uses project runtime storage."""
import argparse
import asyncio
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from threading import Thread

import uvicorn

from app.config import Settings
from app.main import create_app
from app.operator import seed
from app.storage.db import one


async def counts(db):
    async with db.connect() as conn:
        return {table: (await one(conn, f"SELECT count(*) FROM {table}"))[0]
                for table in ("business_record_reviews", "runs", "actions", "evidence", "ledger", "provider_attempts")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, required=True)
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        raise ValueError("Invalid loopback QA port")
    password = json.loads(sys.stdin.readline())["password"]
    with TemporaryDirectory(prefix="valvuln-business-ui-") as directory:
        app = create_app(Settings(data_dir=Path(directory), public_origin=f"http://127.0.0.1:{args.port}",
                                  dispatcher_enabled=False, min_free_bytes=0, _env_file=None))
        asyncio.run(seed(app.state.db, password))
        server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=args.port, log_level="warning", access_log=False))
        def control():
            for line in sys.stdin:
                if line.strip() == "stop":
                    server.should_exit = True
                    return
            server.should_exit = True
        Thread(target=control, daemon=True).start()
        server.run()
        state = asyncio.run(counts(app.state.db))
    print("QA_FINAL " + json.dumps({"counts": state, "temporary_storage_removed": True}), flush=True)


if __name__ == "__main__":
    main()
