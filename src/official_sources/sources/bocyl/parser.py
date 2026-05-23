from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from official_sources.integrity.hashing import sha256_bytes
from official_sources.sources.bocyl.client import validate_bocyl_date

NO_PUBLICATION_STATUS = "no_publication"
BOCYL_DOCUMENT_ID_RE = re.compile(r"BOCYL-D-\d{8}-\d+(?:-\d+)?")


@dataclass(frozen=True)
class BOCYLDocumentMetadata:
    external_id: str
    official_identifier: str
    publication_date: str
    title: str
    department: str | None
    section: str | None
    document_type: str | None
    url_html: str | None
    url_xml: str | None
    url_pdf: str | None
    raw_metadata: dict[str, Any]


@dataclass(frozen=True)
class BOCYLIssue:
    target_date: str
    raw_payload_sha256: str
    status: str
    issue_identifier: str | None
    documents: list[BOCYLDocumentMetadata]


def parse_bocyl_date_response(payload: bytes, *, target_date: str) -> BOCYLIssue:
    validate_bocyl_date(target_date)
    raw_payload_sha256 = sha256_bytes(payload)
    data = json.loads(payload.decode("utf-8-sig"))
    records = data.get("results") or []
    if not records:
        return BOCYLIssue(
            target_date=target_date,
            raw_payload_sha256=raw_payload_sha256,
            status=NO_PUBLICATION_STATUS,
            issue_identifier=None,
            documents=[],
        )
    documents = [_metadata_from_api_record(record) for record in records]
    issue_identifiers = {
        _required_text(record.get("no_edicion"), "BOCYL record") for record in records
    }
    if len(issue_identifiers) != 1:
        raise ValueError(f"BOCYL response for {target_date} has mixed issue identifiers")
    return BOCYLIssue(
        target_date=target_date,
        raw_payload_sha256=raw_payload_sha256,
        status="success",
        issue_identifier=issue_identifiers.pop(),
        documents=documents,
    )


def parse_bocyl_document_metadata(payload: bytes) -> BOCYLDocumentMetadata:
    raw_hash = sha256_bytes(payload)
    data = json.loads(payload.decode("utf-8-sig"))
    metadata = _metadata_from_api_record(data)
    return BOCYLDocumentMetadata(
        **{
            **metadata.__dict__,
            "raw_metadata": {
                **metadata.raw_metadata,
                "metadata_sha256": raw_hash,
            },
        }
    )


def _metadata_from_api_record(record: dict[str, Any]) -> BOCYLDocumentMetadata:
    publication_date = validate_bocyl_date(
        _required_text(record.get("fecha_publicacion"), "BOCYL record")
    ).isoformat()
    issue_identifier = _required_text(record.get("no_edicion"), "BOCYL record")
    url_pdf = _clean_optional_text(record.get("enlace_fichero_pdf"))
    url_xml = _clean_optional_text(record.get("enlace_fichero_xml"))
    url_html = _clean_optional_text(record.get("enlace_fichero_html"))
    document_identifier = _extract_document_identifier(url_pdf, url_xml, url_html)
    return BOCYLDocumentMetadata(
        external_id=f"BOCYL:{document_identifier}",
        official_identifier=document_identifier,
        publication_date=publication_date,
        title=_required_text(record.get("titulo"), "BOCYL record"),
        department=_clean_optional_text(record.get("organismo")),
        section=_clean_optional_text(record.get("seccion")),
        document_type=_clean_optional_text(record.get("rango")),
        url_html=url_html,
        url_xml=url_xml,
        url_pdf=url_pdf,
        raw_metadata={
            "issue_identifier": issue_identifier,
            "document_identifier": document_identifier,
            "page_start": record.get("pagina_inicial"),
            "page_end": record.get("pagina_final"),
            "subsection": _clean_optional_text(record.get("subseccion")),
            "apartado": _clean_optional_text(record.get("apartado")),
            "suborganismo": _clean_optional_text(record.get("suborganismo")),
            "raw_document": record,
        },
    )


def _extract_document_identifier(*urls: str | None) -> str:
    for url in urls:
        if not url:
            continue
        match = BOCYL_DOCUMENT_ID_RE.search(url)
        if match:
            return match.group(0)
    raise ValueError("BOCYL record is missing a BOCYL-D document identifier in artifact URLs")


def _required_text(value: object | None, context: str) -> str:
    cleaned = _clean_optional_text(value)
    if not cleaned:
        raise ValueError(f"{context} is missing a required value")
    return cleaned


def _clean_optional_text(value: object | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
