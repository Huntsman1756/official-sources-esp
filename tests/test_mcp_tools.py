from __future__ import annotations

import inspect
import json
from pathlib import Path

from official_sources import source_coverage
from official_sources.mcp import tools
from official_sources.mcp.server import MCP_TOOL_NAMES, create_repository_from_env

FIXTURES = Path(__file__).parent / "fixtures"


def _fixture_bytes(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


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
        "preview_discovery",
        "recommend_next_sources",
        "recommend_sources_for_consumer",
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
    assert result["count"] == 65
    source_codes = {source["source_code"] for source in result["sources"]}
    assert {"BOE", "BOCYL", "DOUE", "BOP_A_CORUNA", "BOP_ZARAGOZA"}.issubset(source_codes)
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
        "api_discovery_is_evidence": False,
        "api_discovery_is_candidate": False,
        "html_discovery_is_evidence": False,
        "html_discovery_is_candidate": False,
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
    for source_code in {"BOIB", "BOC_CANTABRIA", "DOE"}:
        method_types = {method["type"] for method in sources[source_code]["access_methods"]}
        assert "rss" in method_types


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
    assert result["resource_type"] == "discovery_entries"
    assert result["discovery_types"] == ["rss"]
    assert result["source_code"] == "BOCYL"
    assert result["date"] == "2026-05-24"
    assert result["output_paths"] == {
        "rss": str(output_path),
    }
    assert result["count"] == 1
    assert result["entries"] == [record | {"discovery_type": "rss"}]


def test_mcp_latest_discovery_entries_reads_existing_api_jsonl_for_bopv(tmp_path):
    output_path = tmp_path / "BOPV" / "2026-05-24" / "api_discovery.jsonl"
    output_path.parent.mkdir(parents=True)
    record = {
        "source_code": "BOPV",
        "api_url": "https://api.euskadi.eus/bopv/administrative-acts/2026/5",
        "api_endpoint": "/bopv/administrative-acts/{year}/{month}",
        "title": "BOPV API entry",
        "published_at": "2026-05-24T00:00:00Z",
        "official_url": "https://api.euskadi.eus/bopv/administrative-acts/2026/5/2104",
        "document_id": "2026/05/2104",
        "api_id": "2026/05/2104",
        "summary": "metadata-only",
        "raw_response_hash": "raw",
        "entry_hash": "entry",
        "discovered_at": "2026-05-24T00:00:00Z",
        "monitor_run_id": "run-1",
        "classification_status": "unclassified",
        "evidence_status": "not_evidence",
        "candidate_status": "not_candidate",
    }
    output_path.write_text(json.dumps(record, sort_keys=True) + "\n", encoding="utf-8")

    result = tools.list_latest_discovery_entries(
        source_code="BOPV",
        date="2026-05-24",
        output_root=tmp_path,
    )

    assert result["status"] == "ok"
    assert result["resource_type"] == "discovery_entries"
    assert result["discovery_types"] == ["api"]
    assert result["source_code"] == "BOPV"
    assert result["date"] == "2026-05-24"
    assert result["output_paths"] == {
        "api": str(output_path),
    }
    assert result["count"] == 1
    assert result["entries"] == [record | {"discovery_type": "api"}]
    assert result["entries"][0]["candidate_status"] == "not_candidate"
    assert result["entries"][0]["evidence_status"] == "not_evidence"
    assert result["entries"][0]["classification_status"] == "unclassified"


def test_mcp_latest_discovery_entries_reads_existing_html_jsonl_for_bop_a_coruna(tmp_path):
    output_path = tmp_path / "BOP_A_CORUNA" / "2026-05-25" / "html_discovery.jsonl"
    output_path.parent.mkdir(parents=True)
    record = {
        "source_code": "BOP_A_CORUNA",
        "page_url": "https://bop.dacoruna.gal/bopportal/cambioBoletin.do?fechaInput=25%2F05%2F2026",
        "page_format": "html",
        "entry_id": "717669",
        "document_id": "2026/3193",
        "title": "BOP A Coruna HTML entry",
        "published_at": "2026-05-25",
        "official_url": "https://bop.dacoruna.gal/bopportal/2026_0000003193.html",
        "summary": None,
        "raw_page_hash": "raw-html",
        "entry_hash": "entry-html",
        "discovered_at": "2026-05-25T00:00:00Z",
        "monitor_run_id": "html-run",
        "classification_status": "unclassified",
        "evidence_status": "not_evidence",
        "candidate_status": "not_candidate",
    }
    output_path.write_text(json.dumps(record, sort_keys=True) + "\n", encoding="utf-8")

    result = tools.list_latest_discovery_entries(
        source_code="BOP_A_CORUNA",
        date="2026-05-25",
        output_root=tmp_path,
    )

    assert result["status"] == "ok"
    assert result["resource_type"] == "discovery_entries"
    assert result["discovery_types"] == ["html"]
    assert result["source_code"] == "BOP_A_CORUNA"
    assert result["date"] == "2026-05-25"
    assert result["output_paths"] == {
        "html": str(output_path),
    }
    assert result["count"] == 1
    assert result["entries"] == [record | {"discovery_type": "html"}]
    assert result["entries"][0]["candidate_status"] == "not_candidate"
    assert result["entries"][0]["evidence_status"] == "not_evidence"
    assert result["entries"][0]["classification_status"] == "unclassified"


def test_mcp_latest_discovery_entries_reads_rss_api_and_html_in_deterministic_order(tmp_path):
    rss_path = tmp_path / "BOE" / "2026-05-24" / "rss_discovery.jsonl"
    api_path = tmp_path / "BOE" / "2026-05-24" / "api_discovery.jsonl"
    html_path = tmp_path / "BOE" / "2026-05-24" / "html_discovery.jsonl"
    rss_path.parent.mkdir(parents=True)
    rss_record = {
        "source_code": "BOE",
        "feed_url": "https://www.boe.es/rss/boe.php",
        "feed_format": "rss",
        "entry_id": "rss-entry",
        "title": "RSS entry",
        "published_at": "2026-05-24T00:00:00Z",
        "updated_at": None,
        "official_url": "https://www.boe.es/rss-entry",
        "summary": "rss",
        "raw_feed_hash": "raw-rss",
        "entry_hash": "entry-rss",
        "discovered_at": "2026-05-24T00:00:00Z",
        "monitor_run_id": "rss-run",
        "classification_status": "unclassified",
        "evidence_status": "not_evidence",
        "candidate_status": "not_candidate",
    }
    api_record = {
        "source_code": "BOE",
        "api_url": "https://www.boe.es/datosabiertos/api/boe/sumario/20260524",
        "api_endpoint": "/datosabiertos/api/boe/sumario/{date}",
        "title": "API entry",
        "published_at": "2026-05-24T00:00:00Z",
        "official_url": "https://www.boe.es/api-entry",
        "document_id": "BOE-A-2026-1",
        "api_id": "BOE-A-2026-1",
        "summary": "api",
        "raw_response_hash": "raw-api",
        "entry_hash": "entry-api",
        "discovered_at": "2026-05-24T00:00:00Z",
        "monitor_run_id": "api-run",
        "classification_status": "unclassified",
        "evidence_status": "not_evidence",
        "candidate_status": "not_candidate",
    }
    html_record = {
        "source_code": "BOE",
        "page_url": "https://www.boe.es/html",
        "page_format": "html",
        "entry_id": "html-entry",
        "document_id": "BOE-A-2026-HTML",
        "title": "HTML entry",
        "published_at": "2026-05-24T00:00:00Z",
        "official_url": "https://www.boe.es/html-entry",
        "summary": "html",
        "raw_page_hash": "raw-html",
        "entry_hash": "entry-html",
        "discovered_at": "2026-05-24T00:00:00Z",
        "monitor_run_id": "html-run",
        "classification_status": "unclassified",
        "evidence_status": "not_evidence",
        "candidate_status": "not_candidate",
    }
    rss_path.write_text(json.dumps(rss_record, sort_keys=True) + "\n", encoding="utf-8")
    api_path.write_text(json.dumps(api_record, sort_keys=True) + "\n", encoding="utf-8")
    html_path.write_text(json.dumps(html_record, sort_keys=True) + "\n", encoding="utf-8")

    result = tools.list_latest_discovery_entries(
        source_code="BOE",
        date="2026-05-24",
        output_root=tmp_path,
    )

    assert result["status"] == "ok"
    assert result["discovery_types"] == ["rss", "api", "html"]
    assert result["output_paths"] == {
        "rss": str(rss_path),
        "api": str(api_path),
        "html": str(html_path),
    }
    assert result["entries"] == [
        rss_record | {"discovery_type": "rss"},
        api_record | {"discovery_type": "api"},
        html_record | {"discovery_type": "html"},
    ]


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
        "output_paths": {
            "rss": str(tmp_path / "BOCYL" / "2026-05-24" / "rss_discovery.jsonl"),
            "api": str(tmp_path / "BOCYL" / "2026-05-24" / "api_discovery.jsonl"),
            "html": str(tmp_path / "BOCYL" / "2026-05-24" / "html_discovery.jsonl"),
        },
        "entries": [],
        "count": 0,
        "message": "No discovery output exists for this source/date.",
    }


