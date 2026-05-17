from __future__ import annotations

import httpx

from official_sources.sources.boe.http_policy import BOERequestPolicy


def _client_with_statuses(statuses: list[int], *, retry_after: str | None = None) -> httpx.Client:
    def handler(_request: httpx.Request) -> httpx.Response:
        status = statuses.pop(0)
        headers = {"Retry-After": retry_after} if retry_after else {}
        return httpx.Response(status, content=b"ok", headers=headers)

    return httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=False, timeout=5.0)


def test_default_boe_request_policy_is_conservative():
    policy = BOERequestPolicy.from_env({})

    assert policy.requests_per_second == 1
    assert policy.max_retries == 5
    assert policy.backoff_base_seconds == 1
    assert policy.backoff_max_seconds == 30
    assert policy.jitter_seconds == 0.25


def test_429_triggers_retry_backoff_and_records_audit():
    sleeps: list[float] = []
    client = _client_with_statuses([429, 200])
    policy = BOERequestPolicy(max_retries=5, jitter_seconds=0)

    result = policy.get("https://www.boe.es/test", client=client, sleeper=sleeps.append)

    assert result.status_code == 200
    assert result.audit.retry_count == 1
    assert result.audit.throttle_triggered is True
    assert result.audit.last_http_status == 200
    assert sleeps == [1]


def test_503_triggers_retry_backoff_and_records_audit():
    sleeps: list[float] = []
    client = _client_with_statuses([503, 200])
    policy = BOERequestPolicy(max_retries=5, jitter_seconds=0)

    result = policy.get("https://www.boe.es/test", client=client, sleeper=sleeps.append)

    assert result.status_code == 200
    assert result.audit.retry_count == 1
    assert result.audit.throttle_triggered is True
    assert sleeps == [1]


def test_retry_after_is_respected_when_present():
    sleeps: list[float] = []
    client = _client_with_statuses([429, 200], retry_after="7")
    policy = BOERequestPolicy(max_retries=5, jitter_seconds=0)

    policy.get("https://www.boe.es/test", client=client, sleeper=sleeps.append)

    assert sleeps == [7]


def test_retries_stop_after_configured_max_attempts():
    sleeps: list[float] = []
    client = _client_with_statuses([503, 503, 503])
    policy = BOERequestPolicy(max_retries=2, jitter_seconds=0)

    result = policy.get("https://www.boe.es/test", client=client, sleeper=sleeps.append)

    assert result.status_code == 503
    assert result.audit.retry_count == 2
    assert result.audit.throttle_triggered is True
    assert sleeps == [1, 2]
