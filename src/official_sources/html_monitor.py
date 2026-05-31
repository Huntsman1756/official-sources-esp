from __future__ import annotations

import hashlib
import html
import json
import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlencode, urljoin

import httpx

from official_sources.source_registry import get_source

HTMLFetcher = Callable[[str], bytes | str]


class HTMLMonitorError(ValueError):
    pass


@dataclass(frozen=True)
class HTMLParseResult:
    raw_page_hash: str
    records: list[dict[str, Any]]


@dataclass(frozen=True)
class BOPAcorunaAnnouncement:
    entry_id: str | None
    document_id: str | None
    title: str | None
    official_url: str | None


def validate_html_monitor_date(value: str) -> str:
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError as exc:
        raise HTMLMonitorError("--date must use YYYY-MM-DD format") from exc


def build_html_entry_hash(
    *,
    source_code: str,
    published_at: str | None,
    official_url: str | None,
    document_id: str | None,
    title: str | None,
) -> str:
    if official_url:
        hash_input = f"{source_code}{published_at or ''}{official_url}"
        return hashlib.sha256(hash_input.encode()).hexdigest()
    return hashlib.sha256(f"{source_code}{document_id or ''}{title or ''}".encode()).hexdigest()


def build_html_monitor_output_path(output_root: Path, source_code: str, target_date: str) -> Path:
    return output_root / source_code / target_date / "html_discovery.jsonl"


def build_bop_a_coruna_html_url(template_url: str, *, target_date: str) -> str:
    parsed_date = date.fromisoformat(validate_html_monitor_date(target_date))
    date_ddmmyyyy = quote(parsed_date.strftime("%d/%m/%Y"), safe="")
    return template_url.replace("{date_ddmmyyyy}", date_ddmmyyyy).replace(
        "{date}", parsed_date.isoformat()
    )


def build_bop_albacete_html_url(template_url: str, *, target_date: str) -> str:
    validate_html_monitor_date(target_date)
    return template_url.replace("{date}", target_date)


def build_bop_alicante_html_url(template_url: str, *, target_date: str) -> str:
    parsed_date = date.fromisoformat(validate_html_monitor_date(target_date))
    date_ddmmyyyy = parsed_date.strftime("%d/%m/%Y")
    param_xml = (
        "<raiz><entrada><registro>"
        f"<fechaPub>{date_ddmmyyyy}</fechaPub>"
        "<tipoorganismo></tipoorganismo>"
        "</registro></entrada></raiz>"
    )
    return f"{template_url}?{urlencode({'nemo': 'BOP_CON', 'param': param_xml, 'usuario': '-'})}"


def build_bop_avila_html_url(template_url: str, *, target_date: str) -> str:
    parsed_date = date.fromisoformat(validate_html_monitor_date(target_date))
    return (
        template_url.replace("{yyyy}", f"{parsed_date:%Y}")
        .replace("{dd_mm_yyyy}", parsed_date.strftime("%d-%m-%Y"))
        .replace("{date}", parsed_date.isoformat())
    )


def build_bop_barcelona_html_url(template_url: str, *, target_date: str) -> str:
    validate_html_monitor_date(target_date)
    return template_url


def build_bop_bizkaia_html_url(template_url: str, *, target_date: str) -> str:
    validate_html_monitor_date(target_date)
    return template_url


def build_bop_castellon_html_url(template_url: str, *, target_date: str) -> str:
    validate_html_monitor_date(target_date)
    return template_url


def build_bop_cordoba_html_url(template_url: str, *, target_date: str) -> str:
    parsed_date = date.fromisoformat(validate_html_monitor_date(target_date))
    return template_url.replace("{dd_mm_yyyy}", parsed_date.strftime("%d-%m-%Y")).replace(
        "{date}", parsed_date.isoformat()
    )


def build_bop_malaga_html_url(template_url: str, *, target_date: str) -> str:
    validate_html_monitor_date(target_date)
    return template_url


def build_bop_pontevedra_html_url(template_url: str, *, target_date: str) -> str:
    parsed_date = date.fromisoformat(validate_html_monitor_date(target_date))
    return (
        template_url.replace("{yyyy}", f"{parsed_date:%Y}")
        .replace("{mm}", f"{parsed_date:%m}")
        .replace("{dd}", f"{parsed_date:%d}")
        .replace("{date}", parsed_date.isoformat())
    )


def build_bop_sevilla_html_url(template_url: str, *, target_date: str) -> str:
    validate_html_monitor_date(target_date)
    return template_url


def build_bop_soria_html_url(template_url: str, *, target_date: str) -> str:
    parsed_date = date.fromisoformat(validate_html_monitor_date(target_date))
    return template_url.replace("{dd_mm_yyyy}", parsed_date.strftime("%d-%m-%Y")).replace(
        "{date}", parsed_date.isoformat()
    )


def build_bop_valencia_html_url(template_url: str, *, target_date: str) -> str:
    validate_html_monitor_date(target_date)
    return template_url


def build_bop_valladolid_html_url(template_url: str, *, target_date: str) -> str:
    validate_html_monitor_date(target_date)
    return template_url.replace("{date}", target_date)


def build_docm_html_url(template_url: str, *, target_date: str) -> str:
    parsed_date = date.fromisoformat(validate_html_monitor_date(target_date))
    return template_url.replace("{yyyymmdd}", f"{parsed_date:%Y%m%d}").replace(
        "{date}", parsed_date.isoformat()
    )


def select_html_access_method(source: dict[str, Any]) -> dict[str, Any]:
    for access_method in source.get("access_methods", []):
        if (
            access_method.get("type") == "html"
            and access_method.get("status") == "validated"
            and str(access_method.get("url", "")).strip()
        ):
            return access_method
    raise HTMLMonitorError(
        f"{source.get('source_code', 'source')} does not have a validated html access method"
    )


def monitor_html_source(
    source: dict[str, Any],
    *,
    fetcher: HTMLFetcher | None = None,
    target_date: str,
    limit: int | None = None,
) -> HTMLParseResult:
    target_date = validate_html_monitor_date(target_date)
    if limit is not None and limit < 1:
        raise HTMLMonitorError("--limit must be greater than zero")

    source_code = source["source_code"]
    access_method = select_html_access_method(source)
    page_url = _build_html_monitor_url(source_code, access_method["url"], target_date=target_date)
    fetch = fetcher or fetch_html
    if source_code == "BOP_BIZKAIA":
        landing_page = _coerce_page_bytes(fetch(page_url))
        detail_url = _extract_bop_bizkaia_latest_detail_url(
            landing_page.decode("utf-8", errors="replace"),
            page_url,
        )
        raw_page = _coerce_page_bytes(fetch(detail_url))
        page_url = detail_url
    elif source_code == "BOP_SEVILLA":
        landing_page = _coerce_page_bytes(fetch(page_url))
        detail_url = _extract_bop_sevilla_latest_detail_url(
            landing_page.decode("utf-8", errors="replace"),
            page_url,
        )
        raw_page = _coerce_page_bytes(fetch(detail_url))
        page_url = detail_url
    elif source_code == "BOP_SORIA":
        landing_page = _coerce_page_bytes(fetch(page_url))
        detail_url = _extract_bop_soria_detail_url(
            landing_page.decode("utf-8", errors="replace"),
            page_url,
        )
        raw_page = _coerce_page_bytes(fetch(detail_url))
        page_url = detail_url
    else:
        raw_page = _coerce_page_bytes(fetch(page_url))
    raw_page_hash = hashlib.sha256(raw_page).hexdigest()
    monitor_run_id = hashlib.sha256(
        f"{source_code}{page_url}{target_date}{raw_page_hash}".encode()
    ).hexdigest()[:16]
    result = _parse_html_monitor_response(
        raw_page,
        source_code=source_code,
        page_url=page_url,
        target_date=target_date,
        discovered_at=f"{target_date}T00:00:00Z",
        monitor_run_id=monitor_run_id,
    )
    if limit is None:
        return result
    return HTMLParseResult(raw_page_hash=result.raw_page_hash, records=result.records[:limit])


