from __future__ import annotations

from pathlib import Path

import pytest

from official_sources.citation.builder import build_citation
from official_sources.integrity.hashing import sha256_bytes
from official_sources.sources.boja.client import validate_boja_date
from official_sources.sources.boja.ingestion import ingest_boja_date
from official_sources.sources.boja.parser import parse_boja_search_response

FIXTURES = Path(__file__).parent / "fixtures"


def _fixture_bytes(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


@pytest.mark.parametrize("value", ["2026-05-19", "1980-01-01"])
def test_boja_date_validation_accepts_iso_dates(value):
    assert validate_boja_date(value).isoformat() == value


@pytest.mark.parametrize("value", ["20260519", "2026-02-30", "not-a-date"])
def test_boja_date_validation_rejects_invalid_dates(value):
    with pytest.raises(ValueError):
        validate_boja_date(value)


def test_boja_source_record_creation(repository):
    source = repository.ensure_official_source_boja()

    assert source["code"] == "BOJA"
    assert source["name"] == "Boletin Oficial de la Junta de Andalucia"
    assert source["jurisdiction"] == "autonomous"
    assert source["region_code"] == "ES-AN"
    assert source["access_type"] == "official_api"
    assert source["reliability_level"] == "canonical"


def test_boja_fixture_parses_documents_and_preserves_urls():
    payload = _fixture_bytes("boja_date_with_documents.json")

    parsed = parse_boja_search_response(payload, target_date="2026-05-19")

    assert parsed.target_date == "2026-05-19"
    assert parsed.raw_payload_sha256 == sha256_bytes(payload)
    assert parsed.total_hits == 2
    assert parsed.documents[0].external_id == "BOJA:disposition.2026.94.5"
    assert parsed.documents[0].publication_date == "2026-05-19"
    assert parsed.documents[0].title.startswith("Extracto de la Resolucion")
    assert parsed.documents[0].department == "Universidades"
    assert parsed.documents[0].section == "1. Disposiciones generales"
    assert parsed.documents[0].url_html.endswith("00321045.pdf")
    assert parsed.documents[0].url_pdf == (
        "https://www.juntadeandalucia.es/eboja/2026/94/BOJA26-094-00005-8702-01_00321045.pdf"
    )
    assert parsed.documents[0].raw_metadata["boja_official_id"] == "disposition.2026.94.5"
    assert parsed.documents[0].raw_metadata["hashPdf"] == "fixture-hash-1"


def test_boja_raw_hash_is_computed_before_parsing():
    payload = _fixture_bytes("boja_date_with_documents.json")

    parsed = parse_boja_search_response(payload, target_date="2026-05-19")
    reparsed = parse_boja_search_response(payload + b"\n", target_date="2026-05-19")

    assert parsed.raw_payload_sha256 != reparsed.raw_payload_sha256


def test_boja_empty_fixture_records_no_publication(repository):
    payload = _fixture_bytes("boja_date_empty_or_no_publication.json")

    run = ingest_boja_date(repository, target_date="2026-05-17", payload=payload)

    assert run["status"] == "no_publication"
    assert run["documents_fetched"] == 0
    assert repository.list_documents_by_date("2026-05-17") == []


def test_boja_ingestion_persists_documents_raw_payload_and_citation(repository):
    payload = _fixture_bytes("boja_date_with_documents.json")

    run = ingest_boja_date(repository, target_date="2026-05-19", payload=payload)

    document = repository.get_document_by_external_id("BOJA:disposition.2026.94.5")
    files = repository.list_document_files(document["id"])
    citation = build_citation(repository, "BOJA:disposition.2026.94.5")
    candidate_count = repository.connection.execute(
        "SELECT COUNT(*) AS count FROM source_candidates"
    ).fetchone()["count"]
    download_attempt_count = repository.connection.execute(
        "SELECT COUNT(*) AS count FROM artifact_download_attempts"
    ).fetchone()["count"]

    assert run["status"] == "success"
    assert run["documents_fetched"] == 2
    assert run["documents_new"] == 2
    assert run["documents_updated"] == 0
    assert run["last_http_status"] == 200
    assert document["source_code"] == "BOJA"
    assert document["url_pdf"].endswith(".pdf")
    assert files[0]["file_type"] == "raw_api_response"
    assert files[0]["source_snapshot_hash"] == sha256_bytes(payload)
    assert files[0]["media_type"] == "application/json"
    assert citation["source_code"] == "BOJA"
    assert citation["official_url"] == document["url_html"]
    assert citation["pdf_url"] == document["url_pdf"]
    assert candidate_count == 0
    assert download_attempt_count == 0


def test_boja_ingestion_updates_existing_document(repository):
    payload = _fixture_bytes("boja_date_with_documents.json")

    first = ingest_boja_date(repository, target_date="2026-05-19", payload=payload)
    second = ingest_boja_date(repository, target_date="2026-05-19", payload=payload)

    documents = repository.list_documents_by_date("2026-05-19")
    assert first["documents_new"] == 2
    assert second["documents_new"] == 0
    assert second["documents_updated"] == 2
    assert len(documents) == 2
