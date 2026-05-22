from __future__ import annotations

from pathlib import Path

from official_sources.storage.database import connect
from official_sources.storage.repository import OfficialSourcesRepository


def _fixture_bytes(name: str) -> bytes:
    return (Path(__file__).parent / "fixtures" / name).read_bytes()


def test_ingest_bdns_latest_cli_creates_ingestion_run(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"

    exit_code = run(
        ["--db-path", str(db_path), "ingest-bdns-latest", "--limit", "1"],
        bdns_latest_fetcher=lambda _limit: _fixture_bytes("bdns_latest_convocatorias.json"),
    )

    connection = connect(str(db_path))
    repository = OfficialSourcesRepository(connection)
    run_record = repository.get_latest_ingestion_run("BDNS", "latest")
    document = repository.get_document_by_external_id("BDNS:907362")
    captured = capsys.readouterr()

    assert exit_code == 0
    assert run_record["status"] == "success"
    assert run_record["documents_fetched"] == 1
    assert document["source_code"] == "BDNS"
    assert "command_started=ingest-bdns-latest source_code=BDNS target=latest" in captured.out
    assert "status=success" in captured.out
    assert "documents_fetched=1" in captured.out
    assert "source_snapshot_hash=" in captured.out


def test_ingest_bdns_call_cli_creates_call_detail(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"

    exit_code = run(
        ["--db-path", str(db_path), "ingest-bdns-call", "--num-conv", "907042"],
        bdns_call_fetcher=lambda _num_conv: _fixture_bytes("bdns_convocatoria_detail.json"),
    )

    connection = connect(str(db_path))
    repository = OfficialSourcesRepository(connection)
    run_record = repository.get_latest_ingestion_run("BDNS", "907042")
    document = repository.get_document_by_external_id("BDNS:907042")
    captured = capsys.readouterr()

    assert exit_code == 0
    assert run_record["status"] == "success"
    assert document["raw_metadata_json"]
    assert "command_started=ingest-bdns-call source_code=BDNS num_conv=907042" in captured.out
    assert "official_identifier=BDNS:907042" in captured.out


def test_search_bdns_calls_cli_requires_page_limits(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "search-bdns-calls",
            "--date-from",
            "20/05/2026",
            "--date-to",
            "20/05/2026",
            "--page-size",
            "10",
            "--max-pages",
            "11",
        ],
        bdns_search_fetcher=lambda **_kwargs: _fixture_bytes("bdns_search_convocatorias.json"),
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "max-pages" in captured.err
