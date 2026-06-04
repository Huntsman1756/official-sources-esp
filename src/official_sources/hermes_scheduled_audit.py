from __future__ import annotations

import shlex
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

DEFAULT_REPO_ROOT = Path("/opt/official-sources/app")
DEFAULT_STATE_ROOT = Path("/var/lib/hermes-official-sources-auditor")
DEFAULT_RELEASE_CONTRACT = Path("/etc/official-sources/hermes-audit-contract.yaml")


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str


@dataclass(frozen=True)
class WatchdogResult:
    command: tuple[str, ...]
    result: CommandResult


@dataclass(frozen=True)
class ScheduledStrictAuditResult:
    exit_code: int
    report_path: Path
    strict_report_path: Path
    log_path: Path
    strict_result: CommandResult
    watchdog_results: tuple[WatchdogResult, ...]


CommandRunner = Callable[[list[str], Path], CommandResult]


def run_scheduled_strict_audit(
    *,
    repo_root: Path = DEFAULT_REPO_ROOT,
    state_root: Path = DEFAULT_STATE_ROOT,
    release_contract: Path = DEFAULT_RELEASE_CONTRACT,
    official_sources_bin: str | None = None,
    run_command: CommandRunner | None = None,
    now: Callable[[], datetime] | None = None,
) -> ScheduledStrictAuditResult:
    repo_root = repo_root.resolve()
    state_root = state_root.resolve()
    release_contract = release_contract.resolve()
    reports_dir = state_root / "reports"
    logs_dir = state_root / "logs"
    reports_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    generated_at = (now or (lambda: datetime.now(UTC)))()
    if generated_at.tzinfo is None:
        generated_at = generated_at.replace(tzinfo=UTC)
    generated_at = generated_at.astimezone(UTC)
    stamp = generated_at.strftime("%Y%m%d-%H%M%S")

    strict_report_path = reports_dir / f"strict-release-audit-{stamp}.md"
    report_path = reports_dir / f"vps-audit-{stamp}.md"
    log_path = logs_dir / f"vps-audit-{stamp}.log"

    runner = run_command or _run_command
    bin_path = official_sources_bin or str(repo_root / ".venv" / "bin" / "official-sources")
    strict_command = [
        bin_path,
        "hermes",
        "audit",
        "--repo-root",
        str(repo_root),
        "--registry",
        str(repo_root / "config" / "sources.yaml"),
        "--project-state",
        str(repo_root / "PROJECT_STATE.md"),
        "--release-contract",
        str(release_contract),
        "--strict-release-contract",
        "--fail-on-no-go",
        "--output",
        str(strict_report_path),
    ]

    strict_result = runner(strict_command, repo_root)
    watchdog_results = tuple(
        WatchdogResult(command=tuple(command), result=runner(command, repo_root))
        for command in _watchdog_commands()
    )

    report_path.write_text(
        _render_report(
            generated_at=generated_at,
            repo_root=repo_root,
            release_contract=release_contract,
            strict_command=strict_command,
            strict_report_path=strict_report_path,
            strict_result=strict_result,
            watchdog_results=watchdog_results,
        ),
        encoding="utf-8",
    )
    log_path.write_text(
        _render_log(
            strict_command=strict_command,
            strict_result=strict_result,
            watchdog_results=watchdog_results,
        ),
        encoding="utf-8",
    )

    return ScheduledStrictAuditResult(
        exit_code=strict_result.returncode,
        report_path=report_path,
        strict_report_path=strict_report_path,
        log_path=log_path,
        strict_result=strict_result,
        watchdog_results=watchdog_results,
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


def _watchdog_commands() -> tuple[list[str], ...]:
    return (
        ["git", "rev-parse", "HEAD"],
        ["git", "status", "--short"],
        ["systemctl", "--failed", "--no-pager"],
        ["systemctl", "status", "official-sources-hermes-auditor.timer", "--no-pager"],
        ["systemctl", "status", "official-sources-hermes-auditor.service", "--no-pager"],
        ["systemctl", "status", "official-sources-boe-daily.timer", "--no-pager"],
        ["systemctl", "status", "official-sources-integrity-check.timer", "--no-pager"],
    )


def _render_report(
    *,
    generated_at: datetime,
    repo_root: Path,
    release_contract: Path,
    strict_command: list[str],
    strict_report_path: Path,
    strict_result: CommandResult,
    watchdog_results: tuple[WatchdogResult, ...],
) -> str:
    sections = [
        "# Hermes scheduled strict audit",
        "",
        f"Generated at: {generated_at.isoformat()}",
        f"Repository: `{repo_root}`",
        f"Release contract: `{release_contract}`",
        f"Strict report path: `{strict_report_path}`",
        "",
        "## Strict release audit",
        "",
        f"Command: `{_join_command(strict_command)}`",
        f"Strict release audit exit code: {strict_result.returncode}",
        "",
        "### stdout",
        "",
        "```text",
        strict_result.stdout.strip() or "<empty>",
        "```",
        "",
    ]
    if strict_result.stderr.strip():
        sections.extend(
            [
                "### stderr",
                "",
                "```text",
                strict_result.stderr.strip(),
                "```",
                "",
            ]
        )

    sections.extend(["## Watchdog evidence", ""])
    for watchdog in watchdog_results:
        sections.extend(
            [
                f"### {_join_command(list(watchdog.command))}",
                "",
                f"Exit code: {watchdog.result.returncode}",
                "",
                "```text",
                watchdog.result.stdout.strip() or "<empty>",
                "```",
                "",
            ]
        )
        if watchdog.result.stderr.strip():
            sections.extend(
                [
                    "stderr:",
                    "",
                    "```text",
                    watchdog.result.stderr.strip(),
                    "```",
                    "",
                ]
            )

    sections.extend(
        [
            "## Scheduled verdict",
            "",
            f"Process exit code: {strict_result.returncode}",
            "",
        ]
    )
    return "\n".join(sections)


def _render_log(
    *,
    strict_command: list[str],
    strict_result: CommandResult,
    watchdog_results: tuple[WatchdogResult, ...],
) -> str:
    lines = [
        f"$ {_join_command(strict_command)}",
        f"exit_code={strict_result.returncode}",
        strict_result.stderr.strip() or "stderr=<empty>",
        "",
    ]
    for watchdog in watchdog_results:
        lines.extend(
            [
                f"$ {_join_command(list(watchdog.command))}",
                f"exit_code={watchdog.result.returncode}",
                watchdog.result.stderr.strip() or "stderr=<empty>",
                "",
            ]
        )
    return "\n".join(lines)


def _join_command(command: list[str]) -> str:
    return shlex.join(command)
