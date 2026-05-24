from __future__ import annotations

import inspect
import json

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
        "list_sources",
        "get_source_status",
        "list_monitorable_sources",
        "list_latest_discovery_entries",
        "boe_consolidated_law_get",
        "boe_consolidated_law_text_get",
        "boe_consolidated_law_index_get",
        "boe_consolidated_law_block_get",
        "boe_consolidated_law_citation_build",
        "boe_consolidated_law_block_citation_build",
    } == set(MCP_TOOL_NAMES)
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


def test_missing_boe_summary_returns_structured_cache_miss(repository):
    result = tools.boe_summary_search(
        repository,
        date_from="2024-05-29",
        date_to="2024-05-29",
    )

    assert result["status"] == "cache_miss"
    assert result["resource_type"] == "boe_summary"
    assert result["date"] == "2024-05-29"
    assert "Run controlled BOE ingestion" in result["recommended_action"]


def test_missing_document_returns_structured_cache_miss(repository):
    result = tools.boe_document_get(repository, external_id="BOE-A-2024-99999")

    assert result["status"] == "cache_miss"
    assert result["resource_type"] == "official_document"
    assert result["official_identifier"] == "BOE-A-2024-99999"
    assert "recommended_action" in result


def test_missing_document_text_returns_cache_miss_without_live_fetch(repository):
    source = repository.get_source_by_code("BOE")
    repository.upsert_document(
        source_id=source["id"],
        external_id="BOE-A-2024-11111",
        publication_date="2024-05-29",
        title="Document without cached text",
    )

    result = tools.boe_document_text_get(repository, external_id="BOE-A-2024-11111")

    assert result["status"] == "cache_miss"
    assert result["resource_type"] == "official_document_text"
    assert "Download XML or HTML artifacts" in result["recommended_action"]


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


def test_mcp_source_coverage_list_returns_registered_sources():
    result = tools.list_sources()

    assert result["resource_type"] == "source_coverage"
    assert result["count"] == 22
    source_codes = {source["source_code"] for source in result["sources"]}
    assert {"BOE", "BOCYL", "DOUE"}.issubset(source_codes)
    bocyl = next(source for source in result["sources"] if source["source_code"] == "BOCYL")
    assert bocyl == {
        "source_code": "BOCYL",
        "name": "Boletin Oficial de Castilla y Leon",
        "jurisdiction_level": "autonómica",
        "operational_status": "metadata_adapter_validated",
        "monitor_support": "available",
        "evidence_adapter": True,
    }


def test_mcp_source_status_returns_bocyl_and_safety_flags():
    result = tools.get_source_status(source_code="BOCYL")

    assert result["status"] == "ok"
    assert result["source"]["source_code"] == "BOCYL"
    assert result["source"]["candidate_creation_allowed"] is False
    assert result["source"]["evidence_grade_allowed"] is False
    assert result["safety"] == {
        "candidate_creation_allowed": False,
        "evidence_grade_allowed": False,
        "rss_discovery_is_evidence": False,
        "rss_discovery_is_candidate": False,
    }


def test_mcp_source_status_exposes_inventory_only_sources_as_inventory_only():
    result = tools.get_source_status(source_code="DOUE")

    assert result["status"] == "ok"
    assert result["source"]["source_code"] == "DOUE"
    assert result["source"]["operational_status"] == "inventory_only"
    assert result["source"]["monitor_support"] == "none"


def test_mcp_source_status_unknown_source_returns_safe_error():
    result = tools.get_source_status(source_code="NOPE")

    assert result == {
        "status": "unknown_source",
        "source_code": "NOPE",
        "message": "Unknown source_code: NOPE",
    }


def test_mcp_list_monitorable_sources_exposes_access_methods_without_live_fetch():
    result = tools.list_monitorable_sources()

    assert result["resource_type"] == "monitorable_sources"
    bocyl = next(source for source in result["sources"] if source["source_code"] == "BOCYL")
    method_types = {method["type"] for method in bocyl["access_methods"]}
    assert "rss" in method_types
    assert "json" not in method_types
    assert bocyl["operational_status"] == "metadata_adapter_validated"
    assert all(source["operational_status"] != "inventory_only" for source in result["sources"])


def test_mcp_list_monitorable_sources_includes_expanded_feed_sources():
    result = tools.list_monitorable_sources()

    sources = {source["source_code"]: source for source in result["sources"]}
    boe_method_types = {method["type"] for method in sources["BOE"]["access_methods"]}
    boja_method_types = {method["type"] for method in sources["BOJA"]["access_methods"]}

    assert "rss" in boe_method_types
    assert "atom" in boja_method_types


def test_mcp_latest_discovery_entries_reads_existing_jsonl_only(tmp_path):
    output_path = tmp_path / "BOCYL" / "2026-05-24" / "rss_discovery.jsonl"
    output_path.parent.mkdir(parents=True)
    record = {
        "source_code": "BOCYL",
        "feed_url": "https://bocyl.jcyl.es/rss.do",
        "feed_format": "rss",
        "entry_id": "entry-1",
        "title": "Entry 1",
        "published_at": "2026-05-24T00:00:00Z",
        "updated_at": None,
        "official_url": "https://bocyl.jcyl.es/entry-1",
        "summary": "metadata-only",
        "raw_feed_hash": "raw",
        "entry_hash": "entry",
        "discovered_at": "2026-05-24T00:00:00Z",
        "monitor_run_id": "run-1",
        "classification_status": "unclassified",
        "evidence_status": "not_evidence",
        "candidate_status": "not_candidate",
    }
    output_path.write_text(json.dumps(record, sort_keys=True) + "\n", encoding="utf-8")

    result = tools.list_latest_discovery_entries(
        source_code="BOCYL",
        date="2026-05-24",
        output_root=tmp_path,
    )

    assert result["status"] == "ok"
    assert result["source_code"] == "BOCYL"
    assert result["date"] == "2026-05-24"
    assert result["count"] == 1
    assert result["entries"] == [record]


def test_mcp_latest_discovery_entries_missing_output_returns_empty_safe_result(tmp_path):
    result = tools.list_latest_discovery_entries(
        source_code="BOCYL",
        date="2026-05-24",
        output_root=tmp_path,
    )

    assert result == {
        "status": "empty",
        "source_code": "BOCYL",
        "date": "2026-05-24",
        "output_path": str(tmp_path / "BOCYL" / "2026-05-24" / "rss_discovery.jsonl"),
        "entries": [],
        "count": 0,
        "message": "No RSS discovery output exists for this source/date.",
    }


def test_mcp_latest_discovery_entries_unknown_source_returns_safe_error(tmp_path):
    result = tools.list_latest_discovery_entries(source_code="NOPE", output_root=tmp_path)

    assert result == {
        "status": "unknown_source",
        "source_code": "NOPE",
        "message": "Unknown source_code: NOPE",
    }


def test_mcp_source_coverage_tools_do_not_import_write_path_modules():
    source = inspect.getsource(tools)

    assert "create_source_candidate" not in source
    assert "write_jsonl" not in source
    assert "fetch_feed" not in source
    assert "artifacts" not in source
