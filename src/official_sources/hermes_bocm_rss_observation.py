from __future__ import annotations

import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

DEFAULT_REPO_ROOT = Path("/opt/official-sources/app")
DEFAULT_STATE_ROOT = Path("/var/lib/hermes-official-sources-auditor")
DEFAULT_LIMIT = 1


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str


@dataclass(frozen=True)
class BOCMRSSObservationResult:
    exit_code: int
    rss_output_path: Path
    observations_path: Path
    rss_result: CommandResult
    observations_result: CommandResult


CommandRunner = Callable[[list[str], Path], CommandResult]


def run_bocm_rss_observation(
    *,
    repo_root: Path = DEFAULT_REPO_ROOT,
    state_root: Path = DEFAULT_STATE_ROOT,
    official_sources_bin: str | None = None,
    target_date: str | None = None,
    limit: int = DEFAULT_LIMIT,
    run_command: CommandRunner | None = None,
    now: Callable[[], datetime] | None = None,
) -> BOCMRSSObservationResult:
    repo_root = repo_root.resolve()
    state_root = state_root.resolve()
    observed_date = _target_date(target_date, now)
    freshness_runtime = state_root / "freshness-runtime"
    rss_root = freshness_runtime / "data" / "rss_monitor"
    rss_output_path = rss_root / "BOCM" / observed_date / "rss_discovery.jsonl"
    observations_path = state_root / "freshness-observations" / "latest-bocm-rss.jsonl"

    try:
        rss_root.mkdir(parents=True, exist_ok=True)
        observations_path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        error = CommandResult(
            returncode=2,
            stdout="",
            stderr=f"could not create BOCM observation directories: {exc}",
        )
        return BOCMRSSObservationResult(
            exit_code=2,
            rss_output_path=rss_output_path,
            observations_path=observations_path,
            rss_result=error,
            observations_result=error,
        )

    bin_path = official_sources_bin or str(repo_root / ".venv" / "bin" / "official-sources")
    runner = run_command or _run_command
    rss_command = [
        bin_path,
        "rss",
        "monitor",
        "--source",
        "BOCM",
        "--date",
        observed_date,
        "--limit",
        str(limit),
        "--write",
        "--output-root",
        str(rss_root),
    ]
    rss_result = runner(rss_command, repo_root)
    if rss_result.returncode != 0:
        empty = CommandResult(returncode=rss_result.returncode, stdout="", stderr="")
        return BOCMRSSObservationResult(
            exit_code=rss_result.returncode,
            rss_output_path=rss_output_path,
            observations_path=observations_path,
            rss_result=rss_result,
            observations_result=empty,
        )
    if not rss_output_path.exists():
        observations_result = CommandResult(
            returncode=2,
            stdout="",
            stderr=f"BOCM RSS observation output was not written: {rss_output_path}",
        )
        return BOCMRSSObservationResult(
            exit_code=2,
            rss_output_path=rss_output_path,
            observations_path=observations_path,
            rss_result=rss_result,
            observations_result=observations_result,
        )

    observations_command = [
        bin_path,
        "hermes",
        "freshness-observations",
        "--runtime-root",
        str(freshness_runtime),
        "--source",
        "BOCM",
        "--output",
        str(observations_path),
    ]
    observations_result = runner(observations_command, repo_root)
    if observations_result.returncode == 0 and not observations_path.exists():
        observations_result = CommandResult(
            returncode=2,
            stdout=observations_result.stdout,
            stderr=(
                f"BOCM freshness observation JSONL was not written: {observations_path}"
                if not observations_result.stderr
                else (
                    f"{observations_result.stderr}\n"
                    f"BOCM freshness observation JSONL was not written: {observations_path}"
                )
            ),
        )
    return BOCMRSSObservationResult(
        exit_code=observations_result.returncode,
        rss_output_path=rss_output_path,
        observations_path=observations_path,
        rss_result=rss_result,
        observations_result=observations_result,
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


def _target_date(target_date: str | None, now: Callable[[], datetime] | None) -> str:
    if target_date and target_date != "today":
        return target_date
    generated_at = (now or (lambda: datetime.now(UTC)))()
    if generated_at.tzinfo is None:
        generated_at = generated_at.replace(tzinfo=UTC)
    return generated_at.astimezone(UTC).date().isoformat()
