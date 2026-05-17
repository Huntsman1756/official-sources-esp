from __future__ import annotations

import os

from official_sources.mcp import tools
from official_sources.storage.database import connect, initialize_database
from official_sources.storage.repository import OfficialSourcesRepository

try:
    from fastmcp import FastMCP
except ImportError:  # pragma: no cover
    FastMCP = None


MCP_TOOL_NAMES = {
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
}


def create_repository_from_env() -> OfficialSourcesRepository:
    database_path = os.environ.get(
        "OFFICIAL_SOURCES_DB_PATH",
        os.environ.get("OFFICIAL_SOURCES_DB", "official-sources.sqlite"),
    )
    connection = connect(database_path)
    initialize_database(connection)
    repository = OfficialSourcesRepository(connection)
    repository.ensure_official_source_boe()
    return repository


def create_server(repository: OfficialSourcesRepository | None = None):
    if FastMCP is None:
        raise RuntimeError("FastMCP is not installed")
    repository = repository or create_repository_from_env()
    mcp = FastMCP(name="official-sources")

    @mcp.tool
    def boe_summary_search(
        keyword: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        limit: int = 20,
    ) -> dict:
        return tools.boe_summary_search(
            repository,
            keyword=keyword,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
        )

    @mcp.tool
    def boe_document_get(external_id: str) -> dict:
        return tools.boe_document_get(repository, external_id=external_id)

    @mcp.tool
    def boe_document_text_get(external_id: str) -> dict:
        return tools.boe_document_text_get(repository, external_id=external_id)

    @mcp.tool
    def boe_citation_build(external_id: str) -> dict:
        return tools.boe_citation_build(repository, external_id=external_id)

    @mcp.tool
    def source_trace(external_id: str) -> dict:
        return tools.source_trace(repository, external_id=external_id)

    @mcp.tool
    def integrity_status_get(external_id: str) -> dict:
        return tools.integrity_status_get(repository, external_id=external_id)

    @mcp.tool
    def boe_consolidated_law_get(official_identifier: str) -> dict:
        return tools.boe_consolidated_law_get(
            repository,
            official_identifier=official_identifier,
        )

    @mcp.tool
    def boe_consolidated_law_text_get(
        official_identifier: str,
        block_identifier: str | None = None,
    ) -> dict:
        return tools.boe_consolidated_law_text_get(
            repository,
            official_identifier=official_identifier,
            block_identifier=block_identifier,
        )

    @mcp.tool
    def boe_consolidated_law_citation_build(
        official_identifier: str,
        block_identifier: str | None = None,
    ) -> dict:
        return tools.boe_consolidated_law_citation_build(
            repository,
            official_identifier=official_identifier,
            block_identifier=block_identifier,
        )

    @mcp.tool
    def boe_consolidated_law_index_get(official_identifier: str) -> dict:
        return tools.boe_consolidated_law_index_get(
            repository,
            official_identifier=official_identifier,
        )

    @mcp.tool
    def boe_consolidated_law_block_get(official_identifier: str, block_id: str) -> dict:
        return tools.boe_consolidated_law_block_get(
            repository,
            official_identifier=official_identifier,
            block_id=block_id,
        )

    @mcp.tool
    def boe_consolidated_law_block_citation_build(
        official_identifier: str,
        block_id: str,
    ) -> dict:
        return tools.boe_consolidated_law_block_citation_build(
            repository,
            official_identifier=official_identifier,
            block_id=block_id,
        )

    return mcp


def main() -> None:
    create_server().run()


if __name__ == "__main__":
    main()
