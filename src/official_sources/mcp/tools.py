from __future__ import annotations

import json

from official_sources import source_coverage
from official_sources.api import queries
from official_sources.citation.builder import build_consolidated_law_citation
from official_sources.sources.bdns.business import filter_bdns_business_grants
from official_sources.sources.bdns.client import validate_bdns_catalog_name, validate_bdns_num_conv
from official_sources.sources.boe.consolidated import (
    validate_consolidated_block_id,
    validate_consolidated_identifier,
)
from official_sources.storage.repository import OfficialSourcesRepository


def boe_summary_search(
    repository: OfficialSourcesRepository,
    *,
    keyword: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 20,
) -> dict:
    documents = queries.search_documents(
        repository,
        keyword=keyword,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
    )
    if not documents and date_from and date_from == date_to:
        summary_run = repository.get_latest_summary_ingestion_run("BOE", date_from)
        if summary_run is None:
            return queries.cache_miss(
                resource_type="boe_summary",
                date=date_from,
                recommended_action="Run controlled BOE ingestion for this date",
            )
    return {
        "source_code": "BOE",
        "items": [
            {
                "document_id": item["external_id"],
                "publication_date": item["publication_date"],
                "title": item["title"],
                "source_url": item["url_html"] or item["url_xml"] or item["url_pdf"],
            }
            for item in documents
        ],
    }


def boe_document_get(repository: OfficialSourcesRepository, *, external_id: str) -> dict:
    document = queries.get_document(repository, external_id)
    if "status" in document and document["status"] == "cache_miss":
        return document
    return {
        "document_id": document["external_id"],
        "source_code": document["source_code"],
        "publication_date": document["publication_date"],
        "title": document["title"],
        "department": document["department"],
        "section": document["section"],
        "document_type": document["document_type"],
        "source_url": document["url_html"] or document["url_xml"] or document["url_pdf"],
    }


def boe_document_text_get(repository: OfficialSourcesRepository, *, external_id: str) -> dict:
    document = queries.get_document(repository, external_id)
    if "status" in document and document["status"] == "cache_miss":
        return document
    text = queries.get_document_text(repository, external_id)
    if "status" in text and text["status"] == "cache_miss":
        return text
    return {
        "document_id": document["external_id"],
        "source_code": document["source_code"],
        "source_url": document["url_html"] or document["url_xml"] or document["url_pdf"],
        "publication_date": document["publication_date"],
        "is_official_text": True,
        "content_type": "official_legal_text",
        "content": text["content"],
    }


def boe_citation_build(repository: OfficialSourcesRepository, *, external_id: str) -> dict:
    return queries.get_citation(repository, external_id)


def source_trace(repository: OfficialSourcesRepository, *, external_id: str) -> dict:
    trace = queries.get_trace(repository, external_id)
    if "status" in trace and trace["status"] == "cache_miss":
        return trace
    document = trace["document"]
    return {
        "document_id": document["external_id"],
        "source_code": document["source_code"],
        "publication_date": document["publication_date"],
        "files": [
            {
                "file_type": file_record["file_type"],
                "official_url": file_record["official_url"],
                "source_snapshot_hash": file_record["source_snapshot_hash"],
                "first_seen_at": file_record["first_seen_at"],
                "last_seen_at": file_record["last_seen_at"],
            }
            for file_record in trace["files"]
        ],
    }


def integrity_status_get(repository: OfficialSourcesRepository, *, external_id: str) -> dict:
    return queries.get_integrity(repository, external_id)


def list_sources() -> dict:
    return source_coverage.list_source_coverage()


def get_source_status(*, source_code: str) -> dict:
    return source_coverage.get_source_status(source_code=source_code)


def list_monitorable_sources() -> dict:
    return source_coverage.list_monitorable_sources()


def list_latest_discovery_entries(
    *,
    source_code: str,
    date: str | None = None,
    limit: int | None = 20,
    output_root=None,
) -> dict:
    return source_coverage.list_latest_discovery_entries(
        source_code=source_code,
        date=date,
        limit=limit,
        output_root=output_root,
    )


def preview_discovery(
    *,
    source_code: str,
    date: str,
    limit: int = 1,
    discovery_type: str | None = None,
    rss_fetcher=None,
    api_fetcher=None,
    html_fetcher=None,
) -> dict:
    return source_coverage.preview_discovery(
        source_code=source_code,
        date=date,
        limit=limit,
        discovery_type=discovery_type,
        rss_fetcher=rss_fetcher,
        api_fetcher=api_fetcher,
        html_fetcher=html_fetcher,
    )


def recommend_next_sources(*, limit: int = 5, output_root=None) -> dict:
    return source_coverage.recommend_next_sources(
        limit=limit,
        output_root=output_root,
    )


