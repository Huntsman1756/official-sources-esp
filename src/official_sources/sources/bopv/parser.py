from __future__ import annotations

import ast
import re
import unicodedata
from dataclasses import dataclass
from xml.etree import ElementTree

from official_sources.integrity.hashing import sha256_bytes
from official_sources.sources.bopv.client import (
    bopv_document_identifier,
    bopv_document_stem,
    bopv_issue_identifier,
    build_bopv_document_epub_url,
    build_bopv_document_html_url,
    build_bopv_document_pdf_url,
    build_bopv_document_xml_url,
    build_bopv_issue_html_url,
    build_bopv_issue_xml_url,
    validate_bopv_date,
)

NO_PUBLICATION_STATUS = "no_publication"


@dataclass(frozen=True)
class BOPVIssueDiscovery:
    target_date: str
    raw_payload_sha256: str
    status: str
    issue_identifiers: list[str]
    issue_stems: list[str]
    issue_html_urls: list[str]
    issue_xml_urls: list[str]


@dataclass(frozen=True)
class BOPVDocumentMetadata:
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
    raw_metadata: dict


@dataclass(frozen=True)
class BOPVIssue:
    target_date: str
    issue_identifier: str
    issue_url: str
    raw_payload_sha256: str
    documents: list[BOPVDocumentMetadata]


def parse_bopv_calendar(payload: bytes, *, target_date: str) -> BOPVIssueDiscovery:
    parsed_date = validate_bopv_date(target_date)
    yyyymmdd = parsed_date.strftime("%Y%m%d")
    html = payload.decode("iso-8859-1", errors="replace")
    dates = _extract_js_array(html, "diasHabilitados")
    links_by_date = _extract_js_array(html, "enlaces")
    if yyyymmdd not in dates:
        return BOPVIssueDiscovery(
            target_date=target_date,
            raw_payload_sha256=sha256_bytes(payload),
            status=NO_PUBLICATION_STATUS,
            issue_identifiers=[],
            issue_stems=[],
            issue_html_urls=[],
            issue_xml_urls=[],
        )
    index = dates.index(yyyymmdd)
    issue_links = links_by_date[index] if index < len(links_by_date) else []
    issue_stems = [_issue_stem_from_link(link) for link in issue_links if str(link).strip()]
    status = NO_PUBLICATION_STATUS if not issue_stems else "success"
    return BOPVIssueDiscovery(
        target_date=target_date,
        raw_payload_sha256=sha256_bytes(payload),
        status=status,
        issue_identifiers=[bopv_issue_identifier(target_date, stem) for stem in issue_stems],
        issue_stems=issue_stems,
        issue_html_urls=[build_bopv_issue_html_url(target_date, stem) for stem in issue_stems],
        issue_xml_urls=[build_bopv_issue_xml_url(target_date, stem) for stem in issue_stems],
    )


def parse_bopv_issue_xml(
    payload: bytes,
    *,
    target_date: str,
    issue_identifier: str,
    issue_url: str,
) -> BOPVIssue:
    validate_bopv_date(target_date)
    root = ElementTree.fromstring(payload)
    raw_hash = sha256_bytes(payload)
    section: str | None = None
    subsection: str | None = None
    organism: str | None = None
    title: str | None = None
    documents: list[BOPVDocumentMetadata] = []
    for child in root:
        text = _normalize_text_value(child.text)
        if child.tag == "BOPVSumarioSeccion":
            section = text
        elif child.tag == "BOPVSumarioSubseccion":
            subsection = text
        elif child.tag == "BOPVSumarioOrganismo":
            organism = text
        elif child.tag == "BOPVSumarioTitulo":
            title = text
        elif child.tag == "BOPVSumarioOrden" and text:
            stem = bopv_document_stem(target_date, text)
            documents.append(
                _metadata_from_parts(
                    target_date=target_date,
                    document_stem=stem,
                    order_number=text,
                    title=title or stem,
                    department=organism,
                    section=section,
                    subsection=subsection,
                    issue_identifier=issue_identifier,
                    issue_url=issue_url,
                    extra_raw_metadata={"issue_xml_sha256": raw_hash},
                )
            )
            title = None
    return BOPVIssue(
        target_date=target_date,
        issue_identifier=issue_identifier,
        issue_url=issue_url,
        raw_payload_sha256=raw_hash,
        documents=documents,
    )


def parse_bopv_document_xml(
    payload: bytes,
    *,
    publication_date: str,
    document_stem: str,
) -> BOPVDocumentMetadata:
    validate_bopv_date(publication_date)
    raw_hash = sha256_bytes(payload)
    root = ElementTree.fromstring(payload)
    order_number = _xml_text(root, "BOPVOrden")
    return _metadata_from_parts(
        target_date=publication_date,
        document_stem=document_stem,
        order_number=order_number,
        title=_xml_text(root, "BOPVTitulo") or document_stem,
        department=_xml_text(root, "BOPVOrganismo"),
        section=_xml_text(root, "BOPVSeccion"),
        subsection=_xml_text(root, "BOPVSubseccion"),
        issue_identifier=None,
        issue_url=None,
        extra_raw_metadata={"xml_sha256": raw_hash, "nexpei": root.attrib.get("NEXPEI")},
    )


def _metadata_from_parts(
    *,
    target_date: str,
    document_stem: str,
    order_number: str | None,
    title: str,
    department: str | None,
    section: str | None,
    subsection: str | None,
    issue_identifier: str | None,
    issue_url: str | None,
    extra_raw_metadata: dict | None = None,
) -> BOPVDocumentMetadata:
    official_identifier = bopv_document_identifier(target_date, document_stem)
    raw_metadata = {
        "document_stem": document_stem,
        "order_number": order_number,
        "subsection": subsection,
        "issue_identifier": issue_identifier,
        "issue_url": issue_url,
        "url_epub": build_bopv_document_epub_url(target_date, document_stem),
    }
    if extra_raw_metadata:
        raw_metadata.update(extra_raw_metadata)
    return BOPVDocumentMetadata(
        external_id=f"BOPV:{official_identifier}",
        official_identifier=official_identifier,
        publication_date=target_date,
        title=title,
        department=department,
        section=section,
        document_type=None,
        url_html=build_bopv_document_html_url(target_date, document_stem),
        url_xml=build_bopv_document_xml_url(target_date, document_stem),
        url_pdf=build_bopv_document_pdf_url(target_date, document_stem),
        raw_metadata=raw_metadata,
    )


def _extract_js_array(html: str, name: str) -> list:
    match = re.search(rf"{re.escape(name)}\s*=\s*(\[.*?\]);", html, flags=re.S)
    if not match:
        raise ValueError(f"BOPV calendar does not include {name}")
    value = ast.literal_eval(match.group(1))
    if not isinstance(value, list):
        raise ValueError(f"BOPV calendar {name} is not a list")
    return value


def _issue_stem_from_link(value: object) -> str:
    stem = str(value).strip()
    if stem.endswith(".shtml") or stem.endswith(".xml"):
        stem = stem.rsplit(".", 1)[0]
    return stem


def _xml_text(root: ElementTree.Element, path: str) -> str | None:
    element = root.find(path)
    if element is None:
        return None
    return _normalize_text_value(element.text)


def _normalize_text_value(value: object | None) -> str | None:
    if value is None:
        return None
    text = unicodedata.normalize("NFKC", str(value))
    cleaned = re.sub(r"\s+", " ", text).strip()
    return cleaned or None
