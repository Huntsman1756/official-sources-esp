from __future__ import annotations

import httpx
import pytest

from official_sources.sources.boe.client import (
    BOEClient,
    BOESummaryNotFoundError,
    validate_boe_date,
)
from official_sources.sources.boe.http_policy import BOERequestAudit, BOERequestPolicy
from official_sources.sources.boe.ingestion import (
    _payload_indicates_no_publication,
    ingest_boe_summary,
)
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


def test_boe_summary_404_is_not_retried_aggressively():
    requests = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal requests
        requests += 1
        return httpx.Response(404, content=b'{"error":"not found"}', request=request)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    boe_client = BOEClient(
        client=client,
        request_policy=BOERequestPolicy(max_retries=5, requests_per_second=0),
    )

    with pytest.raises(BOESummaryNotFoundError) as exc_info:
        boe_client.fetch_summary("2026-05-17")

    assert requests == 1
    assert exc_info.value.last_http_status == 404
    assert exc_info.value.retry_count == 0
    assert exc_info.value.throttle_triggered is False


def test_ingestion_records_no_publication_for_boe_summary_404(repository):
    def not_found_fetcher(_target_date: str) -> bytes:
        raise BOESummaryNotFoundError(
            "2026-05-17",
            BOERequestAudit(retry_count=0, throttle_triggered=False, last_http_status=404),
        )

    run = ingest_boe_summary(repository, target_date="2026-05-17", fetcher=not_found_fetcher)

    documents = repository.list_documents_by_date("2026-05-17")
    latest = repository.get_latest_ingestion_run("BOE", "2026-05-17")
    assert run["status"] == "no_publication"
    assert run["documents_fetched"] == 0
    assert run["documents_new"] == 0
    assert run["documents_updated"] == 0
    assert run["last_http_status"] == 404
    assert run["retry_count"] == 0
    assert run["throttle_triggered"] == 0
    assert "BOE summary not found for date 2026-05-17" in run["error_message"]
    assert documents == []
    assert latest["status"] == "no_publication"


def test_sunday_probe_style_404_xml_body_maps_to_no_publication():
    payload = b'<?xml version="1.0" encoding="UTF-8"?><error>Not Found</error>'

    assert _payload_indicates_no_publication(payload) is True


def test_holiday_probe_style_valid_summary_is_not_no_publication(boe_summary_payload):
    assert _payload_indicates_no_publication(boe_summary_payload) is False


def test_empty_200_summary_maps_to_no_publication(repository):
    run = ingest_boe_summary(repository, target_date="2025-01-05", payload=b"")

    assert run["status"] == "no_publication"
    assert run["last_http_status"] == 200


def test_json_summary_without_diary_maps_to_no_publication(repository):
    payload = b'{"status":{"code":"200","text":"ok"},"data":{"sumario":{"metadatos":{}}}}'

    run = ingest_boe_summary(repository, target_date="2025-01-05", payload=payload)

    assert run["status"] == "no_publication"
    assert run["documents_fetched"] == 0


def test_malformed_200_summary_still_fails(repository):
    run = ingest_boe_summary(repository, target_date="2025-01-05", payload=b"{bad json")

    assert run["status"] == "failed"
