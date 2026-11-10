CREATE TABLE users (
 user_id TEXT PRIMARY KEY, login_name TEXT NOT NULL UNIQUE,
 password_hash TEXT NOT NULL, enabled INTEGER NOT NULL DEFAULT 1 CHECK(enabled IN (0,1))
);
CREATE TABLE sessions (
 session_id_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users,
 csrf_hash TEXT NOT NULL, created_at REAL NOT NULL, expires_at REAL NOT NULL, revoked_at REAL
);
CREATE TABLE programs (
 program_id TEXT PRIMARY KEY, display_name TEXT NOT NULL, active_scope_version_id TEXT,
 authorization_epoch INTEGER NOT NULL DEFAULT 0, enabled INTEGER NOT NULL DEFAULT 1,
 FOREIGN KEY(active_scope_version_id) REFERENCES scope_versions(scope_version_id)
);
CREATE TABLE memberships (
 user_id TEXT NOT NULL REFERENCES users, program_id TEXT NOT NULL REFERENCES programs,
 role TEXT NOT NULL CHECK(role IN ('BUG_HUNTER','PROGRAM_ADMIN')), enabled INTEGER NOT NULL DEFAULT 1,
 PRIMARY KEY(user_id, program_id)
);
CREATE TABLE target_bindings (
 target_id TEXT PRIMARY KEY, program_id TEXT NOT NULL REFERENCES programs,
 asset_alias TEXT NOT NULL, fixed_origin TEXT NOT NULL, profile_json TEXT NOT NULL,
 ready INTEGER NOT NULL DEFAULT 0, dirty INTEGER NOT NULL DEFAULT 0,
 UNIQUE(program_id, asset_alias), UNIQUE(target_id,program_id)
);
CREATE TABLE scope_versions (
 scope_version_id TEXT PRIMARY KEY, program_id TEXT NOT NULL REFERENCES programs,
 version INTEGER NOT NULL, state TEXT NOT NULL CHECK(state IN ('DRAFT','ACTIVE','RETIRED')),
 rules_json TEXT NOT NULL, source_text TEXT NOT NULL, source_hash TEXT NOT NULL,
 source_attachment_id TEXT, activated_by TEXT REFERENCES users, activated_at REAL,
 UNIQUE(program_id,version), UNIQUE(scope_version_id,program_id)
);
CREATE UNIQUE INDEX one_active_scope ON scope_versions(program_id) WHERE state='ACTIVE';
CREATE TABLE conversations (
 conversation_id TEXT PRIMARY KEY, program_id TEXT NOT NULL REFERENCES programs,
 owner_user_id TEXT NOT NULL REFERENCES users, draft_title TEXT NOT NULL DEFAULT '',
 draft_body TEXT NOT NULL DEFAULT '', draft_version INTEGER NOT NULL DEFAULT 0, created_at REAL NOT NULL,
 UNIQUE(conversation_id,program_id,owner_user_id)
);
CREATE TABLE messages (
 message_id TEXT PRIMARY KEY, conversation_id TEXT NOT NULL REFERENCES conversations,
 author_user_id TEXT NOT NULL REFERENCES users, kind TEXT NOT NULL CHECK(kind='USER'),
 body TEXT NOT NULL, created_at REAL NOT NULL
);
CREATE TABLE attachments (
 attachment_id TEXT PRIMARY KEY, program_id TEXT NOT NULL REFERENCES programs,
 owner_user_id TEXT NOT NULL REFERENCES users, conversation_id TEXT REFERENCES conversations,
 purpose TEXT NOT NULL CHECK(purpose IN ('REPORT','GUIDELINE')),
 storage_key TEXT NOT NULL UNIQUE, original_name TEXT NOT NULL, detected_type TEXT NOT NULL,
 byte_size INTEGER NOT NULL CHECK(byte_size<=131072), sha256 TEXT NOT NULL,
 parse_status TEXT NOT NULL CHECK(parse_status='PARSED'), extracted_text TEXT NOT NULL,
 FOREIGN KEY(conversation_id,program_id,owner_user_id)
 REFERENCES conversations(conversation_id,program_id,owner_user_id)
);
CREATE UNIQUE INDEX one_report_attachment ON attachments(conversation_id) WHERE purpose='REPORT';
CREATE TABLE reports (
 report_id TEXT PRIMARY KEY, program_id TEXT NOT NULL REFERENCES programs,
 owner_user_id TEXT NOT NULL REFERENCES users, conversation_id TEXT NOT NULL UNIQUE,
 FOREIGN KEY(conversation_id,program_id,owner_user_id)
 REFERENCES conversations(conversation_id,program_id,owner_user_id),
 UNIQUE(report_id,program_id,owner_user_id)
);
CREATE TABLE report_revisions (
 revision_id TEXT PRIMARY KEY, report_id TEXT NOT NULL REFERENCES reports,
 revision_number INTEGER NOT NULL, draft_version INTEGER NOT NULL,
 title TEXT NOT NULL, body TEXT NOT NULL, attachment_id TEXT REFERENCES attachments,
 attachment_text TEXT NOT NULL DEFAULT '', content_hash TEXT NOT NULL,
 claim_json TEXT NOT NULL, submitted_at REAL NOT NULL,
 UNIQUE(report_id,revision_number), UNIQUE(report_id,draft_version), UNIQUE(revision_id,report_id)
);
CREATE TABLE runs (
 run_id TEXT PRIMARY KEY, program_id TEXT NOT NULL REFERENCES programs,
 report_id TEXT NOT NULL REFERENCES reports, report_revision_id TEXT NOT NULL,
 owner_user_id TEXT NOT NULL REFERENCES users, requested_by TEXT NOT NULL REFERENCES users,
 scope_version_id TEXT, authorization_epoch INTEGER NOT NULL, target_id TEXT,
 primary_claim_id TEXT NOT NULL, execution_mode TEXT NOT NULL CHECK(execution_mode IN ('mock','replay','live')),
 process_status TEXT NOT NULL, queue_status TEXT NOT NULL,
 scope_decision TEXT NOT NULL, capability_decision TEXT NOT NULL,
 model_id TEXT, inference_provider TEXT, prompt_version TEXT NOT NULL DEFAULT 'm1-mock-v1',
 code_revision TEXT NOT NULL DEFAULT '0.1.0', limits_json TEXT NOT NULL,
 created_at REAL NOT NULL, queue_expires_at REAL, started_at REAL, finished_at REAL,
 lease_expires_at REAL, error_code TEXT, counters_json TEXT NOT NULL DEFAULT '{}',
 FOREIGN KEY(report_id,program_id,owner_user_id) REFERENCES reports(report_id,program_id,owner_user_id),
 FOREIGN KEY(report_revision_id,report_id) REFERENCES report_revisions(revision_id,report_id),
 FOREIGN KEY(scope_version_id,program_id) REFERENCES scope_versions(scope_version_id,program_id),
 FOREIGN KEY(target_id,program_id) REFERENCES target_bindings(target_id,program_id)
);
CREATE UNIQUE INDEX one_pending_per_owner ON runs(owner_user_id) WHERE queue_status IN ('QUEUED','LEASED');
CREATE UNIQUE INDEX one_active_job ON runs(queue_status) WHERE queue_status='LEASED';
CREATE TABLE idempotency (
 principal_id TEXT NOT NULL REFERENCES users, program_id TEXT NOT NULL REFERENCES programs,
 operation TEXT NOT NULL, key TEXT NOT NULL, payload_hash TEXT NOT NULL, run_id TEXT NOT NULL REFERENCES runs,
 PRIMARY KEY(principal_id,program_id,operation,key)
);
CREATE TABLE actions (
 action_id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs,
 tool_name TEXT NOT NULL, schema_version INTEGER NOT NULL DEFAULT 1, arguments_json TEXT NOT NULL,
 account_alias TEXT, expected_observation TEXT, policy_result TEXT NOT NULL, policy_reason TEXT NOT NULL,
 started_at REAL NOT NULL, finished_at REAL, UNIQUE(action_id,run_id)
);
CREATE TABLE evidence (
 evidence_id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs,
 action_id TEXT NOT NULL, kind TEXT NOT NULL, captured_at REAL NOT NULL,
 artifact_path TEXT NOT NULL, sha256 TEXT NOT NULL, actor_alias TEXT NOT NULL,
 target_alias TEXT NOT NULL, summary TEXT NOT NULL, provenance_json TEXT NOT NULL,
 redaction_version TEXT NOT NULL DEFAULT 'v1', visibility TEXT NOT NULL DEFAULT 'INTERNAL'
 CHECK(visibility IN ('INTERNAL','HUNTER_SAFE')), published_by TEXT REFERENCES users, published_at REAL,
 FOREIGN KEY(action_id,run_id) REFERENCES actions(action_id,run_id)
);
CREATE TABLE assessments (
 run_id TEXT PRIMARY KEY REFERENCES runs, claim_id TEXT NOT NULL, verdict TEXT NOT NULL
 CHECK(verdict IN ('CONFIRMED','REFUTED','INCONCLUSIVE')),
 raw_model_json TEXT NOT NULL, system_verified_json TEXT NOT NULL,
 review_status TEXT NOT NULL DEFAULT 'PENDING', analyst_override TEXT, reviewer_note TEXT,
 reviewed_by TEXT REFERENCES users, reviewed_at REAL, hunter_summary TEXT,
 publication_status TEXT NOT NULL DEFAULT 'PRIVATE'
);
CREATE TABLE ledger (
 entry_id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs,
 provider_attempt_id TEXT UNIQUE, reserved_idr INTEGER NOT NULL CHECK(reserved_idr>=0),
 actual_idr INTEGER CHECK(actual_idr>=0), status TEXT NOT NULL
 CHECK(status IN ('RESERVED','SETTLED','COST_UNKNOWN','RELEASED')), created_at REAL NOT NULL
);
CREATE TABLE provider_attempts (
 provider_attempt_id TEXT PRIMARY KEY, call_id TEXT NOT NULL, run_id TEXT NOT NULL REFERENCES runs,
 provider_id TEXT NOT NULL, model_id TEXT NOT NULL, status TEXT NOT NULL, error_code TEXT,
 fallback_reason TEXT, usage_json TEXT, created_at REAL NOT NULL
);
CREATE TABLE audit_events (
 event_id TEXT PRIMARY KEY, actor_id TEXT, run_id TEXT REFERENCES runs,
 event_type TEXT NOT NULL, details_json TEXT NOT NULL, created_at REAL NOT NULL
);
CREATE TABLE rate_events (bucket TEXT NOT NULL, event_at REAL NOT NULL);
CREATE INDEX rate_bucket ON rate_events(bucket,event_at);
