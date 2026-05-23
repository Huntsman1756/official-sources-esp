from __future__ import annotations

import sqlite3
from pathlib import Path

from official_sources.storage.migrations.runner import migrate_database


def connect(
    database_path: str,
    *,
    enable_wal: bool | None = None,
    check_same_thread: bool = True,
) -> sqlite3.Connection:
    connection = sqlite3.connect(database_path, check_same_thread=check_same_thread)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    wal_enabled = enable_wal if enable_wal is not None else _should_enable_wal(database_path)
    if wal_enabled:
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute("PRAGMA synchronous = NORMAL")
    return connection


def initialize_database(connection: sqlite3.Connection) -> None:
    migrate_database(connection)


def sqlite_runtime_pragmas(connection: sqlite3.Connection) -> dict[str, str]:
    journal_mode = connection.execute("PRAGMA journal_mode").fetchone()[0]
    synchronous_value = int(connection.execute("PRAGMA synchronous").fetchone()[0])
    synchronous_names = {
        0: "off",
        1: "normal",
        2: "full",
        3: "extra",
    }
    return {
        "journal_mode": str(journal_mode).lower(),
        "synchronous": synchronous_names.get(synchronous_value, str(synchronous_value)),
    }


def _should_enable_wal(database_path: str) -> bool:
    if database_path == ":memory:":
        return False
    if database_path.startswith("file:") and "mode=memory" in database_path:
        return False
    return Path(database_path).name != ""
