"""Application-selected bounded planners/verifiers, never selected by report instructions."""
from app.common import AppError
from app.schemas import Claim
from app.storage.db import one


def validator_for(claim: Claim):
    from app.agent import bac, xss, upload
    if claim.category == "BAC":
        return bac
    if claim.category == "XSS":
        return xss
    if claim.category == "UPLOAD":
        return upload
    raise AppError(422, "UNSUPPORTED", "Belum ada validator lab untuk kategori ini.")


async def verify(conn, run_id: str):
    revision = await one(conn, "SELECT r.claim_json FROM report_revisions r JOIN runs u ON u.report_revision_id=r.revision_id WHERE u.run_id=?", (run_id,))
    if not revision:
        raise AppError(404, "NOT_FOUND", "Revisi run tidak ditemukan.")
    return await validator_for(Claim.model_validate_json(revision[0])).verify(conn, run_id)
