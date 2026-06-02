from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from official_sources.api_monitor import (
    APIFetcher,
    APIMonitorError,
    build_api_monitor_output_path,
    monitor_api_source,
)
from official_sources.case_taxonomy import list_case_taxonomy as taxonomy_list_case_taxonomy
from official_sources.downstream_planners import (
    build_evidence_packet as planner_build_evidence_packet,
)
from official_sources.downstream_planners import (
    resolve_fiscal_reference as planner_resolve_fiscal_reference,
)
from official_sources.downstream_planners import (
    resolve_normative_reference as planner_resolve_normative_reference,
)
from official_sources.html_monitor import (
    HTMLFetcher,
    HTMLMonitorError,
    build_html_monitor_output_path,
    monitor_html_source,
)
from official_sources.rss_monitor import (
    FeedFetcher,
    RSSMonitorError,
    build_rss_monitor_output_path,
    monitor_source_feed,
    validate_monitor_date,
)
from official_sources.source_registry import (
    MONITOR_CAPABLE_METHOD_TYPES,
    SourceRegistryError,
)
from official_sources.source_registry import (
    get_source as registry_get_source,
)
from official_sources.source_registry import (
    list_sources as registry_list_sources,
)

DEFAULT_RSS_DISCOVERY_ROOT = Path(__file__).resolve().parents[2] / "data" / "rss_monitor"
DEFAULT_API_DISCOVERY_ROOT = Path(__file__).resolve().parents[2] / "data" / "api_monitor"
DEFAULT_HTML_DISCOVERY_ROOT = Path(__file__).resolve().parents[2] / "data" / "html_monitor"
PROVINCIAL_HTML_DISCOVERY_PRIORITY = (
    "BOP_BARCELONA",
    "BOP_MALAGA",
    "BOP_BIZKAIA",
    "BOP_VALENCIA",
    "BOP_SEVILLA",
    "BOP_ZARAGOZA",
)
DOCUMENTED_DEFER_MARKERS = (
    "zk/javascript",
    "javascript application",
    "js-capable",
    "headless",
    "blocked by",
    "blocking reason",
    "defer until",
    "deferred until",
    "manual-only",
)
DOWNSTREAM_DEMAND_PROFILES = {
    "oposiciones2.0": {
        "consumer": "oposiciones2.0",
        "demand_class": "public_employment_alerts",
        "recommended_sources": (
            (
                "BOP_AVILA",
                "Metadata-only provincial HTML monitor for public-employment alert coverage.",
                "TASK-SOURCE-COVERAGE-REOPEN-OPOSICIONES-001",
            ),
            (
                "BOP_PONTEVEDRA",
                "Metadata-only provincial HTML monitor for public-employment alert coverage.",
                "TASK-SOURCE-COVERAGE-REOPEN-OPOSICIONES-001",
            ),
            (
                "BOP_SORIA",
                "Metadata-only provincial HTML monitor for public-employment alert coverage.",
                "TASK-SOURCE-COVERAGE-REOPEN-OPOSICIONES-001",
            ),
            (
                "BOP_CORDOBA",
                "Metadata-only provincial HTML monitor for public-employment alert coverage.",
                "TASK-SOURCE-COVERAGE-REOPEN-OPOSICIONES-001",
            ),
            (
                "BOP_GRANADA",
                "Metadata-only provincial HTML monitor for public-employment alert coverage.",
                "TASK-SOURCE-COVERAGE-REOPEN-OPOSICIONES-001",
            ),
            (
                "BOP_LEON",
                "Open-data signal for provincial public-employment alert coverage.",
                "TASK-SOURCE-COVERAGE-REOPEN-OPOSICIONES-001",
            ),
            (
                "BOP_PALENCIA",
                "Open-data signal for provincial public-employment alert coverage.",
                "TASK-SOURCE-COVERAGE-REOPEN-OPOSICIONES-001",
            ),
            (
                "BOP_SALAMANCA",
                "Open-data signal for provincial public-employment alert coverage.",
                "TASK-SOURCE-COVERAGE-REOPEN-OPOSICIONES-001",
            ),
        ),
        "missing_capabilities": (
            "BOP_CASTELLON and BOP_SEVILLA are now shared metadata-only monitors",
            "source-specific metadata-only monitors for selected provincial BOPs",
            "consumer-aware alert-grade export ranking",
            "documented DNS-dependent recovery risk for BOP_ALICANTE",
        ),
    },
    "eduayudas": {
        "consumer": "eduayudas",
        "demand_class": "education_aid_evidence",
        "recommended_sources": (
            (
                "BDNS",
                "Primary grants registry family for convocatorias and education-aid discovery.",
                "TASK-MCP-EVIDENCE-PACKETS-EDUAYUDAS-001",
            ),
            (
                "BOE",
                "State-level official evidence and citation source for education-aid records.",
                "TASK-MCP-EVIDENCE-PACKETS-EDUAYUDAS-001",
            ),
            (
                "BOJA",
                "Autonomous education-aid bulletin source with existing adapter history.",
                "TASK-MCP-EVIDENCE-PACKETS-EDUAYUDAS-001",
            ),
            (
                "BOCYL",
                "Autonomous education-aid bulletin source with existing adapter history.",
                "TASK-MCP-EVIDENCE-PACKETS-EDUAYUDAS-001",
            ),
            (
                "BOCM",
                "Autonomous education-aid bulletin source with RSS monitor support.",
                "TASK-MCP-EVIDENCE-PACKETS-EDUAYUDAS-001",
            ),
            (
                "DOGV",
                "Autonomous education-aid bulletin source with existing adapter history.",
                "TASK-MCP-EVIDENCE-PACKETS-EDUAYUDAS-001",
            ),
        ),
        "missing_capabilities": (
            "consumer-scoped education-aid evidence packet profile",
            "BDNS education-aid query profile",
            "product-side staging import remains explicit and reviewed",
        ),
    },
    "la-ayuda": {
        "consumer": "la-ayuda",
        "demand_class": "benefit_source_discovery",
        "recommended_sources": (
            (
                "BOE",
                "State-level legal and consolidated-law reference source for benefit cards.",
                "TASK-MCP-BENEFIT-SOURCE-RESOLVER-LAAYUDA-001",
            ),
            (
                "BDNS",
                "Grants registry family that may support aid and subsidy source discovery.",
                "TASK-MCP-BENEFIT-SOURCE-RESOLVER-LAAYUDA-001",
            ),
            (
                "BOCM",
                "Autonomous bulletin source for benefit/social-aid source discovery.",
                "TASK-MCP-BENEFIT-SOURCE-RESOLVER-LAAYUDA-001",
            ),
            (
                "BOJA",
                "Autonomous bulletin source for benefit/social-aid source discovery.",
                "TASK-MCP-BENEFIT-SOURCE-RESOLVER-LAAYUDA-001",
            ),
            (
                "DOGV",
                "Autonomous bulletin source for benefit/social-aid source discovery.",
                "TASK-MCP-BENEFIT-SOURCE-RESOLVER-LAAYUDA-001",
            ),
            (
                "BOCYL",
                "Autonomous bulletin source for benefit/social-aid source discovery.",
                "TASK-MCP-BENEFIT-SOURCE-RESOLVER-LAAYUDA-001",
            ),
        ),
        "missing_capabilities": (
            "official portal/sede source resolver",
            "normative reference matching for pending cards",
            "manual-review uncertainty state for ambiguous matches",
        ),
    },
    "renta-verificable": {
        "consumer": "renta-verificable",
        "demand_class": "fiscal_reference_resolution",
        "recommended_sources": (
            (
                "BOE",
                "Exact legal-reference source for state-level and consolidated legal citations.",
                "TASK-MCP-FISCAL-REFERENCE-RESOLVER-RENTA-001",
            ),
            (
                "BOCM",
                "Autonomous legal-reference source family for Madrid fiscal rules.",
                "TASK-MCP-FISCAL-REFERENCE-RESOLVER-RENTA-001",
            ),
            (
                "DOGV",
                "Autonomous legal-reference source family for Valencian fiscal rules.",
                "TASK-MCP-FISCAL-REFERENCE-RESOLVER-RENTA-001",
            ),
            (
                "DOGC",
                "Autonomous legal-reference source family for Catalan fiscal rules.",
                "TASK-MCP-FISCAL-REFERENCE-RESOLVER-RENTA-001",
            ),
            (
                "BON",
                "Foral/autonomous legal-reference source family for Navarra fiscal rules.",
                "TASK-MCP-FISCAL-REFERENCE-RESOLVER-RENTA-001",
            ),
            (
                "BOPV",
                "Autonomous legal-reference source family for Basque fiscal rules.",
                "TASK-MCP-FISCAL-REFERENCE-RESOLVER-RENTA-001",
            ),
        ),
        "missing_capabilities": (
            "AEAT-first fiscal reference model",
            "exact BOE/autonomous legal reference audit",
            "foral and Ceuta/Melilla fiscal source inventory",
        ),
    },
}
DOWNSTREAM_CONSUMER_ALIASES = {
    "eduayudas": "eduayudas",
    "la-ayuda": "la-ayuda",
    "la_ayuda": "la-ayuda",
    "oposiciones": "oposiciones2.0",
    "oposiciones2.0": "oposiciones2.0",
    "renta": "renta-verificable",
    "renta-verificable": "renta-verificable",
    "renta_verificable": "renta-verificable",
}
DOWNSTREAM_INTEGRATION_SMOKE_PROFILES = {
    "oposiciones2.0": {
        "consumer": "oposiciones2.0",
        "demand_class": "public_employment_alerts",
        "integration_mode": "json_export_preview_then_reviewed_import",
        "current_mcp_entrypoint": "recommend_sources_for_consumer",
        "smoke_call": {
            "tool": "recommend_sources_for_consumer",
            "arguments": {"consumer": "oposiciones2.0", "limit": 3},
        },
        "expected_status": "ok",
        "expected_output_contract": [
            "resource_type=downstream_source_recommendations",
            "consumer=oposiciones2.0",
            "demand_class=public_employment_alerts",
            "recommendations[0].source_status.product_ready=false",
            "recommendations[0].source_status.candidate_creation_allowed=false",
            "recommendations[0].source_status.evidence_grade_allowed=false",
        ],
        "downstream_preview_command": (
            "npm run import:strict-alerts:preview -- --file <strict_alerts.sample.jsonl>"
        ),
        "required_source_families": [
            "state_bulletin",
            "autonomous_bulletin",
            "provincial_bulletin",
        ],
        "required_fields": [
            "source_code",
            "source_name",
            "territory_code",
            "territory_name",
            "publication_date",
            "title",
            "normalized_title",
            "official_url",
            "alert_type",
            "alert_scope",
            "confidence",
            "matched_terms",
            "matched_rules",
            "dedupe_key",
            "review_status",
            "evidence_grade_status",
        ],
        "must_not_do": [
            "do not auto-create public employment processes",
            "do not send notifications",
            "do not treat alert-grade as evidence-grade",
            "do not import broad or review-only alerts through the strict path",
            "do not treat BOP_ALICANTE DNS recovery as candidate or evidence readiness",
        ],
        "known_risks": [
            "existing BOE helper is REST-shaped and needs an adapter for true MCP",
            "strict import source-code allowlists must remain aligned",
            "DOGV and provincial alerts may require manual review",
        ],
    },
    "eduayudas": {
        "consumer": "eduayudas",
        "demand_class": "education_aid_evidence",
        "integration_mode": "evidence_json_preview_then_private_staging",
        "current_mcp_entrypoint": "build_evidence_packet",
        "smoke_call": {
            "tool": "build_evidence_packet",
            "arguments": {"consumer": "eduayudas", "source_code": "BOE"},
        },
        "expected_status": "ok",
        "expected_output_contract": [
            "resource_type=evidence_packet_profile",
            "consumer=eduayudas",
            "profile=education_aid",
            "packet_status=profile_only",
            "staging_only=true",
        ],
        "downstream_preview_command": (
            "npm run official-sources:preview -- --file <evidence.json>"
        ),
        "required_source_families": [
            "state_bulletin",
            "grants_registry",
            "autonomous_bulletin",
            "education_portals",
        ],
        "required_fields": [
            "source_code",
            "resource_type",
            "official_identifier",
            "title",
            "publication_date",
            "version_date",
            "official_url",
            "citation",
            "integrity",
            "artifacts",
            "official_sources_candidate",
        ],
        "must_not_do": [
            "do not write to eduayudas database",
            "do not create source_candidates",
            "do not create or publish aid_programs",
            "do not treat likely_relevant as approval",
            "do not use records with integrity warnings for automatic use",
        ],
        "known_risks": [
            "downstream schema currently accepts BOE before broader source-code expansion",
            "BDNS and autonomous bulletin use requires separate evidence-model review",
        ],
    },
    "la-ayuda": {
        "consumer": "la-ayuda",
        "demand_class": "benefit_source_discovery",
        "integration_mode": "evidence_json_preview_then_pending_review_candidate",
        "current_mcp_entrypoint": "resolve_normative_reference",
        "smoke_call": {
            "tool": "resolve_normative_reference",
            "arguments": {
                "consumer": "la-ayuda",
                "topic": "housing",
                "jurisdiction": "state",
                "limit": 3,
            },
        },
        "expected_status": "manual_review_required",
        "expected_output_contract": [
            "resource_type=normative_reference_resolution",
            "consumer=la-ayuda",
            "resolution_status=source_leads_only",
            "exact_reference_resolved=false",
            "human_review_required=true",
        ],
        "downstream_preview_command": (
            "npm run official-sources:preview -- --file <evidence.json>"
        ),
        "required_source_families": [
            "state_bulletin",
            "grants_registry",
            "autonomous_bulletin",
            "official_portals",
            "sede_electronica",
        ],
        "required_fields": [
            "source_code",
            "resource_type",
            "official_identifier",
            "title",
            "publication_date",
            "version_date",
            "official_url",
            "citation",
            "integrity",
            "artifacts",
            "official_sources_candidate",
        ],
        "must_not_do": [
            "do not create active Markdown benefit pages automatically",
            "do not mark reviewStatus as revisada",
            "do not treat accept_for_downstream_pilot as approval",
            "do not treat PDF availability as approval",
            "do not decide eligibility, amount, deadline, or legal meaning",
        ],
        "known_risks": [
            "regional source authority is easy to overstate",
            "BDNS extracts may not contain full requirements or incompatibilities",
            "candidate staging must remain pending_review",
        ],
    },
    "renta-verificable": {
        "consumer": "renta-verificable",
        "demand_class": "fiscal_reference_resolution",
        "integration_mode": "build_time_reference_review_before_seed_import",
        "current_mcp_entrypoint": "resolve_fiscal_reference",
        "smoke_call": {
            "tool": "resolve_fiscal_reference",
            "arguments": {
                "consumer": "renta-verificable",
                "tax_year": 2025,
                "jurisdiction": "Madrid",
                "deduction_key": "madrid-alquiler-vivienda-habitual-joven",
                "limit": 3,
            },
        },
        "expected_status": "manual_review_required",
        "expected_output_contract": [
            "resource_type=fiscal_reference_resolution",
            "consumer=renta-verificable",
            "resolution_status=source_leads_only",
            "exact_reference_resolved=false",
            "source_leads[0].source_code=AEAT",
        ],
        "downstream_preview_command": (
            "python src/scripts/python/importers/import_json_to_sqlite.py --check"
        ),
        "required_source_families": [
            "AEAT",
            "state_legal_reference",
            "autonomous_bulletin",
            "foral_or_autonomous_bulletin",
        ],
        "required_fields": [
            "slug",
            "references",
            "type",
            "name",
            "url",
            "section",
            "jurisdiction",
            "status",
            "retrieved_at",
            "last_reviewed_at",
        ],
        "must_not_do": [
            "do not make MCP or AI a fiscal source of truth",
            "do not auto-promote records to verified",
            "do not fabricate fiscal facts, amounts, URLs, or applicability",
            "do not return definitive entitlement language",
            "do not make the live app depend on MCP availability",
        ],
        "known_risks": [
            "downstream fiscal enums and importer expectations need alignment before automation",
            "generic BOE URLs are not exact legal references",
            "project status is not official certification",
        ],
    },
}


