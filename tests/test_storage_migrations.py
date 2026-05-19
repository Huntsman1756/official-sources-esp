from __future__ import annotations

import sqlite3

import pytest

from official_sources.storage.database import connect
from official_sources.storage.migrations.runner import (
    Migration,
    MigrationChecksumError,
    MigrationRunner,
    migrate_database,
    validate_database,
)
from official_sources.storage.schema import SCHEMA_SQL


def _table_columns(connection: sqlite3.Connection) -> dict[str, list[str]]:
    tables = [
        row["name"]
        for row in connection.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
        ).fetchall()
    ]
    return {
        table: [row["name"] for row in connection.execute(f"PRAGMA table_info({table})")]
        for table in tables
    }


def _insert_initial_data(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        INSERT INTO official_sources (
            code, name, jurisdiction, region_code, base_url, access_type,
            reliability_level, created_at, updated_at
        )
        VALUES (
            'BOE', 'Boletin Oficial del Estado', 'state', 'ES',
            'https://www.boe.es', 'official_api', 'canonical',
            '2024-01-01T00:00:00+00:00', '2024-01-01T00:00:00+00:00'
        )
        """
    )
    source_id = connection.execute("SELECT id FROM official_sources WHERE code = 'BOE'").fetchone()[
        "id"
    ]
    connection.execute(
        """
        INSERT INTO official_documents (
            source_id, external_id, publication_date, title, created_at, updated_at
        )
        VALUES (
            ?, 'BOE-A-2024-11111', '2024-05-29', 'Existing document',
            '2024-01-01T00:00:00+00:00', '2024-01-01T00:00:00+00:00'
        )
        """,
        (source_id,),
    )
    document_id = connection.execute(
        "SELECT id FROM official_documents WHERE external_id = 'BOE-A-2024-11111'"
    ).fetchone()["id"]
    connection.execute(
        """
        INSERT INTO document_files (
            document_id, file_type, official_url, size_bytes, sha256,
            source_snapshot_hash, first_seen_at, last_seen_at, created_at, updated_at
        )
        VALUES (
            ?, 'xml',
            'https://www.boe.es/diario_boe/xml.php?id=BOE-A-2024-11111',
            6, 'oldhash', 'oldhash',
            '2024-01-01T00:00:00+00:00', '2024-01-01T00:00:00+00:00',
            '2024-01-01T00:00:00+00:00', '2024-01-01T00:00:00+00:00'
        )
        """,
        (document_id,),
    )
    connection.execute(
        """
        INSERT INTO ingestion_runs (
            source_code, run_date, target_date, status, documents_fetched,
            documents_new, documents_updated, started_at
        )
        VALUES ('BOE', '2024-05-29', '2024-05-29', 'success', 1, 1, 0,
            '2024-01-01T00:00:00+00:00')
        """
    )
    connection.commit()


def _insert_consolidated_data(connection: sqlite3.Connection) -> None:
    source_id = connection.execute("SELECT id FROM official_sources WHERE code = 'BOE'").fetchone()[
        "id"
    ]
    connection.execute(
        """
        INSERT INTO consolidated_laws (
            source_id, external_id, official_identifier, title, jurisdiction,
            official_url, raw_metadata_json, created_at, updated_at
        )
        VALUES (
            ?, 'BOE-A-2024-11111', 'BOE-A-2024-11111', 'Existing law',
            'state',
            'https://www.boe.es/datosabiertos/api/legislacion-consolidada/id/BOE-A-2024-11111',
            '{}', '2024-01-01T00:00:00+00:00', '2024-01-01T00:00:00+00:00'
        )
        """,
        (source_id,),
    )
    law_id = connection.execute(
        "SELECT id FROM consolidated_laws WHERE official_identifier = 'BOE-A-2024-11111'"
    ).fetchone()["id"]
    connection.execute(
        """
        INSERT INTO consolidated_law_versions (
            consolidated_law_id, version_identifier, is_current, official_url,
            raw_payload_hash, source_snapshot_hash, created_at, updated_at
        )
        VALUES (
            ?, 'BOE-A-2024-11111:current', 1,
            'https://www.boe.es/datosabiertos/api/legislacion-consolidada/id/BOE-A-2024-11111',
            'lawhash', 'lawhash',
            '2024-01-01T00:00:00+00:00', '2024-01-01T00:00:00+00:00'
        )
        """,
        (law_id,),
    )
    version_id = connection.execute(
        "SELECT id FROM consolidated_law_versions WHERE consolidated_law_id = ?",
        (law_id,),
    ).fetchone()["id"]
    connection.execute(
        """
        INSERT INTO consolidated_law_text_blocks (
            consolidated_law_id, version_id, block_type, block_identifier,
            title, content, content_sha256, source_snapshot_hash,
            order_index, created_at, updated_at
        )
        VALUES (
            ?, ?, 'article', 'a1', 'Article 1', 'Existing text',
            'contenthash', 'lawhash', 0,
            '2024-01-01T00:00:00+00:00', '2024-01-01T00:00:00+00:00'
        )
        """,
        (law_id, version_id),
    )
    connection.commit()


def _build_initial_database(connection: sqlite3.Connection) -> None:
    MigrationRunner().migrate(connection, target_version=1)
    connection.execute("DROP TABLE schema_migrations")
    _insert_initial_data(connection)


def _build_before_artifact_database(connection: sqlite3.Connection) -> None:
    _build_initial_database(connection)


def _build_before_consolidated_database(connection: sqlite3.Connection) -> None:
    runner = MigrationRunner()
    runner.migrate(connection, target_version=2)
    connection.execute("DROP TABLE schema_migrations")
    _insert_initial_data(connection)


def _build_before_block_fields_database(connection: sqlite3.Connection) -> None:
    runner = MigrationRunner()
    runner.migrate(connection, target_version=3)
    connection.execute("DROP TABLE schema_migrations")
    _insert_initial_data(connection)
    _insert_consolidated_data(connection)


def test_empty_database_migrates_to_latest_schema():
    connection = connect(":memory:")

    result = migrate_database(connection)

    assert result.current_version == 8
    assert result.applied_versions == [1, 2, 3, 4, 5, 6, 7, 8]
    assert validate_database(connection).valid is True


def test_file_database_connection_enables_wal_and_normal_synchronous(tmp_path):
    connection = connect(str(tmp_path / "wal.sqlite"))

    journal_mode = connection.execute("PRAGMA journal_mode").fetchone()[0]
    synchronous = connection.execute("PRAGMA synchronous").fetchone()[0]

    assert journal_mode == "wal"
    assert synchronous == 1


def test_migrations_and_validation_work_with_wal_enabled_database(tmp_path):
    connection = connect(str(tmp_path / "migrated-wal.sqlite"))

    result = migrate_database(connection)

    assert result.current_version == 8
    assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
    assert validate_database(connection).valid is True


@pytest.mark.parametrize(
    "builder",
    [
        _build_initial_database,
        _build_before_artifact_database,
        _build_before_consolidated_database,
        _build_before_block_fields_database,
    ],
)
def test_older_database_states_upgrade_to_latest_and_preserve_data(builder):
    connection = connect(":memory:")
    builder(connection)

    result = migrate_database(connection)

    assert result.current_version == 8
    assert (
        connection.execute("SELECT COUNT(*) AS count FROM official_documents").fetchone()["count"]
        == 1
    )
    assert (
        connection.execute("SELECT COUNT(*) AS count FROM document_files").fetchone()["count"] == 1
    )
    assert (
        connection.execute("SELECT COUNT(*) AS count FROM ingestion_runs").fetchone()["count"] == 1
    )
    assert validate_database(connection).valid is True


def test_consolidated_law_data_survives_block_field_migration():
    connection = connect(":memory:")
    _build_before_block_fields_database(connection)

    migrate_database(connection)

    block = connection.execute("SELECT * FROM consolidated_law_text_blocks").fetchone()
    assert block["content"] == "Existing text"
    assert block["official_block_id"] is None
    assert "official_block_id" in _table_columns(connection)["consolidated_law_text_blocks"]


def test_request_audit_fields_are_added_by_latest_migration():
    connection = connect(":memory:")
    _build_before_block_fields_database(connection)

    migrate_database(connection)

    columns = _table_columns(connection)
    assert "throttle_triggered" in columns["ingestion_runs"]
    assert "retry_count" in columns["ingestion_runs"]
    assert "last_http_status" in columns["ingestion_runs"]
    assert "throttle_triggered" in columns["artifact_download_attempts"]
    assert "retry_count" in columns["artifact_download_attempts"]


def test_ingestion_no_publication_status_is_allowed_by_latest_migration():
    connection = connect(":memory:")
    _build_before_block_fields_database(connection)

    migrate_database(connection)

    connection.execute(
        """
        INSERT INTO ingestion_runs (
            source_code,
            run_date,
            target_date,
            status,
            started_at,
            documents_fetched,
            documents_new,
            documents_updated,
            last_http_status
        )
        VALUES (
            'BOE',
            '2026-05-17',
            '2026-05-17',
            'no_publication',
            '2026-05-17T00:00:00+00:00',
            0,
            0,
            0,
            404
        )
        """
    )
    row = connection.execute(
        "SELECT status, last_http_status FROM ingestion_runs WHERE status = 'no_publication'"
    ).fetchone()

    assert row["status"] == "no_publication"
    assert row["last_http_status"] == 404


def test_candidate_evidence_reviews_table_is_added_by_latest_migration():
    connection = connect(":memory:")

    migrate_database(connection)

    columns = _table_columns(connection)
    assert "candidate_evidence_reviews" in columns
    assert "source_candidate_id" in columns["candidate_evidence_reviews"]
    assert "evidence_review_status" in columns["candidate_evidence_reviews"]
    assert "evidence_label" in columns["candidate_evidence_reviews"]
    assert "selected_for_evidence" in columns["candidate_evidence_reviews"]
    assert "selected_for_pdf" in columns["candidate_evidence_reviews"]
    assert "xml_available" in columns["candidate_evidence_reviews"]
    assert "html_available" in columns["candidate_evidence_reviews"]
    assert "pdf_available" in columns["candidate_evidence_reviews"]
    assert "integrity_warning" in columns["candidate_evidence_reviews"]
    assert "manual_decision" in columns["candidate_evidence_reviews"]
    assert "manual_notes" in columns["candidate_evidence_reviews"]
    assert "needs_pdf" in columns["candidate_evidence_reviews"]
    assert "downstream_project_fit" in columns["candidate_evidence_reviews"]


def test_fresh_migrated_schema_matches_canonical_latest_schema():
    migrated = connect(":memory:")
    canonical = connect(":memory:")

    migrate_database(migrated)
    canonical.executescript(SCHEMA_SQL)
    migrated_columns = _table_columns(migrated)
    canonical_columns = _table_columns(canonical)
    expected_tables = set(canonical_columns) | {"schema_migrations"}

    assert set(migrated_columns) == expected_tables
    for table, columns in canonical_columns.items():
        assert set(migrated_columns[table]) == set(columns)
    assert migrated_columns["schema_migrations"] == [
        "id",
        "version",
        "name",
        "checksum",
        "applied_at",
        "execution_time_ms",
    ]


def test_migration_records_checksum_and_does_not_duplicate_entries():
    connection = connect(":memory:")
    migrate_database(connection)
    first_count = connection.execute("SELECT COUNT(*) AS count FROM schema_migrations").fetchone()[
        "count"
    ]

    result = migrate_database(connection)

    assert result.applied_versions == []
    assert (
        connection.execute("SELECT COUNT(*) AS count FROM schema_migrations").fetchone()["count"]
        == first_count
    )
    assert connection.execute(
        "SELECT checksum FROM schema_migrations WHERE version = 1"
    ).fetchone()["checksum"]


def test_checksum_mismatch_is_detected():
    connection = connect(":memory:")
    migrate_database(connection)
    connection.execute("UPDATE schema_migrations SET checksum = 'tampered' WHERE version = 1")
    connection.commit()

    with pytest.raises(MigrationChecksumError):
        migrate_database(connection)


def test_failed_migration_is_not_marked_as_applied():
    connection = connect(":memory:")
    runner = MigrationRunner(
        migrations=[
            Migration(1, "initial", "CREATE TABLE preserved (id INTEGER PRIMARY KEY)"),
            Migration(
                2,
                "broken",
                "CREATE TABLE broken (id INTEGER PRIMARY KEY); SELECT * FROM missing_table",
            ),
        ]
    )

    with pytest.raises(sqlite3.Error):
        runner.migrate(connection)

    assert [
        row["version"]
        for row in connection.execute("SELECT version FROM schema_migrations").fetchall()
    ] == [1]


def test_validate_fails_on_missing_required_table_and_column():
    missing_table = connect(":memory:")
    migrate_database(missing_table)
    missing_table.execute("DROP TABLE document_texts")

    table_result = validate_database(missing_table)

    assert table_result.valid is False
    assert any("document_texts" in problem for problem in table_result.problems)

    missing_column = connect(":memory:")
    migrate_database(missing_column)
    missing_column.execute(
        """
        CREATE TABLE broken_blocks AS
        SELECT id, consolidated_law_id, version_id FROM consolidated_law_text_blocks
        """
    )
    missing_column.execute("DROP TABLE consolidated_law_text_blocks")
    missing_column.execute("ALTER TABLE broken_blocks RENAME TO consolidated_law_text_blocks")

    column_result = validate_database(missing_column)

    assert column_result.valid is False
    assert any("official_block_id" in problem for problem in column_result.problems)
