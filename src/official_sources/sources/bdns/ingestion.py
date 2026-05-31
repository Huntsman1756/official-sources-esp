from __future__ import annotations

from collections.abc import Callable

from official_sources.sources.bdns.client import (
    BDNSClient,
    build_bdns_call_detail_api_url,
    build_bdns_catalog_url,
    build_bdns_concessions_search_url,
    build_bdns_latest_url,
    build_bdns_search_url,
    parse_bdns_date_filter,
    validate_bdns_catalog_name,
    validate_bdns_limit,
    validate_bdns_max_pages,
    validate_bdns_num_conv,
)
from official_sources.sources.bdns.parser import (
    NO_RESULTS_STATUS,
    BDNSCallMetadata,
    BDNSNotFoundError,
    parse_bdns_call_detail,
    parse_bdns_call_page,
    parse_bdns_catalog,
    parse_bdns_concession_page,
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
            page_count=1,
            pagination_limit_reached=False,
            bdns_result="success" if page.status == "success" else "no_results",
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
            bdns_result=_classify_bdns_error(exc),
            page_count=0,
            pagination_limit_reached=False,
            sample_identifiers=[],
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
            bdns_result="success",
            page_count=1,
            pagination_limit_reached=False,
            sample_identifiers=[call.official_identifier],
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
            bdns_result=_classify_bdns_error(exc),
            page_count=0,
            pagination_limit_reached=False,
            sample_identifiers=[],
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
    page_count = 0
    pagination_limit_reached = False
    bdns_result = "no_results"
    sample_identifiers: list[str] = []
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
            page_count += 1
            source_snapshot_hash = page.source_snapshot_hash
            if page.status == NO_RESULTS_STATUS:
                break
            bdns_result = "success"
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
                if len(sample_identifiers) < 5:
                    sample_identifiers.append(call.official_identifier)
            if page.last:
                break
            if page_number == max_pages:
                pagination_limit_reached = True
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
            bdns_result=bdns_result,
            page_count=page_count,
            pagination_limit_reached=pagination_limit_reached,
            sample_identifiers=sample_identifiers,
        )
    except Exception as exc:
        return _with_bdns_metadata(
            _finish_failed(
                repository,
                run_id=run["id"],
                error_message=str(exc),
                last_http_status=last_http_status,
            ),
            official_identifier=None,
            source_snapshot_hash=source_snapshot_hash,
            bdns_result=_classify_bdns_error(exc),
            page_count=page_count,
            pagination_limit_reached=pagination_limit_reached,
            sample_identifiers=sample_identifiers,
        )


def preview_bdns_catalog(
    catalog_name: str,
    *,
    catalog_payload: bytes | None = None,
    fetcher: Callable | None = None,
    vpd: str = "GE",
    id_admon: str | None = None,
    ambito: str | None = None,
) -> dict:
    catalog_name = validate_bdns_catalog_name(catalog_name)
    source_url = build_bdns_catalog_url(
        catalog_name,
        vpd=vpd,
        id_admon=id_admon,
        ambito=ambito,
    )
    last_http_status = 200 if catalog_payload is not None else None
    retry_count = 0
    throttle_triggered = False
    try:
        if catalog_payload is None:
            if fetcher is not None:
                catalog_payload = fetcher(
                    catalog_name,
                    vpd=vpd,
                    id_admon=id_admon,
                    ambito=ambito,
                )
                last_http_status = getattr(fetcher, "last_http_status", 200)
            else:
                response = BDNSClient().fetch_catalog(
                    catalog_name,
                    vpd=vpd,
                    id_admon=id_admon,
                    ambito=ambito,
                )
                catalog_payload = response.content
                last_http_status = response.status_code
                retry_count = response.audit.retry_count
                throttle_triggered = response.audit.throttle_triggered
        catalog = parse_bdns_catalog(
            catalog_payload,
            catalog_name=catalog_name,
            source_url=source_url,
        )
        return _with_bdns_metadata(
            {
                "status": "success",
                "documents_fetched": 0,
                "documents_new": 0,
                "documents_updated": 0,
                "retry_count": retry_count,
                "throttle_triggered": throttle_triggered,
                "last_http_status": last_http_status or 200,
                "error_message": None,
                "catalog_name": catalog.catalog_name,
                "entry_count": catalog.entry_count,
            },
            official_identifier=None,
            source_snapshot_hash=catalog.source_snapshot_hash,
            bdns_result="success" if catalog.status == "success" else "no_results",
            page_count=1,
            pagination_limit_reached=False,
            sample_identifiers=[entry.external_id for entry in catalog.entries[:5]],
        )
    except Exception as exc:
        return _with_bdns_metadata(
            {
                "status": "failed",
                "documents_fetched": 0,
                "documents_new": 0,
                "documents_updated": 0,
                "retry_count": retry_count,
                "throttle_triggered": throttle_triggered,
                "last_http_status": last_http_status,
                "error_message": str(exc),
                "catalog_name": catalog_name,
                "entry_count": 0,
            },
            official_identifier=None,
            source_snapshot_hash=None,
            bdns_result="failed",
            page_count=0,
            pagination_limit_reached=False,
            sample_identifiers=[],
        )


