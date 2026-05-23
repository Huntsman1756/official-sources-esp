from __future__ import annotations

from pathlib import Path

from official_sources.storage.database import connect
from official_sources.storage.repository import OfficialSourcesRepository


def _fixture_bytes(name: str) -> bytes:
    return (Path(__file__).parent / "fixtures" / name).read_bytes()


def test_ingest_bopv_date_cli_creates_ingestion_run(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"

    def fetcher(kind: str, _target_date: str, _url: str) -> bytes:
        if kind == "calendar":
            return _fixture_bytes("bopv_calendar_052026.html")
        if kind == "issue_xml":
            return _fixture_bytes("bopv_issue_s26_0093.xml")
        raise AssertionError(f"unexpected BOPV fetch kind: {kind}")

    exit_code = run(
        ["--db-path", str(db_path), "ingest-bopv-date", "--date", "2026-05-20"],
        bopv_fetcher=fetcher,
    )

    connection = connect(str(db_path))
    repository = OfficialSourcesRepository(connection)
    run_record = repository.get_latest_ingestion_run("BOPV", "2026-05-20")
    document = repository.get_document_by_external_id("BOPV:BOPV-2026-05-2602104a")
    captured = capsys.readouterr()

    assert exit_code == 0
    assert run_record["status"] == "success"
    assert run_record["documents_fetched"] == 3
    assert document["source_code"] == "BOPV"
    assert (
        "command_started=ingest-bopv-date source_code=BOPV target_date=2026-05-20" in captured.out
    )
    assert "status=success" in captured.out
    assert "issue_identifier=BOPV-2026-0093" in captured.out
    assert "documents_fetched=3" in captured.out
    assert "source_snapshot_hash=" in captured.out


def test_ingest_bopv_date_cli_records_no_publication(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"

    exit_code = run(
        ["--db-path", str(db_path), "ingest-bopv-date", "--date", "2026-05-17"],
        bopv_fetcher=lambda _kind, _date, _url: _fixture_bytes("bopv_calendar_no_publication.html"),
    )

    connection = connect(str(db_path))
    repository = OfficialSourcesRepository(connection)
    run_record = repository.get_latest_ingestion_run("BOPV", "2026-05-17")
    captured = capsys.readouterr()

    assert exit_code == 0
    assert run_record["status"] == "no_publication"
    assert run_record["documents_fetched"] == 0
    assert "status=no_publication" in captured.out
    assert "issue_identifier=none" in captured.out
    assert "documents_fetched=0" in captured.out
