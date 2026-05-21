from __future__ import annotations

import inspect
import time
from collections.abc import Callable

import httpx

from official_sources.integrity.hashing import sha256_bytes
from official_sources.sources.bocm.client import (
    BOCMClient,
    build_bocm_issue_summary_xml_url,
    build_bocm_search_day_url,
    validate_bocm_date,
)
from official_sources.sources.bocm.parser import (
    NO_PUBLICATION_STATUS,
    parse_bocm_issue_page,
    parse_bocm_search_day_response,
)
from official_sources.sources.boe.http_policy import BOERequestAudit
from official_sources.storage.repository import OfficialSourcesRepository

BOCM_PAYLOAD_SEPARATOR = b"\n---BOCM-PAYLOAD---\n"
BOCM_DEFAULT_TIMEOUT_RETRIES = 3
BOCM_TIMEOUT_BACKOFF_BASE_SECONDS = 1.0
BOCM_TIMEOUT_BACKOFF_MAX_SECONDS = 10.0


def ingest_bocm_date(
    repository: OfficialSourcesRepository,
    *,
    target_date: str,
    search_payload: bytes | None = None,
    issue_payload: bytes | None = None,
    fetcher: Callable | None = None,
    max_timeout_retries: int = BOCM_DEFAULT_TIMEOUT_RETRIES,
    sleeper: Callable[[float], None] = time.sleep,
) -> dict:
    validate_bocm_date(target_date)
    run = repository.create_ingestion_run(source_code="BOCM", target_date=target_date)
    request_audit = BOERequestAudit(last_http_status=200 if search_payload is not None else None)
    client: BOCMClient | None = None
    try:
        search_payload, final_url, request_audit, client = _fetch_search_payload(
            target_date=target_date,
            payload=search_payload,
            fetcher=fetcher,
            client=client,
            max_timeout_retries=max_timeout_retries,
            sleeper=sleeper,
        )
        discovery = parse_bocm_search_day_response(
            search_payload,
            target_date=target_date,
            final_url=final_url,
        )
        if discovery.status == NO_PUBLICATION_STATUS:
            run_record = repository.finish_ingestion_run(
                run_id=run["id"],
                status=NO_PUBLICATION_STATUS,
                documents_fetched=0,
                documents_new=0,
                documents_updated=0,
                error_message=f"BOCM returned no issue for date {target_date}",
                retry_count=request_audit.retry_count,
                throttle_triggered=request_audit.throttle_triggered,
                last_http_status=request_audit.last_http_status or 200,
            )
            return _with_bocm_metadata(
                run_record,
                issue_identifier=None,
                source_snapshot_hash=discovery.raw_payload_sha256,
            )
        assert discovery.issue_identifier is not None
        assert discovery.issue_url is not None
        assert discovery.issue_number is not None
        issue_payload_url = build_bocm_issue_summary_xml_url(target_date, discovery.issue_number)
        issue_payload, request_audit, client = _fetch_issue_payload(
            target_date=target_date,
            issue_url=issue_payload_url,
            payload=issue_payload,
            fetcher=fetcher,
            audit=request_audit,
            client=client,
            max_timeout_retries=max_timeout_retries,
            sleeper=sleeper,
        )
        issue = parse_bocm_issue_page(
            issue_payload,
            target_date=target_date,
            issue_identifier=discovery.issue_identifier,
            issue_url=discovery.issue_url,
        )
        source = repository.ensure_official_source_bocm()
        documents_new = 0
        documents_updated = 0
        combined_payload = search_payload + BOCM_PAYLOAD_SEPARATOR + issue_payload
        source_snapshot_hash = sha256_bytes(combined_payload)
        raw_url = build_bocm_search_day_url(target_date)
        for document_metadata in issue.documents:
            existing = repository.get_document_by_external_id(document_metadata.external_id)
            document = repository.upsert_document(
                source_id=source["id"],
                external_id=document_metadata.external_id,
                publication_date=document_metadata.publication_date,
                title=document_metadata.title,
                department=document_metadata.department,
                section=document_metadata.section,
                document_type=document_metadata.document_type,
                url_html=document_metadata.url_html,
                url_xml=document_metadata.url_xml,
                url_pdf=document_metadata.url_pdf,
                raw_metadata=document_metadata.raw_metadata,
            )
            if existing is None:
                documents_new += 1
            else:
                documents_updated += 1
            repository.upsert_document_file(
                document_id=document["id"],
                file_type="raw_api_response",
                official_url=raw_url,
                payload=combined_payload,
                ingestion_run_id=run["id"],
                media_type="text/html",
                source_snapshot_hash=source_snapshot_hash,
            )
        run_record = repository.finish_ingestion_run(
            run_id=run["id"],
            status="success",
            documents_fetched=len(issue.documents),
            documents_new=documents_new,
            documents_updated=documents_updated,
            retry_count=request_audit.retry_count,
            throttle_triggered=request_audit.throttle_triggered,
            last_http_status=request_audit.last_http_status or 200,
        )
        return _with_bocm_metadata(
            run_record,
            issue_identifier=discovery.issue_identifier,
            source_snapshot_hash=source_snapshot_hash,
        )
    except Exception as exc:
        request_audit = client.last_request_audit if client else request_audit
        run_record = repository.finish_ingestion_run(
            run_id=run["id"],
            status="failed",
            documents_fetched=0,
            documents_new=0,
            documents_updated=0,
            error_message=str(exc),
            retry_count=max(getattr(exc, "retry_count", 0), request_audit.retry_count),
            throttle_triggered=getattr(exc, "throttle_triggered", request_audit.throttle_triggered),
            last_http_status=getattr(exc, "last_http_status", request_audit.last_http_status),
        )
        return _with_bocm_metadata(
            run_record,
            issue_identifier=None,
            source_snapshot_hash=None,
        )


