from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

SOURCE_CODE_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")

JURISDICTION_LEVELS = {"estatal", "autonómica", "provincial", "local", "european", "other"}
ACCESS_METHOD_TYPES = {"api", "json", "xml", "rss", "atom", "html", "pdf", "search", "manual"}
ACCESS_METHOD_STATUSES = {"inventory", "candidate", "validated", "paused", "blocked", "deprecated"}
OPERATIONAL_STATUSES = {
    "inventory_only",
    "monitor_candidate",
    "monitor_validated",
    "metadata_adapter_validated",
    "evidence_grade",
    "paused",
    "blocked",
    "deprecated",
}
SUPPORT_STATUSES = {"none", "planned", "available", "validated"}
MONITOR_CAPABLE_METHOD_TYPES = {"rss", "atom", "api", "xml", "html"}
EVIDENCE_GRADE_ALLOWED_SOURCES = {"BOE", "BOJA", "DOGV", "BOCYL", "BOPV", "BORM"}

REQUIRED_SOURCE_FIELDS = {
    "source_code",
    "name",
    "jurisdiction",
    "jurisdiction_level",
    "official_landing_url",
    "access_methods",
    "operational_status",
    "mcp_support",
    "monitor_support",
    "backfill_support",
    "evidence_adapter",
    "candidate_creation_allowed",
    "evidence_grade_allowed",
    "last_verified_at",
    "limitations",
    "notes",
}


class SourceRegistryError(ValueError):
    pass


def default_registry_path() -> Path:
    return Path(__file__).resolve().parents[2] / "config" / "sources.yaml"


def load_source_registry(path: Path | None = None) -> dict[str, Any]:
    registry_path = path or default_registry_path()
    with registry_path.open(encoding="utf-8") as handle:
        registry = yaml.safe_load(handle)
    validate_source_registry(registry)
    return registry


def list_sources(path: Path | None = None) -> list[dict[str, Any]]:
    registry = load_source_registry(path)
    return sorted(registry["sources"], key=lambda source: source["source_code"])


def get_source(source_code: str, path: Path | None = None) -> dict[str, Any]:
    normalized = source_code.strip().upper()
    for source in list_sources(path):
        if source["source_code"] == normalized:
            return source
    raise SourceRegistryError(f"Unknown source_code: {source_code}")


def validate_source_registry(registry: Any) -> None:
    errors: list[str] = []
    if not isinstance(registry, dict):
        raise SourceRegistryError("registry must be a mapping")
    sources = registry.get("sources")
    if not isinstance(sources, list) or not sources:
        raise SourceRegistryError("sources must be a non-empty list")

    seen_codes: set[str] = set()
    for index, source in enumerate(sources):
        _validate_source(source, index, seen_codes, errors)

    if errors:
        raise SourceRegistryError("; ".join(errors))


def _validate_source(
    source: Any,
    index: int,
    seen_codes: set[str],
    errors: list[str],
) -> None:
    label = f"sources[{index}]"
    if not isinstance(source, dict):
        errors.append(f"{label} must be a mapping")
        return

    missing = sorted(REQUIRED_SOURCE_FIELDS - set(source))
    if missing:
        errors.append(f"{label} missing required fields: {', '.join(missing)}")

    source_code = source.get("source_code")
    if not isinstance(source_code, str) or not SOURCE_CODE_RE.fullmatch(source_code):
        errors.append(f"{label}.source_code must be an uppercase stable identifier")
    elif source_code in seen_codes:
        errors.append(f"{label}.source_code duplicates {source_code}")
    else:
        seen_codes.add(source_code)

    _validate_enum(source, label, "jurisdiction_level", JURISDICTION_LEVELS, errors)
    _validate_enum(source, label, "operational_status", OPERATIONAL_STATUSES, errors)
    _validate_enum(source, label, "monitor_support", SUPPORT_STATUSES, errors)
    _validate_enum(source, label, "backfill_support", SUPPORT_STATUSES, errors)

    for field in (
        "mcp_support",
        "evidence_adapter",
        "candidate_creation_allowed",
        "evidence_grade_allowed",
        "degraded",
    ):
        if field in source and not isinstance(source[field], bool):
            errors.append(f"{label}.{field} must be an explicit boolean")

    if source.get("degraded") is False and source.get("degraded_reason") is not None:
        errors.append(f"{label}.degraded_reason must be null when degraded=false")
    degraded_reason = source.get("degraded_reason")
    if source.get("degraded") is True and (
        degraded_reason is None or not str(degraded_reason).strip()
    ):
        errors.append(f"{label}.degraded_reason is required when degraded=true")
    if "recovery_note" in source and not isinstance(source["recovery_note"], str):
        errors.append(f"{label}.recovery_note must be a string when present")

    limitations = source.get("limitations")
    if "limitations" in source and not isinstance(limitations, list):
        errors.append(f"{label}.limitations must be a list")

    access_methods = source.get("access_methods")
    if not isinstance(access_methods, list):
        errors.append(f"{label}.access_methods must be a list, even if empty")
        access_methods = []

    validated_monitor_methods = 0
    for method_index, method in enumerate(access_methods):
        if not isinstance(method, dict):
            errors.append(f"{label}.access_methods[{method_index}] must be a mapping")
            continue
        method_label = f"{label}.access_methods[{method_index}]"
        _validate_enum(method, method_label, "type", ACCESS_METHOD_TYPES, errors)
        _validate_enum(method, method_label, "status", ACCESS_METHOD_STATUSES, errors)
        if method.get("status") == "validated":
            has_url = bool(str(method.get("url", "")).strip())
            has_notes = bool(str(method.get("notes", "")).strip())
            if not (has_url or has_notes):
                errors.append(f"{method_label}.status=validated requires url or notes")
            if method.get("type") in MONITOR_CAPABLE_METHOD_TYPES:
                validated_monitor_methods += 1

    if source.get("operational_status") == "evidence_grade" and not source.get(
        "evidence_grade_allowed"
    ):
        errors.append(f"{label}.operational_status=evidence_grade requires evidence_grade_allowed")

    if source.get("evidence_grade_allowed") and source_code not in EVIDENCE_GRADE_ALLOWED_SOURCES:
        errors.append(f"{label}.evidence_grade_allowed requires existing code/docs evidence")

    if source.get("monitor_support") == "validated" and validated_monitor_methods == 0:
        errors.append(
            f"{label}.monitor_support=validated requires a validated "
            "rss/atom/api/xml/html access method"
        )


def _validate_enum(
    value: dict[str, Any],
    label: str,
    field: str,
    allowed: set[str],
    errors: list[str],
) -> None:
    if field not in value:
        return
    if value[field] not in allowed:
        allowed_values = ", ".join(sorted(allowed))
        errors.append(f"{label}.{field} must be one of: {allowed_values}")
