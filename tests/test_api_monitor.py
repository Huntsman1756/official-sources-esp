from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path

import pytest

import official_sources.api_monitor as api_monitor
from official_sources.api_monitor import (
    APIMonitorError,
    build_api_entry_hash,
    build_api_monitor_output_path,
    build_bopv_api_url,
    monitor_api_source,
    parse_bopv_api_response,
    select_api_access_method,
)
from official_sources.source_coverage import list_monitorable_sources
from official_sources.source_registry import get_source

FIXTURES = Path(__file__).parent / "fixtures"


def _fixture_bytes(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


def test_bopv_api_access_method_exists_in_registry():
    source = get_source("BOPV")
    method = select_api_access_method(source)

    assert method["type"] == "api"
    assert method["status"] == "validated"
    assert method["url"] == "https://api.euskadi.eus/bopv/administrative-acts/{year}/{month}"


def test_parse_minimal_bopv_api_fixture_emits_metadata_only_records():
    raw = _fixture_bytes("bopv_api_month_page.json")
    api_url = build_bopv_api_url(
        "https://api.euskadi.eus/bopv/administrative-acts/{year}/{month}",
        target_date="2026-05-24",
        limit=1,
    )

    result = parse_bopv_api_response(
        raw,
        source_code="BOPV",
        api_url=api_url,
        api_endpoint="/bopv/administrative-acts/{year}/{month}",
        discovered_at="2026-05-24T00:00:00Z",
        monitor_run_id="run-1",
    )

    assert result.raw_response_hash == hashlib.sha256(raw).hexdigest()
    assert len(result.records) == 1
    record = result.records[0]
    assert record["source_code"] == "BOPV"
    assert record["api_url"] == api_url
    assert record["api_endpoint"] == "/bopv/administrative-acts/{year}/{month}"
    assert record["title"].startswith("RESOLUCION 4520/2026")
    assert record["published_at"] == "2026-05-24T00:00:00Z"
    assert record["document_id"] == "2026/05/2104"
    assert record["api_id"] == "2026/05/2104"
    assert record["summary"] == "AUTORIDADES Y PERSONAL - OSAKIDETZA-SERVICIO VASCO DE SALUD"
    assert record["raw_response_hash"] == hashlib.sha256(raw).hexdigest()
    assert record["classification_status"] == "unclassified"
    assert record["evidence_status"] == "not_evidence"
    assert record["candidate_status"] == "not_candidate"
    assert "text" not in record


def test_api_entry_hash_prefers_source_published_at_and_official_url():
    assert build_api_entry_hash(
        source_code="BOPV",
        published_at="2026-05-24T00:00:00Z",
        official_url="https://api.euskadi.eus/bopv/administrative-acts/2026/5/2104?lang=SPANISH",
        api_id="ignored",
    ) == hashlib.sha256(
        b"BOPV"
        b"2026-05-24T00:00:00Z"
        b"https://api.euskadi.eus/bopv/administrative-acts/2026/5/2104?lang=SPANISH"
    ).hexdigest()


def test_api_entry_hash_falls_back_to_api_id_without_official_url():
    assert build_api_entry_hash(
        source_code="BOPV",
        published_at="2026-05-24T00:00:00Z",
        official_url=None,
        api_id="2026/05/2104",
    ) == hashlib.sha256(b"BOPV2026/05/2104").hexdigest()


def test_monitor_api_source_fetches_one_bounded_bopv_request():
    requested_urls = []

    def fetcher(url: str) -> bytes:
        requested_urls.append(url)
        return _fixture_bytes("bopv_api_month_page.json")

    result = monitor_api_source(
        get_source("BOPV"),
        fetcher=fetcher,
        target_date="2026-05-24",
        limit=1,
    )

    assert requested_urls == [
        "https://api.euskadi.eus/bopv/administrative-acts/2026/5"
        "?currentPage=1&itemsOfPage=1&lang=SPANISH"
    ]
    assert len(result.records) == 1
    assert result.records[0]["candidate_status"] == "not_candidate"
    assert result.records[0]["evidence_status"] == "not_evidence"


def test_api_monitor_refuses_source_without_api_access_method():
    with pytest.raises(APIMonitorError) as exc_info:
        select_api_access_method(get_source("BOCYL"))

    assert "does not have a validated api access method" in str(exc_info.value)


def test_api_monitor_has_no_candidate_evidence_pdf_or_artifact_code_paths():
    source = inspect.getsource(api_monitor)

    assert "create_source_candidate" not in source
    assert "evidence_grade" not in source
    assert "ArtifactDownloader" not in source
    assert "download" not in source.lower()
    assert ".pdf" not in source.lower()


def test_api_jsonl_output_path_is_source_and_date_scoped(tmp_path):
    assert build_api_monitor_output_path(tmp_path, "BOPV", "2026-05-24") == (
        tmp_path / "BOPV" / "2026-05-24" / "api_discovery.jsonl"
    )


def test_cli_api_monitor_refuses_all_source_runs(capsys):
    from official_sources.cli import run

    exit_code = run(["api", "monitor", "--source", "ALL", "--date", "2026-05-24"])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "one source at a time" in captured.err


def test_cli_api_monitor_refuses_non_api_sources(capsys):
    from official_sources.cli import run

    exit_code = run(["api", "monitor", "--source", "BOCYL", "--date", "2026-05-24"])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "does not have a validated api access method" in captured.err


def test_cli_api_monitor_preview_does_not_write_or_open_repository(tmp_path, monkeypatch, capsys):
    from official_sources import cli

    def fail_open_repository(_db_path: str):
        raise AssertionError("api monitor must not open SQLite")

    monkeypatch.setattr(cli, "_open_repository", fail_open_repository)

    exit_code = cli.run(
        [
            "api",
            "monitor",
            "--source",
            "BOPV",
            "--date",
            "2026-05-24",
            "--limit",
            "1",
            "--output-root",
            str(tmp_path),
        ],
        api_fetcher=lambda _url: _fixture_bytes("bopv_api_month_page.json"),
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "mode=preview" in captured.out
    assert "discovery_metadata_only=true" in captured.out
    assert not list(tmp_path.rglob("*.jsonl"))


def test_cli_api_monitor_write_requires_explicit_write_flag_and_writes_jsonl(tmp_path, capsys):
    from official_sources.cli import run

    exit_code = run(
        [
            "api",
            "monitor",
            "--source",
            "BOPV",
            "--date",
            "2026-05-24",
            "--limit",
            "1",
            "--write",
            "--output-root",
            str(tmp_path),
        ],
        api_fetcher=lambda _url: _fixture_bytes("bopv_api_month_page.json"),
    )
    captured = capsys.readouterr()
    output_path = tmp_path / "BOPV" / "2026-05-24" / "api_discovery.jsonl"

    assert exit_code == 0
    assert f"output_path={output_path}" in captured.out
    records = [json.loads(line) for line in output_path.read_text(encoding="utf-8").splitlines()]
    assert len(records) == 1
    assert records[0]["source_code"] == "BOPV"
    assert records[0]["candidate_status"] == "not_candidate"
    assert records[0]["evidence_status"] == "not_evidence"


def test_mcp_source_coverage_sees_bopv_as_api_monitorable():
    result = list_monitorable_sources()
    sources = {source["source_code"]: source for source in result["sources"]}
    method_types = {method["type"] for method in sources["BOPV"]["access_methods"]}

    assert "api" in method_types
