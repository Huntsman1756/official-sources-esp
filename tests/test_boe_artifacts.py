from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from official_sources.integrity.hashing import sha256_bytes
from official_sources.mcp import tools
from official_sources.sources.boe.artifacts import (
    BOEArtifactDownloader,
    BOEArtifactDownloadError,
    validate_boe_artifact_url,
)


def _seed_document(repository):
    source = repository.get_source_by_code("BOE")
    return repository.upsert_document(
        source_id=source["id"],
        external_id="BOE-A-2024-11111",
        publication_date="2024-05-29",
        title="Document with artifacts",
        url_xml="https://www.boe.es/diario_boe/xml.php?id=BOE-A-2024-11111",
        url_html="https://www.boe.es/diario_boe/txt.php?id=BOE-A-2024-11111",
        url_pdf="https://www.boe.es/boe/dias/2024/05/29/pdfs/BOE-A-2024-11111.pdf",
    )


def _client_with_payloads(payloads: dict[str, bytes]) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        content = payloads[str(request.url)]
        return httpx.Response(
            200, content=content, headers={"content-type": "application/octet-stream"}
        )

    return httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=False, timeout=5.0)


def _fixture_bytes(name: str) -> bytes:
    return (Path(__file__).parent / "fixtures" / name).read_bytes()


@pytest.mark.parametrize(
    ("artifact_type", "url_field", "fixture_name", "expected_name"),
    [
        ("xml", "url_xml", "boe_document.xml", "document.xml"),
        ("html", "url_html", "boe_document.html", "document.html"),
        ("pdf", "url_pdf", "boe_document.pdf", "document.pdf"),
    ],
)
def test_boe_artifact_download_from_mocked_official_url(
    repository, tmp_path, artifact_type, url_field, fixture_name, expected_name
):
    document = _seed_document(repository)
    payload = _fixture_bytes(fixture_name)
    client = _client_with_payloads({document[url_field]: payload})
    run = repository.create_ingestion_run(source_code="BOE", target_date="2024-05-29")

    downloader = BOEArtifactDownloader(
        repository,
        cache_dir=tmp_path,
        client=client,
        sleeper=lambda _seconds: None,
    )
    results = downloader.download_document_artifacts(
        external_id=document["external_id"],
        artifact_types=[artifact_type],
        ingestion_run_id=run["id"],
    )

    file_record = results[artifact_type]
    assert file_record["file_type"] == artifact_type
    assert file_record["sha256"] == sha256_bytes(payload)
    assert file_record["source_snapshot_hash"] == sha256_bytes(payload)
    assert file_record["signature_status"] == "not_checked"
    assert Path(file_record["local_path"]).name == expected_name
    assert Path(file_record["local_path"]).read_bytes() == payload
    attempts = repository.list_artifact_download_attempts(document_id=document["id"])
    assert attempts[-1]["file_type"] == artifact_type
    assert attempts[-1]["status"] == "success"
    assert attempts[-1]["http_status"] == 200


@pytest.mark.parametrize(
    "url",
    [
        "http://www.boe.es/diario_boe/xml.php?id=BOE-A-2024-11111",
        "file:///tmp/document.xml",
        "C:/tmp/document.xml",
    ],
)
def test_unsupported_url_is_rejected(url):
    with pytest.raises(BOEArtifactDownloadError):
        validate_boe_artifact_url(url)


def test_non_boe_url_is_rejected():
    with pytest.raises(BOEArtifactDownloadError):
        validate_boe_artifact_url("https://example.com/document.xml")


