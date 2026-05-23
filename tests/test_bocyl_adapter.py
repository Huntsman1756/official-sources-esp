from __future__ import annotations

from pathlib import Path

import pytest

from official_sources.citation.builder import build_citation
from official_sources.integrity.hashing import sha256_bytes
from official_sources.sources.bocyl.client import build_bocyl_date_api_url, validate_bocyl_date
from official_sources.sources.bocyl.ingestion import ingest_bocyl_date
from official_sources.sources.bocyl.parser import (
    parse_bocyl_date_response,
    parse_bocyl_document_metadata,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _fixture_bytes(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


@pytest.mark.parametrize("value", ["2026-05-20", "1980-01-01"])
def test_bocyl_date_validation_accepts_iso_dates(value):
    assert validate_bocyl_date(value).isoformat() == value


@pytest.mark.parametrize("value", ["20260520", "2026-02-30", "not-a-date"])
def test_bocyl_date_validation_rejects_invalid_dates(value):
    with pytest.raises(ValueError):
        validate_bocyl_date(value)


def test_bocyl_source_record_creation(repository):
    source = repository.ensure_official_source_bocyl()

    assert source["code"] == "BOCYL"
    assert source["name"] == "Boletín Oficial de Castilla y León"
    assert source["jurisdiction"] == "autonomous"
    assert source["region_code"] == "ES-CL"
    assert source["access_type"] == "official_json"
    assert source["reliability_level"] == "canonical"


def test_date_response_parses_documents_and_preserves_urls():
    payload = _fixture_bytes("bocyl_date_with_documents.json")

    issue = parse_bocyl_date_response(payload, target_date="2026-05-20")

    assert issue.status == "success"
    assert issue.issue_identifier == "94/2026"
    assert issue.raw_payload_sha256 == sha256_bytes(payload)
    assert len(issue.documents) == 2
    assert issue.documents[0].external_id == "BOCYL:BOCYL-D-20052026-94-1"
    assert issue.documents[0].official_identifier == "BOCYL-D-20052026-94-1"
    assert issue.documents[0].publication_date == "2026-05-20"
    assert issue.documents[0].department == "CONSEJERIA DE LA PRESIDENCIA"
    assert issue.documents[0].section == "I. COMUNIDAD DE CASTILLA Y LEON"
    assert issue.documents[0].document_type == "RESOLUCION"
    assert issue.documents[0].url_html.endswith("/BOCYL-D-20052026-94-1.do")
    assert issue.documents[0].url_xml.endswith("/BOCYL-D-20052026-94-1.xml")
    assert issue.documents[0].url_pdf.endswith("/BOCYL-D-20052026-94-1.pdf")
    assert issue.documents[0].raw_metadata["issue_identifier"] == "94/2026"
    assert issue.documents[0].raw_metadata["document_identifier"] == "BOCYL-D-20052026-94-1"


def test_date_response_records_no_publication():
    payload = _fixture_bytes("bocyl_date_no_publication.json")

    issue = parse_bocyl_date_response(payload, target_date="2026-05-17")

    assert issue.status == "no_publication"
    assert issue.issue_identifier is None
    assert issue.documents == []
    assert issue.raw_payload_sha256 == sha256_bytes(payload)


def test_document_metadata_normalizes_identifier_and_citation_fields():
    payload = _fixture_bytes("bocyl_document_metadata.json")

    metadata = parse_bocyl_document_metadata(payload)

    assert metadata.external_id == "BOCYL:BOCYL-D-20052026-94-1"
    assert metadata.official_identifier == "BOCYL-D-20052026-94-1"
    assert metadata.publication_date == "2026-05-20"
    assert metadata.title.startswith("RESOLUCION de 15 de mayo de 2026")
    assert metadata.department == "CONSEJERIA DE LA PRESIDENCIA"
    assert metadata.section == "I. COMUNIDAD DE CASTILLA Y LEON"
    assert metadata.document_type == "RESOLUCION"
    assert metadata.raw_metadata["metadata_sha256"] == sha256_bytes(payload)


def test_raw_hash_is_computed_before_parsing():
    payload = _fixture_bytes("bocyl_date_with_documents.json")

    parsed = parse_bocyl_date_response(payload, target_date="2026-05-20")
    reparsed = parse_bocyl_date_response(payload + b"\n", target_date="2026-05-20")

    assert parsed.raw_payload_sha256 != reparsed.raw_payload_sha256


def test_bocyl_ingestion_stores_documents_without_pdf_or_candidates(repository):
    payload = _fixture_bytes("bocyl_date_with_documents.json")

    run = ingest_bocyl_date(repository, target_date="2026-05-20", date_payload=payload)

    document = repository.get_document_by_external_id("BOCYL:BOCYL-D-20052026-94-1")
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
    assert run["issue_identifier"] == "94/2026"
    assert run["documents_fetched"] == 2
    assert run["documents_new"] == 2
    assert document["source_code"] == "BOCYL"
    assert document["url_xml"].endswith("/BOCYL-D-20052026-94-1.xml")
    assert raw_file_count == 2
    assert pdf_file_count == 0
    assert candidate_count == 0
    assert attempt_count == 0
    assert run["source_snapshot_hash"] == sha256_bytes(payload)


def test_bocyl_ingestion_records_no_publication(repository):
    run = ingest_bocyl_date(
        repository,
        target_date="2026-05-17",
        date_payload=_fixture_bytes("bocyl_date_no_publication.json"),
    )

    assert run["status"] == "no_publication"
    assert run["documents_fetched"] == 0
    assert run["issue_identifier"] is None
    assert repository.list_documents_by_date("2026-05-17") == []


def test_bocyl_ingestion_supports_citation_generation(repository):
    run = ingest_bocyl_date(
        repository,
        target_date="2026-05-20",
        date_payload=_fixture_bytes("bocyl_date_with_documents.json"),
    )

    citation = build_citation(repository, "BOCYL:BOCYL-D-20052026-94-1")

    assert run["status"] == "success"
    assert citation["source_code"] == "BOCYL"
    assert citation["external_id"] == "BOCYL:BOCYL-D-20052026-94-1"
    assert citation["official_url"].endswith("/BOCYL-D-20052026-94-1.do")


def test_bocyl_date_api_url_uses_official_filter():
    url = build_bocyl_date_api_url("2026-05-20")

    assert "jcyl.opendatasoft.com/api/explore/v2.1/catalog/datasets/bocyl/records" in url
    assert "fecha_publicacion" in url
    assert "2026-05-20" in url
