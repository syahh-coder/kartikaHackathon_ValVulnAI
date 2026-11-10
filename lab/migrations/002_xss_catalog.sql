ALTER TABLE users ADD COLUMN display_name TEXT NOT NULL DEFAULT 'Pemohon sintetis';
CREATE TABLE request_reviewers (
    request_id TEXT NOT NULL REFERENCES requests(id),
    reviewer_id TEXT NOT NULL REFERENCES users(id),
    PRIMARY KEY(request_id, reviewer_id)
);
CREATE TABLE catalog_items (
    id TEXT PRIMARY KEY, owner_id TEXT NOT NULL REFERENCES users(id),
    note TEXT NOT NULL, description TEXT NOT NULL
);
CREATE TABLE request_details (
    request_id TEXT PRIMARY KEY REFERENCES requests(id), reason TEXT NOT NULL
);
CREATE TABLE comments (
    id TEXT PRIMARY KEY, request_id TEXT NOT NULL REFERENCES requests(id),
    author_id TEXT NOT NULL REFERENCES users(id), body TEXT NOT NULL
);
CREATE TABLE suppliers (
    id TEXT PRIMARY KEY, owner_id TEXT NOT NULL REFERENCES users(id),
    name TEXT NOT NULL, code TEXT NOT NULL
);
