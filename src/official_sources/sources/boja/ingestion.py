from __future__ import annotations

import inspect
import json
from collections.abc import Callable
from typing import Any

import httpx

from official_sources.integrity.hashing import sha256_bytes
from official_sources.sources.boe.http_policy import BOERequestAudit
from official_sources.sources.boja.client import (
    BOJA_DEFAULT_PAGE_SIZE,
    BOJAClient,
    boja_max_pages_from_env,
    build_boja_search_url,
    validate_boja_date,
)
from official_sources.sources.boja.parser import parse_boja_search_response
from official_sources.storage.repository import OfficialSourcesRepository

NO_PUBLICATION_STATUS = "no_publication"
BOJA_PAGE_SEPARATOR = b"\n---BOJA-PAGE---\n"


def ingest_boja_date(
    repository: OfficialSourcesRepository,
    *,
    target_date: str,
    payload: bytes | None = None,
    fetcher: Callable[[str], bytes] | None = None,
    page_size: int = BOJA_DEFAULT_PAGE_SIZE,
    max_pages: int | None = None,
) -> dict:
    validate_boja_date(target_date)
    max_pages = max_pages or boja_max_pages_from_env()
    run = repository.create_ingestion_run(source_code="BOJA", target_date=target_date)
    request_audit = BOERequestAudit(last_http_status=200 if payload is not None else None)
    client: BOJAClient | None = None
    try:
        pages, request_audit, client = _fetch_boja_pages(
            target_date=target_date,
            payload=payload,
            fetcher=fetcher,
            page_size=page_size,
            max_pages=max_pages,
        )
        parsed_pages = [
            parse_boja_search_response(page_payload, target_date=target_date)
            for page_payload in pages
        ]
        pages_fetched = len(parsed_pages)
        if any(not page.has_total_hits for page in parsed_pages):
            run_record = repository.finish_ingestion_run(
                run_id=run["id"],
                status="failed",
                documents_fetched=0,
                documents_new=0,
                documents_updated=0,
                error_message="BOJA pagination metadata missing total_hits",
                retry_count=request_audit.retry_count,
                throttle_triggered=request_audit.throttle_triggered,
                last_http_status=request_audit.last_http_status or 200,
            )
            return _with_pagination_metadata(
                run_record,
                pages_fetched=pages_fetched,
                pagination_complete=False,
            )
        total_hits = parsed_pages[0].total_hits
        if total_hits == 0:
            run_record = repository.finish_ingestion_run(
                run_id=run["id"],
                status=NO_PUBLICATION_STATUS,
                documents_fetched=0,
                documents_new=0,
                documents_updated=0,
                error_message=f"BOJA returned no documents for date {target_date}",
                retry_count=request_audit.retry_count,
                throttle_triggered=request_audit.throttle_triggered,
                last_http_status=request_audit.last_http_status or 200,
            )
            return _with_pagination_metadata(
                run_record,
                pages_fetched=pages_fetched,
                pagination_complete=True,
            )
        documents_by_external_id = {}
        for parsed in parsed_pages:
            for document in parsed.documents:
                documents_by_external_id.setdefault(document.external_id, document)
        if len(documents_by_external_id) < total_hits:
            if pages_fetched >= max_pages:
                error_message = (
                    f"BOJA pagination exceeded max pages ({max_pages}) before reaching "
                    f"total_hits={total_hits}"
                )
            else:
                error_message = (
                    "BOJA pagination did not collect expected total_hits; "
                    f"collected={len(documents_by_external_id)} total_hits={total_hits}"
                )
            run_record = repository.finish_ingestion_run(
                run_id=run["id"],
                status="failed",
                documents_fetched=0,
                documents_new=0,
                documents_updated=0,
                error_message=error_message,
                retry_count=request_audit.retry_count,
                throttle_triggered=request_audit.throttle_triggered,
                last_http_status=request_audit.last_http_status or 200,
            )
            return _with_pagination_metadata(
                run_record,
                pages_fetched=pages_fetched,
                pagination_complete=False,
            )
        source = repository.ensure_official_source_boja()
        documents_new = 0
        documents_updated = 0
        raw_url = build_boja_search_url(target_date, page=0, size=page_size)
        combined_payload = BOJA_PAGE_SEPARATOR.join(pages)
        combined_source_snapshot_hash = sha256_bytes(combined_payload)
        for document_metadata in documents_by_external_id.values():
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
                media_type="application/json",
                source_snapshot_hash=combined_source_snapshot_hash,
            )
        run_record = repository.finish_ingestion_run(
            run_id=run["id"],
            status="success",
            documents_fetched=len(documents_by_external_id),
            documents_new=documents_new,
            documents_updated=documents_updated,
            retry_count=request_audit.retry_count,
            throttle_triggered=request_audit.throttle_triggered,
            last_http_status=request_audit.last_http_status,
        )
        return _with_pagination_metadata(
            run_record,
            pages_fetched=pages_fetched,
            pagination_complete=True,
        )
    except Exception as exc:
        request_audit = _audit_from_exception(
            exc,
            fallback=client.last_request_audit if client else request_audit,
        )
        if _http_error_indicates_observed_no_publication(exc):
            run_record = repository.finish_ingestion_run(
                run_id=run["id"],
                status=NO_PUBLICATION_STATUS,
                documents_fetched=0,
                documents_new=0,
                documents_updated=0,
                error_message=(
                    f"BOJA returned HTTP 400 Bad request for date {target_date}; "
                    "classified as no_publication based on observed empty-date API behavior"
                ),
                retry_count=request_audit.retry_count,
                throttle_triggered=request_audit.throttle_triggered,
                last_http_status=request_audit.last_http_status,
            )
            return _with_pagination_metadata(
                run_record,
                pages_fetched=0,
                pagination_complete=True,
            )
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
        return _with_pagination_metadata(
            run_record,
            pages_fetched=0,
            pagination_complete=False,
        )