def monitor_html_source_code(
    source_code: str,
    *,
    fetcher: HTMLFetcher | None = None,
    target_date: str,
    limit: int | None = None,
) -> HTMLParseResult:
    return monitor_html_source(
        get_source(source_code),
        fetcher=fetcher,
        target_date=target_date,
        limit=limit,
    )


def parse_bop_a_coruna_html(
    raw_page: bytes | str,
    *,
    source_code: str,
    page_url: str,
    published_at: str,
    discovered_at: str,
    monitor_run_id: str,
) -> HTMLParseResult:
    raw_bytes = _coerce_page_bytes(raw_page)
    raw_page_hash = hashlib.sha256(raw_bytes).hexdigest()
    parser = _BOPAcorunaSummaryParser(page_url)
    parser.feed(raw_bytes.decode("utf-8", errors="replace"))
    records = [
        _build_bop_a_coruna_record(
            announcement=announcement,
            source_code=source_code,
            page_url=page_url,
            raw_page_hash=raw_page_hash,
            published_at=published_at,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
        )
        for announcement in parser.announcements
        if announcement.document_id or announcement.title
    ]
    return HTMLParseResult(raw_page_hash=raw_page_hash, records=records)


def parse_bop_albacete_html(
    raw_page: bytes | str,
    *,
    source_code: str,
    page_url: str,
    requested_date: str,
    discovered_at: str,
    monitor_run_id: str,
) -> HTMLParseResult:
    raw_bytes = _coerce_page_bytes(raw_page)
    raw_page_hash = hashlib.sha256(raw_bytes).hexdigest()
    text = raw_bytes.decode("utf-8", errors="replace")
    published_at = _extract_bop_albacete_publication_date(text) or requested_date
    records = [
        _build_html_record(
            source_code=source_code,
            page_url=page_url,
            page_format="html",
            entry_id=document_id,
            document_id=document_id,
            title=title,
            published_at=published_at,
            official_url=urljoin(page_url, href),
            summary=None,
            raw_page_hash=raw_page_hash,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
            warnings=["pdf_endpoint_not_downloaded"],
        )
        for title, href, document_id in _iter_bop_albacete_announcements(text)
    ]
    return HTMLParseResult(raw_page_hash=raw_page_hash, records=records)


def parse_bop_alicante_response(
    raw_page: bytes | str,
    *,
    source_code: str,
    page_url: str,
    requested_date: str,
    discovered_at: str,
    monitor_run_id: str,
) -> HTMLParseResult:
    raw_bytes = _coerce_page_bytes(raw_page)
    raw_page_hash = hashlib.sha256(raw_bytes).hexdigest()
    try:
        payload = json.loads(raw_bytes.decode("utf-8", errors="replace"))
    except json.JSONDecodeError as exc:
        raise HTMLMonitorError("BOP_ALICANTE response is not valid JSON") from exc

    records = []
    for item in _bop_alicante_items(payload):
        document_id = _first_json_value(item, "edicto")
        title = _first_json_value(item, "extracto")
        official_url = _first_json_value(item, "ubicacion")
        n_bop = _first_json_value(item, "nBop")
        published_at = _ddmmyyyy_to_iso(_first_json_value(item, "fechaPublica")) or requested_date
        summary = (
            " - ".join(
                value
                for value in [
                    _first_json_value(item, "gndenom"),
                    _first_json_value(item, "ampliacion"),
                ]
                if value
            )
            or None
        )
        entry_id = "-".join(value for value in [n_bop, document_id] if value) or None
        records.append(
            _build_html_record(
                source_code=source_code,
                page_url=page_url,
                page_format="json-backed-html",
                entry_id=entry_id,
                document_id=document_id,
                title=title,
                published_at=published_at,
                official_url=official_url,
                summary=summary,
                raw_page_hash=raw_page_hash,
                discovered_at=discovered_at,
                monitor_run_id=monitor_run_id,
                warnings=["pdf_endpoint_not_downloaded"] if official_url else [],
            )
        )
    return HTMLParseResult(raw_page_hash=raw_page_hash, records=records)


def parse_bop_avila_html(
    raw_page: bytes | str,
    *,
    source_code: str,
    page_url: str,
    requested_date: str,
    discovered_at: str,
    monitor_run_id: str,
) -> HTMLParseResult:
    raw_bytes = _coerce_page_bytes(raw_page)
    raw_page_hash = hashlib.sha256(raw_bytes).hexdigest()
    text = raw_bytes.decode("utf-8", errors="replace")
    published_at = _extract_bop_avila_publication_date(text) or requested_date
    records = [
        _build_html_record(
            source_code=source_code,
            page_url=page_url,
            page_format="html",
            entry_id=document_id,
            document_id=document_id,
            title=title,
            published_at=published_at,
            official_url=urljoin(page_url, href),
            summary=None,
            raw_page_hash=raw_page_hash,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
            warnings=["pdf_endpoint_not_downloaded"],
        )
        for title, href, document_id in _iter_bop_avila_announcements(text)
    ]
    return HTMLParseResult(raw_page_hash=raw_page_hash, records=records)


def parse_bop_barcelona_html(
    raw_page: bytes | str,
    *,
    source_code: str,
    page_url: str,
    requested_date: str,
    discovered_at: str,
    monitor_run_id: str,
) -> HTMLParseResult:
    raw_bytes = _coerce_page_bytes(raw_page)
    raw_page_hash = hashlib.sha256(raw_bytes).hexdigest()
    text = raw_bytes.decode("utf-8", errors="replace")
    records = [
        _build_html_record(
            source_code=source_code,
            page_url=page_url,
            page_format="html",
            entry_id=document_id,
            document_id=document_id,
            title=title,
            published_at=published_at or requested_date,
            official_url=urljoin(page_url, href),
            summary=None,
            raw_page_hash=raw_page_hash,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
            warnings=[],
        )
        for title, href, document_id, published_at in _iter_bop_barcelona_announcements(text)
    ]
    return HTMLParseResult(raw_page_hash=raw_page_hash, records=records)


def parse_bop_bizkaia_detail_html(
    raw_page: bytes | str,
    *,
    source_code: str,
    page_url: str,
    requested_date: str,
    discovered_at: str,
    monitor_run_id: str,
) -> HTMLParseResult:
    raw_bytes = _coerce_page_bytes(raw_page)
    raw_page_hash = hashlib.sha256(raw_bytes).hexdigest()
    text = raw_bytes.decode("utf-8", errors="replace")
    published_at = _extract_bop_bizkaia_publication_date(page_url) or requested_date
    records = [
        _build_html_record(
            source_code=source_code,
            page_url=page_url,
            page_format="html",
            entry_id=document_id,
            document_id=document_id,
            title=title,
            published_at=published_at,
            official_url=urljoin(page_url, href),
            summary=None,
            raw_page_hash=raw_page_hash,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
            warnings=["pdf_endpoint_not_downloaded"],
        )
        for title, href, document_id in _iter_bop_bizkaia_announcements(text)
    ]
    return HTMLParseResult(raw_page_hash=raw_page_hash, records=records)


def parse_bop_castellon_html(
    raw_page: bytes | str,
    *,
    source_code: str,
    page_url: str,
    requested_date: str,
    discovered_at: str,
    monitor_run_id: str,
) -> HTMLParseResult:
    raw_bytes = _coerce_page_bytes(raw_page)
    raw_page_hash = hashlib.sha256(raw_bytes).hexdigest()
    text = raw_bytes.decode("utf-8", errors="replace")
    published_at = _extract_bop_castellon_publication_date(text) or requested_date
    records = [
        _build_html_record(
            source_code=source_code,
            page_url=page_url,
            page_format="html",
            entry_id=document_id,
            document_id=document_id,
            title=title,
            published_at=published_at,
            official_url=urljoin(page_url, href),
            summary=section,
            raw_page_hash=raw_page_hash,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
            warnings=["pdf_endpoint_not_downloaded"],
        )
        for title, href, document_id, section in _iter_bop_castellon_announcements(text)
    ]
    return HTMLParseResult(raw_page_hash=raw_page_hash, records=records)


