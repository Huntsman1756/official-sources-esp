from __future__ import annotations

from official_sources.storage.repository import OfficialSourcesRepository


def get_integrity_status(repository: OfficialSourcesRepository, external_id: str) -> dict:
    document = repository.get_document_by_external_id(external_id)
    if document is None:
        raise KeyError(f"Unknown document: {external_id}")
    files = []
    for file_record in repository.list_document_files(document["id"]):
        files.append(
            {
                "file_id": file_record["id"],
                "file_type": file_record["file_type"],
                "sha256": file_record["sha256"],
                "source_snapshot_hash": file_record["source_snapshot_hash"],
                "signature_status": file_record["signature_status"],
                "last_integrity_check_at": file_record["last_integrity_check_at"],
                "content_changed_at": file_record["content_changed_at"],
                "previous_hash": file_record["previous_hash"],
                "change_detected_by": file_record["change_detected_by"],
            }
        )
    return {
        "external_id": document["external_id"],
        "source_code": document["source_code"],
        "files": files,
    }
