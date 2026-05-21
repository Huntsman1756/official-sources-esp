from __future__ import annotations

from pathlib import Path

import pytest

from official_sources.citation.builder import build_citation
from official_sources.integrity.hashing import sha256_bytes
from official_sources.sources.bocm.client import (
    build_bocm_document_json_url,
    build_bocm_document_xml_url,
    validate_bocm_date,
)
from official_sources.sources.bocm.ingestion import BOCM_PAYLOAD_SEPARATOR, ingest_bocm_date
from official_sources.sources.bocm.parser import (
    parse_bocm_document_jsonld,
    parse_bocm_document_xml,
    parse_bocm_issue_page,
    parse_bocm_search_day_response,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _fixture_bytes(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


@pytest.mark.parametrize("value", ["2026-05-20", "1980-01-01"])
def test_bocm_date_validation_accepts_iso_dates(value):
    assert validate_bocm_date(value).isoformat() == value


@pytest.mark.parametrize("value", ["20260520", "2026-02-30", "not-a-date"])
def test_bocm_date_validation_rejects_invalid_dates(value):
    with pytest.raises(ValueError):
        validate_bocm_date(value)


def test_bocm_source_record_creation(repository):
    source = repository.ensure_official_source_bocm()

    assert source["code"] == "BOCM"
    assert source["name"] == "Boletin Oficial de la Comunidad de Madrid"
    assert source["jurisdiction"] == "autonomous"
    assert source["region_code"] == "ES-MD"
    assert source["access_type"] == "official_html"
    assert source["reliability_level"] == "canonical"


def test_search_day_response_resolves_issue():
    payload = _fixture_bytes("bocm_search_day_with_issue.html")

    discovery = parse_bocm_search_day_response(payload, target_date="2026-05-20")

    assert discovery.status == "success"
    assert discovery.issue_identifier == "bocm-20260520-118"
    assert discovery.issue_number == "118"
    assert discovery.issue_url == "https://www.bocm.es/boletin/bocm-20260520-118"
    assert discovery.raw_payload_sha256 == sha256_bytes(payload)


def test_search_day_response_records_no_publication():
    payload = _fixture_bytes("bocm_search_day_no_publication.html")

    discovery = parse_bocm_search_day_response(payload, target_date="2026-05-17")

    assert discovery.status == "no_publication"
    assert discovery.issue_identifier is None
    assert discovery.issue_number is None
    assert discovery.issue_url is None


def test_issue_page_parses_document_list_and_preserves_urls():
    payload = _fixture_bytes("bocm_issue_page.html")

    issue = parse_bocm_issue_page(
        payload,
        target_date="2026-05-20",
        issue_identifier="bocm-20260520-118",
        issue_url="https://www.bocm.es/boletin/bocm-20260520-118",
    )

    assert issue.raw_payload_sha256 == sha256_bytes(payload)
    assert len(issue.documents) == 2
    assert issue.documents[0].official_identifier == "BOCM-20260520-37"
    assert issue.documents[0].external_id == "BOCM:BOCM-20260520-37"
    assert issue.documents[0].url_html == "https://www.bocm.es/bocm-20260520-37"
    assert issue.documents[0].url_xml == build_bocm_document_xml_url("BOCM-20260520-37")
    assert issue.documents[0].raw_metadata["url_jsonld"] == build_bocm_document_json_url(
        "BOCM-20260520-37"
    )
    assert issue.documents[0].url_pdf == (
        "https://www.bocm.es/boletin/CM_Orden_BOCM/2026/05/20/BOCM-20260520-37.PDF"
    )


def test_issue_summary_xml_parses_document_list_and_preserves_urls():
    payload = _fixture_bytes("bocm_issue_summary.xml")

    issue = parse_bocm_issue_page(
        payload,
        target_date="2026-05-20",
        issue_identifier="bocm-20260520-118",
        issue_url="https://www.bocm.es/boletin/bocm-20260520-118",
    )

    assert issue.raw_payload_sha256 == sha256_bytes(payload)
    assert len(issue.documents) == 1
    assert issue.documents[0].official_identifier == "BOCM-20260520-37"
    assert issue.documents[0].section == "I. COMUNIDAD DE MADRID"
    assert issue.documents[0].document_type == "ADENDA"
    assert issue.documents[0].raw_metadata["url_jsonld"] == build_bocm_document_json_url(
        "BOCM-20260520-37"
    )


def test_document_xml_fixture_parses_metadata():
    payload = _fixture_bytes("bocm_document.xml")

    metadata = parse_bocm_document_xml(payload)

    assert metadata.official_identifier == "BOCM-20260520-37"
    assert metadata.publication_date == "2026-05-20"
    assert metadata.department == "CONSEJERIA DE EDUCACION, CIENCIA Y UNIVERSIDADES"
    assert metadata.document_type == "ADENDA"
    assert metadata.url_xml == build_bocm_document_xml_url("BOCM-20260520-37")
    assert metadata.raw_metadata["xml_sha256"] == sha256_bytes(payload)


def test_document_jsonld_fixture_preserves_official_metadata():
    payload = _fixture_bytes("bocm_document_jsonld.json")

    metadata = parse_bocm_document_jsonld(payload)

    assert metadata.official_identifier == "BOCM-20260520-37"
    assert metadata.title.startswith("Adenda de prórroga")
    assert metadata.url_html == "https://www.bocm.es/bocm-20260520-37"
    assert metadata.raw_metadata["jsonld_sha256"] == sha256_bytes(payload)


def test_raw_hash_is_computed_before_parsing():
    payload = _fixture_bytes("bocm_search_day_with_issue.html")

    parsed = parse_bocm_search_day_response(payload, target_date="2026-05-20")
    reparsed = parse_bocm_search_day_response(payload + b"\n", target_date="2026-05-20")

    assert parsed.raw_payload_sha256 != reparsed.raw_payload_sha256


def test_bocm_ingestion_stores_documents_without_pdf_or_candidates(repository):
    search_payload = _fixture_bytes("bocm_search_day_with_issue.html")
    issue_payload = _fixture_bytes("bocm_issue_page.html")

    run = ingest_bocm_date(
        repository,
        target_date="2026-05-20",
        search_payload=search_payload,
        issue_payload=issue_payload,
    )

    document = repository.get_document_by_external_id("BOCM:BOCM-20260520-37")
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
    assert run["issue_identifier"] == "bocm-20260520-118"
    assert run["documents_fetched"] == 2
    assert run["documents_new"] == 2
    assert document["source_code"] == "BOCM"
    assert document["url_xml"] == build_bocm_document_xml_url("BOCM-20260520-37")
    assert raw_file_count == 2
    assert pdf_file_count == 0
    assert candidate_count == 0
    assert attempt_count == 0
    assert run["source_snapshot_hash"] == sha256_bytes(
        search_payload + BOCM_PAYLOAD_SEPARATOR + issue_payload
    )


def test_bocm_ingestion_records_no_publication(repository):
    run = ingest_bocm_date(
        repository,
        target_date="2026-05-17",
        search_payload=_fixture_bytes("bocm_search_day_no_publication.html"),
    )

    assert run["status"] == "no_publication"
    assert run["documents_fetched"] == 0
    assert run["issue_identifier"] is None
    assert repository.list_documents_by_date("2026-05-17") == []


def test_bocm_ingestion_supports_citation_generation(repository):
    run = ingest_bocm_date(
        repository,
        target_date="2026-05-20",
        search_payload=_fixture_bytes("bocm_search_day_with_issue.html"),
        issue_payload=_fixture_bytes("bocm_issue_page.html"),
    )

    citation = build_citation(repository, "BOCM:BOCM-20260520-37")

    assert run["status"] == "success"
    assert citation["source_code"] == "BOCM"
    assert citation["external_id"] == "BOCM:BOCM-20260520-37"
    assert citation["official_url"] == "https://www.bocm.es/bocm-20260520-37"
