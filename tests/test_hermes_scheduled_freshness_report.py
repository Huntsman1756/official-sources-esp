from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from official_sources.hermes_scheduled_freshness_report import (
    CommandResult,
    ScheduledFreshnessReportResult,
    run_scheduled_freshness_report,
)


def test_scheduled_freshness_report_uses_report_only_runtime_root_and_output(tmp_path):
    commands: list[tuple[list[str], Path]] = []

    def fake_run_command(command: list[str], cwd: Path) -> CommandResult:
        commands.append((command, cwd))
        output_path = Path(command[command.index("--output") + 1])
        output_path.write_text("# report\n\nVERDICT: NO-GO\n", encoding="utf-8")
        return CommandResult(returncode=0, stdout="VERDICT: NO-GO\n", stderr="")

    result = run_scheduled_freshness_report(
        repo_root=tmp_path / "app",
        state_root=tmp_path / "state",
        official_sources_bin="/bin/official-sources",
        run_command=fake_run_command,
        now=lambda: datetime(2026, 6, 13, 12, 30, 5, tzinfo=UTC),
    )

    assert result.exit_code == 0
    assert result.report_path == (
        tmp_path
        / "state"
        / "freshness-reports"
        / "hermes-freshness-report-20260613-123005.md"
    )
    assert result.freshness_result.returncode == 0
    assert len(commands) == 1
    command, cwd = commands[0]
    assert cwd == (tmp_path / "app").resolve()
    assert command == [
        "/bin/official-sources",
        "hermes",
        "freshness-report",
        "--runtime-root",
        ".",
        "--now",
        "2026-06-13T12:30:05Z",
        "--default-threshold-hours",
        "72",
        "--critical-source",
        "BOE",
        "--critical-source",
        "BDNS",
        "--critical-source",
        "BOCM",
        "--expected-source",
        "BOE",
        "--expected-source",
        "BDNS",
        "--expected-source",
        "BOCM",
        "--output",
        str(result.report_path),
    ]


def test_cli_scheduled_freshness_report_invokes_report_only_wrapper(tmp_path, capsys, monkeypatch):
    from official_sources import cli

    calls = []

    def fake_run_scheduled_freshness_report(**kwargs):
        calls.append(kwargs)
        return ScheduledFreshnessReportResult(
            exit_code=0,
            report_path=tmp_path / "state" / "freshness-reports" / "report.md",
            freshness_result=CommandResult(returncode=0, stdout="VERDICT: NO-GO\n", stderr=""),
        )

    monkeypatch.setattr(
        cli,
        "run_scheduled_freshness_report",
        fake_run_scheduled_freshness_report,
    )

    exit_code = cli.run(
        [
            "hermes",
            "scheduled-freshness-report",
            "--repo-root",
            str(tmp_path / "app"),
            "--state-root",
            str(tmp_path / "state"),
            "--official-sources-bin",
            "/bin/official-sources",
            "--default-threshold-hours",
            "36",
            "--critical-source",
            "BOE",
            "--expected-source",
            "BOE",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert f"report_path={tmp_path / 'state' / 'freshness-reports' / 'report.md'}" in captured.out
    assert "freshness_exit_code=0" in captured.out
    assert calls == [
        {
            "repo_root": tmp_path / "app",
            "state_root": tmp_path / "state",
            "official_sources_bin": "/bin/official-sources",
            "default_threshold_hours": 36,
            "critical_sources": ("BOE",),
            "expected_sources": ("BOE",),
        }
    ]


def test_cli_scheduled_freshness_report_prints_subprocess_stderr_on_failure(
    tmp_path, capsys, monkeypatch
):
    from official_sources import cli

    def fake_run_scheduled_freshness_report(**kwargs):
        return ScheduledFreshnessReportResult(
            exit_code=2,
            report_path=tmp_path / "state" / "freshness-reports" / "report.md",
            freshness_result=CommandResult(
                returncode=2,
                stdout="",
                stderr="runtime root is not readable",
            ),
        )

    monkeypatch.setattr(
        cli,
        "run_scheduled_freshness_report",
        fake_run_scheduled_freshness_report,
    )

    exit_code = cli.run(
        [
            "hermes",
            "scheduled-freshness-report",
            "--repo-root",
            str(tmp_path / "missing-app"),
            "--state-root",
            str(tmp_path / "state"),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "freshness_exit_code=2" in captured.out
    assert "runtime root is not readable" in captured.err


def test_scheduled_freshness_report_propagates_generation_failure(tmp_path):
    def fake_run_command(command: list[str], cwd: Path) -> CommandResult:
        return CommandResult(
            returncode=2,
            stdout="",
            stderr="runtime root is not readable",
        )

    result = run_scheduled_freshness_report(
        repo_root=tmp_path / "missing-app",
        state_root=tmp_path / "state",
        official_sources_bin="/bin/official-sources",
        run_command=fake_run_command,
        now=lambda: datetime(2026, 6, 13, 12, 30, 5, tzinfo=UTC),
    )

    assert result.exit_code == 2
    assert result.freshness_result.stderr == "runtime root is not readable"


def test_scheduled_freshness_report_fails_if_report_file_is_missing(tmp_path):
    def fake_run_command(command: list[str], cwd: Path) -> CommandResult:
        return CommandResult(returncode=0, stdout="VERDICT: GO\n", stderr="")

    result = run_scheduled_freshness_report(
        repo_root=tmp_path / "app",
        state_root=tmp_path / "state",
        official_sources_bin="/bin/official-sources",
        run_command=fake_run_command,
        now=lambda: datetime(2026, 6, 13, 12, 30, 5, tzinfo=UTC),
    )

    assert result.exit_code == 2
    assert "freshness report was not written" in result.freshness_result.stderr


def test_scheduled_freshness_report_reports_unwritable_state_root(tmp_path, monkeypatch):
    def failing_mkdir(self, *, parents=False, exist_ok=False):
        raise PermissionError("permission denied")

    monkeypatch.setattr(Path, "mkdir", failing_mkdir)

    result = run_scheduled_freshness_report(
        repo_root=tmp_path / "app",
        state_root=tmp_path / "state",
        official_sources_bin="/bin/official-sources",
        now=lambda: datetime(2026, 6, 13, 12, 30, 5, tzinfo=UTC),
    )

    assert result.exit_code == 2
    assert result.report_path == tmp_path / "state" / "freshness-reports"
    assert "could not create freshness report directory" in result.freshness_result.stderr
    assert "permission denied" in result.freshness_result.stderr
