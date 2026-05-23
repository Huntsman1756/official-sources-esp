from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date

import httpx

BORM_INDEX_XML_URL = "https://transparencia.carm.es/rest-services/services/restFile/BORMIndice.xml"
BORM_DEFAULT_TIMEOUT = httpx.Timeout(connect=10.0, read=60.0, write=30.0, pool=10.0)


def validate_borm_date(value: str) -> date:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError(f"Invalid BORM date: {value}. Expected YYYY-MM-DD.")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"Invalid BORM date: {value}. Expected YYYY-MM-DD.") from exc


def build_borm_index_xml_url() -> str:
    return BORM_INDEX_XML_URL


@dataclass(frozen=True)
class BORMHTTPResponse:
    content: bytes
    final_url: str
    status_code: int


class BORMClient:
    def __init__(
        self,
        *,
        index_xml_url: str = BORM_INDEX_XML_URL,
        timeout: httpx.Timeout = BORM_DEFAULT_TIMEOUT,
        client_factory: Callable[[], httpx.Client] | None = None,
    ) -> None:
        self.index_xml_url = index_xml_url
        self._timeout = timeout
        self._client_factory = client_factory
        self.last_http_status: int | None = None

    def fetch_date(self, target_date: str) -> BORMHTTPResponse:
        validate_borm_date(target_date)
        with self._build_client() as client:
            response = client.get(self.index_xml_url, headers={"Accept": "application/xml"})
            self.last_http_status = response.status_code
            response.raise_for_status()
            return BORMHTTPResponse(
                content=response.content,
                final_url=str(response.request.url),
                status_code=response.status_code,
            )

    def _build_client(self) -> httpx.Client:
        if self._client_factory is not None:
            return self._client_factory()
        return httpx.Client(timeout=self._timeout, follow_redirects=True)
