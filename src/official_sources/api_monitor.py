from __future__ import annotations

import hashlib
import json
import xml.etree.ElementTree as ET
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
BOR_API_ENDPOINT = "/boletin/ExportarBoletinServlet"
BOP_CACERES_CALENDAR_API_ENDPOINT = "/boletines/bopMesCalendario"
BOP_CACERES_ANNOUNCEMENTS_API_ENDPOINT = "/anuncios/anunciosAnunciantes"
BOP_HUELVA_API_ENDPOINT = "/lib/bope/anuncios_bop/ajaxAnuncios.php"
BOP_OURENSE_API_ENDPOINT = "/portalapi/api/boletin/getFecha/{yyyymmdd}"


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
    base_url = template_url.replace("{year}", str(parsed_date.year)).replace(
        "{month}", str(parsed_date.month)
    )
    return f"{base_url}?{urlencode({'currentPage': 1, 'itemsOfPage': limit, 'lang': 'SPANISH'})}"


def build_bor_calendar_api_url(template_url: str, *, target_date: str) -> str:
    parsed_date = date.fromisoformat(validate_api_monitor_date(target_date))
    params = {"tipo": 3, "mes": parsed_date.month, "anio": parsed_date.year}
    return f"{template_url}?{urlencode(params)}"


def build_bor_issue_api_url(template_url: str, *, target_date: str, issue_number: str) -> str:
    parsed_date = date.fromisoformat(validate_api_monitor_date(target_date))
    fecha = f"{parsed_date:%Y/%m/%d}"
    return f"{template_url}?{urlencode({'tipo': 1, 'fecha': fecha, 'numero': issue_number})}"


def build_bor_announcement_api_url(template_url: str, *, published_at: str, html_ref: str) -> str:
    parsed_date = date.fromisoformat(validate_api_monitor_date(published_at))
    fecha = f"{parsed_date:%Y/%m/%d}"
    return f"{template_url}?{urlencode({'tipo': 2, 'fecha': fecha, 'referencia': html_ref})}"


def build_bop_huelva_api_url(template_url: str, *, target_date: str) -> str:
    params = {"tipo": 2, "fecha": validate_api_monitor_date(target_date)}
    return f"{template_url}?{urlencode(params)}"


def build_bop_caceres_calendar_api_url(base_url: str, *, target_date: str) -> str:
    parsed_date = date.fromisoformat(validate_api_monitor_date(target_date))
    params = {"mes": parsed_date.month, "anio": parsed_date.year}
    return f"{base_url.rstrip('/')}{BOP_CACERES_CALENDAR_API_ENDPOINT}?{urlencode(params)}"


def build_bop_caceres_announcements_api_url(base_url: str, *, issue_id: str) -> str:
    params = {"idBoletin": issue_id}
    return f"{base_url.rstrip('/')}{BOP_CACERES_ANNOUNCEMENTS_API_ENDPOINT}?{urlencode(params)}"


