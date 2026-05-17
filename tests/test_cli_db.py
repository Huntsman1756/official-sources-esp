from __future__ import annotations

from official_sources.storage.database import connect


def test_cli_db_status_reports_versions_and_pending_migrations(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "status.sqlite"

    exit_code = run(["--db-path", str(db_path), "db", "status"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert f"database_path={db_path}" in captured.out
    assert "current_version=0" in captured.out
    assert "latest_version=5" in captured.out
    assert "pending_migrations=5" in captured.out


def test_cli_db_migrate_applies_pending_migrations_and_preserves_data(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "migrate.sqlite"
    assert run(["--db-path", str(db_path), "db", "migrate"]) == 0
    connection = connect(str(db_path))
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
    connection.commit()

    exit_code = run(["--db-path", str(db_path), "db", "migrate"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "status=up_to_date" in captured.out
    assert (
        connection.execute("SELECT COUNT(*) AS count FROM official_sources").fetchone()["count"]
        == 1
    )


def test_cli_db_validate_reports_valid_database(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "validate.sqlite"
    run(["--db-path", str(db_path), "db", "migrate"])

    exit_code = run(["--db-path", str(db_path), "db", "validate"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "status=valid" in captured.out


def test_cli_db_validate_fails_for_invalid_database(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "invalid.sqlite"
    connection = connect(str(db_path))
    connection.execute("CREATE TABLE unrelated (id INTEGER PRIMARY KEY)")
    connection.commit()

    exit_code = run(["--db-path", str(db_path), "db", "validate"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "status=invalid" in captured.out
    assert "schema_migrations" in captured.err


def test_cli_db_commands_reject_directory_database_path(tmp_path, capsys):
    from official_sources.cli import run

    exit_code = run(["--db-path", str(tmp_path), "db", "migrate"])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "Database path points to a directory" in captured.err
