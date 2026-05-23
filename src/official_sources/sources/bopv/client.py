from __future__ import annotations

import re
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date

import httpx

from official_sources.sources.boe.http_policy import BOERequestAudit, BOERequestPolicy

BOPV_BASE_URL = "https://www.euskadi.eus"
BOPV_DEFAULT_TIMEOUT = httpx.Timeout(connect=10.0, read=60.0, write=30.0, pool=10.0)


def validate_bopv_date(value: str) -> date:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError(f"Invalid BOPV date: {value}. Expected YYYY-MM-DD.")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"Invalid BOPV date: {value}. Expected YYYY-MM-DD.") from exc
    return parsed


def build_bopv_calendar_url(target_date: str, *, base_url: str = BOPV_BASE_URL) -> str:
    parsed = validate_bopv_date(target_date)
    return f"{base_url}/bopv2/datos/{parsed:%m%Y}.shtml"


def build_bopv_issue_html_url(
    target_date: str,
    issue_stem: str,
    *,
    base_url: str = BOPV_BASE_URL,
) -> str:
    parsed = validate_bopv_date(target_date)
    normalized_stem = _normalize_issue_stem(issue_stem)
    return f"{base_url}/bopv2/datos/{parsed:%Y}/{parsed:%m}/{normalized_stem}.shtml"


def build_bopv_issue_xml_url(
    target_date: str,
    issue_stem: str,
    *,
    base_url: str = BOPV_BASE_URL,
) -> str:
    parsed = validate_bopv_date(target_date)
    normalized_stem = _normalize_issue_stem(issue_stem)
    return f"{base_url}/bopv2/datos/{parsed:%Y}/{parsed:%m}/{normalized_stem}.xml"


def build_bopv_document_html_url(
    target_date: str,
    document_stem: str,
    *,
    base_url: str = BOPV_BASE_URL,
) -> str:
    return _build_bopv_document_url(target_date, document_stem, "shtml", base_url=base_url)


def build_bopv_document_xml_url(
    target_date: str,
    document_stem: str,
    *,
    base_url: str = BOPV_BASE_URL,
) -> str:
    return _build_bopv_document_url(target_date, document_stem, "xml", base_url=base_url)


def build_bopv_document_pdf_url(
    target_date: str,
    document_stem: str,
    *,
    base_url: str = BOPV_BASE_URL,
) -> str:
    return _build_bopv_document_url(target_date, document_stem, "pdf", base_url=base_url)


def build_bopv_document_epub_url(
    target_date: str,
    document_stem: str,
    *,
    base_url: str = BOPV_BASE_URL,
) -> str:
    return _build_bopv_document_url(target_date, document_stem, "epub", base_url=base_url)


def bopv_issue_identifier(target_date: str, issue_stem: str) -> str:
    parsed = validate_bopv_date(target_date)
    match = re.fullmatch(r"s\d{2}_(\d{4})", _normalize_issue_stem(issue_stem))
    if not match:
        raise ValueError(f"Invalid BOPV issue stem: {issue_stem}")
    return f"BOPV-{parsed:%Y}-{match.group(1)}"


def bopv_document_identifier(target_date: str, document_stem: str) -> str:
    parsed = validate_bopv_date(target_date)
    normalized_stem = _normalize_document_stem(document_stem)
    return f"BOPV-{parsed:%Y}-{parsed:%m}-{normalized_stem}"


def bopv_document_stem(target_date: str, order_number: str | int) -> str:
    parsed = validate_bopv_date(target_date)
    order_text = str(order_number).strip()
    if not order_text.isdigit():
        raise ValueError(f"Invalid BOPV order number: {order_number}")
    return f"{parsed:%y}{int(order_text):05d}a"


def _build_bopv_document_url(
    target_date: str,
    document_stem: str,
    extension: str,
    *,
    base_url: str,
) -> str:
    parsed = validate_bopv_date(target_date)
    normalized_stem = _normalize_document_stem(document_stem)
    return f"{base_url}/bopv2/datos/{parsed:%Y}/{parsed:%m}/{normalized_stem}.{extension}"


def _normalize_issue_stem(issue_stem: str) -> str:
    stem = issue_stem.strip()
    if stem.endswith(".shtml") or stem.endswith(".xml") or stem.endswith(".pdf"):
        stem = stem.rsplit(".", 1)[0]
    if not re.fullmatch(r"s\d{2}_\d{4}", stem):
        raise ValueError(f"Invalid BOPV issue stem: {issue_stem}")
    return stem


def _normalize_document_stem(document_stem: str) -> str:
    stem = document_stem.strip()
    if "." in stem:
        stem = stem.rsplit(".", 1)[0]
    if not re.fullmatch(r"\d{7}a", stem):
        raise ValueError(f"Invalid BOPV document stem: {document_stem}")
    return stem


@dataclass(frozen=True)
class BOPVHTTPResponse:
    content: bytes
    final_url: str
    audit: BOERequestAudit


class BOPVClient:
    def __init__(
        self,
        *,
        base_url: str = BOPV_BASE_URL,
        request_policy: BOERequestPolicy | None = None,
        sleeper: Callable[[float], None] | None = None,
        timeout: httpx.Timeout = BOPV_DEFAULT_TIMEOUT,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._policy = request_policy or BOERequestPolicy.from_env()
        self._sleeper = sleeper
        self._timeout = timeout
        self.last_request_audit = BOERequestAudit()

    def fetch_calendar(self, target_date: str) -> BOPVHTTPResponse:
        result = self._get(
            build_bopv_calendar_url(target_date, base_url=self.base_url),
            accept="text/html,application/xhtml+xml",
        )
        self.last_request_audit = result.audit
        result.raise_for_status()
        return BOPVHTTPResponse(
            content=result.content,
            final_url=str(result.request.url),
            audit=result.audit,
        )

    def fetch_issue_xml(self, issue_xml_url: str) -> BOPVHTTPResponse:
        result = self._get(issue_xml_url, accept="application/xml,text/xml")
        self.last_request_audit = result.audit
        result.raise_for_status()
        return BOPVHTTPResponse(
            content=result.content,
            final_url=str(result.request.url),
            audit=result.audit,
        )

    def _get(self, url: str, *, accept: str):
        with httpx.Client(timeout=self._timeout, follow_redirects=True) as client:
            return self._policy.get(
                url,
                headers={"Accept": accept},
                client=client,
                sleeper=self._sleeper or time.sleep,
            )
