from __future__ import annotations

from official_sources.citation.builder import build_citation, build_consolidated_law_citation


def test_citation_generation(repository):
    source = repository.get_source_by_code("BOE")
    document = repository.upsert_document(
        source_id=source["id"],
        external_id="BOE-A-2024-11111",
        publication_date="2024-05-29",
        title="Document title",
        url_html="https://www.boe.es/diario_boe/txt.php?id=BOE-A-2024-11111",
    )

    citation = build_citation(repository, document["external_id"])

    assert citation["source_code"] == "BOE"
    assert citation["external_id"] == "BOE-A-2024-11111"
    assert citation["source_url"].startswith("https://www.boe.es/")


def test_citation_metadata_and_integrity_metadata_are_separate_concerns(repository):
    source = repository.get_source_by_code("BOE")
    document = repository.upsert_document(
        source_id=source["id"],
        external_id="BOE-A-2024-11111",
        publication_date="2024-05-29",
        title="Document title",
    )
    repository.upsert_document_file(
        document_id=document["id"],
        file_type="xml",
        official_url="https://www.boe.es/diario_boe/xml.php?id=BOE-A-2024-11111",
        payload=b"<xml/>",
        ingestion_run_id=None,
    )

    citation = build_citation(repository, document["external_id"])

    assert "sha256" not in citation
    assert "source_snapshot_hash" not in citation


def test_consolidated_law_block_citation_includes_official_block_metadata(repository):
    source = repository.get_source_by_code("BOE")
    law = repository.upsert_consolidated_law(
        source_id=source["id"],
        external_id="BOE-A-2024-11111",
        official_identifier="BOE-A-2024-11111",
        title="Test consolidated law",
        law_type=None,
        jurisdiction="state",
        department=None,
        publication_date="2024-05-29",
        consolidation_status="finalizado",
        official_url="https://www.boe.es/buscar/act.php?id=BOE-A-2024-11111",
        raw_metadata={},
    )
    version = repository.upsert_consolidated_law_version(
        consolidated_law_id=law["id"],
        version_identifier="BOE-A-2024-11111:block:a1",
        version_date="2024-05-30",
        valid_from=None,
        valid_to=None,
        is_current=True,
        official_url="https://www.boe.es/datosabiertos/api/legislacion-consolidada/id/BOE-A-2024-11111/texto/bloque/a1",
        raw_payload_hash="abc",
        source_snapshot_hash="abc",
    )
    repository.upsert_consolidated_law_text_block(
        consolidated_law_id=law["id"],
        version_id=version["id"],
        official_block_id="a1",
        block_type="article",
        block_identifier="Article 1",
        title="Article 1",
        content="Official text",
        content_sha256="hash",
        source_snapshot_hash="abc",
        order_index=0,
        parent_block_id=None,
        block_path="a1",
        api_url="https://www.boe.es/datosabiertos/api/legislacion-consolidada/id/BOE-A-2024-11111/texto/bloque/a1",
        raw_payload_hash="abc",
    )

    citation = build_consolidated_law_citation(
        repository,
        "BOE-A-2024-11111",
        block_identifier="a1",
    )

    assert citation["source_code"] == "BOE"
    assert citation["resource_type"] == "consolidated_law_block"
    assert citation["official_identifier"] == "BOE-A-2024-11111"
    assert citation["law_title"] == "Test consolidated law"
    assert citation["version_date"] == "2024-05-30"
    assert citation["block_id"] == "a1"
    assert citation["block_type"] == "article"
    assert citation["block_identifier"] == "Article 1"
    assert citation["block_title"] == "Article 1"
    assert citation["official_url"].endswith("/texto/bloque/a1")
