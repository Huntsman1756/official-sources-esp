from __future__ import annotations

from official_sources.citation.builder import build_citation
from official_sources.integrity.service import get_integrity_status
from official_sources.storage.repository import OfficialSourcesRepository


def search_documents(
    repository: OfficialSourcesRepository,
    *,
    keyword: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 20,
) -> list[dict]:
    return repository.search_documents(
        keyword=keyword,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
    )


def get_document(repository: OfficialSourcesRepository, external_id: str) -> dict:
    document = repository.get_document_by_external_id(external_id)
    if document is None:
        return cache_miss(
            resource_type="official_document",
            official_identifier=external_id,
            recommended_action=(
                "Ingest the corresponding BOE summary date or fetch by official identifier "
                "if supported"
            ),
        )
    return document


def get_document_text(repository: OfficialSourcesRepository, external_id: str) -> dict:
    document = get_document(repository, external_id)
    if document.get("status") == "cache_miss":
        return document
    text = repository.get_document_text(document["id"])
    if text is None:
        return cache_miss(
            resource_type="official_document_text",
            official_identifier=external_id,
            recommended_action="Download XML or HTML artifacts for this document",
        )
    return text


def get_citation(repository: OfficialSourcesRepository, external_id: str) -> dict:
    if repository.get_document_by_external_id(external_id) is None:
        return cache_miss(
            resource_type="official_document",
            official_identifier=external_id,
            recommended_action=(
                "Ingest the corresponding BOE summary date or fetch by official identifier "
                "if supported"
            ),
        )
    return build_citation(repository, external_id)


def get_trace(repository: OfficialSourcesRepository, external_id: str) -> dict:
    document = get_document(repository, external_id)
    if document.get("status") == "cache_miss":
        return document
    return {
        "document": document,
        "files": repository.list_document_files(document["id"]),
    }


def get_integrity(repository: OfficialSourcesRepository, external_id: str) -> dict:
    if repository.get_document_by_external_id(external_id) is None:
        return cache_miss(
            resource_type="official_document",
            official_identifier=external_id,
            recommended_action=(
                "Ingest the corresponding BOE summary date or fetch by official identifier "
                "if supported"
            ),
        )
    return get_integrity_status(repository, external_id)


def cache_miss(
    *,
    resource_type: str,
    recommended_action: str,
    date: str | None = None,
    official_identifier: str | None = None,
) -> dict:
    result = {
        "status": "cache_miss",
        "resource_type": resource_type,
        "recommended_action": recommended_action,
    }
    if date is not None:
        result["date"] = date
    if official_identifier is not None:
        result["official_identifier"] = official_identifier
    return result