def _fetch_search_payload(
    *,
    target_date: str,
    payload: bytes | None,
    fetcher: Callable | None,
    client: BOCMClient | None,
    max_timeout_retries: int,
    sleeper: Callable[[float], None],
) -> tuple[bytes, str | None, BOERequestAudit, BOCMClient | None]:
    if payload is not None:
        return payload, None, BOERequestAudit(last_http_status=200), client
    search_url = build_bocm_search_day_url(target_date)
    if fetcher is not None:
        response_payload, audit = _fetch_with_timeout_retries(
            operation=lambda: _call_bocm_fetcher(fetcher, "search_day", target_date, search_url),
            kind="search_day",
            target_date=target_date,
            base_audit=BOERequestAudit(
                retry_count=getattr(fetcher, "retry_count", 0),
                throttle_triggered=getattr(fetcher, "throttle_triggered", False),
                last_http_status=getattr(fetcher, "last_http_status", 200),
            ),
            max_timeout_retries=max_timeout_retries,
            sleeper=sleeper,
        )
        return response_payload, None, audit, client
    client = client or BOCMClient()
    result, audit = _fetch_with_timeout_retries(
        operation=lambda: client.fetch_search_day(target_date),
        kind="search_day",
        target_date=target_date,
        base_audit=BOERequestAudit(),
        max_timeout_retries=max_timeout_retries,
        sleeper=sleeper,
    )
    return result.content, result.final_url, audit, client


def _fetch_issue_payload(
    *,
    target_date: str,
    issue_url: str,
    payload: bytes | None,
    fetcher: Callable | None,
    audit: BOERequestAudit,
    client: BOCMClient | None,
    max_timeout_retries: int,
    sleeper: Callable[[float], None],
) -> tuple[bytes, BOERequestAudit, BOCMClient | None]:
    if payload is not None:
        return payload, audit, client
    if fetcher is not None:
        payload, retry_audit = _fetch_with_timeout_retries(
            operation=lambda: _call_bocm_fetcher(fetcher, "issue_page", target_date, issue_url),
            kind="issue_page",
            target_date=target_date,
            base_audit=BOERequestAudit(
                throttle_triggered=audit.throttle_triggered
                or getattr(fetcher, "throttle_triggered", False),
                last_http_status=getattr(
                    fetcher, "last_http_status", audit.last_http_status or 200
                ),
            ),
            max_timeout_retries=max_timeout_retries,
            sleeper=sleeper,
        )
        return (
            payload,
            _merge_audit(audit, retry_audit),
            client,
        )
    client = client or BOCMClient()
    result, retry_audit = _fetch_with_timeout_retries(
        operation=lambda: client.fetch_issue_page(issue_url),
        kind="issue_page",
        target_date=target_date,
        base_audit=audit,
        max_timeout_retries=max_timeout_retries,
        sleeper=sleeper,
    )
    return result.content, _merge_audit(audit, retry_audit), client


