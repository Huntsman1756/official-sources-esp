from __future__ import annotations

from official_sources.integrity.hashing import sha256_bytes
from official_sources.integrity.service import get_integrity_status


def test_stored_artifact_hashes_are_deterministic():
    assert sha256_bytes(b"same") == sha256_bytes(b"same")
    assert sha256_bytes(b"same") != sha256_bytes(b"different")


def test_integrity_status_reports_hashes_without_citation_fields(repository):
    source = repository.get_source_by_code("BOE")
    document = repository.upsert_document(
        source_id=source["id"],
        external_id="BOE-A-2024-11111",
        publication_date="2024-05-29",
        title="Document",
    )
    repository.upsert_document_file(
        document_id=document["id"],
        file_type="pdf",
        official_url="https://www.boe.es/boe/dias/2024/05/29/pdfs/BOE-A-2024-11111.pdf",
        payload=b"%PDF",
        ingestion_run_id=None,
    )

    status = get_integrity_status(repository, "BOE-A-2024-11111")

    assert status["external_id"] == "BOE-A-2024-11111"
    assert status["files"][0]["sha256"] == sha256_bytes(b"%PDF")
    assert "source_url" not in status["files"][0]
