from __future__ import annotations

import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

DEFAULT_REPO_ROOT = Path("/opt/official-sources/app")
DEFAULT_STATE_ROOT = Path("/var/lib/hermes-official-sources-auditor")
DEFAULT_CRITICAL_SOURCES = ("BOE", "BDNS", "BOCM")
DEFAULT_EXPECTED_SOURCES = ("BOE", "BDNS", "BOCM")
DEFAULT_THRESHOLD_HOURS = 72


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str


@dataclass(frozen=True)
class ScheduledFreshnessReportResult:
    exit_code: int
    report_path: Path
    observations_path: Path
    freshness_result: CommandResult


CommandRunner = Callable[[list[str], Path], CommandResult]


def run_scheduled_freshness_report(
    *,
    repo_root: Path = DEFAULT_REPO_ROOT,
    state_root: Path = DEFAULT_STATE_ROOT,
    official_sources_bin: str | None = None,
    default_threshold_hours: int = DEFAULT_THRESHOLD_HOURS,
    critical_sources: tuple[str, ...] = DEFAULT_CRITICAL_SOURCES,
    expected_sources: tuple[str, ...] = DEFAULT_EXPECTED_SOURCES,
    run_command: CommandRunner | None = None,
    now: Callable[[], datetime] | None = None,
) -> ScheduledFreshnessReportResult:
    repo_root = repo_root.resolve()
    state_root = state_root.resolve()
    reports_dir = state_root / "freshness-reports"
    freshness_runtime = state_root / "freshness-runtime"
    observations_dir = state_root / "freshness-observations"
    observations_path = observations_dir / "latest-critical.jsonl"
    try:
        reports_dir.mkdir(parents=True, exist_ok=True)
        observations_dir.mkdir(parents=True, exist_ok=True)
        (freshness_runtime / "data" / "rss_monitor").mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        return ScheduledFreshnessReportResult(
            exit_code=2,
            report_path=reports_dir,
            observations_path=observations_path,
            freshness_result=CommandResult(
                returncode=2,
                stdout="",
                stderr=f"could not create freshness schedule directories under {state_root}: {exc}",
            ),
        )

    started_at = _utc_now(now)
    stamp = started_at.strftime("%Y%m%d-%H%M%S")
    report_path = reports_dir / f"hermes-freshness-report-{stamp}.md"

    bin_path = official_sources_bin or str(repo_root / ".venv" / "bin" / "official-sources")
    runner = run_command or _run_command
    source_codes = _ordered_sources(critical_sources, expected_sources)
    for command in _observation_commands(
        bin_path=bin_path,
        repo_root=repo_root,
        state_root=state_root,
        freshness_runtime=freshness_runtime,
        observations_path=observations_path,
        observed_date=started_at.date().isoformat(),
        source_codes=source_codes,
    ):
        result = runner(command, repo_root)
        if result.returncode != 0:
            return ScheduledFreshnessReportResult(
                exit_code=result.returncode,
                report_path=report_path,
                observations_path=observations_path,
                freshness_result=result,
            )
    if not observations_path.exists():
        return ScheduledFreshnessReportResult(
            exit_code=2,
            report_path=report_path,
            observations_path=observations_path,
            freshness_result=CommandResult(
                returncode=2,
                stdout="",
                stderr=f"freshness observations were not written: {observations_path}",
            ),
        )

    report_at = _utc_now(now)
    command = [
        bin_path,
        "hermes",
        "freshness-report",
        "--observations-jsonl",
        str(observations_path),
        "--now",
        _format_timestamp(report_at),
        "--default-threshold-hours",
        str(default_threshold_hours),
    ]
    for source_code in critical_sources:
        command.extend(["--critical-source", source_code])
    for source_code in expected_sources:
        command.extend(["--expected-source", source_code])
    command.extend(["--output", str(report_path)])

    freshness_result = runner(command, repo_root)
    if freshness_result.returncode == 0 and not report_path.exists():
        freshness_result = CommandResult(
            returncode=2,
            stdout=freshness_result.stdout,
            stderr=(
                f"freshness report was not written: {report_path}"
                if not freshness_result.stderr
                else f"{freshness_result.stderr}\nfreshness report was not written: {report_path}"
            ),
        )
    return ScheduledFreshnessReportResult(
        exit_code=freshness_result.returncode,
        report_path=report_path,
        observations_path=observations_path,
        freshness_result=freshness_result,
    )


def _observation_commands(
    *,
    bin_path: str,
    repo_root: Path,
    state_root: Path,
    freshness_runtime: Path,
    observations_path: Path,
    observed_date: str,
    source_codes: tuple[str, ...],
) -> tuple[list[str], ...]:
    commands: list[list[str]] = []
    if "BOE" in source_codes:
        commands.append(
            [
                bin_path,
                "rss",
                "monitor",
                "--source",
                "BOE",
                "--date",
                observed_date,
                "--limit",
                "1",
                "--write",
                "--output-root",
                str(freshness_runtime / "data" / "rss_monitor"),
            ]
        )
    if "BOCM" in source_codes:
        commands.append(
            [
                bin_path,
                "hermes",
                "bocm-rss-observation",
                "--repo-root",
                str(repo_root),
                "--state-root",
                str(state_root),
                "--official-sources-bin",
                bin_path,
                "--date",
                "today",
                "--limit",
                "1",
            ]
        )
    if "BDNS" in source_codes:
        commands.append(
            [
                bin_path,
                "hermes",
                "bdns-observation",
                "--repo-root",
                str(repo_root),
                "--state-root",
                str(state_root),
                "--official-sources-bin",
                bin_path,
                "--limit",
                "1",
            ]
        )
    freshness_observations_command = [
        bin_path,
        "hermes",
        "freshness-observations",
        "--runtime-root",
        str(freshness_runtime),
    ]
    for source_code in source_codes:
        freshness_observations_command.extend(["--source", source_code])
    freshness_observations_command.extend(["--output", str(observations_path)])
    commands.append(freshness_observations_command)
    return tuple(commands)


def _ordered_sources(
    critical_sources: tuple[str, ...],
    expected_sources: tuple[str, ...],
) -> tuple[str, ...]:
    ordered: list[str] = []
    for source_code in (*critical_sources, *expected_sources):
        normalized = source_code.strip().upper()
        if normalized and normalized not in ordered:
            ordered.append(normalized)
    return tuple(ordered)


def _run_command(command: list[str], cwd: Path) -> CommandResult:
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        return CommandResult(returncode=127, stdout="", stderr=str(exc))
    return CommandResult(
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def _utc_now(now: Callable[[], datetime] | None) -> datetime:
    generated_at = (now or (lambda: datetime.now(UTC)))()
    if generated_at.tzinfo is None:
        generated_at = generated_at.replace(tzinfo=UTC)
    return generated_at.astimezone(UTC)


def _format_timestamp(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")