def parse_bop_cordoba_html(
    raw_page: bytes | str,
    *,
    source_code: str,
    page_url: str,
    requested_date: str,
    discovered_at: str,
    monitor_run_id: str,
) -> HTMLParseResult:
    raw_bytes = _coerce_page_bytes(raw_page)
    raw_page_hash = hashlib.sha256(raw_bytes).hexdigest()
    text = raw_bytes.decode("utf-8", errors="replace")
    published_at = _extract_bop_cordoba_publication_date(page_url) or requested_date
    records = [
        _build_html_record(
            source_code=source_code,
            page_url=page_url,
            page_format="nextjs-rsc-html",
            entry_id=entry_id,
            document_id=document_id,
            title=title,
            published_at=published_at,
            official_url=urljoin(page_url, href),
            summary=issuer,
            raw_page_hash=raw_page_hash,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
            warnings=["pdf_endpoint_not_downloaded"],
        )
        for entry_id, title, href, document_id, issuer in _iter_bop_cordoba_announcements(text)
    ]
    return HTMLParseResult(raw_page_hash=raw_page_hash, records=records)


def parse_bop_malaga_html(
    raw_page: bytes | str,
    *,
    source_code: str,
    page_url: str,
    requested_date: str,
    discovered_at: str,
    monitor_run_id: str,
) -> HTMLParseResult:
    raw_bytes = _coerce_page_bytes(raw_page)
    raw_page_hash = hashlib.sha256(raw_bytes).hexdigest()
    text = raw_bytes.decode("utf-8", errors="replace")
    published_at = _extract_bop_malaga_publication_date(text) or requested_date
    records = [
        _build_html_record(
            source_code=source_code,
            page_url=page_url,
            page_format="html",
            entry_id=document_id,
            document_id=document_id,
            title=title,
            published_at=published_at,
            official_url=urljoin(page_url, href),
            summary=None,
            raw_page_hash=raw_page_hash,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
            warnings=[],
        )
        for title, href, document_id in _iter_bop_malaga_announcements(text)
    ]
    return HTMLParseResult(raw_page_hash=raw_page_hash, records=records)


def parse_bop_pontevedra_html(
    raw_page: bytes | str,
    *,
    source_code: str,
    page_url: str,
    requested_date: str,
    discovered_at: str,
    monitor_run_id: str,
) -> HTMLParseResult:
    raw_bytes = _coerce_page_bytes(raw_page)
    raw_page_hash = hashlib.sha256(raw_bytes).hexdigest()
    text = raw_bytes.decode("utf-8", errors="replace")
    published_at = _extract_bop_pontevedra_publication_date(text) or requested_date
    records = [
        _build_html_record(
            source_code=source_code,
            page_url=page_url,
            page_format="html",
            entry_id=document_id,
            document_id=document_id,
            title=title,
            published_at=published_at,
            official_url=urljoin(page_url, href),
            summary=issuer,
            raw_page_hash=raw_page_hash,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
            warnings=["pdf_endpoint_not_downloaded"],
        )
        for title, href, document_id, issuer in _iter_bop_pontevedra_announcements(text)
    ]
    return HTMLParseResult(raw_page_hash=raw_page_hash, records=records)


def parse_bop_sevilla_html(
    raw_page: bytes | str,
    *,
    source_code: str,
    page_url: str,
    requested_date: str,
    discovered_at: str,
    monitor_run_id: str,
) -> HTMLParseResult:
    raw_bytes = _coerce_page_bytes(raw_page)
    raw_page_hash = hashlib.sha256(raw_bytes).hexdigest()
    text = raw_bytes.decode("utf-8", errors="replace")
    records = [
        _build_html_record(
            source_code=source_code,
            page_url=page_url,
            page_format="html",
            entry_id=document_id,
            document_id=document_id,
            title=title,
            published_at=published_at or requested_date,
            official_url=urljoin(page_url, href),
            summary=summary,
            raw_page_hash=raw_page_hash,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
            warnings=[],
        )
        for title, href, document_id, published_at, summary in _iter_bop_sevilla_announcements(text)
    ]
    return HTMLParseResult(raw_page_hash=raw_page_hash, records=records)


def parse_bop_soria_html(
    raw_page: bytes | str,
    *,
    source_code: str,
    page_url: str,
    requested_date: str,
    discovered_at: str,
    monitor_run_id: str,
) -> HTMLParseResult:
    raw_bytes = _coerce_page_bytes(raw_page)
    raw_page_hash = hashlib.sha256(raw_bytes).hexdigest()
    text = raw_bytes.decode("utf-8", errors="replace")
    published_at = _extract_bop_soria_publication_date(text) or requested_date
    records = [
        _build_html_record(
            source_code=source_code,
            page_url=page_url,
            page_format="html",
            entry_id=document_id,
            document_id=document_id,
            title=title,
            published_at=published_at,
            official_url=urljoin(page_url, href),
            summary=summary,
            raw_page_hash=raw_page_hash,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
            warnings=["pdf_endpoint_not_downloaded"],
        )
        for title, href, document_id, summary in _iter_bop_soria_announcements(text)
    ]
    return HTMLParseResult(raw_page_hash=raw_page_hash, records=records)


def parse_bop_valencia_html(
    raw_page: bytes | str,
    *,
    source_code: str,
    page_url: str,
    requested_date: str,
    discovered_at: str,
    monitor_run_id: str,
) -> HTMLParseResult:
    raw_bytes = _coerce_page_bytes(raw_page)
    raw_page_hash = hashlib.sha256(raw_bytes).hexdigest()
    text = raw_bytes.decode("utf-8", errors="replace")
    records = [
        _build_html_record(
            source_code=source_code,
            page_url=page_url,
            page_format="html",
            entry_id=document_id,
            document_id=document_id,
            title=title,
            published_at=published_at or requested_date,
            official_url=None,
            summary=None,
            raw_page_hash=raw_page_hash,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
            warnings=[],
        )
        for title, document_id, published_at in _iter_bop_valencia_announcements(text)
    ]
    return HTMLParseResult(raw_page_hash=raw_page_hash, records=records)


def parse_bop_valladolid_html(
    raw_page: bytes | str,
    *,
    source_code: str,
    page_url: str,
    requested_date: str,
    discovered_at: str,
    monitor_run_id: str,
) -> HTMLParseResult:
    raw_bytes = _coerce_page_bytes(raw_page)
    raw_page_hash = hashlib.sha256(raw_bytes).hexdigest()
    text = raw_bytes.decode("utf-8", errors="replace")
    published_at = _extract_bop_valladolid_publication_date(text) or requested_date
    records = [
        _build_html_record(
            source_code=source_code,
            page_url=page_url,
            page_format="html",
            entry_id=document_id,
            document_id=document_id,
            title=title,
            published_at=published_at,
            official_url=urljoin(page_url, href),
            summary=issuer,
            raw_page_hash=raw_page_hash,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
            warnings=["pdf_endpoint_not_downloaded"],
        )
        for title, href, document_id, issuer in _iter_bop_valladolid_announcements(text)
    ]
    return HTMLParseResult(raw_page_hash=raw_page_hash, records=records)


def parse_docm_html(
    raw_page: bytes | str,
    *,
    source_code: str,
    page_url: str,
    requested_date: str,
    discovered_at: str,
    monitor_run_id: str,
) -> HTMLParseResult:
    raw_bytes = _coerce_page_bytes(raw_page)
    raw_page_hash = hashlib.sha256(raw_bytes).hexdigest()
    text = raw_bytes.decode("utf-8", errors="replace")
    published_at = _extract_docm_publication_date(text) or requested_date
    issue_number = _extract_docm_issue_number(text)
    records = []
    for item in _iter_docm_announcements(text):
        record = _build_html_record(
            source_code=source_code,
            page_url=page_url,
            page_format="html",
            entry_id=item["entry_id"],
            document_id=item["document_id"],
            title=item["title"],
            published_at=published_at,
            official_url=urljoin(page_url, item["href"]) if item["href"] else None,
            summary=item["summary"],
            raw_page_hash=raw_page_hash,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
            warnings=["pdf_endpoint_not_downloaded"] if item["has_pdf"] else [],
        )
        if issue_number:
            record["issue_number"] = issue_number
        if item["page"]:
            record["page"] = item["page"]
        records.append(record)
    return HTMLParseResult(raw_page_hash=raw_page_hash, records=records)


