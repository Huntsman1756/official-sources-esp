from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from official_sources.hermes_bocm_rss_observation import (
    BOCMRSSObservationResult,
    CommandResult,
    run_bocm_rss_observation,
)


def test_bocm_rss_observation_writes_runtime_jsonl_then_latest_observation(tmp_path):
    commands: list[tuple[list[str], Path]] = []

    def fake_run_command(command: list[str], cwd: Path) -> CommandResult:
        commands.append((command, cwd))
        if command[1:3] == ["rss", "monitor"]:
            output_root = Path(command[command.index("--output-root") + 1])
            output_path = output_root / "BOCM" / "2026-06-13" / "rss_discovery.jsonl"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(
                '{"source_code":"BOCM","discovered_at":"2026-06-13T08:15:00Z"}\n',
                encoding="utf-8",
            )
            return CommandResult(returncode=0, stdout="output_path=" + str(output_path), stderr="")
        if command[1:3] == ["hermes", "freshness-observations"]:
            output_path = Path(command[command.index("--output") + 1])
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(
                '{"source":"BOCM","observed_at":"2026-06-13T08:15:00Z","timestamp_type":"observed"}\n',
                encoding="utf-8",
            )
            return CommandResult(returncode=0, stdout="observations_written=1\n", stderr="")
        raise AssertionError(f"unexpected command: {command}")

    result = run_bocm_rss_observation(
        repo_root=tmp_path / "app",
        state_root=tmp_path / "state",
        official_sources_bin="/bin/official-sources",
        run_command=fake_run_command,
        now=lambda: datetime(2026, 6, 13, 12, 30, 5, tzinfo=UTC),
    )

    freshness_runtime = (tmp_path / "state" / "freshness-runtime").resolve()
    rss_root = freshness_runtime / "data" / "rss_monitor"
    observations_path = (
        tmp_path / "state" / "freshness-observations" / "latest-bocm-rss.jsonl"
    ).resolve()
    rss_output_path = rss_root / "BOCM" / "2026-06-13" / "rss_discovery.jsonl"

    assert result.exit_code == 0
    assert result.rss_output_path == rss_output_path
    assert result.observations_path == observations_path
    assert result.rss_result.returncode == 0
    assert result.observations_result.returncode == 0
    assert commands == [
        (
            [
                "/bin/official-sources",
                "rss",
                "monitor",
                "--source",
                "BOCM",
                "--date",
                "2026-06-13",
                "--limit",
                "1",
                "--write",
                "--output-root",
                str(rss_root),
            ],
            (tmp_path / "app").resolve(),
        ),
        (
            [
                "/bin/official-sources",
                "hermes",
                "freshness-observations",
                "--runtime-root",
                str(freshness_runtime),
                "--source",
                "BOCM",
                "--output",
                str(observations_path),
            ],
            (tmp_path / "app").resolve(),
        ),
    ]


def test_bocm_rss_observation_fails_if_monitor_output_is_missing(tmp_path):
    commands: list[list[str]] = []

    def fake_run_command(command: list[str], cwd: Path) -> CommandResult:
        commands.append(command)
        return CommandResult(returncode=0, stdout="records=1\n", stderr="")

    result = run_bocm_rss_observation(
        repo_root=tmp_path / "app",
        state_root=tmp_path / "state",
        official_sources_bin="/bin/official-sources",
        run_command=fake_run_command,
        now=lambda: datetime(2026, 6, 13, 12, 30, 5, tzinfo=UTC),
    )

    assert result.exit_code == 2
    assert "BOCM RSS observation output was not written" in result.observations_result.stderr
    assert len(commands) == 1


def test_cli_bocm_rss_observation_invokes_manual_wrapper(tmp_path, capsys, monkeypatch):
    from official_sources import cli

    calls = []

    def fake_run_bocm_rss_observation(**kwargs):
        calls.append(kwargs)
        return BOCMRSSObservationResult(
            exit_code=0,
            rss_output_path=tmp_path
            / "state"
            / "freshness-runtime"
            / "data"
            / "rss_monitor"
            / "BOCM"
            / "2026-06-13"
            / "rss_discovery.jsonl",
            observations_path=tmp_path
            / "state"
            / "freshness-observations"
            / "latest-bocm-rss.jsonl",
            rss_result=CommandResult(returncode=0, stdout="rss ok", stderr=""),
            observations_result=CommandResult(returncode=0, stdout="observations ok", stderr=""),
        )

    monkeypatch.setattr(cli, "run_bocm_rss_observation", fake_run_bocm_rss_observation)

    exit_code = cli.run(
        [
            "hermes",
            "bocm-rss-observation",
            "--repo-root",
            str(tmp_path / "app"),
            "--state-root",
            str(tmp_path / "state"),
            "--official-sources-bin",
            "/bin/official-sources",
            "--date",
            "2026-06-13",
            "--limit",
            "1",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "rss_output_path=" in captured.out
    assert "observations_path=" in captured.out
    assert "bocm_rss_observation_exit_code=0" in captured.out
    assert calls == [
        {
            "repo_root": tmp_path / "app",
            "state_root": tmp_path / "state",
            "official_sources_bin": "/bin/official-sources",
            "target_date": "2026-06-13",
            "limit": 1,
        }
    ]
