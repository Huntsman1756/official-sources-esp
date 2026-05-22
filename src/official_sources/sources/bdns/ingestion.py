from __future__ import annotations

from collections.abc import Callable

from official_sources.sources.bdns.client import (
    BDNSClient,
    build_bdns_call_detail_api_url,
    build_bdns_latest_url,
    build_bdns_search_url,
    parse_bdns_date_filter,
    validate_bdns_limit,
    validate_bdns_max_pages,
    validate_bdns_num_conv,
)
from official_sources.sources.bdns.parser import (
    NO_RESULTS_STATUS,
    BDNSCallMetadata,
    parse_bdns_call_detail,
    parse_bdns_call_page,
)
from official_sources.storage.repository import OfficialSourcesRepository


def ingest_bdns_latest(
    repository: OfficialSourcesRepository,
    *,
    limit: int,
    latest_payload: bytes | None = None,
    fetcher: Callable | None = None,
) -> dict:
    validate_bdns_limit(limit, option_name="limit")
    source_url = build_bdns_latest_url(page_size=limit)
    run = repository.create_ingestion_run(source_code="BDNS", target_date="latest")
    last_http_status = 200 if latest_payload is not None else None
    retry_count = 0
    throttle_triggered = False
    try:
        if latest_payload is None:
            if fetcher is not None:
                latest_payload = fetcher(limit)
                last_http_status = getattr(fetcher, "last_http_status", 200)
            else:
                client = BDNSClient()
                response = client.fetch_latest(limit=limit)
                latest_payload = response.content
                last_http_status = response.status_code
                retry_count = response.audit.retry_count
                throttle_triggered = response.audit.throttle_triggered
        page = parse_bdns_call_page(latest_payload, source_url=source_url)
        return _store_call_page(
            repository,
            run_id=run["id"],
            page_payload=latest_payload,
            page=page,
            status="success" if page.status == "success" else "success",
            last_http_status=last_http_status or 200,
            retry_count=retry_count,
            throttle_triggered=throttle_triggered,
        )
    except Exception as exc:
        return _finish_failed(
            repository,
            run_id=run["id"],
            error_message=str(exc),
            last_http_status=last_http_status,
            retry_count=retry_count,
            throttle_triggered=throttle_triggered,
        )


def ingest_bdns_call(
    repository: OfficialSourcesRepository,
    *,
    num_conv: str,
    detail_payload: bytes | None = None,
    fetcher: Callable | None = None,
) -> dict:
    num_conv = validate_bdns_num_conv(num_conv)
    run = repository.create_ingestion_run(source_code="BDNS", target_date=num_conv)
    last_http_status = 200 if detail_payload is not None else None
    retry_count = 0
    throttle_triggered = False
    try:
        source_url = build_bdns_call_detail_api_url(num_conv)
        if detail_payload is None:
            if fetcher is not None:
                detail_payload = fetcher(num_conv)
                last_http_status = getattr(fetcher, "last_http_status", 200)
            else:
                client = BDNSClient()
                response = client.fetch_call_detail(num_conv)
                detail_payload = response.content
                last_http_status = response.status_code
                retry_count = response.audit.retry_count
                throttle_triggered = response.audit.throttle_triggered
        call = parse_bdns_call_detail(detail_payload, num_conv=num_conv)
        source = repository.ensure_official_source_bdns()
        existing = repository.get_document_by_external_id(call.external_id)
        document = _upsert_call(repository, source_id=source["id"], call=call)
        repository.upsert_document_file(
            document_id=document["id"],
            file_type="raw_api_response",
            official_url=source_url,
            payload=detail_payload,
            ingestion_run_id=run["id"],
            media_type="application/json",
            source_snapshot_hash=call.raw_metadata["detail_api_sha256"],
        )
        run_record = repository.finish_ingestion_run(
            run_id=run["id"],
            status="success",
            documents_fetched=1,
            documents_new=1 if existing is None else 0,
            documents_updated=0 if existing is None else 1,
            retry_count=retry_count,
            throttle_triggered=throttle_triggered,
            last_http_status=last_http_status or 200,
        )
        return _with_bdns_metadata(
            run_record,
            official_identifier=call.official_identifier,
            source_snapshot_hash=call.raw_metadata["detail_api_sha256"],
        )
    except Exception as exc:
        return _with_bdns_metadata(
            _finish_failed(
                repository,
                run_id=run["id"],
                error_message=str(exc),
                last_http_status=last_http_status,
                retry_count=retry_count,
                throttle_triggered=throttle_triggered,
            ),
            official_identifier=None,
            source_snapshot_hash=None,
        )