def list_source_coverage() -> dict:
    sources = [
        {
            "source_code": source["source_code"],
            "name": source["name"],
            "jurisdiction_level": source["jurisdiction_level"],
            "operational_status": source["operational_status"],
            "monitor_support": source["monitor_support"],
            "evidence_adapter": source["evidence_adapter"],
        }
        for source in registry_list_sources()
    ]
    return {
        "resource_type": "source_coverage",
        "count": len(sources),
        "sources": sources,
    }


def get_source_status(*, source_code: str) -> dict:
    try:
        source = registry_get_source(source_code)
    except SourceRegistryError as exc:
        return _unknown_source(source_code, exc)
    return {
        "status": "ok",
        "resource_type": "source_status",
        "source": source,
        "safety": _source_safety(source),
    }


def list_monitorable_sources() -> dict:
    sources = []
    for source in registry_list_sources():
        methods = [
            _coverage_access_method(method)
            for method in source["access_methods"]
            if method["type"] in MONITOR_CAPABLE_METHOD_TYPES and method["status"] != "deprecated"
        ]
        if not methods or source["operational_status"] == "inventory_only":
            continue
        sources.append(
            {
                "source_code": source["source_code"],
                "name": source["name"],
                "operational_status": source["operational_status"],
                "monitor_support": source["monitor_support"],
                "access_methods": methods,
                "candidate_creation_allowed": source["candidate_creation_allowed"],
                "evidence_grade_allowed": source["evidence_grade_allowed"],
            }
        )
    return {
        "resource_type": "monitorable_sources",
        "count": len(sources),
        "sources": sources,
    }


