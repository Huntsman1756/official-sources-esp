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


def test_relay_promoted_sources_are_marked_explicitly():
    registry = load_source_registry()
    sources = {source["source_code"]: source for source in registry["sources"]}

    for source_code in ("BOP_CUENCA", "BOP_SALAMANCA", "BOP_ZARAGOZA"):
        source = sources[source_code]
        assert source["operational_status"] == "monitor_validated"
        assert source["monitor_support"] == "available"
        assert source["blocked_vps"] is False
        assert source["pending_relay"] is False
        assert source["candidate_creation_allowed"] is False
        assert source["evidence_grade_allowed"] is False


def test_bop_alicante_recovery_descriptor_is_explicit():
    registry = load_source_registry()
    sources = {source["source_code"]: source for source in registry["sources"]}
    source = sources["BOP_ALICANTE"]

    assert source["operational_status"] == "monitor_validated"
    assert source["monitor_support"] == "available"
    assert source["candidate_creation_allowed"] is False
    assert source["evidence_grade_allowed"] is False
    assert source["degraded"] is False
    assert source["degraded_reason"] is None
    assert "resolved 2026-06-02" in source["recovery_note"]


def test_validate_source_registry_rejects_degraded_without_reason():
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
                        "status": "validated",
                        "notes": "Validated test feed.",
                    }
                ],
                "operational_status": "monitor_validated",
                "mcp_support": False,
                "monitor_support": "available",
                "backfill_support": "none",
                "evidence_adapter": False,
                "candidate_creation_allowed": False,
                "evidence_grade_allowed": False,
                "degraded": True,
                "degraded_reason": None,
                "last_verified_at": "2026-06-02",
                "limitations": [],
                "notes": "",
            }
        ]
    }

    with pytest.raises(SourceRegistryError) as exc_info:
        validate_source_registry(registry)

    assert "degraded_reason is required when degraded=true" in str(exc_info.value)


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
