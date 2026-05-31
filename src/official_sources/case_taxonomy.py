from __future__ import annotations

from typing import Any

CASE_TAXONOMY = {
    "public_employment_alerts": {
        "demand_class": "public_employment_alerts",
        "case_type": "public_employment_alert",
        "primary_consumers": ["oposiciones2.0"],
        "consumer_aliases": ["oposiciones", "oposiciones2.0"],
        "topics": ["public_employment"],
        "jurisdictions": ["state", "autonomous", "provincial", "local"],
        "source_families": [
            "BOE",
            "autonomous_bulletins",
            "provincial_bulletins",
            "local_public_employment_surfaces",
        ],
        "intended_capabilities": [
            "metadata_discovery",
            "official_url_resolution",
            "dedupe_key_planning",
            "alert_grade_export_planning",
        ],
        "required_next_task": "TASK-SOURCE-COVERAGE-REOPEN-OPOSICIONES-001",
        "review_policy": "metadata_only_human_review",
        "safe_outputs": [
            "source recommendation",
            "metadata-only discovery record",
            "official URL",
            "manual-review alert input",
        ],
        "must_not_infer": [
            "candidate_ready",
            "evidence_grade",
            "notification_ready",
            "all_sources_green",
            "product_publication_allowed",
        ],
    },
    "education_aid_evidence": {
        "demand_class": "education_aid_evidence",
        "case_type": "education_aid",
        "primary_consumers": ["eduayudas"],
        "consumer_aliases": ["eduayudas"],
        "topics": ["education", "grants"],
        "jurisdictions": ["state", "autonomous", "provincial", "local"],
        "source_families": [
            "BDNS",
            "BOE",
            "autonomous_bulletins",
            "education_portals",
        ],
        "intended_capabilities": [
            "reviewable_evidence_packet",
            "official_identifier_resolution",
            "citation_planning",
            "integrity_metadata_planning",
        ],
        "required_next_task": "TASK-MCP-EVIDENCE-PACKETS-EDUAYUDAS-001",
        "review_policy": "evidence_staging_human_review",
        "safe_outputs": [
            "source recommendation",
            "reviewable evidence-packet candidate",
            "official URL",
            "manual-review staging input",
        ],
        "must_not_infer": [
            "aid_created",
            "aid_published",
            "eligibility_decided",
            "evidence_grade_without_adapter",
            "product_acceptance_allowed",
        ],
    },
    "benefit_source_discovery": {
        "demand_class": "benefit_source_discovery",
        "case_type": "benefit_source",
        "primary_consumers": ["la-ayuda"],
        "consumer_aliases": ["la-ayuda", "la_ayuda"],
        "topics": [
            "housing",
            "family",
            "dependency",
            "disability",
            "social_services",
            "benefits",
        ],
        "jurisdictions": ["state", "autonomous", "provincial", "local"],
        "source_families": [
            "BOE",
            "BDNS",
            "autonomous_bulletins",
            "official_portals",
            "sede_electronica",
        ],
        "intended_capabilities": [
            "official_source_discovery",
            "normative_reference_planning",
            "reviewable_evidence_packet",
            "uncertainty_state",
        ],
        "required_next_task": "TASK-MCP-BENEFIT-SOURCE-RESOLVER-LAAYUDA-001",
        "review_policy": "source_match_human_review",
        "safe_outputs": [
            "source recommendation",
            "official source candidate",
            "normative reference candidate",
            "manual-review uncertainty state",
        ],
        "must_not_infer": [
            "benefit_page_approved",
            "eligibility_decided",
            "amount_or_deadline_verified",
            "publication_ready",
            "legal_meaning_decided",
        ],
    },
    "fiscal_reference_resolution": {
        "demand_class": "fiscal_reference_resolution",
        "case_type": "fiscal_reference",
        "primary_consumers": ["renta-verificable"],
        "consumer_aliases": ["renta", "renta-verificable", "renta_verificable"],
        "topics": ["tax", "irpf", "deductions"],
        "jurisdictions": ["state", "autonomous", "foral", "ceuta_melilla"],
        "source_families": [
            "AEAT",
            "BOE",
            "autonomous_bulletins",
            "foral_tax_sources",
        ],
        "intended_capabilities": [
            "exact_reference_resolution",
            "official_identifier_resolution",
            "version_date_planning",
            "fiscal_uncertainty_state",
        ],
        "required_next_task": "TASK-MCP-FISCAL-REFERENCE-RESOLVER-RENTA-001",
        "review_policy": "fiscal_reference_human_review",
        "safe_outputs": [
            "source recommendation",
            "official reference candidate",
            "review-date requirement",
            "manual-review uncertainty state",
        ],
        "must_not_infer": [
            "tax_advice",
            "deduction_applicability_decided",
            "legal_meaning_decided",
            "fiscal_claim_verified",
            "product_publication_allowed",
        ],
    },
    "future_grants_registry": {
        "demand_class": "future_grants_registry",
        "case_type": "grant_registry",
        "primary_consumers": ["future_grants_registry"],
        "consumer_aliases": ["future_grants_registry"],
        "topics": ["grants", "subsidies"],
        "jurisdictions": ["state", "autonomous", "provincial", "local"],
        "source_families": [
            "BDNS",
            "BOE",
            "autonomous_bulletins",
            "grant_portals",
        ],
        "intended_capabilities": [
            "convocatoria_metadata",
            "official_identifier_resolution",
            "hash_and_trace_planning",
            "controlled_export_planning",
        ],
        "required_next_task": "TASK-MCP-BDNS-GRANTS-DEMAND-001",
        "review_policy": "future_consumer_profile_required",
        "safe_outputs": [
            "source-family recommendation",
            "convocatoria metadata planning",
            "manual-review export input",
        ],
        "must_not_infer": [
            "grant_published",
            "concession_published",
            "eligibility_decided",
            "privacy_review_completed",
            "product_publication_allowed",
        ],
    },
}

