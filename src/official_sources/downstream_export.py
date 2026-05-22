from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from official_sources.storage.repository import OfficialSourcesRepository


def build_downstream_evidence_export(
    repository: OfficialSourcesRepository,
    source_candidate_id: int,
) -> dict[str, Any]:
    row = _candidate_export_row(repository, source_candidate_id)
    files = repository.list_document_files(row["document_id"])
    pdf_file = _first_file(files, "pdf")
    xml_file = _first_file(files, "xml")
    html_file = _first_file(files, "html")
    primary_file = pdf_file or xml_file or html_file
    integrity_warning = bool(row["integrity_warning"]) or any(
        file_record["content_changed_at"] for file_record in files
    )
    content_sha256 = primary_file["sha256"] if primary_file else row["source_snapshot_hash"]
    source_snapshot_hash = (
        primary_file["source_snapshot_hash"] if primary_file else row["source_snapshot_hash"]
    )
    last_integrity_check_at = primary_file["last_integrity_check_at"] if primary_file else None
    content_changed_at = primary_file["content_changed_at"] if primary_file else None

    official_identifier = str(row["external_id"])
    citation = {
        "source_code": row["source_code"],
        "source_name": row["source_name"],
        "resource_type": "official_document",
        "official_identifier": official_identifier,
        "title": row["title"],
        "official_url": row["official_url"],
        "publication_date": row["publication_date"],
        "version_date": None,
    }
    return {
        "schema_version": 1,
        "exported_at": datetime.now(UTC).isoformat(),
        "source_code": row["source_code"],
        "resource_type": "official_document",
        "official_identifier": official_identifier,
        "title": row["title"],
        "publication_date": row["publication_date"],
        "version_date": None,
        "official_url": row["official_url"],
        "citation": citation,
        "integrity": {
            "source_snapshot_hash": source_snapshot_hash,
            "content_sha256": content_sha256,
            "hashes_match": source_snapshot_hash == content_sha256,
            "last_integrity_check_at": last_integrity_check_at,
            "content_changed_at": content_changed_at,
            "has_integrity_warning": integrity_warning,
            "integrity_warning_reason": "content_changed" if integrity_warning else None,
            "signature_status": primary_file["signature_status"] if primary_file else "not_checked",
        },
        "artifacts": {
            "xml_available": xml_file is not None,
            "html_available": html_file is not None,
            "pdf_available": pdf_file is not None,
            **({"xml": _public_artifact(xml_file)} if xml_file else {}),
            **({"html": _public_artifact(html_file)} if html_file else {}),
            **({"pdf": _public_artifact(pdf_file)} if pdf_file else {}),
        },
        "official_sources_candidate": {
            "candidate_id": row["candidate_id"],
            "candidate_type": row["candidate_type"],
            "document_id": row["document_id"],
            "downstream_project_fit": row["downstream_project_fit"],
            "evidence_label": row["evidence_label"],
            "evidence_level": row["evidence_level"],
            "evidence_review_status": row["evidence_review_status"],
            "extraction_status": row["extraction_status"],
            "manual_decision": row["manual_decision"],
            "matched_keywords": _matched_keywords(row["matched_fields_json"]),
            "project_key": row["project_key"],
            "review_status": row["review_status"],
            "reviewed_at": row["reviewed_at"],
            "reviewed_by": row["reviewed_by"],
            "score": _matched_score(row["matched_fields_json"]),
            "score_reasons": _matched_score_reasons(row["matched_fields_json"]),
            "selected_for_pdf": bool(row["selected_for_pdf"]),
        },
        f"{str(row['source_code']).lower()}_metadata": _decode_json(row["raw_metadata_json"]),
        "safety": {
            "raw_text_included": False,
            "xml_payload_included": False,
            "html_payload_included": False,
            "contains_local_artifact_paths": False,
        },
    }


