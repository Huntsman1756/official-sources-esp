from __future__ import annotations

from collections.abc import Callable

from official_sources.sources.boe.client import BOEClient, validate_boe_date
from official_sources.sources.boe.http_policy import BOERequestAudit
from official_sources.sources.boe.parser import parse_boe_summary
from official_sources.storage.repository import OfficialSourcesRepository


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
    except Exception as exc:
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