CONSUMER_ALIASES = {
    alias: demand_class
    for demand_class, profile in CASE_TAXONOMY.items()
    for alias in profile["consumer_aliases"]
}

SUPPORTED_JURISDICTIONS = [
    "state",
    "autonomous",
    "provincial",
    "local",
    "foral",
    "ceuta_melilla",
]

SUPPORTED_TOPICS = [
    "benefits",
    "deductions",
    "dependency",
    "disability",
    "education",
    "family",
    "grants",
    "housing",
    "irpf",
    "public_employment",
    "social_services",
    "subsidies",
    "tax",
]

SHARED_SAFETY = {
    "mode": "read_only",
    "writes_performed": False,
    "candidate_creation_allowed": False,
    "evidence_grade_allowed": False,
    "product_automation_allowed": False,
    "human_review_required": True,
}

CONTRACT_REFS = [
    "docs/SOURCE_STATUS_CONTRACT.md",
    "docs/MCP_CASE_TAXONOMY.md",
    "docs/MCP_DOWNSTREAM_DEMAND_CONTRACT.md",
    "docs/MCP_DOWNSTREAM_SOURCE_NEEDS_MATRIX.md",
]


def list_case_taxonomy(
    *,
    consumer: str | None = None,
    demand_class: str | None = None,
) -> dict[str, Any]:
    selected_demand_class = _resolve_requested_demand_class(
        consumer=consumer,
        demand_class=demand_class,
    )
    if selected_demand_class["status"] != "ok":
        return selected_demand_class

    case_items = _select_cases(selected_demand_class["demand_class"])
    return {
        "status": "ok",
        "resource_type": "case_taxonomy",
        **SHARED_SAFETY,
        "contract_refs": CONTRACT_REFS,
        "supported_demand_classes": sorted(CASE_TAXONOMY),
        "supported_consumers": sorted(
            {
                consumer
                for profile in CASE_TAXONOMY.values()
                for consumer in profile["primary_consumers"]
            }
        ),
        "supported_jurisdictions": SUPPORTED_JURISDICTIONS,
        "supported_topics": SUPPORTED_TOPICS,
        "count": len(case_items),
        "cases": case_items,
        "rules": [
            "deterministic taxonomy",
            "read-only planning only",
            "no source fetches",
            "no monitor execution",
            "no writes",
            "no candidates",
            "no evidence-grade promotion",
            "no downstream mutation",
            "manual review required",
        ],
    }


def _resolve_requested_demand_class(
    *,
    consumer: str | None,
    demand_class: str | None,
) -> dict[str, Any]:
    normalized_consumer = consumer.strip().lower() if consumer else None
    normalized_demand_class = demand_class.strip() if demand_class else None
    consumer_demand_class = None

    if normalized_consumer:
        consumer_demand_class = CONSUMER_ALIASES.get(normalized_consumer)
        if consumer_demand_class is None:
            return {
                "status": "unsupported_consumer",
                "consumer": consumer,
                "supported_consumers": sorted(
                    {
                        consumer
                        for profile in CASE_TAXONOMY.values()
                        for consumer in profile["primary_consumers"]
                    }
                ),
                "message": "Unknown downstream consumer; add an explicit taxonomy profile first.",
            }

    if normalized_demand_class and normalized_demand_class not in CASE_TAXONOMY:
        return {
            "status": "unsupported_demand_class",
            "demand_class": normalized_demand_class,
            "supported_demand_classes": sorted(CASE_TAXONOMY),
            "message": "Unknown demand class; add an explicit taxonomy profile first.",
        }

    if (
        consumer_demand_class is not None
        and normalized_demand_class is not None
        and consumer_demand_class != normalized_demand_class
    ):
        return {
            "status": "unsupported_demand_class",
            "consumer": consumer,
            "demand_class": normalized_demand_class,
            "supported_demand_class": consumer_demand_class,
            "message": "Demand class does not match the registered consumer taxonomy.",
        }

    return {
        "status": "ok",
        "demand_class": consumer_demand_class or normalized_demand_class,
    }


def _select_cases(demand_class: str | None) -> list[dict[str, Any]]:
    profiles = (
        [CASE_TAXONOMY[demand_class]]
        if demand_class is not None
        else [CASE_TAXONOMY[key] for key in sorted(CASE_TAXONOMY)]
    )
    return [_case_response(profile) for profile in profiles]


def _case_response(profile: dict[str, Any]) -> dict[str, Any]:
    return {
        "demand_class": profile["demand_class"],
        "case_type": profile["case_type"],
        "primary_consumers": list(profile["primary_consumers"]),
        "topics": list(profile["topics"]),
        "jurisdictions": list(profile["jurisdictions"]),
        "source_families": list(profile["source_families"]),
        "intended_capabilities": list(profile["intended_capabilities"]),
        "required_next_task": profile["required_next_task"],
        "review_policy": profile["review_policy"],
        "safe_outputs": list(profile["safe_outputs"]),
        "must_not_infer": list(profile["must_not_infer"]),
    }
