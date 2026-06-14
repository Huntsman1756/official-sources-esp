from __future__ import annotations

import json
import sqlite3

from official_sources.hermes_freshness_observation_producer import (
    collect_freshness_observations,
    write_observations_jsonl,
)
from official_sources.storage.database import initialize_database


def _read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_collects_monitor_observation_from_discovered_at_not_publication_date(tmp_path):
    output_path = tmp_path / "data" / "rss_monitor" / "BOE" / "2026-06-13" / "rss_discovery.jsonl"
    output_path.parent.mkdir(parents=True)
    output_path.write_text(
        json.dumps(
            {
                "source_code": "BOE",
                "title": "BOE record",
                "published_at": "2026-06-14T12:00:00Z",
                "discovered_at": "2026-06-13T07:30:00Z",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    observations = collect_freshness_observations(runtime_root=tmp_path)

    assert observations == (
        {
            "source": "BOE",
            "observed_at": "2026-06-13T07:30:00Z",
            "observation_kind": "existing_runtime_state",
            "input_path": str(output_path),
            "input_kind": "rss_monitor_jsonl",
            "timestamp_type": "observed",
            "confidence": "operational",
            "reason": "derived from monitor discovered_at",
            "latest_record_date": "2026-06-14T12:00:00Z",
        },
    )


def test_collects_latest_successful_sqlite_ingestion_run_without_using_failed_runs(tmp_path):
    database_path = tmp_path / "official-sources.sqlite"
    with sqlite3.connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        initialize_database(connection)
        connection.executemany(
            """
            INSERT INTO ingestion_runs (
                source_code, run_date, target_date, status, documents_fetched,
                documents_new, documents_updated, started_at, finished_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    "BDNS",
                    "2026-06-11",
                    None,
                    "success",
                    10,
                    0,
                    0,
                    "2026-06-11T07:00:00Z",
                    "2026-06-11T07:05:00Z",
                ),
                (
                    "BDNS",
                    "2026-06-13",
                    None,
                    "failed",
                    0,
                    0,
                    0,
                    "2026-06-13T07:00:00Z",
                    "2026-06-13T07:01:00Z",
                ),
                (
                    "BDNS",
                    "2026-06-12",
                    None,
                    "success",
                    12,
                    0,
                    0,
                    "2026-06-12T07:00:00Z",
                    "2026-06-12T07:05:00Z",
                ),
            ],
        )
        connection.commit()

    observations = collect_freshness_observations(
        runtime_root=tmp_path,
        db_path=database_path,
        source_codes=("BDNS",),
    )

    assert observations == (
        {
            "source": "BDNS",
            "observed_at": "2026-06-12T07:05:00Z",
            "observation_kind": "existing_runtime_state",
            "input_path": str(database_path),
            "input_kind": "sqlite_ingestion_runs",
            "timestamp_type": "observed",
            "confidence": "operational",
            "reason": "derived from successful ingestion_run id=3 status=success; no live fetch",
        },
    )


def test_cli_writes_only_explicit_observations_jsonl(tmp_path, capsys):
    from official_sources.cli import run

    monitor_output = (
        tmp_path / "runtime" / "data" / "rss_monitor" / "BOCM" / "2026-06-13" / "rss_discovery.jsonl"
    )
    monitor_output.parent.mkdir(parents=True)
    monitor_output.write_text(
        json.dumps(
            {
                "source_code": "BOCM",
                "title": "BOCM record",
                "discovered_at": "2026-06-13T08:15:00Z",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    output_path = tmp_path / "freshness-observations.jsonl"

    exit_code = run(
        [
            "hermes",
            "freshness-observations",
            "--runtime-root",
            str(tmp_path / "runtime"),
            "--output",
            str(output_path),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "observations_written=1" in captured.out
    assert captured.err == ""
    assert _read_jsonl(output_path) == [
        {
            "source": "BOCM",
            "observed_at": "2026-06-13T08:15:00Z",
            "observation_kind": "existing_runtime_state",
            "input_path": str(monitor_output),
            "input_kind": "rss_monitor_jsonl",
            "timestamp_type": "observed",
            "confidence": "operational",
            "reason": "derived from monitor discovered_at",
        }
    ]
    assert not (tmp_path / "runtime" / "freshness-observations.jsonl").exists()


def test_collects_monitor_observation_preserves_source_reason(tmp_path):
    output_path = tmp_path / "data" / "api_monitor" / "BDNS" / "2026-06-13" / "api_discovery.jsonl"
    output_path.parent.mkdir(parents=True)
    output_path.write_text(
        json.dumps(
            {
                "source_code": "BDNS",
                "discovered_at": "2026-06-13T10:15:00Z",
                "published_at": "2026-06-12",
                "reason": "derived from operator-controlled BDNS latest API observation",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    observations = collect_freshness_observations(runtime_root=tmp_path)

    assert observations == (
        {
            "source": "BDNS",
            "observed_at": "2026-06-13T10:15:00Z",
            "observation_kind": "existing_runtime_state",
            "input_path": str(output_path),
            "input_kind": "api_monitor_jsonl",
            "timestamp_type": "observed",
            "confidence": "operational",
            "reason": "derived from operator-controlled BDNS latest API observation",
            "latest_record_date": "2026-06-12T00:00:00Z",
        },
    )


def test_collects_monitor_observation_accepts_rfc2822_record_date(tmp_path):
    output_path = tmp_path / "data" / "rss_monitor" / "BOE" / "2026-06-14" / "rss_discovery.jsonl"
    output_path.parent.mkdir(parents=True)
    output_path.write_text(
        json.dumps(
            {
                "source_code": "BOE",
                "discovered_at": "2026-06-14T00:00:00Z",
                "published_at": "Sat, 13 Jun 2026 00:00:00 +0200",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    observations = collect_freshness_observations(runtime_root=tmp_path)

    assert observations == (
        {
            "source": "BOE",
            "observed_at": "2026-06-14T00:00:00Z",
            "observation_kind": "existing_runtime_state",
            "input_path": str(output_path),
            "input_kind": "rss_monitor_jsonl",
            "timestamp_type": "observed",
            "confidence": "operational",
            "reason": "derived from monitor discovered_at",
            "latest_record_date": "2026-06-12T22:00:00Z",
        },
    )
