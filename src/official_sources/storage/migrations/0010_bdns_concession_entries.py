from __future__ import annotations

UP_SQL = """
CREATE TABLE IF NOT EXISTS bdns_concession_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    concession_code TEXT NOT NULL UNIQUE,
    external_id TEXT NOT NULL UNIQUE,
    call_identifier TEXT,
    call_code TEXT,
    call_internal_id INTEGER,
    concession_date TEXT,
    registration_date TEXT,
    amount REAL,
    aid_equivalent REAL,
    instrument TEXT,
    department TEXT,
    section TEXT,
    beneficiary_name TEXT,
    beneficiary_person_id INTEGER,
    base_regulation_url TEXT,
    raw_metadata_json TEXT NOT NULL DEFAULT '{}',
    source_url TEXT NOT NULL,
    source_snapshot_hash TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    previous_hash TEXT,
    first_seen_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    content_changed_at TEXT,
    change_detected_by INTEGER REFERENCES ingestion_runs(id),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_bdns_concession_entries_call
ON bdns_concession_entries(call_identifier);

CREATE INDEX IF NOT EXISTS idx_bdns_concession_entries_date
ON bdns_concession_entries(concession_date);
"""
