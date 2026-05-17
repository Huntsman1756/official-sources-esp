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
        raise KeyError(f"Unknown document: {external_id}")
    return document


def get_document_text(repository: OfficialSourcesRepository, external_id: str) -> dict:
    document = get_document(repository, external_id)
    text = repository.get_document_text(document["id"])
    if text is None:
        raise KeyError(f"No text stored for document: {external_id}")
    return text


def get_citation(repository: OfficialSourcesRepository, external_id: str) -> dict:
    return build_citation(repository, external_id)


def get_trace(repository: OfficialSourcesRepository, external_id: str) -> dict:
    document = get_document(repository, external_id)
    return {
        "document": document,
        "files": repository.list_document_files(document["id"]),
    }


def get_integrity(repository: OfficialSourcesRepository, external_id: str) -> dict:
    return get_integrity_status(repository, external_id)
