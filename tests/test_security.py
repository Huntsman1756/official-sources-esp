from __future__ import annotations

from official_sources.mcp.server import MCP_TOOL_NAMES


def test_mcp_excludes_legislation_tools_that_are_not_implemented_safely():
    assert "boe_legislation_search" not in MCP_TOOL_NAMES
    assert "boe_legislation_structure_get" not in MCP_TOOL_NAMES


def test_mcp_tools_do_not_expose_shell_url_or_filesystem_capabilities():
    import official_sources.mcp.tools as mcp_tools

    module_source = mcp_tools.__loader__.get_source(mcp_tools.__name__)

    assert "subprocess" not in module_source
    assert "httpx" not in module_source
    assert "open(" not in module_source
    assert "Path(" not in module_source