def recommend_sources_for_consumer(
    *,
    consumer: str,
    demand_class: str | None = None,
    limit: int = 5,
) -> dict:
    return source_coverage.recommend_sources_for_consumer(
        consumer=consumer,
        demand_class=demand_class,
        limit=limit,
    )


def list_downstream_integration_smokes(*, consumer: str | None = None) -> dict:
    return source_coverage.list_downstream_integration_smokes(consumer=consumer)


def check_downstream_integration_smokes(*, consumer: str | None = None) -> dict:
    return source_coverage.check_downstream_integration_smokes(consumer=consumer)


def list_case_taxonomy(
    *,
    consumer: str | None = None,
    demand_class: str | None = None,
) -> dict:
    return source_coverage.list_case_taxonomy(
        consumer=consumer,
        demand_class=demand_class,
    )


def build_evidence_packet(
    *,
    consumer: str,
    source_code: str | None = None,
    official_identifier: str | None = None,
    profile: str | None = None,
) -> dict:
    return source_coverage.build_evidence_packet(
        consumer=consumer,
        source_code=source_code,
        official_identifier=official_identifier,
        profile=profile,
    )


def resolve_normative_reference(
    *,
    consumer: str,
    topic: str,
    jurisdiction: str,
    known_title: str | None = None,
    limit: int = 10,
) -> dict:
    return source_coverage.resolve_normative_reference(
        consumer=consumer,
        topic=topic,
        jurisdiction=jurisdiction,
        known_title=known_title,
        limit=limit,
    )


def resolve_fiscal_reference(
    *,
    consumer: str,
    tax_year: int,
    jurisdiction: str,
    deduction_key: str | None = None,
    limit: int = 10,
) -> dict:
    return source_coverage.resolve_fiscal_reference(
        consumer=consumer,
        tax_year=tax_year,
        jurisdiction=jurisdiction,
        deduction_key=deduction_key,
        limit=limit,
    )


def bdns_grant_calls_list(
    repository: OfficialSourcesRepository,
    *,
    limit: int = 20,
) -> dict:
    bounded_limit = _bounded_limit(limit)
    documents = repository.list_bdns_grant_call_documents(limit=bounded_limit)
    return {
        "status": "ok",
        "resource_type": "bdns_grant_calls",
        "source_code": "BDNS",
        "mode": "read_only",
        "writes_performed": False,
        "count": len(documents),
        "items": [_bdns_grant_call_record(document) for document in documents],
    }


def bdns_business_grants_list(
    repository: OfficialSourcesRepository,
    *,
    min_score: float = 0.35,
    limit: int = 20,
) -> dict:
    if min_score < 0 or min_score > 1:
        raise ValueError("min_score must be between 0 and 1.")
    bounded_limit = _bounded_limit(limit)
    documents = repository.list_bdns_grant_call_documents(limit=None)
    records = filter_bdns_business_grants(
        documents,
        min_score=min_score,
        limit=bounded_limit,
    )
    return {
        "status": "ok",
        "resource_type": "bdns_business_grants",
        "source_code": "BDNS",
        "mode": "read_only",
        "writes_performed": False,
        "min_score": min_score,
        "count": len(records),
        "items": records,
    }


def bdns_catalog_entries_list(
    repository: OfficialSourcesRepository,
    *,
    catalog_name: str | None = None,
    limit: int = 50,
) -> dict:
    validated_catalog = validate_bdns_catalog_name(catalog_name) if catalog_name else None
    bounded_limit = _bounded_limit(limit, default=50)
    entries = repository.list_bdns_catalog_entries(
        catalog_name=validated_catalog,
        limit=bounded_limit,
    )
    return {
        "status": "ok",
        "resource_type": "bdns_catalog_entries",
        "source_code": "BDNS",
        "mode": "read_only",
        "writes_performed": False,
        "catalog_name": validated_catalog,
        "count": len(entries),
        "items": [_bdns_catalog_entry_record(entry) for entry in entries],
    }


def bdns_concessions_list(
    repository: OfficialSourcesRepository,
    *,
    num_conv: str | None = None,
    call_identifier: str | None = None,
    limit: int = 50,
) -> dict:
    normalized_call_identifier = _bdns_call_identifier(
        num_conv=num_conv,
        call_identifier=call_identifier,
    )
    bounded_limit = _bounded_limit(limit, default=50)
    entries = repository.list_bdns_concession_entries(
        call_identifier=normalized_call_identifier,
        limit=bounded_limit,
    )
    return {
        "status": "ok",
        "resource_type": "bdns_concessions",
        "source_code": "BDNS",
        "mode": "read_only",
        "writes_performed": False,
        "call_identifier": normalized_call_identifier,
        "count": len(entries),
        "items": [_bdns_concession_record(entry) for entry in entries],
    }


