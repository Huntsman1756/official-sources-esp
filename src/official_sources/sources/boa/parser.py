from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from official_sources.integrity.hashing import sha256_bytes
from official_sources.sources.boa.client import validate_boa_date

NO_PUBLICATION_STATUS = "no_publication"
BOA_OFFICIAL_URL_RE = re.compile(r"https://www\.boa\.aragon\.es/cgi-bin/EBOA/BRSCGI\?[^`´\s]+")


@dataclass(frozen=True)
class BOADocumentMetadata:
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
class BOAIssue:
    target_date: str
    raw_payload_sha256: str
    status: str
    issue_identifier: str | None
    documents: list[BOADocumentMetadata]


def parse_boa_date_response(payload: bytes, *, target_date: str) -> BOAIssue:
    validate_boa_date(target_date)
    raw_payload_sha256 = sha256_bytes(payload)
    text = _decode_boa_payload(payload)
    if _is_no_publication_payload(text):
        return BOAIssue(
            target_date=target_date,
            raw_payload_sha256=raw_payload_sha256,
            status=NO_PUBLICATION_STATUS,
            issue_identifier=None,
            documents=[],
        )
    records = json.loads(text)
    if not records:
        return BOAIssue(
            target_date=target_date,
            raw_payload_sha256=raw_payload_sha256,
            status=NO_PUBLICATION_STATUS,
            issue_identifier=None,
            documents=[],
        )
    documents = [_metadata_from_api_record(record) for record in records]
    issue_identifiers = {
        _issue_identifier(record)
        for record in records
        if _clean_optional_text(record.get("Numeroboletin"))
    }
    if len(issue_identifiers) != 1:
        raise ValueError(f"BOA response for {target_date} has mixed issue identifiers")
    return BOAIssue(
        target_date=target_date,
        raw_payload_sha256=raw_payload_sha256,
        status="success",
        issue_identifier=issue_identifiers.pop(),
        documents=documents,
    )


def parse_boa_document_metadata(payload: bytes) -> BOADocumentMetadata:
    raw_hash = sha256_bytes(payload)
    data = json.loads(_decode_boa_payload(payload))
    metadata = _metadata_from_api_record(data)
    return BOADocumentMetadata(
        **{
            **metadata.__dict__,
            "raw_metadata": {
                **metadata.raw_metadata,
                "metadata_sha256": raw_hash,
            },
        }
    )


def _metadata_from_api_record(record: dict[str, Any]) -> BOADocumentMetadata:
    document_identifier = _required_text(record.get("DOCN"), "BOA record")
    publication_date = _parse_boa_compact_date(
        _required_text(record.get("FechaPublicacion"), "BOA record")
    )
    issue_identifier = _issue_identifier(record)
    document_pdf_url = _first_official_url(record.get("UrlPdf"))
    issue_pdf_url = _first_official_url(record.get("UrlBCOM"))
    return BOADocumentMetadata(
        external_id=f"BOA:{document_identifier}",
        official_identifier=document_identifier,
        publication_date=publication_date,
        title=_required_text(record.get("Titulo"), "BOA record"),
        department=_clean_optional_text(record.get("Emisor")),
        section=_clean_optional_text(record.get("Seccion")),
        document_type=_clean_optional_text(record.get("Rango")),
        url_html=None,
        url_xml=None,
        url_pdf=document_pdf_url,
        raw_metadata={
            "issue_identifier": issue_identifier,
            "document_identifier": document_identifier,
            "issue_pdf_url": issue_pdf_url,
            "norden": _clean_optional_text(record.get("NOrden")),
            "subsection": _clean_optional_text(record.get("Subseccion")),
            "disposition_date": _parse_optional_boa_compact_date(record.get("Fechadisposicion")),
            "subject_code": _clean_optional_text(record.get("CodigoMateria")),
            "raw_document": record,
        },
    )


def _decode_boa_payload(payload: bytes) -> str:
    try:
        return payload.decode("utf-8-sig")
    except UnicodeDecodeError:
        return payload.decode("iso-8859-1")


def _is_no_publication_payload(text: str) -> bool:
    stripped = text.lstrip()
    return stripped.startswith("<!DOCTYPE html>") and "No se han recuperado documentos" in text


def _issue_identifier(record: dict[str, Any]) -> str:
    issue_number = _required_text(record.get("Numeroboletin"), "BOA record")
    publication_date = _parse_boa_compact_date(
        _required_text(record.get("FechaPublicacion"), "BOA record")
    )
    return f"{issue_number}/{publication_date[:4]}"


def _parse_boa_compact_date(value: str) -> str:
    if not re.fullmatch(r"\d{8}", value):
        raise ValueError(f"Invalid BOA compact date: {value}")
    return validate_boa_date(f"{value[:4]}-{value[4:6]}-{value[6:8]}").isoformat()


def _parse_optional_boa_compact_date(value: object | None) -> str | None:
    text = _clean_optional_text(value)
    return _parse_boa_compact_date(text) if text else None


def _first_official_url(value: object | None) -> str | None:
    text = _clean_optional_text(value)
    if not text:
        return None
    match = BOA_OFFICIAL_URL_RE.search(text)
    return match.group(0) if match else None


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