def ingest_bdns_catalog(
    repository: OfficialSourcesRepository,
    catalog_name: str,
    *,
    catalog_payload: bytes | None = None,
    fetcher: Callable | None = None,
    vpd: str = "GE",
    id_admon: str | None = None,
    ambito: str | None = None,
) -> dict:
    catalog_name = validate_bdns_catalog_name(catalog_name)
    source_url = build_bdns_catalog_url(
        catalog_name,
        vpd=vpd,
        id_admon=id_admon,
        ambito=ambito,
    )
    target = f"catalog:{catalog_name}"
    run = repository.create_ingestion_run(source_code="BDNS", target_date=target)
    last_http_status = 200 if catalog_payload is not None else None
    retry_count = 0
    throttle_triggered = False
    source_snapshot_hash: str | None = None
    try:
        if catalog_payload is None:
            if fetcher is not None:
                catalog_payload = fetcher(
                    catalog_name,
                    vpd=vpd,
                    id_admon=id_admon,
                    ambito=ambito,
                )
                last_http_status = getattr(fetcher, "last_http_status", 200)
            else:
                response = BDNSClient().fetch_catalog(
                    catalog_name,
                    vpd=vpd,
                    id_admon=id_admon,
                    ambito=ambito,
                )
                catalog_payload = response.content
                last_http_status = response.status_code
                retry_count = response.audit.retry_count
                throttle_triggered = response.audit.throttle_triggered
        catalog = parse_bdns_catalog(
            catalog_payload,
            catalog_name=catalog_name,
            source_url=source_url,
        )
        source_snapshot_hash = catalog.source_snapshot_hash
        documents_new = 0
        documents_updated = 0
        sample_identifiers: list[str] = []
        for entry in catalog.entries:
            scoped_code = _scoped_catalog_code(
                catalog_name=entry.catalog_name,
                code=entry.code,
                id_admon=id_admon,
            )
            existing = repository.get_bdns_catalog_entry(entry.catalog_name, scoped_code)
            record = repository.upsert_bdns_catalog_entry(
                catalog_name=entry.catalog_name,
                code=scoped_code,
                name=entry.name,
                source_url=catalog.source_url,
                raw_metadata=_catalog_entry_raw_metadata(
                    entry.raw_metadata,
                    catalog_name=entry.catalog_name,
                    id_admon=id_admon,
                ),
                source_snapshot_hash=catalog.source_snapshot_hash,
                ingestion_run_id=run["id"],
            )
            if existing is None:
                documents_new += 1
            elif existing["content_hash"] != record["content_hash"]:
                documents_updated += 1
            if len(sample_identifiers) < 5:
                sample_identifiers.append(record["external_id"])
        run_record = repository.finish_ingestion_run(
            run_id=run["id"],
            status="success",
            documents_fetched=catalog.entry_count,
            documents_new=documents_new,
            documents_updated=documents_updated,
            retry_count=retry_count,
            throttle_triggered=throttle_triggered,
            last_http_status=last_http_status or 200,
        )
        return _with_bdns_metadata(
            {
                **run_record,
                "catalog_name": catalog.catalog_name,
                "entry_count": catalog.entry_count,
            },
            official_identifier=None,
            source_snapshot_hash=catalog.source_snapshot_hash,
            bdns_result="success" if catalog.status == "success" else "no_results",
            page_count=1,
            pagination_limit_reached=False,
            sample_identifiers=sample_identifiers,
        )
    except Exception as exc:
        return _with_bdns_metadata(
            {
                **_finish_failed(
                    repository,
                    run_id=run["id"],
                    error_message=str(exc),
                    last_http_status=last_http_status,
                    retry_count=retry_count,
                    throttle_triggered=throttle_triggered,
                ),
                "catalog_name": catalog_name,
                "entry_count": 0,
            },
            official_identifier=None,
            source_snapshot_hash=source_snapshot_hash,
            bdns_result="failed",
            page_count=0,
            pagination_limit_reached=False,
            sample_identifiers=[],
        )


