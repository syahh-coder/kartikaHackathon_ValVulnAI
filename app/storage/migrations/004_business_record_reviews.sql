-- Manual uploaded records; never worker observations or vulnerability assessments.
CREATE TABLE business_record_reviews (
 review_id TEXT PRIMARY KEY,
 report_id TEXT NOT NULL REFERENCES reports,
 report_revision_id TEXT NOT NULL,
 scope_version_id TEXT NOT NULL REFERENCES scope_versions,
 imported_by TEXT NOT NULL REFERENCES users,
 imported_at REAL NOT NULL,
 record_path TEXT NOT NULL UNIQUE,
 record_sha256 TEXT NOT NULL,
 byte_size INTEGER NOT NULL CHECK(byte_size BETWEEN 1 AND 131072),
 result_json TEXT NOT NULL,
 provenance_json TEXT NOT NULL,
 review_status TEXT NOT NULL DEFAULT 'PENDING' CHECK(review_status IN ('PENDING','REVIEWED')),
 reviewer_note TEXT,
 reviewed_by TEXT REFERENCES users,
 reviewed_at REAL,
 publication_status TEXT NOT NULL DEFAULT 'PRIVATE' CHECK(publication_status IN ('PRIVATE','PUBLISHED')),
 hunter_summary TEXT,
 UNIQUE(report_revision_id,record_sha256),
 FOREIGN KEY(report_revision_id,report_id) REFERENCES report_revisions(revision_id,report_id)
);
CREATE INDEX business_reviews_report ON business_record_reviews(report_id,imported_at);
