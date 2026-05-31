from __future__ import annotations

from typing import Any

from official_sources.case_taxonomy import CONTRACT_REFS, SHARED_SAFETY
from official_sources.source_registry import SourceRegistryError, get_source

EDUCATION_AID_SOURCE_PROFILES = {
    "BDNS": {
        "source_family": "grants_registry",
        "priority": 1,
        "why": "Primary official convocatoria registry for grants and education-aid discovery.",
        "required_fields": [
            "convocatoria_id",
            "official_url",
            "convocatoria_title",
            "granting_body",
            "publication_date",
            "application_deadline",
            "bdns_hash_or_trace",
        ],
    },
    "BOE": {
        "source_family": "state_bulletin",
        "priority": 2,
        "why": "State official bulletin and citation source for education-aid evidence.",
        "required_fields": [
            "official_identifier",
            "official_url",
            "title",
            "department",
            "publication_date",
            "citation",
            "integrity_trace",
        ],
    },
    "BOJA": {
        "source_family": "autonomous_bulletin",
        "priority": 3,
        "why": "Autonomous bulletin source for Andalusia education-aid evidence.",
        "required_fields": [
            "official_url",
            "title",
            "publication_date",
            "issuing_body",
            "jurisdiction",
            "reviewed_at",
        ],
    },
    "BOCYL": {
        "source_family": "autonomous_bulletin",
        "priority": 4,
        "why": "Autonomous bulletin source for Castilla y Leon education-aid evidence.",
        "required_fields": [
            "official_url",
            "title",
            "publication_date",
            "issuing_body",
            "jurisdiction",
            "reviewed_at",
        ],
    },
    "BOCM": {
        "source_family": "autonomous_bulletin",
        "priority": 5,
        "why": "Autonomous bulletin source for Madrid education-aid evidence.",
        "required_fields": [
            "official_url",
            "title",
            "publication_date",
            "issuing_body",
            "jurisdiction",
            "reviewed_at",
        ],
    },
    "DOGV": {
        "source_family": "autonomous_bulletin",
        "priority": 6,
        "why": "Autonomous bulletin source for Valencian education-aid evidence.",
        "required_fields": [
            "official_url",
            "title",
            "publication_date",
            "issuing_body",
            "jurisdiction",
            "reviewed_at",
        ],
    },
}

EDUCATION_AID_MISSING_SOURCE_FAMILIES = [
    {
        "source_family": "education_portals",
        "registered": False,
        "required_review": "Map official ministry or autonomous education portal before use.",
        "must_not_infer": ["official_url_verified", "aid_published", "eligibility_decided"],
    }
]

BENEFIT_TOPIC_PROFILES = {
    "benefits": {
        "source_codes": ["BOE", "BDNS", "BOCM", "BOJA", "DOGV", "BOCYL"],
        "missing_source_families": ["official_portals", "sede_electronica"],
    },
    "housing": {
        "source_codes": ["BOE", "BDNS", "BOCM", "BOJA", "DOGV", "BOCYL"],
        "missing_source_families": ["housing_portals", "sede_electronica"],
    },
    "family": {
        "source_codes": ["BOE", "BDNS", "BOCM", "BOJA", "DOGV", "BOCYL"],
        "missing_source_families": ["social_services_portals", "sede_electronica"],
    },
    "dependency": {
        "source_codes": ["BOE", "BOCM", "BOJA", "DOGV", "BOCYL"],
        "missing_source_families": ["dependency_portals", "sede_electronica"],
    },
    "disability": {
        "source_codes": ["BOE", "BOCM", "BOJA", "DOGV", "BOCYL"],
        "missing_source_families": ["disability_portals", "sede_electronica"],
    },
    "social_services": {
        "source_codes": ["BOE", "BDNS", "BOCM", "BOJA", "DOGV", "BOCYL"],
        "missing_source_families": ["social_services_portals", "sede_electronica"],
    },
}