def test_mcp_latest_discovery_entries_missing_api_output_returns_empty_without_fetch(
    tmp_path,
    monkeypatch,
):
    from official_sources import api_monitor

    def fail_fetch_api(_url: str):
        raise AssertionError("MCP discovery reader must not fetch live API data")

    monkeypatch.setattr(api_monitor, "fetch_api", fail_fetch_api)

    result = tools.list_latest_discovery_entries(
        source_code="BOPV",
        date="2026-05-24",
        output_root=tmp_path,
    )

    assert result["status"] == "empty"
    assert result["source_code"] == "BOPV"
    assert result["entries"] == []
    assert result["count"] == 0
    assert result["output_paths"] == {
        "rss": str(tmp_path / "BOPV" / "2026-05-24" / "rss_discovery.jsonl"),
        "api": str(tmp_path / "BOPV" / "2026-05-24" / "api_discovery.jsonl"),
        "html": str(tmp_path / "BOPV" / "2026-05-24" / "html_discovery.jsonl"),
    }


def test_mcp_latest_discovery_entries_missing_html_output_returns_empty_without_fetch(
    tmp_path,
    monkeypatch,
):
    from official_sources import html_monitor

    def fail_fetch_html(_url: str):
        raise AssertionError("MCP discovery reader must not fetch live HTML")

    monkeypatch.setattr(html_monitor, "fetch_html", fail_fetch_html)

    result = tools.list_latest_discovery_entries(
        source_code="BOP_A_CORUNA",
        date="2026-05-25",
        output_root=tmp_path,
    )

    assert result["status"] == "empty"
    assert result["source_code"] == "BOP_A_CORUNA"
    assert result["entries"] == []
    assert result["count"] == 0
    assert result["output_paths"] == {
        "rss": str(tmp_path / "BOP_A_CORUNA" / "2026-05-25" / "rss_discovery.jsonl"),
        "api": str(tmp_path / "BOP_A_CORUNA" / "2026-05-25" / "api_discovery.jsonl"),
        "html": str(tmp_path / "BOP_A_CORUNA" / "2026-05-25" / "html_discovery.jsonl"),
    }


