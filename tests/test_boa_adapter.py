from __future__ import annotations

from pathlib import Path

import pytest

from official_sources.citation.builder import build_citation
from official_sources.integrity.hashing import sha256_bytes
from official_sources.sources.boa.client import build_boa_date_url, validate_boa_date
from official_sources.sources.boa.ingestion import ingest_boa_date
from official_sources.sources.boa.parser import parse_boa_date_response, parse_boa_document_metadata

FIXTURES = Path(__file__).parent / "fixtures"


def _fixture_bytes(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


@pytest.mark.parametrize("value", ["2026-01-28", "2010-01-04"])
def test_boa_date_validation_accepts_iso_dates(value):
    assert validate_boa_date(value).isoformat() == value


@pytest.mark.parametrize("value", ["20260128", "2026-02-30", "not-a-date"])
def test_boa_date_validation_rejects_invalid_dates(value):
    with pytest.raises(ValueError):
        validate_boa_date(value)


def test_boa_source_record_creation(repository):
    source = repository.ensure_official_source_boa()

    assert source["code"] == "BOA"
    assert source["name"] == "Boletín Oficial de Aragón"
    assert source["jurisdiction"] == "autonomous"
    assert source["region_code"] == "ES-AR"
    assert source["access_type"] == "official_json"
    assert source["reliability_level"] == "canonical"


def test_boa_date_response_parses_documents_and_preserves_urls():
    payload = _fixture_bytes("boa_date_with_documents.json")

    issue = parse_boa_date_response(payload, target_date="2026-01-28")

    assert issue.status == "success"
    assert issue.issue_identifier == "18/2026"
    assert issue.raw_payload_sha256 == sha256_bytes(payload)
    assert len(issue.documents) == 2
    assert issue.documents[0].external_id == "BOA:007955475"
    assert issue.documents[0].official_identifier == "007955475"
    assert issue.documents[0].publication_date == "2026-01-28"
    assert (
        issue.documents[0].department
        == "DEPARTAMENTO DE HACIENDA, INTERIOR Y ADMINISTRACION PUBLICA"
    )
    assert issue.documents[0].section == "I. Disposiciones Generales"
    assert issue.documents[0].document_type == "CORRECCION - ORDEN"
    assert issue.documents[0].url_pdf == (
        "https://www.boa.aragon.es/cgi-bin/EBOA/BRSCGI?CMD=VEROBJ&MLKOB=1432645850303"
    )
    assert issue.documents[0].url_html is None
    assert issue.documents[0].url_xml is None
    assert issue.documents[0].raw_metadata["issue_identifier"] == "18/2026"
    assert issue.documents[0].raw_metadata["issue_pdf_url"].endswith("MLKOB=1432643830202")


def test_boa_date_response_records_no_publication_html():
    payload = _fixture_bytes("boa_date_no_publication.html")

    issue = parse_boa_date_response(payload, target_date="2026-01-25")

    assert issue.status == "no_publication"
    assert issue.issue_identifier is None
    assert issue.documents == []
    assert issue.raw_payload_sha256 == sha256_bytes(payload)


def test_boa_document_metadata_normalizes_identifier_and_citation_fields():
    payload = _fixture_bytes("boa_document_metadata.json")

    metadata = parse_boa_document_metadata(payload)

    assert metadata.external_id == "BOA:007955475"
    assert metadata.official_identifier == "007955475"
    assert metadata.publication_date == "2026-01-28"
    assert metadata.title.startswith("CORRECCION de errores")
    assert metadata.department == "DEPARTAMENTO DE HACIENDA, INTERIOR Y ADMINISTRACION PUBLICA"
    assert metadata.section == "I. Disposiciones Generales"
    assert metadata.document_type == "CORRECCION - ORDEN"
    assert metadata.raw_metadata["metadata_sha256"] == sha256_bytes(payload)


def test_boa_ingestion_stores_metadata_without_artifacts_or_candidates(repository):
    payload = _fixture_bytes("boa_date_with_documents.json")

    run = ingest_boa_date(repository, target_date="2026-01-28", date_payload=payload)

    document = repository.get_document_by_external_id("BOA:007955475")
    files = repository.list_document_files(document["id"])
    candidate_count = repository.connection.execute(
        "SELECT COUNT(*) AS count FROM source_candidates"
    ).fetchone()["count"]
    artifact_attempt_count = repository.connection.execute(
        "SELECT COUNT(*) AS count FROM artifact_download_attempts"
    ).fetchone()["count"]
    non_raw_file_count = repository.connection.execute(
        "SELECT COUNT(*) AS count FROM document_files WHERE file_type != 'raw_api_response'"
    ).fetchone()["count"]

    assert run["status"] == "success"
    assert run["issue_identifier"] == "18/2026"
    assert run["documents_fetched"] == 2
    assert run["documents_new"] == 2
    assert document["source_code"] == "BOA"
    assert document["url_pdf"].endswith("MLKOB=1432645850303")
    assert files[0]["official_url"] == build_boa_date_url("2026-01-28")
    assert files[0]["media_type"] == "application/json"
    assert candidate_count == 0
    assert artifact_attempt_count == 0
    assert non_raw_file_count == 0
    assert run["source_snapshot_hash"] == sha256_bytes(payload)


def test_boa_ingestion_records_no_publication(repository):
    run = ingest_boa_date(
        repository,
        target_date="2026-01-25",
        date_payload=_fixture_bytes("boa_date_no_publication.html"),
    )

    assert run["status"] == "no_publication"
    assert run["documents_fetched"] == 0
    assert run["issue_identifier"] is None
    assert repository.list_documents_by_date("2026-01-25") == []


def test_boa_ingestion_supports_citation_generation(repository):
    run = ingest_boa_date(
        repository,
        target_date="2026-01-28",
        date_payload=_fixture_bytes("boa_date_with_documents.json"),
    )

    citation = build_citation(repository, "BOA:007955475")

    assert run["status"] == "success"
    assert citation["source_code"] == "BOA"
    assert citation["external_id"] == "BOA:007955475"
    assert citation["official_url"].endswith("MLKOB=1432645850303")
