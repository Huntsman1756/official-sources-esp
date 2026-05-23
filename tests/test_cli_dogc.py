from __future__ import annotations

from pathlib import Path

from official_sources.storage.database import connect
from official_sources.storage.repository import OfficialSourcesRepository


def _fixture_bytes(name: str) -> bytes:
    return (Path(__file__).parent / "fixtures" / name).read_bytes()


def test_ingest_dogc_date_cli_creates_ingestion_run(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"

    exit_code = run(
        ["--db-path", str(db_path), "ingest-dogc-date", "--date", "2026-05-22"],
        dogc_fetcher=lambda _date: _fixture_bytes("dogc_date_with_documents.json"),
        dogc_document_fetcher=lambda _document_id: _fixture_bytes("dogc_document_metadata.json"),
    )

    connection = connect(str(db_path))
    repository = OfficialSourcesRepository(connection)
    run_record = repository.get_latest_ingestion_run("DOGC", "2026-05-22")
    document = repository.get_document_by_external_id("DOGC:CVE-DOGC-A-26141001-2026")
    captured = capsys.readouterr()

    assert exit_code == 0
    assert run_record["status"] == "success"
    assert run_record["documents_fetched"] == 2
    assert document["source_code"] == "DOGC"
    assert (
        "command_started=ingest-dogc-date source_code=DOGC target_date=2026-05-22" in captured.out
    )
    assert "status=success" in captured.out
    assert "issue_identifier=9671" in captured.out
    assert "documents_fetched=2" in captured.out
    assert "source_snapshot_hash=" in captured.out
    assert "source_snapshot_hash=none" not in captured.out


def test_ingest_dogc_date_cli_records_no_publication(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"

    exit_code = run(
        ["--db-path", str(db_path), "ingest-dogc-date", "--date", "2026-05-23"],
        dogc_fetcher=lambda _date: _fixture_bytes("dogc_date_no_publication.json"),
    )

    connection = connect(str(db_path))
    repository = OfficialSourcesRepository(connection)
    run_record = repository.get_latest_ingestion_run("DOGC", "2026-05-23")
    captured = capsys.readouterr()

    assert exit_code == 0
    assert run_record["status"] == "no_publication"
    assert run_record["documents_fetched"] == 0
    assert "status=no_publication" in captured.out
    assert "issue_identifier=none" in captured.out
    assert "documents_fetched=0" in captured.out
