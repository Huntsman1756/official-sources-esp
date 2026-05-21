from __future__ import annotations

from pathlib import Path

import httpx

from official_sources.storage.database import connect
from official_sources.storage.repository import OfficialSourcesRepository


def _fixture_bytes(name: str) -> bytes:
    return (Path(__file__).parent / "fixtures" / name).read_bytes()


def test_ingest_bocm_date_cli_creates_ingestion_run(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"

    def fetcher(kind: str, target_date: str, _url: str) -> bytes:
        if kind == "search_day":
            return _fixture_bytes("bocm_search_day_with_issue.html")
        if kind == "issue_page":
            return _fixture_bytes("bocm_issue_page.html")
        raise AssertionError(f"unexpected BOCM fetch kind: {kind}")

    exit_code = run(
        ["--db-path", str(db_path), "ingest-bocm-date", "--date", "2026-05-20"],
        bocm_fetcher=fetcher,
    )

    connection = connect(str(db_path))
    repository = OfficialSourcesRepository(connection)
    run_record = repository.get_latest_ingestion_run("BOCM", "2026-05-20")
    document = repository.get_document_by_external_id("BOCM:BOCM-20260520-37")
    captured = capsys.readouterr()

    assert exit_code == 0
    assert run_record["status"] == "success"
    assert run_record["documents_fetched"] == 2
    assert document["source_code"] == "BOCM"
    assert (
        "command_started=ingest-bocm-date source_code=BOCM target_date=2026-05-20" in captured.out
    )
    assert "status=success" in captured.out
    assert "issue_identifier=bocm-20260520-118" in captured.out
    assert "documents_fetched=2" in captured.out
    assert "source_snapshot_hash=" in captured.out
    assert "source_snapshot_hash=none" not in captured.out


def test_ingest_bocm_date_cli_records_no_publication(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"

    exit_code = run(
        ["--db-path", str(db_path), "ingest-bocm-date", "--date", "2026-05-17"],
        bocm_fetcher=lambda _kind, _date, _url: _fixture_bytes(
            "bocm_search_day_no_publication.html"
        ),
    )

    connection = connect(str(db_path))
    repository = OfficialSourcesRepository(connection)
    run_record = repository.get_latest_ingestion_run("BOCM", "2026-05-17")
    captured = capsys.readouterr()

    assert exit_code == 0
    assert run_record["status"] == "no_publication"
    assert run_record["documents_fetched"] == 0
    assert "status=no_publication" in captured.out
    assert "issue_identifier=none" in captured.out
    assert "documents_fetched=0" in captured.out


def test_ingest_bocm_date_cli_reports_repeated_read_timeout(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"

    def fetcher(kind: str, _target_date: str, _url: str) -> bytes:
        if kind == "search_day":
            return _fixture_bytes("bocm_search_day_with_issue.html")
        raise httpx.ReadTimeout("persistent BOCM read timeout")

    exit_code = run(
        ["--db-path", str(db_path), "ingest-bocm-date", "--date", "2026-05-20"],
        bocm_fetcher=fetcher,
    )

    connection = connect(str(db_path))
    repository = OfficialSourcesRepository(connection)
    run_record = repository.get_latest_ingestion_run("BOCM", "2026-05-20")
    captured = capsys.readouterr()

    assert exit_code == 1
    assert run_record["status"] == "failed"
    assert run_record["retry_count"] > 0
    assert run_record["status"] != "no_publication"
    assert "status=failed" in captured.out
    assert "retry_count=" in captured.out
    assert "error_message=" in captured.out
    assert "timed_out_after" in captured.out
