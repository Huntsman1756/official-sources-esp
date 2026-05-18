from __future__ import annotations

import hashlib
import importlib
import sqlite3
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from types import ModuleType

from official_sources.storage.schema import SCHEMA_SQL

MIGRATION_MODULE_NAMES = [
    "0001_initial",
    "0002_artifact_download_attempts",
    "0003_consolidated_legislation",
    "0004_consolidated_index_blocks",
    "0005_request_audit_fields",
    "0006_ingestion_no_publication_status",
    "0007_candidate_evidence_reviews",
]

SCHEMA_MIGRATIONS_SQL = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version INTEGER NOT NULL UNIQUE,
    name TEXT NOT NULL,
    checksum TEXT NOT NULL,
    applied_at TEXT NOT NULL,
    execution_time_ms INTEGER NOT NULL
);
"""


class MigrationError(RuntimeError):
    pass


class MigrationChecksumError(MigrationError):
    pass


@dataclass(frozen=True)
class Migration:
    version: int
    name: str
    checksum_input: str
    apply_func: Callable[[sqlite3.Connection], None] | None = None

    @property
    def checksum(self) -> str:
        payload = f"{self.version}:{self.name}:{self.checksum_input}".encode()
        return hashlib.sha256(payload).hexdigest()

    def apply(self, connection: sqlite3.Connection) -> None:
        if self.apply_func is not None:
            self.apply_func(connection)
        else:
            _execute_sql_statements(connection, self.checksum_input)


@dataclass(frozen=True)
class MigrationResult:
    current_version: int
    latest_version: int
    pending_versions: list[int]
    applied_versions: list[int]


@dataclass(frozen=True)
class SchemaValidationResult:
    valid: bool
    current_version: int
    latest_version: int
    problems: list[str]


class MigrationRunner:
    def __init__(self, migrations: list[Migration] | None = None) -> None:
        self.migrations = sorted(
            migrations or load_migrations(),
            key=lambda migration: migration.version,
        )
        versions = [migration.version for migration in self.migrations]
        if versions != sorted(set(versions)):
            raise MigrationError("Migration versions must be unique and sorted")

    @property
    def latest_version(self) -> int:
        if not self.migrations:
            return 0
        return self.migrations[-1].version

    def status(self, connection: sqlite3.Connection) -> MigrationResult:
        if _table_exists(connection, "schema_migrations"):
            self._verify_applied_checksums(connection)
        current_version = self.current_version(connection)
        pending = [
            migration.version
            for migration in self.migrations
            if migration.version > current_version
        ]
        return MigrationResult(
            current_version=current_version,
            latest_version=self.latest_version,
            pending_versions=pending,
            applied_versions=[],
        )

    def current_version(self, connection: sqlite3.Connection) -> int:
        if not _table_exists(connection, "schema_migrations"):
            return 0
        row = connection.execute("SELECT MAX(version) AS version FROM schema_migrations").fetchone()
        return int(row["version"] or 0)

    def migrate(
        self,
        connection: sqlite3.Connection,
        *,
        target_version: int | None = None,
    ) -> MigrationResult:
        self._ensure_metadata_table(connection)
        self._verify_applied_checksums(connection)
        target = target_version if target_version is not None else self.latest_version
        current_version = self.current_version(connection)
        pending = [
            migration
            for migration in self.migrations
            if current_version < migration.version <= target
        ]
        applied_versions: list[int] = []
        for migration in pending:
            start = time.perf_counter()
            try:
                connection.execute("BEGIN")
                migration.apply(connection)
                execution_time_ms = int((time.perf_counter() - start) * 1000)
                connection.execute(
                    """
                    INSERT INTO schema_migrations (
                        version, name, checksum, applied_at, execution_time_ms
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        migration.version,
                        migration.name,
                        migration.checksum,
                        _utc_now(),
                        execution_time_ms,
                    ),
                )
            except Exception:
                connection.rollback()
                raise
            else:
                connection.commit()
                applied_versions.append(migration.version)
        return MigrationResult(
            current_version=self.current_version(connection),
            latest_version=self.latest_version,
            pending_versions=[
                migration.version
                for migration in self.migrations
                if self.current_version(connection) < migration.version
            ],
            applied_versions=applied_versions,
        )

    def validate(self, connection: sqlite3.Connection) -> SchemaValidationResult:
        problems: list[str] = []
        if not _table_exists(connection, "schema_migrations"):
            problems.append("Missing required table: schema_migrations")
            current_version = 0
        else:
            try:
                self._verify_applied_checksums(connection)
            except MigrationChecksumError as exc:
                problems.append(str(exc))
            current_version = self.current_version(connection)
        if current_version != self.latest_version:
            problems.append(
                f"Schema version {current_version} does not match latest {self.latest_version}"
            )
        for table, columns in latest_required_columns().items():
            if not _table_exists(connection, table):
                problems.append(f"Missing required table: {table}")
                continue
            existing_columns = {
                row["name"] for row in connection.execute(f"PRAGMA table_info({table})").fetchall()
            }
            for column in columns:
                if column not in existing_columns:
                    problems.append(f"Missing required column: {table}.{column}")
        return SchemaValidationResult(
            valid=not problems,
            current_version=current_version,
            latest_version=self.latest_version,
            problems=problems,
        )

    def _ensure_metadata_table(self, connection: sqlite3.Connection) -> None:
        connection.executescript(SCHEMA_MIGRATIONS_SQL)
        connection.commit()

    def _verify_applied_checksums(self, connection: sqlite3.Connection) -> None:
        if not _table_exists(connection, "schema_migrations"):
            return
        expected = {migration.version: migration for migration in self.migrations}
        rows = connection.execute(
            "SELECT version, name, checksum FROM schema_migrations ORDER BY version"
        ).fetchall()
        for row in rows:
            migration = expected.get(row["version"])
            if migration is None:
                raise MigrationChecksumError(f"Unknown applied migration version: {row['version']}")
            if row["checksum"] != migration.checksum:
                raise MigrationChecksumError(
                    f"Checksum mismatch for migration {row['version']} ({row['name']})"
                )