FISCAL_JURISDICTION_SOURCE_PROFILES = {
    "state": ["AEAT", "BOE"],
    "estatal": ["AEAT", "BOE"],
    "madrid": ["AEAT", "BOE", "BOCM"],
    "comunidad de madrid": ["AEAT", "BOE", "BOCM"],
    "valencia": ["AEAT", "BOE", "DOGV"],
    "comunitat valenciana": ["AEAT", "BOE", "DOGV"],
    "comunidad valenciana": ["AEAT", "BOE", "DOGV"],
    "catalunya": ["AEAT", "BOE", "DOGC"],
    "cataluna": ["AEAT", "BOE", "DOGC"],
    "cataluña": ["AEAT", "BOE", "DOGC"],
    "navarra": ["AEAT", "BOE", "BON"],
    "pais vasco": ["AEAT", "BOE", "BOPV"],
    "país vasco": ["AEAT", "BOE", "BOPV"],
    "euskadi": ["AEAT", "BOE", "BOPV"],
}

FISCAL_FALLBACK_SOURCE_CODES = ["AEAT", "BOE"]

AEAT_RENTA_2025_SOURCE = {
    "source_family": "AEAT",
    "registered": False,
    "official_url": "https://sede.agenciatributaria.gob.es/Sede/Ayuda/25Manual/100.html",
    "deductions_url": (
        "https://sede.agenciatributaria.gob.es/Sede/Ayuda/25Manual/100/deducciones-autonomicas.html"
    ),
    "role": "primary_fiscal_guidance",
    "required_review": "Verify exact AEAT manual section and reviewed date before product use.",
}


def build_evidence_packet(
    *,
    consumer: str,
    source_code: str | None = None,
    official_identifier: str | None = None,
    profile: str | None = None,
) -> dict[str, Any]:
    if consumer.strip().lower() != "eduayudas":
        return {
            "status": "unsupported_consumer",
            "consumer": consumer,
            "supported_consumers": ["eduayudas"],
            "message": "Evidence packet planning is currently implemented only for eduayudas.",
        }
    requested_profile = profile.strip() if profile else "education_aid"
    if requested_profile != "education_aid":
        return {
            "status": "unsupported_profile",
            "consumer": "eduayudas",
            "profile": requested_profile,
            "supported_profiles": ["education_aid"],
            "message": "Profile does not match the implemented education-aid evidence contract.",
        }

    selected_sources = _select_education_aid_sources(source_code)
    if isinstance(selected_sources, dict):
        return selected_sources

    packet_candidate = None
    if official_identifier:
        packet_candidate = {
            "official_identifier": official_identifier.strip(),
            "source_code": (
                selected_sources[0]["source_code"] if len(selected_sources) == 1 else None
            ),
            "evidence_status": "not_evidence",
            "candidate_status": "not_candidate",
            "review_status": "manual_review_required",
            "stored_metadata_status": "not_loaded_by_this_planning_tool",
            "message": (
                "Use this as a review target only; no artifact download, evidence-grade "
                "promotion, or product import was performed."
            ),
        }

    return {
        "status": "ok",
        "resource_type": "evidence_packet_profile",
        "consumer": "eduayudas",
        "demand_class": "education_aid_evidence",
        "profile": "education_aid",
        **SHARED_SAFETY,
        "contract_refs": CONTRACT_REFS,
        "staging_only": True,
        "packet_status": "profile_only",
        "packet_candidate": packet_candidate,
        "source_requirements": selected_sources,
        "missing_source_families": EDUCATION_AID_MISSING_SOURCE_FAMILIES,
        "required_packet_fields": [
            "consumer",
            "profile",
            "source_code",
            "source_family",
            "official_identifier",
            "official_url",
            "title",
            "publication_date",
            "issuing_body",
            "jurisdiction",
            "retrieved_at",
            "reviewed_at",
            "evidence_status",
            "candidate_status",
            "review_status",
        ],
        "rules": [
            "reviewable staging only",
            "official sources only",
            "no live fetches",
            "no artifact downloads",
            "no JSONL writes",
            "no product writes",
            "no aid creation",
            "no eligibility decision",
            "no evidence-grade promotion",
        ],
        "must_not_infer": [
            "aid_created",
            "aid_published",
            "eligibility_decided",
            "evidence_grade",
            "product_acceptance_allowed",
        ],
    }


