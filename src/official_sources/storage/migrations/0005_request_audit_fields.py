from __future__ import annotations

CHECKSUM_INPUT = """
ALTER TABLE ingestion_runs ADD COLUMN throttle_triggered INTEGER NOT NULL DEFAULT 0;
ALTER TABLE ingestion_runs ADD COLUMN retry_count INTEGER NOT NULL DEFAULT 0;
ALTER TABLE ingestion_runs ADD COLUMN last_http_status INTEGER;
ALTER TABLE artifact_download_attempts ADD COLUMN throttle_triggered INTEGER NOT NULL DEFAULT 0;
ALTER TABLE artifact_download_attempts ADD COLUMN retry_count INTEGER NOT NULL DEFAULT 0;
"""


def apply(connection) -> None:
    _add_column_if_missing(
        connection,
        "ingestion_runs",
        "throttle_triggered",
        "INTEGER NOT NULL DEFAULT 0",
    )
    _add_column_if_missing(
        connection,
        "ingestion_runs",
        "retry_count",
        "INTEGER NOT NULL DEFAULT 0",
    )
    _add_column_if_missing(connection, "ingestion_runs", "last_http_status", "INTEGER")
    _add_column_if_missing(
        connection,
        "artifact_download_attempts",
        "throttle_triggered",
        "INTEGER NOT NULL DEFAULT 0",
    )
    _add_column_if_missing(
        connection,
        "artifact_download_attempts",
        "retry_count",
        "INTEGER NOT NULL DEFAULT 0",
    )


def _add_column_if_missing(connection, table: str, column: str, definition: str) -> None:
    columns = {row["name"] for row in connection.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in columns:
        connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
