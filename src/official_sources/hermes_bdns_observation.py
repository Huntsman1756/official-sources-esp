from __future__ import annotations

import json
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from official_sources.integrity.hashing import sha256_bytes
from official_sources.sources.bdns.client import BDNSClient, validate_bdns_limit
from official_sources.sources.bdns.parser import parse_bdns_call_page

DEFAULT_REPO_ROOT = Path("/opt/official-sources/app")
DEFAULT_STATE_ROOT = Path("/var/lib/hermes-official-sources-auditor")
DEFAULT_LIMIT = 1


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str


@dataclass(frozen=True)
class BDNSObservationFetchResult:
    content: bytes
    final_url: str
    status_code: int
    retry_count: int
    throttle_triggered: bool


@dataclass(frozen=True)
class BDNSObservationResult:
    exit_code: int
    api_output_path: Path
    observations_path: Path
    records_seen: int
    latest_record_date: str | None
    fetch_status_code: int | None
    observations_result: CommandResult


CommandRunner = Callable[[list[str], Path], CommandResult]
FetchLatest = Callable[[int], BDNSObservationFetchResult]


def run_bdns_observation(
    *,
    repo_root: Path = DEFAULT_REPO_ROOT,
    state_root: Path = DEFAULT_STATE_ROOT,
    official_sources_bin: str | None = None,
    limit: int = DEFAULT_LIMIT,
    fetch_latest: FetchLatest | None = None,
    run_command: CommandRunner | None = None,
    now: Callable[[], datetime] | None = None,
) -> BDNSObservationResult:
    repo_root = repo_root.resolve()
    state_root = state_root.resolve()
    observed_at = _observed_at(now)
    observed_date = observed_at.date().isoformat()
    freshness_runtime = state_root / "freshness-runtime"
    api_root = freshness_runtime / "data" / "api_monitor"
    api_output_path = api_root / "BDNS" / observed_date / "api_discovery.jsonl"
    observations_path = state_root / "freshness-observations" / "latest-bdns.jsonl"

    try:
        normalized_limit = validate_bdns_limit(limit, option_name="limit")
    except ValueError as exc:
        return _error_result(
            api_output_path=api_output_path,
            observations_path=observations_path,
            stderr=str(exc),
        )

    try:
        api_output_path.parent.mkdir(parents=True, exist_ok=True)
        observations_path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        return _error_result(
            api_output_path=api_output_path,
            observations_path=observations_path,
            stderr=f"could not create BDNS observation directories: {exc}",
        )

    try:
        fetch_result = (fetch_latest or _fetch_latest)(normalized_limit)
        if not 200 <= fetch_result.status_code < 300:
            return _error_result(
                api_output_path=api_output_path,
                observations_path=observations_path,
                stderr=f"BDNS latest observation returned HTTP {fetch_result.status_code}",
                fetch_status_code=fetch_result.status_code,
            )
        page = parse_bdns_call_page(fetch_result.content, source_url=fetch_result.final_url)
    except Exception as exc:
        return _error_result(
            api_output_path=api_output_path,
            observations_path=observations_path,
            stderr=f"BDNS latest observation failed: {exc}",
        )

    if not page.calls:
        return _error_result(
            api_output_path=api_output_path,
            observations_path=observations_path,
            stderr="BDNS latest observation returned no records; no freshness observation written",
            fetch_status_code=fetch_result.status_code,
        )

    latest_record_date = max(call.publication_date for call in page.calls)
    records = [
        {
            "source_code": "BDNS",
            "discovered_at": _format_timestamp(observed_at),
            "published_at": call.publication_date,
            "timestamp_type": "observed",
            "observation_kind": "bdns_latest_observation",
            "official_identifier": call.official_identifier,
            "source_url": page.source_url,
            "status_code": fetch_result.status_code,
            "source_snapshot_hash": sha256_bytes(fetch_result.content),
            "records_seen": len(page.calls),
            "record_index": index,
            "reason": "derived from operator-controlled BDNS latest API observation",
        }
        for index, call in enumerate(page.calls, 1)
    ]
    try:
        api_output_path.write_text(
            "".join(f"{json.dumps(record, sort_keys=True)}\n" for record in records),
            encoding="utf-8",
        )
    except OSError as exc:
        return _error_result(
            api_output_path=api_output_path,
            observations_path=observations_path,
            stderr=f"could not write BDNS API observation JSONL: {exc}",
            fetch_status_code=fetch_result.status_code,
        )

    bin_path = official_sources_bin or str(repo_root / ".venv" / "bin" / "official-sources")
    observations_command = [
        bin_path,
        "hermes",
        "freshness-observations",
        "--runtime-root",
        str(freshness_runtime),
        "--source",
        "BDNS",
        "--output",
        str(observations_path),
    ]
    observations_result = (run_command or _run_command)(observations_command, repo_root)
    if observations_result.returncode == 0 and not observations_path.exists():
        observations_result = CommandResult(
            returncode=2,
            stdout=observations_result.stdout,
            stderr=(
                f"BDNS freshness observation JSONL was not written: {observations_path}"
                if not observations_result.stderr
                else (
                    f"{observations_result.stderr}\n"
                    f"BDNS freshness observation JSONL was not written: {observations_path}"
                )
            ),
        )

    return BDNSObservationResult(
        exit_code=observations_result.returncode,
        api_output_path=api_output_path,
        observations_path=observations_path,
        records_seen=len(page.calls),
        latest_record_date=latest_record_date,
        fetch_status_code=fetch_result.status_code,
        observations_result=observations_result,
    )


def _fetch_latest(limit: int) -> BDNSObservationFetchResult:
    response = BDNSClient().fetch_latest(limit=limit)
    return BDNSObservationFetchResult(
        content=response.content,
        final_url=response.final_url,
        status_code=response.status_code,
        retry_count=response.audit.retry_count,
        throttle_triggered=response.audit.throttle_triggered,
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


def _observed_at(now: Callable[[], datetime] | None) -> datetime:
    generated_at = (now or (lambda: datetime.now(UTC)))()
    if generated_at.tzinfo is None:
        generated_at = generated_at.replace(tzinfo=UTC)
    return generated_at.astimezone(UTC)


def _format_timestamp(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _error_result(
    *,
    api_output_path: Path,
    observations_path: Path,
    stderr: str,
    fetch_status_code: int | None = None,
) -> BDNSObservationResult:
    return BDNSObservationResult(
        exit_code=2,
        api_output_path=api_output_path,
        observations_path=observations_path,
        records_seen=0,
        latest_record_date=None,
        fetch_status_code=fetch_status_code,
        observations_result=CommandResult(returncode=2, stdout="", stderr=stderr),
    )
