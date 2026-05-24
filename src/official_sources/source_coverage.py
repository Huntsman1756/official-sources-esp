from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from official_sources.rss_monitor import (
    RSSMonitorError,
    build_rss_monitor_output_path,
    validate_monitor_date,
)
from official_sources.source_registry import (
    MONITOR_CAPABLE_METHOD_TYPES,
    SourceRegistryError,
)
from official_sources.source_registry import (
    get_source as registry_get_source,
)
from official_sources.source_registry import (
    list_sources as registry_list_sources,
)

DEFAULT_RSS_DISCOVERY_ROOT = Path(__file__).resolve().parents[2] / "data" / "rss_monitor"


def list_source_coverage() -> dict:
    sources = [
        {
            "source_code": source["source_code"],
            "name": source["name"],
            "jurisdiction_level": source["jurisdiction_level"],
            "operational_status": source["operational_status"],
            "monitor_support": source["monitor_support"],
            "evidence_adapter": source["evidence_adapter"],
        }
        for source in registry_list_sources()
    ]
    return {
        "resource_type": "source_coverage",
        "count": len(sources),
        "sources": sources,
    }


def get_source_status(*, source_code: str) -> dict:
    try:
        source = registry_get_source(source_code)
    except SourceRegistryError as exc:
        return _unknown_source(source_code, exc)
    return {
        "status": "ok",
        "resource_type": "source_status",
        "source": source,
        "safety": _source_safety(source),
    }


def list_monitorable_sources() -> dict:
    sources = []
    for source in registry_list_sources():
        methods = [
            _coverage_access_method(method)
            for method in source["access_methods"]
            if method["type"] in MONITOR_CAPABLE_METHOD_TYPES
            and method["status"] != "deprecated"
        ]
        if not methods or source["operational_status"] == "inventory_only":
            continue
        sources.append(
            {
                "source_code": source["source_code"],
                "name": source["name"],
                "operational_status": source["operational_status"],
                "monitor_support": source["monitor_support"],
                "access_methods": methods,
                "candidate_creation_allowed": source["candidate_creation_allowed"],
                "evidence_grade_allowed": source["evidence_grade_allowed"],
            }
        )
    return {
        "resource_type": "monitorable_sources",
        "count": len(sources),
        "sources": sources,
    }


def list_latest_discovery_entries(
    *,
    source_code: str,
    date: str | None = None,
    limit: int | None = 20,
    output_root: Path | None = None,
) -> dict:
    try:
        source = registry_get_source(source_code)
    except SourceRegistryError as exc:
        return _unknown_source(source_code, exc)
    normalized_source_code = source["source_code"]
    if limit is not None and limit < 1:
        return {
            "status": "invalid_request",
            "source_code": normalized_source_code,
            "message": "limit must be greater than zero",
        }

    root = output_root or DEFAULT_RSS_DISCOVERY_ROOT
    target_date = _resolve_discovery_date(root, normalized_source_code, date)
    if target_date is None:
        return {
            "status": "empty",
            "source_code": normalized_source_code,
            "date": None,
            "output_path": str(root / normalized_source_code),
            "entries": [],
            "count": 0,
            "message": "No RSS discovery output exists for this source.",
        }

    output_path = build_rss_monitor_output_path(root, normalized_source_code, target_date)
    if not output_path.exists():
        return {
            "status": "empty",
            "source_code": normalized_source_code,
            "date": target_date,
            "output_path": str(output_path),
            "entries": [],
            "count": 0,
            "message": "No RSS discovery output exists for this source/date.",
        }

    try:
        entries = _read_discovery_jsonl(output_path, limit)
    except json.JSONDecodeError as exc:
        return {
            "status": "invalid_output",
            "source_code": normalized_source_code,
            "date": target_date,
            "output_path": str(output_path),
            "entries": [],
            "count": 0,
            "message": f"RSS discovery output is not valid JSONL: {exc}",
        }
    return {
        "status": "ok",
        "resource_type": "rss_discovery_entries",
        "source_code": normalized_source_code,
        "date": target_date,
        "output_path": str(output_path),
        "entries": entries,
        "count": len(entries),
        "discovery_only": True,
        "safety": _source_safety(source),
    }


def _source_safety(source: dict[str, Any]) -> dict:
    return {
        "candidate_creation_allowed": source["candidate_creation_allowed"],
        "evidence_grade_allowed": source["evidence_grade_allowed"],
        "rss_discovery_is_evidence": False,
        "rss_discovery_is_candidate": False,
    }


def _coverage_access_method(method: dict[str, Any]) -> dict:
    return {
        "type": method["type"],
        "url": method.get("url"),
        "status": method["status"],
        "notes": method.get("notes"),
    }


def _unknown_source(source_code: str, exc: SourceRegistryError) -> dict:
    return {
        "status": "unknown_source",
        "source_code": source_code.strip().upper(),
        "message": str(exc),
    }


def _resolve_discovery_date(root: Path, source_code: str, value: str | None) -> str | None:
    if value is not None:
        try:
            return validate_monitor_date(value)
        except RSSMonitorError:
            return value
    source_root = root / source_code
    if not source_root.exists():
        return None
    candidates = [
        path.name
        for path in source_root.iterdir()
        if path.is_dir() and build_rss_monitor_output_path(root, source_code, path.name).exists()
    ]
    return sorted(candidates, reverse=True)[0] if candidates else None


def _read_discovery_jsonl(output_path: Path, limit: int | None) -> list[dict[str, Any]]:
    entries = []
    for line in output_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        entries.append(json.loads(line))
        if limit is not None and len(entries) >= limit:
            break
    return entries