def export_downstream_evidence_files(
    repository: OfficialSourcesRepository,
    candidate_ids: list[int],
    output_dir: Path,
) -> list[Path]:
    written: list[Path] = []
    for candidate_id in candidate_ids:
        payload = build_downstream_evidence_export(repository, candidate_id)
        fit = payload["official_sources_candidate"]["downstream_project_fit"] or "unrouted"
        target_dir = output_dir / _group_name(str(fit))
        target_dir.mkdir(parents=True, exist_ok=True)
        filename = _export_filename(
            candidate_id,
            str(payload["source_code"]),
            str(payload["official_identifier"]),
        )
        path = target_dir / filename
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
        written.append(path)
    return written


def _candidate_export_row(
    repository: OfficialSourcesRepository,
    source_candidate_id: int,
) -> dict[str, Any]:
    row = repository.connection.execute(
        """
        SELECT
            c.id AS candidate_id,
            c.document_id AS document_id,
            c.project_key AS project_key,
            c.candidate_type AS candidate_type,
            c.extraction_status AS extraction_status,
            c.evidence_level AS evidence_level,
            c.matched_fields_json AS matched_fields_json,
            c.review_status AS review_status,
            d.external_id AS external_id,
            d.publication_date AS publication_date,
            d.title AS title,
            d.department AS department,
            d.section AS section,
            d.url_html AS url_html,
            d.url_xml AS url_xml,
            d.url_pdf AS url_pdf,
            d.raw_metadata_json AS raw_metadata_json,
            s.code AS source_code,
            s.name AS source_name,
            COALESCE(d.url_html, d.url_xml, d.url_pdf) AS official_url,
            r.evidence_review_status AS evidence_review_status,
            r.evidence_label AS evidence_label,
            r.manual_decision AS manual_decision,
            r.downstream_project_fit AS downstream_project_fit,
            r.reviewed_by AS reviewed_by,
            r.reviewed_at AS reviewed_at,
            COALESCE(r.selected_for_pdf, 0) AS selected_for_pdf,
            COALESCE(r.integrity_warning, 0) AS integrity_warning
        FROM source_candidates c
        JOIN official_documents d ON d.id = c.document_id
        JOIN official_sources s ON s.id = d.source_id
        LEFT JOIN candidate_evidence_reviews r ON r.source_candidate_id = c.id
        WHERE c.id = ?
        """,
        (source_candidate_id,),
    ).fetchone()
    if row is None:
        raise KeyError(f"Unknown source candidate: {source_candidate_id}")
    return dict(row)


def _first_file(files: list[dict[str, Any]], file_type: str) -> dict[str, Any] | None:
    return next(
        (file_record for file_record in files if file_record["file_type"] == file_type),
        None,
    )


def _public_artifact(file_record: dict[str, Any]) -> dict[str, Any]:
    return {
        "official_url": file_record["official_url"],
        "media_type": file_record["media_type"],
        "size_bytes": file_record["size_bytes"],
        "sha256": file_record["sha256"],
    }


def _decode_json(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    parsed = json.loads(value)
    return parsed if isinstance(parsed, dict) else {}


def _matched_keywords(value: str) -> list[str]:
    parsed = _decode_json(value)
    keywords = parsed.get("keywords", [])
    return keywords if isinstance(keywords, list) else []


def _matched_score(value: str) -> int | None:
    parsed = _decode_json(value)
    score = parsed.get("score")
    return score if isinstance(score, int) else None


def _matched_score_reasons(value: str) -> list[str]:
    parsed = _decode_json(value)
    reasons = parsed.get("score_reasons", [])
    return reasons if isinstance(reasons, list) else []


def _group_name(fit: str) -> str:
    if fit == "EduAyudas":
        return "eduayudas"
    return fit


def _export_filename(candidate_id: int, source_code: str, official_identifier: str) -> str:
    safe_identifier = official_identifier.replace(":", "_").replace("/", "_")
    return f"{candidate_id}_{source_code}_{safe_identifier}.json"
