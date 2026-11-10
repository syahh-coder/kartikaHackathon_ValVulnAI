CREATE TABLE upload_blobs (
    storage_key TEXT PRIMARY KEY, content BLOB NOT NULL
);
CREATE TABLE uploads (
    id TEXT PRIMARY KEY, request_id TEXT NOT NULL REFERENCES requests(id),
    uploader_id TEXT NOT NULL REFERENCES users(id), filename TEXT NOT NULL,
    media_type TEXT NOT NULL, storage_key TEXT NOT NULL REFERENCES upload_blobs(storage_key)
);
