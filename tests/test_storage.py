from __future__ import annotations

from datetime import UTC, datetime

from official_sources.integrity.hashing import sha256_bytes


def test_official_source_creation(repository):
    source = repository.get_source_by_code("BOE")

    assert source["code"] == "BOE"
    assert source["jurisdiction"] == "state"
    assert source["region_code"] == "ES"
    assert source["access_type"] == "official_api"
    assert source["reliability_level"] == "canonical"


def test_signature_status_defaults_to_not_checked(repository):
    source = repository.get_source_by_code("BOE")
    document = repository.upsert_document(
        source_id=source["id"],
        external_id="BOE-A-2024-11111",
        publication_date="2024-05-29",
        title="Document",
    )

    file_record = repository.upsert_document_file(
        document_id=document["id"],
        file_type="xml",
        official_url="https://www.boe.es/diario_boe/xml.php?id=BOE-A-2024-11111",
        payload=b"<xml/>",
        ingestion_run_id=None,
    )

    assert file_record["signature_status"] == "not_checked"


def test_candidate_default_review_status_is_human_review_required(repository):
    source = repository.get_source_by_code("BOE")
    document = repository.upsert_document(
        source_id=source["id"],
        external_id="BOE-A-2024-11111",
        publication_date="2024-05-29",
        title="Document",
    )

    candidate = repository.create_source_candidate(
        document_id=document["id"],
        project_key="test",
        candidate_type="aid",
        extraction_status="raw_detected",
        evidence_level="official_document_found",
        matched_fields={},
    )

    assert candidate["review_status"] == "human_review_required"


def test_ingestion_run_is_created_for_failed_attempt(repository):
    run = repository.create_ingestion_run(source_code="BOE", target_date="2024-05-29")
    repository.finish_ingestion_run(
        run_id=run["id"],
        status="failed",
        error_message="network unavailable",
        documents_fetched=0,
        documents_new=0,
        documents_updated=0,
    )

    finished = repository.get_ingestion_run(run["id"])

    assert finished["status"] == "failed"
    assert finished["error_message"] == "network unavailable"
    assert finished["finished_at"] is not None


def test_hash_change_preserves_previous_hash_and_records_audit_event(repository):
    source = repository.get_source_by_code("BOE")
    document = repository.upsert_document(
        source_id=source["id"],
        external_id="BOE-A-2024-11111",
        publication_date="2024-05-29",
        title="Document",
    )
    run_one = repository.create_ingestion_run(source_code="BOE", target_date="2024-05-29")
    first = repository.upsert_document_file(
        document_id=document["id"],
        file_type="xml",
        official_url="https://www.boe.es/diario_boe/xml.php?id=BOE-A-2024-11111",
        payload=b"first payload",
        ingestion_run_id=run_one["id"],
    )

    run_two = repository.create_ingestion_run(source_code="BOE", target_date="2024-05-30")
    second = repository.upsert_document_file(
        document_id=document["id"],
        file_type="xml",
        official_url="https://www.boe.es/diario_boe/xml.php?id=BOE-A-2024-11111",
        payload=b"second payload",
        ingestion_run_id=run_two["id"],
    )
    checks = repository.list_integrity_checks(document_file_id=first["id"])

    assert second["previous_hash"] == sha256_bytes(b"first payload")
    assert second["sha256"] == sha256_bytes(b"second payload")
    assert second["content_changed_at"] is not None
    assert second["change_detected_by"] == run_two["id"]
    assert checks[-1]["previous_sha256"] == sha256_bytes(b"first payload")
    assert checks[-1]["current_sha256"] == sha256_bytes(b"second payload")
    assert checks[-1]["changed"] == 1


def test_updated_timestamps_are_utc_iso_strings(repository):
    source = repository.get_source_by_code("BOE")
    parsed = datetime.fromisoformat(source["created_at"])

    assert parsed.tzinfo == UTC