def load_migrations() -> list[Migration]:
    migrations: list[Migration] = []
    for module_name in MIGRATION_MODULE_NAMES:
        module = importlib.import_module(f"official_sources.storage.migrations.{module_name}")
        migrations.append(_migration_from_module(module))
    return migrations


def migrate_database(connection: sqlite3.Connection) -> MigrationResult:
    return MigrationRunner().migrate(connection)


def validate_database(connection: sqlite3.Connection) -> SchemaValidationResult:
    return MigrationRunner().validate(connection)


def latest_required_columns() -> dict[str, list[str]]:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.executescript(SCHEMA_MIGRATIONS_SQL)
    connection.executescript(SCHEMA_SQL)
    rows = connection.execute(
        """
        SELECT name FROM sqlite_master
        WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
        ORDER BY name
        """
    ).fetchall()
    return {
        row["name"]: [
            column["name"]
            for column in connection.execute(f"PRAGMA table_info({row['name']})").fetchall()
        ]
        for row in rows
    }


def _migration_from_module(module: ModuleType) -> Migration:
    version_text, name = module.__name__.rsplit(".", maxsplit=1)[1].split("_", maxsplit=1)
    checksum_input = getattr(module, "CHECKSUM_INPUT", getattr(module, "UP_SQL", ""))
    apply_func = getattr(module, "apply", None)
    return Migration(
        version=int(version_text),
        name=name,
        checksum_input=checksum_input,
        apply_func=apply_func,
    )


def _table_exists(connection: sqlite3.Connection, table: str) -> bool:
    row = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table,),
    ).fetchone()
    return row is not None


def _execute_sql_statements(connection: sqlite3.Connection, sql: str) -> None:
    for statement in sql.split(";"):
        statement = statement.strip()
        if statement:
            connection.execute(statement)


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()
