-- Baseline schema migration for bustag.
-- Uses IF NOT EXISTS to stay safe on existing databases.

CREATE TABLE IF NOT EXISTS item (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    fanhao TEXT NOT NULL UNIQUE,
    url TEXT NOT NULL UNIQUE,
    release_date DATE NOT NULL,
    add_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    meta_info TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tag (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,
    value TEXT NOT NULL,
    url TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_tag_type_value ON tag(type, value);

CREATE TABLE IF NOT EXISTS item_tag (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id TEXT NOT NULL,
    tag_id INTEGER NOT NULL,
    FOREIGN KEY(item_id) REFERENCES item(fanhao),
    FOREIGN KEY(tag_id) REFERENCES tag(id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_item_tag_unique ON item_tag(item_id, tag_id);

CREATE TABLE IF NOT EXISTS item_rate (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rate_type INTEGER NOT NULL,
    rate_value INTEGER NOT NULL,
    item_id TEXT NOT NULL UNIQUE,
    rete_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(item_id) REFERENCES item(fanhao)
);

CREATE TABLE IF NOT EXISTS local_item (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id TEXT NOT NULL UNIQUE,
    path TEXT,
    size INTEGER,
    add_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_view_date DATETIME,
    view_times INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY(item_id) REFERENCES item(fanhao)
);

CREATE TABLE IF NOT EXISTS "user" (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
