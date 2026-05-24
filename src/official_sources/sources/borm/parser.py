from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Any

from official_sources.integrity.hashing import sha256_bytes
from official_sources.sources.borm.client import validate_borm_date

NO_PUBLICATION_STATUS = "no_publication"


@dataclass(frozen=True)
class BORMDocumentMetadata:
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
class BORMIssue:
    target_date: str
    raw_payload_sha256: str
    status: str
    issue_identifier: str | None
    issue_identifiers: list[str]
    documents: list[BORMDocumentMetadata]


def parse_borm_date_response(payload: bytes, *, target_date: str) -> BORMIssue:
    validate_borm_date(target_date)
    raw_payload_sha256 = sha256_bytes(payload)
    root = ET.fromstring(payload)
    records = [
        _element_to_record(element)
        for element in _record_elements(root)
        if (_clean_optional_text(element.findtext("Fec_Publicacion")) or "").startswith(target_date)
    ]
    if not records:
        return BORMIssue(
            target_date=target_date,
            raw_payload_sha256=raw_payload_sha256,
            status=NO_PUBLICATION_STATUS,
            issue_identifier=None,
            issue_identifiers=[],
            documents=[],
        )
    issue_identifiers = _issue_identifiers_in_order(records)
    if len(issue_identifiers) != 1 and not _is_boletin_with_supplement(records):
        raise ValueError(f"BORM response for {target_date} has mixed issue identifiers")
    return BORMIssue(
        target_date=target_date,
        raw_payload_sha256=raw_payload_sha256,
        status="success",
        issue_identifier=",".join(issue_identifiers),
        issue_identifiers=issue_identifiers,
        documents=[_metadata_from_record(record) for record in records],
    )


def parse_borm_document_metadata(payload: bytes) -> BORMDocumentMetadata:
    raw_hash = sha256_bytes(payload)
    root = ET.fromstring(payload)
    record = _element_to_record(root)
    metadata = _metadata_from_record(record)
    return BORMDocumentMetadata(
        **{
            **metadata.__dict__,
            "raw_metadata": {
                **metadata.raw_metadata,
                "metadata_sha256": raw_hash,
            },
        }
    )


def _record_elements(root: ET.Element) -> list[ET.Element]:
    if _strip_namespace(root.tag) == "resultado":
        return [root]
    return [element for element in root if _strip_namespace(element.tag) == "resultado"]


def _element_to_record(element: ET.Element) -> dict[str, str | None]:
    return {_strip_namespace(child.tag): _clean_optional_text(child.text) for child in element}


def _metadata_from_record(record: dict[str, str | None]) -> BORMDocumentMetadata:
    publication_date = validate_borm_date(
        _required_text(record.get("Fec_Publicacion"), "BORM record")[:10]
    ).isoformat()
    official_identifier = _required_text(record.get("NPE"), "BORM record")
    issue_identifier = _issue_identifier(record)
    announcement_id = _required_text(record.get("ID_Anuncio"), "BORM record")
    digital_object_id = _clean_optional_text(record.get("ID_Objeto_Digital_Anuncio"))
    issue_year = _required_text(record.get("Ejercicio_Publicacion"), "BORM record")
    issue_number = _required_text(record.get("Num_Publicacion"), "BORM record")
    return BORMDocumentMetadata(
        external_id=f"BORM:{official_identifier}",
        official_identifier=official_identifier,
        publication_date=publication_date,
        title=_required_text(record.get("Sumario"), "BORM record"),
        department=_clean_optional_text(record.get("Anunciante"))
        or _clean_optional_text(record.get("Administracion")),
        section=_clean_optional_text(record.get("Seccion")),
        document_type=_clean_optional_text(record.get("Rango")),
        url_html=_clean_optional_text(record.get("URL_HTML")),
        url_xml=None,
        url_pdf=_clean_optional_text(record.get("URL_PDF")),
        raw_metadata={
            "issue_identifier": issue_identifier,
            "announcement_id": announcement_id,
            "digital_object_id": digital_object_id,
            "publication_type": _clean_optional_text(record.get("Publicacion")),
            "administration": _clean_optional_text(record.get("Administracion")),
            "subsection": _clean_optional_text(record.get("Apartado")),
            "disposition_number": _clean_optional_text(record.get("Num_Disposicion")),
            "disposition_date": _clean_optional_text(record.get("Fec_Disposicion")),
            "category": _clean_optional_text(record.get("Categoria")),
            "pages": _clean_optional_text(record.get("NUM_PAGINAS")),
            "issue_pdf_url": _build_issue_pdf_url(issue_year=issue_year, issue_number=issue_number),
            "summary_pdf_url": _build_summary_pdf_url(
                issue_year=issue_year,
                issue_number=issue_number,
            ),
            "raw_document": record,
        },
    )


def _issue_identifier(record: dict[str, str | None]) -> str:
    issue_number = _required_text(record.get("Num_Publicacion"), "BORM record")
    issue_year = _required_text(record.get("Ejercicio_Publicacion"), "BORM record")
    return f"{issue_number}/{issue_year}"


def _issue_identifiers_in_order(records: list[dict[str, str | None]]) -> list[str]:
    identifiers: list[str] = []
    for record in records:
        identifier = _issue_identifier(record)
        if identifier not in identifiers:
            identifiers.append(identifier)
    return identifiers


def _is_boletin_with_supplement(records: list[dict[str, str | None]]) -> bool:
    publication_types_by_issue: dict[str, set[str]] = {}
    for record in records:
        publication_type = (_clean_optional_text(record.get("Publicacion")) or "").upper()
        if publication_type not in {"BOLETIN", "SUPLEMENTO"}:
            return False
        publication_types_by_issue.setdefault(_issue_identifier(record), set()).add(
            publication_type
        )

    boletin_issue_count = sum(
        1
        for publication_types in publication_types_by_issue.values()
        if "BOLETIN" in publication_types
    )
    supplement_issue_count = sum(
        1
        for publication_types in publication_types_by_issue.values()
        if publication_types == {"SUPLEMENTO"}
    )
    return boletin_issue_count == 1 and supplement_issue_count >= 1


def _build_issue_pdf_url(*, issue_year: str, issue_number: str) -> str:
    return f"https://www.borm.es/services/boletin/ano/{issue_year}/numero/{issue_number}/pdf"


def _build_summary_pdf_url(*, issue_year: str, issue_number: str) -> str:
    return (
        f"https://www.borm.es/services/boletin/ano/{issue_year}/numero/{issue_number}/sumario/pdf"
    )


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


def _strip_namespace(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]
