"""Administrative evidence workflow, without target tools or model dispatch.

The input is an already checked, untrusted uploaded record attached to a report.
Consistency cannot establish target origin, actor authorization or impact.
"""
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.common import digest, packed


VERSION = "business-evidence-workflow-v1"
Phase = Literal["NEEDS_SNAPSHOT_REVIEW", "NEEDS_COMPLETE_RECORD", "NEEDS_RECORD_RECONCILIATION",
                "NEEDS_SOURCE_AND_IMPACT_EVIDENCE"]
ActionCode = Literal["REVIEW_SNAPSHOT_VERSION", "REQUEST_COMPLETE_RECORD", "RECONCILE_RECORD",
                     "VERIFY_CAPTURE_SOURCE", "VERIFY_ACTOR_AUTHORIZATION", "REVIEW_CLAIM_BINDING",
                     "REVIEW_IMPACT_AND_CONTROLS"]
CHECK_TEXT = {
    "REVIEW_SNAPSHOT_VERSION": "Tinjau versi laporan dan aturan yang terikat pada rekaman ini. Gunakan snapshot baru bila klaim atau aturan berubah; rekaman lama tetap terikat ke versi asal.",
    "REQUEST_COMPLETE_RECORD": "Minta rekaman kontrol normal yang lengkap sesuai format, termasuk urutan event dan metadata aktor yang diperlukan.",
    "RECONCILE_RECORD": "Tinjau ketidaksesuaian terhadap rekaman asli dan dokumentasikan penjelasannya. Unggah rekaman koreksi sebagai rekaman baru; pertahankan rekaman sebelumnya.",
    "VERIFY_CAPTURE_SOURCE": "Periksa dan dokumentasikan asal rekaman serta kaitannya dengan aset dan kondisi yang dilaporkan.",
    "VERIFY_ACTOR_AUTHORIZATION": "Periksa identitas, unit dan kewenangan aktor dengan referensi yang dapat dipercaya; metadata unggahan saja belum cukup.",
    "REVIEW_CLAIM_BINDING": "Cocokkan rekaman dengan klaim utama pada snapshot laporan ini. Lampiran ke laporan tidak otomatis membuktikan kecocokan isinya.",
    "REVIEW_IMPACT_AND_CONTROLS": "Tinjau bukti dampak dan kontrol yang relevan secara manual. Rekaman alur normal saja tidak menetapkan validitas klaim kerentanan.",
}
SUMMARIES = {
    "NEEDS_SNAPSHOT_REVIEW": "Ada versi laporan atau aturan yang lebih baru. Tinjau binding snapshot sebelum memakai rekaman ini untuk keputusan berikutnya.",
    "NEEDS_COMPLETE_RECORD": "Rekaman belum lengkap. Lengkapi bukti terlebih dahulu; kekurangan data tidak menyangkal klaim.",
    "NEEDS_RECORD_RECONCILIATION": "Rekaman mengandung ketidaksesuaian yang perlu ditinjau. Ini belum membuktikan kerentanan atau penyebabnya.",
    "NEEDS_SOURCE_AND_IMPACT_EVIDENCE": "Rekaman konsisten, tetapi sumber, kewenangan aktor, kecocokan klaim dan dampaknya masih perlu diverifikasi.",
}


class Frozen(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class NextAction(Frozen):
    code: ActionCode
    instruction: str = Field(max_length=1000)
    executor: Literal["PROGRAM_ADMIN"] = "PROGRAM_ADMIN"
    automatic: Literal[False] = False


class Binding(Frozen):
    review_id: str
    report_id: str
    report_revision_id: str
    report_revision_number: int = Field(ge=1)
    report_content_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    scope_version_id: str
    business_rules_version: str
    business_rules_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    is_current_report_revision: bool
    is_current_scope: bool


class UntrustedClaim(Frozen):
    primary_claim: str = Field(max_length=2000)
    asset_alias: str | None = Field(max_length=64)
    path: str | None = Field(max_length=2048)
    claim_count: Literal[1] = 1
    category: Literal["BUSINESS_LOGIC"] = "BUSINESS_LOGIC"
    instruction_authority: Literal["NONE"] = "NONE"


class WorkflowContext(Frozen):
    version: Literal["business-evidence-workflow-v1"] = VERSION
    mode: Literal["ADMINISTRATIVE_RECORD_TRIAGE"] = "ADMINISTRATIVE_RECORD_TRIAGE"
    phase: Phase
    summary: str
    binding: Binding
    untrusted_claim: UntrustedClaim
    business_rules: str = Field(max_length=4000)
    record_consistency_status: Literal["CONSISTENT", "INCONSISTENT", "INCOMPLETE"]
    findings: list[Annotated[str, Field(pattern=r"^[A-Z0-9_]{1,80}$")]] = Field(max_length=64)
    next_actions: list[NextAction] = Field(max_length=7)
    evidence_origin: Literal["ADMIN_UPLOADED_UNATTESTED_RECORD"] = "ADMIN_UPLOADED_UNATTESTED_RECORD"
    target_execution_allowed: Literal[False] = False
    model_dispatch_allowed: Literal[False] = False
    vulnerability_verdict: None = None
    ground_truth: None = None


class WorkflowPacket(WorkflowContext):
    context_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


def build(*, binding: Binding, claim: UntrustedClaim, business_rules: str, result: dict) -> dict:
    """Build fixed administrative actions; never derive commands from input text."""
    if result["status"] not in {"CONSISTENT", "INCONSISTENT", "INCOMPLETE"}:
        raise ValueError("WORKFLOW_RESULT_INVALID")
    codes = []
    if not binding.is_current_report_revision or not binding.is_current_scope:
        phase = "NEEDS_SNAPSHOT_REVIEW"
        codes.append("REVIEW_SNAPSHOT_VERSION")
    elif result["status"] == "INCOMPLETE":
        phase = "NEEDS_COMPLETE_RECORD"
    elif result["status"] == "INCONSISTENT":
        phase = "NEEDS_RECORD_RECONCILIATION"
    else:
        phase = "NEEDS_SOURCE_AND_IMPACT_EVIDENCE"
    if result["status"] == "INCOMPLETE":
        codes.append("REQUEST_COMPLETE_RECORD")
    elif result["status"] == "INCONSISTENT":
        codes.append("RECONCILE_RECORD")
    codes += ["VERIFY_CAPTURE_SOURCE", "VERIFY_ACTOR_AUTHORIZATION", "REVIEW_CLAIM_BINDING", "REVIEW_IMPACT_AND_CONTROLS"]
    context = WorkflowContext(phase=phase, summary=SUMMARIES[phase], binding=binding, untrusted_claim=claim,
                              business_rules=business_rules, record_consistency_status=result["status"],
                              findings=result["findings"], next_actions=[NextAction(code=code, instruction=CHECK_TEXT[code]) for code in codes])
    value = context.model_dump(mode="json")
    # This binds context bytes, not the authenticity of the uploaded material.
    return WorkflowPacket(**value, context_sha256=digest(packed(value))).model_dump(mode="json")
