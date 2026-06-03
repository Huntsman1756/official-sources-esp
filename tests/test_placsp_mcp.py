from __future__ import annotations

from official_sources.source_coverage import recommend_sources_for_consumer
from official_sources.source_registry import get_source, load_source_registry


def test_placsp_registry_is_metadata_only_and_fail_closed():
    registry = load_source_registry()
    source_codes = {source["source_code"] for source in registry["sources"]}
    source = get_source("PLACSP")

    assert "PLACSP" in source_codes
    assert source["operational_status"] == "metadata_adapter_validated"
    assert source["mcp_support"] is True
    assert source["monitor_support"] == "available"
    assert source["backfill_support"] == "available"
    assert source["evidence_adapter"] is False
    assert source["candidate_creation_allowed"] is False
    assert source["evidence_grade_allowed"] is False


def test_contratosabiertos_recommends_placsp_without_product_readiness():
    result = recommend_sources_for_consumer(consumer="contratosabiertos", limit=1)

    assert result["status"] == "ok"
    assert result["consumer"] == "contratosabiertos"
    assert result["demand_class"] == "public_procurement"
    recommendation = result["recommendations"][0]
    assert recommendation["source_code"] == "PLACSP"
    assert recommendation["source_status"]["registry_operational_status"] == (
        "metadata_adapter_validated"
    )
    assert recommendation["source_status"]["candidate_creation_allowed"] is False
    assert recommendation["source_status"]["evidence_grade_allowed"] is False
    assert recommendation["source_status"]["product_ready"] is False