def test_mcp_source_status_exposes_bop_a_coruna_as_monitor_validated():
    result = tools.get_source_status(source_code="BOP_A_CORUNA")

    assert result["status"] == "ok"
    assert result["source"]["operational_status"] == "monitor_validated"
    assert result["source"]["monitor_support"] == "available"
    assert result["source"]["candidate_creation_allowed"] is False
    assert result["source"]["evidence_grade_allowed"] is False


def test_mcp_preview_discovery_runs_rss_preview_without_writing(tmp_path):
    result = tools.preview_discovery(
        source_code="BOCYL",
        date="2026-05-24",
        limit=1,
        rss_fetcher=lambda _url: _fixture_bytes("rss_monitor_minimal.xml"),
    )

    assert result["status"] == "ok"
    assert result["resource_type"] == "discovery_preview"
    assert result["source_code"] == "BOCYL"
    assert result["discovery_type"] == "rss"
    assert result["mode"] == "preview"
    assert result["output_written"] is False
    assert result["count"] == 1
    assert result["records"][0]["source_code"] == "BOCYL"
    assert result["records"][0]["candidate_status"] == "not_candidate"
    assert result["records"][0]["evidence_status"] == "not_evidence"
    assert result["records"][0]["classification_status"] == "unclassified"
    assert not list(tmp_path.rglob("*.jsonl"))