def preview_bdns_concessions(
    *,
    num_conv: str,
    page_size: int,
    concessions_payload: bytes | None = None,
    fetcher: Callable | None = None,
    vpd: str = "GE",
    include_beneficiary_fields: bool = False,
) -> dict:
    num_conv = validate_bdns_num_conv(num_conv)
    validate_bdns_limit(page_size, option_name="page-size")
    source_url = build_bdns_concessions_search_url(
        num_conv=num_conv,
        page_size=page_size,
        vpd=vpd,
    )
    last_http_status = 200 if concessions_payload is not None else None
    retry_count = 0
    throttle_triggered = False
    try:
        if concessions_payload is None:
            if fetcher is not None:
                concessions_payload = fetcher(
                    num_conv=num_conv,
                    page=1,
                    page_size=page_size,
                    vpd=vpd,
                )
                last_http_status = getattr(fetcher, "last_http_status", 200)
            else:
                response = BDNSClient().fetch_concessions_search(
                    num_conv=num_conv,
                    page=1,
                    page_size=page_size,
                    vpd=vpd,
                )
                concessions_payload = response.content
                last_http_status = response.status_code
                retry_count = response.audit.retry_count
                throttle_triggered = response.audit.throttle_triggered
        page = parse_bdns_concession_page(
            concessions_payload,
            source_url=source_url,
            include_beneficiary_fields=include_beneficiary_fields,
        )
        return _with_bdns_metadata(
            {
                "status": "success",
                "documents_fetched": 0,
                "documents_new": 0,
                "documents_updated": 0,
                "retry_count": retry_count,
                "throttle_triggered": throttle_triggered,
                "last_http_status": last_http_status or 200,
                "error_message": None,
                "catalog_name": None,
                "entry_count": len(page.concessions),
            },
            official_identifier=None,
            source_snapshot_hash=page.source_snapshot_hash,
            bdns_result="success" if page.status == "success" else "no_results",
            page_count=1,
            pagination_limit_reached=False,
            sample_identifiers=[entry.external_id for entry in page.concessions[:5]],
        )
    except Exception as exc:
        return _with_bdns_metadata(
            {
                "status": "failed",
                "documents_fetched": 0,
                "documents_new": 0,
                "documents_updated": 0,
                "retry_count": retry_count,
                "throttle_triggered": throttle_triggered,
                "last_http_status": last_http_status,
                "error_message": str(exc),
                "catalog_name": None,
                "entry_count": 0,
            },
            official_identifier=None,
            source_snapshot_hash=None,
            bdns_result="failed",
            page_count=0,
            pagination_limit_reached=False,
            sample_identifiers=[],
        )


