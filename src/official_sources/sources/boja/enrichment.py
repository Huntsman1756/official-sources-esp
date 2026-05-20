from __future__ import annotations

import json
from collections import Counter
from collections.abc import Callable
from typing import Any

import httpx

from official_sources.sources.boe.http_policy import BOERequestAudit
from official_sources.sources.boja.client import BOJAClient
from official_sources.sources.boja.parser import parse_boja_search_response
from official_sources.storage.repository import OfficialSourcesRepository


def enrich_boja_evidence_urls(
    repository: OfficialSourcesRepository,
    *,
    candidate_ids: list[int] | None = None,
    document_ids: list[int] | None = None,
    fetcher: Callable[[str], bytes] | None = None,
) -> dict[str, Any]:
    candidate_ids = candidate_ids or []
    document_ids = document_ids or []
    documents = _selected_boja_documents(repository, candidate_ids, document_ids)
    client: BOJAClient | None = None
    counts: dict[str, Any] = {
        "selected_documents": len(documents),
        "enriched": 0,
        "skipped": 0,
        "failed": 0,
        "missing_evidence_url": 0,
        "retries": 0,
        "throttle_events": 0,
    }
    http_status_counts: Counter[str] = Counter()
    for document in documents:
        official_id = _boja_official_id(document)
        try:
            if fetcher is not None:
                payload = fetcher(official_id)
                audit = BOERequestAudit(last_http_status=200)
            else:
                client = client or BOJAClient()
                payload = client.fetch_document_detail(official_id)
                audit = client.last_request_audit
            parsed = parse_boja_search_response(payload, target_date=document["publication_date"])
            detail = _matching_detail_document(parsed.documents, document["external_id"])
            if detail is None or not detail.url_pdf:
                counts["skipped"] += 1
                counts["missing_evidence_url"] += 1
                counts["retries"] += audit.retry_count
                counts["throttle_events"] += audit.throttle_triggered
                http_status_counts[_status_value(audit.last_http_status)] += 1
                continue
            raw_metadata = _merged_raw_metadata(document, detail.raw_metadata)
            repository.upsert_document(
                source_id=document["source_id"],
                external_id=document["external_id"],
                publication_date=document["publication_date"],
                title=document["title"],
                department=document["department"],
                section=document["section"],
                document_type=document["document_type"],
                url_html=document["url_html"] or detail.url_html,
                url_xml=document["url_xml"],
                url_pdf=detail.url_pdf or document["url_pdf"],
                raw_metadata=raw_metadata,
            )
            counts["enriched"] += 1
            counts["retries"] += audit.retry_count
            counts["throttle_events"] += audit.throttle_triggered
            http_status_counts[_status_value(audit.last_http_status)] += 1
        except Exception as exc:
            counts["failed"] += 1
            status_code = _status_from_exception(exc)
            http_status_counts[_status_value(status_code)] += 1
    counts["http_status_summary"] = _format_counter(http_status_counts)
    return counts


def _selected_boja_documents(
    repository: OfficialSourcesRepository,
    candidate_ids: list[int],
    document_ids: list[int],
) -> list[dict[str, Any]]:
    if bool(candidate_ids) == bool(document_ids):
        raise ValueError("Provide exactly one of candidate_ids or document_ids")
    documents = (
        repository.list_documents_by_candidate_ids(candidate_ids)
        if candidate_ids
        else repository.list_documents_by_ids(document_ids)
    )
    expected_count = len(candidate_ids or document_ids)
    if len(documents) != expected_count:
        raise ValueError("One or more selected BOJA records were not found")
    mismatched = sorted(
        {document["source_code"] for document in documents if document["source_code"] != "BOJA"}
    )
    if mismatched:
        raise ValueError(
            f"Selected documents must belong to source BOJA; found {','.join(mismatched)}"
        )
    return documents


def _boja_official_id(document: dict[str, Any]) -> str:
    raw_metadata = json.loads(document["raw_metadata_json"] or "{}")
    official_id = raw_metadata.get("boja_official_id") or raw_metadata.get("id")
    if isinstance(official_id, str) and official_id.strip():
        return official_id.strip()
    external_id = document["external_id"]
    if isinstance(external_id, str) and external_id.startswith("BOJA:"):
        return external_id.removeprefix("BOJA:")
    raise ValueError(f"BOJA document {document['id']} lacks a stable official identifier")


def _matching_detail_document(details: list[Any], external_id: str) -> Any | None:
    for detail in details:
        if detail.external_id == external_id:
            return detail
    return details[0] if len(details) == 1 else None


def _merged_raw_metadata(
    document: dict[str, Any],
    detail_metadata: dict[str, Any],
) -> dict[str, Any]:
    current = json.loads(document["raw_metadata_json"] or "{}")
    merged = {**current, **detail_metadata}
    for noisy_key in ("body", "bodyNoHtml"):
        merged.pop(noisy_key, None)
    return merged


def _status_from_exception(exc: Exception) -> int | None:
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code
    return getattr(exc, "last_http_status", None)


def _status_value(value: int | None) -> str:
    return str(value) if value is not None else "none"


def _format_counter(counter: Counter[str]) -> str:
    if not counter:
        return "none"
    return ",".join(f"{key}:{counter[key]}" for key in sorted(counter))
