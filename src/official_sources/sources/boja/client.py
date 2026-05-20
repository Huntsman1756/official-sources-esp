from __future__ import annotations

import time
from collections.abc import Callable
from datetime import date
from urllib.parse import urlencode

import httpx

from official_sources.sources.boe.http_policy import BOERequestAudit, BOERequestPolicy

BOJA_API_BASE_URL = "https://datos.juntadeandalucia.es/api/v0/boja"
BOJA_SEARCH_ENDPOINT = "/get/search_pagination"
BOJA_DEFAULT_PAGE_SIZE = 200


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

    def fetch_date(self, target_date: str) -> bytes:
        url = build_boja_search_url(target_date, base_url=self.base_url)
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
