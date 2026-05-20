from __future__ import annotations

from official_sources.storage.repository import OfficialSourcesRepository


def build_citation(repository: OfficialSourcesRepository, external_id: str) -> dict:
    document = repository.get_document_by_external_id(external_id)
    if document is None:
        raise KeyError(f"Unknown document: {external_id}")
    source_url = document["url_html"] or document["url_xml"] or document["url_pdf"]
    return {
        "source_code": document["source_code"],
        "source_name": document["source_name"],
        "external_id": document["external_id"],
        "title": document["title"],
        "publication_date": document["publication_date"],
        "source_url": source_url,
        "official_url": source_url,
        "pdf_url": document["url_pdf"],
        "citation": (
            f"{document['source_code']} {document['external_id']}, "
            f"{document['publication_date']}, {document['title']}"
        ),
    }


def build_consolidated_law_citation(
    repository: OfficialSourcesRepository,
    official_identifier: str,
    *,
    block_identifier: str | None = None,
) -> dict:
    law = repository.get_consolidated_law_by_identifier(official_identifier)
    if law is None:
        raise KeyError(f"Unknown consolidated law: {official_identifier}")
    versions = repository.list_consolidated_law_versions(law["id"])
    version = versions[-1] if versions else None
    result = {
        "source_code": law["source_code"],
        "resource_type": "consolidated_law",
        "official_identifier": law["official_identifier"],
        "title": law["title"],
        "version_date": version["version_date"] if version else None,
        "publication_date": law["publication_date"],
        "official_url": law["official_url"],
        "retrieved_at": version["updated_at"] if version else law["updated_at"],
    }
    if block_identifier is not None:
        block = repository.get_consolidated_law_text_block(law["id"], block_identifier)
        if block is None:
            raise KeyError(f"Unknown consolidated law block: {block_identifier}")
        block_version = None
        for candidate in versions:
            if candidate["id"] == block["version_id"]:
                block_version = candidate
                break
        result.update(
            {
                "resource_type": "consolidated_law_block",
                "law_title": law["title"],
                "version_date": (
                    block_version["version_date"] if block_version else result["version_date"]
                ),
                "block_id": block["official_block_id"] or block["block_identifier"],
                "block_type": block["block_type"],
                "block_identifier": block["block_identifier"],
                "block_title": block["title"],
                "official_url": block["api_url"] or result["official_url"],
                "retrieved_at": block["updated_at"],
            }
        )
    return result
