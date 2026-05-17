from __future__ import annotations

import time
from collections.abc import Callable
from datetime import date

import httpx

from official_sources.sources.boe.http_policy import BOERequestAudit, BOERequestPolicy

BOE_SUMMARY_AVAILABLE_FROM = date(1960, 9, 1)


def validate_boe_date(value: str) -> date:
    if len(value) != 10 or value[4] != "-" or value[7] != "-":
        raise ValueError("BOE dates must use YYYY-MM-DD format")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("BOE dates must use YYYY-MM-DD format") from exc
    if parsed < BOE_SUMMARY_AVAILABLE_FROM:
        raise ValueError("BOE summary data is available from 1960-09-01")
    return parsed


class BOEClient:
    def __init__(
        self,
        base_url: str = "https://www.boe.es",
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

    def fetch_summary(self, target_date: str) -> bytes:
        parsed = validate_boe_date(target_date)
        date_token = parsed.strftime("%Y%m%d")
        url = f"{self.base_url}/datosabiertos/api/boe/sumario/{date_token}"

        if self.client is not None:
            result = self._get(url, self.client)
        else:
            with httpx.Client(follow_redirects=False, timeout=self.timeout) as client:
                result = self._get(url, client)
        self.last_request_audit = result.audit
        if result.status_code == 404:
            raise BOESummaryNotFoundError(target_date, result.audit)
        result.raise_for_status()
        return result.content

    def _get(self, url: str, client: httpx.Client):
        return self.request_policy.get(
            url,
            headers={"Accept": "application/json"},
            client=client,
            sleeper=self.sleeper or time.sleep,
        )


class BOESummaryNotFoundError(Exception):
    def __init__(self, target_date: str, audit: BOERequestAudit | None = None) -> None:
        self.target_date = target_date
        self.retry_count = audit.retry_count if audit else 0
        self.throttle_triggered = audit.throttle_triggered if audit else False
        self.last_http_status = audit.last_http_status if audit else 404
        super().__init__(f"BOE summary not found for date {target_date}")
