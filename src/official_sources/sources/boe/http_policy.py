from __future__ import annotations

import os
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime

import httpx

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


@dataclass(frozen=True)
class BOERequestAudit:
    retry_count: int = 0
    throttle_triggered: bool = False
    last_http_status: int | None = None


@dataclass(frozen=True)
class BOEHTTPResult:
    content: bytes
    status_code: int
    headers: httpx.Headers
    request: httpx.Request
    audit: BOERequestAudit

    def raise_for_status(self) -> None:
        if 200 <= self.status_code < 300:
            return
        response = httpx.Response(
            self.status_code,
            content=self.content,
            headers=self.headers,
            request=self.request,
        )
        response.raise_for_status()


@dataclass
class BOERequestPolicy:
    requests_per_second: float = 1
    max_retries: int = 5
    backoff_base_seconds: float = 1
    backoff_max_seconds: float = 30
    jitter_seconds: float = 0.25
    _last_request_at: float | None = None

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> BOERequestPolicy:
        environ = environ or os.environ
        return cls(
            requests_per_second=_float_env(environ, "OFFICIAL_SOURCES_BOE_REQUESTS_PER_SECOND", 1),
            max_retries=_int_env(environ, "OFFICIAL_SOURCES_BOE_MAX_RETRIES", 5),
            backoff_base_seconds=_float_env(
                environ, "OFFICIAL_SOURCES_BOE_BACKOFF_BASE_SECONDS", 1
            ),
            backoff_max_seconds=_float_env(environ, "OFFICIAL_SOURCES_BOE_BACKOFF_MAX_SECONDS", 30),
            jitter_seconds=_float_env(environ, "OFFICIAL_SOURCES_BOE_JITTER_SECONDS", 0.25),
        )

    def get(
        self,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        client: httpx.Client,
        sleeper: Callable[[float], None] = time.sleep,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> BOEHTTPResult:
        retry_count = 0
        throttle_triggered = self._apply_rate_limit(sleeper=sleeper, monotonic=monotonic)
        while True:
            response = client.get(url, headers=headers)
            retries_exhausted = retry_count >= self.max_retries
            if response.status_code not in RETRYABLE_STATUS_CODES or retries_exhausted:
                return BOEHTTPResult(
                    content=response.content,
                    status_code=response.status_code,
                    headers=response.headers,
                    request=response.request,
                    audit=BOERequestAudit(
                        retry_count=retry_count,
                        throttle_triggered=throttle_triggered,
                        last_http_status=response.status_code,
                    ),
                )
            retry_count += 1
            throttle_triggered = True
            sleeper(self._retry_delay(response, retry_count))

    def _apply_rate_limit(
        self,
        *,
        sleeper: Callable[[float], None],
        monotonic: Callable[[], float],
    ) -> bool:
        if self.requests_per_second <= 0:
            self._last_request_at = monotonic()
            return False
        now = monotonic()
        min_interval = 1 / self.requests_per_second
        if self._last_request_at is None:
            self._last_request_at = now
            return False
        elapsed = now - self._last_request_at
        if elapsed >= min_interval:
            self._last_request_at = now
            return False
        delay = min_interval - elapsed
        sleeper(delay)
        self._last_request_at = monotonic()
        return True

    def _retry_delay(self, response: httpx.Response, retry_count: int) -> float:
        retry_after = _parse_retry_after(response.headers.get("Retry-After"))
        if retry_after is not None:
            return min(retry_after + self.jitter_seconds, self.backoff_max_seconds)
        backoff = self.backoff_base_seconds * (2 ** (retry_count - 1))
        return min(backoff + self.jitter_seconds, self.backoff_max_seconds)


def _parse_retry_after(value: str | None) -> float | None:
    if not value:
        return None
    value = value.strip()
    if value.isdigit():
        return float(value)
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    delay = (parsed - datetime.now(UTC)).total_seconds()
    return max(delay, 0)


def _int_env(environ: Mapping[str, str], name: str, default: int) -> int:
    raw = environ.get(name)
    return default if raw is None else int(raw)


def _float_env(environ: Mapping[str, str], name: str, default: float) -> float:
    raw = environ.get(name)
    return default if raw is None else float(raw)
