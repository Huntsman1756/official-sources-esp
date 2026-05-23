from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from urllib.parse import urlencode

import httpx

BOCYL_API_BASE_URL = "https://jcyl.opendatasoft.com/api/explore/v2.1/catalog/datasets/bocyl"
BOCYL_DEFAULT_TIMEOUT = httpx.Timeout(connect=10.0, read=60.0, write=30.0, pool=10.0)


def validate_bocyl_date(value: str) -> date:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError(f"Invalid BOCYL date: {value}. Expected YYYY-MM-DD.")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"Invalid BOCYL date: {value}. Expected YYYY-MM-DD.") from exc


def build_bocyl_date_api_url(
    target_date: str,
    *,
    limit: int = 100,
    base_url: str = BOCYL_API_BASE_URL,
) -> str:
    validate_bocyl_date(target_date)
    query = urlencode(
        {
            "limit": limit,
            "where": f"fecha_publicacion=date'{target_date}'",
        }
    )
    return f"{base_url.rstrip('/')}/records?{query}"


@dataclass(frozen=True)
class BOCYLHTTPResponse:
    content: bytes
    final_url: str
    status_code: int


class BOCYLClient:
    def __init__(
        self,
        *,
        base_url: str = BOCYL_API_BASE_URL,
        timeout: httpx.Timeout = BOCYL_DEFAULT_TIMEOUT,
        client_factory: Callable[[], httpx.Client] | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._client_factory = client_factory
        self.last_http_status: int | None = None

    def fetch_date(self, target_date: str) -> BOCYLHTTPResponse:
        url = build_bocyl_date_api_url(target_date, base_url=self.base_url)
        with self._build_client() as client:
            response = client.get(url, headers={"Accept": "application/json"})
            self.last_http_status = response.status_code
            response.raise_for_status()
            return BOCYLHTTPResponse(
                content=response.content,
                final_url=str(response.request.url),
                status_code=response.status_code,
            )

    def _build_client(self) -> httpx.Client:
        if self._client_factory is not None:
            return self._client_factory()
        return httpx.Client(timeout=self._timeout, follow_redirects=True)
