from __future__ import annotations

UP_SQL = """
CREATE TABLE IF NOT EXISTS bdns_catalog_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    catalog_name TEXT NOT NULL,
    code TEXT NOT NULL,
    external_id TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    source_url TEXT NOT NULL,
    raw_metadata_json TEXT NOT NULL DEFAULT '{}',
    source_snapshot_hash TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    previous_hash TEXT,
    first_seen_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    content_changed_at TEXT,
    change_detected_by INTEGER REFERENCES ingestion_runs(id),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(catalog_name, code)
);

CREATE INDEX IF NOT EXISTS idx_bdns_catalog_entries_catalog
ON bdns_catalog_entries(catalog_name);
"""
