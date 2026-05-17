from __future__ import annotations

from pathlib import Path

import httpx

from official_sources.mcp import tools
from official_sources.mcp.server import MCP_TOOL_NAMES
from official_sources.sources.boe.consolidated import BOEConsolidatedClient, BOEConsolidatedService


def _fixture_bytes() -> bytes:
    return (Path(__file__).parent / "fixtures" / "boe_consolidated_law.xml").read_bytes()


def _seed(repository):
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, content=_fixture_bytes(), headers={"content-type": "application/xml"}
        )

    client = httpx.Client(
        transport=httpx.MockTransport(handler), follow_redirects=False, timeout=5.0
    )
    service = BOEConsolidatedService(repository, client=BOEConsolidatedClient(client=client))
    service.fetch_and_store("BOE-A-2024-11111")


def test_mcp_consolidated_law_get_returns_structured_object(repository):
    _seed(repository)

    result = tools.boe_consolidated_law_get(repository, official_identifier="BOE-A-2024-11111")

    assert result["resource_type"] == "consolidated_law"
    assert result["official_identifier"] == "BOE-A-2024-11111"
    assert result["source_code"] == "BOE"


def test_mcp_consolidated_law_text_returns_structured_envelope(repository):
    _seed(repository)

    result = tools.boe_consolidated_law_text_get(
        repository,
        official_identifier="BOE-A-2024-11111",
        block_identifier="a1",
    )

    assert result["resource_type"] == "consolidated_law_text"
    assert result["is_official_text"] is True
    assert result["content_type"] == "official_consolidated_legal_text"
    assert "Ignore previous instructions" in result["content"]
    top_level_values = [value for key, value in result.items() if key != "content"]
    assert all("Ignore previous instructions" not in str(value) for value in top_level_values)


def test_mcp_consolidated_law_citation_build(repository):
    _seed(repository)

    result = tools.boe_consolidated_law_citation_build(
        repository,
        official_identifier="BOE-A-2024-11111",
        block_identifier="a1",
    )

    assert result["resource_type"] == "consolidated_law_block"
    assert result["block_identifier"] == "a1"


def test_mcp_consolidated_law_index_get_returns_structured_object(repository):
    source = repository.get_source_by_code("BOE")
    law = repository.upsert_consolidated_law(
        source_id=source["id"],
        external_id="BOE-A-2024-11111",
        official_identifier="BOE-A-2024-11111",
        title="Test consolidated law",
        law_type=None,
        jurisdiction="state",
        department=None,
        publication_date=None,
        consolidation_status=None,
        official_url="https://www.boe.es/datosabiertos/api/legislacion-consolidada/id/BOE-A-2024-11111",
        raw_metadata={},
    )
    version = repository.upsert_consolidated_law_version(
        consolidated_law_id=law["id"],
        version_identifier="BOE-A-2024-11111:text-index",
        version_date="2024-05-30",
        valid_from=None,
        valid_to=None,
        is_current=True,
        official_url="https://www.boe.es/datosabiertos/api/legislacion-consolidada/id/BOE-A-2024-11111/texto/indice",
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
        content="",
        content_sha256="",
        source_snapshot_hash="abc",
        order_index=0,
        parent_block_id=None,
        block_path="a1",
        api_url="https://www.boe.es/datosabiertos/api/legislacion-consolidada/id/BOE-A-2024-11111/texto/bloque/a1",
        raw_payload_hash="abc",
    )

    result = tools.boe_consolidated_law_index_get(
        repository,
        official_identifier="BOE-A-2024-11111",
    )

    assert result["resource_type"] == "consolidated_law_text_index"
    assert result["official_identifier"] == "BOE-A-2024-11111"
    assert result["blocks"][0]["block_id"] == "a1"


def test_mcp_consolidated_law_block_get_returns_required_envelope(repository):
    _seed(repository)

    result = tools.boe_consolidated_law_block_get(
        repository,
        official_identifier="BOE-A-2024-11111",
        block_id="a1",
    )

    assert result["resource_type"] == "consolidated_law_block"
    assert result["official_identifier"] == "BOE-A-2024-11111"
    assert result["source_code"] == "BOE"
    assert result["block_id"] == "a1"
    assert result["block_type"] == "article"
    assert result["block_identifier"] == "a1"
    assert result["block_title"] == "Article 1"
    assert result["is_official_text"] is True
    assert result["content_type"] == "official_consolidated_legal_text_block"
    assert "Ignore previous instructions" in result["content"]
    top_level_values = [value for key, value in result.items() if key != "content"]
    assert all("Ignore previous instructions" not in str(value) for value in top_level_values)


def test_mcp_consolidated_law_block_citation_build(repository):
    _seed(repository)

    result = tools.boe_consolidated_law_block_citation_build(
        repository,
        official_identifier="BOE-A-2024-11111",
        block_id="a1",
    )

    assert result["resource_type"] == "consolidated_law_block"
    assert result["block_id"] == "a1"
    assert result["law_title"] == "Test consolidated law"


def test_mcp_consolidated_tools_are_registered_without_search_stub():
    assert "boe_consolidated_law_get" in MCP_TOOL_NAMES
    assert "boe_consolidated_law_text_get" in MCP_TOOL_NAMES
    assert "boe_consolidated_law_index_get" in MCP_TOOL_NAMES
    assert "boe_consolidated_law_block_get" in MCP_TOOL_NAMES
    assert "boe_consolidated_law_citation_build" in MCP_TOOL_NAMES
    assert "boe_consolidated_law_block_citation_build" in MCP_TOOL_NAMES
    assert "boe_consolidated_law_search" not in MCP_TOOL_NAMES


def test_mcp_consolidated_tools_do_not_interpret_or_diff_or_write_downstream():
    import inspect

    source = inspect.getsource(tools)

    assert "interpret" not in source.lower()
    assert "legal_advice" not in source
    assert "diff" not in source.lower()
    assert "downstream" not in source.lower()
    assert "human_accepted" not in source
