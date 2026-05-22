from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from typing import Any

from official_sources.integrity.hashing import sha256_bytes
from official_sources.sources.dogv.client import (
    build_dogv_document_html_url,
    build_dogv_document_metadata_url,
    build_dogv_document_pdf_url,
    build_dogv_document_xml_url,
    validate_dogv_date,
)

NO_PUBLICATION_STATUS = "no_publication"


@dataclass(frozen=True)
class DOGVDocumentMetadata:
    external_id: str
    official_identifier: str
    publication_date: str
    title: str
    department: str | None
    section: str | None
    document_type: str | None
    url_html: str
    url_xml: str
    url_pdf: str | None
    raw_metadata: dict[str, Any]


@dataclass(frozen=True)
class DOGVIssue:
    target_date: str
    raw_payload_sha256: str
    status: str
    issue_identifier: str | None
    documents: list[DOGVDocumentMetadata]


def parse_dogv_date_response(payload: bytes, *, target_date: str) -> DOGVIssue:
    validate_dogv_date(target_date)
    raw_payload_sha256 = sha256_bytes(payload)
    data = json.loads(payload.decode("utf-8-sig"))
    header = data.get("cabecera")
    provisions = data.get("disposiciones")
    if not header or not provisions:
        return DOGVIssue(
            target_date=target_date,
            raw_payload_sha256=raw_payload_sha256,
            status=NO_PUBLICATION_STATUS,
            issue_identifier=None,
            documents=[],
        )
    issue_identifier = str(header.get("numeroDogv") or "").strip()
    if not issue_identifier:
        raise ValueError(f"DOGV response for {target_date} has no issue number")
    documents = [_metadata_from_date_item(item, issue_identifier) for item in provisions]
    return DOGVIssue(
        target_date=target_date,
        raw_payload_sha256=raw_payload_sha256,
        status="success",
        issue_identifier=issue_identifier,
        documents=documents,
    )


def parse_dogv_document_metadata(
    payload: bytes,
    *,
    fallback_document_id: int | str,
) -> DOGVDocumentMetadata:
    raw_hash = sha256_bytes(payload)
    data = json.loads(payload.decode("utf-8-sig"))
    document_number = _required_text(data.get("documentNumber"), "DOGV document metadata")
    official_identifier = _official_identifier(document_number, data.get("identifier"))
    publication_date = _normalize_datetime_date(
        _required_text(data.get("date_publication"), "DOGV document metadata")
    )
    title = _first_text(data.get("title_spa"), data.get("title_vci"), data.get("title"))
    return DOGVDocumentMetadata(
        external_id=f"DOGV:{official_identifier}",
        official_identifier=official_identifier,
        publication_date=publication_date,
        title=title or official_identifier,
        department=_clean_optional_text(data.get("author")),
        section=_clean_optional_text(data.get("section")),
        document_type=_clean_optional_text(data.get("range")),
        url_html=build_dogv_document_html_url(document_number),
        url_xml=build_dogv_document_xml_url(fallback_document_id),
        url_pdf=None,
        raw_metadata={
            "dogv_document_id": fallback_document_id,
            "codigo_insercion": document_number,
            "journal_number": _clean_optional_text(data.get("journal_number")),
            "url_metadata": build_dogv_document_metadata_url(fallback_document_id),
            "metadata_sha256": raw_hash,
            "source_metadata": data,
        },
    )


def _metadata_from_date_item(item: dict[str, Any], issue_identifier: str) -> DOGVDocumentMetadata:
    document_id = _required_text(item.get("id"), "DOGV date document")
    codigo_insercion = _required_text(item.get("codigoInsercion"), "DOGV date document")
    official_identifier = _official_identifier(codigo_insercion, None)
    publication_date = _normalize_publication_date(
        _required_text(item.get("fechaPublicacion"), "DOGV date document")
    )
    section = _description(item.get("seccion"))
    subsection = _description(item.get("subseccion"))
    raw_metadata = {
        "dogv_document_id": document_id,
        "codigo_insercion": codigo_insercion,
        "issue_identifier": issue_identifier,
        "url_metadata": build_dogv_document_metadata_url(document_id),
        "url_xml_dynamic": build_dogv_document_xml_url(document_id),
        "raw_document": item,
    }
    return DOGVDocumentMetadata(
        external_id=f"DOGV:{official_identifier}",
        official_identifier=official_identifier,
        publication_date=publication_date,
        title=_required_text(item.get("titulo"), "DOGV date document"),
        department=_clean_optional_text(item.get("organismo")),
        section=" / ".join(part for part in [section, subsection] if part) or None,
        document_type=None,
        url_html=build_dogv_document_html_url(codigo_insercion),
        url_xml=build_dogv_document_xml_url(document_id),
        url_pdf=build_dogv_document_pdf_url(str(item["urlPdf"])) if item.get("urlPdf") else None,
        raw_metadata=raw_metadata,
    )


def _official_identifier(document_number: str, explicit_identifier: object | None) -> str:
    explicit = _clean_optional_text(explicit_identifier)
    if explicit:
        return explicit
    normalized = document_number.replace("/", "-")
    return f"DOGV-C-{normalized}"


def _normalize_publication_date(value: str) -> str:
    parts = value.split("/")
    if len(parts) == 3:
        return date(int(parts[2]), int(parts[1]), int(parts[0])).isoformat()
    return validate_dogv_date(value).isoformat()


def _normalize_datetime_date(value: str) -> str:
    return validate_dogv_date(value.split()[0]).isoformat()


def _description(value: object | None) -> str | None:
    if not isinstance(value, dict):
        return None
    return _clean_optional_text(value.get("descripcion"))


def _first_text(*values: object | None) -> str | None:
    for value in values:
        cleaned = _clean_optional_text(value)
        if cleaned:
            return cleaned
    return None


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