def _fetch_boja_pages(
    *,
    target_date: str,
    payload: bytes | None,
    fetcher: Callable | None,
    page_size: int,
    max_pages: int,
) -> tuple[list[bytes], BOERequestAudit, BOJAClient | None]:
    if payload is not None:
        return [payload], BOERequestAudit(last_http_status=200), None
    pages: list[bytes] = []
    client: BOJAClient | None = None
    request_audit = BOERequestAudit()
    for page in range(max_pages):
        if fetcher is not None:
            page_payload = _call_boja_fetcher(fetcher, target_date, page, page_size)
            request_audit = BOERequestAudit(
                retry_count=max(request_audit.retry_count, getattr(fetcher, "retry_count", 0)),
                throttle_triggered=(
                    request_audit.throttle_triggered
                    or getattr(fetcher, "throttle_triggered", False)
                ),
                last_http_status=getattr(fetcher, "last_http_status", 200),
            )
        else:
            client = client or BOJAClient()
            page_payload = client.fetch_date_page(target_date, page=page, size=page_size)
            request_audit = BOERequestAudit(
                retry_count=max(request_audit.retry_count, client.last_request_audit.retry_count),
                throttle_triggered=(
                    request_audit.throttle_triggered or client.last_request_audit.throttle_triggered
                ),
                last_http_status=client.last_request_audit.last_http_status,
            )
        pages.append(page_payload)
        parsed = parse_boja_search_response(page_payload, target_date=target_date)
        if not parsed.has_total_hits:
            return pages, request_audit, client
        collected = sum(
            len(parse_boja_search_response(item, target_date=target_date).documents)
            for item in pages
        )
        if parsed.total_hits == 0 or collected >= parsed.total_hits:
            return pages, request_audit, client
        if not parsed.documents:
            return pages, request_audit, client
    return pages, request_audit, client


def _call_boja_fetcher(fetcher: Callable, target_date: str, page: int, page_size: int) -> bytes:
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
        return fetcher(target_date, page, page_size)
    if page == 0:
        return fetcher(target_date)
    raise ValueError("BOJA fetcher does not support pagination")


def _http_error_indicates_observed_no_publication(exc: Exception) -> bool:
    if not isinstance(exc, httpx.HTTPStatusError):
        return False
    response = exc.response
    if response.status_code != 400:
        return False
    payload = _json_object_from_response(response)
    if payload is None:
        return False
    message = str(payload.get("message") or "").strip().lower()
    status = payload.get("status")
    keys = set(payload)
    return status == 400 and message == "bad request" and keys <= {"status", "message"}


def _json_object_from_response(response: httpx.Response) -> dict[str, Any] | None:
    content_type = response.headers.get("content-type", "").lower()
    if "json" not in content_type:
        return None
    try:
        payload = response.json()
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def _with_pagination_metadata(
    run_record: dict,
    *,
    pages_fetched: int,
    pagination_complete: bool,
) -> dict:
    return {
        **run_record,
        "pages_fetched": pages_fetched,
        "pagination_complete": pagination_complete,
    }


def _audit_from_exception(
    exc: Exception,
    *,
    fallback: BOERequestAudit | None = None,
) -> BOERequestAudit:
    fallback = fallback or BOERequestAudit()
    status_code = getattr(exc, "last_http_status", None)
    if status_code is None and isinstance(exc, httpx.HTTPStatusError):
        status_code = exc.response.status_code
    return BOERequestAudit(
        retry_count=getattr(exc, "retry_count", fallback.retry_count),
        throttle_triggered=getattr(exc, "throttle_triggered", fallback.throttle_triggered),
        last_http_status=status_code if status_code is not None else fallback.last_http_status,
    )
