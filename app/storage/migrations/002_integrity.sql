CREATE TABLE login_nonces (nonce_hash TEXT PRIMARY KEY, csrf_hash TEXT NOT NULL, expires_at REAL NOT NULL);
CREATE TRIGGER immutable_report_revision BEFORE UPDATE ON report_revisions
BEGIN SELECT RAISE(ABORT, 'Report revision is immutable'); END;
CREATE TRIGGER immutable_scope_rules BEFORE UPDATE OF rules_json,source_text,source_hash,program_id,version ON scope_versions
BEGIN SELECT RAISE(ABORT, 'Scope snapshot is immutable'); END;