def ingest_bdns_concessions(
    repository: OfficialSourcesRepository,
    *,
    num_conv: str,
    page_size: int,
    max_pages: int,
    fetcher: Callable | None = None,
    vpd: str = "GE",
    include_beneficiary_fields: bool = False,
) -> dict:
    num_conv = validate_bdns_num_conv(num_conv)
    validate_bdns_limit(page_size, option_name="page-size")
    validate_bdns_max_pages(max_pages)
    run = repository.create_ingestion_run(
        source_code="BDNS",
        target_date=f"concesiones:{num_conv}",
    )
    documents_fetched = 0
    documents_new = 0
    documents_updated = 0
    source_snapshot_hash: str | None = None
    last_http_status = None
    retry_count = 0
    throttle_triggered = False
    page_count = 0
    pagination_limit_reached = False
    bdns_result = "no_results"
    sample_identifiers: list[str] = []
    try:
        for page_number in range(1, max_pages + 1):
            source_url = build_bdns_concessions_search_url(
                num_conv=num_conv,
                page=page_number,
                page_size=page_size,
                vpd=vpd,
            )
            if fetcher is not None:
                payload = fetcher(
                    num_conv=num_conv,
                    page=page_number,
                    page_size=page_size,
                    vpd=vpd,
                )
                last_http_status = getattr(fetcher, "last_http_status", 200)
            else:
                response = BDNSClient().fetch_concessions_search(
                    num_conv=num_conv,
                    page=page_number,
                    page_size=page_size,
                    vpd=vpd,
                )
                payload = response.content
                last_http_status = response.status_code
                retry_count += response.audit.retry_count
                throttle_triggered = throttle_triggered or response.audit.throttle_triggered
            page = parse_bdns_concession_page(
                payload,
                source_url=source_url,
                include_beneficiary_fields=include_beneficiary_fields,
            )
            page_count += 1
            source_snapshot_hash = page.source_snapshot_hash
            if page.status == NO_RESULTS_STATUS:
                break
            bdns_result = "success"
            for concession in page.concessions:
                existing = repository.get_bdns_concession_entry(concession.concession_code)
                record = repository.upsert_bdns_concession_entry(
                    concession_code=concession.concession_code,
                    external_id=concession.external_id,
                    call_identifier=concession.call_identifier,
                    source_url=page.source_url,
                    source_snapshot_hash=page.source_snapshot_hash,
                    raw_metadata=concession.raw_metadata,
                    ingestion_run_id=run["id"],
                )
                documents_fetched += 1
                if existing is None:
                    documents_new += 1
                elif existing["content_hash"] != record["content_hash"]:
                    documents_updated += 1
                if len(sample_identifiers) < 5:
                    sample_identifiers.append(record["external_id"])
            if page.last:
                break
            if page_number == max_pages:
                pagination_limit_reached = True
        run_record = repository.finish_ingestion_run(
            run_id=run["id"],
            status="success",
            documents_fetched=documents_fetched,
            documents_new=documents_new,
            documents_updated=documents_updated,
            retry_count=retry_count,
            throttle_triggered=throttle_triggered,
            last_http_status=last_http_status or 200,
        )
        return _with_bdns_metadata(
            {
                **run_record,
                "catalog_name": None,
                "entry_count": documents_fetched,
            },
            official_identifier=f"BDNS:{num_conv}",
            source_snapshot_hash=source_snapshot_hash,
            bdns_result=bdns_result,
            page_count=page_count,
            pagination_limit_reached=pagination_limit_reached,
            sample_identifiers=sample_identifiers,
        )
    except Exception as exc:
        return _with_bdns_metadata(
            {
                **_finish_failed(
                    repository,
                    run_id=run["id"],
                    error_message=str(exc),
                    last_http_status=last_http_status,
                    retry_count=retry_count,
                    throttle_triggered=throttle_triggered,
                ),
                "catalog_name": None,
                "entry_count": documents_fetched,
            },
            official_identifier=f"BDNS:{num_conv}",
            source_snapshot_hash=source_snapshot_hash,
            bdns_result="failed",
            page_count=page_count,
            pagination_limit_reached=pagination_limit_reached,
            sample_identifiers=sample_identifiers,
        )


