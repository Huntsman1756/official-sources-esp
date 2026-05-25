from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path

import pytest

import official_sources.html_monitor as html_monitor
from official_sources.html_monitor import (
    HTMLMonitorError,
    build_bop_a_coruna_html_url,
    build_html_entry_hash,
    build_html_monitor_output_path,
    monitor_html_source,
    parse_bop_a_coruna_html,
    select_html_access_method,
)
from official_sources.source_coverage import list_monitorable_sources
from official_sources.source_registry import get_source, load_source_registry

FIXTURES = Path(__file__).parent / "fixtures"


def _fixture_bytes(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


def test_bop_a_coruna_html_access_method_exists_in_registry():
    source = get_source("BOP_A_CORUNA")
    method = select_html_access_method(source)

    assert source["operational_status"] == "monitor_validated"
    assert source["monitor_support"] == "available"
    assert method["type"] == "html"
    assert method["status"] == "validated"
    assert method["url"] == (
        "https://bop.dacoruna.gal/bopportal/"
        "cambioBoletin.do?fechaInput={date_ddmmyyyy}"
    )
    assert source["candidate_creation_allowed"] is False
    assert source["evidence_grade_allowed"] is False


def test_build_bop_a_coruna_html_url_is_one_date_request():
    assert build_bop_a_coruna_html_url(
        "https://bop.dacoruna.gal/bopportal/cambioBoletin.do?fechaInput={date_ddmmyyyy}",
        target_date="2026-05-25",
    ) == "https://bop.dacoruna.gal/bopportal/cambioBoletin.do?fechaInput=25%2F05%2F2026"


def test_parse_bop_a_coruna_fixture_emits_metadata_only_records():
    raw = _fixture_bytes("bop_a_coruna_latest.html")
    page_url = "https://bop.dacoruna.gal/bopportal/cambioBoletin.do?fechaInput=25%2F05%2F2026"

    result = parse_bop_a_coruna_html(
        raw,
        source_code="BOP_A_CORUNA",
        page_url=page_url,
        published_at="2026-05-25",
        discovered_at="2026-05-25T00:00:00Z",
        monitor_run_id="run-1",
    )

    assert result.raw_page_hash == hashlib.sha256(raw).hexdigest()
    assert len(result.records) == 1
    record = result.records[0]
    assert record["source_code"] == "BOP_A_CORUNA"
    assert record["page_url"] == page_url
    assert record["page_format"] == "html"
    assert record["document_id"] == "2026/3193"
    assert record["entry_id"] == "717669"
    assert record["title"] == "Resolucion de perdida del derecho al accesit del premio provincial"
    assert record["published_at"] == "2026-05-25"
    assert record["official_url"] == "https://bop.dacoruna.gal/bopportal/2026_0000003193.html"
    assert record["raw_page_hash"] == hashlib.sha256(raw).hexdigest()
    assert record["classification_status"] == "unclassified"
    assert record["evidence_status"] == "not_evidence"
    assert record["candidate_status"] == "not_candidate"
    assert "pdf_url" not in record


def test_html_entry_hash_prefers_source_published_at_and_official_url():
    assert build_html_entry_hash(
        source_code="BOP_A_CORUNA",
        published_at="2026-05-25",
        official_url="https://bop.dacoruna.gal/bopportal/2026_0000003193.html",
        document_id="ignored",
        title="ignored",
    ) == hashlib.sha256(
        b"BOP_A_CORUNA"
        b"2026-05-25"
        b"https://bop.dacoruna.gal/bopportal/2026_0000003193.html"
    ).hexdigest()


def test_monitor_html_source_fetches_one_bounded_request():
    requested_urls = []

    def fetcher(url: str) -> bytes:
        requested_urls.append(url)
        return _fixture_bytes("bop_a_coruna_latest.html")

    result = monitor_html_source(
        get_source("BOP_A_CORUNA"),
        fetcher=fetcher,
        target_date="2026-05-25",
        limit=1,
    )

    assert requested_urls == [
        "https://bop.dacoruna.gal/bopportal/cambioBoletin.do?fechaInput=25%2F05%2F2026"
    ]
    assert len(result.records) == 1
    assert result.records[0]["candidate_status"] == "not_candidate"
    assert result.records[0]["evidence_status"] == "not_evidence"


def test_html_monitor_refuses_source_without_validated_html_access_method():
    with pytest.raises(HTMLMonitorError) as exc_info:
        select_html_access_method(get_source("BOP_ZARAGOZA"))

    assert "does not have a validated html access method" in str(exc_info.value)


def test_html_monitor_has_no_candidate_evidence_or_artifact_code_paths():
    source = inspect.getsource(html_monitor)

    assert "create_source_candidate" not in source
    assert "ArtifactDownloader" not in source
    assert "download_pdf" not in source.lower()
    assert "evidence_grade" not in source


def test_html_jsonl_output_path_is_source_and_date_scoped(tmp_path):
    assert build_html_monitor_output_path(tmp_path, "BOP_A_CORUNA", "2026-05-25") == (
        tmp_path / "BOP_A_CORUNA" / "2026-05-25" / "html_discovery.jsonl"
    )


def test_cli_html_monitor_refuses_all_source_runs(capsys):
    from official_sources.cli import run

    exit_code = run(["html", "monitor", "--source", "ALL", "--date", "2026-05-25"])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "one source at a time" in captured.err


def test_cli_html_monitor_refuses_source_without_validated_html(capsys):
    from official_sources.cli import run

    exit_code = run(["html", "monitor", "--source", "BOP_ZARAGOZA", "--date", "2026-05-25"])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "does not have a validated html access method" in captured.err


def test_cli_html_monitor_preview_does_not_write_or_open_repository(tmp_path, monkeypatch, capsys):
    from official_sources import cli

    def fail_open_repository(_db_path: str):
        raise AssertionError("html monitor must not open SQLite")

    monkeypatch.setattr(cli, "_open_repository", fail_open_repository)

    exit_code = cli.run(
        [
            "html",
            "monitor",
            "--source",
            "BOP_A_CORUNA",
            "--date",
            "2026-05-25",
            "--limit",
            "1",
            "--output-root",
            str(tmp_path),
        ],
        html_fetcher=lambda _url: _fixture_bytes("bop_a_coruna_latest.html"),
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "mode=preview" in captured.out
    assert "discovery_metadata_only=true" in captured.out
    assert not list(tmp_path.rglob("*.jsonl"))


def test_cli_html_monitor_write_requires_explicit_write_flag_and_writes_jsonl(tmp_path, capsys):
    from official_sources.cli import run

    exit_code = run(
        [
            "html",
            "monitor",
            "--source",
            "BOP_A_CORUNA",
            "--date",
            "2026-05-25",
            "--limit",
            "1",
            "--write",
            "--output-root",
            str(tmp_path),
        ],
        html_fetcher=lambda _url: _fixture_bytes("bop_a_coruna_latest.html"),
    )
    captured = capsys.readouterr()
    output_path = tmp_path / "BOP_A_CORUNA" / "2026-05-25" / "html_discovery.jsonl"

    assert exit_code == 0
    assert f"output_path={output_path}" in captured.out
    records = [json.loads(line) for line in output_path.read_text(encoding="utf-8").splitlines()]
    assert len(records) == 1
    assert records[0]["source_code"] == "BOP_A_CORUNA"
    assert records[0]["candidate_status"] == "not_candidate"
    assert records[0]["evidence_status"] == "not_evidence"


def test_mcp_source_coverage_sees_bop_a_coruna_as_html_monitorable():
    result = list_monitorable_sources()
    sources = {source["source_code"]: source for source in result["sources"]}
    method_types = {method["type"] for method in sources["BOP_A_CORUNA"]["access_methods"]}

    assert "html" in method_types
    assert sources["BOP_A_CORUNA"]["candidate_creation_allowed"] is False
    assert sources["BOP_A_CORUNA"]["evidence_grade_allowed"] is False


def test_existing_source_registry_validation_still_passes():
    registry = load_source_registry()

    assert len(registry["sources"]) == 65
