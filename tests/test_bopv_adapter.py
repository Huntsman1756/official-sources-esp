from __future__ import annotations

from pathlib import Path

import pytest

from official_sources.citation.builder import build_citation
from official_sources.integrity.hashing import sha256_bytes
from official_sources.sources.bopv.client import (
    build_bopv_document_html_url,
    build_bopv_document_pdf_url,
    build_bopv_document_xml_url,
    build_bopv_issue_html_url,
    build_bopv_issue_xml_url,
    validate_bopv_date,
)
from official_sources.sources.bopv.ingestion import BOPV_PAYLOAD_SEPARATOR, ingest_bopv_date
from official_sources.sources.bopv.parser import (
    parse_bopv_calendar,
    parse_bopv_document_xml,
    parse_bopv_issue_xml,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _fixture_bytes(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


@pytest.mark.parametrize("value", ["2026-05-20", "1980-01-01"])
def test_bopv_date_validation_accepts_iso_dates(value):
    assert validate_bopv_date(value).isoformat() == value


@pytest.mark.parametrize("value", ["20260520", "2026-02-30", "not-a-date"])
def test_bopv_date_validation_rejects_invalid_dates(value):
    with pytest.raises(ValueError):
        validate_bopv_date(value)


def test_bopv_source_record_creation(repository):
    source = repository.ensure_official_source_bopv()

    assert source["code"] == "BOPV"
    assert (
        source["name"]
        == "Boletín Oficial del País Vasco / Euskal Herriko Agintaritzaren Aldizkaria"
    )
    assert source["jurisdiction"] == "autonomous"
    assert source["region_code"] == "ES-PV"
    assert source["access_type"] == "official_xml"
    assert source["reliability_level"] == "canonical"


def test_calendar_resolves_date_to_issue_and_preserves_official_urls():
    payload = _fixture_bytes("bopv_calendar_052026.html")

    discovery = parse_bopv_calendar(payload, target_date="2026-05-20")

    assert discovery.status == "success"
    assert discovery.issue_identifiers == ["BOPV-2026-0093"]
    assert discovery.issue_html_urls == [build_bopv_issue_html_url("2026-05-20", "s26_0093")]
    assert discovery.issue_xml_urls == [build_bopv_issue_xml_url("2026-05-20", "s26_0093")]
    assert discovery.raw_payload_sha256 == sha256_bytes(payload)


def test_calendar_records_no_publication_when_date_absent():
    payload = _fixture_bytes("bopv_calendar_no_publication.html")

    discovery = parse_bopv_calendar(payload, target_date="2026-05-17")

    assert discovery.status == "no_publication"
    assert discovery.issue_identifiers == []
    assert discovery.issue_xml_urls == []


def test_issue_xml_parses_documents_and_preserves_artifact_urls():
    payload = _fixture_bytes("bopv_issue_s26_0093.xml")

    issue = parse_bopv_issue_xml(
        payload,
        target_date="2026-05-20",
        issue_identifier="BOPV-2026-0093",
        issue_url=build_bopv_issue_html_url("2026-05-20", "s26_0093"),
    )

    assert issue.raw_payload_sha256 == sha256_bytes(payload)
    assert len(issue.documents) == 3
    assert issue.documents[0].official_identifier == "BOPV-2026-05-2602104a"
    assert issue.documents[0].external_id == "BOPV:BOPV-2026-05-2602104a"
    assert issue.documents[0].department == "OSAKIDETZA-SERVICIO VASCO DE SALUD"
    assert issue.documents[0].section == "AUTORIDADES Y PERSONAL"
    assert issue.documents[0].url_html == build_bopv_document_html_url("2026-05-20", "2602104a")
    assert issue.documents[0].url_xml == build_bopv_document_xml_url("2026-05-20", "2602104a")
    assert issue.documents[0].url_pdf == build_bopv_document_pdf_url("2026-05-20", "2602104a")
    assert issue.documents[0].raw_metadata["issue_xml_sha256"] == sha256_bytes(payload)
    assert issue.documents[0].raw_metadata["order_number"] == "2104"
    assert issue.documents[0].raw_metadata["document_stem"] == "2602104a"


def test_document_xml_fixture_parses_metadata():
    payload = _fixture_bytes("bopv_document_2602104a.xml")

    metadata = parse_bopv_document_xml(
        payload,
        publication_date="2026-05-20",
        document_stem="2602104a",
    )

    assert metadata.official_identifier == "BOPV-2026-05-2602104a"
    assert metadata.publication_date == "2026-05-20"
    assert metadata.department == "OSAKIDETZA-SERVICIO VASCO DE SALUD"
    assert metadata.document_type is None
    assert metadata.url_xml == build_bopv_document_xml_url("2026-05-20", "2602104a")
    assert metadata.raw_metadata["xml_sha256"] == sha256_bytes(payload)


def test_bopv_ingestion_stores_documents_without_pdf_downloads_or_candidates(repository):
    calendar_payload = _fixture_bytes("bopv_calendar_052026.html")
    issue_payload = _fixture_bytes("bopv_issue_s26_0093.xml")

    run = ingest_bopv_date(
        repository,
        target_date="2026-05-20",
        calendar_payload=calendar_payload,
        issue_payloads=[issue_payload],
    )

    document = repository.get_document_by_external_id("BOPV:BOPV-2026-05-2602104a")
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
    assert run["issue_identifier"] == "BOPV-2026-0093"
    assert run["documents_fetched"] == 3
    assert run["documents_new"] == 3
    assert document["source_code"] == "BOPV"
    assert document["url_pdf"] == build_bopv_document_pdf_url("2026-05-20", "2602104a")
    assert raw_file_count == 3
    assert pdf_file_count == 0
    assert candidate_count == 0
    assert attempt_count == 0
    assert run["source_snapshot_hash"] == sha256_bytes(
        calendar_payload + BOPV_PAYLOAD_SEPARATOR + issue_payload
    )


def test_bopv_ingestion_records_no_publication(repository):
    run = ingest_bopv_date(
        repository,
        target_date="2026-05-17",
        calendar_payload=_fixture_bytes("bopv_calendar_no_publication.html"),
    )

    assert run["status"] == "no_publication"
    assert run["documents_fetched"] == 0
    assert run["issue_identifier"] is None
    assert repository.list_documents_by_date("2026-05-17") == []


def test_bopv_ingestion_supports_citation_generation(repository):
    run = ingest_bopv_date(
        repository,
        target_date="2026-05-20",
        calendar_payload=_fixture_bytes("bopv_calendar_052026.html"),
        issue_payloads=[_fixture_bytes("bopv_issue_s26_0093.xml")],
    )

    citation = build_citation(repository, "BOPV:BOPV-2026-05-2602104a")

    assert run["status"] == "success"
    assert citation["source_code"] == "BOPV"
    assert citation["external_id"] == "BOPV:BOPV-2026-05-2602104a"
    assert citation["official_url"] == build_bopv_document_html_url("2026-05-20", "2602104a")