def resolve_normative_reference(
    *,
    consumer: str,
    topic: str,
    jurisdiction: str,
    known_title: str | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    normalized_consumer = consumer.strip().lower()
    if normalized_consumer not in {"la-ayuda", "la_ayuda"}:
        return {
            "status": "unsupported_consumer",
            "consumer": consumer,
            "supported_consumers": ["la-ayuda"],
            "message": "Normative-reference planning is currently implemented only for la-ayuda.",
        }
    if limit < 1 or limit > 20:
        return {
            "status": "invalid_request",
            "message": "limit must be between 1 and 20",
        }
    normalized_topic = topic.strip().lower()
    if normalized_topic not in BENEFIT_TOPIC_PROFILES:
        return {
            "status": "unsupported_topic",
            "topic": topic,
            "supported_topics": sorted(BENEFIT_TOPIC_PROFILES),
            "message": "Topic is not in the benefit source resolver taxonomy.",
        }
    if not jurisdiction.strip():
        return {
            "status": "invalid_request",
            "message": "jurisdiction is required",
        }

    profile = BENEFIT_TOPIC_PROFILES[normalized_topic]
    source_leads = [
        _source_lead(source_code, topic=normalized_topic, jurisdiction=jurisdiction)
        for source_code in profile["source_codes"][:limit]
    ]
    return {
        "status": "manual_review_required",
        "resource_type": "normative_reference_resolution",
        "consumer": "la-ayuda",
        "demand_class": "benefit_source_discovery",
        "topic": normalized_topic,
        "jurisdiction": jurisdiction.strip(),
        "known_title": known_title.strip() if known_title else None,
        **SHARED_SAFETY,
        "contract_refs": CONTRACT_REFS,
        "resolution_status": "source_leads_only",
        "exact_reference_resolved": False,
        "source_leads": source_leads,
        "missing_source_families": [
            {
                "source_family": source_family,
                "registered": False,
                "required_review": (
                    "Map exact official portal or sede source before treating it as a reference."
                ),
                "must_not_infer": ["official_url_verified", "legal_meaning_decided"],
            }
            for source_family in profile["missing_source_families"]
        ],
        "manual_review_reasons": [
            "Exact official reference was not resolved by this planning tool.",
            "Source leads require product-side review before citation or publication.",
            "Official source discovery is not eligibility, amount, deadline, or legal review.",
        ],
        "must_not_infer": [
            "benefit_page_approved",
            "eligibility_decided",
            "amount_or_deadline_verified",
            "publication_ready",
            "legal_meaning_decided",
        ],
        "rules": [
            "source-family planning only",
            "no arbitrary URL fetching",
            "no invented URLs",
            "no markdown generation",
            "no product writes",
            "no eligibility decision",
            "manual review required",
        ],
    }


def resolve_fiscal_reference(
    *,
    consumer: str,
    tax_year: int,
    jurisdiction: str,
    deduction_key: str | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    normalized_consumer = consumer.strip().lower()
    if normalized_consumer not in {"renta", "renta-verificable", "renta_verificable"}:
        return {
            "status": "unsupported_consumer",
            "consumer": consumer,
            "supported_consumers": ["renta-verificable"],
            "message": (
                "Fiscal-reference planning is currently implemented only for renta-verificable."
            ),
        }
    if limit < 1 or limit > 20:
        return {
            "status": "invalid_request",
            "message": "limit must be between 1 and 20",
        }
    if tax_year < 2000 or tax_year > 2100:
        return {
            "status": "invalid_request",
            "message": "tax_year must be between 2000 and 2100",
        }
    normalized_jurisdiction = _normalize_jurisdiction(jurisdiction)
    if not normalized_jurisdiction:
        return {
            "status": "invalid_request",
            "message": "jurisdiction is required",
        }

    source_codes = FISCAL_JURISDICTION_SOURCE_PROFILES.get(
        normalized_jurisdiction,
        FISCAL_FALLBACK_SOURCE_CODES,
    )[:limit]
    source_leads = [
        _fiscal_source_lead(source_code, tax_year=tax_year, jurisdiction=jurisdiction)
        for source_code in source_codes
    ]
    return {
        "status": "manual_review_required",
        "resource_type": "fiscal_reference_resolution",
        "consumer": "renta-verificable",
        "demand_class": "fiscal_reference_resolution",
        "tax_year": tax_year,
        "jurisdiction": jurisdiction.strip(),
        "deduction_key": deduction_key.strip() if deduction_key else None,
        **SHARED_SAFETY,
        "contract_refs": CONTRACT_REFS,
        "resolution_status": "source_leads_only",
        "exact_reference_resolved": False,
        "source_leads": source_leads,
        "manual_review_reasons": [
            "Exact fiscal reference was not resolved by this planning tool.",
            "AEAT guidance, BOE legal references, and autonomous/foral sources require review.",
            "Fiscal source matching is not tax advice or deduction applicability review.",
        ],
        "required_reference_fields": [
            "consumer",
            "tax_year",
            "jurisdiction",
            "deduction_key",
            "source_family",
            "source_code",
            "official_url",
            "official_identifier",
            "version_date",
            "reviewed_at",
            "uncertainty_state",
            "manual_review_required",
        ],
        "must_not_infer": [
            "tax_advice",
            "deduction_applicability_decided",
            "legal_meaning_decided",
            "fiscal_claim_verified",
            "product_publication_allowed",
        ],
        "rules": [
            "AEAT-first planning",
            "exact official reference required before product use",
            "no arbitrary URL fetching",
            "no invented URLs",
            "no tax conclusions",
            "no legal interpretation",
            "no product writes",
            "manual review required",
        ],
    }


def _select_education_aid_sources(source_code: str | None) -> list[dict[str, Any]] | dict[str, Any]:
    if source_code is None:
        codes = list(EDUCATION_AID_SOURCE_PROFILES)
    else:
        normalized = source_code.strip().upper()
        if normalized not in EDUCATION_AID_SOURCE_PROFILES:
            return {
                "status": "unsupported_source",
                "source_code": normalized,
                "supported_sources": list(EDUCATION_AID_SOURCE_PROFILES),
                "message": "Source is not in the education-aid evidence packet profile.",
            }
        codes = [normalized]
    return [_education_source_requirement(code) for code in codes]


def _education_source_requirement(source_code: str) -> dict[str, Any]:
    profile = EDUCATION_AID_SOURCE_PROFILES[source_code]
    try:
        source = get_source(source_code)
    except SourceRegistryError:
        source = None
    return {
        "source_code": source_code,
        "source_family": profile["source_family"],
        "priority": profile["priority"],
        "registered": source is not None,
        "registry_operational_status": source["operational_status"] if source else None,
        "monitor_support": source["monitor_support"] if source else None,
        "evidence_adapter": source["evidence_adapter"] if source else False,
        "candidate_creation_allowed": False,
        "evidence_grade_allowed": False,
        "product_ready": False,
        "why": profile["why"],
        "required_fields": list(profile["required_fields"]),
        "review_status": "manual_review_required",
    }


def _fiscal_source_lead(source_code: str, *, tax_year: int, jurisdiction: str) -> dict[str, Any]:
    if source_code == "AEAT":
        return _aeat_source_lead(tax_year=tax_year, jurisdiction=jurisdiction)
    try:
        source = get_source(source_code)
    except SourceRegistryError:
        return {
            "source_code": source_code,
            "registered": False,
            "source_family": "unknown",
            "tax_year": tax_year,
            "jurisdiction": jurisdiction.strip(),
            "review_status": "manual_review_required",
            "product_ready": False,
        }
    return {
        "source_code": source["source_code"],
        "name": source["name"],
        "registered": True,
        "source_family": _fiscal_source_family(source_code),
        "tax_year": tax_year,
        "jurisdiction": jurisdiction.strip(),
        "official_landing_url": source.get("official_landing_url"),
        "registry_operational_status": source["operational_status"],
        "monitor_support": source["monitor_support"],
        "evidence_adapter": source["evidence_adapter"],
        "candidate_creation_allowed": False,
        "evidence_grade_allowed": False,
        "exact_reference_resolved": False,
        "review_status": "manual_review_required",
        "product_ready": False,
        "safe_downstream_uses": ["fiscal_reference_planning", "manual_review"],
        "must_not_infer": [
            "exact_reference",
            "tax_advice",
            "deduction_applicability_decided",
            "legal_meaning_decided",
            "publication_ready",
        ],
    }


def _aeat_source_lead(*, tax_year: int, jurisdiction: str) -> dict[str, Any]:
    source = AEAT_RENTA_2025_SOURCE if tax_year == 2025 else None
    return {
        "source_code": "AEAT",
        "name": "Agencia Estatal de Administracion Tributaria",
        "registered": False,
        "source_family": "AEAT",
        "tax_year": tax_year,
        "jurisdiction": jurisdiction.strip(),
        "official_url": source["official_url"] if source else None,
        "deductions_url": source["deductions_url"] if source else None,
        "role": "primary_fiscal_guidance",
        "exact_reference_resolved": False,
        "review_status": "manual_review_required",
        "product_ready": False,
        "required_review": (
            source["required_review"]
            if source
            else "Map exact AEAT manual/source URL for the requested tax year before product use."
        ),
        "safe_downstream_uses": ["fiscal_reference_planning", "manual_review"],
        "must_not_infer": [
            "registered_source",
            "exact_reference",
            "tax_advice",
            "deduction_applicability_decided",
            "publication_ready",
        ],
    }


def _fiscal_source_family(source_code: str) -> str:
    if source_code == "BOE":
        return "state_legal_reference"
    if source_code in {"BON", "BOPV"}:
        return "foral_or_autonomous_bulletin"
    return "autonomous_bulletin"


def _normalize_jurisdiction(value: str) -> str:
    return (
        value.strip()
        .lower()
        .replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
    )


def _source_lead(source_code: str, *, topic: str, jurisdiction: str) -> dict[str, Any]:
    try:
        source = get_source(source_code)
    except SourceRegistryError:
        return {
            "source_code": source_code,
            "registered": False,
            "topic": topic,
            "jurisdiction": jurisdiction.strip(),
            "review_status": "manual_review_required",
            "product_ready": False,
        }
    return {
        "source_code": source["source_code"],
        "name": source["name"],
        "registered": True,
        "topic": topic,
        "jurisdiction": jurisdiction.strip(),
        "official_landing_url": source.get("official_landing_url"),
        "registry_operational_status": source["operational_status"],
        "monitor_support": source["monitor_support"],
        "evidence_adapter": source["evidence_adapter"],
        "candidate_creation_allowed": False,
        "evidence_grade_allowed": False,
        "exact_reference_resolved": False,
        "review_status": "manual_review_required",
        "product_ready": False,
        "safe_downstream_uses": ["source_discovery", "manual_review"],
        "must_not_infer": [
            "exact_reference",
            "evidence_grade",
            "publication_ready",
            "legal_meaning_decided",
        ],
    }
