from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_security_docs_contain_tool_output_trust_model_and_no_auth_warning():
    security = _read("docs/SECURITY.md")

    assert "Tool output trust model" in security
    assert "This MCP server has no authentication" in security
    assert "private VPN" in security


def test_mcp_docs_do_not_instruct_binding_to_public_interfaces():
    combined = "\n".join(
        [
            _read("README.md"),
            _read("docs/MCP_TOOLS.md"),
            _read("docs/PRE_DEPLOY_VPS_CHECKLIST.md"),
            _read("docs/SECURITY.md"),
        ]
    )

    assert "bind MCP to 0.0.0.0" not in combined
    assert "0.0.0.0" in combined
    assert "public Docker port mapping" in combined
    assert "Cloudflare Tunnel" in combined


def test_systemd_templates_do_not_expose_public_listener():
    for path in (ROOT / "deploy" / "systemd").iterdir():
        content = path.read_text(encoding="utf-8")
        assert "ListenStream" not in content
        assert "0.0.0.0" not in content
        assert "nginx" not in content.lower()


def test_boe_calendar_semantics_are_documented():
    combined = "\n".join(
        [
            _read("docs/SOURCES_POLICY.md"),
            _read("docs/ARCHITECTURE.md"),
            _read("docs/reports/BOE_NO_PUBLICATION_PROBE_2026-05-17.md"),
        ]
    )

    assert "BOE publishes every day of the year except Sundays" in combined
    assert "BORME publication rules are different" in combined
    assert "must not be reused for BOE daily summary ingestion" in combined
