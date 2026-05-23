from __future__ import annotations

from pathlib import Path

from official_sources.storage.database import connect
from official_sources.storage.repository import OfficialSourcesRepository


def _fixture_bytes(name: str) -> bytes:
    return (Path(__file__).parent / "fixtures" / name).read_bytes()


def test_ingest_bocyl_date_cli_creates_ingestion_run(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"

    exit_code = run(
        ["--db-path", str(db_path), "ingest-bocyl-date", "--date", "2026-05-20"],
        bocyl_fetcher=lambda _date: _fixture_bytes("bocyl_date_with_documents.json"),
    )

    connection = connect(str(db_path))
    repository = OfficialSourcesRepository(connection)
    run_record = repository.get_latest_ingestion_run("BOCYL", "2026-05-20")
    document = repository.get_document_by_external_id("BOCYL:BOCYL-D-20052026-94-1")
    captured = capsys.readouterr()

    assert exit_code == 0
    assert run_record["status"] == "success"
    assert run_record["documents_fetched"] == 2
    assert document["source_code"] == "BOCYL"
    assert (
        "command_started=ingest-bocyl-date source_code=BOCYL target_date=2026-05-20" in captured.out
    )
    assert "status=success" in captured.out
    assert "issue_identifier=94/2026" in captured.out
    assert "documents_fetched=2" in captured.out
    assert "source_snapshot_hash=" in captured.out
    assert "source_snapshot_hash=none" not in captured.out


def test_ingest_bocyl_date_cli_records_no_publication(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"

    exit_code = run(
        ["--db-path", str(db_path), "ingest-bocyl-date", "--date", "2026-05-17"],
        bocyl_fetcher=lambda _date: _fixture_bytes("bocyl_date_no_publication.json"),
    )

    connection = connect(str(db_path))
    repository = OfficialSourcesRepository(connection)
    run_record = repository.get_latest_ingestion_run("BOCYL", "2026-05-17")
    captured = capsys.readouterr()

    assert exit_code == 0
    assert run_record["status"] == "no_publication"
    assert run_record["documents_fetched"] == 0
    assert "status=no_publication" in captured.out
    assert "issue_identifier=none" in captured.out
    assert "documents_fetched=0" in captured.out
