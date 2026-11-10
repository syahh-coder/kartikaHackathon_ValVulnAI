"""Private functional-v2 preparation/freeze/dispatch CLI. Text only, never executes a target."""
import argparse
import asyncio
import getpass
import json
import time
from pathlib import Path

from app.agent.ledger import budget_used
from app.auth import Principal, member, passwords
from app.common import AppError, packed, rate_limit, uid
from app.config import Settings
from app.providers.contracts import ProviderFailure
from app.providers.text_provider import input_token_bound, require_configuration, secret
from app.storage.db import Database, all_rows, one
from evaluator.functional_v2 import (DraftManifest, EvaluationError, Outcome, Outcomes, read_document,
                                     read_manifest, readiness, schedule, score, write_new)
from evaluator.text_context import CONTRACT, PROMPT_VERSION, context_for, prompt, sha
from evaluator.text_dispatch import configuration, dispatch

ROOT = Path(__file__).resolve().parents[1]


def source_hash() -> str:
    files = sorted(p for folder in ("app", "boundary", "evaluator") for p in (ROOT/folder).rglob("*")
                   if p.suffix in {".py", ".sql"} and "__pycache__" not in p.parts)
    files += [ROOT/name for name in ("requirements.lock", "requirements-worker.lock", "pyproject.toml")]
    return sha(packed({p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in files}))


def config_readiness(config: Settings) -> dict:
    # Called once by the preparation command; never print secret values or their lengths.
    c = config
    required = {"live_mode": c.triage_mode == "live", ("azure_key" if c.triage_provider == "azure" else "openrouter_key"): bool(secret(c).strip()),
                "fixed_model": bool(c.triage_model), "provider_slug": bool(c.triage_provider_slug),
                "provider_name": bool(c.triage_provider_name), "access_verified": c.triage_access_verified,
                "token_bound_verified": c.triage_token_bound_verified, "price_snapshot": bool(c.triage_price_snapshot),
                "prompt_price": c.triage_prompt_usd_per_million is not None,
                "completion_price": c.triage_completion_usd_per_million is not None,
                "usd_to_idr": c.triage_usd_to_idr is not None, "reservation": c.triage_reservation_idr > 0}
    if c.triage_provider == "azure":
        required.update({"azure_endpoint": bool(c.azure_endpoint), "azure_expected_model": bool(c.azure_expected_model),
                         "azure_api_capabilities_verified": c.azure_api_capabilities_verified})
    valid = False
    if all(required.values()):
        try:
            require_configuration(c)
            valid = True
        except ProviderFailure:
            pass
    return {"status": "CONFIGURED_NOT_VERIFIED" if valid else "CONFIGURATION_REQUIRED",
            "requirements_present": required, "live_verified": False, "provider_requests": 0}


async def authenticate(db, login: str) -> Principal:
    password = getpass.getpass("Password admin lokal (tidak disimpan): ")
    async with db.transaction() as conn:
        await rate_limit(conn, "evaluation-login:"+login, 5, 60)
        row = await one(conn, "SELECT * FROM users WHERE login_name=? AND enabled=1", (login,))
        valid = bool(row and passwords.verify(password, row["password_hash"]))
    if not valid:
        raise EvaluationError("ADMIN_AUTH_REQUIRED")
    return Principal(row["user_id"], login, "local-operator")


async def contexts(db, config, user, packet: Path, manifest, bindings: dict) -> list[dict]:
    if set(bindings) != {c.report_id for c in manifest.cases} or any(not isinstance(v, str) for v in bindings.values()):
        raise EvaluationError("EXACT_CASE_RUN_BINDINGS_REQUIRED")
    result = []
    async with db.transaction() as conn:
        for case in manifest.cases:
            text = (packet/case.report_file).read_text(encoding="utf-8")
            result.append(await context_for(conn, config.data_dir, user, case, text, bindings[case.report_id],
                                           secret(config)))
    return result


def check_case_gt(case, context):
    gt, binding = case.ground_truth, context["binding"]
    rules = context["A"]["public_rules"]
    rules_version = str(rules["rules"].get("business_rules_version") or rules["version"])
    if (not gt or gt.target_snapshot != binding["target_snapshot_id"] or gt.scope_version != binding["scope_version_id"] or
            gt.rules_version != rules_version):
        raise EvaluationError("GT_CONTEXT_BINDING_INVALID")


