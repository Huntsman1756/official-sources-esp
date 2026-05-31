from __future__ import annotations

import json
import re
from typing import Any

BUSINESS_GRANTS_PROFILE = "business_grants"

_BENEFICIARY_TERMS = {
    "pyme": "beneficiary:pyme",
    "pymes": "beneficiary:pyme",
    "empresa": "beneficiary:empresa",
    "empresas": "beneficiary:empresa",
    "actividad economica": "beneficiary:actividad_economica",
    "autonomo": "beneficiary:autonomo",
    "autonomos": "beneficiary:autonomo",
    "emprendedor": "beneficiary:emprendedor",
    "emprendedores": "beneficiary:emprendedor",
}

_TOPIC_TERMS = {
    "turismo": "topic:turismo",
    "comercio": "topic:comercio",
    "digitalizacion": "topic:digitalizacion",
    "innovacion": "topic:innovacion",
    "i+d": "topic:innovacion",
    "investigacion": "topic:innovacion",
    "energia": "topic:energia",
    "eficiencia energetica": "topic:energia",
    "internacionalizacion": "topic:internacionalizacion",
    "exportacion": "topic:internacionalizacion",
    "empleo": "topic:empleo",
    "contratacion": "topic:empleo",
    "formacion": "topic:formacion",
    "industria": "topic:industria",
}

_INSTRUMENT_TERMS = {
    "subvencion": "instrument:subvencion",
    "entrega dineraria": "instrument:subvencion",
    "prestamo": "instrument:prestamo",
    "credito": "instrument:credito",
    "incentivo": "instrument:incentivo",
}

_EXCLUSION_TERMS = {
    "sancion": "exclusion:sancion",
    "recurso": "exclusion:recurso",
    "expropiacion": "exclusion:expropiacion",
}


def build_bdns_business_grant_record(document: dict[str, Any]) -> dict[str, Any]:
    raw_metadata = json.loads(document["raw_metadata_json"] or "{}")
    score, reasons = score_bdns_business_grant(document, raw_metadata)
    return {
        "profile": BUSINESS_GRANTS_PROFILE,
        "source_code": "BDNS",
        "external_id": document["external_id"],
        "official_identifier": document["external_id"],
        "publication_date": document["publication_date"],
        "title": document["title"],
        "department": document["department"],
        "section": document["section"],
        "document_type": document["document_type"],
        "official_url": document["url_html"],
        "bdns_code": raw_metadata.get("bdns_code"),
        "bdns_internal_id": raw_metadata.get("bdns_internal_id"),
        "application_start_date": raw_metadata.get("application_start_date"),
        "application_end_date": raw_metadata.get("application_end_date"),
        "budget": raw_metadata.get("budget"),
        "beneficiary_type": raw_metadata.get("beneficiary_type") or [],
        "instrument_type": raw_metadata.get("instrument_type") or [],
        "sector_activity": raw_metadata.get("sector_activity") or [],
        "territorial_scope": raw_metadata.get("territorial_scope") or [],
        "catalog_enrichment": raw_metadata.get("catalog_enrichment") or {},
        "document_metadata": raw_metadata.get("document_metadata") or [],
        "announcement_metadata": raw_metadata.get("announcement_metadata") or [],
        "business_relevance_score": score,
        "business_relevance_reasons": reasons,
        "review_status": "manual_review_required",
        "candidate_creation_allowed": False,
        "evidence_grade_allowed": False,
        "product_automation_allowed": False,
        "export_schema": "bdns_business_grant_v1",
    }


def filter_bdns_business_grants(
    documents: list[dict[str, Any]],
    *,
    min_score: float,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    records = [
        record
        for record in (build_bdns_business_grant_record(document) for document in documents)
        if record["business_relevance_score"] >= min_score
    ]
    records.sort(
        key=lambda record: (
            record["business_relevance_score"],
            record["publication_date"] or "",
            record["official_identifier"],
        ),
        reverse=True,
    )
    return records[:limit] if limit is not None else records


def score_bdns_business_grant(
    document: dict[str, Any],
    raw_metadata: dict[str, Any],
) -> tuple[float, list[str]]:
    haystack = _normalized_text(
        " ".join(
            [
                str(document["title"] or ""),
                str(document["department"] or ""),
                str(raw_metadata.get("beneficiary_type") or ""),
                str(raw_metadata.get("instrument_type") or ""),
                str(raw_metadata.get("sector_activity") or ""),
                str(raw_metadata.get("territorial_scope") or ""),
                str(raw_metadata.get("source_metadata") or ""),
            ]
        )
    )
    reasons: list[str] = []
    score = 0.0
    score += _score_terms(haystack, _BENEFICIARY_TERMS, 0.45, reasons)
    score += _score_terms(haystack, _TOPIC_TERMS, 0.18, reasons)
    score += _score_terms(haystack, _INSTRUMENT_TERMS, 0.2, reasons)
    if raw_metadata.get("budget"):
        score += 0.1
        reasons.append("budget:present")
    if raw_metadata.get("application_end_date"):
        score += 0.1
        reasons.append("deadline:present")
    score -= _score_terms(haystack, _EXCLUSION_TERMS, 0.35, reasons)
    return round(max(0.0, min(1.0, score)), 2), sorted(set(reasons))


def _score_terms(
    haystack: str,
    terms: dict[str, str],
    weight: float,
    reasons: list[str],
) -> float:
    score = 0.0
    seen_reasons: set[str] = set()
    for term, reason in terms.items():
        if term in haystack and reason not in seen_reasons:
            score += weight
            seen_reasons.add(reason)
            reasons.append(reason)
    return score


def _normalized_text(value: str) -> str:
    normalized = (
        value.lower()
        .replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
        .replace("ü", "u")
        .replace("ñ", "n")
    )
    return re.sub(r"\s+", " ", normalized)
