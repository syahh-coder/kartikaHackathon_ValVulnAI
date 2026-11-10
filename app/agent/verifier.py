from typing import Literal

from pydantic import Field

from app.common import AppError
from app.schemas import DTO
from app.storage.db import one


class AssessmentProposal(DTO):
    claim_id: str
    verdict: Literal["CONFIRMED", "REFUTED", "INCONCLUSIVE"]
    reasoning: str = Field(min_length=1, max_length=4000)
    supporting_evidence_ids: list[str] = Field(default_factory=list, max_length=40)
    contradicting_evidence_ids: list[str] = Field(default_factory=list, max_length=40)
    controls_performed: list[str] = Field(default_factory=list, max_length=20)
    missing_prerequisites: list[str] = Field(default_factory=list, max_length=20)
    limitations: list[str] = Field(default_factory=list, max_length=20)
    next_action: str = Field(max_length=2000)


async def validate_assessment(conn, run_id: str, proposal: AssessmentProposal):
    run = await one(conn, "SELECT primary_claim_id FROM runs WHERE run_id=?", (run_id,))
    if not run or proposal.claim_id != run[0]:
        raise AppError(422, "CLAIM_MISMATCH", "Klaim assessment tidak cocok dengan run.")
    for eid in proposal.supporting_evidence_ids + proposal.contradicting_evidence_ids:
        evidence = await one(conn, "SELECT e.* FROM evidence e JOIN actions a ON e.action_id=a.action_id AND e.run_id=a.run_id "
                                   "WHERE e.evidence_id=? AND e.run_id=?", (eid, run_id))
        if not evidence:
            raise AppError(422, "EVIDENCE_MISMATCH", "Evidence harus berasal dari action pada run yang sama.")
    if proposal.verdict != "INCONCLUSIVE":
        from app.agent.lab_validation import verify
        verified = await verify(conn, run_id)
        required = set(verified["supporting_evidence_ids"] + verified["contradicting_evidence_ids"])
        supplied = set(proposal.supporting_evidence_ids + proposal.contradicting_evidence_ids)
        if proposal.verdict != verified["verdict"] or not required or required != supplied:
            raise AppError(422, "IMPACT_NOT_VERIFIED", "Dampak/kontrol klaim belum terbukti pada observasi tersimpan.")
    return proposal.model_dump(exclude={"claim_id"})
