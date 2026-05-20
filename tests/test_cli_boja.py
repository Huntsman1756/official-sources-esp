from __future__ import annotations

from pathlib import Path

from official_sources.storage.database import connect
from official_sources.storage.repository import OfficialSourcesRepository


def _fixture_bytes(name: str) -> bytes:
    return (Path(__file__).parent / "fixtures" / name).read_bytes()


def test_ingest_boja_date_cli_creates_ingestion_run(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    exit_code = run(
        ["--db-path", str(db_path), "ingest-boja-date", "--date", "2026-05-19"],
        boja_fetcher=lambda _date: _fixture_bytes("boja_date_with_documents.json"),
    )

    connection = connect(str(db_path))
    repository = OfficialSourcesRepository(connection)
    run_record = repository.get_latest_ingestion_run("BOJA", "2026-05-19")
    document = repository.get_document_by_external_id("BOJA:disposition.2026.94.5")
    captured = capsys.readouterr()

    assert exit_code == 0
    assert run_record["status"] == "success"
    assert run_record["documents_fetched"] == 2
    assert document["source_code"] == "BOJA"
    assert (
        "command_started=ingest-boja-date source_code=BOJA target_date=2026-05-19" in captured.out
    )
    assert "pages_fetched=1" in captured.out
    assert "pagination_complete=true" in captured.out
    assert "documents_fetched=2" in captured.out


def test_ingest_boja_date_cli_records_no_publication(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    exit_code = run(
        ["--db-path", str(db_path), "ingest-boja-date", "--date", "2026-05-17"],
        boja_fetcher=lambda _date: _fixture_bytes("boja_date_empty_or_no_publication.json"),
    )

    connection = connect(str(db_path))
    repository = OfficialSourcesRepository(connection)
    run_record = repository.get_latest_ingestion_run("BOJA", "2026-05-17")
    captured = capsys.readouterr()

    assert exit_code == 0
    assert run_record["status"] == "no_publication"
    assert "status=no_publication" in captured.out
    assert "pages_fetched=1" in captured.out
    assert "pagination_complete=true" in captured.out
    assert "documents_fetched=0" in captured.out