async def freeze(db, config, user, packet, manifest, bound_contexts):
    if not readiness(manifest)["gt_worksheet_complete"]:
        raise EvaluationError("HUMAN_GT_REQUIRED")
    require_configuration(config)
    if config.triage_mode != "live":
        raise EvaluationError("CONFIGURATION_REQUIRED")
    if [c["report_id"] for c in bound_contexts] != [c.report_id for c in manifest.cases]:
        raise EvaluationError("CONTEXT_SET_MISMATCH")
    current = await contexts(db, config, user, packet, manifest,
                             {c["report_id"]: c["binding"]["run_id"] for c in bound_contexts})
    if current != bound_contexts:
        raise EvaluationError("CONTEXT_CHANGED")
    for case, ctx in zip(manifest.cases, current):
        check_case_gt(case, ctx)
        for arm in ("A", "B"):
            if input_token_bound(config, prompt(ctx, arm)[0], **CONTRACT) > 8192:
                raise EvaluationError("CONTEXT_LIMIT")
    cfg = configuration(config)
    async with db.connect() as conn:
        proof = await one(conn, "SELECT j.evaluation_id,j.output_json,l.status ledger_status,l.actual_idr FROM evaluation_jobs j "
                          "JOIN ledger l USING(evaluation_id) WHERE j.arm='SMOKE' AND j.status='SUCCESS' "
                          "AND j.config_json=? AND j.freeze_hash=? ORDER BY j.created_at DESC LIMIT 1", (packed(cfg), source_hash()))
        outcome = json.loads(proof["output_json"]) if proof and proof["output_json"] else {}
        if (not proof or proof["ledger_status"] != "SETTLED" or outcome.get("status") != "SUCCESS" or
                outcome.get("cost_idr") is None or outcome.get("cost_idr") != proof["actual_idr"] or
                outcome.get("input_tokens") is None or outcome.get("output_tokens") is None):
            raise EvaluationError("LIVE_SMOKE_REQUIRED")
        if await budget_used(conn) + len(manifest.cases)*2*config.triage_reservation_idr > config.budget_idr:
            raise EvaluationError("WHOLE_SCHEDULE_RESERVATION_REQUIRED")
    payload = {"protocol": "functional-v2", "status": "FROZEN_PRIVATE", "created_at": time.time(),
               "manifest": manifest.model_dump(), "contexts": current, "configuration": cfg,
               "source_hash": source_hash(), "contract": CONTRACT, "live_smoke_evaluation_id": proof["evaluation_id"],
               "order": [[c.report_id, arm] for c in manifest.cases for arm in ("A", "B")],
               "error_policy": "One attempt per slot. Preserve failure/unknown cost. No fallback, retry or result selection."}
    return payload | {"freeze_hash": sha(packed(payload))}


def validate_freeze(value, config):
    body = {k: v for k, v in value.items() if k != "freeze_hash"}
    if (value.get("status") != "FROZEN_PRIVATE" or value.get("freeze_hash") != sha(packed(body)) or
            value.get("source_hash") != source_hash() or value.get("configuration") != configuration(config) or
            value.get("contract") != CONTRACT):
        raise EvaluationError("FREEZE_OR_CONFIGURATION_CHANGED")
    manifest = DraftManifest.model_validate(value["manifest"])
    if not readiness(manifest)["gt_worksheet_complete"]:
        raise EvaluationError("HUMAN_GT_REQUIRED")
    expected = [[c.report_id, a] for c in manifest.cases for a in ("A", "B")]
    if value["order"] != expected or [c["report_id"] for c in value["contexts"]] != [c.report_id for c in manifest.cases]:
        raise EvaluationError("FROZEN_SCHEDULE_INVALID")
    return manifest


