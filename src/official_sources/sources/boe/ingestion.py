from __future__ import annotations

from collections.abc import Callable

import httpx

from official_sources.sources.boe.client import (
    BOEClient,
    BOESummaryNotFoundError,
    validate_boe_date,
)
from official_sources.sources.boe.http_policy import BOERequestAudit
from official_sources.sources.boe.parser import parse_boe_summary
from official_sources.storage.repository import OfficialSourcesRepository

NO_PUBLICATION_STATUS = "no_publication"


def ingest_boe_summary(
    repository: OfficialSourcesRepository,
    *,
    target_date: str,
    payload: bytes | None = None,
    fetcher: Callable[[str], bytes] | None = None,
) -> dict:
    validate_boe_date(target_date)
    run = repository.create_ingestion_run(source_code="BOE", target_date=target_date)
    request_audit = BOERequestAudit(last_http_status=200 if payload is not None else None)
    client: BOEClient | None = None
    try:
        if payload is None:
            if fetcher is not None:
                payload = fetcher(target_date)
                request_audit = BOERequestAudit(
                    retry_count=getattr(fetcher, "retry_count", 0),
                    throttle_triggered=getattr(fetcher, "throttle_triggered", False),
                    last_http_status=getattr(fetcher, "last_http_status", 200),
                )
            else:
                client = BOEClient()
                payload = client.fetch_summary(target_date)
                request_audit = client.last_request_audit
        parsed = parse_boe_summary(payload)
        source = repository.ensure_official_source_boe()
        documents_new = 0
        documents_updated = 0
        raw_url = "https://www.boe.es/datosabiertos/api/boe/sumario/" + target_date.replace("-", "")
        for document_metadata in parsed.documents:
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
                payload=payload,
                ingestion_run_id=run["id"],
                media_type="application/json",
                source_snapshot_hash=parsed.raw_payload_sha256,
            )
        return repository.finish_ingestion_run(
            run_id=run["id"],
            status="success",
            documents_fetched=len(parsed.documents),
            documents_new=documents_new,
            documents_updated=documents_updated,
            retry_count=request_audit.retry_count,
            throttle_triggered=request_audit.throttle_triggered,
            last_http_status=request_audit.last_http_status,
        )
    except BOESummaryNotFoundError as exc:
        fallback_audit = client.last_request_audit if client else None
        request_audit = _audit_from_exception(exc, fallback=fallback_audit)
        return repository.finish_ingestion_run(
            run_id=run["id"],
            status=NO_PUBLICATION_STATUS,
            documents_fetched=0,
            documents_new=0,
            documents_updated=0,
            error_message=str(exc),
            retry_count=request_audit.retry_count,
            throttle_triggered=request_audit.throttle_triggered,
            last_http_status=404,
        )
    except Exception as exc:
        request_audit = _audit_from_exception(
            exc,
            fallback=client.last_request_audit if client else request_audit,
        )
        return repository.finish_ingestion_run(
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
