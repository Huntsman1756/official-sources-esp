from __future__ import annotations

import os
import time
from collections.abc import Callable, Mapping
from datetime import date
from urllib.parse import quote, urlencode

import httpx

from official_sources.sources.boe.http_policy import BOERequestAudit, BOERequestPolicy

BOJA_API_BASE_URL = "https://datos.juntadeandalucia.es/api/v0/boja"
BOJA_SEARCH_ENDPOINT = "/get/search_pagination"
BOJA_DEFAULT_PAGE_SIZE = 200
BOJA_DEFAULT_MAX_PAGES_PER_DATE = 20


def boja_max_pages_from_env(environ: Mapping[str, str] | None = None) -> int:
    environ = environ or os.environ
    raw = environ.get("OFFICIAL_SOURCES_BOJA_MAX_PAGES_PER_DATE")
    if raw is None:
        return BOJA_DEFAULT_MAX_PAGES_PER_DATE
    value = int(raw)
    if value <= 0:
        raise ValueError("OFFICIAL_SOURCES_BOJA_MAX_PAGES_PER_DATE must be greater than zero")
    return value


def validate_boja_date(value: str) -> date:
    if len(value) != 10 or value[4] != "-" or value[7] != "-":
        raise ValueError("BOJA dates must use YYYY-MM-DD format")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("BOJA dates must use YYYY-MM-DD format") from exc


def build_boja_search_url(
    target_date: str,
    *,
    base_url: str = BOJA_API_BASE_URL,
    size: int = BOJA_DEFAULT_PAGE_SIZE,
    page: int = 0,
) -> str:
    validate_boja_date(target_date)
    query = urlencode(
        {
            "order_by": "date",
            "mode": "DESC",
            "size": size,
            "page": page,
            "date_from": target_date,
            "date_to": target_date,
        }
    )
    return f"{base_url.rstrip('/')}{BOJA_SEARCH_ENDPOINT}?{query}"


def build_boja_detail_url(
    official_id: str,
    *,
    base_url: str = BOJA_API_BASE_URL,
) -> str:
    official_id = official_id.strip()
    if not official_id:
        raise ValueError("BOJA official identifier is required")
    return f"{base_url.rstrip('/')}/{quote(official_id, safe='')}"


class BOJAClient:
    def __init__(
        self,
        base_url: str = BOJA_API_BASE_URL,
        timeout: float = 30.0,
        *,
        request_policy: BOERequestPolicy | None = None,
        sleeper: Callable[[float], None] | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.request_policy = request_policy or BOERequestPolicy.from_env()
        self.sleeper = sleeper
        self.client = client
        self.last_request_audit = BOERequestAudit()

    def fetch_date_page(
        self,
        target_date: str,
        *,
        page: int = 0,
        size: int = BOJA_DEFAULT_PAGE_SIZE,
    ) -> bytes:
        url = build_boja_search_url(target_date, base_url=self.base_url, page=page, size=size)
        if self.client is not None:
            result = self._get(url, self.client)
        else:
            with httpx.Client(follow_redirects=False, timeout=self.timeout) as client:
                result = self._get(url, client)
        self.last_request_audit = result.audit
        result.raise_for_status()
        return result.content

    def fetch_date(self, target_date: str) -> bytes:
        return self.fetch_date_page(target_date, page=0, size=BOJA_DEFAULT_PAGE_SIZE)

    def fetch_document_detail(self, official_id: str) -> bytes:
        url = build_boja_detail_url(official_id, base_url=self.base_url)
        if self.client is not None:
            result = self._get(url, self.client)
        else:
            with httpx.Client(follow_redirects=False, timeout=self.timeout) as client:
                result = self._get(url, client)
        self.last_request_audit = result.audit
        result.raise_for_status()
        return result.content

    def _get(self, url: str, client: httpx.Client):
        return self.request_policy.get(
            url,
            headers={"Accept": "application/json"},
            client=client,
            sleeper=self.sleeper or time.sleep,
        )
