from fastapi import APIRouter, Depends, Request

from app.auth import Principal, principal
from app.providers.triage_contracts import TriageInput

router = APIRouter()


@router.post("/api/conversations/{conversation_id}/triages", status_code=202)
async def create_triage(conversation_id: str, body: TriageInput, request: Request, user: Principal = Depends(principal)):
    service = request.app.state.text_triage
    triage_id = await service.create(user, conversation_id, body.expected_draft_version,
                                     request.headers.get("Idempotency-Key", ""))
    return await service.get(user, triage_id)


@router.get("/api/triages/{triage_id}")
async def get_triage(triage_id: str, request: Request, user: Principal = Depends(principal)):
    return await request.app.state.text_triage.get(user, triage_id)


@router.post("/api/triages/{triage_id}/cancel")
async def cancel_triage(triage_id: str, request: Request, user: Principal = Depends(principal)):
    service = request.app.state.text_triage
    await service.cancel(user, triage_id)
    return await service.get(user, triage_id)