def test_artifact_hash_unchanged_updates_integrity_timestamps(repository, tmp_path):
    document = _seed_document(repository)
    payload = _fixture_bytes("boe_document.xml")
    client = _client_with_payloads({document["url_xml"]: payload})
    downloader = BOEArtifactDownloader(
        repository,
        cache_dir=tmp_path,
        client=client,
        sleeper=lambda _seconds: None,
    )
    run_one = repository.create_ingestion_run(source_code="BOE", target_date="2024-05-29")
    first = downloader.download_document_artifacts(
        external_id=document["external_id"],
        artifact_types=["xml"],
        ingestion_run_id=run_one["id"],
    )["xml"]
    run_two = repository.create_ingestion_run(source_code="BOE", target_date="2024-05-29")

    second = downloader.download_document_artifacts(
        external_id=document["external_id"],
        artifact_types=["xml"],
        ingestion_run_id=run_two["id"],
    )["xml"]
    checks = repository.list_integrity_checks(first["id"])

    assert second["sha256"] == first["sha256"]
    assert second["last_seen_at"] >= first["last_seen_at"]
    assert second["last_integrity_check_at"] >= first["last_integrity_check_at"]
    assert second["previous_hash"] is None
    assert second["content_changed_at"] is None
    assert checks[-1]["changed"] == 0


def test_artifact_hash_changed_preserves_previous_hash_and_creates_integrity_event(
    repository, tmp_path
):
    document = _seed_document(repository)
    first_payload = b"<document><text>first</text></document>"
    second_payload = b"<document><text>second</text></document>"
    current_payload = first_payload

    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == document["url_xml"]
        return httpx.Response(200, content=current_payload)

    client = httpx.Client(
        transport=httpx.MockTransport(handler), follow_redirects=False, timeout=5.0
    )
    downloader = BOEArtifactDownloader(
        repository,
        cache_dir=tmp_path,
        client=client,
        sleeper=lambda _seconds: None,
    )
    run_one = repository.create_ingestion_run(source_code="BOE", target_date="2024-05-29")
    first = downloader.download_document_artifacts(
        external_id=document["external_id"],
        artifact_types=["xml"],
        ingestion_run_id=run_one["id"],
    )["xml"]
    current_payload = second_payload
    run_two = repository.create_ingestion_run(source_code="BOE", target_date="2024-05-30")

    second = downloader.download_document_artifacts(
        external_id=document["external_id"],
        artifact_types=["xml"],
        ingestion_run_id=run_two["id"],
    )["xml"]
    checks = repository.list_integrity_checks(first["id"])

    assert second["sha256"] == sha256_bytes(second_payload)
    assert second["previous_hash"] == sha256_bytes(first_payload)
    assert second["content_changed_at"] is not None
    assert second["change_detected_by"] == run_two["id"]
    assert checks[-1]["previous_sha256"] == sha256_bytes(first_payload)
    assert checks[-1]["current_sha256"] == sha256_bytes(second_payload)
    assert checks[-1]["changed"] == 1
    attempts = repository.list_artifact_download_attempts(document_id=document["id"])
    assert attempts[-1]["status"] == "changed"


def test_failed_download_creates_artifact_download_attempt_with_error(repository, tmp_path):
    document = _seed_document(repository)

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, content=b"unavailable")

    client = httpx.Client(
        transport=httpx.MockTransport(handler), follow_redirects=False, timeout=5.0
    )
    downloader = BOEArtifactDownloader(
        repository,
        cache_dir=tmp_path,
        client=client,
        sleeper=lambda _seconds: None,
    )
    run = repository.create_ingestion_run(source_code="BOE", target_date="2024-05-29")

    with pytest.raises(BOEArtifactDownloadError):
        downloader.download_document_artifacts(
            external_id=document["external_id"],
            artifact_types=["xml"],
            ingestion_run_id=run["id"],
        )

    attempts = repository.list_artifact_download_attempts(document_id=document["id"])
    assert attempts[-1]["status"] == "failed"
    assert attempts[-1]["http_status"] == 503
    assert "HTTP 503" in attempts[-1]["error_message"]


