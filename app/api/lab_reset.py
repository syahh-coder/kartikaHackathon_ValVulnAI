from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, ConfigDict, model_validator
from typing import Literal

from app.auth import Principal, principal
from boundary.lab_reset import LabCondition

router = APIRouter()


class ResetInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    confirm: Literal["RESET_VULNERABLE_DEMO", "RESET_DEMO_LAB"]
    condition: LabCondition = "vulnerable"

    @model_validator(mode="after")
    def legacy_condition(self):
        if self.confirm == "RESET_VULNERABLE_DEMO" and self.condition != "vulnerable":
            raise ValueError("Gunakan konfirmasi RESET_DEMO_LAB untuk mode kontrol diperbaiki.")
        return self


class ManualInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    confirm: Literal["OPEN_SHARED_MANUAL_LAB"]


@router.post("/api/programs/{program_id}/lab-manual-session")
async def open_manual(program_id: str, body: ManualInput, request: Request, user: Principal = Depends(principal)):
    return await request.app.state.lab_reset.open_manual(user, program_id)


@router.get("/api/programs/{program_id}/lab-reset")
async def status(program_id: str, request: Request, user: Principal = Depends(principal)):
    return await request.app.state.lab_reset.status(user, program_id)


@router.post("/api/programs/{program_id}/lab-reset", status_code=202)
async def start(program_id: str, body: ResetInput, request: Request, user: Principal = Depends(principal)):
    return await request.app.state.lab_reset.start(user, program_id, body.condition)
