from __future__ import annotations

import os
import sqlite3
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path

APPLICATION_TABLES = [
    "official_sources",
    "official_documents",
    "document_files",
    "document_texts",
    "document_references",
    "source_candidates",
    "ingestion_runs",
    "integrity_checks",
    "artifact_download_attempts",
    "consolidated_laws",
    "consolidated_law_versions",
    "consolidated_law_text_blocks",
    "consolidated_law_references",
    "consolidated_law_integrity_checks",
    "schema_migrations",
]


class SQLiteBackupError(RuntimeError):
    pass


@dataclass(frozen=True)
class SQLiteBackupResult:
    source_path: Path
    output_path: Path
    page_count: int
    verification_mode: str
    source_check: str
    backup_check: str
    row_counts_checked: bool
    size_bytes: int


def backup_sqlite_database(
    database_path: str | Path,
    output_path: str | Path,
    *,
    force: bool = False,
    verification_mode: str = "quick_check",
    min_size_bytes: int = 1024,
) -> SQLiteBackupResult:
    source = Path(database_path)
    output = Path(output_path)
    _validate_backup_paths(source, output, force=force)
    _validate_verification_mode(verification_mode)
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists() and force:
        output.unlink()
    source_connection = sqlite3.connect(str(source))
    destination_connection = sqlite3.connect(str(output))
    source_check = "skipped"
    backup_check = "skipped"
    row_counts_checked = False
    try:
        if verification_mode != "none":
            source_check = _run_sqlite_check(source_connection, verification_mode, "source")
        source_counts = _application_row_counts(source_connection)
        page_count = source_connection.execute("PRAGMA page_count").fetchone()[0]
        source_connection.backup(destination_connection)
        destination_connection.execute("PRAGMA optimize")
        destination_connection.commit()
        if verification_mode != "none":
            backup_check = _run_sqlite_check(destination_connection, verification_mode, "backup")
            backup_counts = _application_row_counts(destination_connection)
            _compare_row_counts(source_counts, backup_counts)
            row_counts_checked = True
    except Exception:
        destination_connection.close()
        source_connection.close()
        if output.exists():
            output.rename(output.with_suffix(output.suffix + ".failed"))
        raise
    finally:
        with suppress(Exception):
            source_connection.close()
        with suppress(Exception):
            destination_connection.close()
    size_bytes = output.stat().st_size
    if size_bytes < min_size_bytes:
        output.rename(output.with_suffix(output.suffix + ".failed"))
        raise SQLiteBackupError(
            f"Backup file is smaller than minimum: size_bytes={size_bytes} "
            f"min_size_bytes={min_size_bytes}"
        )
    _restrict_file_permissions(output)
    return SQLiteBackupResult(
        source_path=source,
        output_path=output,
        page_count=page_count,
        verification_mode=verification_mode,
        source_check=source_check,
        backup_check=backup_check,
        row_counts_checked=row_counts_checked,
        size_bytes=size_bytes,
    )


def _validate_backup_paths(source: Path, output: Path, *, force: bool) -> None:
    if not source.exists():
        raise SQLiteBackupError(f"Database path does not exist: {source}")
    if source.is_dir():
        raise SQLiteBackupError("Database path points to a directory")
    if output.exists() and output.is_dir():
        raise SQLiteBackupError("Backup output path points to a directory")
    if output.exists() and not force:
        raise SQLiteBackupError(f"Backup output already exists: {output}")
    if source.resolve() == output.resolve():
        raise SQLiteBackupError("Backup output must be different from database path")
    if output.parent.exists() and not output.parent.is_dir():
        raise SQLiteBackupError(f"Backup output parent is not a directory: {output.parent}")


def _validate_verification_mode(mode: str) -> None:
    if mode not in {"quick_check", "full_check", "none"}:
        raise SQLiteBackupError(f"Unsupported backup verification mode: {mode}")


def _run_sqlite_check(
    connection: sqlite3.Connection,
    verification_mode: str,
    label: str,
) -> str:
    pragma = "integrity_check" if verification_mode == "full_check" else "quick_check"
    result = connection.execute(f"PRAGMA {pragma}").fetchone()[0]
    if result != "ok":
        raise SQLiteBackupError(f"{label} database {pragma} failed: {result}")
    return result


def _application_row_counts(connection: sqlite3.Connection) -> dict[str, int]:
    existing_tables = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }
    counts: dict[str, int] = {}
    for table in APPLICATION_TABLES:
        if table in existing_tables:
            counts[table] = connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    return counts


def _compare_row_counts(source_counts: dict[str, int], backup_counts: dict[str, int]) -> None:
    if source_counts != backup_counts:
        raise SQLiteBackupError(
            f"Backup row-count comparison failed: source={source_counts} backup={backup_counts}"
        )


def _restrict_file_permissions(path: Path) -> None:
    with suppress(OSError):
        os.chmod(path, 0o600)