def list_latest_discovery_entries(
    *,
    source_code: str,
    date: str | None = None,
    limit: int | None = 20,
    output_root: Path | None = None,
) -> dict:
    try:
        source = registry_get_source(source_code)
    except SourceRegistryError as exc:
        return _unknown_source(source_code, exc)
    normalized_source_code = source["source_code"]
    if limit is not None and limit < 1:
        return {
            "status": "invalid_request",
            "source_code": normalized_source_code,
            "message": "limit must be greater than zero",
        }

    rss_root = output_root or DEFAULT_RSS_DISCOVERY_ROOT
    api_root = output_root or DEFAULT_API_DISCOVERY_ROOT
    html_root = output_root or DEFAULT_HTML_DISCOVERY_ROOT
    target_date = _resolve_discovery_date(
        rss_root,
        api_root,
        html_root,
        normalized_source_code,
        date,
    )
    if target_date is None:
        return {
            "status": "empty",
            "source_code": normalized_source_code,
            "date": None,
            "output_paths": {
                "rss": str(rss_root / normalized_source_code),
                "api": str(api_root / normalized_source_code),
                "html": str(html_root / normalized_source_code),
            },
            "entries": [],
            "count": 0,
            "message": "No discovery output exists for this source.",
        }

    output_paths = {
        "rss": build_rss_monitor_output_path(rss_root, normalized_source_code, target_date),
        "api": build_api_monitor_output_path(api_root, normalized_source_code, target_date),
        "html": build_html_monitor_output_path(html_root, normalized_source_code, target_date),
    }
    existing_output_paths = {
        discovery_type: path for discovery_type, path in output_paths.items() if path.exists()
    }
    if not existing_output_paths:
        return {
            "status": "empty",
            "source_code": normalized_source_code,
            "date": target_date,
            "output_paths": {key: str(path) for key, path in output_paths.items()},
            "entries": [],
            "count": 0,
            "message": "No discovery output exists for this source/date.",
        }

    try:
        entries: list[dict[str, Any]] = []
        for discovery_type, output_path in existing_output_paths.items():
            entries.extend(
                _with_discovery_type(
                    _read_discovery_jsonl(output_path, _remaining_limit(limit, len(entries))),
                    discovery_type,
                )
            )
            if limit is not None and len(entries) >= limit:
                break
    except json.JSONDecodeError as exc:
        return {
            "status": "invalid_output",
            "source_code": normalized_source_code,
            "date": target_date,
            "output_paths": {key: str(path) for key, path in existing_output_paths.items()},
            "entries": [],
            "count": 0,
            "message": f"Discovery output is not valid JSONL: {exc}",
        }
    return {
        "status": "ok",
        "resource_type": "discovery_entries",
        "source_code": normalized_source_code,
        "date": target_date,
        "discovery_types": list(existing_output_paths),
        "output_paths": {key: str(path) for key, path in existing_output_paths.items()},
        "entries": entries,
        "count": len(entries),
        "discovery_only": True,
        "safety": _source_safety(source),
    }


