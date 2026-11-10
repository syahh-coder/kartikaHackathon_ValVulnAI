-- Independent text requests: never insert a lab run to account for inference.
CREATE TABLE text_triages (
 triage_id TEXT PRIMARY KEY, conversation_id TEXT NOT NULL REFERENCES conversations,
 program_id TEXT NOT NULL REFERENCES programs, owner_user_id TEXT NOT NULL REFERENCES users,
 requested_by TEXT NOT NULL REFERENCES users, session_hash TEXT NOT NULL,
 draft_version INTEGER NOT NULL, scope_version_id TEXT REFERENCES scope_versions,
 authorization_epoch INTEGER NOT NULL, mode TEXT NOT NULL CHECK(mode IN ('mock','live','replay')),
 status TEXT NOT NULL CHECK(status IN ('PENDING','RUNNING','SUCCEEDED','FAILED','CANCELLED')),
 error_code TEXT, idempotency_key TEXT NOT NULL, input_hash TEXT NOT NULL,
 prompt_version TEXT NOT NULL, schema_version TEXT NOT NULL, input_json TEXT NOT NULL,
 config_json TEXT NOT NULL, output_json TEXT, created_at REAL NOT NULL, finished_at REAL,
 UNIQUE(requested_by,conversation_id,idempotency_key)
);
CREATE UNIQUE INDEX one_active_text_triage ON text_triages((1)) WHERE status IN ('PENDING','RUNNING');

-- Preserve every old row and its identifiers. No other table references these tables.
CREATE TABLE ledger_text (
 entry_id TEXT PRIMARY KEY, run_id TEXT REFERENCES runs,
 provider_attempt_id TEXT UNIQUE, reserved_idr INTEGER NOT NULL CHECK(reserved_idr>=0),
 actual_idr INTEGER CHECK(actual_idr>=0), status TEXT NOT NULL
 CHECK(status IN ('RESERVED','SETTLED','COST_UNKNOWN','RELEASED')), created_at REAL NOT NULL,
 triage_id TEXT REFERENCES text_triages,
 CHECK((run_id IS NOT NULL) != (triage_id IS NOT NULL))
);
INSERT INTO ledger_text SELECT *,NULL FROM ledger;
DROP TABLE ledger;
ALTER TABLE ledger_text RENAME TO ledger;

CREATE TABLE provider_attempts_text (
 provider_attempt_id TEXT PRIMARY KEY, call_id TEXT NOT NULL, run_id TEXT REFERENCES runs,
 provider_id TEXT NOT NULL, model_id TEXT NOT NULL, status TEXT NOT NULL, error_code TEXT,
 fallback_reason TEXT, usage_json TEXT, created_at REAL NOT NULL,
 triage_id TEXT REFERENCES text_triages, metadata_json TEXT, redacted_response TEXT, finished_at REAL,
 CHECK((run_id IS NOT NULL) != (triage_id IS NOT NULL))
);
INSERT INTO provider_attempts_text SELECT *,NULL,NULL,NULL,NULL FROM provider_attempts;
DROP TABLE provider_attempts;
ALTER TABLE provider_attempts_text RENAME TO provider_attempts;
