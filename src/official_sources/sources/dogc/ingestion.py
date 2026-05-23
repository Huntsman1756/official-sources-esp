from __future__ import annotations

from collections.abc import Callable

from official_sources.sources.dogc.client import (
    DOGCClient,
    build_dogc_date_search_url,
    validate_dogc_date,
)
from official_sources.sources.dogc.parser import (
    NO_PUBLICATION_STATUS,
    DOGCDocumentMetadata,
    parse_dogc_date_response,
    parse_dogc_document_metadata,
)
from official_sources.storage.repository import OfficialSourcesRepository


def ingest_dogc_date(
    repository: OfficialSourcesRepository,
    *,
    target_date: str,
    date_payload: bytes | None = None,
    document_payloads: dict[str, bytes] | None = None,
    fetcher: Callable | None = None,
    document_fetcher: Callable | None = None,
) -> dict:
    validate_dogc_date(target_date)
    document_payloads = document_payloads or {}
    run = repository.create_ingestion_run(source_code="DOGC", target_date=target_date)
    last_http_status = 200 if date_payload is not None else None
    try:
        client: DOGCClient | None = None
        if date_payload is None:
            if fetcher is not None:
                date_payload = _call_dogc_fetcher(fetcher, target_date)
                last_http_status = getattr(fetcher, "last_http_status", 200)
            else:
                client = DOGCClient()
                response = client.fetch_date(target_date)
                date_payload = response.content
                last_http_status = response.status_code
        issue = parse_dogc_date_response(date_payload, target_date=target_date)
        if issue.status == NO_PUBLICATION_STATUS:
            run_record = repository.finish_ingestion_run(
                run_id=run["id"],
                status=NO_PUBLICATION_STATUS,
                documents_fetched=0,
                documents_new=0,
                documents_updated=0,
                error_message=f"DOGC returned no records for date {target_date}",
                last_http_status=last_http_status or 200,
            )
            return _with_dogc_metadata(
                run_record,
                issue_identifier=None,
                source_snapshot_hash=issue.raw_payload_sha256,
            )
        source = repository.ensure_official_source_dogc()
        documents_new = 0
        documents_updated = 0
        raw_url = build_dogc_date_search_url()
        for search_metadata in issue.documents:
            document_id = str(search_metadata.raw_metadata["dogc_document_id"])
            document_metadata = _enrich_document_metadata(
                search_metadata,
                document_id=document_id,
                document_payloads=document_payloads,
                document_fetcher=document_fetcher,
                client=client,
            )
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
                media_type="application/json",
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
        return _with_dogc_metadata(
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
        return _with_dogc_metadata(
            run_record,
            issue_identifier=None,
            source_snapshot_hash=None,
        )


def _enrich_document_metadata(
    search_metadata: DOGCDocumentMetadata,
    *,
    document_id: str,
    document_payloads: dict[str, bytes],
    document_fetcher: Callable | None,
    client: DOGCClient | None,
) -> DOGCDocumentMetadata:
    payload = document_payloads.get(document_id)
    if payload is None and document_fetcher is not None:
        payload = document_fetcher(document_id)
    if payload is None:
        if client is None:
            client = DOGCClient()
        payload = client.fetch_document_metadata(document_id).content
    detail_metadata = parse_dogc_document_metadata(payload, fallback_document_id=document_id)
    return DOGCDocumentMetadata(
        external_id=detail_metadata.external_id,
        official_identifier=detail_metadata.official_identifier,
        publication_date=detail_metadata.publication_date,
        title=detail_metadata.title,
        department=detail_metadata.department,
        section=detail_metadata.section,
        document_type=detail_metadata.document_type,
        url_html=detail_metadata.url_html,
        url_xml=detail_metadata.url_xml or search_metadata.url_xml,
        url_pdf=detail_metadata.url_pdf or search_metadata.url_pdf,
        raw_metadata={
            **search_metadata.raw_metadata,
            **detail_metadata.raw_metadata,
            "search_metadata": search_metadata.raw_metadata,
        },
    )


def _call_dogc_fetcher(fetcher: Callable, target_date: str) -> bytes:
    return fetcher(target_date)


def _with_dogc_metadata(
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
