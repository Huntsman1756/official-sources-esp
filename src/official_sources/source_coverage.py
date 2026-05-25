from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from official_sources.api_monitor import (
    APIFetcher,
    APIMonitorError,
    build_api_monitor_output_path,
    monitor_api_source,
)
from official_sources.html_monitor import (
    HTMLFetcher,
    HTMLMonitorError,
    build_html_monitor_output_path,
    monitor_html_source,
)
from official_sources.rss_monitor import (
    FeedFetcher,
    RSSMonitorError,
    build_rss_monitor_output_path,
    monitor_source_feed,
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
DEFAULT_API_DISCOVERY_ROOT = Path(__file__).resolve().parents[2] / "data" / "api_monitor"
DEFAULT_HTML_DISCOVERY_ROOT = Path(__file__).resolve().parents[2] / "data" / "html_monitor"


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

    rss_root = output_root or DEFAULT_RSS_DISCOVERY_ROOT
    api_root = output_root or DEFAULT_API_DISCOVERY_ROOT
    html_root = output_root or DEFAULT_HTML_DISCOVERY_ROOT
    target_date = _resolve_discovery_date(
        rss_root,
        api_root,
        html_root,
        normalized_source_code,
        date,
    )
    if target_date is None:
        return {
            "status": "empty",
            "source_code": normalized_source_code,
            "date": None,
            "output_paths": {
                "rss": str(rss_root / normalized_source_code),
                "api": str(api_root / normalized_source_code),
                "html": str(html_root / normalized_source_code),
            },
            "entries": [],
            "count": 0,
            "message": "No discovery output exists for this source.",
        }

    output_paths = {
        "rss": build_rss_monitor_output_path(rss_root, normalized_source_code, target_date),
        "api": build_api_monitor_output_path(api_root, normalized_source_code, target_date),
        "html": build_html_monitor_output_path(html_root, normalized_source_code, target_date),
    }
    existing_output_paths = {
        discovery_type: path for discovery_type, path in output_paths.items() if path.exists()
    }
    if not existing_output_paths:
        return {
            "status": "empty",
            "source_code": normalized_source_code,
            "date": target_date,
            "output_paths": {key: str(path) for key, path in output_paths.items()},
            "entries": [],
            "count": 0,
            "message": "No discovery output exists for this source/date.",
        }

    try:
        entries: list[dict[str, Any]] = []
        for discovery_type, output_path in existing_output_paths.items():
            entries.extend(
                _with_discovery_type(
                    _read_discovery_jsonl(output_path, _remaining_limit(limit, len(entries))),
                    discovery_type,
                )
            )
            if limit is not None and len(entries) >= limit:
                break
    except json.JSONDecodeError as exc:
        return {
            "status": "invalid_output",
            "source_code": normalized_source_code,
            "date": target_date,
            "output_paths": {key: str(path) for key, path in existing_output_paths.items()},
            "entries": [],
            "count": 0,
            "message": f"Discovery output is not valid JSONL: {exc}",
        }
    return {
        "status": "ok",
        "resource_type": "discovery_entries",
        "source_code": normalized_source_code,
        "date": target_date,
        "discovery_types": list(existing_output_paths),
        "output_paths": {key: str(path) for key, path in existing_output_paths.items()},
        "entries": entries,
        "count": len(entries),
        "discovery_only": True,
        "safety": _source_safety(source),
    }


def preview_discovery(
    *,
    source_code: str,
    date: str,
    limit: int = 1,
    discovery_type: str | None = None,
    rss_fetcher: FeedFetcher | None = None,
    api_fetcher: APIFetcher | None = None,
    html_fetcher: HTMLFetcher | None = None,
) -> dict:
    normalized_request_code = source_code.strip().upper()
    if normalized_request_code in {"", "*", "ALL"} or "," in normalized_request_code:
        return {
            "status": "invalid_request",
            "source_code": normalized_request_code,
            "message": "preview_discovery requires one explicit source_code",
        }
    if limit < 1 or limit > 10:
        return {
            "status": "invalid_request",
            "source_code": normalized_request_code,
            "message": "limit must be between 1 and 10",
        }
    requested_type = discovery_type.strip().lower() if discovery_type else None
    if requested_type is not None and requested_type not in {"rss", "api", "html"}:
        return {
            "status": "invalid_request",
            "source_code": normalized_request_code,
            "discovery_type": requested_type,
            "message": "discovery_type must be one of: rss, api, html",
        }
    try:
        source = registry_get_source(normalized_request_code)
    except SourceRegistryError as exc:
        return _unknown_source(normalized_request_code, exc)

    available_types = _implemented_preview_types(source)
    if source["operational_status"] == "inventory_only" or not available_types:
        return _not_monitorable(
            source["source_code"],
            requested_type,
            "Source does not have validated monitor support for MCP preview.",
        )
    selected_type = requested_type or _select_preview_type(available_types)
    if selected_type is None:
        return {
            "status": "invalid_request",
            "source_code": source["source_code"],
            "available_discovery_types": available_types,
            "message": "Multiple discovery types are available; provide discovery_type.",
        }
    if selected_type not in available_types:
        return _not_monitorable(
            source["source_code"],
            selected_type,
            f"Source does not have a validated {selected_type} monitor for MCP preview.",
        )

    try:
        result = _run_preview(
            source,
            selected_type,
            target_date=date,
            limit=limit,
            rss_fetcher=rss_fetcher,
            api_fetcher=api_fetcher,
            html_fetcher=html_fetcher,
        )
    except (RSSMonitorError, APIMonitorError, HTMLMonitorError) as exc:
        return {
            "status": "invalid_request",
            "source_code": source["source_code"],
            "discovery_type": selected_type,
            "message": str(exc),
        }

    records = result.records[:limit]
    return {
        "status": "ok",
        "resource_type": "discovery_preview",
        "source_code": source["source_code"],
        "discovery_type": selected_type,
        "date": date,
        "mode": "preview",
        "records": records,
        "count": len(records),
        "warnings": _preview_warnings(records),
        "output_written": False,
        "discovery_only": True,
        "safety": _source_safety(source),
    }


def _source_safety(source: dict[str, Any]) -> dict:
    return {
        "candidate_creation_allowed": source["candidate_creation_allowed"],
        "evidence_grade_allowed": source["evidence_grade_allowed"],
        "rss_discovery_is_evidence": False,
        "rss_discovery_is_candidate": False,
        "api_discovery_is_evidence": False,
        "api_discovery_is_candidate": False,
        "html_discovery_is_evidence": False,
        "html_discovery_is_candidate": False,
    }


def _implemented_preview_types(source: dict[str, Any]) -> list[str]:
    source_code = source["source_code"]
    access_methods = source.get("access_methods", [])
    preview_types = []
    if any(
        method.get("type") in {"rss", "atom"}
        and method.get("status") == "validated"
        and str(method.get("url", "")).strip()
        for method in access_methods
    ):
        preview_types.append("rss")
    if source_code == "BOPV" and any(
        method.get("type") == "api"
        and method.get("status") == "validated"
        and str(method.get("url", "")).strip()
        for method in access_methods
    ):
        preview_types.append("api")
    if source_code == "BOP_A_CORUNA" and any(
        method.get("type") == "html"
        and method.get("status") == "validated"
        and str(method.get("url", "")).strip()
        for method in access_methods
    ):
        preview_types.append("html")
    return preview_types


def _select_preview_type(available_types: list[str]) -> str | None:
    if len(available_types) == 1:
        return available_types[0]
    return None


def _run_preview(
    source: dict[str, Any],
    discovery_type: str,
    *,
    target_date: str,
    limit: int,
    rss_fetcher: FeedFetcher | None,
    api_fetcher: APIFetcher | None,
    html_fetcher: HTMLFetcher | None,
):
    if discovery_type == "rss":
        return monitor_source_feed(
            source,
            fetcher=rss_fetcher,
            target_date=target_date,
            limit=limit,
        )
    if discovery_type == "api":
        return monitor_api_source(
            source,
            fetcher=api_fetcher,
            target_date=target_date,
            limit=limit,
        )
    if discovery_type == "html":
        return monitor_html_source(
            source,
            fetcher=html_fetcher,
            target_date=target_date,
            limit=limit,
        )
    raise ValueError(f"Unknown discovery_type: {discovery_type}")


def _preview_warnings(records: list[dict[str, Any]]) -> list[str]:
    warnings = []
    for record in records:
        for warning in record.get("warnings", []):
            if warning not in warnings:
                warnings.append(warning)
    return warnings


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


def _not_monitorable(source_code: str, discovery_type: str | None, message: str) -> dict:
    result = {
        "status": "not_monitorable",
        "source_code": source_code,
        "message": message,
    }
    if discovery_type is not None:
        result["discovery_type"] = discovery_type
    return result


def _resolve_discovery_date(
    rss_root: Path,
    api_root: Path,
    html_root: Path,
    source_code: str,
    value: str | None,
) -> str | None:
    if value is not None:
        try:
            return validate_monitor_date(value)
        except RSSMonitorError:
            return value
    candidates = _dated_output_candidates(rss_root, source_code, "rss") + _dated_output_candidates(
        api_root, source_code, "api"
    ) + _dated_output_candidates(
        html_root, source_code, "html"
    )
    return sorted(candidates, reverse=True)[0] if candidates else None


def _dated_output_candidates(root: Path, source_code: str, discovery_type: str) -> list[str]:
    source_root = root / source_code
    if not source_root.exists():
        return []
    return [
        path.name
        for path in source_root.iterdir()
        if path.is_dir()
        and _discovery_output_path(root, source_code, path.name, discovery_type).exists()
    ]


def _discovery_output_path(
    root: Path,
    source_code: str,
    target_date: str,
    discovery_type: str,
) -> Path:
    if discovery_type == "rss":
        return build_rss_monitor_output_path(root, source_code, target_date)
    if discovery_type == "api":
        return build_api_monitor_output_path(root, source_code, target_date)
    if discovery_type == "html":
        return build_html_monitor_output_path(root, source_code, target_date)
    raise ValueError(f"Unknown discovery_type: {discovery_type}")


def _read_discovery_jsonl(output_path: Path, limit: int | None) -> list[dict[str, Any]]:
    entries = []
    for line in output_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        entries.append(json.loads(line))
        if limit is not None and len(entries) >= limit:
            break
    return entries


def _with_discovery_type(
    entries: list[dict[str, Any]],
    discovery_type: str,
) -> list[dict[str, Any]]:
    return [entry | {"discovery_type": discovery_type} for entry in entries]


def _remaining_limit(limit: int | None, current_count: int) -> int | None:
    if limit is None:
        return None
    return max(limit - current_count, 0)
