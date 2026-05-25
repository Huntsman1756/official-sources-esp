from __future__ import annotations

from official_sources import source_coverage
from official_sources.api import queries
from official_sources.citation.builder import build_consolidated_law_citation
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
