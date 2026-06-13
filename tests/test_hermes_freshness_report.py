from __future__ import annotations

import json
from datetime import UTC, datetime

from official_sources.hermes_freshness_report import (
    FreshnessObservation,
    SourceFreshness,
    evaluate_freshness,
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
    assert "| BOE | healthy | 2026-06-13T08:00:00Z | 36 | 4.0 | none |" in report
    assert "| BOP_TEST | stale | 2026-06-10T12:00:00Z | 24 | 72.0 | none |" in report
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