def preview_discovery(
    *,
    source_code: str,
    date: str,
    limit: int = 1,
    discovery_type: str | None = None,
    rss_fetcher: FeedFetcher | None = None,
    api_fetcher: APIFetcher | None = None,
    html_fetcher: HTMLFetcher | None = None,
) -> dict:
    normalized_request_code = source_code.strip().upper()
    if normalized_request_code in {"", "*", "ALL"} or "," in normalized_request_code:
        return {
            "status": "invalid_request",
            "source_code": normalized_request_code,
            "message": "preview_discovery requires one explicit source_code",
        }
    if limit < 1 or limit > 10:
        return {
            "status": "invalid_request",
            "source_code": normalized_request_code,
            "message": "limit must be between 1 and 10",
        }
    requested_type = discovery_type.strip().lower() if discovery_type else None
    if requested_type is not None and requested_type not in {"rss", "api", "html"}:
        return {
            "status": "invalid_request",
            "source_code": normalized_request_code,
            "discovery_type": requested_type,
            "message": "discovery_type must be one of: rss, api, html",
        }
    try:
        source = registry_get_source(normalized_request_code)
    except SourceRegistryError as exc:
        return _unknown_source(normalized_request_code, exc)

    available_types = _implemented_preview_types(source)
    if source["operational_status"] == "inventory_only" or not available_types:
        return _not_monitorable(
            source,
            requested_type,
            "Source does not have validated monitor support for MCP preview.",
        )
    selected_type = requested_type or _select_preview_type(available_types)
    if selected_type is None:
        return {
            "status": "invalid_request",
            "source_code": source["source_code"],
            "available_discovery_types": available_types,
            "message": "Multiple discovery types are available; provide discovery_type.",
        }
    if selected_type not in available_types:
        return _not_monitorable(
            source,
            selected_type,
            f"Source does not have a validated {selected_type} monitor for MCP preview.",
        )

    try:
        result = _run_preview(
            source,
            selected_type,
            target_date=date,
            limit=limit,
            rss_fetcher=rss_fetcher,
            api_fetcher=api_fetcher,
            html_fetcher=html_fetcher,
        )
    except (RSSMonitorError, APIMonitorError, HTMLMonitorError) as exc:
        return {
            "status": "invalid_request",
            "source_code": source["source_code"],
            "discovery_type": selected_type,
            "message": str(exc),
        }

    records = result.records[:limit]
    return {
        "status": "ok",
        "resource_type": "discovery_preview",
        "source_code": source["source_code"],
        "discovery_type": selected_type,
        "date": date,
        "mode": "preview",
        "records": records,
        "count": len(records),
        "warnings": _preview_warnings(records),
        "output_written": False,
        "discovery_only": True,
        "safety": _source_safety(source),
    }


def recommend_next_sources(
    *,
    limit: int = 5,
    output_root: Path | None = None,
) -> dict:
    if limit < 1 or limit > 20:
        return {
            "status": "invalid_request",
            "message": "limit must be between 1 and 20",
        }

    rss_root = output_root or DEFAULT_RSS_DISCOVERY_ROOT
    api_root = output_root or DEFAULT_API_DISCOVERY_ROOT
    html_root = output_root or DEFAULT_HTML_DISCOVERY_ROOT
    candidates = [
        _build_provincial_html_recommendation(
            source,
            rss_root=rss_root,
            api_root=api_root,
            html_root=html_root,
        )
        for source in registry_list_sources()
        if _is_provincial_html_pilot_candidate(source)
    ]
    recommendations = sorted(candidates, key=_provincial_html_recommendation_sort_key)[:limit]
    return {
        "status": "ok",
        "resource_type": "source_recommendations",
        "strategy": "provincial_html_discovery_pilot",
        "count": len(recommendations),
        "recommendations": recommendations,
        "rules": [
            "deterministic registry scan",
            "provincial inventory_only sources only",
            "documented blocked/deferred sources excluded from normal ranking",
            "documented provincial pilot waves prioritized before alphabetical fallback",
            "no monitor execution",
            "no writes",
            "no candidates",
            "no evidence-grade records",
        ],
        "safety": {
            "creates_candidates": False,
            "creates_evidence_grade": False,
            "writes_jsonl": False,
            "runs_previews": False,
            "downloads_files": False,
            "touches_downstream": False,
        },
    }


