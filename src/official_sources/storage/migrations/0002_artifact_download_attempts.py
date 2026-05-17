from __future__ import annotations

UP_SQL = """
CREATE TABLE IF NOT EXISTS artifact_download_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL REFERENCES official_documents(id),
    ingestion_run_id INTEGER REFERENCES ingestion_runs(id),
    file_type TEXT NOT NULL,
    official_url TEXT,
    status TEXT NOT NULL CHECK(status IN ('success', 'skipped', 'failed', 'changed')),
    http_status INTEGER,
    error_message TEXT,
    started_at TEXT NOT NULL,
    finished_at TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""
