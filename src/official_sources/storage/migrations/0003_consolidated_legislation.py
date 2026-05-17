from __future__ import annotations

UP_SQL = """
CREATE TABLE IF NOT EXISTS consolidated_laws (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER NOT NULL REFERENCES official_sources(id),
    external_id TEXT NOT NULL,
    official_identifier TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    law_type TEXT,
    jurisdiction TEXT NOT NULL,
    department TEXT,
    publication_date TEXT,
    consolidation_status TEXT,
    official_url TEXT NOT NULL,
    raw_metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS consolidated_law_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    consolidated_law_id INTEGER NOT NULL REFERENCES consolidated_laws(id),
    version_identifier TEXT NOT NULL,
    version_date TEXT,
    valid_from TEXT,
    valid_to TEXT,
    is_current INTEGER NOT NULL CHECK(is_current IN (0, 1)),
    official_url TEXT NOT NULL,
    raw_payload_hash TEXT NOT NULL,
    source_snapshot_hash TEXT NOT NULL,
    previous_hash TEXT,
    content_changed_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(consolidated_law_id, version_identifier)
);

CREATE TABLE IF NOT EXISTS consolidated_law_text_blocks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    consolidated_law_id INTEGER NOT NULL REFERENCES consolidated_laws(id),
    version_id INTEGER NOT NULL REFERENCES consolidated_law_versions(id),
    block_type TEXT NOT NULL,
    block_identifier TEXT NOT NULL,
    title TEXT,
    content TEXT NOT NULL,
    content_sha256 TEXT NOT NULL,
    source_snapshot_hash TEXT NOT NULL,
    order_index INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS consolidated_law_references (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    consolidated_law_id INTEGER NOT NULL REFERENCES consolidated_laws(id),
    referenced_identifier TEXT,
    reference_type TEXT NOT NULL,
    reference_text TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS consolidated_law_integrity_checks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    consolidated_law_version_id INTEGER NOT NULL REFERENCES consolidated_law_versions(id),
    checked_at TEXT NOT NULL,
    previous_sha256 TEXT,
    current_sha256 TEXT NOT NULL,
    changed INTEGER NOT NULL CHECK(changed IN (0, 1)),
    change_reason TEXT,
    notes TEXT,
    created_at TEXT NOT NULL
);
"""