def test_mcp_preview_discovery_runs_api_preview_without_writing(tmp_path):
    result = tools.preview_discovery(
        source_code="BOPV",
        date="2026-05-24",
        limit=1,
        api_fetcher=lambda _url: _fixture_bytes("bopv_api_month_page.json"),
    )

    assert result["status"] == "ok"
    assert result["source_code"] == "BOPV"
    assert result["discovery_type"] == "api"
    assert result["mode"] == "preview"
    assert result["output_written"] is False
    assert result["count"] == 1
    assert result["records"][0]["candidate_status"] == "not_candidate"
    assert result["records"][0]["evidence_status"] == "not_evidence"
    assert result["records"][0]["classification_status"] == "unclassified"
    assert not list(tmp_path.rglob("*.jsonl"))


def test_mcp_preview_discovery_runs_html_preview_without_writing(tmp_path):
    result = tools.preview_discovery(
        source_code="BOP_A_CORUNA",
        date="2026-05-25",
        limit=1,
        html_fetcher=lambda _url: _fixture_bytes("bop_a_coruna_latest.html"),
    )

    assert result["status"] == "ok"
    assert result["source_code"] == "BOP_A_CORUNA"
    assert result["discovery_type"] == "html"
    assert result["mode"] == "preview"
    assert result["output_written"] is False
    assert result["count"] == 1
    assert result["records"][0]["candidate_status"] == "not_candidate"
    assert result["records"][0]["evidence_status"] == "not_evidence"
    assert result["records"][0]["classification_status"] == "unclassified"
    assert not list(tmp_path.rglob("*.jsonl"))


def test_mcp_preview_discovery_refuses_unknown_source():
    result = tools.preview_discovery(source_code="NOPE", date="2026-05-24")

    assert result == {
        "status": "unknown_source",
        "source_code": "NOPE",
        "message": "Unknown source_code: NOPE",
    }


def test_mcp_preview_discovery_refuses_inventory_only_unmonitored_source():
    result = tools.preview_discovery(source_code="BOP_ZARAGOZA", date="2026-05-24")

    assert result["status"] == "not_monitorable"
    assert result["source_code"] == "BOP_ZARAGOZA"
    assert "validated monitor support" in result["message"]


def test_mcp_preview_discovery_refuses_limit_above_ten():
    result = tools.preview_discovery(source_code="BOCYL", date="2026-05-24", limit=11)

    assert result == {
        "status": "invalid_request",
        "source_code": "BOCYL",
        "message": "limit must be between 1 and 10",
    }


def test_mcp_preview_discovery_refuses_broad_all_source_request():
    result = tools.preview_discovery(source_code="ALL", date="2026-05-24")

    assert result == {
        "status": "invalid_request",
        "source_code": "ALL",
        "message": "preview_discovery requires one explicit source_code",
    }


def test_mcp_preview_discovery_refuses_comma_separated_source_request():
    result = tools.preview_discovery(source_code="BOCYL,BOPV", date="2026-05-24")

    assert result == {
        "status": "invalid_request",
        "source_code": "BOCYL,BOPV",
        "message": "preview_discovery requires one explicit source_code",
    }


def test_mcp_preview_discovery_refuses_wrong_discovery_type():
    result = tools.preview_discovery(
        source_code="BOPV",
        date="2026-05-24",
        discovery_type="rss",
    )

    assert result["status"] == "not_monitorable"
    assert result["source_code"] == "BOPV"
    assert result["discovery_type"] == "rss"
    assert "validated rss monitor" in result["message"]


def test_mcp_preview_discovery_never_calls_write_paths(monkeypatch):
    from official_sources import api_monitor, html_monitor, rss_monitor

    def fail_write(*_args, **_kwargs):
        raise AssertionError("MCP preview must not write discovery JSONL")

    monkeypatch.setattr(rss_monitor, "write_jsonl", fail_write)
    monkeypatch.setattr(api_monitor, "write_api_jsonl", fail_write)
    monkeypatch.setattr(html_monitor, "write_html_jsonl", fail_write)

    result = tools.preview_discovery(
        source_code="BOCYL",
        date="2026-05-24",
        limit=1,
        rss_fetcher=lambda _url: _fixture_bytes("rss_monitor_minimal.xml"),
    )

    assert result["status"] == "ok"
    assert result["output_written"] is False


