from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path

import pytest

import official_sources.rss_monitor as rss_monitor
from official_sources.rss_monitor import (
    RSSMonitorError,
    build_entry_hash,
    build_rss_monitor_output_path,
    monitor_source_feed,
    parse_feed,
    select_feed_access_method,
)
from official_sources.source_registry import get_source, load_source_registry

FIXTURES = Path(__file__).parent / "fixtures"


def _fixture_bytes(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


def test_parse_minimal_rss_2_fixture_emits_discovery_metadata():
    raw_feed = _fixture_bytes("rss_monitor_minimal.xml")

    result = parse_feed(
        raw_feed,
        source_code="BOCYL",
        feed_url="https://bocyl.jcyl.es/rss.do",
        discovered_at="2026-05-24T00:00:00Z",
        monitor_run_id="run-1",
    )

    assert result.feed_format == "rss"
    assert len(result.records) == 1
    record = result.records[0]
    assert record["source_code"] == "BOCYL"
    assert record["feed_url"] == "https://bocyl.jcyl.es/rss.do"
    assert record["feed_format"] == "rss"
    assert record["entry_id"] == "https://bocyl.jcyl.es/boletin.do?fechaBoletin=22/05/2026&edicion=96"
    assert record["title"] == "Boletin del dia 22/05/2026 edicion 96"
    assert record["published_at"] == "Fri, 22 May 2026 18:05:45 GMT"
    assert record["updated_at"] is None
    assert record["official_url"] == (
        "https://bocyl.jcyl.es/boletin.do?fechaBoletin=22/05/2026&edicion=96"
    )
    assert record["summary"] == "Resumen metadata-only del boletin."
    assert record["raw_feed_hash"] == hashlib.sha256(raw_feed).hexdigest()
    assert record["classification_status"] == "unclassified"
    assert record["evidence_status"] == "not_evidence"
    assert record["candidate_status"] == "not_candidate"


def test_parse_minimal_atom_fixture_emits_discovery_metadata():
    result = parse_feed(
        _fixture_bytes("atom_monitor_minimal.xml"),
        source_code="BOCYL",
        feed_url="https://bocyl.jcyl.es/atom.do",
        discovered_at="2026-05-24T00:00:00Z",
        monitor_run_id="run-2",
    )

    assert result.feed_format == "atom"
    assert result.records[0]["entry_id"] == "tag:bocyl.jcyl.es,2026:96"
    assert result.records[0]["published_at"] == "2026-05-22T18:05:45Z"
    assert result.records[0]["updated_at"] == "2026-05-22T18:05:46Z"
    assert result.records[0]["summary"] == "Resumen Atom metadata-only."


def test_entry_hash_prefers_source_published_at_and_official_url():
    assert build_entry_hash(
        source_code="BOCYL",
        published_at="2026-05-22T18:05:45Z",
        official_url="https://bocyl.jcyl.es/boletin.do?fechaBoletin=22/05/2026&edicion=96",
        entry_id="ignored",
        title="ignored",
    ) == hashlib.sha256(
        b"BOCYL"
        b"2026-05-22T18:05:45Z"
        b"https://bocyl.jcyl.es/boletin.do?fechaBoletin=22/05/2026&edicion=96"
    ).hexdigest()


def test_entry_hash_falls_back_and_warns_without_official_url():
    result = parse_feed(
        (
            b'<?xml version="1.0"?><rss version="2.0"><channel><item>'
            b"<title>No URL</title><guid>g1</guid></item></channel></rss>"
        ),
        source_code="BOCYL",
        feed_url="https://bocyl.jcyl.es/rss.do",
        discovered_at="2026-05-24T00:00:00Z",
        monitor_run_id="run-3",
    )

    assert result.records[0]["entry_hash"] == hashlib.sha256(b"BOCYLg1No URL").hexdigest()
    assert result.records[0]["warnings"] == ["entry_hash_fallback_missing_official_url"]


def test_bocyl_pilot_access_method_exists_in_registry():
    source = get_source("BOCYL")
    access_method = select_feed_access_method(source)

    assert access_method["type"] == "rss"
    assert access_method["status"] == "validated"
    assert access_method["url"] == "https://bocyl.jcyl.es/rss.do"


@pytest.mark.parametrize(
    ("source_code", "expected_type", "expected_url"),
    [
        ("BOE", "rss", "https://www.boe.es/rss/boe.php"),
        ("BOJA", "atom", "https://www.juntadeandalucia.es/boja/distribucion/boja.xml"),
        ("BOIB", "rss", "https://www.caib.es/eboibfront/es/rss"),
        ("BOC_CANTABRIA", "rss", "https://www.cantabria.es/o/BOC/feed/6802081"),
        ("DOE", "rss", "https://doe.juntaex.es/rss/rss.php?seccion=6"),
    ],
)
def test_expanded_feed_access_methods_exist_in_registry(
    source_code,
    expected_type,
    expected_url,
):
    source = get_source(source_code)
    access_method = select_feed_access_method(source)

    assert access_method["type"] == expected_type
    assert access_method["status"] == "validated"
    assert access_method["url"] == expected_url


@pytest.mark.parametrize(
    ("source_code", "fixture_name"),
    [
        ("BOE", "rss_monitor_minimal.xml"),
        ("BOJA", "atom_monitor_minimal.xml"),
        ("BOIB", "rss_monitor_minimal.xml"),
        ("BOC_CANTABRIA", "rss_monitor_minimal.xml"),
        ("DOE", "rss_monitor_minimal.xml"),
    ],
)
def test_monitor_accepts_expanded_sources_as_discovery_only(source_code, fixture_name):
    result = monitor_source_feed(
        get_source(source_code),
        fetcher=lambda _url: _fixture_bytes(fixture_name),
        target_date="2026-05-24",
        limit=1,
    )

    assert len(result.records) == 1
    assert result.records[0]["source_code"] == source_code
    assert result.records[0]["candidate_status"] == "not_candidate"
    assert result.records[0]["evidence_status"] == "not_evidence"
    assert "candidate_id" not in result.records[0]
    assert "document_id" not in result.records[0]


def test_monitor_source_feed_refuses_source_without_rss_or_atom_method():
    source = {
        "source_code": "TEST",
        "access_methods": [{"type": "json", "url": "https://example.test", "status": "validated"}],
    }

    with pytest.raises(RSSMonitorError) as exc_info:
        monitor_source_feed(
            source,
            fetcher=lambda _url: b"",
            target_date="2026-05-24",
        )

    assert "does not have a validated rss/atom access method" in str(exc_info.value)


def test_monitor_source_feed_limits_records_and_does_not_create_candidates_or_evidence():
    source = get_source("BOCYL")

    result = monitor_source_feed(
        source,
        fetcher=lambda _url: _fixture_bytes("rss_monitor_minimal.xml"),
        target_date="2026-05-24",
        limit=1,
    )

    assert len(result.records) == 1
    assert result.records[0]["candidate_status"] == "not_candidate"
    assert result.records[0]["evidence_status"] == "not_evidence"
    assert "candidate_id" not in result.records[0]
    assert "document_id" not in result.records[0]


def test_rss_monitor_has_no_candidate_evidence_or_artifact_code_paths():
    source = inspect.getsource(rss_monitor)

    assert "create_source_candidate" not in source
    assert "evidence_grade" not in source
    assert "ArtifactDownloader" not in source
    assert "download" not in source.lower()
    assert ".pdf" not in source.lower()


def test_jsonl_output_path_is_source_and_date_scoped(tmp_path):
    assert build_rss_monitor_output_path(tmp_path, "BOCYL", "2026-05-24") == (
        tmp_path / "BOCYL" / "2026-05-24" / "rss_discovery.jsonl"
    )


def test_cli_refuses_all_source_runs(capsys):
    from official_sources.cli import run

    exit_code = run(["rss", "monitor", "--source", "ALL", "--date", "2026-05-24"])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "one source at a time" in captured.err


def test_cli_refuses_source_without_feed(capsys):
    from official_sources.cli import run

    exit_code = run(["rss", "monitor", "--source", "BDNS", "--date", "2026-05-24"])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "does not have a validated rss/atom access method" in captured.err


def test_cli_preview_does_not_write_or_open_repository(tmp_path, monkeypatch, capsys):
    from official_sources import cli

    def fail_open_repository(_db_path: str):
        raise AssertionError("rss monitor must not open SQLite")

    monkeypatch.setattr(cli, "_open_repository", fail_open_repository)

    exit_code = cli.run(
        [
            "rss",
            "monitor",
            "--source",
            "BOCYL",
            "--date",
            "2026-05-24",
            "--output-root",
            str(tmp_path),
        ],
        rss_fetcher=lambda _url: _fixture_bytes("rss_monitor_minimal.xml"),
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "mode=preview" in captured.out
    assert not list(tmp_path.rglob("*.jsonl"))


def test_cli_write_requires_explicit_write_flag_and_writes_jsonl(tmp_path, capsys):
    from official_sources.cli import run

    exit_code = run(
        [
            "rss",
            "monitor",
            "--source",
            "BOCYL",
            "--date",
            "2026-05-24",
            "--limit",
            "1",
            "--write",
            "--output-root",
            str(tmp_path),
        ],
        rss_fetcher=lambda _url: _fixture_bytes("rss_monitor_minimal.xml"),
    )
    captured = capsys.readouterr()
    output_path = tmp_path / "BOCYL" / "2026-05-24" / "rss_discovery.jsonl"

    assert exit_code == 0
    assert f"output_path={output_path}" in captured.out
    records = [json.loads(line) for line in output_path.read_text(encoding="utf-8").splitlines()]
    assert len(records) == 1
    assert records[0]["source_code"] == "BOCYL"
    assert records[0]["candidate_status"] == "not_candidate"


def test_existing_source_registry_validation_still_passes():
    registry = load_source_registry()

    assert len(registry["sources"]) == 22