async def run(db, config, user, packet, frozen, output: Path):
    manifest = validate_freeze(frozen, config)
    # Preserve output folder; existing schedule entries in DB are never dispatched again.
    output.mkdir(parents=True, exist_ok=False)
    frozen_hash = frozen["freeze_hash"]
    terminal_error = None
    async with db.connect() as conn:
        unresolved = await one(conn, "SELECT 1 FROM ledger l JOIN evaluation_jobs j USING(evaluation_id) "
                               "WHERE j.freeze_hash=? AND l.status IN ('RESERVED','COST_UNKNOWN')", (frozen_hash,))
    if unresolved:
        return await export_results(db, frozen, output, "PRIOR_COST_OR_OUTCOME_UNKNOWN_REVIEW_REQUIRED")
    for case, ctx in zip(manifest.cases, frozen["contexts"]):
        async def guard(conn):
            actual = await context_for(conn, config.data_dir, user, case, (packet/case.report_file).read_text(encoding="utf-8"),
                                       ctx["binding"]["run_id"], secret(config))
            if actual != ctx:
                raise EvaluationError("FROZEN_CONTEXT_CHANGED")
            if frozen["source_hash"] != source_hash() or frozen["configuration"] != configuration(config):
                raise EvaluationError("FROZEN_CONFIGURATION_CHANGED")
        for arm in ("A", "B"):
            async with db.connect() as conn:
                previous = await one(conn, "SELECT 1 FROM evaluation_jobs WHERE freeze_hash=? AND report_key=? AND arm=?",
                                     (frozen_hash, case.report_id, arm))
            if previous:
                continue
            try:
                text, refs = prompt(ctx, arm)
                result = await dispatch(db, config, user, freeze_hash=frozen_hash, report_key=case.report_id, arm=arm,
                                        text=text, references=refs, guard=guard, run_id=ctx["binding"]["run_id"])
                if result["cost_idr"] is None or result["error_code"] in {"PROVIDER_DRIFT", "AUTH_ERROR", "QUOTA_EXHAUSTED", "COST_EXCEEDS_RESERVATION"}:
                    terminal_error = result["error_code"] or "COST_UNKNOWN_REVIEW_REQUIRED"
                    break
            except (EvaluationError, ProviderFailure, AppError) as exc:
                terminal_error = getattr(exc, "code", str(exc))
                break
        if terminal_error:
            break
    return await export_results(db, frozen, output, terminal_error)


async def export_results(db, frozen, output, terminal_error=None):
    manifest = DraftManifest.model_validate(frozen["manifest"])
    outcomes = schedule(manifest)
    records = []
    async with db.connect() as conn:
        for slot in outcomes.slots:
            row = await one(conn, "SELECT j.*,l.status accounting_status,l.actual_idr FROM evaluation_jobs j "
                            "LEFT JOIN ledger l USING(evaluation_id) WHERE j.freeze_hash=? AND j.report_key=? AND j.arm=?",
                            (frozen["freeze_hash"], slot.report_id, slot.arm))
            if not row:
                continue
            value = json.loads(row["output_json"]) if row["output_json"] else {
                "status": "ERROR", "error_code": "INTERRUPTED_OUTCOME_UNKNOWN", "attempts": 1,
                "cost_idr": None, "raw_response_reference": "application-db:evaluation_jobs/"+row["evaluation_id"]}
            value["cost_idr"] = row["actual_idr"] if row["accounting_status"] == "SETTLED" else None
            value["accounting_status"] = row["accounting_status"]
            records.append({"report_id": slot.report_id, "arm": slot.arm, **value})
            slot.status, slot.error_code, slot.attempts = value["status"], value.get("error_code"), 1
            slot.prediction = value["prediction"]["prediction"] if value.get("prediction") else None
            for key in ("cost_idr", "input_tokens", "output_tokens", "elapsed_seconds", "raw_response_reference"):
                setattr(slot, key, value.get(key))
    outcomes = Outcomes.model_validate(outcomes.model_dump())
    summary = score(manifest, outcomes)
    summary.update(status="APPLICATION_LEDGER_RECORD_SCORING", freeze_hash=frozen["freeze_hash"],
                   live_verified=any(r.get("status") == "SUCCESS" for r in records),
                   evaluated=all(r.status != "NOT_STARTED" for r in outcomes.slots),
                   benchmark_claim_allowed=False, terminal_error=terminal_error,
                   review_required="Check provenance, all attempts, reconciled costs and completeness before any benchmark claim.")
    write_new(output/"outcomes.json", outcomes.model_dump())
    write_new(output/"raw-records.private.json", {"records": records})
    write_new(output/"report.json", summary)
    return summary


