from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date
from typing import Any
from urllib.parse import parse_qs, urlparse

from official_sources.integrity.hashing import sha256_bytes
from official_sources.sources.dogc.client import build_dogc_document_html_url, validate_dogc_date

NO_PUBLICATION_STATUS = "no_publication"


@dataclass(frozen=True)
class DOGCDocumentMetadata:
    external_id: str
    official_identifier: str
    publication_date: str
    title: str
    department: str | None
    section: str | None
    document_type: str | None
    url_html: str
    url_xml: str | None
    url_pdf: str | None
    raw_metadata: dict[str, Any]


@dataclass(frozen=True)
class DOGCIssue:
    target_date: str
    raw_payload_sha256: str
    status: str
    issue_identifier: str | None
    documents: list[DOGCDocumentMetadata]


def parse_dogc_date_response(payload: bytes, *, target_date: str) -> DOGCIssue:
    validate_dogc_date(target_date)
    raw_payload_sha256 = sha256_bytes(payload)
    data = json.loads(payload.decode("utf-8-sig"))
    records = data.get("resultSearch") or []
    if not records:
        return DOGCIssue(
            target_date=target_date,
            raw_payload_sha256=raw_payload_sha256,
            status=NO_PUBLICATION_STATUS,
            issue_identifier=None,
            documents=[],
        )
    documents = [
        _metadata_from_search_record(record, target_date=target_date) for record in records
    ]
    explicit_issue_identifier = _clean_optional_text(data.get("issue_identifier"))
    issue_identifiers = (
        {explicit_issue_identifier}
        if explicit_issue_identifier
        else {
            issue
            for document in documents
            if (issue := _clean_optional_text(document.raw_metadata.get("issue_identifier")))
        }
    )
    if len(issue_identifiers) != 1:
        raise ValueError(f"DOGC response for {target_date} has mixed or missing issue identifiers")
    return DOGCIssue(
        target_date=target_date,
        raw_payload_sha256=raw_payload_sha256,
        status="success",
        issue_identifier=issue_identifiers.pop(),
        documents=documents,
    )


def parse_dogc_document_metadata(
    payload: bytes,
    *,
    fallback_document_id: int | str,
) -> DOGCDocumentMetadata:
    raw_hash = sha256_bytes(payload)
    data = json.loads(payload.decode("utf-8-sig"))
    document_data = data.get("documentData") or {}
    cve = _required_text(document_data.get("CVE"), "DOGC document metadata")
    publication_date = _normalize_dogc_date(
        _required_text(document_data.get("dateDOGC"), "DOGC document metadata")
    )
    link_download = data.get("linkDownload") or {}
    return DOGCDocumentMetadata(
        external_id=f"DOGC:{cve}",
        official_identifier=cve,
        publication_date=publication_date,
        title=_required_text(data.get("titleDocument"), "DOGC document metadata"),
        department=_clean_optional_text(document_data.get("issuingAuthority")),
        section=_clean_optional_text(document_data.get("sectionDOGC")),
        document_type=_clean_optional_text(document_data.get("typeDocument")),
        url_html=build_dogc_document_html_url(fallback_document_id),
        url_xml=_clean_optional_text(link_download.get("linkDownloadXML")),
        url_pdf=_clean_optional_text(link_download.get("linkDownloadPDF")),
        raw_metadata={
            "dogc_document_id": str(fallback_document_id),
            "issue_identifier": _clean_optional_text(document_data.get("numDOGC")),
            "date_document": _clean_optional_text(document_data.get("dateDocument")),
            "num_document": _clean_optional_text(document_data.get("numDocument")),
            "num_control": _clean_optional_text(document_data.get("numControl")),
            "uri_eli": (data.get("uriELI") or {}).get("link"),
            "url_rdf": _clean_optional_text(link_download.get("linkDownloadRDF")),
            "url_turtle": _clean_optional_text(link_download.get("linkDownloadTTL")),
            "metadata_sha256": raw_hash,
            "source_metadata": data,
        },
    )


def _metadata_from_search_record(
    record: dict[str, Any], *, target_date: str
) -> DOGCDocumentMetadata:
    document_id = _extract_document_id(record)
    publication_date = _normalize_dogc_date(_required_text(record.get("date"), "DOGC record"))
    if publication_date != target_date:
        raise ValueError(
            f"DOGC record publication date {publication_date} does not match {target_date}"
        )
    pdf_url = _clean_optional_text(record.get("linkDownloadPDF"))
    version_id = _extract_query_value(pdf_url, "versionId")
    official_identifier = _identifier_from_record(record, document_id)
    issue_identifier = _issue_from_pdf_version(version_id)
    return DOGCDocumentMetadata(
        external_id=f"DOGC:{official_identifier}",
        official_identifier=official_identifier,
        publication_date=publication_date,
        title=_required_text(record.get("title"), "DOGC record"),
        department=None,
        section=None,
        document_type=None,
        url_html=build_dogc_document_html_url(document_id),
        url_xml=_build_akoma_url(document_id, version_id, "xml"),
        url_pdf=pdf_url,
        raw_metadata={
            "dogc_document_id": document_id,
            "issue_identifier": issue_identifier,
            "version_id": version_id,
            "url_rdf": _build_akoma_url(document_id, version_id, "rdf"),
            "url_turtle": _build_akoma_url(document_id, version_id, "turtle"),
            "raw_document": record,
        },
    )


def _extract_document_id(record: dict[str, Any]) -> str:
    document_id = _clean_optional_text(record.get("idDocument"))
    if document_id:
        return document_id
    link_title = _required_text(record.get("linkTitle"), "DOGC record")
    parsed = parse_qs(urlparse(link_title).query)
    values = parsed.get("documentId")
    if not values:
        raise ValueError("DOGC record is missing documentId")
    return values[0]


def _identifier_from_record(record: dict[str, Any], document_id: str) -> str:
    candidate = _clean_optional_text(record.get("CVE"))
    if candidate:
        return candidate
    return document_id


def _issue_from_pdf_version(version_id: str | None) -> str | None:
    if version_id and re.fullmatch(r"\d{7}", version_id):
        return str(int(version_id[:4]) + 7520)
    return None


def _build_akoma_url(document_id: str, version_id: str | None, file_format: str) -> str | None:
    if not version_id:
        return None
    return (
        "https://portaldogc.gencat.cat/utilsEADOP/AppJava/AkomaNtoso?"
        f"idNumber={document_id}&idVersion={version_id}&format={file_format}"
    )


def _extract_query_value(url: str | None, key: str) -> str | None:
    if not url:
        return None
    values = parse_qs(urlparse(url).query).get(key)
    return values[0] if values else None


def _normalize_dogc_date(value: str) -> str:
    parts = value.split("/")
    if len(parts) == 3:
        return date(int(parts[2]), int(parts[1]), int(parts[0])).isoformat()
    return validate_dogc_date(value).isoformat()


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
