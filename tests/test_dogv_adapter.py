from __future__ import annotations

from pathlib import Path

import pytest

from official_sources.citation.builder import build_citation
from official_sources.integrity.hashing import sha256_bytes
from official_sources.sources.dogv.client import (
    build_dogv_document_html_url,
    build_dogv_document_metadata_url,
    build_dogv_document_pdf_url,
    build_dogv_document_xml_url,
    validate_dogv_date,
)
from official_sources.sources.dogv.ingestion import ingest_dogv_date
from official_sources.sources.dogv.parser import (
    parse_dogv_date_response,
    parse_dogv_document_metadata,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _fixture_bytes(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


@pytest.mark.parametrize("value", ["2026-05-20", "1980-01-01"])
def test_dogv_date_validation_accepts_iso_dates(value):
    assert validate_dogv_date(value).isoformat() == value


@pytest.mark.parametrize("value", ["20260520", "2026-02-30", "not-a-date"])
def test_dogv_date_validation_rejects_invalid_dates(value):
    with pytest.raises(ValueError):
        validate_dogv_date(value)


def test_dogv_source_record_creation(repository):
    source = repository.ensure_official_source_dogv()

    assert source["code"] == "DOGV"
    assert source["name"] == "Diari Oficial de la Generalitat Valenciana"
    assert source["jurisdiction"] == "autonomous"
    assert source["region_code"] == "ES-VC"
    assert source["access_type"] == "official_json"
    assert source["reliability_level"] == "canonical"


def test_date_response_parses_documents_and_preserves_urls():
    payload = _fixture_bytes("dogv_date_with_documents.json")

    issue = parse_dogv_date_response(payload, target_date="2026-05-20")

    assert issue.status == "success"
    assert issue.issue_identifier == "10366"
    assert issue.raw_payload_sha256 == sha256_bytes(payload)
    assert len(issue.documents) == 2
    assert issue.documents[0].external_id == "DOGV:DOGV-C-2026-16061"
    assert issue.documents[0].official_identifier == "DOGV-C-2026-16061"
    assert issue.documents[0].publication_date == "2026-05-20"
    assert issue.documents[0].url_html == build_dogv_document_html_url("2026/16061")
    assert issue.documents[0].url_xml == build_dogv_document_xml_url(477348)
    assert issue.documents[0].url_pdf == build_dogv_document_pdf_url(
        "/2026/05/20/pdf/2026_16061_es.pdf"
    )
    assert issue.documents[0].raw_metadata["url_metadata"] == build_dogv_document_metadata_url(
        477348
    )


def test_date_response_records_no_publication():
    payload = _fixture_bytes("dogv_date_no_publication.json")

    issue = parse_dogv_date_response(payload, target_date="2026-05-17")

    assert issue.status == "no_publication"
    assert issue.issue_identifier is None
    assert issue.documents == []
    assert issue.raw_payload_sha256 == sha256_bytes(payload)


def test_document_metadata_normalizes_identifier_and_citation_fields():
    payload = _fixture_bytes("dogv_document_metadata.json")

    metadata = parse_dogv_document_metadata(payload, fallback_document_id=477348)

    assert metadata.official_identifier == "DOGV-C-2026-16061"
    assert metadata.publication_date == "2026-05-20"
    assert metadata.title.startswith("EXTRACTO de la Resolucion")
    assert metadata.department == "Generalitat Valenciana"
    assert metadata.section == "III. ACTOS ADMINISTRATIVOS"
    assert metadata.document_type == "Extracto"
    assert metadata.url_html == build_dogv_document_html_url("2026/16061")
    assert metadata.url_xml == build_dogv_document_xml_url(477348)
    assert metadata.raw_metadata["metadata_sha256"] == sha256_bytes(payload)


def test_raw_hash_is_computed_before_parsing():
    payload = _fixture_bytes("dogv_date_with_documents.json")

    parsed = parse_dogv_date_response(payload, target_date="2026-05-20")
    reparsed = parse_dogv_date_response(payload + b"\n", target_date="2026-05-20")

    assert parsed.raw_payload_sha256 != reparsed.raw_payload_sha256


def test_dogv_ingestion_stores_documents_without_pdf_or_candidates(repository):
    payload = _fixture_bytes("dogv_date_with_documents.json")

    run = ingest_dogv_date(repository, target_date="2026-05-20", date_payload=payload)

    document = repository.get_document_by_external_id("DOGV:DOGV-C-2026-16061")
    raw_file_count = repository.connection.execute(
        "SELECT COUNT(*) AS count FROM document_files WHERE file_type = 'raw_api_response'"
    ).fetchone()["count"]
    pdf_file_count = repository.connection.execute(
        "SELECT COUNT(*) AS count FROM document_files WHERE file_type = 'pdf'"
    ).fetchone()["count"]
    candidate_count = repository.connection.execute(
        "SELECT COUNT(*) AS count FROM source_candidates"
    ).fetchone()["count"]
    attempt_count = repository.connection.execute(
        "SELECT COUNT(*) AS count FROM artifact_download_attempts"
    ).fetchone()["count"]

    assert run["status"] == "success"
    assert run["issue_identifier"] == "10366"
    assert run["documents_fetched"] == 2
    assert run["documents_new"] == 2
    assert document["source_code"] == "DOGV"
    assert document["url_xml"] == build_dogv_document_xml_url(477348)
    assert raw_file_count == 2
    assert pdf_file_count == 0
    assert candidate_count == 0
    assert attempt_count == 0
    assert run["source_snapshot_hash"] == sha256_bytes(payload)


def test_dogv_ingestion_records_no_publication(repository):
    run = ingest_dogv_date(
        repository,
        target_date="2026-05-17",
        date_payload=_fixture_bytes("dogv_date_no_publication.json"),
    )

    assert run["status"] == "no_publication"
    assert run["documents_fetched"] == 0
    assert run["issue_identifier"] is None
    assert repository.list_documents_by_date("2026-05-17") == []


def test_dogv_ingestion_supports_citation_generation(repository):
    run = ingest_dogv_date(
        repository,
        target_date="2026-05-20",
        date_payload=_fixture_bytes("dogv_date_with_documents.json"),
    )

    citation = build_citation(repository, "DOGV:DOGV-C-2026-16061")

    assert run["status"] == "success"
    assert citation["source_code"] == "DOGV"
    assert citation["external_id"] == "DOGV:DOGV-C-2026-16061"
    assert citation["official_url"] == build_dogv_document_html_url("2026/16061")
