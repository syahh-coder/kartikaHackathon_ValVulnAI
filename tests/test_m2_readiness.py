import time
from uuid import uuid4

from httpx import ASGITransport,AsyncClient


async def test_readiness_checks_worker_dirty_state(env,monkeypatch,tmp_path):
    from app.transport import Handoff
    app,p,*_=env
    app.state.config.transport_key_file=tmp_path/"key"
    app.state.config.transport_key_file.write_text("31"*32)
    value={"boot_id":str(uuid4()),"captured_at":time.time(),"status":"IDLE","snapshot_id":str(uuid4()),"dirty":False}
    monkeypatch.setattr(Handoff,"heartbeat",lambda self:value)
    async with app.state.db.transaction() as conn:
        await conn.execute("UPDATE target_bindings SET ready=1,dirty=0,snapshot_id=?",(value["snapshot_id"],))
    async with AsyncClient(transport=ASGITransport(app=app),base_url="http://127.0.0.1:8000") as client:
        assert (await client.get("/api/readiness")).json()["lab"]=="OPERATOR_VERIFIED"
        value["dirty"]=True
        result=(await client.get("/api/readiness")).json()
        assert result["lab"]=="OPERATOR_CHECK_REQUIRED"
        assert result["lab_validation_from_ui"]=="AVAILABLE"
