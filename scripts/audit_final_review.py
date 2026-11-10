"""Collect actual local review checks; no provider/target calls, GT writes or publication."""
import argparse
import hashlib
import json
import re
import struct
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile

from evaluator.functional_v2 import read_manifest, readiness
from evaluator.text_benchmark import source_hash
from scripts.build_review_package import selected
from scripts.r4_container_check import ROOT, active_snapshot

REPORTS = ("runner-initial.xml", "context-retest.xml", "runner-integration.xml", "runner-integration-retest.xml",
           "runner-final.xml", "affected-integration.xml", "freeze-final.xml", "accounting-final.xml", "smoke-proof-final.xml")
DOCS = ("AGENTS.md", "README.md", "plan.md", "docs/execution-prompt.md", "docs/implementation.md", "docs/evaluation.md",
        "docs/architecture.md", "docs/runtime.md", "docs/submission-scope.md", "docs/distribution.md", "docs/submission-checklist.md",
        "docs/third-party.md", "docs/final-review.md", "docs/r3-r4-verification.md", "docs/r3-runbook.md", "docs/review-quickstart.md",
        "submission/README.md", "submission/demo-storyboard.md", "submission/release-draft.md", "submission/form-draft.md",
        "artifacts/r3/review-v1/review-guide.md")


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def audit(archive: Path, output: Path):
    if output.exists(): raise ValueError("Output exists")
    latest, runs = {}, []
    for filename in REPORTS:
        xml = ET.parse(ROOT/"artifacts/r3"/filename)
        rows = list(xml.iter("testcase"))
        failures = 0
        for row in rows:
            passed = row.find("failure") is None and row.find("error") is None and row.find("skipped") is None
            latest[(row.get("classname"),row.get("name"))] = passed
            failures += not passed
        runs.append({"file":filename,"tests":len(rows),"failures":failures})
    assert all(latest.values())
    missing, links = [], 0
    for name in DOCS:
        path = ROOT/name
        text = path.read_text(encoding="utf-8")
        assert len(re.findall(r"^```",text,re.MULTILINE))%2 == 0, name
        for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)",text):
            target = target.strip("<>").split("#",1)[0]
            if not target or re.match(r"^[a-z]+://",target): continue
            resolved = (path.parent/target).resolve()
            links += 1
            if not resolved.exists() and resolved != output.resolve(): missing.append({"file":name,"target":target})
    assert not missing, missing
    worksheet = readiness(read_manifest(ROOT/"artifacts/r3/candidates-v1"))
    assert worksheet["human_accepted"] == 0 and not worksheet["human_gt"]
    pending = load(ROOT/"artifacts/r3/review-v1/outcomes.pending.json")
    assert len(pending["slots"])==40 and all(r["status"]=="NOT_STARTED" and r["cost_idr"] is None for r in pending["slots"])
    proposals=load(ROOT/"artifacts/r3/review-v1/proposals.private.json")
    assert all(c["proposed_label"] is None and not c["accepted_by_human"] for c in proposals["cases"])
    thumbnail=(ROOT/"submission/thumbnail.png").read_bytes()
    width,height=struct.unpack(">II",thumbnail[16:24])
    assert (width,height)==(1200,630) and len(thumbnail)<=500000
    pdf=(ROOT/"submission/slides.pdf").read_bytes()
    pages=len(re.findall(rb"/Type\s*/Page\b",pdf))
    assert pages==9
    screenshots=list((ROOT/"submission/screenshots").glob("*.png"))
    assert len(screenshots)==3
    video=(ROOT/"submission/demo-preview-MOCK.webm").read_bytes()
    assert video.startswith(b"\x1a\x45\xdf\xa3")
    capture=load(ROOT/"artifacts/r4/capture-result.json")
    assert capture["status"]=="PASS" and not capture["page_errors"] and capture["qa"]["real_provider_requests"]==capture["qa"]["target_requests"]==0
    container=load(ROOT/"artifacts/r4/container-check-retest.json")
    preview=load(ROOT/"artifacts/r4/preview-check.json")
    active=active_snapshot()
    assert container["status"]==preview["status"]=="PASS" and container["active_before"]==preview["active_after"]==active
    archive_check=load(ROOT/"artifacts/r4/archive-check.json")
    digest=hashlib.sha256(archive.read_bytes()).hexdigest()
    assert archive_check["status"]=="PASS" and archive_check["archive_sha256"]==digest
    assert (archive.parent/(archive.name+".sha256")).read_text(encoding="ascii").split()[0]==digest
    with ZipFile(archive) as z:
        manifest=json.loads(z.read("valvuln-ai/PACKAGE-MANIFEST.json"))
        current={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in selected(ROOT)}
        assert set(current)==set(manifest["files"])
        assert all(current[k]==v["sha256"] for k,v in manifest["files"].items())
        assert all(not n.startswith("valvuln-ai/artifacts/") and "/.local-data/" not in n and not n.endswith("/.env") for n in z.namelist())
    proof=subprocess.run(["docker","run","--rm","--network","none","--entrypoint","python","valvuln-review-evaluator:20261107",
                          "-c","from evaluator.text_benchmark import source_hash;print(source_hash())"],capture_output=True,text=True,check=True,timeout=30)
    assert proof.stdout.strip()==source_hash()
    invalid=subprocess.run([sys.executable,"-m","evaluator.text_benchmark","freeze","--output",str(ROOT/"artifacts/r3/should-not-exist.json")],
                           cwd=ROOT,capture_output=True,text=True)
    assert invalid.returncode==2 and not (ROOT/"artifacts/r3/should-not-exist.json").exists()
    result={"status":"READY_FOR_REVIEW_WITH_PENDING_INPUTS","code_tested":True,"live_verified":False,"frozen":False,"evaluated":False,
            "published":False,"submitted":False,"unique_targeted_tests":len(latest),"all_latest_results_pass":True,"test_runs":runs,
            "docs_checked":len(DOCS),"local_links_checked":links,"missing_local_links":[],"fences_balanced":True,
            "archive":{"path":str(archive.relative_to(ROOT)),"sha256":digest,"bytes":archive.stat().st_size,"files":len(current),
                       "matches_current_selected_worktree":True,"extraction_http_restart":"PASS","dependency_install_from_scratch":False},
            "assets":{"thumbnail":{"width":width,"height":height,"bytes":len(thumbnail)},"slide_pages":pages,"screenshots":len(screenshots),
                      "video_preview_bytes":len(video),"video_status":"DRAFT_MOCK_PREVIEW_WITHOUT_NARRATION"},
            "source_hash_host_and_evaluator_image":source_hash(),"invalid_cli_args_fail_before_dispatch":True,
            "active_data_preserved":True,"active_runs":active["data"]["runs"]["count"],"active_ledger_rows":active["data"]["ledger"]["count"],
            "human_accepted":0,"human_gt":0,"case_bound_final_contexts":0,"real_scheduled_slots":40,"real_started_slots":0,"metrics":None,
            "model_provider_requests_this_batch":0,"target_requests_this_batch":0,"actual_configuration_status":"CONFIGURATION_REQUIRED"}
    output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({"status":result["status"],"unique_targeted_tests":len(latest),"local_links_checked":links,"archive_sha256":digest}))


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("archive",type=Path);parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args();audit(args.archive.resolve(),args.output.resolve())