def boe_consolidated_law_get(
    repository: OfficialSourcesRepository,
    *,
    official_identifier: str,
) -> dict:
    law = repository.get_consolidated_law_by_identifier(official_identifier)
    if law is None:
        raise KeyError(f"Unknown consolidated law: {official_identifier}")
    versions = repository.list_consolidated_law_versions(law["id"])
    return {
        "resource_type": "consolidated_law",
        "official_identifier": law["official_identifier"],
        "source_code": law["source_code"],
        "title": law["title"],
        "law_type": law["law_type"],
        "jurisdiction": law["jurisdiction"],
        "department": law["department"],
        "publication_date": law["publication_date"],
        "consolidation_status": law["consolidation_status"],
        "official_url": law["official_url"],
        "versions": [
            {
                "version_identifier": version["version_identifier"],
                "version_date": version["version_date"],
                "is_current": bool(version["is_current"]),
                "official_url": version["official_url"],
                "source_snapshot_hash": version["source_snapshot_hash"],
            }
            for version in versions
        ],
    }


def boe_consolidated_law_text_get(
    repository: OfficialSourcesRepository,
    *,
    official_identifier: str,
    block_identifier: str | None = None,
) -> dict:
    law = repository.get_consolidated_law_by_identifier(official_identifier)
    if law is None:
        raise KeyError(f"Unknown consolidated law: {official_identifier}")
    versions = repository.list_consolidated_law_versions(law["id"])
    version = versions[-1] if versions else None
    if block_identifier is not None:
        block = repository.get_consolidated_law_text_block(law["id"], block_identifier)
        if block is None:
            raise KeyError(f"Unknown consolidated law block: {block_identifier}")
        content = block["content"]
    else:
        blocks = repository.list_consolidated_law_text_blocks(law["id"])
        content = "\n\n".join(block["content"] for block in blocks)
    return {
        "resource_type": "consolidated_law_text",
        "official_identifier": law["official_identifier"],
        "source_code": law["source_code"],
        "source_url": law["official_url"],
        "version_date": version["version_date"] if version else law["publication_date"],
        "is_official_text": True,
        "content_type": "official_consolidated_legal_text",
        "content": content,
    }


def boe_consolidated_law_citation_build(
    repository: OfficialSourcesRepository,
    *,
    official_identifier: str,
    block_identifier: str | None = None,
) -> dict:
    return build_consolidated_law_citation(
        repository,
        official_identifier,
        block_identifier=block_identifier,
    )


def boe_consolidated_law_index_get(
    repository: OfficialSourcesRepository,
    *,
    official_identifier: str,
) -> dict:
    official_identifier = validate_consolidated_identifier(official_identifier)
    law = repository.get_consolidated_law_by_identifier(official_identifier)
    if law is None:
        raise KeyError(f"Unknown consolidated law: {official_identifier}")
    version = _latest_version_with_marker(repository, law["id"], ":text-index")
    if version is None:
        raise KeyError(f"No consolidated law text index stored for: {official_identifier}")
    blocks = repository.list_consolidated_law_text_blocks(law["id"], version["id"])
    return {
        "resource_type": "consolidated_law_text_index",
        "official_identifier": law["official_identifier"],
        "source_code": law["source_code"],
        "source_url": version["official_url"],
        "version_date": version["version_date"],
        "is_official_text": True,
        "content_type": "official_consolidated_legal_text_index",
        "blocks": [
            {
                "block_id": block["official_block_id"] or block["block_identifier"],
                "block_type": block["block_type"],
                "block_identifier": block["block_identifier"],
                "block_title": block["title"],
                "parent_block_id": block["parent_block_id"],
                "block_path": block["block_path"],
                "source_url": block["api_url"],
                "order_index": block["order_index"],
            }
            for block in blocks
        ],
    }


def boe_consolidated_law_block_get(
    repository: OfficialSourcesRepository,
    *,
    official_identifier: str,
    block_id: str,
) -> dict:
    official_identifier = validate_consolidated_identifier(official_identifier)
    block_id = validate_consolidated_block_id(block_id)
    law = repository.get_consolidated_law_by_identifier(official_identifier)
    if law is None:
        raise KeyError(f"Unknown consolidated law: {official_identifier}")
    block = repository.get_consolidated_law_text_block(law["id"], block_id)
    if block is None:
        raise KeyError(f"Unknown consolidated law block: {block_id}")
    version = _version_by_id(repository, law["id"], block["version_id"])
    return {
        "resource_type": "consolidated_law_block",
        "official_identifier": law["official_identifier"],
        "source_code": law["source_code"],
        "source_url": block["api_url"] or version["official_url"] or law["official_url"],
        "version_date": version["version_date"] if version else law["publication_date"],
        "block_id": block["official_block_id"] or block["block_identifier"],
        "block_type": block["block_type"],
        "block_identifier": block["block_identifier"],
        "block_title": block["title"],
        "is_official_text": True,
        "content_type": "official_consolidated_legal_text_block",
        "content": block["content"],
    }