def test_mcp_recommend_next_sources_returns_ranked_viable_provincial_inventory_sources(tmp_path):
    result = tools.recommend_next_sources(limit=6, output_root=tmp_path)

    assert result["status"] == "ok"
    assert result["resource_type"] == "source_recommendations"
    assert result["strategy"] == "provincial_html_discovery_pilot"
    assert result["count"] == 6
    assert [item["source_code"] for item in result["recommendations"]] == [
        "BOP_ZARAGOZA",
        "BOP_ARABA_ALAVA",
        "BOP_AVILA",
        "BOP_BURGOS",
        "BOP_CACERES",
        "BOP_CADIZ",
    ]
    first = result["recommendations"][0]
    assert first["recommended_task"] == "provincial_html_discovery_pilot"
    assert first["confidence"] == "medium"
    assert first["operational_status"] == "inventory_only"
    assert first["monitor_support"] == "none"
    assert first["discovery_cache_status"] == "no_discovery_cache"
    assert first["latest_cache_date"] is None
    assert first["implemented_preview_available"] is False
    assert first["candidate_creation_allowed"] is False
    assert first["evidence_grade_allowed"] is False
    assert "metadata-only" in first["constraints"]
    assert "no candidates" in first["constraints"]


def test_mcp_recommend_next_sources_excludes_already_monitored_html_source(tmp_path):
    result = tools.recommend_next_sources(limit=20, output_root=tmp_path)

    source_codes = {item["source_code"] for item in result["recommendations"]}
    assert {
        "BOP_A_CORUNA",
        "BOP_ALBACETE",
        "BOP_ALICANTE",
        "BOP_BARCELONA",
        "BOP_BIZKAIA",
        "BOP_LUGO",
        "BOP_MALAGA",
        "BOP_VALENCIA",
    }.isdisjoint(source_codes)
    assert all(item["operational_status"] == "inventory_only" for item in result["recommendations"])


def test_mcp_recommend_next_sources_excludes_documented_blocked_or_deferred_source(tmp_path):
    result = tools.recommend_next_sources(limit=20, output_root=tmp_path)

    source_codes = {item["source_code"] for item in result["recommendations"]}
    assert "BOP_ALMERIA" not in source_codes

    status = tools.get_source_status(source_code="BOP_ALMERIA")
    assert status["status"] == "ok"
    assert status["source"]["source_code"] == "BOP_ALMERIA"
    assert status["source"]["operational_status"] == "inventory_only"
    assert status["source"]["monitor_support"] == "none"
    assert status["source"]["candidate_creation_allowed"] is False
    assert status["source"]["evidence_grade_allowed"] is False
    assert any("ZK/JavaScript" in limitation for limitation in status["source"]["limitations"])


