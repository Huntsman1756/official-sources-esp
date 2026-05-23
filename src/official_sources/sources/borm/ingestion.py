from __future__ import annotations

from collections.abc import Callable

from official_sources.sources.borm.client import (
    BORMClient,
    build_borm_index_xml_url,
    validate_borm_date,
)
from official_sources.sources.borm.parser import NO_PUBLICATION_STATUS, parse_borm_date_response
from official_sources.storage.repository import OfficialSourcesRepository


def ingest_borm_date(
    repository: OfficialSourcesRepository,
    *,
    target_date: str,
    date_payload: bytes | None = None,
    fetcher: Callable | None = None,
) -> dict:
    validate_borm_date(target_date)
    run = repository.create_ingestion_run(source_code="BORM", target_date=target_date)
    last_http_status = 200 if date_payload is not None else None
    try:
        if date_payload is None:
            if fetcher is not None:
                date_payload = _call_borm_fetcher(fetcher, target_date)
                last_http_status = getattr(fetcher, "last_http_status", 200)
            else:
                client = BORMClient()
                response = client.fetch_date(target_date)
                date_payload = response.content
                last_http_status = response.status_code
        issue = parse_borm_date_response(date_payload, target_date=target_date)
        if issue.status == NO_PUBLICATION_STATUS:
            run_record = repository.finish_ingestion_run(
                run_id=run["id"],
                status=NO_PUBLICATION_STATUS,
                documents_fetched=0,
                documents_new=0,
                documents_updated=0,
                error_message=f"BORM returned no records for date {target_date}",
                last_http_status=last_http_status or 200,
            )
            return _with_borm_metadata(
                run_record,
                issue_identifier=None,
                source_snapshot_hash=issue.raw_payload_sha256,
            )
        source = repository.ensure_official_source_borm()
        documents_new = 0
        documents_updated = 0
        raw_url = build_borm_index_xml_url()
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
                payload=date_payload,
                ingestion_run_id=run["id"],
                media_type="application/xml",
                source_snapshot_hash=issue.raw_payload_sha256,
            )
        run_record = repository.finish_ingestion_run(
            run_id=run["id"],
            status="success",
            documents_fetched=len(issue.documents),
            documents_new=documents_new,
            documents_updated=documents_updated,
            last_http_status=last_http_status or 200,
        )
        return _with_borm_metadata(
            run_record,
            issue_identifier=issue.issue_identifier,
            source_snapshot_hash=issue.raw_payload_sha256,
        )
    except Exception as exc:
        run_record = repository.finish_ingestion_run(
            run_id=run["id"],
            status="failed",
            documents_fetched=0,
            documents_new=0,
            documents_updated=0,
            error_message=str(exc),
            last_http_status=last_http_status,
        )
        return _with_borm_metadata(
            run_record,
            issue_identifier=None,
            source_snapshot_hash=None,
        )


def _call_borm_fetcher(fetcher: Callable, target_date: str) -> bytes:
    return fetcher(target_date)


def _with_borm_metadata(
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