def recommend_sources_for_consumer(
    *,
    consumer: str,
    demand_class: str | None = None,
    limit: int = 5,
) -> dict:
    if limit < 1 or limit > 20:
        return {
            "status": "invalid_request",
            "message": "limit must be between 1 and 20",
        }
    normalized_consumer = _normalize_downstream_consumer(consumer)
    if normalized_consumer is None:
        return {
            "status": "unsupported_consumer",
            "consumer": consumer,
            "supported_consumers": sorted(
                profile["consumer"] for profile in DOWNSTREAM_DEMAND_PROFILES.values()
            ),
            "message": (
                "Unknown downstream consumer; add an explicit profile before recommending "
                "source work."
            ),
        }

    profile = DOWNSTREAM_DEMAND_PROFILES[normalized_consumer]
    expected_demand_class = profile["demand_class"]
    requested_demand_class = demand_class.strip() if demand_class else expected_demand_class
    if requested_demand_class != expected_demand_class:
        return {
            "status": "unsupported_demand_class",
            "consumer": profile["consumer"],
            "demand_class": requested_demand_class,
            "supported_demand_class": expected_demand_class,
            "message": "Demand class does not match the registered downstream profile.",
        }

    recommendations = [
        _build_downstream_source_recommendation(
            source_code,
            reason,
            next_task,
            demand_class=expected_demand_class,
        )
        for source_code, reason, next_task in profile["recommended_sources"][:limit]
    ]
    return {
        "status": "ok",
        "resource_type": "downstream_source_recommendations",
        "consumer": profile["consumer"],
        "demand_class": expected_demand_class,
        "mode": "read_only",
        "writes_performed": False,
        "candidate_creation_allowed": False,
        "evidence_grade_allowed": False,
        "product_automation_allowed": False,
        "human_review_required": True,
        "contract_refs": [
            "docs/SOURCE_STATUS_CONTRACT.md",
            "docs/MCP_DOWNSTREAM_DEMAND_CONTRACT.md",
            "docs/MCP_DOWNSTREAM_SOURCE_NEEDS_MATRIX.md",
        ],
        "count": len(recommendations),
        "recommendations": recommendations,
        "missing_capabilities": list(profile["missing_capabilities"]),
        "rules": [
            "deterministic downstream-demand profile",
            "registry read only",
            "no monitor execution",
            "no live fetches",
            "no writes",
            "no candidates",
            "no evidence-grade records",
            "no downstream mutation",
        ],
    }


def list_downstream_integration_smokes(*, consumer: str | None = None) -> dict:
    profiles = _select_downstream_integration_smoke_profiles(consumer)
    if isinstance(profiles, dict):
        return profiles

    return {
        "status": "ok",
        "resource_type": "downstream_integration_smoke_matrix",
        "version": "read-only-upstream-v1",
        "mode": "read_only",
        "writes_performed": False,
        "candidate_creation_allowed": False,
        "evidence_grade_allowed": False,
        "product_automation_allowed": False,
        "human_review_required": True,
        "contract_refs": [
            "docs/SOURCE_STATUS_CONTRACT.md",
            "docs/MCP_DOWNSTREAM_DEMAND_CONTRACT.md",
            "docs/MCP_DOWNSTREAM_INTEGRATION_CLOSURE.md",
            "docs/MCP_TOOLS.md",
        ],
        "count": len(profiles),
        "smokes": [_integration_smoke_profile(profile) for profile in profiles],
        "rules": [
            "read-only upstream only",
            "consumer preview before import",
            "no downstream writes from MCP",
            "no candidate creation",
            "no evidence-grade promotion",
            "no product publication",
            "no legal, fiscal, eligibility, ranking, or approval conclusions",
            "manual review required before product automation",
        ],
    }


def check_downstream_integration_smokes(*, consumer: str | None = None) -> dict:
    profiles = _select_downstream_integration_smoke_profiles(consumer)
    if isinstance(profiles, dict):
        return profiles

    results = [_run_downstream_integration_smoke(profile) for profile in profiles]
    passed_count = sum(1 for result in results if result["passed"] is True)
    return {
        "status": "ok" if passed_count == len(results) else "failed",
        "resource_type": "downstream_integration_smoke_run",
        "version": "read-only-upstream-v1",
        "mode": "read_only",
        "writes_performed": False,
        "candidate_creation_allowed": False,
        "evidence_grade_allowed": False,
        "product_automation_allowed": False,
        "human_review_required": True,
        "execution_scope": "official_sources_internal_mcp_calls_only",
        "downstream_commands_executed": False,
        "monitor_previews_executed": False,
        "live_fetches_performed": False,
        "jsonl_written": False,
        "registry_mutated": False,
        "contract_refs": [
            "docs/SOURCE_STATUS_CONTRACT.md",
            "docs/MCP_DOWNSTREAM_DEMAND_CONTRACT.md",
            "docs/MCP_DOWNSTREAM_INTEGRATION_CLOSURE.md",
            "docs/MCP_TOOLS.md",
        ],
        "count": len(results),
        "passed_count": passed_count,
        "failed_count": len(results) - passed_count,
        "results": results,
        "rules": [
            "execute only deterministic in-process official-sources MCP/planner calls",
            "do not run downstream preview/import commands",
            "do not run monitor previews",
            "do not fetch live sources",
            "do not write JSONL",
            "do not mutate registry",
            "do not create candidates",
            "do not create evidence-grade records",
            "do not publish product content",
        ],
    }


def list_case_taxonomy(
    *,
    consumer: str | None = None,
    demand_class: str | None = None,
) -> dict:
    return taxonomy_list_case_taxonomy(
        consumer=consumer,
        demand_class=demand_class,
    )


def build_evidence_packet(
    *,
    consumer: str,
    source_code: str | None = None,
    official_identifier: str | None = None,
    profile: str | None = None,
) -> dict:
    return planner_build_evidence_packet(
        consumer=consumer,
        source_code=source_code,
        official_identifier=official_identifier,
        profile=profile,
    )


