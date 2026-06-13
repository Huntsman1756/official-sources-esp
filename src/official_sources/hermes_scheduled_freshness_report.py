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
    try:
        reports_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        return ScheduledFreshnessReportResult(
            exit_code=2,
            report_path=reports_dir,
            freshness_result=CommandResult(
                returncode=2,
                stdout="",
                stderr=f"could not create freshness report directory {reports_dir}: {exc}",
            ),
        )

    generated_at = _utc_now(now)
    stamp = generated_at.strftime("%Y%m%d-%H%M%S")
    report_path = reports_dir / f"hermes-freshness-report-{stamp}.md"

    bin_path = official_sources_bin or str(repo_root / ".venv" / "bin" / "official-sources")
    command = [
        bin_path,
        "hermes",
        "freshness-report",
        "--runtime-root",
        ".",
        "--now",
        _format_timestamp(generated_at),
        "--default-threshold-hours",
        str(default_threshold_hours),
    ]
    for source_code in critical_sources:
        command.extend(["--critical-source", source_code])
    for source_code in expected_sources:
        command.extend(["--expected-source", source_code])
    command.extend(["--output", str(report_path)])

    runner = run_command or _run_command
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
        freshness_result=freshness_result,
    )


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
