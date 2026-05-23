from __future__ import annotations

from pathlib import Path

import pytest

from official_sources.citation.builder import build_citation
from official_sources.integrity.hashing import sha256_bytes
from official_sources.sources.dogc.client import (
    build_dogc_date_search_payload,
    build_dogc_document_html_url,
    validate_dogc_date,
)
from official_sources.sources.dogc.ingestion import ingest_dogc_date
from official_sources.sources.dogc.parser import (
    parse_dogc_date_response,
    parse_dogc_document_metadata,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _fixture_bytes(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


@pytest.mark.parametrize("value", ["2026-05-22", "1977-12-05"])
def test_dogc_date_validation_accepts_iso_dates(value):
    assert validate_dogc_date(value).isoformat() == value


@pytest.mark.parametrize("value", ["20260522", "2026-02-30", "not-a-date"])
def test_dogc_date_validation_rejects_invalid_dates(value):
    with pytest.raises(ValueError):
        validate_dogc_date(value)


def test_dogc_source_record_creation(repository):
    source = repository.ensure_official_source_dogc()

    assert source["code"] == "DOGC"
    assert source["name"] == "Diari Oficial de la Generalitat de Catalunya"
    assert source["jurisdiction"] == "autonomous"
    assert source["region_code"] == "ES-CT"
    assert source["access_type"] == "official_api"
    assert source["reliability_level"] == "canonical"


def test_date_search_payload_uses_official_dogc_date_format():
    payload = build_dogc_date_search_payload("2026-05-22")

    assert payload["publicationDateInitial"] == "22/05/2026"
    assert payload["publicationDateFinal"] == "22/05/2026"
    assert payload["language"] == "ca"


def test_date_response_parses_documents_and_preserves_urls():
    payload = _fixture_bytes("dogc_date_with_documents.json")

    issue = parse_dogc_date_response(payload, target_date="2026-05-22")

    assert issue.status == "success"
    assert issue.issue_identifier == "9671"
    assert issue.raw_payload_sha256 == sha256_bytes(payload)
    assert len(issue.documents) == 2
    assert issue.documents[0].external_id == "DOGC:1044918"
    assert issue.documents[0].official_identifier == "1044918"
    assert issue.documents[0].publication_date == "2026-05-22"
    assert issue.documents[0].url_html == build_dogc_document_html_url("1044918")
    assert issue.documents[0].url_pdf.endswith("versionId=2151744&type=01")
    assert issue.documents[0].url_xml.endswith("idNumber=1044918&idVersion=2151744&format=xml")


def test_date_response_records_no_publication():
    payload = _fixture_bytes("dogc_date_no_publication.json")

    issue = parse_dogc_date_response(payload, target_date="2026-05-23")

    assert issue.status == "no_publication"
    assert issue.issue_identifier is None
    assert issue.documents == []
    assert issue.raw_payload_sha256 == sha256_bytes(payload)


def test_document_metadata_normalizes_identifier_and_citation_fields():
    payload = _fixture_bytes("dogc_document_metadata.json")

    metadata = parse_dogc_document_metadata(payload, fallback_document_id="1044918")

    assert metadata.official_identifier == "CVE-DOGC-A-26141001-2026"
    assert metadata.publication_date == "2026-05-22"
    assert metadata.title.startswith("Llei 5/2026")
    assert metadata.department == "Departament de la Presidencia"
    assert metadata.section == "Disposicions generals"
    assert metadata.document_type == "Llei"
    assert metadata.url_html == build_dogc_document_html_url("1044918")
    assert metadata.url_xml.endswith("format=xml")
    assert metadata.raw_metadata["metadata_sha256"] == sha256_bytes(payload)


def test_dogc_ingestion_stores_documents_without_pdf_or_candidates(repository):
    payload = _fixture_bytes("dogc_date_with_documents.json")
    detail_payload = _fixture_bytes("dogc_document_metadata.json")

    run = ingest_dogc_date(
        repository,
        target_date="2026-05-22",
        date_payload=payload,
        document_payloads={"1044918": detail_payload, "1044864": detail_payload},
    )

    document = repository.get_document_by_external_id("DOGC:CVE-DOGC-A-26141001-2026")
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
    assert run["issue_identifier"] == "9671"
    assert run["documents_fetched"] == 2
    assert run["documents_new"] == 1
    assert document["source_code"] == "DOGC"
    assert document["url_xml"].endswith("format=xml")
    assert raw_file_count == 1
    assert pdf_file_count == 0
    assert candidate_count == 0
    assert attempt_count == 0
    assert run["source_snapshot_hash"] == sha256_bytes(payload)


def test_dogc_ingestion_records_no_publication(repository):
    run = ingest_dogc_date(
        repository,
        target_date="2026-05-23",
        date_payload=_fixture_bytes("dogc_date_no_publication.json"),
    )

    assert run["status"] == "no_publication"
    assert run["documents_fetched"] == 0
    assert run["issue_identifier"] is None
    assert repository.list_documents_by_date("2026-05-23") == []


def test_dogc_ingestion_supports_citation_generation(repository):
    run = ingest_dogc_date(
        repository,
        target_date="2026-05-22",
        date_payload=_fixture_bytes("dogc_date_with_documents.json"),
        document_payloads={"1044918": _fixture_bytes("dogc_document_metadata.json")},
    )

    citation = build_citation(repository, "DOGC:CVE-DOGC-A-26141001-2026")

    assert run["status"] == "success"
    assert citation["source_code"] == "DOGC"
    assert citation["external_id"] == "DOGC:CVE-DOGC-A-26141001-2026"
    assert citation["official_url"] == build_dogc_document_html_url("1044918")