async def recover_interrupted(db, config, user):
    """Explicitly close expired dispatch records, retaining the full reservation. Never sends a request."""
    recovered = []
    async with db.transaction() as conn:
        rows = await all_rows(conn, "SELECT * FROM evaluation_jobs WHERE status='DISPATCHED'")
        for row in rows:
            frozen_config = json.loads(row["config_json"])
            if time.time() < row["created_at"] + frozen_config["timeout_seconds"] + 60:
                raise EvaluationError("DISPATCH_MAY_STILL_BE_ACTIVE")
            if row["run_id"]:
                run = await one(conn, "SELECT program_id FROM runs WHERE run_id=?", (row["run_id"],))
                await member(conn, user, run[0], admin=True)
            elif row["requested_by"] != user.user_id:
                raise EvaluationError("SMOKE_OWNER_REQUIRED")
            await conn.execute("UPDATE ledger SET status='COST_UNKNOWN' WHERE evaluation_id=? AND status='RESERVED'", (row["evaluation_id"],))
            await conn.execute("UPDATE provider_attempts SET status='ERROR',error_code='INTERRUPTED_OUTCOME_UNKNOWN',finished_at=? "
                               "WHERE evaluation_id=? AND status='DISPATCHED'", (time.time(), row["evaluation_id"]))
            await conn.execute("UPDATE evaluation_jobs SET status='ERROR',error_code='INTERRUPTED_OUTCOME_UNKNOWN',finished_at=? "
                               "WHERE evaluation_id=?", (time.time(), row["evaluation_id"]))
            recovered.append(row["evaluation_id"])
    return {"status": "INTERRUPTED_RECORDS_CLOSED", "evaluation_ids": recovered,
            "reservations_retained": True, "provider_requests": 0, "replay_allowed": False}


def simulate(packet: Path, output: Path):
    manifest = read_manifest(packet)
    output.mkdir(parents=True, exist_ok=False)
    rows, records = [], []
    for case in manifest.cases:
        for arm in ("A", "B"):
            raw = {"prediction": "ABSTAIN", "reason": "SIMULATION_ONLY: no model or bound target observations.", "references": ["REPORT"]}
            from evaluator.functional_v2 import parse_prediction
            parsed = parse_prediction(packed(raw), {"REPORT", "RULES"})
            ref = f"simulation.raw.json#{case.report_id}/{arm}"
            rows.append(Outcome(report_id=case.report_id, arm=arm, status="SUCCESS", prediction=parsed.prediction,
                                attempts=1, cost_idr=0, input_tokens=0, output_tokens=0, raw_response_reference=ref))
            records.append({"report_id": case.report_id, "arm": arm, "raw": raw, "origin": "SIMULATION"})
    write_new(output/"simulation.outcomes.json", Outcomes(origin="SIMULATION", slots=rows).model_dump())
    write_new(output/"simulation.raw.json", {"origin": "SIMULATION", "records": records})
    result = {"status": "SIMULATION_ONLY", "scheduled_slots": len(rows), "schema_valid_responses": len(rows),
              "provider_requests": 0, "target_requests": 0, "live_verified": False, "frozen": False,
              "evaluated": False, "metrics": None, "gt_worksheet": readiness(manifest)}
    write_new(output/"simulation.report.json", result)
    return result


