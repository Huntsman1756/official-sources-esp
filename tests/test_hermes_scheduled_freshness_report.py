from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from official_sources.hermes_scheduled_freshness_report import (
    CommandResult,
    ScheduledFreshnessReportResult,
    run_scheduled_freshness_report,
)


def test_scheduled_freshness_report_builds_critical_observations_before_report(tmp_path):
    commands: list[tuple[list[str], Path]] = []

    def fake_run_command(command: list[str], cwd: Path) -> CommandResult:
        commands.append((command, cwd))
        if command[1:3] == ["rss", "monitor"]:
            output_root = Path(command[command.index("--output-root") + 1])
            output_path = output_root / "BOE" / "2026-06-13" / "rss_discovery.jsonl"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(
                '{"source_code":"BOE","discovered_at":"2026-06-13T00:00:00Z"}\n',
                encoding="utf-8",
            )
            return CommandResult(returncode=0, stdout="boe ok\n", stderr="")
        if command[1:3] == ["hermes", "bocm-rss-observation"]:
            return CommandResult(returncode=0, stdout="bocm ok\n", stderr="")
        if command[1:3] == ["hermes", "bdns-observation"]:
            return CommandResult(returncode=0, stdout="bdns ok\n", stderr="")
        if command[1:3] == ["hermes", "freshness-observations"]:
            output_path = Path(command[command.index("--output") + 1])
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(
                '{"source":"BOE","observed_at":"2026-06-13T00:00:00Z"}\n',
                encoding="utf-8",
            )
            return CommandResult(returncode=0, stdout="observations_written=3\n", stderr="")
        if command[1:3] == ["hermes", "freshness-report"]:
            output_path = Path(command[command.index("--output") + 1])
            output_path.write_text("# report\n\nVERDICT: GO\n", encoding="utf-8")
            return CommandResult(returncode=0, stdout="VERDICT: GO\n", stderr="")
        raise AssertionError(f"unexpected command: {command}")

    result = run_scheduled_freshness_report(
        repo_root=tmp_path / "app",
        state_root=tmp_path / "state",
        official_sources_bin="/bin/official-sources",
        run_command=fake_run_command,
        now=lambda: datetime(2026, 6, 13, 12, 30, 5, tzinfo=UTC),
    )

    assert result.exit_code == 0
    assert result.observations_path == (
        tmp_path / "state" / "freshness-observations" / "latest-critical.jsonl"
    )
    assert result.report_path == (
        tmp_path
        / "state"
        / "freshness-reports"
        / "hermes-freshness-report-20260613-123005.md"
    )
    assert result.freshness_result.returncode == 0
    assert len(commands) == 5
    assert [cwd for _command, cwd in commands] == [(tmp_path / "app").resolve()] * 5
    assert commands[0][0] == [
        "/bin/official-sources",
        "rss",
        "monitor",
        "--source",
        "BOE",
        "--date",
        "2026-06-13",
        "--limit",
        "1",
        "--write",
        "--output-root",
        str(tmp_path / "state" / "freshness-runtime" / "data" / "rss_monitor"),
    ]
    assert commands[1][0] == [
        "/bin/official-sources",
        "hermes",
        "bocm-rss-observation",
        "--repo-root",
        str((tmp_path / "app").resolve()),
        "--state-root",
        str((tmp_path / "state").resolve()),
        "--official-sources-bin",
        "/bin/official-sources",
        "--date",
        "today",
        "--limit",
        "1",
    ]
    assert commands[2][0] == [
        "/bin/official-sources",
        "hermes",
        "bdns-observation",
        "--repo-root",
        str((tmp_path / "app").resolve()),
        "--state-root",
        str((tmp_path / "state").resolve()),
        "--official-sources-bin",
        "/bin/official-sources",
        "--limit",
        "1",
    ]
    assert commands[3][0] == [
        "/bin/official-sources",
        "hermes",
        "freshness-observations",
        "--runtime-root",
        str(tmp_path / "state" / "freshness-runtime"),
        "--source",
        "BOE",
        "--source",
        "BDNS",
        "--source",
        "BOCM",
        "--output",
        str(result.observations_path),
    ]
    assert commands[4][0] == [
        "/bin/official-sources",
        "hermes",
        "freshness-report",
        "--observations-jsonl",
        str(result.observations_path),
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
            observations_path=tmp_path
            / "state"
            / "freshness-observations"
            / "latest-critical.jsonl",
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
    assert (
        f"observations_path={tmp_path / 'state' / 'freshness-observations' / 'latest-critical.jsonl'}"
        in captured.out
    )
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
            observations_path=tmp_path
            / "state"
            / "freshness-observations"
            / "latest-critical.jsonl",
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
        if command[1:3] == ["hermes", "freshness-observations"]:
            output_path = Path(command[command.index("--output") + 1])
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(
                '{"source":"BOE","observed_at":"2026-06-13T00:00:00Z"}\n',
                encoding="utf-8",
            )
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


def test_scheduled_freshness_report_fails_if_observation_command_fails(tmp_path):
    commands: list[list[str]] = []

    def fake_run_command(command: list[str], cwd: Path) -> CommandResult:
        commands.append(command)
        if command[1:3] == ["rss", "monitor"]:
            return CommandResult(returncode=2, stdout="", stderr="BOE RSS failed")
        raise AssertionError(f"unexpected command after failed observation: {command}")

    result = run_scheduled_freshness_report(
        repo_root=tmp_path / "app",
        state_root=tmp_path / "state",
        official_sources_bin="/bin/official-sources",
        run_command=fake_run_command,
        now=lambda: datetime(2026, 6, 13, 12, 30, 5, tzinfo=UTC),
    )

    assert result.exit_code == 2
    assert len(commands) == 1
    assert result.freshness_result.stderr == "BOE RSS failed"


def test_scheduled_freshness_report_uses_post_observation_time_for_report_now(tmp_path):
    commands: list[list[str]] = []
    times = iter(
        [
            datetime(2026, 6, 13, 12, 30, 5, tzinfo=UTC),
            datetime(2026, 6, 13, 12, 31, 10, tzinfo=UTC),
        ]
    )

    def fake_run_command(command: list[str], cwd: Path) -> CommandResult:
        commands.append(command)
        if command[1:3] == ["hermes", "freshness-observations"]:
            output_path = Path(command[command.index("--output") + 1])
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(
                '{"source":"BOE","observed_at":"2026-06-13T12:30:30Z"}\n',
                encoding="utf-8",
            )
        if command[1:3] == ["hermes", "freshness-report"]:
            output_path = Path(command[command.index("--output") + 1])
            output_path.write_text("# report\n\nVERDICT: GO\n", encoding="utf-8")
        return CommandResult(returncode=0, stdout="ok\n", stderr="")

    run_scheduled_freshness_report(
        repo_root=tmp_path / "app",
        state_root=tmp_path / "state",
        official_sources_bin="/bin/official-sources",
        run_command=fake_run_command,
        now=lambda: next(times),
    )

    report_command = commands[-1]
    assert report_command[report_command.index("--now") + 1] == "2026-06-13T12:31:10Z"


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
    assert "could not create freshness schedule directories" in result.freshness_result.stderr
    assert "permission denied" in result.freshness_result.stderr
