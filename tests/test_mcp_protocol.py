from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys

import pytest
from fastmcp import Client

from official_sources.mcp.server import MCP_TOOL_NAMES, create_server


@pytest.mark.asyncio
async def test_mcp_initialize_advertises_project_identity_and_tools(repository):
    async with Client(create_server(repository)) as client:
        initialize_result = client.initialize_result

    assert initialize_result.protocolVersion == "2025-11-25"
    assert initialize_result.serverInfo.name == "official-sources"
    assert initialize_result.serverInfo.version == "0.1.0"
    assert initialize_result.capabilities.tools is not None


@pytest.mark.asyncio
async def test_mcp_tools_list_has_stable_described_json_schema_tools(repository):
    async with Client(create_server(repository)) as client:
        tools = await client.list_tools()

    assert [tool.name for tool in tools] == list(MCP_TOOL_NAMES)
    for tool in tools:
        assert tool.name in MCP_TOOL_NAMES
        assert tool.description
        assert tool.inputSchema["type"] == "object"
        assert tool.outputSchema["type"] == "object"


@pytest.mark.asyncio
async def test_mcp_tools_call_returns_structured_cache_miss_without_writes(tmp_path, monkeypatch):
    database_path = tmp_path / "mcp.sqlite"
    monkeypatch.setenv("OFFICIAL_SOURCES_DB_PATH", str(database_path))

    async with Client(create_server()) as client:
        result = await client.call_tool(
            "boe_document_get",
            {"external_id": "BOE-A-2024-99999"},
        )

    assert result.structured_content == {
        "status": "cache_miss",
        "resource_type": "official_document",
        "official_identifier": "BOE-A-2024-99999",
        "recommended_action": (
            "Ingest the corresponding BOE summary date or fetch by official identifier if supported"
        ),
    }
    with sqlite3.connect(database_path) as connection:
        after_candidates = connection.execute("SELECT COUNT(*) FROM source_candidates").fetchone()[
            0
        ]
    assert after_candidates == 0


def test_mcp_stdio_initialize_writes_only_json_rpc_to_stdout(tmp_path):
    database_path = tmp_path / "mcp-stdio.sqlite"
    env = os.environ.copy()
    env["OFFICIAL_SOURCES_DB_PATH"] = str(database_path)
    process = subprocess.Popen(
        [sys.executable, "-m", "official_sources.mcp.server"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        env=env,
    )
    assert process.stdin is not None
    assert process.stdout is not None
    try:
        process.stdin.write(
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2025-11-25",
                        "capabilities": {},
                        "clientInfo": {"name": "official-sources-test", "version": "0.0.0"},
                    },
                }
            )
            + "\n"
        )
        process.stdin.flush()

        response = json.loads(process.stdout.readline())

        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert response["result"]["protocolVersion"] == "2025-11-25"
        assert response["result"]["serverInfo"] == {
            "name": "official-sources",
            "version": "0.1.0",
        }
        assert "tools" in response["result"]["capabilities"]
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