def boe_consolidated_law_block_citation_build(
    repository: OfficialSourcesRepository,
    *,
    official_identifier: str,
    block_id: str,
) -> dict:
    validate_consolidated_block_id(block_id)
    return build_consolidated_law_citation(
        repository,
        official_identifier,
        block_identifier=block_id,
    )


def _latest_version_with_marker(
    repository: OfficialSourcesRepository,
    law_id: int,
    marker: str,
) -> dict | None:
    versions = [
        version
        for version in repository.list_consolidated_law_versions(law_id)
        if marker in version["version_identifier"]
    ]
    return versions[-1] if versions else None


def _version_by_id(
    repository: OfficialSourcesRepository,
    law_id: int,
    version_id: int,
) -> dict | None:
    for version in repository.list_consolidated_law_versions(law_id):
        if version["id"] == version_id:
            return version
    return None


def _bounded_limit(value: int | None, *, default: int = 20, hard_max: int = 100) -> int:
    if value is None:
        return default
    if value < 1:
        raise ValueError("limit must be at least 1.")
    return min(value, hard_max)


def _bdns_call_identifier(
    *,
    num_conv: str | None,
    call_identifier: str | None,
) -> str | None:
    if num_conv:
        return f"BDNS:{validate_bdns_num_conv(num_conv)}"
    if not call_identifier:
        return None
    cleaned = call_identifier.strip()
    if cleaned.startswith("BDNS:"):
        validate_bdns_num_conv(cleaned.removeprefix("BDNS:"))
        return cleaned
    return f"BDNS:{validate_bdns_num_conv(cleaned)}"


def _bdns_grant_call_record(document: dict) -> dict:
    raw_metadata = json.loads(document["raw_metadata_json"] or "{}")
    return {
        "external_id": document["external_id"],
        "official_identifier": document["external_id"],
        "publication_date": document["publication_date"],
        "title": document["title"],
        "department": document["department"],
        "section": document["section"],
        "document_type": document["document_type"],
        "source_url": document["url_html"],
        "bdns_code": _dict_value(raw_metadata, "bdns_code"),
        "bdns_internal_id": _dict_value(raw_metadata, "bdns_internal_id"),
        "registration_date": _dict_value(raw_metadata, "registration_date"),
        "application_start_date": _dict_value(raw_metadata, "application_start_date"),
        "application_end_date": _dict_value(raw_metadata, "application_end_date"),
        "budget": _dict_value(raw_metadata, "budget"),
        "beneficiary_type": _dict_value(raw_metadata, "beneficiary_type") or [],
        "instrument_type": _dict_value(raw_metadata, "instrument_type") or [],
        "sector_activity": _dict_value(raw_metadata, "sector_activity") or [],
        "territorial_scope": _dict_value(raw_metadata, "territorial_scope") or [],
        "catalog_enrichment": _dict_value(raw_metadata, "catalog_enrichment") or {},
        "document_metadata": _dict_value(raw_metadata, "document_metadata") or [],
        "announcement_metadata": _dict_value(raw_metadata, "announcement_metadata") or [],
    }


def _bdns_catalog_entry_record(entry: dict) -> dict:
    return {
        "external_id": entry["external_id"],
        "catalog_name": entry["catalog_name"],
        "code": entry["code"],
        "name": entry["name"],
        "source_url": entry["source_url"],
        "source_snapshot_hash": entry["source_snapshot_hash"],
        "first_seen_at": entry["first_seen_at"],
        "last_seen_at": entry["last_seen_at"],
    }


def _bdns_concession_record(entry: dict) -> dict:
    return {
        "external_id": entry["external_id"],
        "concession_code": entry["concession_code"],
        "call_identifier": entry["call_identifier"],
        "call_code": entry["call_code"],
        "call_internal_id": entry["call_internal_id"],
        "concession_date": entry["concession_date"],
        "registration_date": entry["registration_date"],
        "amount": entry["amount"],
        "aid_equivalent": entry["aid_equivalent"],
        "instrument": entry["instrument"],
        "department": entry["department"],
        "section": entry["section"],
        "base_regulation_url": entry["base_regulation_url"],
        "source_url": entry["source_url"],
        "source_snapshot_hash": entry["source_snapshot_hash"],
        "first_seen_at": entry["first_seen_at"],
        "last_seen_at": entry["last_seen_at"],
    }


def _dict_value(data: dict, key: str):
    try:
        return data[key]
    except KeyError:
        return None
