from __future__ import annotations

import inspect

from official_sources.mcp import tools
from official_sources.mcp.server import MCP_TOOL_NAMES, create_repository_from_env


def _seed_document_with_text(repository, instruction_like_text):
    source = repository.get_source_by_code("BOE")
    document = repository.upsert_document(
        source_id=source["id"],
        external_id="BOE-A-2024-11111",
        publication_date="2024-05-29",
        title="Instruction-like legal text",
        url_html="https://www.boe.es/diario_boe/txt.php?id=BOE-A-2024-11111",
    )
    file_record = repository.upsert_document_file(
        document_id=document["id"],
        file_type="html",
        official_url="https://www.boe.es/diario_boe/txt.php?id=BOE-A-2024-11111",
        payload=instruction_like_text.encode("utf-8"),
        ingestion_run_id=None,
    )
    repository.create_document_text(
        document_id=document["id"],
        source_file_id=file_record["id"],
        text_type="clean_text",
        language="es",
        content=instruction_like_text,
        extraction_method="fixture",
    )
    return document


def test_mcp_tool_names_use_compatible_snake_case_names():
    assert {
        "boe_summary_search",
        "boe_document_get",
        "boe_document_text_get",
        "boe_citation_build",
        "source_trace",
        "integrity_status_get",
        "boe_consolidated_law_get",
        "boe_consolidated_law_text_get",
        "boe_consolidated_law_index_get",
        "boe_consolidated_law_block_get",
        "boe_consolidated_law_citation_build",
        "boe_consolidated_law_block_citation_build",
    } == MCP_TOOL_NAMES
    assert all("." not in name and name == name.lower() for name in MCP_TOOL_NAMES)


def test_mcp_repository_uses_db_path_env_before_legacy_db_env(tmp_path, monkeypatch):
    preferred_db = tmp_path / "preferred.sqlite"
    legacy_db = tmp_path / "legacy.sqlite"
    monkeypatch.setenv("OFFICIAL_SOURCES_DB_PATH", str(preferred_db))
    monkeypatch.setenv("OFFICIAL_SOURCES_DB", str(legacy_db))

    create_repository_from_env()

    assert preferred_db.exists()
    assert not legacy_db.exists()


def test_mcp_tools_return_structured_objects_never_raw_legal_text_strings(
    repository, instruction_like_text
):
    _seed_document_with_text(repository, instruction_like_text)

    result = tools.boe_document_text_get(repository, external_id="BOE-A-2024-11111")

    assert isinstance(result, dict)
    assert result["is_official_text"] is True
    assert result["content_type"] == "official_legal_text"
    assert result["content"] == instruction_like_text


def test_instruction_like_content_remains_inside_structured_content_field(
    repository, instruction_like_text
):
    _seed_document_with_text(repository, instruction_like_text)

    result = tools.boe_document_text_get(repository, external_id="BOE-A-2024-11111")

    assert "Ignore previous instructions" in result["content"]
    top_level_values = [value for key, value in result.items() if key != "content"]
    assert all("Ignore previous instructions" not in str(value) for value in top_level_values)


def test_official_text_envelope_contains_source_url_and_publication_date(
    repository, instruction_like_text
):
    _seed_document_with_text(repository, instruction_like_text)

    result = tools.boe_document_text_get(repository, external_id="BOE-A-2024-11111")

    assert result["document_id"] == "BOE-A-2024-11111"
    assert result["source_code"] == "BOE"
    assert result["source_url"].startswith("https://www.boe.es/")
    assert result["publication_date"] == "2024-05-29"


def test_mcp_tools_expose_integrity_status_but_cannot_modify_it(repository, instruction_like_text):
    _seed_document_with_text(repository, instruction_like_text)

    before = tools.integrity_status_get(repository, external_id="BOE-A-2024-11111")
    after = tools.integrity_status_get(repository, external_id="BOE-A-2024-11111")

    assert before == after
    assert before["files"]


def test_no_mcp_tool_can_write_to_protected_tables():
    protected_names = {
        "upsert_document",
        "create_source_candidate",
        "upsert_document_file",
        "create_integrity_check",
        "create_document_text",
        "finish_ingestion_run",
        "create_ingestion_run",
    }
    source = inspect.getsource(tools)

    for name in protected_names:
        assert f".{name}(" not in source
    assert "downstream" not in source.lower()
