from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass

import httpx

from official_sources.sources.boe.http_policy import BOERequestAudit, BOERequestPolicy

PLACSP_BASE_URL = "https://contrataciondelsectorpublico.gob.es"
PLACSP_DEFAULT_TIMEOUT = httpx.Timeout(connect=10.0, read=90.0, write=30.0, pool=10.0)
PLACSP_DEFAULT_LIMIT = 50
PLACSP_HARD_MAX_LIMIT = 500

PLACSP_FEEDS = {
    "profiles": {
        "syndication_id": "643",
        "name": "licitacionesPerfilesContratanteCompleto3",
    },
    "aggregated": {
        "syndication_id": "1044",
        "name": "PlataformasAgregadasSinMenores",
    },
    "minor_contracts": {
        "syndication_id": "1143",
        "name": "contratosMenoresPerfilesContratantes",
    },
    "self_means": {
        "syndication_id": "1383",
        "name": "EMP_SectorPublico",
    },
    "market_preliminary": {
        "syndication_id": "1403",
        "name": "CPM_SectorPublico",
    },
}


@dataclass(frozen=True)
class PLACSPHTTPResponse:
    content: bytes
    final_url: str
    status_code: int
    audit: BOERequestAudit


class PLACSPClient:
    def __init__(
        self,
        *,
        timeout: httpx.Timeout = PLACSP_DEFAULT_TIMEOUT,
        request_policy: BOERequestPolicy | None = None,
        client_factory: Callable[[], httpx.Client] | None = None,
    ) -> None:
        self._timeout = timeout
        self._request_policy = request_policy or BOERequestPolicy(max_retries=3)
        self._client_factory = client_factory
        self.last_audit = BOERequestAudit()

    def fetch_feed(self, feed_type: str) -> PLACSPHTTPResponse:
        return self._get(
            build_placsp_feed_url(feed_type),
            accept="application/atom+xml, application/xml, text/xml",
        )

    def fetch_dataset_zip(self, feed_type: str, *, period: str) -> PLACSPHTTPResponse:
        return self._get(
            build_placsp_dataset_url(feed_type, period=period),
            accept="application/zip",
        )

    def _get(self, url: str, *, accept: str) -> PLACSPHTTPResponse:
        with self._build_client() as client:
            response = self._request_policy.get(
                url,
                headers={"Accept": accept, "User-Agent": "official-sources/PLACSP"},
                client=client,
            )
            self.last_audit = response.audit
            response.raise_for_status()
            return PLACSPHTTPResponse(
                content=response.content,
                final_url=str(response.request.url),
                status_code=response.status_code,
                audit=response.audit,
            )

    def _build_client(self) -> httpx.Client:
        if self._client_factory is not None:
            return self._client_factory()
        return httpx.Client(timeout=self._timeout, follow_redirects=True)


def validate_placsp_feed_type(value: str) -> str:
    cleaned = str(value).strip().lower()
    if cleaned not in PLACSP_FEEDS:
        allowed = ", ".join(sorted(PLACSP_FEEDS))
        raise ValueError(f"Invalid PLACSP feed type: {value}. Allowed feed types: {allowed}.")
    return cleaned


def validate_placsp_period(value: str) -> str:
    cleaned = str(value).strip()
    if not re.fullmatch(r"\d{6}", cleaned):
        raise ValueError(f"Invalid PLACSP period: {value}. Expected YYYYMM.")
    month = int(cleaned[4:6])
    if month < 1 or month > 12:
        raise ValueError(f"Invalid PLACSP period month: {value}.")
    return cleaned


def validate_placsp_limit(value: int) -> int:
    if value < 1:
        raise ValueError("limit must be at least 1.")
    if value > PLACSP_HARD_MAX_LIMIT:
        raise ValueError(f"limit must be <= {PLACSP_HARD_MAX_LIMIT}.")
    return value


def build_placsp_feed_url(
    feed_type: str,
    *,
    base_url: str = PLACSP_BASE_URL,
) -> str:
    feed = PLACSP_FEEDS[validate_placsp_feed_type(feed_type)]
    return (
        f"{base_url.rstrip('/')}/sindicacion/sindicacion_{feed['syndication_id']}/"
        f"{feed['name']}.atom"
    )


def build_placsp_dataset_url(
    feed_type: str,
    *,
    period: str,
    base_url: str = PLACSP_BASE_URL,
) -> str:
    feed = PLACSP_FEEDS[validate_placsp_feed_type(feed_type)]
    period = validate_placsp_period(period)
    return (
        f"{base_url.rstrip('/')}/sindicacion/sindicacion_{feed['syndication_id']}/"
        f"{feed['name']}_{period}.zip"
    )
