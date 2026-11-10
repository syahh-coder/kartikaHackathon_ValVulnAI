-- Safe business workflow baseline. No runtime-selectable weakened condition.
CREATE TABLE business_items (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    stock INTEGER NOT NULL CHECK(typeof(stock)='integer' AND stock BETWEEN 0 AND 10000)
);
CREATE TABLE business_staff (
    user_id TEXT PRIMARY KEY REFERENCES users(id),
    unit TEXT NOT NULL
);
CREATE TABLE business_requests (
    request_id TEXT PRIMARY KEY REFERENCES requests(id),
    item_id TEXT NOT NULL REFERENCES business_items(id),
    quantity INTEGER NOT NULL CHECK(typeof(quantity)='integer' AND quantity BETWEEN 1 AND 1000),
    state TEXT NOT NULL CHECK(state IN ('DRAFT','SUBMITTED','APPROVED','FULFILLED')),
    version INTEGER NOT NULL CHECK(version >= 1),
    approved_by TEXT REFERENCES users(id)
);
CREATE TABLE business_fulfillments (
    id TEXT NOT NULL UNIQUE,
    request_id TEXT PRIMARY KEY REFERENCES business_requests(request_id),
    actor_id TEXT NOT NULL REFERENCES users(id),
    quantity INTEGER NOT NULL CHECK(quantity BETWEEN 1 AND 1000),
    request_version INTEGER NOT NULL,
    stock_before INTEGER NOT NULL,
    stock_after INTEGER NOT NULL CHECK(stock_after >= 0),
    created_at REAL NOT NULL,
    CHECK(stock_before-stock_after=quantity)
);
CREATE TABLE business_events (
    id TEXT PRIMARY KEY,
    request_id TEXT NOT NULL REFERENCES business_requests(request_id),
    actor_id TEXT NOT NULL REFERENCES users(id),
    operation TEXT NOT NULL CHECK(operation IN ('CREATE','EDIT','SUBMIT','APPROVE','FULFILL')),
    before_json TEXT NOT NULL,
    after_json TEXT NOT NULL,
    created_at REAL NOT NULL
);
CREATE TRIGGER business_approved_fields_locked BEFORE UPDATE ON business_requests
WHEN OLD.state IN ('APPROVED','FULFILLED')
 AND (NEW.item_id != OLD.item_id OR NEW.quantity != OLD.quantity)
BEGIN SELECT RAISE(ABORT, 'Approved material fields are immutable'); END;
