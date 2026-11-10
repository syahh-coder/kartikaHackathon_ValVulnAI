ALTER TABLE runs ADD COLUMN tool_execution_mode TEXT NOT NULL DEFAULT 'NONE' CHECK(tool_execution_mode IN ('NONE','LAB'));
ALTER TABLE runs ADD COLUMN target_snapshot_id TEXT;
ALTER TABLE runs ADD COLUMN worker_boot_id TEXT;
ALTER TABLE target_bindings ADD COLUMN dirty_run_id TEXT REFERENCES runs(run_id);
ALTER TABLE target_bindings ADD COLUMN maintenance INTEGER NOT NULL DEFAULT 0 CHECK(maintenance IN (0,1));
ALTER TABLE target_bindings ADD COLUMN snapshot_id TEXT;
CREATE TABLE handoff_actions (
 action_id TEXT PRIMARY KEY REFERENCES actions(action_id),run_id TEXT NOT NULL REFERENCES runs,
 action_seq INTEGER NOT NULL,envelope_json TEXT NOT NULL,envelope_hash TEXT NOT NULL,
 status TEXT NOT NULL CHECK(status IN ('ISSUED','RECEIVED','UNKNOWN')),
 observation_json TEXT,expires_at REAL NOT NULL,
 UNIQUE(run_id,action_seq),FOREIGN KEY(action_id,run_id) REFERENCES actions(action_id,run_id)
);
CREATE TRIGGER immutable_handoff BEFORE UPDATE OF envelope_json,envelope_hash,run_id,action_seq ON handoff_actions
BEGIN SELECT RAISE(ABORT,'Handoff envelope is immutable'); END;
