from __future__ import annotations

import json
import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from urllib.parse import parse_qs, urlencode, urlparse

import httpx

DOGC_PORTAL_BASE_URL = "https://portaldogc.gencat.cat"
DOGC_PUBLIC_BASE_URL = "https://dogc.gencat.cat"
DOGC_DEFAULT_TIMEOUT = httpx.Timeout(connect=10.0, read=60.0, write=30.0, pool=10.0)


def validate_dogc_date(value: str) -> date:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError(f"Invalid DOGC date: {value}. Expected YYYY-MM-DD.")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"Invalid DOGC date: {value}. Expected YYYY-MM-DD.") from exc


def build_dogc_date_search_url(*, base_url: str = DOGC_PORTAL_BASE_URL) -> str:
    return f"{base_url.rstrip('/')}/eadop-rest/api/dogc/searchDOGC"


def build_dogc_document_metadata_url(*, base_url: str = DOGC_PORTAL_BASE_URL) -> str:
    return f"{base_url.rstrip('/')}/eadop-rest/api/dogc/documentDOGC"


def build_dogc_calendar_url(*, base_url: str = DOGC_PORTAL_BASE_URL) -> str:
    return f"{base_url.rstrip('/')}/eadop-rest/api/dogc/calendarDOGC"


def build_dogc_document_html_url(
    document_id: int | str,
    *,
    lang: str = "ca",
    base_url: str = DOGC_PUBLIC_BASE_URL,
) -> str:
    if not str(document_id).strip():
        raise ValueError("DOGC document ID is required for document HTML URL.")
    return (
        f"{base_url.rstrip('/')}/{lang}/document-del-dogc/?{urlencode({'documentId': document_id})}"
    )


def build_dogc_date_search_payload(target_date: str, *, lang: str = "ca") -> dict:
    parsed = validate_dogc_date(target_date)
    dogc_date = parsed.strftime("%d/%m/%Y")
    return {
        "typeSearch": "1",
        "value": "",
        "title": False,
        "current": False,
        "range": [],
        "issuingAuthority": [],
        "publicationDateInitial": dogc_date,
        "publicationDateFinal": dogc_date,
        "dispositionDateInitial": "",
        "dispositionDateFinal": "",
        "sectionDOGC": [],
        "thematicDescriptor": [],
        "organizationDescriptor": [],
        "geographicDescriptor": [],
        "aranese": False,
        "expandSearchFullText": False,
        "noCurrent": False,
        "orderBy": "6",
        "page": "1",
        "numResultsByPage": "100",
        "advanced": False,
        "language": lang,
    }


@dataclass(frozen=True)
class DOGCHTTPResponse:
    content: bytes
    final_url: str
    status_code: int


class DOGCClient:
    def __init__(
        self,
        *,
        base_url: str = DOGC_PORTAL_BASE_URL,
        timeout: httpx.Timeout = DOGC_DEFAULT_TIMEOUT,
        client_factory: Callable[[], httpx.Client] | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._client_factory = client_factory
        self.last_http_status: int | None = None

    def fetch_date(self, target_date: str) -> DOGCHTTPResponse:
        parsed_date = validate_dogc_date(target_date)
        issue_identifier = self._fetch_issue_identifier(parsed_date)
        url = build_dogc_date_search_url(base_url=self.base_url)
        payload = build_dogc_date_search_payload(target_date)
        with self._build_client() as client:
            response = client.post(url, json=payload)
            self.last_http_status = response.status_code
            response.raise_for_status()
            content = _inject_issue_identifier(response.content, issue_identifier)
            return DOGCHTTPResponse(
                content=content,
                final_url=str(response.request.url),
                status_code=response.status_code,
            )

    def fetch_document_metadata(self, document_id: int | str) -> DOGCHTTPResponse:
        url = build_dogc_document_metadata_url(base_url=self.base_url)
        with self._build_client() as client:
            response = client.post(
                url,
                data={"documentId": str(document_id), "language": "ca"},
            )
            self.last_http_status = response.status_code
            response.raise_for_status()
            return DOGCHTTPResponse(
                content=response.content,
                final_url=str(response.request.url),
                status_code=response.status_code,
            )

    def _build_client(self) -> httpx.Client:
        if self._client_factory is not None:
            return self._client_factory()
        return httpx.Client(timeout=self._timeout, follow_redirects=True)

    def _fetch_issue_identifier(self, target_date: date) -> str | None:
        url = build_dogc_calendar_url(base_url=self.base_url)
        with self._build_client() as client:
            response = client.post(
                url,
                data={
                    "month": str(target_date.month),
                    "year": str(target_date.year),
                    "language": "ca",
                },
            )
            self.last_http_status = response.status_code
            response.raise_for_status()
            data = response.json()
        wanted = target_date.strftime("%d/%m/%Y")
        for item in data.get("calendar") or []:
            if item.get("date") != wanted or not item.get("hasDOGC"):
                continue
            values = parse_qs(urlparse(item.get("linkDOGC") or "").query).get("numDOGC")
            return values[0] if values else None
        return None


def _inject_issue_identifier(content: bytes, issue_identifier: str | None) -> bytes:
    if not issue_identifier:
        return content
    data = json.loads(content.decode("utf-8-sig"))
    data["issue_identifier"] = issue_identifier
    return json.dumps(data, ensure_ascii=False, sort_keys=True).encode("utf-8")