def search_bdns_calls(
    repository: OfficialSourcesRepository,
    *,
    date_from: str | None,
    date_to: str | None,
    page_size: int,
    max_pages: int,
    fetcher: Callable | None = None,
) -> dict:
    if date_from:
        parse_bdns_date_filter(date_from)
    if date_to:
        parse_bdns_date_filter(date_to)
    validate_bdns_limit(page_size, option_name="page-size")
    validate_bdns_max_pages(max_pages)
    target = f"search:{date_from or 'any'}:{date_to or 'any'}"
    run = repository.create_ingestion_run(source_code="BDNS", target_date=target)
    source = repository.ensure_official_source_bdns()
    documents_fetched = 0
    documents_new = 0
    documents_updated = 0
    source_snapshot_hash: str | None = None
    last_http_status = None
    try:
        for page_number in range(1, max_pages + 1):
            source_url = build_bdns_search_url(
                date_from=date_from,
                date_to=date_to,
                page=page_number,
                page_size=page_size,
            )
            if fetcher is not None:
                payload = fetcher(
                    date_from=date_from,
                    date_to=date_to,
                    page=page_number,
                    page_size=page_size,
                )
                last_http_status = getattr(fetcher, "last_http_status", 200)
            else:
                response = BDNSClient().fetch_search(
                    date_from=date_from,
                    date_to=date_to,
                    page=page_number,
                    page_size=page_size,
                )
                payload = response.content
                last_http_status = response.status_code
            page = parse_bdns_call_page(payload, source_url=source_url)
            source_snapshot_hash = page.source_snapshot_hash
            if page.status == NO_RESULTS_STATUS:
                break
            for call in page.calls:
                existing = repository.get_document_by_external_id(call.external_id)
                document = _upsert_call(repository, source_id=source["id"], call=call)
                repository.upsert_document_file(
                    document_id=document["id"],
                    file_type="raw_api_response",
                    official_url=page.source_url,
                    payload=payload,
                    ingestion_run_id=run["id"],
                    media_type="application/json",
                    source_snapshot_hash=page.source_snapshot_hash,
                )
                documents_fetched += 1
                if existing is None:
                    documents_new += 1
                else:
                    documents_updated += 1
            if page.last:
                break
        run_record = repository.finish_ingestion_run(
            run_id=run["id"],
            status="success",
            documents_fetched=documents_fetched,
            documents_new=documents_new,
            documents_updated=documents_updated,
            last_http_status=last_http_status or 200,
        )
        return _with_bdns_metadata(
            run_record,
            official_identifier=None,
            source_snapshot_hash=source_snapshot_hash,
        )
    except Exception as exc:
        return _finish_failed(
            repository,
            run_id=run["id"],
            error_message=str(exc),
            last_http_status=last_http_status,
        )


def _store_call_page(
    repository: OfficialSourcesRepository,
    *,
    run_id: int,
    page_payload: bytes,
    page,
    status: str,
    last_http_status: int,
    retry_count: int,
    throttle_triggered: bool,
) -> dict:
    source = repository.ensure_official_source_bdns()
    documents_new = 0
    documents_updated = 0
    for call in page.calls:
        existing = repository.get_document_by_external_id(call.external_id)
        document = _upsert_call(repository, source_id=source["id"], call=call)
        repository.upsert_document_file(
            document_id=document["id"],
            file_type="raw_api_response",
            official_url=page.source_url,
            payload=page_payload,
            ingestion_run_id=run_id,
            media_type="application/json",
            source_snapshot_hash=page.source_snapshot_hash,
        )
        if existing is None:
            documents_new += 1
        else:
            documents_updated += 1
    run_record = repository.finish_ingestion_run(
        run_id=run_id,
        status=status,
        documents_fetched=len(page.calls),
        documents_new=documents_new,
        documents_updated=documents_updated,
        retry_count=retry_count,
        throttle_triggered=throttle_triggered,
        last_http_status=last_http_status,
    )
    return _with_bdns_metadata(
        run_record,
        official_identifier=None,
        source_snapshot_hash=page.source_snapshot_hash,
    )


def _upsert_call(
    repository: OfficialSourcesRepository,
    *,
    source_id: int,
    call: BDNSCallMetadata,
) -> dict:
    return repository.upsert_document(
        source_id=source_id,
        external_id=call.external_id,
        publication_date=call.publication_date,
        title=call.title,
        department=call.department,
        section=call.section,
        document_type=call.raw_metadata.get("resource_type") or call.document_type,
        url_html=call.url_html,
        url_xml=call.url_xml,
        url_pdf=call.url_pdf,
        raw_metadata=call.raw_metadata,
    )


def _finish_failed(
    repository: OfficialSourcesRepository,
    *,
    run_id: int,
    error_message: str,
    last_http_status: int | None,
    retry_count: int = 0,
    throttle_triggered: bool = False,
) -> dict:
    return repository.finish_ingestion_run(
        run_id=run_id,
        status="failed",
        documents_fetched=0,
        documents_new=0,
        documents_updated=0,
        error_message=error_message,
        retry_count=retry_count,
        throttle_triggered=throttle_triggered,
        last_http_status=last_http_status,
    )


def _with_bdns_metadata(
    run_record: dict,
    *,
    official_identifier: str | None,
    source_snapshot_hash: str | None,
) -> dict:
    return {
        **run_record,
        "official_identifier": official_identifier,
        "source_snapshot_hash": source_snapshot_hash,
    }