def build_bop_ourense_api_url(template_url: str, *, target_date: str) -> str:
    parsed_date = date.fromisoformat(validate_api_monitor_date(target_date))
    return template_url.replace("{yyyymmdd}", parsed_date.strftime("%Y%m%d")).replace(
        "{date}", parsed_date.isoformat()
    )


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
    fetch = fetcher or fetch_api
    if source_code == "BOPV":
        request_limit = limit or 50
        api_url = build_bopv_api_url(
            access_method["url"], target_date=target_date, limit=request_limit
        )
        raw_response = _coerce_response_bytes(fetch(api_url))
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
    if source_code == "BOR":
        calendar_url = build_bor_calendar_api_url(access_method["url"], target_date=target_date)
        raw_calendar = _coerce_response_bytes(fetch(calendar_url))
        issue_number = parse_bor_calendar_issue_number(raw_calendar, target_date=target_date)
        if not issue_number:
            raw_response_hash = hashlib.sha256(raw_calendar).hexdigest()
            return APIParseResult(raw_response_hash=raw_response_hash, records=[])
        issue_url = build_bor_issue_api_url(
            access_method["url"], target_date=target_date, issue_number=issue_number
        )
        raw_issue = _coerce_response_bytes(fetch(issue_url))
        raw_response_hash = hashlib.sha256(
            raw_calendar + b"\n---BOR-ISSUE---\n" + raw_issue
        ).hexdigest()
        monitor_run_id = hashlib.sha256(
            f"{source_code}{issue_url}{target_date}{raw_response_hash}".encode()
        ).hexdigest()[:16]
        result = parse_bor_issue_response(
            raw_issue,
            source_code=source_code,
            api_url=issue_url,
            api_endpoint=BOR_API_ENDPOINT,
            source_base_url=access_method["url"],
            requested_date=target_date,
            discovered_at=f"{target_date}T00:00:00Z",
            monitor_run_id=monitor_run_id,
        )
        return APIParseResult(raw_response_hash=raw_response_hash, records=result.records[:limit])
    if source_code == "BOP_HUELVA":
        api_url = build_bop_huelva_api_url(access_method["url"], target_date=target_date)
        raw_response = (
            _coerce_response_bytes(fetch(api_url))
            if fetcher
            else fetch_bop_huelva_api(access_method["url"], target_date=target_date)
        )
        raw_response_hash = hashlib.sha256(raw_response).hexdigest()
        monitor_run_id = hashlib.sha256(
            f"{source_code}{api_url}{target_date}{raw_response_hash}".encode()
        ).hexdigest()[:16]
        result = parse_bop_huelva_api_response(
            raw_response,
            source_code=source_code,
            api_url=api_url,
            api_endpoint=BOP_HUELVA_API_ENDPOINT,
            requested_date=target_date,
            discovered_at=f"{target_date}T00:00:00Z",
            monitor_run_id=monitor_run_id,
        )
        return APIParseResult(raw_response_hash=raw_response_hash, records=result.records[:limit])
    if source_code == "BOP_CACERES":
        calendar_url = build_bop_caceres_calendar_api_url(
            access_method["url"], target_date=target_date
        )
        raw_calendar = _coerce_response_bytes(fetch(calendar_url))
        issue_id = parse_bop_caceres_calendar_issue_id(raw_calendar, target_date=target_date)
        if not issue_id:
            raw_response_hash = hashlib.sha256(raw_calendar).hexdigest()
            return APIParseResult(raw_response_hash=raw_response_hash, records=[])
        announcements_url = build_bop_caceres_announcements_api_url(
            access_method["url"], issue_id=issue_id
        )
        raw_announcements = _coerce_response_bytes(fetch(announcements_url))
        raw_response_hash = hashlib.sha256(
            raw_calendar + b"\n---BOP-CACERES-ANNOUNCEMENTS---\n" + raw_announcements
        ).hexdigest()
        monitor_run_id = hashlib.sha256(
            f"{source_code}{announcements_url}{target_date}{raw_response_hash}".encode()
        ).hexdigest()[:16]
        result = parse_bop_caceres_announcements_response(
            raw_announcements,
            source_code=source_code,
            api_url=announcements_url,
            api_endpoint=BOP_CACERES_ANNOUNCEMENTS_API_ENDPOINT,
            requested_date=target_date,
            discovered_at=f"{target_date}T00:00:00Z",
            monitor_run_id=monitor_run_id,
        )
        return APIParseResult(raw_response_hash=raw_response_hash, records=result.records[:limit])
    if source_code == "BOP_OURENSE":
        api_url = build_bop_ourense_api_url(access_method["url"], target_date=target_date)
        raw_response = (
            _coerce_response_bytes(fetch(api_url))
            if fetcher
            else fetch_bop_ourense_api(api_url)
        )
        raw_response_hash = hashlib.sha256(raw_response).hexdigest()
        monitor_run_id = hashlib.sha256(
            f"{source_code}{api_url}{target_date}{raw_response_hash}".encode()
        ).hexdigest()[:16]
        result = parse_bop_ourense_api_response(
            raw_response,
            source_code=source_code,
            api_url=api_url,
            api_endpoint=BOP_OURENSE_API_ENDPOINT,
            requested_date=target_date,
            discovered_at=f"{target_date}T00:00:00Z",
            monitor_run_id=monitor_run_id,
        )
        return APIParseResult(raw_response_hash=raw_response_hash, records=result.records[:limit])
    raise APIMonitorError(
        "api monitor currently supports BOPV, BOR, BOP_CACERES, BOP_HUELVA, and BOP_OURENSE only"
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


def parse_bor_calendar_issue_number(raw_response: bytes | str, *, target_date: str) -> str | None:
    raw_bytes = _coerce_response_bytes(raw_response)
    root = _parse_bor_xml(raw_bytes, context="BOR calendar")
    parsed_date = date.fromisoformat(validate_api_monitor_date(target_date))
    target_value = parsed_date.strftime("%d/%m/%Y")
    for day in root.findall("day"):
        if day.attrib.get("value") == target_value:
            return _string_or_none(day.attrib.get("numero"))
    return None


def parse_bor_issue_response(
    raw_response: bytes | str,
    *,
    source_code: str,
    api_url: str,
    api_endpoint: str,
    source_base_url: str,
    requested_date: str,
    discovered_at: str,
    monitor_run_id: str,
) -> APIParseResult:
    raw_bytes = _coerce_response_bytes(raw_response)
    raw_response_hash = hashlib.sha256(raw_bytes).hexdigest()
    root = _parse_bor_xml(raw_bytes, context="BOR issue")
    issue_number = _bor_issue_number(root)
    published_at = _ddmmyyyy_dash_to_iso(_bor_issue_date(root)) or requested_date

    records = []
    for item in _iter_bor_announcements(root):
        html_ref = item["html_ref"]
        pdf_ref = item["pdf_ref"]
        api_id = html_ref or pdf_ref
        official_url = (
            build_bor_announcement_api_url(
                source_base_url, published_at=published_at, html_ref=html_ref
            )
            if html_ref
            else None
        )
        records.append(
            {
                "source_code": source_code,
                "api_url": api_url,
                "api_endpoint": api_endpoint,
                "title": item["title"],
                "published_at": published_at,
                "official_url": official_url,
                "document_id": api_id,
                "api_id": api_id,
                "issue_number": issue_number,
                "summary": _join_summary_parts(
                    item["section"], item["subsection"], item["department"], item["committee"]
                ),
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
                "warnings": ["pdf_endpoint_not_downloaded"] if pdf_ref else [],
            }
        )
    return APIParseResult(raw_response_hash=raw_response_hash, records=records)


def parse_bop_huelva_api_response(
    raw_response: bytes | str,
    *,
    source_code: str,
    api_url: str,
    api_endpoint: str,
    requested_date: str,
    discovered_at: str,
    monitor_run_id: str,
) -> APIParseResult:
    raw_bytes = _coerce_response_bytes(raw_response)
    raw_response_hash = hashlib.sha256(raw_bytes).hexdigest()
    try:
        payload = json.loads(raw_bytes.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise APIMonitorError(f"BOP_HUELVA API response is not valid JSON: {exc}") from exc
    if payload.get("success") is not True:
        return APIParseResult(raw_response_hash=raw_response_hash, records=[])
    published_at = _string_or_none(payload.get("fecha_publicacion")) or requested_date
    issue_number = _string_or_none((payload.get("Indice") or {}).get("num_bop"))
    return APIParseResult(
        raw_response_hash=raw_response_hash,
        records=[
            _build_bop_huelva_record(
                item=item,
                source_code=source_code,
                api_url=api_url,
                api_endpoint=api_endpoint,
                published_at=published_at,
                issue_number=issue_number,
                raw_response_hash=raw_response_hash,
                discovered_at=discovered_at,
                monitor_run_id=monitor_run_id,
            )
            for item in payload.get("Anuncios", [])
            if isinstance(item, dict)
        ],
    )


def parse_bop_caceres_calendar_issue_id(
    raw_response: bytes | str, *, target_date: str
) -> str | None:
    raw_bytes = _coerce_response_bytes(raw_response)
    try:
        payload = json.loads(raw_bytes.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise APIMonitorError(f"BOP_CACERES calendar response is not valid JSON: {exc}") from exc
    data = payload.get("data", [])
    if not isinstance(data, list):
        raise APIMonitorError("BOP_CACERES calendar response field data must be a list")
    parsed_date = date.fromisoformat(validate_api_monitor_date(target_date))
    for item in data:
        if not isinstance(item, dict):
            continue
        if item.get("diaBop") != parsed_date.day:
            continue
        issue_id = _string_or_none(item.get("idBoletin"))
        if issue_id:
            return issue_id
    return None


def parse_bop_caceres_announcements_response(
    raw_response: bytes | str,
    *,
    source_code: str,
    api_url: str,
    api_endpoint: str,
    requested_date: str,
    discovered_at: str,
    monitor_run_id: str,
) -> APIParseResult:
    raw_bytes = _coerce_response_bytes(raw_response)
    raw_response_hash = hashlib.sha256(raw_bytes).hexdigest()
    try:
        payload = json.loads(raw_bytes.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise APIMonitorError(
            f"BOP_CACERES announcements response is not valid JSON: {exc}"
        ) from exc
    data = payload.get("data", [])
    if not isinstance(data, list):
        raise APIMonitorError("BOP_CACERES announcements response field data must be a list")
    return APIParseResult(
        raw_response_hash=raw_response_hash,
        records=[
            _build_bop_caceres_record(
                item=item,
                source_code=source_code,
                api_url=api_url,
                api_endpoint=api_endpoint,
                requested_date=requested_date,
                raw_response_hash=raw_response_hash,
                discovered_at=discovered_at,
                monitor_run_id=monitor_run_id,
            )
            for item in data
            if isinstance(item, dict)
        ],
    )


def parse_bop_ourense_api_response(
    raw_response: bytes | str,
    *,
    source_code: str,
    api_url: str,
    api_endpoint: str,
    requested_date: str,
    discovered_at: str,
    monitor_run_id: str,
) -> APIParseResult:
    raw_bytes = _coerce_response_bytes(raw_response)
    raw_response_hash = hashlib.sha256(raw_bytes).hexdigest()
    try:
        payload = json.loads(raw_bytes.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise APIMonitorError(f"BOP_OURENSE API response is not valid JSON: {exc}") from exc
    if not isinstance(payload, list):
        raise APIMonitorError("BOP_OURENSE API response must be a list")
    records = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        boletin = item.get("boletin")
        if not isinstance(boletin, dict):
            continue
        published_at = _yyyymmdd_to_iso(_string_or_none(boletin.get("fechaPublicacion")))
        if published_at != requested_date:
            continue
        issue_number = _string_or_none(boletin.get("numeroBop"))
        for edicto in boletin.get("edictos", []):
            if isinstance(edicto, dict):
                records.append(
                    _build_bop_ourense_record(
                        item=edicto,
                        source_code=source_code,
                        api_url=api_url,
                        api_endpoint=api_endpoint,
                        published_at=published_at,
                        issue_number=issue_number,
                        raw_response_hash=raw_response_hash,
                        discovered_at=discovered_at,
                        monitor_run_id=monitor_run_id,
                    )
                )
    return APIParseResult(raw_response_hash=raw_response_hash, records=records)


def write_api_jsonl(records: list[dict[str, Any]], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = "".join(
        f"{json.dumps(record, ensure_ascii=False, sort_keys=True)}\n" for record in records
    )
    output_path.write_text(payload, encoding="utf-8")
    return output_path


def fetch_api(url: str) -> bytes:
    with httpx.Client(follow_redirects=True, timeout=30.0) as client:
        response = client.get(
            url,
            headers={"Accept": "application/json, application/xml, text/xml"},
        )
        response.raise_for_status()
        return response.content


def fetch_bop_huelva_api(url: str, *, target_date: str) -> bytes:
    with httpx.Client(follow_redirects=True, timeout=30.0) as client:
        response = client.post(
            url,
            data={"tipo": "2", "fecha": validate_api_monitor_date(target_date)},
            headers={
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            },
        )
        response.raise_for_status()
        return response.content


def fetch_bop_ourense_api(url: str) -> bytes:
    from official_sources.html_monitor import _html_ssl_context

    with httpx.Client(follow_redirects=True, timeout=30.0, verify=_html_ssl_context()) as client:
        response = client.get(
            url,
            headers={
                "Accept": "application/json,text/plain,*/*",
                "Referer": "https://bop.depourense.es/portal/",
                "User-Agent": "Mozilla/5.0 official-sources-api-monitor/0.1",
            },
        )
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


def _build_bop_huelva_record(
    *,
    item: dict[str, Any],
    source_code: str,
    api_url: str,
    api_endpoint: str,
    published_at: str,
    issue_number: str | None,
    raw_response_hash: str,
    discovered_at: str,
    monitor_run_id: str,
) -> dict[str, Any]:
    api_id = _string_or_none(item.get("id_anuncio")) or _string_or_none(item.get("num_expe"))
    document_id = _string_or_none(item.get("num_expe")) or api_id
    item_published_at = _iso_date_prefix(_string_or_none(item.get("fecha_publicacion")))
    effective_published_at = item_published_at or published_at
    official_url = (
        f"https://s2.diphuelva.es/servicios/bope_web/anuncio/?anuncio={document_id}"
        if document_id
        else None
    )
    warnings = ["pdf_endpoint_not_downloaded"] if _string_or_none(item.get("documento")) else []
    if not official_url:
        warnings.append("entry_hash_fallback_missing_official_url")
    return {
        "source_code": source_code,
        "api_url": api_url,
        "api_endpoint": api_endpoint,
        "title": _string_or_none(item.get("titulo")),
        "published_at": effective_published_at,
        "official_url": official_url,
        "document_id": document_id,
        "api_id": api_id,
        "issue_number": issue_number,
        "summary": _join_summary_parts(
            _string_or_none(item.get("Seccion")),
            _string_or_none(item.get("Categoria")),
            _string_or_none(item.get("entidad_anunciante")),
        ),
        "raw_response_hash": raw_response_hash,
        "entry_hash": build_api_entry_hash(
            source_code=source_code,
            published_at=effective_published_at,
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


def _build_bop_caceres_record(
    *,
    item: dict[str, Any],
    source_code: str,
    api_url: str,
    api_endpoint: str,
    requested_date: str,
    raw_response_hash: str,
    discovered_at: str,
    monitor_run_id: str,
) -> dict[str, Any]:
    api_id = _string_or_none(item.get("idAnuncio"))
    document_id = _string_or_none(item.get("csv")) or api_id
    official_url = (
        f"https://bop.dip-caceres.es/bop/anuncio.html?{urlencode({'csv': document_id})}"
        if document_id and document_id.startswith("BOP-")
        else None
    )
    warnings = []
    if _string_or_none(item.get("urlPdf")):
        warnings.append("pdf_endpoint_not_downloaded")
    if not official_url:
        warnings.append("entry_hash_fallback_missing_official_url")
    return {
        "source_code": source_code,
        "api_url": api_url,
        "api_endpoint": api_endpoint,
        "title": _string_or_none(item.get("tituloAnuncio")),
        "published_at": requested_date,
        "official_url": official_url,
        "document_id": document_id,
        "api_id": api_id,
        "issue_number": _string_or_none(item.get("numBop")),
        "summary": _join_summary_parts(
            _string_or_none(item.get("nombreTipoEntidad")),
            _string_or_none(item.get("nombreGrupoEntidad")),
            _string_or_none(item.get("nombreEntidad")),
        ),
        "raw_response_hash": raw_response_hash,
        "entry_hash": build_api_entry_hash(
            source_code=source_code,
            published_at=requested_date,
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


def _build_bop_ourense_record(
    *,
    item: dict[str, Any],
    source_code: str,
    api_url: str,
    api_endpoint: str,
    published_at: str,
    issue_number: str | None,
    raw_response_hash: str,
    discovered_at: str,
    monitor_run_id: str,
) -> dict[str, Any]:
    api_id = _string_or_none(item.get("id"))
    title = _string_or_none(item.get("sumarioCas")) or _string_or_none(item.get("sumarioGal"))
    official_url = (
        f"https://bop.depourense.es/portalapi/api/edicto/descargar/html/{api_id}/es"
        if api_id
        else None
    )
    warnings = [] if official_url else ["entry_hash_fallback_missing_official_url"]
    seccion = item.get("seccion")
    section_name = _string_or_none(seccion.get("nombre")) if isinstance(seccion, dict) else None
    return {
        "source_code": source_code,
        "api_url": api_url,
        "api_endpoint": api_endpoint,
        "title": title,
        "published_at": published_at,
        "official_url": official_url,
        "document_id": api_id,
        "api_id": api_id,
        "issue_number": issue_number,
        "summary": _join_summary_parts(section_name, _string_or_none(item.get("sumario"))),
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


def _parse_bor_xml(raw_response: bytes, *, context: str) -> ET.Element:
    try:
        root = ET.fromstring(raw_response)
    except ET.ParseError as exc:
        raise APIMonitorError(f"{context} response is not valid XML: {exc}") from exc
    if root.tag != "aplication" or root.attrib.get("status") != "ok":
        raise APIMonitorError(f"{context} response is not an ok BOR payload")
    return root


def _bor_issue_date(root: ET.Element) -> str | None:
    return _xml_text(root.find("./boletin/cabecera/fecha"))


def _bor_issue_number(root: ET.Element) -> str | None:
    return _xml_text(root.find("./boletin/cabecera/numero"))


def _iter_bor_announcements(root: ET.Element) -> list[dict[str, str | None]]:
    records = []
    for section in root.findall("./boletin/anuncios/romano"):
        section_label = _xml_attr(section, "denominacion")
        for subsection in section.findall("letra"):
            subsection_label = _xml_attr(subsection, "denominacion")
            for department in subsection.findall("organo"):
                department_label = _xml_attr(department, "denominacion")
                for committee in department.findall("comite"):
                    committee_label = _xml_attr(committee, "denominacion")
                    for announcement in committee.findall("anuncio"):
                        title = _xml_text(announcement.find("titulo"))
                        html_ref = _bor_content_reference(announcement, "html")
                        pdf_ref = _bor_content_reference(announcement, "pdf")
                        if title and (html_ref or pdf_ref):
                            records.append(
                                {
                                    "title": title,
                                    "html_ref": html_ref,
                                    "pdf_ref": pdf_ref,
                                    "section": section_label,
                                    "subsection": subsection_label,
                                    "department": department_label,
                                    "committee": committee_label,
                                }
                            )
    return records


def _bor_content_reference(announcement: ET.Element, content_type: str) -> str | None:
    for content in announcement.findall("contenido"):
        if content.attrib.get("tipo", "").lower() == content_type:
            return _xml_text(content)
    return None


def _xml_attr(element: ET.Element, key: str) -> str | None:
    return _string_or_none(element.attrib.get(key))


def _xml_text(element: ET.Element | None) -> str | None:
    if element is None or element.text is None:
        return None
    return _string_or_none(element.text)


def _ddmmyyyy_dash_to_iso(value: str | None) -> str | None:
    if not value:
        return None
    try:
        day, month, year = value.split("-")
        return date(int(year), int(month), int(day)).isoformat()
    except ValueError:
        return None


def _yyyymmdd_to_iso(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return date(int(value[:4]), int(value[4:6]), int(value[6:8])).isoformat()
    except ValueError:
        return None


def _iso_date_prefix(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10]).isoformat()
    except ValueError:
        return None


def _join_summary_parts(*values: str | None) -> str | None:
    summary = " - ".join(value for value in values if value and value != "***")
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
