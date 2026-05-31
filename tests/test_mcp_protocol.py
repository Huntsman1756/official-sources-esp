from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys

import pytest
from fastmcp import Client

from official_sources.mcp.server import MCP_TOOL_NAMES, create_server
from official_sources.sources.bdns.ingestion import ingest_bdns_concessions
from official_sources.storage.database import connect, initialize_database
from official_sources.storage.repository import OfficialSourcesRepository


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


@pytest.mark.asyncio
async def test_mcp_bdns_concessions_call_returns_sanitized_cache_without_writes(
    tmp_path,
    monkeypatch,
):
    database_path = tmp_path / "mcp.sqlite"
    monkeypatch.setenv("OFFICIAL_SOURCES_DB_PATH", str(database_path))
    seed_connection = connect(str(database_path))
    initialize_database(seed_connection)
    seed_repository = OfficialSourcesRepository(seed_connection)
    payload = json.dumps(
        {
            "content": [
                {
                    "codConcesion": "SB152503815",
                    "numeroConvocatoria": "877699",
                    "fechaConcesion": "2026-05-29",
                    "importe": 17243.86,
                    "beneficiario": "Persona Fisica",
                    "idPersona": 22127337,
                }
            ],
            "last": True,
        }
    ).encode()
    ingest_bdns_concessions(
        seed_repository,
        num_conv="877699",
        page_size=1,
        max_pages=1,
        fetcher=lambda **_kwargs: payload,
    )
    seed_connection.close()
    with sqlite3.connect(database_path) as connection:
        before_runs = connection.execute("SELECT COUNT(*) FROM ingestion_runs").fetchone()[0]

    async with Client(create_server()) as client:
        result = await client.call_tool(
            "bdns_concessions_list",
            {"num_conv": "877699", "limit": 5},
        )

    with sqlite3.connect(database_path) as connection:
        after_runs = connection.execute("SELECT COUNT(*) FROM ingestion_runs").fetchone()[0]
    assert result.structured_content["status"] == "ok"
    assert result.structured_content["resource_type"] == "bdns_concessions"
    assert result.structured_content["writes_performed"] is False
    assert result.structured_content["items"][0]["external_id"] == "BDNS:concesion:SB152503815"
    assert "beneficiary_name" not in result.structured_content["items"][0]
    assert "Persona Fisica" not in json.dumps(result.structured_content)
    assert after_runs == before_runs


@pytest.mark.asyncio
async def test_mcp_case_taxonomy_call_returns_readonly_envelope_without_writes(
    tmp_path,
    monkeypatch,
):
    database_path = tmp_path / "mcp.sqlite"
    monkeypatch.setenv("OFFICIAL_SOURCES_DB_PATH", str(database_path))

    async with Client(create_server()) as client:
        result = await client.call_tool(
            "list_case_taxonomy",
            {"consumer": "eduayudas"},
        )

    assert result.structured_content["status"] == "ok"
    assert result.structured_content["resource_type"] == "case_taxonomy"
    assert result.structured_content["writes_performed"] is False
    assert result.structured_content["candidate_creation_allowed"] is False
    assert result.structured_content["evidence_grade_allowed"] is False
    assert result.structured_content["product_automation_allowed"] is False
    assert result.structured_content["cases"][0]["demand_class"] == "education_aid_evidence"
    with sqlite3.connect(database_path) as connection:
        after_candidates = connection.execute("SELECT COUNT(*) FROM source_candidates").fetchone()[
            0
        ]
    assert after_candidates == 0


@pytest.mark.asyncio
async def test_mcp_downstream_integration_smokes_call_returns_readonly_matrix_without_writes(
    tmp_path,
    monkeypatch,
):
    database_path = tmp_path / "mcp.sqlite"
    monkeypatch.setenv("OFFICIAL_SOURCES_DB_PATH", str(database_path))

    async with Client(create_server()) as client:
        result = await client.call_tool(
            "list_downstream_integration_smokes",
            {"consumer": "renta"},
        )

    assert result.structured_content["status"] == "ok"
    assert result.structured_content["resource_type"] == "downstream_integration_smoke_matrix"
    assert result.structured_content["writes_performed"] is False
    assert result.structured_content["candidate_creation_allowed"] is False
    assert result.structured_content["evidence_grade_allowed"] is False
    assert result.structured_content["product_automation_allowed"] is False
    assert result.structured_content["smokes"][0]["consumer"] == "renta-verificable"
    assert result.structured_content["smokes"][0]["smoke_call"]["tool"] == (
        "resolve_fiscal_reference"
    )
    with sqlite3.connect(database_path) as connection:
        after_candidates = connection.execute("SELECT COUNT(*) FROM source_candidates").fetchone()[
            0
        ]
    assert after_candidates == 0