async def main_async(args):
    if args.output and args.output.exists():
        raise EvaluationError("OUTPUT_ALREADY_EXISTS")
    if args.output and not args.output.parent.is_dir():
        raise EvaluationError("OUTPUT_PARENT_REQUIRED")
    if args.operation == "simulate":
        return simulate(args.packet, args.output)
    config = Settings()
    if args.operation == "configuration":
        result = config_readiness(config)
        if args.output:
            write_new(args.output, result)
        return result
    # Never create a new accounting database to get a fresh budget. Migration is a separate app-start step.
    if not config.db_path.is_file():
        raise EvaluationError("AUTHORITATIVE_APPLICATION_DB_REQUIRED")
    db = Database(config.db_path)
    async with db.connect() as conn:
        if not await one(conn, "SELECT 1 FROM schema_versions WHERE version='006_text_evaluation.sql'"):
            raise EvaluationError("APPLICATION_SCHEMA_006_REQUIRED")
    user = await authenticate(db, args.admin_login)
    if args.operation == "recover":
        result = await recover_interrupted(db, config, user)
        write_new(args.output, result)
        return result
    if args.operation == "smoke":
        if not args.program_id:
            raise EvaluationError("PROGRAM_REQUIRED")
        async def guard(conn):
            await member(conn, user, args.program_id, admin=True)
        result = await dispatch(db, config, user, freeze_hash=source_hash(), report_key=uid(), arm="SMOKE",
                                text=packed({"report": {"reference": "REPORT", "text": "Development smoke: insufficient information."},
                                             "public_rules": {"reference": "RULES", "rules": "No target interaction authorized."}}),
                                references={"REPORT", "RULES"}, guard=guard)
        if result["status"] == "SUCCESS" and (result["cost_idr"] is None or result["input_tokens"] is None or result["output_tokens"] is None):
            async with db.transaction() as conn:
                await conn.execute("UPDATE evaluation_jobs SET status='ERROR',error_code='SMOKE_USAGE_OR_COST_UNKNOWN' WHERE evaluation_id=?",
                                   (result["evaluation_id"],))
            result["live_verified"] = False
        else:
            result["live_verified"] = result["status"] == "SUCCESS"
        write_new(args.output, result)
        return {"status": result["status"], "live_verified": result["live_verified"]}
    if args.operation == "export":
        frozen = read_document(args.freeze)
        validate_freeze(frozen, config)
        args.output.mkdir(parents=True, exist_ok=False)
        # Require current program administration before exporting private records.
        async with db.connect() as conn:
            for ctx in frozen["contexts"]:
                await member(conn, user, ctx["binding"]["program_id"], admin=True)
        return await export_results(db, frozen, args.output)
    manifest = read_manifest(args.packet, args.manifest)
    if args.operation == "contexts":
        value = await contexts(db, config, user, args.packet, manifest, read_document(args.bindings))
        write_new(args.output, {"contexts": value})
        return {"status": "BOUND_CONTEXTS_EXPORTED", "cases": len(value)}
    if args.operation == "freeze":
        value = await freeze(db, config, user, args.packet, manifest, read_document(args.contexts)["contexts"])
        write_new(args.output, value)
        return {"status": "FROZEN_PRIVATE", "freeze_hash": value["freeze_hash"]}
    return await run(db, config, user, args.packet, read_document(args.freeze), args.output)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["configuration", "contexts", "smoke", "freeze", "run", "export", "simulate", "recover"])
    parser.add_argument("--packet", type=Path, default=Path("artifacts/r3/candidates-v1"))
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--bindings", type=Path)
    parser.add_argument("--contexts", type=Path)
    parser.add_argument("--freeze", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--admin-login", default="admin")
    parser.add_argument("--program-id")
    args = parser.parse_args(argv)
    required = {"contexts": ("bindings",), "freeze": ("contexts", "manifest"),
                "run": ("freeze",), "export": ("freeze",), "smoke": ("program_id",)}
    for field in required.get(args.operation, ()):
        if getattr(args, field) is None:
            parser.error("--"+field.replace("_", "-")+" is required for "+args.operation)
    if args.operation != "configuration" and not args.output:
        parser.error("--output is required; existing files/directories are never overwritten")
    try:
        result = asyncio.run(main_async(args))
        print(json.dumps(result, ensure_ascii=False, allow_nan=False))
        return 2 if result.get("status") in {"CONFIGURATION_REQUIRED", "ERROR"} else 0
    except (EvaluationError, AppError, ProviderFailure) as exc:
        print(json.dumps({"status": "ERROR", "error_code": getattr(exc, "code", str(exc)),
                          "detail": "No fallback; inspect the named prerequisite. Dispatched attempts remain in the application ledger."}))
        return 2
    except (ValueError, TypeError, KeyError, OSError):
        print(json.dumps({"status": "ERROR", "error_code": "EVALUATION_PREREQUISITE_OR_INPUT_INVALID",
                          "detail": "Check private inputs, admin access, schema 006, binding, freeze and configuration; no fallback."}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
