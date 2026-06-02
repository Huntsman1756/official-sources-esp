from __future__ import annotations

from collections.abc import Callable

from official_sources.sources.placsp.client import (
    PLACSPClient,
    build_placsp_feed_url,
    validate_placsp_feed_type,
    validate_placsp_limit,
)
from official_sources.sources.placsp.parser import NO_RESULTS_STATUS, parse_placsp_atom
from official_sources.storage.repository import OfficialSourcesRepository


def preview_placsp_feed(
    *,
    feed_type: str,
    limit: int = 50,
    feed_payload: bytes | None = None,
    fetcher: Callable | None = None,
) -> dict:
    feed_type = validate_placsp_feed_type(feed_type)
    limit = validate_placsp_limit(limit)
    source_url = build_placsp_feed_url(feed_type)
    last_http_status = 200 if feed_payload is not None else None
    retry_count = 0
    throttle_triggered = False
    try:
        if feed_payload is None:
            if fetcher is not None:
                feed_payload = fetcher(feed_type=feed_type, source_url=source_url)
                last_http_status = getattr(fetcher, "last_http_status", 200)
            else:
                response = PLACSPClient().fetch_feed(feed_type)
                feed_payload = response.content
                last_http_status = response.status_code
                retry_count = response.audit.retry_count
                throttle_triggered = response.audit.throttle_triggered
        page = parse_placsp_atom(feed_payload, source_url=source_url, feed_type=feed_type)
        tenders = page.tenders[:limit]
        return _with_placsp_metadata(
            {
                "status": "success",
                "documents_fetched": 0,
                "documents_new": 0,
                "documents_updated": 0,
                "retry_count": retry_count,
                "throttle_triggered": throttle_triggered,
                "last_http_status": last_http_status or 200,
                "error_message": None,
                "entry_count": len(tenders),
                "deleted_entry_count": len(page.deleted_entries),
            },
            source_snapshot_hash=page.source_snapshot_hash,
            placsp_result="success" if page.status == "success" else "no_results",
            sample_identifiers=[tender.official_identifier for tender in tenders[:5]],
            next_url=page.next_url,
        )
    except Exception as exc:
        return _with_placsp_metadata(
            {
                "status": "failed",
                "documents_fetched": 0,
                "documents_new": 0,
                "documents_updated": 0,
                "retry_count": retry_count,
                "throttle_triggered": throttle_triggered,
                "last_http_status": last_http_status,
                "error_message": str(exc),
                "entry_count": 0,
                "deleted_entry_count": 0,
            },
            source_snapshot_hash=None,
            placsp_result="failed",
            sample_identifiers=[],
            next_url=None,
        )


def ingest_placsp_feed(
    repository: OfficialSourcesRepository,
    *,
    feed_type: str,
    limit: int,
    feed_payload: bytes | None = None,
    fetcher: Callable | None = None,
) -> dict:
    feed_type = validate_placsp_feed_type(feed_type)
    limit = validate_placsp_limit(limit)
    source_url = build_placsp_feed_url(feed_type)
    run = repository.create_ingestion_run(source_code="PLACSP", target_date=f"feed:{feed_type}")
    last_http_status = 200 if feed_payload is not None else None
    retry_count = 0
    throttle_triggered = False
    try:
        if feed_payload is None:
            if fetcher is not None:
                feed_payload = fetcher(feed_type=feed_type, source_url=source_url)
                last_http_status = getattr(fetcher, "last_http_status", 200)
            else:
                response = PLACSPClient().fetch_feed(feed_type)
                feed_payload = response.content
                last_http_status = response.status_code
                retry_count = response.audit.retry_count
                throttle_triggered = response.audit.throttle_triggered
        page = parse_placsp_atom(feed_payload, source_url=source_url, feed_type=feed_type)
        return _store_tender_page(
            repository,
            run_id=run["id"],
            page_payload=feed_payload,
            page=page,
            limit=limit,
            last_http_status=last_http_status or 200,
            retry_count=retry_count,
            throttle_triggered=throttle_triggered,
        )
    except Exception as exc:
        return _with_placsp_metadata(
            repository.finish_ingestion_run(
                run_id=run["id"],
                status="failed",
                documents_fetched=0,
                documents_new=0,
                documents_updated=0,
                error_message=str(exc),
                retry_count=retry_count,
                throttle_triggered=throttle_triggered,
                last_http_status=last_http_status,
            ),
            source_snapshot_hash=None,
            placsp_result="failed",
            sample_identifiers=[],
            next_url=None,
        )


def _store_tender_page(
    repository: OfficialSourcesRepository,
    *,
    run_id: int,
    page_payload: bytes,
    page,
    limit: int,
    last_http_status: int,
    retry_count: int,
    throttle_triggered: bool,
) -> dict:
    source = repository.ensure_official_source_placsp()
    documents_new = 0
    documents_updated = 0
    tenders = page.tenders[:limit]
    for tender in tenders:
        existing = repository.get_document_by_external_id(tender.external_id)
        document = repository.upsert_document(
            source_id=source["id"],
            external_id=tender.external_id,
            publication_date=tender.publication_date,
            title=tender.title,
            department=tender.department,
            section=tender.section,
            document_type=tender.document_type,
            url_html=tender.url_html,
            url_xml=tender.url_xml,
            url_pdf=tender.url_pdf,
            raw_metadata=tender.raw_metadata,
        )
        repository.upsert_document_file(
            document_id=document["id"],
            file_type="raw_api_response",
            official_url=page.source_url,
            payload=page_payload,
            ingestion_run_id=run_id,
            media_type="application/atom+xml",
            source_snapshot_hash=page.source_snapshot_hash,
        )
        if existing is None:
            documents_new += 1
        else:
            documents_updated += 1
    run_record = repository.finish_ingestion_run(
        run_id=run_id,
        status="success",
        documents_fetched=len(tenders),
        documents_new=documents_new,
        documents_updated=documents_updated,
        retry_count=retry_count,
        throttle_triggered=throttle_triggered,
        last_http_status=last_http_status,
    )
    return _with_placsp_metadata(
        run_record,
        source_snapshot_hash=page.source_snapshot_hash,
        placsp_result="success" if page.status != NO_RESULTS_STATUS else "no_results",
        sample_identifiers=[tender.official_identifier for tender in tenders[:5]],
        next_url=page.next_url,
    )


def _with_placsp_metadata(
    run_record: dict,
    *,
    source_snapshot_hash: str | None,
    placsp_result: str,
    sample_identifiers: list[str],
    next_url: str | None,
) -> dict:
    return {
        **run_record,
        "source_snapshot_hash": source_snapshot_hash,
        "placsp_result": placsp_result,
        "sample_identifiers": sample_identifiers,
        "next_url": next_url,
    }
