-- Text-only evaluation calls share the authoritative application ledger.
CREATE TABLE evaluation_jobs (
 evaluation_id TEXT PRIMARY KEY, freeze_hash TEXT NOT NULL, report_key TEXT NOT NULL,
 arm TEXT NOT NULL CHECK(arm IN ('A','B','SMOKE')), requested_by TEXT NOT NULL REFERENCES users,
 run_id TEXT REFERENCES runs, status TEXT NOT NULL CHECK(status IN ('DISPATCHED','SUCCESS','ERROR')),
 input_json TEXT NOT NULL, config_json TEXT NOT NULL, output_json TEXT, error_code TEXT,
 created_at REAL NOT NULL, finished_at REAL,
 UNIQUE(freeze_hash,report_key,arm)
);
CREATE TABLE ledger_evaluation (
 entry_id TEXT PRIMARY KEY, run_id TEXT REFERENCES runs, provider_attempt_id TEXT UNIQUE,
 reserved_idr INTEGER NOT NULL CHECK(reserved_idr>=0), actual_idr INTEGER CHECK(actual_idr>=0),
 status TEXT NOT NULL CHECK(status IN ('RESERVED','SETTLED','COST_UNKNOWN','RELEASED')),
 created_at REAL NOT NULL, triage_id TEXT REFERENCES text_triages,
 evaluation_id TEXT REFERENCES evaluation_jobs,
 CHECK((run_id IS NOT NULL)+(triage_id IS NOT NULL)+(evaluation_id IS NOT NULL)=1)
);
INSERT INTO ledger_evaluation SELECT *,NULL FROM ledger;
DROP TABLE ledger;
ALTER TABLE ledger_evaluation RENAME TO ledger;
CREATE TABLE provider_attempts_evaluation (
 provider_attempt_id TEXT PRIMARY KEY, call_id TEXT NOT NULL, run_id TEXT REFERENCES runs,
 provider_id TEXT NOT NULL, model_id TEXT NOT NULL, status TEXT NOT NULL, error_code TEXT,
 fallback_reason TEXT, usage_json TEXT, created_at REAL NOT NULL,
 triage_id TEXT REFERENCES text_triages, metadata_json TEXT, redacted_response TEXT, finished_at REAL,
 evaluation_id TEXT REFERENCES evaluation_jobs,
 CHECK((run_id IS NOT NULL)+(triage_id IS NOT NULL)+(evaluation_id IS NOT NULL)=1)
);
INSERT INTO provider_attempts_evaluation SELECT *,NULL FROM provider_attempts;
DROP TABLE provider_attempts;
ALTER TABLE provider_attempts_evaluation RENAME TO provider_attempts;