def resolve_normative_reference(
    *,
    consumer: str,
    topic: str,
    jurisdiction: str,
    known_title: str | None = None,
    limit: int = 10,
) -> dict:
    return planner_resolve_normative_reference(
        consumer=consumer,
        topic=topic,
        jurisdiction=jurisdiction,
        known_title=known_title,
        limit=limit,
    )


def resolve_fiscal_reference(
    *,
    consumer: str,
    tax_year: int,
    jurisdiction: str,
    deduction_key: str | None = None,
    limit: int = 10,
) -> dict:
    return planner_resolve_fiscal_reference(
        consumer=consumer,
        tax_year=tax_year,
        jurisdiction=jurisdiction,
        deduction_key=deduction_key,
        limit=limit,
    )


def _select_downstream_integration_smoke_profiles(
    consumer: str | None,
) -> list[dict[str, Any]] | dict[str, Any]:
    if consumer is not None:
        normalized_consumer = _normalize_downstream_consumer(consumer)
        if normalized_consumer is None:
            return {
                "status": "unsupported_consumer",
                "consumer": consumer,
                "supported_consumers": sorted(DOWNSTREAM_INTEGRATION_SMOKE_PROFILES),
                "message": (
                    "Unknown downstream consumer; add an explicit integration smoke profile first."
                ),
            }
        return [DOWNSTREAM_INTEGRATION_SMOKE_PROFILES[normalized_consumer]]
    return [
        DOWNSTREAM_INTEGRATION_SMOKE_PROFILES[key]
        for key in sorted(DOWNSTREAM_INTEGRATION_SMOKE_PROFILES)
    ]


def _integration_smoke_profile(profile: dict[str, Any]) -> dict[str, Any]:
    return {
        **profile,
        "mode": "read_only",
        "writes_performed": False,
        "candidate_creation_allowed": False,
        "evidence_grade_allowed": False,
        "product_automation_allowed": False,
        "human_review_required": True,
        "closure_status": "ready_for_product_side_preview",
        "acceptance_gate": (
            "Downstream product must run its preview/import check and keep records in manual "
            "review before any product write or publication."
        ),
    }


def _run_downstream_integration_smoke(profile: dict[str, Any]) -> dict[str, Any]:
    smoke_call = profile["smoke_call"]
    tool_name = smoke_call["tool"]
    arguments = smoke_call["arguments"]
    try:
        output = _call_downstream_integration_smoke_tool(tool_name, arguments)
    except Exception as exc:
        output = {
            "status": "failed",
            "resource_type": "downstream_integration_smoke_error",
            "message": str(exc),
            "error_type": type(exc).__name__,
        }

    status_check = {
        "name": "expected_status",
        "expected": profile["expected_status"],
        "actual": output.get("status"),
        "passed": output.get("status") == profile["expected_status"],
    }
    safety_checks = _downstream_smoke_safety_checks(output)
    contract_checks = [
        _evaluate_expected_output_contract(output, expectation)
        for expectation in profile["expected_output_contract"]
    ]
    all_checks = [status_check, *safety_checks, *contract_checks]
    return {
        "consumer": profile["consumer"],
        "demand_class": profile["demand_class"],
        "integration_mode": profile["integration_mode"],
        "smoke_call": smoke_call,
        "expected_status": profile["expected_status"],
        "actual_status": output.get("status"),
        "passed": all(check["passed"] is True for check in all_checks),
        "checks": all_checks,
        "output_summary": _downstream_smoke_output_summary(output),
        "downstream_command_executed": False,
        "monitor_preview_executed": False,
        "live_fetch_performed": False,
        "writes_performed": False,
        "candidate_creation_allowed": False,
        "evidence_grade_allowed": False,
        "product_automation_allowed": False,
        "human_review_required": True,
    }