def test_artifact_download_attempt_records_retry_and_throttle_information(repository, tmp_path):
    document = _seed_document(repository)
    responses = [httpx.Response(503, content=b"unavailable"), httpx.Response(200, content=b"<x/>")]

    def handler(_request: httpx.Request) -> httpx.Response:
        return responses.pop(0)

    client = httpx.Client(
        transport=httpx.MockTransport(handler), follow_redirects=False, timeout=5.0
    )
    downloader = BOEArtifactDownloader(
        repository,
        cache_dir=tmp_path,
        client=client,
        sleeper=lambda _seconds: None,
    )

    downloader.download_document_artifacts(
        external_id=document["external_id"],
        artifact_types=["xml"],
        ingestion_run_id=None,
    )

    attempts = repository.list_artifact_download_attempts(document_id=document["id"])
    assert attempts[-1]["status"] == "success"
    assert attempts[-1]["retry_count"] == 1
    assert attempts[-1]["throttle_triggered"] == 1


def test_rejected_non_boe_url_creates_failure_attempt_without_fetching(repository, tmp_path):
    source = repository.get_source_by_code("BOE")
    document = repository.upsert_document(
        source_id=source["id"],
        external_id="BOE-A-2024-11111",
        publication_date="2024-05-29",
        title="Bad URL",
        url_xml="https://example.com/document.xml",
    )
    called = False

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal called
        called = True
        return httpx.Response(200, content=b"unsafe")

    client = httpx.Client(
        transport=httpx.MockTransport(handler), follow_redirects=False, timeout=5.0
    )
    downloader = BOEArtifactDownloader(repository, cache_dir=tmp_path, client=client)

    with pytest.raises(BOEArtifactDownloadError):
        downloader.download_document_artifacts(
            external_id=document["external_id"],
            artifact_types=["xml"],
            ingestion_run_id=None,
        )

    attempts = repository.list_artifact_download_attempts(document_id=document["id"])
    assert called is False
    assert attempts[-1]["status"] == "failed"
    assert attempts[-1]["http_status"] is None
    assert "official BOE host" in attempts[-1]["error_message"]


def test_download_attempts_and_integrity_checks_are_separate(repository, tmp_path):
    document = _seed_document(repository)
    payload = _fixture_bytes("boe_document.xml")
    client = _client_with_payloads({document["url_xml"]: payload})
    downloader = BOEArtifactDownloader(repository, cache_dir=tmp_path, client=client)

    file_record = downloader.download_document_artifacts(
        external_id=document["external_id"],
        artifact_types=["xml"],
        ingestion_run_id=None,
    )["xml"]

    attempts = repository.list_artifact_download_attempts(document_id=document["id"])
    checks = repository.list_integrity_checks(document_file_id=file_record["id"])
    assert attempts[-1]["official_url"] == document["url_xml"]
    assert attempts[-1]["status"] == "success"
    assert checks[-1]["change_reason"] == "new_file"
    assert "official_url" not in checks[-1]


def test_xml_and_html_text_extraction_remain_wrapped_in_mcp_output(repository, tmp_path):
    document = _seed_document(repository)
    xml_payload = _fixture_bytes("boe_document.xml")
    html_payload = _fixture_bytes("boe_document.html")
    client = _client_with_payloads(
        {
            document["url_xml"]: xml_payload,
            document["url_html"]: html_payload,
        }
    )
    downloader = BOEArtifactDownloader(repository, cache_dir=tmp_path, client=client)
    downloader.download_document_artifacts(
        external_id=document["external_id"],
        artifact_types=["xml", "html"],
        ingestion_run_id=None,
    )

    result = tools.boe_document_text_get(repository, external_id=document["external_id"])

    assert result["is_official_text"] is True
    assert result["content_type"] == "official_legal_text"
    assert "Ignore previous instructions" in result["content"]


def test_no_mcp_tool_performs_artifact_download():
    import inspect

    source = inspect.getsource(tools)

    assert "ArtifactDownloader" not in source
    assert "download_document_artifacts" not in source
    assert ".get(" not in source
