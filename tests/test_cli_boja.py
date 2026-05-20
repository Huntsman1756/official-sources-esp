from __future__ import annotations

from pathlib import Path

import httpx

from official_sources.storage.database import connect, initialize_database
from official_sources.storage.repository import OfficialSourcesRepository


def _fixture_bytes(name: str) -> bytes:
    return (Path(__file__).parent / "fixtures" / name).read_bytes()


def _boja_400_no_publication_fetcher(_target_date: str, _page: int, _size: int) -> bytes:
    request = httpx.Request(
        "GET", "https://datos.juntadeandalucia.es/api/v0/boja/get/search_pagination"
    )
    response = httpx.Response(
        400,
        request=request,
        headers={"content-type": "application/json"},
        content=_fixture_bytes("boja_http_400_no_publication.json"),
    )
    raise httpx.HTTPStatusError(
        f"Client error '400' for url '{request.url}'",
        request=request,
        response=response,
    )


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


def test_ingest_boja_date_cli_records_observed_400_no_publication(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    exit_code = run(
        ["--db-path", str(db_path), "ingest-boja-date", "--date", "2026-04-25"],
        boja_fetcher=_boja_400_no_publication_fetcher,
    )

    connection = connect(str(db_path))
    repository = OfficialSourcesRepository(connection)
    run_record = repository.get_latest_ingestion_run("BOJA", "2026-04-25")
    captured = capsys.readouterr()

    assert exit_code == 0
    assert run_record["status"] == "no_publication"
    assert run_record["last_http_status"] == 400
    assert "status=no_publication" in captured.out
    assert "pagination_complete=true" in captured.out
    assert "last_http_status=400" in captured.out


def test_enrich_boja_evidence_urls_cli_updates_selected_candidate_only(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    connection = connect(str(db_path))
    initialize_database(connection)
    repository = OfficialSourcesRepository(connection)
    source = repository.ensure_official_source_boja()
    selected = repository.upsert_document(
        source_id=source["id"],
        external_id="BOJA:disposition.2026.94.5",
        publication_date="2026-05-19",
        title="Selected BOJA document",
        department="Universidades",
        section="1. Disposiciones generales",
        raw_metadata={"id": "disposition.2026.94.5"},
    )
    unselected = repository.upsert_document(
        source_id=source["id"],
        external_id="BOJA:disposition.2026.94.6",
        publication_date="2026-05-19",
        title="Unselected BOJA document",
        department="Universidades",
        section="1. Disposiciones generales",
        raw_metadata={"id": "disposition.2026.94.6"},
    )
    repository.create_source_candidate(
        document_id=selected["id"],
        project_key="boja-ayudas",
        candidate_type="aid",
        extraction_status="raw_detected",
        evidence_level="metadata",
        matched_fields={"keywords": ["becas"]},
    )
    repository.create_source_candidate(
        document_id=unselected["id"],
        project_key="boja-ayudas",
        candidate_type="aid",
        extraction_status="raw_detected",
        evidence_level="metadata",
        matched_fields={"keywords": ["becas"]},
    )
    candidate_id = repository.connection.execute(
        "SELECT id FROM source_candidates WHERE document_id = ?", (selected["id"],)
    ).fetchone()["id"]

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "enrich-boja-evidence-urls",
            "--candidate-ids",
            str(candidate_id),
        ],
        boja_detail_fetcher=lambda _official_id: _fixture_bytes(
            "boja_document_detail_with_pdf.json"
        ),
    )

    refreshed = OfficialSourcesRepository(connect(str(db_path)))
    selected_after = refreshed.get_document_by_external_id("BOJA:disposition.2026.94.5")
    unselected_after = refreshed.get_document_by_external_id("BOJA:disposition.2026.94.6")
    captured = capsys.readouterr()

    assert exit_code == 0
    assert selected_after["url_pdf"].endswith("BOJA26-094-00002-6601-01_00337837.pdf")
    assert unselected_after["url_pdf"] is None
    assert (
        "command_started=enrich-boja-evidence-urls source_code=BOJA target=scoped" in captured.out
    )
    assert "selected_documents=1" in captured.out
    assert "enriched=1" in captured.out
    assert "missing_evidence_url=0" in captured.out