def _call_downstream_integration_smoke_tool(
    tool_name: str,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    if tool_name == "recommend_sources_for_consumer":
        return recommend_sources_for_consumer(**arguments)
    if tool_name == "build_evidence_packet":
        return build_evidence_packet(**arguments)
    if tool_name == "resolve_normative_reference":
        return resolve_normative_reference(**arguments)
    if tool_name == "resolve_fiscal_reference":
        return resolve_fiscal_reference(**arguments)
    raise ValueError(f"Unsupported internal smoke tool: {tool_name}")


def _downstream_smoke_safety_checks(output: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        _check_output_value(output, "mode", "read_only"),
        _check_output_value(output, "writes_performed", False),
        _check_output_value(output, "candidate_creation_allowed", False),
        _check_output_value(output, "evidence_grade_allowed", False),
        _check_output_value(output, "product_automation_allowed", False),
        _check_output_value(output, "human_review_required", True),
    ]


def _evaluate_expected_output_contract(
    output: dict[str, Any],
    expectation: str,
) -> dict[str, Any]:
    if "=" not in expectation:
        return {
            "name": expectation,
            "expected": None,
            "actual": None,
            "passed": False,
            "message": "Expected contract item must use path=value syntax.",
        }
    path, expected_value = expectation.split("=", 1)
    return _check_output_value(output, path, _parse_expected_value(expected_value))


def _check_output_value(output: dict[str, Any], path: str, expected: Any) -> dict[str, Any]:
    found, actual = _get_path_value(output, path)
    return {
        "name": path,
        "expected": expected,
        "actual": actual if found else None,
        "passed": found and actual == expected,
    }


def _parse_expected_value(value: str) -> Any:
    normalized = value.strip()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    if normalized == "null":
        return None
    if normalized.isdigit():
        return int(normalized)
    return normalized


def _get_path_value(data: Any, path: str) -> tuple[bool, Any]:
    current = data
    for part in path.split("."):
        key, index = _parse_path_part(part)
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return False, None
        if index is not None:
            if isinstance(current, list) and 0 <= index < len(current):
                current = current[index]
            else:
                return False, None
    return True, current


def _parse_path_part(part: str) -> tuple[str, int | None]:
    if part.endswith("]") and "[" in part:
        key, raw_index = part[:-1].split("[", 1)
        return key, int(raw_index)
    return part, None


def _downstream_smoke_output_summary(output: dict[str, Any]) -> dict[str, Any]:
    summary = {
        "status": output.get("status"),
        "resource_type": output.get("resource_type"),
        "consumer": output.get("consumer"),
        "demand_class": output.get("demand_class"),
        "mode": output.get("mode"),
        "writes_performed": output.get("writes_performed"),
        "candidate_creation_allowed": output.get("candidate_creation_allowed"),
        "evidence_grade_allowed": output.get("evidence_grade_allowed"),
        "product_automation_allowed": output.get("product_automation_allowed"),
        "human_review_required": output.get("human_review_required"),
    }
    if "count" in output:
        summary["count"] = output["count"]
    if "resolution_status" in output:
        summary["resolution_status"] = output["resolution_status"]
    if "exact_reference_resolved" in output:
        summary["exact_reference_resolved"] = output["exact_reference_resolved"]
    return summary


def _source_safety(source: dict[str, Any]) -> dict:
    return {
        "candidate_creation_allowed": source["candidate_creation_allowed"],
        "evidence_grade_allowed": source["evidence_grade_allowed"],
        "rss_discovery_is_evidence": False,
        "rss_discovery_is_candidate": False,
        "api_discovery_is_evidence": False,
        "api_discovery_is_candidate": False,
        "html_discovery_is_evidence": False,
        "html_discovery_is_candidate": False,
    }


def _normalize_downstream_consumer(value: str) -> str | None:
    normalized = value.strip().lower()
    return DOWNSTREAM_CONSUMER_ALIASES.get(normalized)


def _build_downstream_source_recommendation(
    source_code: str,
    reason: str,
    next_task: str,
    *,
    demand_class: str,
) -> dict:
    try:
        source = registry_get_source(source_code)
    except SourceRegistryError:
        return {
            "source_code": source_code,
            "registered": False,
            "demand_class": demand_class,
            "reason": reason,
            "next_task": next_task,
            "status": "missing_registry_entry",
            "human_review_required": True,
            "product_ready": False,
        }
    return {
        "source_code": source["source_code"],
        "name": source["name"],
        "demand_class": demand_class,
        "reason": reason,
        "next_task": next_task,
        "source_status": _downstream_source_status(source),
    }


def _downstream_source_status(source: dict[str, Any]) -> dict:
    runtime_health = "degraded/manual-review" if source.get("degraded") is True else "unknown"
    safe_uses = ["inventory_awareness", "manual_review"]
    if source["operational_status"] == "monitor_validated":
        safe_uses.insert(0, "metadata_discovery")
    elif source["operational_status"] == "metadata_adapter_validated":
        safe_uses.insert(0, "upstream_metadata")
    return {
        "registered": True,
        "registry_operational_status": source["operational_status"],
        "runtime_health": runtime_health,
        "monitor_support": source["monitor_support"],
        "evidence_adapter": source["evidence_adapter"],
        "candidate_creation_allowed": source["candidate_creation_allowed"],
        "evidence_grade_allowed": source["evidence_grade_allowed"],
        "product_ready": False,
        "safe_downstream_uses": safe_uses,
        "must_not_infer": [
            "candidate_ready",
            "evidence_grade",
            "publication_ready",
            "runtime_healthy",
            "product_automation_allowed",
        ],
    }


def _is_provincial_html_pilot_candidate(source: dict[str, Any]) -> bool:
    return (
        source["jurisdiction_level"] == "provincial"
        and source["operational_status"] == "inventory_only"
        and source["monitor_support"] == "none"
        and source["candidate_creation_allowed"] is False
        and source["evidence_grade_allowed"] is False
        and bool(str(source.get("official_landing_url", "")).strip())
        and not _has_documented_normal_ranking_blocker(source)
    )


def _has_documented_normal_ranking_blocker(source: dict[str, Any]) -> bool:
    if source["operational_status"] in {"blocked", "paused", "deprecated"}:
        return True
    if any(method.get("status") == "blocked" for method in source.get("access_methods", [])):
        return True

    evidence_text = " ".join(
        [
            str(source.get("notes", "")),
            *[str(limitation) for limitation in source.get("limitations", [])],
            *[str(method.get("notes", "")) for method in source.get("access_methods", [])],
        ]
    ).lower()
    return any(marker in evidence_text for marker in DOCUMENTED_DEFER_MARKERS)


def _provincial_html_recommendation_sort_key(item: dict[str, Any]) -> tuple[int, str]:
    priority = {
        source_code: index for index, source_code in enumerate(PROVINCIAL_HTML_DISCOVERY_PRIORITY)
    }
    source_code = item["source_code"]
    return (priority.get(source_code, len(priority)), source_code)


def _build_provincial_html_recommendation(
    source: dict[str, Any],
    *,
    rss_root: Path,
    api_root: Path,
    html_root: Path,
) -> dict:
    source_code = source["source_code"]
    latest_cache_date = _resolve_discovery_date(rss_root, api_root, html_root, source_code, None)
    return {
        "source_code": source_code,
        "name": source["name"],
        "jurisdiction_level": source["jurisdiction_level"],
        "operational_status": source["operational_status"],
        "monitor_support": source["monitor_support"],
        "official_landing_url": source["official_landing_url"],
        "recommended_task": "provincial_html_discovery_pilot",
        "confidence": "medium",
        "reason": (
            "Provincial inventory_only source with official landing URL and no validated "
            "monitor; suitable for one-source HTML discovery verification."
        ),
        "constraints": [
            "metadata-only",
            "preview first",
            "no PDFs",
            "no candidates",
            "no evidence-grade",
            "no downstream writes",
            "one source only",
        ],
        "limitations": source.get("limitations", []),
        "discovery_cache_status": (
            "has_discovery_cache" if latest_cache_date is not None else "no_discovery_cache"
        ),
        "latest_cache_date": latest_cache_date,
        "implemented_preview_available": bool(_implemented_preview_types(source)),
        "candidate_creation_allowed": source["candidate_creation_allowed"],
        "evidence_grade_allowed": source["evidence_grade_allowed"],
    }


def _implemented_preview_types(source: dict[str, Any]) -> list[str]:
    source_code = source["source_code"]
    access_methods = source.get("access_methods", [])
    preview_types = []
    if any(
        method.get("type") in {"rss", "atom"}
        and method.get("status") == "validated"
        and str(method.get("url", "")).strip()
        for method in access_methods
    ):
        preview_types.append("rss")
    if source_code in {
        "AYTO_ZARAGOZA_EMPLEO",
        "BOPV",
        "BOR",
        "BOP_CACERES",
        "BOP_HUELVA",
        "BOP_OURENSE",
    } and any(
        method.get("type") == "api"
        and method.get("status") == "validated"
        and str(method.get("url", "")).strip()
        for method in access_methods
    ):
        preview_types.append("api")
    if source_code in {
        "DOCM",
        "BOP_A_CORUNA",
        "BOP_ALBACETE",
        "BOP_ALICANTE",
        "BOP_ALMERIA",
        "BOP_ARABA_ALAVA",
        "BOP_AVILA",
        "BOP_BARCELONA",
        "BON",
        "BOP_BIZKAIA",
        "BOP_BURGOS",
        "BOP_CADIZ",
        "BOP_CASTELLON",
        "BOP_CIUDAD_REAL",
        "BOP_CORDOBA",
        "BOP_CUENCA",
        "BOP_GIRONA",
        "BOP_GIPUZKOA",
        "BOP_GRANADA",
        "BOP_HUESCA",
        "BOP_JAEN",
        "BOP_LAS_PALMAS",
        "BOP_LEON",
        "BOP_LLEIDA",
        "BOP_MALAGA",
        "BOP_PALENCIA",
        "BOP_PONTEVEDRA",
        "BOP_SALAMANCA",
        "BOP_SEGOVIA",
        "BOP_SEVILLA",
        "BOP_SANTA_CRUZ_TENERIFE",
        "BOP_SORIA",
        "BOP_TARRAGONA",
        "BOP_TERUEL",
        "BOP_TOLEDO",
        "BOP_VALENCIA",
        "BOP_VALLADOLID",
        "BOP_ZARAGOZA",
        "BOP_ZAMORA",
        "BOPA",
    } and any(
        method.get("type") == "html"
        and method.get("status") == "validated"
        and str(method.get("url", "")).strip()
        for method in access_methods
    ):
        preview_types.append("html")
    return preview_types


def _select_preview_type(available_types: list[str]) -> str | None:
    if len(available_types) == 1:
        return available_types[0]
    return None


def _run_preview(
    source: dict[str, Any],
    discovery_type: str,
    *,
    target_date: str,
    limit: int,
    rss_fetcher: FeedFetcher | None,
    api_fetcher: APIFetcher | None,
    html_fetcher: HTMLFetcher | None,
):
    if discovery_type == "rss":
        return monitor_source_feed(
            source,
            fetcher=rss_fetcher,
            target_date=target_date,
            limit=limit,
        )
    if discovery_type == "api":
        return monitor_api_source(
            source,
            fetcher=api_fetcher,
            target_date=target_date,
            limit=limit,
        )
    if discovery_type == "html":
        return monitor_html_source(
            source,
            fetcher=html_fetcher,
            target_date=target_date,
            limit=limit,
        )
    raise ValueError(f"Unknown discovery_type: {discovery_type}")


def _preview_warnings(records: list[dict[str, Any]]) -> list[str]:
    warnings = []
    for record in records:
        for warning in record.get("warnings", []):
            if warning not in warnings:
                warnings.append(warning)
    return warnings


def _coverage_access_method(method: dict[str, Any]) -> dict:
    return {
        "type": method["type"],
        "url": method.get("url"),
        "status": method["status"],
        "notes": method.get("notes"),
    }


def _unknown_source(source_code: str, exc: SourceRegistryError) -> dict:
    return {
        "status": "unknown_source",
        "source_code": source_code.strip().upper(),
        "message": str(exc),
    }


def _not_monitorable(source: dict[str, Any], discovery_type: str | None, message: str) -> dict:
    result = {
        "status": "not_monitorable",
        "source_code": source["source_code"],
        "operational_status": source.get("operational_status"),
        "monitor_support": source.get("monitor_support"),
        "blocked_vps": source.get("blocked_vps", False),
        "pending_relay": source.get("pending_relay", False),
        "candidate_creation_allowed": source.get("candidate_creation_allowed"),
        "evidence_grade_allowed": source.get("evidence_grade_allowed"),
        "message": message,
    }
    if discovery_type is not None:
        result["discovery_type"] = discovery_type
    return result


def _resolve_discovery_date(
    rss_root: Path,
    api_root: Path,
    html_root: Path,
    source_code: str,
    value: str | None,
) -> str | None:
    if value is not None:
        try:
            return validate_monitor_date(value)
        except RSSMonitorError:
            return value
    candidates = (
        _dated_output_candidates(rss_root, source_code, "rss")
        + _dated_output_candidates(api_root, source_code, "api")
        + _dated_output_candidates(html_root, source_code, "html")
    )
    return sorted(candidates, reverse=True)[0] if candidates else None


def _dated_output_candidates(root: Path, source_code: str, discovery_type: str) -> list[str]:
    source_root = root / source_code
    if not source_root.exists():
        return []
    return [
        path.name
        for path in source_root.iterdir()
        if path.is_dir()
        and _discovery_output_path(root, source_code, path.name, discovery_type).exists()
    ]


def _discovery_output_path(
    root: Path,
    source_code: str,
    target_date: str,
    discovery_type: str,
) -> Path:
    if discovery_type == "rss":
        return build_rss_monitor_output_path(root, source_code, target_date)
    if discovery_type == "api":
        return build_api_monitor_output_path(root, source_code, target_date)
    if discovery_type == "html":
        return build_html_monitor_output_path(root, source_code, target_date)
    raise ValueError(f"Unknown discovery_type: {discovery_type}")


def _read_discovery_jsonl(output_path: Path, limit: int | None) -> list[dict[str, Any]]:
    entries = []
    for line in output_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        entries.append(json.loads(line))
        if limit is not None and len(entries) >= limit:
            break
    return entries


def _with_discovery_type(
    entries: list[dict[str, Any]],
    discovery_type: str,
) -> list[dict[str, Any]]:
    return [entry | {"discovery_type": discovery_type} for entry in entries]


def _remaining_limit(limit: int | None, current_count: int) -> int | None:
    if limit is None:
        return None
    return max(limit - current_count, 0)