def test_mcp_recommend_next_sources_surfaces_existing_cache_without_reading_live(tmp_path):
    output_path = tmp_path / "BOP_ZARAGOZA" / "2026-05-24" / "html_discovery.jsonl"
    output_path.parent.mkdir(parents=True)
    output_path.write_text(
        json.dumps(
            {
                "source_code": "BOP_ZARAGOZA",
                "candidate_status": "not_candidate",
                "evidence_status": "not_evidence",
                "classification_status": "unclassified",
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    result = tools.recommend_next_sources(limit=1, output_root=tmp_path)

    assert result["recommendations"][0]["source_code"] == "BOP_ZARAGOZA"
    assert result["recommendations"][0]["discovery_cache_status"] == "has_discovery_cache"
    assert result["recommendations"][0]["latest_cache_date"] == "2026-05-24"


def test_mcp_recommend_next_sources_refuses_invalid_limit():
    result = tools.recommend_next_sources(limit=0)

    assert result == {
        "status": "invalid_request",
        "message": "limit must be between 1 and 20",
    }


def test_mcp_recommend_next_sources_does_not_execute_previews_or_write(tmp_path, monkeypatch):
    def fail_preview(*_args, **_kwargs):
        raise AssertionError("recommend_next_sources must not run discovery previews")

    monkeypatch.setattr(source_coverage, "monitor_source_feed", fail_preview)
    monkeypatch.setattr(source_coverage, "monitor_api_source", fail_preview)
    monkeypatch.setattr(source_coverage, "monitor_html_source", fail_preview)

    result = tools.recommend_next_sources(limit=2, output_root=tmp_path)

    assert result["status"] == "ok"
    assert result["count"] == 2
    assert not list(tmp_path.rglob("*.jsonl"))


def test_mcp_recommend_sources_for_consumer_prioritizes_downstream_need():
    result = tools.recommend_sources_for_consumer(consumer="oposiciones2.0", limit=3)

    assert result["status"] == "ok"
    assert result["resource_type"] == "downstream_source_recommendations"
    assert result["consumer"] == "oposiciones2.0"
    assert result["demand_class"] == "public_employment_alerts"
    assert result["mode"] == "read_only"
    assert result["writes_performed"] is False
    assert result["candidate_creation_allowed"] is False
    assert result["evidence_grade_allowed"] is False
    assert result["product_automation_allowed"] is False
    assert result["human_review_required"] is True
    assert [item["source_code"] for item in result["recommendations"]] == [
        "BOP_AVILA",
        "BOP_PONTEVEDRA",
        "BOP_SORIA",
    ]
    first_status = result["recommendations"][0]["source_status"]
    assert first_status["registered"] is True
    assert first_status["registry_operational_status"] == "inventory_only"
    assert first_status["product_ready"] is False
    assert first_status["candidate_creation_allowed"] is False
    assert first_status["evidence_grade_allowed"] is False
    assert "publication_ready" in first_status["must_not_infer"]
    assert (
        "BOP_CASTELLON and BOP_SEVILLA are now shared metadata-only monitors"
        in result["missing_capabilities"]
    )


def test_mcp_recommend_sources_for_consumer_supports_product_alias():
    result = tools.recommend_sources_for_consumer(consumer="renta", limit=1)

    assert result["status"] == "ok"
    assert result["consumer"] == "renta-verificable"
    assert result["demand_class"] == "fiscal_reference_resolution"
    assert result["recommendations"][0]["source_code"] == "BOE"
    assert "AEAT-first fiscal reference model" in result["missing_capabilities"]


def test_mcp_recommend_sources_for_consumer_refuses_unknown_consumer():
    result = tools.recommend_sources_for_consumer(consumer="unknown-product")

    assert result["status"] == "unsupported_consumer"
    assert result["consumer"] == "unknown-product"
    assert "oposiciones2.0" in result["supported_consumers"]


def test_mcp_recommend_sources_for_consumer_refuses_wrong_demand_class():
    result = tools.recommend_sources_for_consumer(
        consumer="eduayudas",
        demand_class="public_employment_alerts",
    )

    assert result == {
        "status": "unsupported_demand_class",
        "consumer": "eduayudas",
        "demand_class": "public_employment_alerts",
        "supported_demand_class": "education_aid_evidence",
        "message": "Demand class does not match the registered downstream profile.",
    }


def test_mcp_recommend_sources_for_consumer_refuses_invalid_limit():
    result = tools.recommend_sources_for_consumer(consumer="oposiciones2.0", limit=0)

    assert result == {
        "status": "invalid_request",
        "message": "limit must be between 1 and 20",
    }


def test_mcp_latest_discovery_entries_unknown_source_returns_safe_error(tmp_path):
    result = tools.list_latest_discovery_entries(source_code="NOPE", output_root=tmp_path)

    assert result == {
        "status": "unknown_source",
        "source_code": "NOPE",
        "message": "Unknown source_code: NOPE",
    }


def test_mcp_source_coverage_tools_do_not_import_write_path_modules():
    source = inspect.getsource(tools) + inspect.getsource(source_coverage)

    assert "create_source_candidate" not in source
    assert "write_jsonl" not in source
    assert "write_api_jsonl" not in source
    assert "write_html_jsonl" not in source
    assert "fetch_feed" not in source
    assert "fetch_api" not in source
    assert "fetch_html" not in source
    assert "artifacts" not in source
