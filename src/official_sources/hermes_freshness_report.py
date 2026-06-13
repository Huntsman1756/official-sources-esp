from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class HermesFreshnessReportError(ValueError):
    pass


@dataclass(frozen=True)
class SourceFreshness:
    source_code: str
    last_seen: str | None
    threshold_hours: int
    critical: bool
    calendar_exception: str | None
    impact: str

    def __post_init__(self) -> None:
        source_code = self.source_code.strip().upper()
        if not source_code:
            raise HermesFreshnessReportError("source_code is required")
        if self.threshold_hours <= 0:
            raise HermesFreshnessReportError("threshold_hours must be positive")
        object.__setattr__(self, "source_code", source_code)


@dataclass(frozen=True)
class FreshnessObservation:
    now: datetime
    sources: tuple[SourceFreshness, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "now", _ensure_utc(self.now))
        object.__setattr__(self, "sources", tuple(self.sources))


@dataclass(frozen=True)
class FreshnessCheck:
    source_code: str
    status: str
    last_seen: str | None
    threshold_hours: int
    age_hours: float | None
    calendar_exception: str | None
    impact: str
    critical: bool


@dataclass(frozen=True)
class FreshnessResult:
    verdict: str
    generated_at: str
    checks: tuple[FreshnessCheck, ...]
    failures: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    forbidden_actions_confirmed: dict[str, bool] = field(default_factory=dict)


def load_observation(path: Path, *, now: datetime) -> FreshnessObservation:
    with path.open(encoding="utf-8") as handle:
        raw = json.load(handle)
    if not isinstance(raw, dict):
        raise HermesFreshnessReportError("freshness state must be a JSON object")
    raw_sources = raw.get("sources")
    if not isinstance(raw_sources, list):
        raise HermesFreshnessReportError("freshness state must include a sources list")
    sources = tuple(_source_from_mapping(item, index) for index, item in enumerate(raw_sources, 1))
    return FreshnessObservation(now=now, sources=sources)


def evaluate_freshness(observation: FreshnessObservation) -> FreshnessResult:
    failures: list[str] = []
    warnings: list[str] = []
    checks = tuple(
        _evaluate_source(observation.now, source, failures, warnings)
        for source in observation.sources
    )
    if failures:
        verdict = "NO-GO"
    elif warnings:
        verdict = "WARNING"
    else:
        verdict = "GO"
    return FreshnessResult(
        verdict=verdict,
        generated_at=_format_timestamp(observation.now),
        checks=checks,
        failures=tuple(failures),
        warnings=tuple(warnings),
        forbidden_actions_confirmed={
            "git_mutation": False,
            "registry_mutated": False,
            "sqlite_written": False,
            "official_documents_written": False,
            "evidence_created": False,
            "candidates_created": False,
            "artifacts_downloaded": False,
            "downstream_writes": False,
            "publication_created": False,
            "systemd_mutated": False,
        },
    )


def render_markdown_report(result: FreshnessResult) -> str:
    lines = [
        "# Hermes Freshness Report",
        "",
        f"VERDICT: {result.verdict}",
        f"generated_at: {result.generated_at}",
        "",
        "## Checks",
        "",
        "| Source | Status | Last seen | Threshold hours | Age hours | Calendar exception |",
        "| --- | --- | --- | ---: | ---: | --- |",
    ]
    for check in result.checks:
        lines.append(
            "| "
            f"{check.source_code} | "
            f"{check.status} | "
            f"{check.last_seen or 'missing'} | "
            f"{check.threshold_hours} | "
            f"{_display_age(check.age_hours)} | "
            f"{check.calendar_exception or 'none'} |"
        )

    lines.extend(["", "## Impact"])
    if result.checks:
        lines.extend(f"- {check.source_code}: {check.impact}" for check in result.checks)
    else:
        lines.append("- none")

    lines.extend(["", "## Failed gates"])
    if result.failures:
        lines.extend(f"- {failure}" for failure in result.failures)
    else:
        lines.append("- none")

    lines.extend(["", "## Warnings"])
    if result.warnings:
        lines.extend(f"- {warning}" for warning in result.warnings)
    else:
        lines.append("- none")

    lines.extend(["", "## Forbidden actions confirmed"])
    lines.extend(
        f"- {name}: {str(value).lower()}"
        for name, value in result.forbidden_actions_confirmed.items()
    )
    return "\n".join(lines) + "\n"


def parse_timestamp(value: str) -> datetime:
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = f"{normalized[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise HermesFreshnessReportError(f"invalid timestamp: {value}") from exc
    return _ensure_utc(parsed)


def _evaluate_source(
    now: datetime,
    source: SourceFreshness,
    failures: list[str],
    warnings: list[str],
) -> FreshnessCheck:
    if source.calendar_exception:
        return FreshnessCheck(
            source_code=source.source_code,
            status="calendar-exempt",
            last_seen=source.last_seen,
            threshold_hours=source.threshold_hours,
            age_hours=_age_hours(now, source.last_seen) if source.last_seen else None,
            calendar_exception=source.calendar_exception,
            impact=source.impact,
            critical=source.critical,
        )
    if source.last_seen is None:
        if source.critical:
            failures.append(f"{source.source_code} critical freshness timestamp is missing")
        else:
            warnings.append(f"{source.source_code} freshness timestamp is missing")
        return FreshnessCheck(
            source_code=source.source_code,
            status="missing",
            last_seen=None,
            threshold_hours=source.threshold_hours,
            age_hours=None,
            calendar_exception=None,
            impact=source.impact,
            critical=source.critical,
        )

    age_hours = _age_hours(now, source.last_seen)
    if age_hours > source.threshold_hours:
        message = (
            f"{source.source_code} {'critical ' if source.critical else ''}stale for "
            f"{_display_age(age_hours)}h over threshold {source.threshold_hours}h"
        )
        if source.critical:
            failures.append(message)
        else:
            warnings.append(message)
        status = "stale"
    else:
        status = "healthy"
    return FreshnessCheck(
        source_code=source.source_code,
        status=status,
        last_seen=source.last_seen,
        threshold_hours=source.threshold_hours,
        age_hours=age_hours,
        calendar_exception=None,
        impact=source.impact,
        critical=source.critical,
    )


def _source_from_mapping(raw: Any, index: int) -> SourceFreshness:
    if not isinstance(raw, dict):
        raise HermesFreshnessReportError(f"sources[{index}] must be an object")
    try:
        return SourceFreshness(
            source_code=str(raw["source_code"]),
            last_seen=_optional_string(raw.get("last_seen")),
            threshold_hours=int(raw["threshold_hours"]),
            critical=bool(raw["critical"]),
            calendar_exception=_optional_string(raw.get("calendar_exception")),
            impact=str(raw["impact"]),
        )
    except KeyError as exc:
        raise HermesFreshnessReportError(f"sources[{index}] missing field: {exc.args[0]}") from exc


def _age_hours(now: datetime, last_seen: str) -> float:
    delta = now - parse_timestamp(last_seen)
    return round(delta.total_seconds() / 3600, 1)


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _format_timestamp(value: datetime) -> str:
    return _ensure_utc(value).isoformat().replace("+00:00", "Z")


def _display_age(value: float | None) -> str:
    if value is None:
        return "missing"
    return f"{value:.1f}"


def _optional_string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
