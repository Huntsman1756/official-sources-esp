from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import httpx

from official_sources.source_registry import get_source

APIFetcher = Callable[[str], bytes | str]
BOPV_API_ENDPOINT = "/bopv/administrative-acts/{year}/{month}"


class APIMonitorError(ValueError):
    pass


@dataclass(frozen=True)
class APIParseResult:
    raw_response_hash: str
    records: list[dict[str, Any]]


def validate_api_monitor_date(value: str) -> str:
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError as exc:
        raise APIMonitorError("--date must use YYYY-MM-DD format") from exc


def build_api_entry_hash(
    *,
    source_code: str,
    published_at: str | None,
    official_url: str | None,
    api_id: str | None,
) -> str:
    if official_url:
        hash_input = f"{source_code}{published_at or ''}{official_url}"
        return hashlib.sha256(hash_input.encode()).hexdigest()
    return hashlib.sha256(f"{source_code}{api_id or ''}".encode()).hexdigest()


def build_api_monitor_output_path(output_root: Path, source_code: str, target_date: str) -> Path:
    return output_root / source_code / target_date / "api_discovery.jsonl"


def select_api_access_method(source: dict[str, Any]) -> dict[str, Any]:
    for access_method in source.get("access_methods", []):
        if (
            access_method.get("type") == "api"
            and access_method.get("status") == "validated"
            and str(access_method.get("url", "")).strip()
        ):
            return access_method
    raise APIMonitorError(
        f"{source.get('source_code', 'source')} does not have a validated api access method"
    )


def build_bopv_api_url(template_url: str, *, target_date: str, limit: int) -> str:
    parsed_date = date.fromisoformat(validate_api_monitor_date(target_date))
    base_url = (
        template_url.replace("{year}", str(parsed_date.year)).replace(
            "{month}", str(parsed_date.month)
        )
    )
    return f"{base_url}?{urlencode({'currentPage': 1, 'itemsOfPage': limit, 'lang': 'SPANISH'})}"


def monitor_api_source(
    source: dict[str, Any],
    *,
    fetcher: APIFetcher | None = None,
    target_date: str,
    limit: int | None = None,
) -> APIParseResult:
    target_date = validate_api_monitor_date(target_date)
    if limit is not None and limit < 1:
        raise APIMonitorError("--limit must be greater than zero")

    source_code = source["source_code"]
    access_method = select_api_access_method(source)
    if source_code != "BOPV":
        raise APIMonitorError("api monitor currently supports BOPV only")

    request_limit = limit or 50
    api_url = build_bopv_api_url(access_method["url"], target_date=target_date, limit=request_limit)
    raw_response = _coerce_response_bytes((fetcher or fetch_api)(api_url))
    raw_response_hash = hashlib.sha256(raw_response).hexdigest()
    monitor_run_id = hashlib.sha256(
        f"{source_code}{api_url}{target_date}{raw_response_hash}".encode()
    ).hexdigest()[:16]
    return parse_bopv_api_response(
        raw_response,
        source_code=source_code,
        api_url=api_url,
        api_endpoint=BOPV_API_ENDPOINT,
        discovered_at=f"{target_date}T00:00:00Z",
        monitor_run_id=monitor_run_id,
    )


def monitor_api_source_code(
    source_code: str,
    *,
    fetcher: APIFetcher | None = None,
    target_date: str,
    limit: int | None = None,
) -> APIParseResult:
    return monitor_api_source(
        get_source(source_code),
        fetcher=fetcher,
        target_date=target_date,
        limit=limit,
    )


def parse_bopv_api_response(
    raw_response: bytes | str,
    *,
    source_code: str,
    api_url: str,
    api_endpoint: str,
    discovered_at: str,
    monitor_run_id: str,
) -> APIParseResult:
    raw_bytes = _coerce_response_bytes(raw_response)
    raw_response_hash = hashlib.sha256(raw_bytes).hexdigest()
    try:
        payload = json.loads(raw_bytes.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise APIMonitorError(f"BOPV API response is not valid JSON: {exc}") from exc

    items = payload.get("items", [])
    if not isinstance(items, list):
        raise APIMonitorError("BOPV API response field items must be a list")

    return APIParseResult(
        raw_response_hash=raw_response_hash,
        records=[
            _build_bopv_record(
                item=item,
                source_code=source_code,
                api_url=api_url,
                api_endpoint=api_endpoint,
                raw_response_hash=raw_response_hash,
                discovered_at=discovered_at,
                monitor_run_id=monitor_run_id,
            )
            for item in items
            if isinstance(item, dict)
        ],
    )


def write_api_jsonl(records: list[dict[str, Any]], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = "".join(
        f"{json.dumps(record, ensure_ascii=False, sort_keys=True)}\n" for record in records
    )
    output_path.write_text(payload, encoding="utf-8")
    return output_path


def fetch_api(url: str) -> bytes:
    with httpx.Client(follow_redirects=True, timeout=30.0) as client:
        response = client.get(url, headers={"Accept": "application/json"})
        response.raise_for_status()
        return response.content


def _build_bopv_record(
    *,
    item: dict[str, Any],
    source_code: str,
    api_url: str,
    api_endpoint: str,
    raw_response_hash: str,
    discovered_at: str,
    monitor_run_id: str,
) -> dict[str, Any]:
    api_id = _string_or_none(item.get("id"))
    published_at = _string_or_none(item.get("publishDate"))
    official_url = _bopv_detail_api_url(api_id)
    warnings = [] if official_url else ["entry_hash_fallback_missing_official_url"]
    return {
        "source_code": source_code,
        "api_url": api_url,
        "api_endpoint": api_endpoint,
        "title": _string_or_none(item.get("name")),
        "published_at": published_at,
        "official_url": official_url,
        "document_id": api_id,
        "api_id": api_id,
        "summary": _bopv_summary(item),
        "raw_response_hash": raw_response_hash,
        "entry_hash": build_api_entry_hash(
            source_code=source_code,
            published_at=published_at,
            official_url=official_url,
            api_id=api_id,
        ),
        "discovered_at": discovered_at,
        "monitor_run_id": monitor_run_id,
        "classification_status": "unclassified",
        "evidence_status": "not_evidence",
        "candidate_status": "not_candidate",
        "warnings": warnings,
    }


def _bopv_detail_api_url(api_id: str | None) -> str | None:
    if not api_id:
        return None
    parts = [part for part in api_id.split("/") if part]
    if len(parts) != 3:
        return None
    year, month, order = parts
    if not (year.isdigit() and month.isdigit() and order.isdigit()):
        return None
    return (
        "https://api.euskadi.eus/bopv/administrative-acts/"
        f"{int(year)}/{int(month)}/{int(order)}?lang=SPANISH"
    )


def _bopv_summary(item: dict[str, Any]) -> str | None:
    values = [
        _string_or_none(item.get("section")),
        _string_or_none(item.get("department")),
    ]
    summary = " - ".join(value for value in values if value)
    return summary or None


def _string_or_none(value: object | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _coerce_response_bytes(raw_response: bytes | str) -> bytes:
    if isinstance(raw_response, bytes):
        return raw_response
    return raw_response.encode("utf-8")
