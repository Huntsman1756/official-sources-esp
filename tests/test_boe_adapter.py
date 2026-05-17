from __future__ import annotations

import pytest

from official_sources.sources.boe.client import validate_boe_date
from official_sources.sources.boe.ingestion import ingest_boe_summary
from official_sources.sources.boe.parser import parse_boe_summary


@pytest.mark.parametrize("value", ["2024-05-29", "1960-09-01"])
def test_boe_date_input_validation_accepts_iso_dates(value):
    assert validate_boe_date(value).isoformat() == value


@pytest.mark.parametrize("value", ["20240529", "2024-02-30", "1959-12-31", "not-a-date"])
def test_boe_date_input_validation_rejects_invalid_dates(value):
    with pytest.raises(ValueError):
        validate_boe_date(value)


def test_boe_api_response_parsing_using_fixture(boe_summary_payload):
    parsed = parse_boe_summary(boe_summary_payload)

    assert parsed.publication_date == "2024-05-29"
    assert parsed.raw_payload_sha256
    assert parsed.documents[0].external_id == "BOE-A-2024-11111"
    assert parsed.documents[0].url_xml.endswith("BOE-A-2024-11111")


def test_source_snapshot_hash_is_computed_from_raw_payload_before_parsing(boe_summary_payload):
    parsed = parse_boe_summary(boe_summary_payload)

    changed_whitespace = boe_summary_payload + b"\n"
    reparsed = parse_boe_summary(changed_whitespace)

    assert parsed.raw_payload_sha256 != reparsed.raw_payload_sha256


def test_ingestion_persists_documents_and_records_success(repository, boe_summary_payload):
    run = ingest_boe_summary(repository, target_date="2024-05-29", payload=boe_summary_payload)

    document = repository.get_document_by_external_id("BOE-A-2024-11111")
    files = repository.list_document_files(document["id"])

    assert run["status"] == "success"
    assert run["documents_fetched"] == 1
    assert document["url_pdf"].endswith(".pdf")
    assert files[0]["file_type"] == "raw_api_response"
    assert files[0]["source_snapshot_hash"]


def test_ingestion_records_failed_run_when_fetch_fails(repository):
    def failing_fetcher(_target_date: str) -> bytes:
        raise RuntimeError("boom")

    run = ingest_boe_summary(repository, target_date="2024-05-29", fetcher=failing_fetcher)

    assert run["status"] == "failed"
    assert "boom" in run["error_message"]
