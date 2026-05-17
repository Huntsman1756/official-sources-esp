from __future__ import annotations

CHECKSUM_INPUT = """
ALTER TABLE consolidated_law_text_blocks ADD COLUMN official_block_id TEXT;
ALTER TABLE consolidated_law_text_blocks ADD COLUMN parent_block_id TEXT;
ALTER TABLE consolidated_law_text_blocks ADD COLUMN block_path TEXT;
ALTER TABLE consolidated_law_text_blocks ADD COLUMN api_url TEXT;
ALTER TABLE consolidated_law_text_blocks ADD COLUMN raw_payload_hash TEXT;
ALTER TABLE consolidated_law_text_blocks ADD COLUMN raw_metadata_json TEXT NOT NULL DEFAULT '{}';
ALTER TABLE consolidated_law_text_blocks ADD COLUMN last_seen_at TEXT;
ALTER TABLE consolidated_law_text_blocks ADD COLUMN content_changed_at TEXT;
ALTER TABLE consolidated_law_text_blocks ADD COLUMN previous_hash TEXT;
ALTER TABLE consolidated_law_text_blocks ADD COLUMN change_detected_by
    INTEGER REFERENCES ingestion_runs(id);
"""


def apply(connection) -> None:
    _add_column_if_missing(connection, "consolidated_law_text_blocks", "official_block_id", "TEXT")
    _add_column_if_missing(connection, "consolidated_law_text_blocks", "parent_block_id", "TEXT")
    _add_column_if_missing(connection, "consolidated_law_text_blocks", "block_path", "TEXT")
    _add_column_if_missing(connection, "consolidated_law_text_blocks", "api_url", "TEXT")
    _add_column_if_missing(connection, "consolidated_law_text_blocks", "raw_payload_hash", "TEXT")
    _add_column_if_missing(
        connection,
        "consolidated_law_text_blocks",
        "raw_metadata_json",
        "TEXT NOT NULL DEFAULT '{}'",
    )
    _add_column_if_missing(connection, "consolidated_law_text_blocks", "last_seen_at", "TEXT")
    _add_column_if_missing(connection, "consolidated_law_text_blocks", "content_changed_at", "TEXT")
    _add_column_if_missing(connection, "consolidated_law_text_blocks", "previous_hash", "TEXT")
    _add_column_if_missing(
        connection,
        "consolidated_law_text_blocks",
        "change_detected_by",
        "INTEGER REFERENCES ingestion_runs(id)",
    )


def _add_column_if_missing(connection, table: str, column: str, definition: str) -> None:
    columns = {row["name"] for row in connection.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in columns:
        connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
