import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError

from app.config import Settings
from app.main import create_app
from app.storage.db import one


async def test_migration_restart_preserves_data(tmp_path):
    settings = Settings(data_dir=tmp_path, _env_file=None)
    app = create_app(settings)
    async with app.router.lifespan_context(app):
        async with app.state.db.transaction() as conn:
            await conn.execute("INSERT INTO users VALUES ('u','demo','not-a-real-hash',1)")
    app2 = create_app(settings)
    async with app2.router.lifespan_context(app2):
        async with app2.state.db.connect() as conn:
            assert await one(conn, "SELECT 1 FROM users WHERE user_id='u'")
            assert (await one(conn, "SELECT count(*) n FROM schema_versions"))["n"] == 6
            assert (await one(conn, "SELECT count(*) n FROM runs"))["n"] == 0
            assert (await one(conn, "SELECT count(*) n FROM ledger"))["n"] == 0
        async with AsyncClient(transport=ASGITransport(app=app2), base_url="http://127.0.0.1:8000") as client:
            assert (await client.get("/api/health")).status_code == 200
            assert (await client.get("/api/readiness")).json()["worker"] == "NOT_IMPLEMENTED"


@pytest.mark.parametrize("kwargs", [
    {"budget_idr": 50_001}, {"execution_mode": "silent-fallback"},
    {"public_origin": "http://0.0.0.0:8000"}, {"public_origin": "http://localhost:8000/path"},
    {"public_origin": "https://example.test"}, {"allow_http_loopback": False},
])
def test_invalid_config_rejected(kwargs):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **kwargs)
