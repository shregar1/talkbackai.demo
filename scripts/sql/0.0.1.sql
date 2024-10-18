CREATE TABLE user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    urn TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    first_name NULL,
    last_name NULL
    password TEXT NOT NULL,
    created_at TEXT NOT NULL,
    is_logged_in INTEGER NOT NULL DEFAULT 0,
    is_deleted INTEGER NOT NULL DEFAULT 0,
    last_login TEXT,
    updated_at TEXT
);

CREATE INDEX idx_user_urn ON user (urn);
CREATE INDEX idx_user_created_at ON user (created_at);
