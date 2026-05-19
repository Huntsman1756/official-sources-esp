from __future__ import annotations

import inspect
import shutil

import pytest

from official_sources.citation.builder import build_citation, build_consolidated_law_citation
from official_sources.cli import run
from official_sources.mcp import tools
from official_sources.storage.backup import SQLiteBackupError, backup_sqlite_database
from official_sources.storage.database import connect
from official_sources.storage.migrations.runner import MigrationRunner, validate_database
from official_sources.storage.repository import OfficialSourcesRepository


def _build_realistic_pre_latest_database(path) -> None:
    connection = connect(str(path))
    MigrationRunner().migrate(connection, target_version=3)
    connection.execute("DROP TABLE schema_migrations")
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
        INSERT INTO ingestion_runs (
            source_code, run_date, target_date, status, documents_fetched,
            documents_new, documents_updated, started_at, finished_at
        )
        VALUES (
            'BOE', '2024-05-29', '2024-05-29', 'success', 1, 1, 0,
            '2024-05-29T10:00:00+00:00', '2024-05-29T10:01:00+00:00'
        )
        """
    )
    run_id = connection.execute("SELECT id FROM ingestion_runs").fetchone()["id"]
    connection.execute(
        """
        INSERT INTO official_documents (
            source_id, external_id, publication_date, title, department, section,
            document_type, url_html, url_xml, raw_metadata_json, created_at, updated_at
        )
        VALUES (
            ?, 'BOE-A-2024-11111', '2024-05-29', 'Existing document',
            'Ministry', 'I', 'law',
            'https://www.boe.es/diario_boe/txt.php?id=BOE-A-2024-11111',
            'https://www.boe.es/diario_boe/xml.php?id=BOE-A-2024-11111',
            '{}', '2024-05-29T10:00:00+00:00', '2024-05-29T10:00:00+00:00'
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
            document_id, file_type, official_url, media_type, size_bytes, sha256,
            source_snapshot_hash, first_seen_at, last_seen_at,
            last_integrity_check_at, created_at, updated_at
        )
        VALUES (
            ?, 'xml',
            'https://www.boe.es/diario_boe/xml.php?id=BOE-A-2024-11111',
            'application/xml', 12, 'filehash', 'filehash',
            '2024-05-29T10:00:00+00:00', '2024-05-29T10:00:00+00:00',
            '2024-05-29T10:00:00+00:00',
            '2024-05-29T10:00:00+00:00', '2024-05-29T10:00:00+00:00'
        )
        """,
        (document_id,),
    )
    file_id = connection.execute("SELECT id FROM document_files").fetchone()["id"]
    connection.execute(
        """
        INSERT INTO document_texts (
            document_id, source_file_id, text_type, language, content,
            content_sha256, extraction_method, created_at, updated_at
        )
        VALUES (
            ?, ?, 'clean_text', 'es', 'Existing official document text',
            'texthash', 'fixture', '2024-05-29T10:00:00+00:00',
            '2024-05-29T10:00:00+00:00'
        )
        """,
        (document_id, file_id),
    )
    connection.execute(
        """
        INSERT INTO artifact_download_attempts (
            document_id, ingestion_run_id, file_type, official_url, status,
            http_status, started_at, finished_at, created_at
        )
        VALUES (
            ?, ?, 'xml',
            'https://www.boe.es/diario_boe/xml.php?id=BOE-A-2024-11111',
            'success', 200, '2024-05-29T10:00:00+00:00',
            '2024-05-29T10:00:01+00:00', '2024-05-29T10:00:01+00:00'
        )
        """,
        (document_id, run_id),
    )
    connection.execute(
        """
        INSERT INTO consolidated_laws (
            source_id, external_id, official_identifier, title, law_type,
            jurisdiction, official_url, raw_metadata_json, created_at, updated_at
        )
        VALUES (
            ?, 'BOE-A-2024-11111', 'BOE-A-2024-11111', 'Existing law',
            'Law', 'state',
            'https://www.boe.es/datosabiertos/api/legislacion-consolidada/id/BOE-A-2024-11111',
            '{}', '2024-05-29T10:00:00+00:00', '2024-05-29T10:00:00+00:00'
        )
        """,
        (source_id,),
    )
    law_id = connection.execute("SELECT id FROM consolidated_laws").fetchone()["id"]
    connection.execute(
        """
        INSERT INTO consolidated_law_versions (
            consolidated_law_id, version_identifier, version_date, is_current,
            official_url, raw_payload_hash, source_snapshot_hash, created_at, updated_at
        )
        VALUES (
            ?, 'BOE-A-2024-11111:block:a1', '2024-05-29', 1,
            'https://www.boe.es/datosabiertos/api/legislacion-consolidada/id/BOE-A-2024-11111/texto/bloque/a1',
            'lawhash', 'lawhash',
            '2024-05-29T10:00:00+00:00', '2024-05-29T10:00:00+00:00'
        )
        """,
        (law_id,),
    )
    version_id = connection.execute("SELECT id FROM consolidated_law_versions").fetchone()["id"]
    connection.execute(
        """
        INSERT INTO consolidated_law_text_blocks (
            consolidated_law_id, version_id, block_type, block_identifier,
            title, content, content_sha256, source_snapshot_hash,
            order_index, created_at, updated_at
        )
        VALUES (
            ?, ?, 'article', 'a1', 'Article 1',
            'Existing official block text', 'blockhash', 'lawhash', 0,
            '2024-05-29T10:00:00+00:00', '2024-05-29T10:00:00+00:00'
        )
        """,
        (law_id, version_id),
    )
    connection.commit()
    connection.close()


def test_backup_creates_readable_sqlite_copy(tmp_path):
    db_path = tmp_path / "source.sqlite"
    backup_path = tmp_path / "backups" / "official_sources_20240529_100000.sqlite"
    _build_realistic_pre_latest_database(db_path)

    result = backup_sqlite_database(db_path, backup_path)

    assert result.output_path == backup_path
    assert backup_path.exists()
    restored = connect(str(backup_path))
    assert restored.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert (
        restored.execute("SELECT COUNT(*) AS count FROM official_documents").fetchone()["count"]
        == 1
    )
    assert result.verification_mode == "quick_check"
    assert result.source_check == "ok"
    assert result.backup_check == "ok"
    assert result.row_counts_checked is True
    assert result.size_bytes >= 1024


def test_backup_does_not_overwrite_without_force(tmp_path):
    db_path = tmp_path / "source.sqlite"
    backup_path = tmp_path / "backup.sqlite"
    _build_realistic_pre_latest_database(db_path)
    backup_path.write_bytes(b"existing")

    with pytest.raises(SQLiteBackupError, match="already exists"):
        backup_sqlite_database(db_path, backup_path)

    result = backup_sqlite_database(db_path, backup_path, force=True)

    assert result.output_path == backup_path
    assert connect(str(backup_path)).execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def test_backup_rejects_invalid_output_path(tmp_path):
    db_path = tmp_path / "source.sqlite"
    _build_realistic_pre_latest_database(db_path)

    with pytest.raises(SQLiteBackupError, match="directory"):
        backup_sqlite_database(db_path, tmp_path)


def test_realistic_restore_migrate_validate_and_read_smoke(tmp_path, capsys):
    source_path = tmp_path / "persistent.sqlite"
    backup_path = tmp_path / "backup.sqlite"
    restored_path = tmp_path / "restored.sqlite"
    _build_realistic_pre_latest_database(source_path)

    backup_sqlite_database(source_path, backup_path)
    shutil.copy2(backup_path, restored_path)
    exit_code = run(["--db-path", str(restored_path), "db", "migrate"])
    status_exit_code = run(["--db-path", str(restored_path), "status", "--date", "2024-05-29"])

    connection = connect(str(restored_path))
    repository = OfficialSourcesRepository(connection)
    validation = validate_database(connection)
    citation = build_citation(repository, "BOE-A-2024-11111")
    block_citation = build_consolidated_law_citation(
        repository,
        "BOE-A-2024-11111",
        block_identifier="a1",
    )
    block = tools.boe_consolidated_law_block_get(
        repository,
        official_identifier="BOE-A-2024-11111",
        block_id="a1",
    )

    assert exit_code == 0
    assert status_exit_code == 0
    assert validation.valid is True
    assert validation.current_version == 8
    assert citation["external_id"] == "BOE-A-2024-11111"
    assert block_citation["resource_type"] == "consolidated_law_block"
    assert block["content"] == "Existing official block text"
    artifact_attempts = connection.execute(
        "SELECT COUNT(*) AS count FROM artifact_download_attempts"
    ).fetchone()["count"]
    assert artifact_attempts == 1
    assert "documents=1" in capsys.readouterr().out


def test_backup_module_does_not_use_network_or_downstream_writes():
    import official_sources.storage.backup as backup_module

    source = inspect.getsource(backup_module)

    assert "httpx" not in source
    assert "requests" not in source
    assert "boe" not in source.lower()
    assert "mcp" not in source.lower()
    assert "downstream" not in source.lower()


def test_backup_full_check_uses_integrity_check(tmp_path):
    db_path = tmp_path / "source.sqlite"
    backup_path = tmp_path / "backup.sqlite"
    _build_realistic_pre_latest_database(db_path)

    result = backup_sqlite_database(db_path, backup_path, verification_mode="full_check")

    assert result.verification_mode == "full_check"
    assert result.source_check == "ok"
    assert result.backup_check == "ok"


def test_backup_no_verify_skips_checks(tmp_path):
    db_path = tmp_path / "source.sqlite"
    backup_path = tmp_path / "backup.sqlite"
    _build_realistic_pre_latest_database(db_path)

    result = backup_sqlite_database(db_path, backup_path, verification_mode="none")

    assert result.verification_mode == "none"
    assert result.source_check == "skipped"
    assert result.backup_check == "skipped"
    assert result.row_counts_checked is False


def test_backup_fails_if_backup_size_is_below_threshold(tmp_path):
    db_path = tmp_path / "source.sqlite"
    backup_path = tmp_path / "backup.sqlite"
    _build_realistic_pre_latest_database(db_path)

    with pytest.raises(SQLiteBackupError, match="smaller than minimum"):
        backup_sqlite_database(db_path, backup_path, min_size_bytes=10_000_000)


def test_backup_fails_if_source_check_fails(tmp_path, monkeypatch):
    import official_sources.storage.backup as backup_module

    db_path = tmp_path / "source.sqlite"
    backup_path = tmp_path / "backup.sqlite"
    _build_realistic_pre_latest_database(db_path)

    def fail_source(_connection, _verification_mode, label):
        if label == "source":
            raise SQLiteBackupError("source database quick_check failed: bad")
        return "ok"

    monkeypatch.setattr(backup_module, "_run_sqlite_check", fail_source)

    with pytest.raises(SQLiteBackupError, match="source database quick_check failed"):
        backup_sqlite_database(db_path, backup_path)


def test_backup_fails_if_backup_check_fails(tmp_path, monkeypatch):
    import official_sources.storage.backup as backup_module

    db_path = tmp_path / "source.sqlite"
    backup_path = tmp_path / "backup.sqlite"
    _build_realistic_pre_latest_database(db_path)

    def fail_backup(_connection, _verification_mode, label):
        if label == "backup":
            raise SQLiteBackupError("backup database quick_check failed: bad")
        return "ok"

    monkeypatch.setattr(backup_module, "_run_sqlite_check", fail_backup)

    with pytest.raises(SQLiteBackupError, match="backup database quick_check failed"):
        backup_sqlite_database(db_path, backup_path)


def test_backup_fails_if_row_counts_differ(tmp_path, monkeypatch):
    import official_sources.storage.backup as backup_module

    db_path = tmp_path / "source.sqlite"
    backup_path = tmp_path / "backup.sqlite"
    _build_realistic_pre_latest_database(db_path)

    def fail_counts(_source_counts, _backup_counts):
        raise SQLiteBackupError("Backup row-count comparison failed")

    monkeypatch.setattr(backup_module, "_compare_row_counts", fail_counts)

    with pytest.raises(SQLiteBackupError, match="row-count comparison failed"):
        backup_sqlite_database(db_path, backup_path)


def test_cli_db_backup_rejects_conflicting_verification_modes(tmp_path, capsys):
    db_path = tmp_path / "source.sqlite"
    backup_path = tmp_path / "backup.sqlite"
    _build_realistic_pre_latest_database(db_path)

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "db",
            "backup",
            "--output",
            str(backup_path),
            "--quick-check",
            "--full-check",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "cannot be used together" in captured.err


def test_cli_db_backup_creates_file_and_help_mentions_command(tmp_path, capsys):
    db_path = tmp_path / "source.sqlite"
    backup_path = tmp_path / "backup.sqlite"
    _build_realistic_pre_latest_database(db_path)

    help_exit = run(["db", "--help"])
    exit_code = run(["--db-path", str(db_path), "db", "backup", "--output", str(backup_path)])

    captured = capsys.readouterr()
    assert help_exit == 0
    assert "backup" in captured.out
    assert exit_code == 0
    assert backup_path.exists()
    assert "status=success" in captured.out
    assert "verification=quick_check" in captured.out


def test_cli_db_backup_rejects_existing_output_without_force(tmp_path, capsys):
    db_path = tmp_path / "source.sqlite"
    backup_path = tmp_path / "backup.sqlite"
    _build_realistic_pre_latest_database(db_path)
    backup_path.write_bytes(b"existing")

    exit_code = run(["--db-path", str(db_path), "db", "backup", "--output", str(backup_path)])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "already exists" in captured.err


def test_cli_db_backup_supports_explicit_force(tmp_path, capsys):
    db_path = tmp_path / "source.sqlite"
    backup_path = tmp_path / "backup.sqlite"
    _build_realistic_pre_latest_database(db_path)
    backup_path.write_bytes(b"existing")

    exit_code = run(
        ["--db-path", str(db_path), "db", "backup", "--output", str(backup_path), "--force"]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "status=success" in captured.out
    assert connect(str(backup_path)).execute("PRAGMA integrity_check").fetchone()[0] == "ok"