def _scoped_catalog_code(
    *,
    catalog_name: str,
    code: str,
    id_admon: str | None,
) -> str:
    if catalog_name == "organos" and id_admon:
        return f"{id_admon.upper()}:{code}"
    return code


def _catalog_entry_raw_metadata(
    raw_metadata: dict,
    *,
    catalog_name: str,
    id_admon: str | None,
) -> dict:
    if catalog_name == "organos" and id_admon:
        return {
            **raw_metadata,
            "id_admon": id_admon.upper(),
            "bdns_catalog_code": raw_metadata.get("codigo")
            or raw_metadata.get("codigoBDNS")
            or raw_metadata.get("codigoBdns")
            or raw_metadata.get("id")
            or raw_metadata.get("clave"),
        }
    return raw_metadata


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
    page_count: int,
    pagination_limit_reached: bool,
    bdns_result: str,
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
        bdns_result=bdns_result,
        page_count=page_count,
        pagination_limit_reached=pagination_limit_reached,
        sample_identifiers=[call.official_identifier for call in page.calls[:5]],
    )


def _upsert_call(
    repository: OfficialSourcesRepository,
    *,
    source_id: int,
    call: BDNSCallMetadata,
) -> dict:
    raw_metadata = _with_catalog_enrichment(repository, call.raw_metadata)
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
        raw_metadata=raw_metadata,
    )


def _with_catalog_enrichment(
    repository: OfficialSourcesRepository,
    raw_metadata: dict,
) -> dict:
    source_metadata = raw_metadata.get("source_metadata")
    if not isinstance(source_metadata, dict):
        return raw_metadata
    enrichment: dict[str, list[dict[str, str]]] = {}
    for source_field, catalog_name in _BDNS_CALL_CATALOG_FIELDS.items():
        matches = _resolve_catalog_matches(
            repository,
            catalog_name=catalog_name,
            items=source_metadata.get(source_field),
        )
        if matches:
            enrichment[catalog_name] = matches
    if not enrichment:
        return raw_metadata
    return {
        **raw_metadata,
        "catalog_enrichment": enrichment,
    }


_BDNS_CALL_CATALOG_FIELDS = {
    "instrumentos": "instrumentos",
    "tiposBeneficiarios": "beneficiarios",
    "sectores": "sectores",
    "regiones": "regiones",
}


def _resolve_catalog_matches(
    repository: OfficialSourcesRepository,
    *,
    catalog_name: str,
    items: object,
) -> list[dict[str, str]]:
    if not isinstance(items, list):
        return []
    matches: list[dict[str, str]] = []
    seen_codes: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            continue
        code = _catalog_item_code(item)
        if not code or code in seen_codes:
            continue
        seen_codes.add(code)
        entry = repository.get_bdns_catalog_entry(catalog_name, code)
        if entry is None:
            continue
        matches.append(
            {
                "catalog_name": entry["catalog_name"],
                "code": entry["code"],
                "name": entry["name"],
                "external_id": entry["external_id"],
            }
        )
    return matches


def _catalog_item_code(item: dict) -> str | None:
    for key in ("codigo", "codigoBDNS", "codigoBdns", "id", "clave"):
        value = item.get(key)
        if value is not None:
            text = str(value).strip()
            if text:
                return text
    return None


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
    bdns_result: str,
    page_count: int,
    pagination_limit_reached: bool,
    sample_identifiers: list[str],
) -> dict:
    return {
        **run_record,
        "official_identifier": official_identifier,
        "source_snapshot_hash": source_snapshot_hash,
        "bdns_result": bdns_result,
        "page_count": page_count,
        "pagination_limit_reached": pagination_limit_reached,
        "sample_identifiers": sample_identifiers,
    }


def _classify_bdns_error(exc: Exception) -> str:
    if isinstance(exc, BDNSNotFoundError):
        return "not_found"
    return "failed"
