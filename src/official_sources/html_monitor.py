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
    raw_page = _coerce_page_bytes((fetcher or fetch_html)(page_url))
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
        summary = " - ".join(
            value
            for value in [
                _first_json_value(item, "gndenom"),
                _first_json_value(item, "ampliacion"),
            ]
            if value
        ) or None
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


def write_html_jsonl(records: list[dict[str, Any]], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = "".join(
        f"{json.dumps(record, ensure_ascii=False, sort_keys=True)}\n" for record in records
    )
    output_path.write_text(payload, encoding="utf-8")
    return output_path


def fetch_html(url: str) -> bytes:
    with httpx.Client(follow_redirects=True, timeout=30.0) as client:
        response = client.get(
            url,
            headers={"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"},
        )
        response.raise_for_status()
        return response.content


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
    raise HTMLMonitorError(
        "html monitor currently supports BOP_A_CORUNA, BOP_ALBACETE, and BOP_ALICANTE only"
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


def _url_last_number(value: str) -> str | None:
    match = re.search(r"(\d+)(?:\D*)$", value)
    if not match:
        return None
    return match.group(1)


def _has_class(value: str | None, class_name: str) -> bool:
    return bool(value and class_name in value.split())


def _normalize_text(value: str | None) -> str:
    text = html.unescape(value or "")
    return " ".join(text.split())


def _coerce_page_bytes(raw_page: bytes | str) -> bytes:
    if isinstance(raw_page, bytes):
        return raw_page
    return raw_page.encode("utf-8")
