from __future__ import annotations

import pytest

from official_sources.source_registry import (
    SourceRegistryError,
    load_source_registry,
    validate_source_registry,
)


def test_load_source_registry_validates_required_initial_coverage():
    registry = load_source_registry()
    source_codes = {source["source_code"] for source in registry["sources"]}

    assert {
        "BOE",
        "BOJA",
        "BOCM",
        "DOGV",
        "DOGC",
        "BOCYL",
        "BOPV",
        "BORM",
        "BDNS",
        "BOA",
    } <= source_codes
    assert {"BOPA", "BOIB", "BOCCE", "BOME"} <= source_codes
    assert {"BOP_A_CORUNA", "BOP_ZARAGOZA"} <= source_codes
    assert len(source_codes) == len(registry["sources"])


def test_vps_blocked_sources_are_marked_explicitly():
    registry = load_source_registry()
    sources = {source["source_code"]: source for source in registry["sources"]}

    assert sources["BOP_CUENCA"]["blocked_vps"] is True
    assert sources["BOP_CUENCA"]["pending_relay"] is True
    assert sources["BOP_SALAMANCA"]["blocked_vps"] is True
    assert sources["BOP_SALAMANCA"]["pending_relay"] is True
    assert sources["BOP_ZARAGOZA"]["blocked_vps"] is True
    assert sources["BOP_ZARAGOZA"]["pending_relay"] is True


def test_validate_source_registry_rejects_ambiguous_status_values():
    registry = {
        "sources": [
            {
                "source_code": "TEST",
                "name": "Test source",
                "jurisdiction": "ES",
                "jurisdiction_level": "estatal",
                "official_landing_url": "https://example.test",
                "access_methods": [
                    {
                        "type": "rss",
                        "url": "https://example.test/feed",
                        "status": "ok",
                        "notes": "Ambiguous status must fail.",
                    }
                ],
                "operational_status": "active",
                "mcp_support": False,
                "monitor_support": "none",
                "backfill_support": "none",
                "evidence_adapter": False,
                "candidate_creation_allowed": False,
                "evidence_grade_allowed": False,
                "last_verified_at": "2026-05-24",
                "limitations": [],
                "notes": "",
            }
        ]
    }

    with pytest.raises(SourceRegistryError) as exc_info:
        validate_source_registry(registry)

    assert "operational_status" in str(exc_info.value)
    assert "access_methods[0].status" in str(exc_info.value)


def test_validate_source_registry_requires_monitor_validated_access_method():
    registry = {
        "sources": [
            {
                "source_code": "TEST",
                "name": "Test source",
                "jurisdiction": "ES",
                "jurisdiction_level": "estatal",
                "official_landing_url": "https://example.test",
                "access_methods": [
                    {
                        "type": "manual",
                        "status": "validated",
                        "notes": "Manual path is not monitor-capable.",
                    }
                ],
                "operational_status": "monitor_validated",
                "mcp_support": False,
                "monitor_support": "validated",
                "backfill_support": "none",
                "evidence_adapter": False,
                "candidate_creation_allowed": False,
                "evidence_grade_allowed": False,
                "last_verified_at": "2026-05-24",
                "limitations": [],
                "notes": "",
            }
        ]
    }

    with pytest.raises(SourceRegistryError) as exc_info:
        validate_source_registry(registry)

    assert "monitor_support=validated" in str(exc_info.value)


def test_sources_cli_list_outputs_registry_summary(capsys):
    from official_sources.cli import run

    exit_code = run(["sources", "list"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "source_code operational_status" in captured.out
    assert "BOCYL" in captured.out
    assert "inventory_only" in captured.out


def test_sources_cli_status_outputs_one_source(capsys):
    from official_sources.cli import run

    exit_code = run(["sources", "status", "--source", "BOCYL"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "source_code=BOCYL" in captured.out
    assert "official_landing_url=https://bocyl.jcyl.es/portada.do" in captured.out
    assert "candidate_creation_allowed=False" in captured.out