@pytest.mark.asyncio
async def test_mcp_check_downstream_integration_smokes_call_returns_readonly_results_without_writes(
    tmp_path,
    monkeypatch,
):
    database_path = tmp_path / "mcp.sqlite"
    monkeypatch.setenv("OFFICIAL_SOURCES_DB_PATH", str(database_path))

    async with Client(create_server()) as client:
        result = await client.call_tool(
            "check_downstream_integration_smokes",
            {"consumer": "renta"},
        )

    assert result.structured_content["status"] == "ok"
    assert result.structured_content["resource_type"] == "downstream_integration_smoke_run"
    assert result.structured_content["writes_performed"] is False
    assert result.structured_content["candidate_creation_allowed"] is False
    assert result.structured_content["evidence_grade_allowed"] is False
    assert result.structured_content["product_automation_allowed"] is False
    assert result.structured_content["downstream_commands_executed"] is False
    assert result.structured_content["monitor_previews_executed"] is False
    assert result.structured_content["results"][0]["consumer"] == "renta-verificable"
    assert result.structured_content["results"][0]["passed"] is True
    with sqlite3.connect(database_path) as connection:
        after_candidates = connection.execute("SELECT COUNT(*) FROM source_candidates").fetchone()[
            0
        ]
        document_files = connection.execute("SELECT COUNT(*) FROM document_files").fetchone()[0]
        artifact_attempts = connection.execute(
            "SELECT COUNT(*) FROM artifact_download_attempts"
        ).fetchone()[0]
        ingestion_runs = connection.execute("SELECT COUNT(*) FROM ingestion_runs").fetchone()[0]
    assert after_candidates == 0
    assert document_files == 0
    assert artifact_attempts == 0
    assert ingestion_runs == 0


@pytest.mark.asyncio
async def test_mcp_downstream_planner_calls_return_readonly_envelopes_without_writes(
    tmp_path,
    monkeypatch,
):
    database_path = tmp_path / "mcp.sqlite"
    monkeypatch.setenv("OFFICIAL_SOURCES_DB_PATH", str(database_path))

    async with Client(create_server()) as client:
        evidence_result = await client.call_tool(
            "build_evidence_packet",
            {"consumer": "eduayudas", "source_code": "BDNS"},
        )
        reference_result = await client.call_tool(
            "resolve_normative_reference",
            {"consumer": "la-ayuda", "topic": "housing", "jurisdiction": "state", "limit": 2},
        )

    assert evidence_result.structured_content["status"] == "ok"
    assert evidence_result.structured_content["writes_performed"] is False
    assert evidence_result.structured_content["evidence_grade_allowed"] is False
    assert reference_result.structured_content["status"] == "manual_review_required"
    assert reference_result.structured_content["exact_reference_resolved"] is False
    assert reference_result.structured_content["writes_performed"] is False
    with sqlite3.connect(database_path) as connection:
        after_candidates = connection.execute("SELECT COUNT(*) FROM source_candidates").fetchone()[
            0
        ]
    assert after_candidates == 0


@pytest.mark.asyncio
async def test_mcp_fiscal_reference_call_returns_manual_review_without_writes(
    tmp_path,
    monkeypatch,
):
    database_path = tmp_path / "mcp.sqlite"
    monkeypatch.setenv("OFFICIAL_SOURCES_DB_PATH", str(database_path))

    async with Client(create_server()) as client:
        result = await client.call_tool(
            "resolve_fiscal_reference",
            {"consumer": "renta", "tax_year": 2025, "jurisdiction": "Madrid", "limit": 2},
        )

    assert result.structured_content["status"] == "manual_review_required"
    assert result.structured_content["resource_type"] == "fiscal_reference_resolution"
    assert result.structured_content["writes_performed"] is False
    assert result.structured_content["evidence_grade_allowed"] is False
    assert result.structured_content["exact_reference_resolved"] is False
    assert result.structured_content["source_leads"][0]["source_code"] == "AEAT"
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
