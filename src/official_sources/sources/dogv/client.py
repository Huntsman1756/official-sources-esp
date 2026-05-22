from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from urllib.parse import quote, urlencode

import httpx

DOGV_BASE_URL = "https://dogv.gva.es"
DOGV_PORTAL_BASE_URL = f"{DOGV_BASE_URL}/dogv-portal"
DOGV_DEFAULT_TIMEOUT = httpx.Timeout(connect=10.0, read=60.0, write=30.0, pool=10.0)


def validate_dogv_date(value: str) -> date:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError(f"Invalid DOGV date: {value}. Expected YYYY-MM-DD.")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"Invalid DOGV date: {value}. Expected YYYY-MM-DD.") from exc


def build_dogv_date_url(
    target_date: str,
    *,
    lang: str = "es",
    base_url: str = DOGV_PORTAL_BASE_URL,
) -> str:
    validate_dogv_date(target_date)
    return f"{base_url}/dogv?{urlencode({'date': target_date, 'lang': lang})}"


def build_dogv_calendar_url(
    start_date: str,
    end_date: str,
    *,
    base_url: str = DOGV_PORTAL_BASE_URL,
) -> str:
    validate_dogv_date(start_date)
    validate_dogv_date(end_date)
    return f"{base_url}/dogv/calendar?{urlencode({'startDate': start_date, 'endDate': end_date})}"


def build_dogv_document_html_url(
    codigo_insercion: str,
    *,
    lang: str = "es",
    base_url: str = DOGV_BASE_URL,
) -> str:
    if not codigo_insercion:
        raise ValueError("DOGV insertion code is required for document HTML URL.")
    return f"{base_url}/{lang}/resultat-dogv?signatura={quote(codigo_insercion, safe='/')}"


def build_dogv_document_metadata_url(
    document_id: int | str,
    *,
    lang: str = "es",
    base_url: str = DOGV_PORTAL_BASE_URL,
) -> str:
    return f"{base_url}/disposicion/metadata/{document_id}?{urlencode({'lang': lang})}"


def build_dogv_document_xml_url(
    document_id: int | str,
    *,
    lang: str = "es",
    base_url: str = DOGV_PORTAL_BASE_URL,
) -> str:
    return f"{base_url}/export/disposicion/xml/dinamico/{document_id}?{urlencode({'lang': lang})}"


def build_dogv_document_pdf_url(
    url_pdf: str,
    *,
    base_url: str = DOGV_BASE_URL,
) -> str:
    if not url_pdf:
        raise ValueError("DOGV PDF URL path is required.")
    if url_pdf.startswith("http://") or url_pdf.startswith("https://"):
        return url_pdf
    return f"{base_url}/datos{url_pdf if url_pdf.startswith('/') else '/' + url_pdf}"


@dataclass(frozen=True)
class DOGVHTTPResponse:
    content: bytes
    final_url: str
    status_code: int


class DOGVClient:
    def __init__(
        self,
        *,
        base_url: str = DOGV_PORTAL_BASE_URL,
        timeout: httpx.Timeout = DOGV_DEFAULT_TIMEOUT,
        client_factory: Callable[[], httpx.Client] | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._client_factory = client_factory
        self.last_http_status: int | None = None

    def fetch_date(self, target_date: str) -> DOGVHTTPResponse:
        url = build_dogv_date_url(target_date, base_url=self.base_url)
        with self._build_client() as client:
            response = client.get(url, headers={"Accept": "application/json"})
            self.last_http_status = response.status_code
            response.raise_for_status()
            return DOGVHTTPResponse(
                content=response.content,
                final_url=str(response.request.url),
                status_code=response.status_code,
            )

    def _build_client(self) -> httpx.Client:
        if self._client_factory is not None:
            return self._client_factory()
        return httpx.Client(timeout=self._timeout, follow_redirects=True)
