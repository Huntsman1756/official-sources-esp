from __future__ import annotations

import json
from datetime import UTC, datetime

from official_sources.hermes_freshness_report import (
    FreshnessObservation,
    SourceFreshness,
    evaluate_freshness,
    load_runtime_observation,
    render_markdown_report,
)

NOW = datetime(2026, 6, 13, 12, 0, tzinfo=UTC)


def _source(**overrides) -> SourceFreshness:
    values = {
        "source_code": "BOE",
        "last_seen": "2026-06-13T08:00:00Z",
        "threshold_hours": 36,
        "critical": True,
        "calendar_exception": None,
        "impact": "BOE monitor freshness is current.",
    }
    values.update(overrides)
    return SourceFreshness(**values)


def _observation(*sources: SourceFreshness) -> FreshnessObservation:
    return FreshnessObservation(now=NOW, sources=sources)


def test_fresh_source_returns_go_with_auditable_fields():
    result = evaluate_freshness(_observation(_source()))

    assert result.verdict == "GO"
    assert result.checks[0].status == "healthy"
    assert result.checks[0].reason == "age within threshold"
    assert result.checks[0].age_hours == 4.0
    assert result.checks[0].threshold_hours == 36
    assert result.checks[0].calendar_exception is None
    assert result.checks[0].impact == "BOE monitor freshness is current."


def test_non_critical_stale_source_returns_warning():
    result = evaluate_freshness(
        _observation(
            _source(
                source_code="BOP_TEST",
                critical=False,
                last_seen="2026-06-10T12:00:00Z",
                threshold_hours=24,
                impact="Non-critical source needs manual review.",
            )
        )
    )

    assert result.verdict == "WARNING"
    assert result.checks[0].status == "stale"
    assert result.checks[0].reason == "age exceeds threshold"
    assert result.checks[0].age_hours == 72.0
    assert result.warnings == ("BOP_TEST stale for 72.0h over threshold 24h",)


def test_critical_stale_source_returns_no_go():
    result = evaluate_freshness(
        _observation(
            _source(
                last_seen="2026-06-10T11:00:00Z",
                threshold_hours=48,
                impact="Critical BOE state is too old.",
            )
        )
    )

    assert result.verdict == "NO-GO"
    assert result.checks[0].status == "stale"
    assert result.failures == ("BOE critical stale for 73.0h over threshold 48h",)


def test_missing_critical_source_returns_no_go():
    result = evaluate_freshness(
        _observation(
            _source(
                source_code="BDNS",
                last_seen=None,
                threshold_hours=24,
                impact="BDNS cache timestamp is missing.",
            )
        )
    )

    assert result.verdict == "NO-GO"
    assert result.checks[0].status == "missing"
    assert result.checks[0].reason == "last_seen missing"
    assert result.checks[0].age_hours is None
    assert result.failures == ("BDNS critical freshness timestamp is missing",)


def test_calendar_exception_keeps_stale_source_go():
    result = evaluate_freshness(
        _observation(
            _source(
                last_seen="2026-06-10T12:00:00Z",
                threshold_hours=24,
                calendar_exception="holiday",
                impact="Holiday explains missing publication.",
            )
        )
    )

    assert result.verdict == "GO"
    assert result.checks[0].status == "calendar-exempt"
    assert result.checks[0].reason == "calendar exception: holiday"
    assert result.checks[0].calendar_exception == "holiday"
    assert result.failures == ()
    assert result.warnings == ()


def test_report_renders_verdict_sources_thresholds_calendar_and_impact():
    result = evaluate_freshness(
        _observation(
            _source(source_code="BOE"),
            _source(
                source_code="BOP_TEST",
                critical=False,
                last_seen="2026-06-10T12:00:00Z",
                threshold_hours=24,
                impact="Non-critical source needs manual review.",
            ),
        )
    )

    report = render_markdown_report(result)

    assert "VERDICT: WARNING" in report
    assert (
        "| BOE | healthy | age within threshold | 2026-06-13T08:00:00Z | 36 | 4.0 | none |"
        in report
    )
    assert (
        "| BOP_TEST | stale | age exceeds threshold | 2026-06-10T12:00:00Z | 24 | 72.0 | none |"
        in report
    )
    assert "Non-critical source needs manual review." in report
    assert "- official_documents_written: false" in report
    assert "- downstream_writes: false" in report