def _call_bocm_fetcher(fetcher: Callable, kind: str, target_date: str, url: str) -> bytes:
    parameters = inspect.signature(fetcher).parameters
    accepts_varargs = any(
        parameter.kind == inspect.Parameter.VAR_POSITIONAL for parameter in parameters.values()
    )
    positional_count = sum(
        1
        for parameter in parameters.values()
        if parameter.kind
        in {inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD}
    )
    if accepts_varargs or positional_count >= 3:
        return fetcher(kind, target_date, url)
    if accepts_varargs or positional_count >= 2:
        return fetcher(kind, target_date)
    return fetcher(target_date)


def _fetch_with_timeout_retries(
    *,
    operation: Callable,
    kind: str,
    target_date: str,
    base_audit: BOERequestAudit,
    max_timeout_retries: int,
    sleeper: Callable[[float], None],
):
    retry_count = 0
    throttle_triggered = base_audit.throttle_triggered
    last_http_status = base_audit.last_http_status
    while True:
        try:
            result = operation()
            result_audit = getattr(result, "audit", None)
            if result_audit is not None:
                retry_count += result_audit.retry_count
                throttle_triggered = throttle_triggered or result_audit.throttle_triggered
                last_http_status = result_audit.last_http_status
            return result, BOERequestAudit(
                retry_count=base_audit.retry_count + retry_count,
                throttle_triggered=throttle_triggered,
                last_http_status=last_http_status,
            )
        except httpx.TimeoutException as exc:
            if retry_count >= max_timeout_retries:
                raise BOCMMetadataTimeoutError(
                    kind=kind,
                    target_date=target_date,
                    attempts=retry_count + 1,
                    original=exc,
                    retry_count=base_audit.retry_count + retry_count,
                    throttle_triggered=True,
                    last_http_status=last_http_status,
                ) from exc
            retry_count += 1
            throttle_triggered = True
            sleeper(_timeout_backoff_delay(retry_count))


def _timeout_backoff_delay(retry_count: int) -> float:
    delay = BOCM_TIMEOUT_BACKOFF_BASE_SECONDS * (2 ** (retry_count - 1))
    return min(delay, BOCM_TIMEOUT_BACKOFF_MAX_SECONDS)


def _merge_audit(first: BOERequestAudit, second: BOERequestAudit) -> BOERequestAudit:
    return BOERequestAudit(
        retry_count=first.retry_count + second.retry_count,
        throttle_triggered=first.throttle_triggered or second.throttle_triggered,
        last_http_status=second.last_http_status
        if second.last_http_status is not None
        else first.last_http_status,
    )


class BOCMMetadataTimeoutError(RuntimeError):
    def __init__(
        self,
        *,
        kind: str,
        target_date: str,
        attempts: int,
        original: Exception,
        retry_count: int,
        throttle_triggered: bool,
        last_http_status: int | None,
    ) -> None:
        super().__init__(
            f"BOCM {kind} request for {target_date} timed out after {attempts} attempts: {original}"
        )
        self.retry_count = retry_count
        self.throttle_triggered = throttle_triggered
        self.last_http_status = last_http_status


def _with_bocm_metadata(
    run_record: dict,
    *,
    issue_identifier: str | None,
    source_snapshot_hash: str | None,
) -> dict:
    return {
        **run_record,
        "issue_identifier": issue_identifier,
        "source_snapshot_hash": source_snapshot_hash,
    }
