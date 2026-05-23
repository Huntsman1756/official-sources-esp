from __future__ import annotations

import inspect
from collections.abc import Callable

from official_sources.integrity.hashing import sha256_bytes
from official_sources.sources.boe.http_policy import BOERequestAudit
from official_sources.sources.bopv.client import (
    BOPVClient,
    build_bopv_calendar_url,
    validate_bopv_date,
)
from official_sources.sources.bopv.parser import (
    NO_PUBLICATION_STATUS,
    parse_bopv_calendar,
    parse_bopv_issue_xml,
)
from official_sources.storage.repository import OfficialSourcesRepository

BOPV_PAYLOAD_SEPARATOR = b"\n---BOPV-PAYLOAD---\n"


def ingest_bopv_date(
    repository: OfficialSourcesRepository,
    *,
    target_date: str,
    calendar_payload: bytes | None = None,
    issue_payloads: list[bytes] | None = None,
    fetcher: Callable | None = None,
) -> dict:
    validate_bopv_date(target_date)
    run = repository.create_ingestion_run(source_code="BOPV", target_date=target_date)
    request_audit = BOERequestAudit(last_http_status=200 if calendar_payload is not None else None)
    client: BOPVClient | None = None
    try:
        calendar_payload, request_audit, client = _fetch_calendar_payload(
            target_date=target_date,
            payload=calendar_payload,
            fetcher=fetcher,
            client=client,
        )
        discovery = parse_bopv_calendar(calendar_payload, target_date=target_date)
        if discovery.status == NO_PUBLICATION_STATUS:
            run_record = repository.finish_ingestion_run(
                run_id=run["id"],
                status=NO_PUBLICATION_STATUS,
                documents_fetched=0,
                documents_new=0,
                documents_updated=0,
                error_message=f"BOPV returned no issue for date {target_date}",
                retry_count=request_audit.retry_count,
                throttle_triggered=request_audit.throttle_triggered,
                last_http_status=request_audit.last_http_status or 200,
            )
            return _with_bopv_metadata(
                run_record,
                issue_identifier=None,
                source_snapshot_hash=discovery.raw_payload_sha256,
            )
        fetched_issue_payloads, request_audit, client = _fetch_issue_payloads(
            target_date=target_date,
            issue_xml_urls=discovery.issue_xml_urls,
            payloads=issue_payloads,
            fetcher=fetcher,
            audit=request_audit,
            client=client,
        )
        source = repository.ensure_official_source_bopv()
        documents_new = 0
        documents_updated = 0
        source_snapshot_payload = BOPV_PAYLOAD_SEPARATOR.join(
            [calendar_payload, *fetched_issue_payloads]
        )
        source_snapshot_hash = sha256_bytes(source_snapshot_payload)
        raw_url = build_bopv_calendar_url(target_date)
        issue_identifier_parts: list[str] = []
        documents_fetched = 0
        for index, issue_payload in enumerate(fetched_issue_payloads):
            issue_identifier = discovery.issue_identifiers[index]
            issue_identifier_parts.append(issue_identifier)
            issue = parse_bopv_issue_xml(
                issue_payload,
                target_date=target_date,
                issue_identifier=issue_identifier,
                issue_url=discovery.issue_html_urls[index],
            )
            documents_fetched += len(issue.documents)
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
                    payload=source_snapshot_payload,
                    ingestion_run_id=run["id"],
                    media_type="application/xml",
                    source_snapshot_hash=source_snapshot_hash,
                )
        run_record = repository.finish_ingestion_run(
            run_id=run["id"],
            status="success",
            documents_fetched=documents_fetched,
            documents_new=documents_new,
            documents_updated=documents_updated,
            retry_count=request_audit.retry_count,
            throttle_triggered=request_audit.throttle_triggered,
            last_http_status=request_audit.last_http_status or 200,
        )
        return _with_bopv_metadata(
            run_record,
            issue_identifier=",".join(issue_identifier_parts),
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
            retry_count=request_audit.retry_count,
            throttle_triggered=request_audit.throttle_triggered,
            last_http_status=request_audit.last_http_status,
        )
        return _with_bopv_metadata(
            run_record,
            issue_identifier=None,
            source_snapshot_hash=None,
        )


def _fetch_calendar_payload(
    *,
    target_date: str,
    payload: bytes | None,
    fetcher: Callable | None,
    client: BOPVClient | None,
) -> tuple[bytes, BOERequestAudit, BOPVClient | None]:
    if payload is not None:
        return payload, BOERequestAudit(last_http_status=200), client
    url = build_bopv_calendar_url(target_date)
    if fetcher is not None:
        return (
            _call_bopv_fetcher(fetcher, "calendar", target_date, url),
            BOERequestAudit(
                retry_count=getattr(fetcher, "retry_count", 0),
                throttle_triggered=getattr(fetcher, "throttle_triggered", False),
                last_http_status=getattr(fetcher, "last_http_status", 200),
            ),
            client,
        )
    client = client or BOPVClient()
    result = client.fetch_calendar(target_date)
    return result.content, result.audit, client


def _fetch_issue_payloads(
    *,
    target_date: str,
    issue_xml_urls: list[str],
    payloads: list[bytes] | None,
    fetcher: Callable | None,
    audit: BOERequestAudit,
    client: BOPVClient | None,
) -> tuple[list[bytes], BOERequestAudit, BOPVClient | None]:
    if payloads is not None:
        return payloads, audit, client
    fetched_payloads = []
    for issue_xml_url in issue_xml_urls:
        if fetcher is not None:
            fetched_payloads.append(
                _call_bopv_fetcher(fetcher, "issue_xml", target_date, issue_xml_url)
            )
        else:
            client = client or BOPVClient()
            result = client.fetch_issue_xml(issue_xml_url)
            audit = _merge_audit(audit, result.audit)
            fetched_payloads.append(result.content)
    return fetched_payloads, audit, client


def _call_bopv_fetcher(fetcher: Callable, kind: str, target_date: str, url: str) -> bytes:
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


def _merge_audit(first: BOERequestAudit, second: BOERequestAudit) -> BOERequestAudit:
    return BOERequestAudit(
        retry_count=first.retry_count + second.retry_count,
        throttle_triggered=first.throttle_triggered or second.throttle_triggered,
        last_http_status=second.last_http_status
        if second.last_http_status is not None
        else first.last_http_status,
    )


def _with_bopv_metadata(
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