def write_html_jsonl(records: list[dict[str, Any]], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = "".join(
        f"{json.dumps(record, ensure_ascii=False, sort_keys=True)}\n" for record in records
    )
    output_path.write_text(payload, encoding="utf-8")
    return output_path


def fetch_html(url: str) -> bytes:
    try:
        with httpx.Client(follow_redirects=True, timeout=30.0) as client:
            response = client.get(
                url,
                headers={
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "User-Agent": "official-sources-html-monitor/0.1",
                },
            )
            response.raise_for_status()
            return response.content
    except httpx.HTTPError as exc:
        raise HTMLMonitorError(f"html monitor fetch failed for {url}: {exc}") from exc


def _build_bop_a_coruna_record(
    *,
    announcement: BOPAcorunaAnnouncement,
    source_code: str,
    page_url: str,
    raw_page_hash: str,
    published_at: str,
    discovered_at: str,
    monitor_run_id: str,
) -> dict[str, Any]:
    return _build_html_record(
        source_code=source_code,
        page_url=page_url,
        page_format="html",
        entry_id=announcement.entry_id,
        document_id=announcement.document_id,
        title=announcement.title,
        published_at=published_at,
        official_url=announcement.official_url,
        summary=None,
        raw_page_hash=raw_page_hash,
        discovered_at=discovered_at,
        monitor_run_id=monitor_run_id,
        warnings=[],
    )


def _build_html_monitor_url(source_code: str, template_url: str, *, target_date: str) -> str:
    if source_code == "BOP_A_CORUNA":
        return build_bop_a_coruna_html_url(template_url, target_date=target_date)
    if source_code == "BOP_ALBACETE":
        return build_bop_albacete_html_url(template_url, target_date=target_date)
    if source_code == "BOP_ALICANTE":
        return build_bop_alicante_html_url(template_url, target_date=target_date)
    if source_code == "BOP_AVILA":
        return build_bop_avila_html_url(template_url, target_date=target_date)
    if source_code == "BOP_BARCELONA":
        return build_bop_barcelona_html_url(template_url, target_date=target_date)
    if source_code == "BOP_BIZKAIA":
        return build_bop_bizkaia_html_url(template_url, target_date=target_date)
    if source_code == "BOP_CASTELLON":
        return build_bop_castellon_html_url(template_url, target_date=target_date)
    if source_code == "BOP_CORDOBA":
        return build_bop_cordoba_html_url(template_url, target_date=target_date)
    if source_code == "BOP_MALAGA":
        return build_bop_malaga_html_url(template_url, target_date=target_date)
    if source_code == "BOP_PONTEVEDRA":
        return build_bop_pontevedra_html_url(template_url, target_date=target_date)
    if source_code == "BOP_SEVILLA":
        return build_bop_sevilla_html_url(template_url, target_date=target_date)
    if source_code == "BOP_SORIA":
        return build_bop_soria_html_url(template_url, target_date=target_date)
    if source_code == "BOP_VALENCIA":
        return build_bop_valencia_html_url(template_url, target_date=target_date)
    if source_code == "BOP_VALLADOLID":
        return build_bop_valladolid_html_url(template_url, target_date=target_date)
    if source_code == "DOCM":
        return build_docm_html_url(template_url, target_date=target_date)
    raise HTMLMonitorError(
        "html monitor currently supports BOP_A_CORUNA, BOP_ALBACETE, BOP_ALICANTE, "
        "BOP_AVILA, BOP_BARCELONA, BOP_BIZKAIA, BOP_CASTELLON, BOP_CORDOBA, "
        "BOP_MALAGA, BOP_SEVILLA, BOP_SORIA, BOP_PONTEVEDRA, BOP_VALENCIA, "
        "BOP_VALLADOLID, and DOCM only"
    )


def _parse_html_monitor_response(
    raw_page: bytes,
    *,
    source_code: str,
    page_url: str,
    target_date: str,
    discovered_at: str,
    monitor_run_id: str,
) -> HTMLParseResult:
    if source_code == "BOP_A_CORUNA":
        return parse_bop_a_coruna_html(
            raw_page,
            source_code=source_code,
            page_url=page_url,
            published_at=target_date,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
        )
    if source_code == "BOP_ALBACETE":
        return parse_bop_albacete_html(
            raw_page,
            source_code=source_code,
            page_url=page_url,
            requested_date=target_date,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
        )
    if source_code == "BOP_ALICANTE":
        return parse_bop_alicante_response(
            raw_page,
            source_code=source_code,
            page_url=page_url,
            requested_date=target_date,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
        )
    if source_code == "BOP_AVILA":
        return parse_bop_avila_html(
            raw_page,
            source_code=source_code,
            page_url=page_url,
            requested_date=target_date,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
        )
    if source_code == "BOP_BARCELONA":
        return parse_bop_barcelona_html(
            raw_page,
            source_code=source_code,
            page_url=page_url,
            requested_date=target_date,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
        )
    if source_code == "BOP_BIZKAIA":
        return parse_bop_bizkaia_detail_html(
            raw_page,
            source_code=source_code,
            page_url=page_url,
            requested_date=target_date,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
        )
    if source_code == "BOP_CASTELLON":
        return parse_bop_castellon_html(
            raw_page,
            source_code=source_code,
            page_url=page_url,
            requested_date=target_date,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
        )
    if source_code == "BOP_CORDOBA":
        return parse_bop_cordoba_html(
            raw_page,
            source_code=source_code,
            page_url=page_url,
            requested_date=target_date,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
        )
    if source_code == "BOP_MALAGA":
        return parse_bop_malaga_html(
            raw_page,
            source_code=source_code,
            page_url=page_url,
            requested_date=target_date,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
        )
    if source_code == "BOP_PONTEVEDRA":
        return parse_bop_pontevedra_html(
            raw_page,
            source_code=source_code,
            page_url=page_url,
            requested_date=target_date,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
        )
    if source_code == "BOP_SEVILLA":
        return parse_bop_sevilla_html(
            raw_page,
            source_code=source_code,
            page_url=page_url,
            requested_date=target_date,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
        )
    if source_code == "BOP_SORIA":
        return parse_bop_soria_html(
            raw_page,
            source_code=source_code,
            page_url=page_url,
            requested_date=target_date,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
        )
    if source_code == "BOP_VALENCIA":
        return parse_bop_valencia_html(
            raw_page,
            source_code=source_code,
            page_url=page_url,
            requested_date=target_date,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
        )
    if source_code == "BOP_VALLADOLID":
        return parse_bop_valladolid_html(
            raw_page,
            source_code=source_code,
            page_url=page_url,
            requested_date=target_date,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
        )
    if source_code == "DOCM":
        return parse_docm_html(
            raw_page,
            source_code=source_code,
            page_url=page_url,
            requested_date=target_date,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
        )
    raise HTMLMonitorError(f"Unsupported html monitor source: {source_code}")


def _build_html_record(
    *,
    source_code: str,
    page_url: str,
    page_format: str,
    entry_id: str | None,
    document_id: str | None,
    title: str | None,
    published_at: str | None,
    official_url: str | None,
    summary: str | None,
    raw_page_hash: str,
    discovered_at: str,
    monitor_run_id: str,
    warnings: list[str],
) -> dict[str, Any]:
    normalized_warnings = list(warnings)
    if not official_url:
        normalized_warnings.append("entry_hash_fallback_missing_official_url")
    return {
        "source_code": source_code,
        "page_url": page_url,
        "page_format": page_format,
        "entry_id": entry_id,
        "document_id": document_id,
        "title": title,
        "published_at": published_at,
        "official_url": official_url,
        "summary": summary,
        "raw_page_hash": raw_page_hash,
        "entry_hash": build_html_entry_hash(
            source_code=source_code,
            published_at=published_at,
            official_url=official_url,
            document_id=document_id,
            title=title,
        ),
        "discovered_at": discovered_at,
        "monitor_run_id": monitor_run_id,
        "classification_status": "unclassified",
        "evidence_status": "not_evidence",
        "candidate_status": "not_candidate",
        "warnings": normalized_warnings,
    }


class _BOPAcorunaSummaryParser(HTMLParser):
    def __init__(self, page_url: str) -> None:
        super().__init__(convert_charrefs=True)
        self._page_url = page_url
        self._in_block = False
        self._block_depth = 0
        self._current_id: str | None = None
        self._current_href: str | None = None
        self._links: list[tuple[str, str]] = []
        self.announcements: list[BOPAcorunaAnnouncement] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "div" and _has_class(attributes.get("class"), "bloqueAnuncio"):
            self._in_block = True
            self._block_depth = 1
            self._current_id = attributes.get("id")
            self._links = []
            return
        if self._in_block:
            if tag == "div":
                self._block_depth += 1
            if tag == "a":
                self._current_href = attributes.get("href")

    def handle_data(self, data: str) -> None:
        if not self._in_block or not self._current_href:
            return
        text = _normalize_text(data)
        if text:
            self._links.append((self._current_href, text))

    def handle_endtag(self, tag: str) -> None:
        if not self._in_block:
            return
        if tag == "a":
            self._current_href = None
        if tag == "div":
            self._block_depth -= 1
            if self._block_depth <= 0:
                self._append_current_announcement()
                self._in_block = False
                self._current_id = None
                self._links = []

    def _append_current_announcement(self) -> None:
        document_id = _first_document_id(text for _, text in self._links)
        title = _first_title(self._links, document_id)
        official_url = _first_html_url(self._links, self._page_url)
        self.announcements.append(
            BOPAcorunaAnnouncement(
                entry_id=self._current_id,
                document_id=document_id,
                title=title,
                official_url=official_url,
            )
        )


def _first_document_id(values: object) -> str | None:
    for value in values:
        match = re.search(r"\b\d{4}/\d+\b", str(value))
        if match:
            return match.group(0)
    return None


def _first_title(links: list[tuple[str, str]], document_id: str | None) -> str | None:
    for _, text in links:
        normalized = _normalize_text(text)
        if not normalized or normalized == document_id:
            continue
        if normalized.upper() == "PDF" or normalized.upper().startswith("HTML"):
            continue
        return normalized
    return None


def _first_html_url(links: list[tuple[str, str]], page_url: str) -> str | None:
    for href, _ in links:
        if href.lower().split("?", 1)[0].endswith(".html"):
            return urljoin(page_url, href)
    return None


def _extract_bop_albacete_publication_date(text: str) -> str | None:
    match = re.search(r"Bolet[ií]n\s+N[uú]mero\s+\d+\s+\((\d{2}/\d{2}/\d{4})\)", text, re.I)
    if not match:
        return None
    return _ddmmyyyy_to_iso(match.group(1))


def _iter_bop_albacete_announcements(text: str) -> list[tuple[str, str, str]]:
    pattern = re.compile(
        r'<div[^>]*class="[^"]*\bcol-12\b(?![^"]*\btext-end\b)[^"]*"[^>]*>'
        r"\s*(?P<title>[^<][^<]*?)\s*</div>\s*"
        r'<div[^>]*class="[^"]*\bcol-12\b[^"]*\btext-end\b[^"]*"[^>]*>\s*'
        r'<a[^>]+href="(?P<href>[^"]+)"[^>]*>.*?</a>',
        re.I | re.S,
    )
    announcements = []
    for match in pattern.finditer(text):
        title = _normalize_text(match.group("title"))
        href = html.unescape(match.group("href"))
        document_id = _url_last_number(href)
        if title and href and document_id:
            announcements.append((title, href, document_id))
    return announcements


def _iter_bop_barcelona_announcements(text: str) -> list[tuple[str, str, str, str | None]]:
    block_pattern = re.compile(
        r"<article\b[^>]*>(?P<article>.*?)</article>"
        r'|<div[^>]+class="[^"]*\bcard-body\b[^"]*"[^>]*>(?P<card>.*?)</div>\s*</div>',
        re.I | re.S,
    )
    announcements = []
    for block in block_pattern.finditer(text):
        body = block.group("article") or block.group("card") or ""
        link = re.search(
            r'<a[^>]+href="(?P<href>[^"]+)"[^>]*>(?P<title>.*?)</a>',
            body,
            re.I | re.S,
        )
        if not link:
            continue
        href = html.unescape(link.group("href"))
        title = _normalize_text(_strip_tags(link.group("title")))
        document_id = _first_value([_first_register_number(body), _url_last_number(href)])
        published_at = _first_value(
            [_first_datetime_value(body), _ddmmyyyy_to_iso(_first_date_text(body))]
        )
        if title and href and document_id:
            announcements.append((title, href, document_id, published_at))
    return announcements


def _extract_bop_bizkaia_latest_detail_url(text: str, page_url: str) -> str:
    for tag in re.finditer(r"<a\b(?P<attrs>[^>]+)>", text, re.I | re.S):
        attrs = tag.group("attrs")
        if "last-boletin-detail" not in attrs and "_IYBIWBCC_bdate" not in attrs:
            continue
        href_match = re.search(r'href="(?P<href>[^"]+)"', attrs, re.I)
        if not href_match:
            continue
        href = html.unescape(href_match.group("href"))
        if "_IYBIWBCC_bdate" in href:
            return urljoin(page_url, href)
    raise HTMLMonitorError("BOP_BIZKAIA landing page did not expose latest bulletin detail URL")


def _iter_bop_bizkaia_announcements(text: str) -> list[tuple[str, str, str]]:
    row_pattern = re.compile(
        r'<li[^>]+class="[^"]*\brow\b[^"]*"[^>]*>(?P<body>.*?)</li>',
        re.I | re.S,
    )
    announcements = []
    for row in row_pattern.finditer(text):
        body = row.group("body")
        link = re.search(
            r'<a[^>]+href="(?P<href>[^"]+\.pdf)"[^>]*class="[^"]*\bbtn_bobresult\b[^"]*"',
            body,
            re.I | re.S,
        )
        if not link:
            continue
        href = html.unescape(link.group("href"))
        document_id = _bop_bizkaia_document_id_from_url(href)
        summary = _first_id_block_text(body, "emisorResumen")
        heading = _first_heading_text(body)
        title = _join_title_parts(heading, summary)
        if title and href and document_id:
            announcements.append((title, href, document_id))
    return announcements


def _extract_bop_castellon_publication_date(text: str) -> str | None:
    match = re.search(r"Sumario\s+BOP\s+N[ºo]\s+\d+.*?(\d{2}/\d{2}/\d{4})", text, re.I | re.S)
    if match:
        return _ddmmyyyy_to_iso(match.group(1))
    return None


def _iter_bop_castellon_announcements(text: str) -> list[tuple[str, str, str, str | None]]:
    pattern = re.compile(
        r'(?P<section><span[^>]+class="titulo2"[^>]*>.*?</span>)?'
        r"(?P<prefix>.*?)"
        r'<a[^>]+href="(?P<href>[^"]*descargarAnuncio\?idAnuncio=(?P<id>\d+)[^"]*)"[^>]*>'
        r".*?</a>.*?"
        r'<span[^>]+class="titulo4"[^>]*>(?P<title>.*?)</span>',
        re.I | re.S,
    )
    announcements = []
    last_section: str | None = None
    for match in pattern.finditer(text):
        section_text = _normalize_text(_strip_tags(match.group("section") or ""))
        if section_text:
            last_section = section_text
        href = html.unescape(match.group("href"))
        document_id = _normalize_text(match.group("id"))
        title = _normalize_text(_strip_tags(match.group("title")))
        if title and href and document_id:
            announcements.append((title, href, document_id, last_section))
    return announcements


def _extract_bop_bizkaia_publication_date(page_url: str) -> str | None:
    match = re.search(r"_IYBIWBCC_bdate=(\d{8})", page_url)
    if not match:
        return None
    return _yyyymmdd_to_iso(match.group(1))


def _iter_bop_malaga_announcements(text: str) -> list[tuple[str, str, str]]:
    article_pattern = re.compile(r"<article\b[^>]*>(?P<body>.*?)</article>", re.I | re.S)
    announcements = []
    for article in article_pattern.finditer(text):
        body = article.group("body")
        link = re.search(
            r'<a[^>]+href="(?P<href>[^"]+)"[^>]*>\s*Ver\s+edicto\s+(?P<id>[^<]+)</a>',
            body,
            re.I | re.S,
        )
        if not link:
            continue
        title = _first_value(
            [
                _first_class_block_text(body, "vista_sumario"),
                _first_class_block_text(body, "vista_edicto"),
                _first_heading_text(body),
            ]
        )
        href = html.unescape(link.group("href"))
        document_id = _normalize_text(link.group("id"))
        if title and href and document_id:
            announcements.append((title, href, document_id))
    return announcements


def _extract_bop_sevilla_latest_detail_url(text: str, page_url: str) -> str:
    for tag in re.finditer(r"<a\b(?P<attrs>[^>]+)>", text, re.I | re.S):
        attrs = tag.group("attrs")
        href_match = re.search(r'href="(?P<href>[^"]+)"', attrs, re.I)
        if not href_match:
            continue
        href = html.unescape(href_match.group("href"))
        if "/publica/consulta-de-bops/buscador/BOP-" in href:
            return urljoin(page_url, href)
    raise HTMLMonitorError("BOP_SEVILLA landing page did not expose latest bulletin detail URL")


def _iter_bop_sevilla_announcements(
    text: str,
) -> list[tuple[str, str, str, str | None, str | None]]:
    item_pattern = re.compile(
        r'<li[^>]+class="[^"]*\belementoListado\b[^"]*"[^>]*>(?P<body>.*?)</li>',
        re.I | re.S,
    )
    announcements = []
    for item in item_pattern.finditer(text):
        body = item.group("body")
        link = re.search(
            r'<a[^>]+href="(?P<href>[^"]+)"[^>]*(?:title="(?P<title_attr>[^"]*)")?[^>]*>'
            r"\s*Ir\s+al\s+detalle\s*</a>",
            body,
            re.I | re.S,
        )
        if not link:
            continue
        title = _first_value(
            [
                _normalize_text(link.group("title_attr")),
                _first_heading_text(body),
            ]
        )
        href = html.unescape(link.group("href"))
        document_id = _first_bop_sevilla_document_id(body)
        published_at = _ddmmyyyy_to_iso(_first_date_text(body))
        summary = _first_class_block_text(body, "campo_1")
        if title and href and document_id:
            announcements.append((title, href, document_id, published_at, summary))
    return announcements


def _extract_bop_soria_detail_url(text: str, page_url: str) -> str:
    for tag in re.finditer(r"<a\b(?P<attrs>[^>]+)>", text, re.I | re.S):
        attrs = tag.group("attrs")
        href_match = re.search(r'href="(?P<href>[^"]+)"', attrs, re.I)
        if not href_match:
            continue
        href = html.unescape(href_match.group("href"))
        if "/mod.boloficial/mem.detalle/" in href:
            return urljoin(page_url, href)
    raise HTMLMonitorError("BOP_SORIA date page did not expose bulletin detail URL")


def _extract_bop_soria_publication_date(text: str) -> str | None:
    match = re.search(
        r"\b(\d{1,2})\s+de\s+([a-záéíóú]+)\s+de\s+(\d{4})\b",
        _strip_tags(text),
        re.I,
    )
    if not match:
        return None
    month = _SPANISH_MONTHS.get(match.group(2).lower())
    if not month:
        return None
    return date(int(match.group(3)), month, int(match.group(1))).isoformat()


def _iter_bop_soria_announcements(text: str) -> list[tuple[str, str, str, str | None]]:
    item_pattern = re.compile(r"<li>(?P<body>.*?)</li>", re.I | re.S)
    context: list[str | None] = [None, None, None]
    announcements = []
    summary_start = text.lower().find("<h3>sumario</h3>")
    for item in item_pattern.finditer(text):
        if summary_start < 0 or item.start() < summary_start:
            continue
        body = item.group("body")
        link = re.search(
            r'<a[^>]+href="(?P<href>[^"]+/mod\.documentos/mem\.descargar/[^"]+)"[^>]*>',
            body,
            re.I | re.S,
        )
        if not link:
            continue
        parts = [_normalize_soria_context(part) for part in _class_texts(body, "fec-f1")]
        non_empty_parts = [part for part in parts if part]
        if not non_empty_parts:
            continue
        for index, part in enumerate(parts[:3]):
            if part:
                context[index] = part
        title = non_empty_parts[-1]
        href = html.unescape(link.group("href"))
        document_id = _bop_soria_document_id_from_url(href)
        summary = _join_title_parts(*context)
        if title and href and document_id:
            announcements.append((title, href, document_id, summary))
    return announcements


def _normalize_soria_context(value: str | None) -> str | None:
    normalized = _normalize_text(value)
    if not normalized:
        return None
    return normalized.lstrip("- ").strip() or None


def _iter_bop_valencia_announcements(text: str) -> list[tuple[str, str, str | None]]:
    block_pattern = re.compile(
        r'<div[^>]+class="[^"]*\banuncio\b[^"]*"[^>]*>(?P<body>.*?)(?='
        r'<script[^>]+id="list:\d+:[^"]+_s"|<div[^>]+class="[^"]*\banuncio\b|</body>)',
        re.I | re.S,
    )
    announcements = []
    for block in block_pattern.finditer(text):
        body = block.group("body")
        title_match = re.search(
            r'<div[^>]+class="[^"]*\bsumario\b[^"]*"[^>]*>.*?'
            r"<a\b[^>]*>(?P<title>.*?)</a>",
            body,
            re.I | re.S,
        )
        title = _normalize_text(_strip_tags(title_match.group("title"))) if title_match else None
        document_id = _first_register_label_value(body, "registre")
        published_at = _ddmmyyyy_to_iso(_first_date_text(body))
        if title and document_id:
            announcements.append((title, document_id, published_at))
    return announcements


def _extract_bop_avila_publication_date(text: str) -> str | None:
    match = re.search(r"\[\s*(\d{2}/\d{2}/\d{4})\s*\]", _strip_tags(text))
    if not match:
        match = re.search(r"\b(\d{2}/\d{2}/\d{4})\b", _strip_tags(text))
    return _ddmmyyyy_to_iso(match.group(1)) if match else None


def _iter_bop_avila_announcements(text: str) -> list[tuple[str, str, str]]:
    link_pattern = re.compile(
        r'<a[^>]+href="(?P<href>[^"]*/bops/\d{4}/\d{2}-\d{2}-\d{4}/[^"]+\.pdf)"'
        r"[^>]*>(?P<title>.*?)</a>",
        re.I | re.S,
    )
    announcements = []
    for link in link_pattern.finditer(text):
        href = html.unescape(link.group("href"))
        document_id = _bop_avila_document_id_from_url(href)
        title = _normalize_text(_strip_tags(link.group("title")))
        if title and document_id:
            announcements.append((title, href, document_id))
    return announcements


def _extract_bop_cordoba_publication_date(page_url: str) -> str | None:
    match = re.search(r"/dia/(\d{2})-(\d{2})-(\d{4})(?:\b|$)", page_url)
    if not match:
        return None
    return date(int(match.group(3)), int(match.group(2)), int(match.group(1))).isoformat()


def _iter_bop_cordoba_announcements(text: str) -> list[tuple[str, str, str, str, str | None]]:
    pattern = re.compile(
        r'\\"li\\",\\"(?P<entry_id>\d+)\\",\{\\"className\\":\\"announcement[^"]*\\"'
        r'.*?\\"children\\":\[\\" \\",\\"(?P<title>.*?)\\"\]\}'
        r'.*?\\"href\\":\\"(?P<href>/visor-pdf/[^"]+?/(?P<document_id>BOP-A-\d{4}-\d+)\.pdf)\\"',
        re.I | re.S,
    )
    announcements = []
    for match in pattern.finditer(text):
        title = _decode_nextjs_text(match.group("title"))
        href = _decode_nextjs_text(match.group("href"))
        document_id = match.group("document_id")
        issuer = _last_bop_cordoba_issuer(text[: match.start()])
        if title and href and document_id:
            announcements.append((match.group("entry_id"), title, href, document_id, issuer))
    return announcements


def _last_bop_cordoba_issuer(text: str) -> str | None:
    pattern = re.compile(
        r'\\"className\\":\\"emisor\\".*?\\"h2\\",null,\{\\"children\\":\\"(?P<issuer>.*?)\\"\}',
        re.I | re.S,
    )
    matches = list(pattern.finditer(text))
    if not matches:
        return None
    return _decode_nextjs_text(matches[-1].group("issuer"))


def _decode_nextjs_text(value: str | None) -> str | None:
    if value is None:
        return None
    try:
        decoded = json.loads(f'"{value}"')
    except json.JSONDecodeError:
        decoded = value
    return _normalize_text(decoded)


def _extract_bop_valladolid_publication_date(text: str) -> str | None:
    match = re.search(
        r'id="bop_sumario_tit_fecha"[^>]*>\s*(\d{1,2})\s+de\s+'
        r"([a-záéíóú]+)\s+de\s+(\d{4})",
        text,
        re.I,
    )
    if not match:
        match = re.search(
            r"\b(\d{1,2})\s+de\s+([a-záéíóú]+)\s+de\s+(\d{4})\b",
            _strip_tags(text),
            re.I,
        )
    if not match:
        return None
    month = _SPANISH_MONTHS.get(match.group(2).lower())
    if not month:
        return None
    return date(int(match.group(3)), month, int(match.group(1))).isoformat()


def _iter_bop_valladolid_announcements(text: str) -> list[tuple[str, str, str, str | None]]:
    item_pattern = re.compile(
        r'<li[^>]+class="[^"]*\bun_anuncio\b[^"]*"[^>]*>(?P<body>.*?)</li>',
        re.I | re.S,
    )
    announcements = []
    for item in item_pattern.finditer(text):
        body = item.group("body")
        link = re.search(
            r'<p[^>]+class="[^"]*\bbop_res_articulo\b[^"]*"[^>]*>.*?'
            r'<a[^>]+href="(?P<href>[^"]+\.pdf)"[^>]*(?:title="(?P<title_attr>[^"]*)")?'
            r"[^>]*>(?P<title>.*?)</a>",
            body,
            re.I | re.S,
        )
        if not link:
            continue
        href = html.unescape(link.group("href"))
        document_id = _bop_valladolid_document_id_from_url(href)
        title = _first_value(
            [
                _normalize_text(link.group("title_attr")),
                _normalize_text(_strip_tags(link.group("title"))),
            ]
        )
        issuer = _first_class_block_text(body, "bop_tit_articulo")
        if title and href and document_id:
            announcements.append((title, href, document_id, issuer))
    return announcements


def _extract_bop_pontevedra_publication_date(text: str) -> str | None:
    match = re.search(
        r'<span[^>]+class="[^"]*\bfecha\b[^"]*"[^>]*>.*?'
        r"\b(\d{1,2})\s+de\s+([a-z]+)\s+de\s+(\d{4})\b",
        text,
        re.I | re.S,
    )
    if not match:
        match = re.search(
            r"\b(\d{1,2})\s+de\s+([a-z]+)\s+de\s+(\d{4})\b",
            _strip_tags(text),
            re.I,
        )
    if not match:
        return None
    month = _SPANISH_MONTHS.get(match.group(2).lower())
    if not month:
        return None
    return date(int(match.group(3)), month, int(match.group(1))).isoformat()


def _iter_bop_pontevedra_announcements(text: str) -> list[tuple[str, str, str, str | None]]:
    item_pattern = re.compile(r"<li\b[^>]*>(?P<body>.*?)</li>", re.I | re.S)
    announcements = []
    for item in item_pattern.finditer(text):
        body = item.group("body")
        link = re.search(
            r'<p[^>]+class="[^"]*\bsumario\b[^"]*"[^>]*>.*?'
            r'<a[^>]+href="(?P<href>[^"]+)"[^>]*>(?P<title>.*?)</a>',
            body,
            re.I | re.S,
        )
        if not link:
            continue
        href = html.unescape(link.group("href"))
        pdf_link = re.search(
            r'<a[^>]+class="[^"]*\bbotDescPDF\b[^"]*"[^>]+href="(?P<href>[^"]+)"',
            body,
            re.I | re.S,
        )
        document_id = _bop_pontevedra_document_id_from_url(href)
        if document_id is None and pdf_link:
            document_id = _bop_pontevedra_document_id_from_url(
                html.unescape(pdf_link.group("href"))
            )
        title = _normalize_text(_strip_tags(link.group("title")))
        issuer = _first_class_block_text(body, "pub")
        if title and href and document_id:
            announcements.append((title, href, document_id, issuer))
    return announcements


def _extract_docm_publication_date(text: str) -> str | None:
    date_text = _first_class_block_text(text, "fechaDiario")
    if not date_text:
        return None
    match = re.search(r"\b(\d{1,2})\s+de\s+([a-záéíóú]+)\s+de\s+(\d{4})\b", date_text, re.I)
    if not match:
        return None
    month = _SPANISH_MONTHS.get(match.group(2).lower())
    if not month:
        return None
    return date(int(match.group(3)), month, int(match.group(1))).isoformat()


def _extract_docm_issue_number(text: str) -> str | None:
    issue_text = _first_class_block_text(text, "numeroDiario")
    if not issue_text:
        return None
    match = re.search(r"\bN[úu]m\.?\s*(\d+)\b", issue_text, re.I)
    return match.group(1) if match else None


def _iter_docm_announcements(text: str) -> list[dict[str, Any]]:
    block_pattern = re.compile(
        r'<div\s+class\s*=\s*"disp_(?P<id>\d+)"[^>]*>(?P<body>.*?)(?='
        r'<div\s+class\s*=\s*"disp_|<div\s+class\s*=\s*"organismo|'
        r'<div\s+class\s*=\s*"categoriaDiario|</body>)',
        re.I | re.S,
    )
    announcements = []
    for block in block_pattern.finditer(text):
        body = block.group("body")
        title = _first_docm_sumario_text(body)
        nid = _first_docm_nid(body)
        href = _first_docm_html_href(body)
        page = _first_class_block_text(body, "paginaDisposicion")
        category = _last_docm_context_text(text[: block.start()], "cabeceraCategoria")
        organism = _last_docm_context_text(text[: block.start()], "tituloOrganismo")
        if title and (nid or href):
            announcements.append(
                {
                    "entry_id": f"DOCM:{nid}" if nid else f"DOCM:{block.group('id')}",
                    "document_id": nid,
                    "title": title,
                    "href": href,
                    "summary": _join_title_parts(category, organism),
                    "page": page,
                    "has_pdf": "descargarArchivo.do" in body,
                }
            )
    return announcements


def _first_docm_sumario_text(text: str) -> str | None:
    value = _first_class_block_text(text, "sumario")
    if not value:
        return None
    return re.sub(r"\s*\[NID\s+\d{4}/\d+\]\s*$", "", value).strip()


def _first_docm_nid(text: str) -> str | None:
    match = re.search(r"\[NID\s+(\d{4}/\d+)\]", _strip_tags(text), re.I)
    return match.group(1) if match else None


def _first_docm_html_href(text: str) -> str | None:
    match = re.search(
        r"abreVentanaHtml\('(?P<href>verArchivoHtml\.do\?ruta=[^']+?\.html&amp;tipo=rutaDocm)'\)",
        text,
        re.I | re.S,
    )
    if not match:
        return None
    return html.unescape(match.group("href"))


def _last_docm_context_text(text: str, class_name: str) -> str | None:
    pattern = re.compile(
        rf'<[^>]+class\s*=\s*"[^"]*\b{re.escape(class_name)}\b[^"]*"[^>]*>'
        r"(?P<body>.*?)</[^>]+>",
        re.I | re.S,
    )
    matches = list(pattern.finditer(text))
    if not matches:
        return None
    return _normalize_text(_strip_tags(matches[-1].group("body")))


def _extract_bop_malaga_publication_date(text: str) -> str | None:
    match = re.search(r"Bolet[ií]n\s+del\s+(\d{2}/\d{2}/\d{4})", text, re.I)
    if match:
        return _ddmmyyyy_to_iso(match.group(1))
    long_match = re.search(
        r"Bolet[ií]n\s+Oficial\s+de\s+la\s+Provincia\s+de\s+M[aá]laga"
        r".*?\b(\d{1,2})\s+de\s+([a-záéíóú]+)\s+de\s+(\d{4})\b",
        text,
        re.I | re.S,
    )
    if not long_match:
        return None
    month = _SPANISH_MONTHS.get(long_match.group(2).lower())
    if not month:
        return None
    return date(int(long_match.group(3)), month, int(long_match.group(1))).isoformat()


def _bop_alicante_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    if "error" in payload:
        return []
    try:
        items = payload["boletin"]["bop"][0]["registro"]
    except (KeyError, IndexError, TypeError):
        return []
    if not isinstance(items, list):
        return []
    return [item for item in items if isinstance(item, dict)]


def _first_json_value(item: dict[str, Any], key: str) -> str | None:
    value = item.get(key)
    if isinstance(value, list) and value:
        return _normalize_text(str(value[0]))
    if isinstance(value, str):
        return _normalize_text(value)
    return None


def _ddmmyyyy_to_iso(value: str | None) -> str | None:
    if not value:
        return None
    try:
        day, month, year = value.split("/")
        return date(int(year), int(month), int(day)).isoformat()
    except (TypeError, ValueError):
        return None


def _yyyymmdd_to_iso(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return date(int(value[:4]), int(value[4:6]), int(value[6:8])).isoformat()
    except (TypeError, ValueError):
        return None


def _url_last_number(value: str) -> str | None:
    match = re.search(r"(\d+)(?:\D*)$", value)
    if not match:
        return None
    return match.group(1)


def _bop_bizkaia_document_id_from_url(value: str) -> str | None:
    match = re.search(r"/([^/]+?)_(?:cas|eus)\.pdf\b", value, re.I)
    if not match:
        return None
    return match.group(1)


def _bop_avila_document_id_from_url(value: str) -> str | None:
    match = re.search(r"/([^/]+)\.pdf\b", value, re.I)
    if not match:
        return None
    document_id = match.group(1)
    if re.fullmatch(r"\d{2}-\d{2}-\d{4}", document_id):
        return None
    return document_id


def _bop_valladolid_document_id_from_url(value: str) -> str | None:
    match = re.search(r"/(BOPVA-A-\d{4}-\d+)\.pdf\b", value, re.I)
    if not match:
        return None
    return match.group(1).upper()


def _bop_pontevedra_document_id_from_url(value: str) -> str | None:
    match = re.search(r"/(\d{8,})(?:/|$|\.pdf\b)", value, re.I)
    if not match:
        return None
    return match.group(1)


def _bop_soria_document_id_from_url(value: str) -> str | None:
    match = re.search(r"fichero\.documentos_(\d+)", value, re.I)
    if not match:
        return None
    return html.unescape(match.group(1))


def _first_register_number(text: str) -> str | None:
    match = re.search(r"\bRegistre\s*:?\s*(\d{6,})\b", _strip_tags(text), re.I)
    if match:
        return match.group(1)
    return None


def _first_register_label_value(text: str, label: str) -> str | None:
    plain_text = _strip_tags(text)
    match = re.search(rf"\bN[uú]m\.?\s+{re.escape(label)}:\s*([0-9]+/[0-9]+)", plain_text, re.I)
    if match:
        return match.group(1)
    return None


def _first_bop_sevilla_document_id(text: str) -> str | None:
    match = re.search(r"\bBOP-SE-\d{4}-\d+\b", _strip_tags(text), re.I)
    if match:
        return match.group(0)
    return None


def _first_datetime_value(text: str) -> str | None:
    match = re.search(r'datetime="(\d{4}-\d{2}-\d{2})"', text, re.I)
    if match:
        return match.group(1)
    return None


def _first_date_text(text: str) -> str | None:
    match = re.search(r"\b\d{2}/\d{2}/\d{4}\b", _strip_tags(text))
    if match:
        return match.group(0)
    return None


def _first_value(values: list[str | None]) -> str | None:
    for value in values:
        if value:
            return value
    return None


def _first_class_block_text(text: str, class_name: str) -> str | None:
    match = re.search(
        rf'<[^>]+class\s*=\s*"[^"]*\b{re.escape(class_name)}\b[^"]*"[^>]*>'
        r"(?P<body>.*?)(?:<span\b|</span>|</p>|</div>)",
        text,
        re.I | re.S,
    )
    if not match:
        return None
    return _normalize_text(_strip_tags(match.group("body")))


def _class_texts(text: str, class_name: str) -> list[str]:
    pattern = re.compile(
        rf'<[^>]+class\s*=\s*"[^"]*\b{re.escape(class_name)}\b[^"]*"[^>]*>'
        r"(?P<body>.*?)</[^>]+>",
        re.I | re.S,
    )
    return [_normalize_text(_strip_tags(match.group("body"))) for match in pattern.finditer(text)]


def _first_id_block_text(text: str, id_prefix: str) -> str | None:
    match = re.search(
        rf'<[^>]+id="{re.escape(id_prefix)}[^"]*"[^>]*>(?P<body>.*?)</[^>]+>',
        text,
        re.I | re.S,
    )
    if not match:
        return None
    return _normalize_text(_strip_tags(match.group("body")))


def _first_heading_text(text: str) -> str | None:
    match = re.search(r"<h[1-6]\b[^>]*>(?P<title>.*?)</h[1-6]>", text, re.I | re.S)
    if not match:
        return None
    return _normalize_text(_strip_tags(match.group("title")))


def _join_title_parts(*parts: str | None) -> str | None:
    normalized_parts = [_normalize_text(part) for part in parts if _normalize_text(part)]
    if not normalized_parts:
        return None
    return " - ".join(normalized_parts)


def _strip_tags(value: str) -> str:
    return re.sub(r"<[^>]+>", " ", html.unescape(value))


_SPANISH_MONTHS = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "maio": 5,
    "junio": 6,
    "xuno": 6,
    "xu\u00f1o": 6,
    "julio": 7,
    "xullo": 7,
    "agosto": 8,
    "septiembre": 9,
    "setiembre": 9,
    "setembro": 9,
    "octubre": 10,
    "outubro": 10,
    "noviembre": 11,
    "novembro": 11,
    "diciembre": 12,
    "decembro": 12,
    "xaneiro": 1,
    "febreiro": 2,
}


def _has_class(value: str | None, class_name: str) -> bool:
    return bool(value and class_name in value.split())


def _normalize_text(value: str | None) -> str:
    text = html.unescape(value or "")
    text = " ".join(text.split())
    return re.sub(r"\s+([.,;:])", r"\1", text)


def _coerce_page_bytes(raw_page: bytes | str) -> bytes:
    if isinstance(raw_page, bytes):
        return raw_page
    return raw_page.encode("utf-8")
