from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

DISCOVERY_INPUTS = {
    "rss": ("data/rss_monitor", "rss_discovery.jsonl", "rss_monitor_jsonl"),
    "api": ("data/api_monitor", "api_discovery.jsonl", "api_monitor_jsonl"),
    "html": ("data/html_monitor", "html_discovery.jsonl", "html_monitor_jsonl"),
}
OBSERVED_TIMESTAMP_KEYS = ("discovered_at", "observed_at")
RECORD_DATE_KEYS = ("updated_at", "published_at")


class HermesFreshnessObservationProducerError(ValueError):
    pass


def collect_freshness_observations(
    *,
    runtime_root: Path,
    db_path: Path | None = None,
    source_codes: tuple[str, ...] = (),
) -> tuple[dict[str, Any], ...]:
    normalized_sources = _normalized_sources(source_codes)
    candidates: dict[str, tuple[datetime, dict[str, Any]]] = {}

    for observed_at, observation in _iter_monitor_observations(
        runtime_root.resolve(),
        normalized_sources,
    ):
        _keep_latest(candidates, observed_at, observation)

    if db_path is not None:
        for observed_at, observation in _iter_sqlite_ingestion_observations(
            db_path.resolve(),
            normalized_sources,
        ):
            _keep_latest(candidates, observed_at, observation)

    return tuple(candidates[source][1] for source in sorted(candidates))


def write_observations_jsonl(observations: tuple[dict[str, Any], ...], output_path: Path) -> None:
    lines = [json.dumps(observation, sort_keys=True) for observation in observations]
    output_path.write_text("".join(f"{line}\n" for line in lines), encoding="utf-8")


def _iter_monitor_observations(
    runtime_root: Path,
    source_codes: set[str],
) -> tuple[tuple[datetime, dict[str, Any]], ...]:
    observations: list[tuple[datetime, dict[str, Any]]] = []
    for _, (relative_root, filename, input_kind) in DISCOVERY_INPUTS.items():
        discovery_root = runtime_root / relative_root
        if not discovery_root.exists():
            continue
        for output_path in sorted(discovery_root.glob(f"*/*/{filename}")):
            source_code = output_path.parent.parent.name.strip().upper()
            if source_codes and source_code not in source_codes:
                continue
            parsed = _parse_monitor_output(output_path)
            if parsed is None:
                continue
            observed_at, latest_record_date = parsed
            observation = {
                "source": source_code,
                "observed_at": _format_timestamp(observed_at),
                "observation_kind": "existing_runtime_state",
                "input_path": str(output_path),
                "input_kind": input_kind,
                "timestamp_type": "observed",
                "confidence": "operational",
                "reason": "derived from monitor discovered_at; no live fetch",
            }
            if latest_record_date is not None:
                observation["latest_record_date"] = _format_timestamp(latest_record_date)
            observations.append((observed_at, observation))
    return tuple(observations)


def _parse_monitor_output(output_path: Path) -> tuple[datetime, datetime | None] | None:
    latest_observed: datetime | None = None
    latest_record_date: datetime | None = None
    try:
        lines = output_path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise HermesFreshnessObservationProducerError(
            f"could not read freshness observation input {output_path}: {exc}"
        ) from exc

    for line_number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise HermesFreshnessObservationProducerError(
                f"freshness observation input {output_path}:{line_number} is not valid JSON"
            ) from exc
        if not isinstance(record, dict):
            raise HermesFreshnessObservationProducerError(
                f"freshness observation input {output_path}:{line_number} must be a JSON object"
            )
        observed = _first_timestamp(record, OBSERVED_TIMESTAMP_KEYS)
        if observed is not None and (latest_observed is None or observed > latest_observed):
            latest_observed = observed
        record_date = _first_timestamp(record, RECORD_DATE_KEYS)
        if record_date is not None and (
            latest_record_date is None or record_date > latest_record_date
        ):
            latest_record_date = record_date

    if latest_observed is None:
        return None
    return latest_observed, latest_record_date


def _iter_sqlite_ingestion_observations(
    db_path: Path,
    source_codes: set[str],
) -> tuple[tuple[datetime, dict[str, Any]], ...]:
    if not db_path.exists():
        raise HermesFreshnessObservationProducerError(
            f"SQLite database does not exist: {db_path}"
        )
    observations: dict[str, tuple[datetime, dict[str, Any]]] = {}
    try:
        connection = sqlite3.connect(f"{db_path.as_uri()}?mode=ro", uri=True)
    except sqlite3.Error as exc:
        raise HermesFreshnessObservationProducerError(
            f"could not open SQLite database read-only: {db_path}: {exc}"
        ) from exc
    try:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only = ON")
        rows = connection.execute(
            """
            SELECT id, source_code, status, finished_at
            FROM ingestion_runs
            WHERE status IN ('success', 'no_publication')
              AND finished_at IS NOT NULL
            ORDER BY source_code, id
            """
        ).fetchall()
    except sqlite3.Error as exc:
        raise HermesFreshnessObservationProducerError(
            f"could not read SQLite ingestion_runs from {db_path}: {exc}"
        ) from exc
    finally:
        connection.close()

    for row in rows:
        source_code = str(row["source_code"]).strip().upper()
        if source_codes and source_code not in source_codes:
            continue
        observed_at = _parse_timestamp(str(row["finished_at"]))
        observation = {
            "source": source_code,
            "observed_at": _format_timestamp(observed_at),
            "observation_kind": "existing_runtime_state",
            "input_path": str(db_path),
            "input_kind": "sqlite_ingestion_runs",
            "timestamp_type": "observed",
            "confidence": "operational",
            "reason": (
                "derived from successful ingestion_run "
                f"id={row['id']} status={row['status']}; no live fetch"
            ),
        }
        _keep_latest(observations, observed_at, observation)
    return tuple(observations[source] for source in sorted(observations))


def _keep_latest(
    observations: dict[str, tuple[datetime, dict[str, Any]]],
    observed_at: datetime,
    observation: dict[str, Any],
) -> None:
    source_code = str(observation["source"]).strip().upper()
    current = observations.get(source_code)
    if current is None or observed_at > current[0]:
        observations[source_code] = (observed_at, observation)


def _first_timestamp(record: dict[str, Any], keys: tuple[str, ...]) -> datetime | None:
    for key in keys:
        value = record.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return _parse_timestamp(text)
    return None


def _parse_timestamp(value: str) -> datetime:
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = f"{normalized[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise HermesFreshnessObservationProducerError(f"invalid timestamp: {value}") from exc
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _format_timestamp(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _normalized_sources(source_codes: tuple[str, ...]) -> set[str]:
    return {source.strip().upper() for source in source_codes if source.strip()}