def test_cli_freshness_report_reads_fixture_and_writes_only_explicit_report(tmp_path, capsys):
    from official_sources.cli import run

    state_path = tmp_path / "freshness-state.json"
    report_path = tmp_path / "freshness-report.md"
    state_path.write_text(
        json.dumps(
            {
                "sources": [
                    {
                        "source_code": "BOE",
                        "last_seen": "2026-06-13T08:00:00Z",
                        "threshold_hours": 36,
                        "critical": True,
                        "calendar_exception": None,
                        "impact": "BOE monitor freshness is current.",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    exit_code = run(
        [
            "hermes",
            "freshness-report",
            "--state",
            str(state_path),
            "--now",
            "2026-06-13T12:00:00Z",
            "--output",
            str(report_path),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "VERDICT: GO" in captured.out
    assert report_path.read_text(encoding="utf-8") == captured.out
    assert sorted(path.name for path in tmp_path.iterdir()) == [
        "freshness-report.md",
        "freshness-state.json",
    ]


def test_cli_freshness_report_without_output_writes_nothing(tmp_path, capsys):
    from official_sources.cli import run

    state_path = tmp_path / "freshness-state.json"
    state_path.write_text(
        json.dumps(
            {
                "sources": [
                    {
                        "source_code": "BOE",
                        "last_seen": "2026-06-13T08:00:00Z",
                        "threshold_hours": 36,
                        "critical": True,
                        "calendar_exception": None,
                        "impact": "BOE monitor freshness is current.",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    exit_code = run(
        [
            "hermes",
            "freshness-report",
            "--state",
            str(state_path),
            "--now",
            "2026-06-13T12:00:00Z",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "VERDICT: GO" in captured.out
    assert sorted(path.name for path in tmp_path.iterdir()) == ["freshness-state.json"]


def test_runtime_observation_loads_latest_monitor_jsonl_without_changing_engine(tmp_path):
    output_path = tmp_path / "data" / "rss_monitor" / "BOE" / "2026-06-13" / "rss_discovery.jsonl"
    output_path.parent.mkdir(parents=True)
    output_path.write_text(
        json.dumps(
            {
                "source_code": "BOE",
                "title": "BOE entry",
                "published_at": "2026-06-13T07:30:00Z",
                "discovered_at": "2026-06-13T08:00:00Z",
                "candidate_status": "not_candidate",
                "evidence_status": "not_evidence",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    observation = load_runtime_observation(
        tmp_path,
        now=NOW,
        default_threshold_hours=36,
        critical_sources=("BOE",),
    )
    result = evaluate_freshness(observation)

    assert result.verdict == "GO"
    assert observation.sources[0].source_code == "BOE"
    assert observation.sources[0].last_seen == "2026-06-13T08:00:00Z"
    assert observation.sources[0].threshold_hours == 36
    assert observation.sources[0].critical is True
    assert "Runtime discovery output observed" in observation.sources[0].impact
    assert str(output_path) in observation.sources[0].impact


def test_runtime_observation_marks_expected_missing_source(tmp_path):
    observation = load_runtime_observation(
        tmp_path,
        now=NOW,
        default_threshold_hours=24,
        critical_sources=("BDNS",),
        expected_sources=("BDNS",),
    )
    result = evaluate_freshness(observation)

    assert result.verdict == "NO-GO"
    assert observation.sources[0].source_code == "BDNS"
    assert observation.sources[0].last_seen is None
    assert observation.sources[0].impact == "Expected runtime discovery output is missing."
    assert result.checks[0].status == "missing"


def test_runtime_observation_rejects_empty_unscoped_runtime_root(tmp_path):
    try:
        load_runtime_observation(
            tmp_path,
            now=NOW,
            default_threshold_hours=24,
        )
    except ValueError as exc:
        assert "no runtime discovery outputs found" in str(exc)
    else:
        raise AssertionError("empty runtime root must not produce a silent GO")


def test_cli_freshness_report_runtime_root_reads_real_inputs_without_extra_writes(tmp_path, capsys):
    from official_sources.cli import run

    output_path = tmp_path / "data" / "api_monitor" / "BOPV" / "2026-06-13" / "api_discovery.jsonl"
    output_path.parent.mkdir(parents=True)
    output_path.write_text(
        json.dumps(
            {
                "source_code": "BOPV",
                "title": "BOPV entry",
                "published_at": "2026-06-13",
                "discovered_at": "2026-06-13T08:00:00Z",
                "candidate_status": "not_candidate",
                "evidence_status": "not_evidence",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    exit_code = run(
        [
            "hermes",
            "freshness-report",
            "--runtime-root",
            str(tmp_path),
            "--now",
            "2026-06-13T12:00:00Z",
            "--default-threshold-hours",
            "36",
            "--critical-source",
            "BOPV",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "VERDICT: GO" in captured.out
    assert (
        "| BOPV | healthy | age within threshold | 2026-06-13T08:00:00Z | 36 | 4.0 | none |"
        in captured.out
    )
    assert not (tmp_path / "freshness-report.md").exists()
