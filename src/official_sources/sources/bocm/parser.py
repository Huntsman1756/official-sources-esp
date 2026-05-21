from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from datetime import date
from html import unescape
from urllib.parse import urljoin
from xml.etree import ElementTree

from official_sources.integrity.hashing import sha256_bytes
from official_sources.sources.bocm.client import (
    BOCM_BASE_URL,
    build_bocm_document_html_url,
    build_bocm_document_json_url,
    build_bocm_document_pdf_url,
    build_bocm_document_xml_url,
    build_bocm_issue_url,
    validate_bocm_date,
)

NO_PUBLICATION_STATUS = "no_publication"
BOCM_DOCUMENT_ID_RE = re.compile(r"BOCM-\d{8}-\d+", re.IGNORECASE)
BOCM_ISSUE_RE = re.compile(r"bocm-(\d{8})-(\d+)", re.IGNORECASE)
LINK_RE = re.compile(
    r"<a\b[^>]*href=[\"'](?P<href>[^\"']+)[\"'][^>]*>(?P<label>.*?)</a>",
    re.I | re.S,
)
TAG_RE = re.compile(r"<[^>]+>")


@dataclass(frozen=True)
class BOCMIssueDiscovery:
    target_date: str
    raw_payload_sha256: str
    status: str
    issue_identifier: str | None = None
    issue_number: str | None = None
    issue_url: str | None = None


@dataclass(frozen=True)
class BOCMDocumentMetadata:
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
class BOCMIssuePage:
    target_date: str
    issue_identifier: str
    issue_url: str
    raw_payload_sha256: str
    documents: list[BOCMDocumentMetadata]


def parse_bocm_search_day_response(
    payload: bytes,
    *,
    target_date: str,
    final_url: str | None = None,
) -> BOCMIssueDiscovery:
    parsed_date = validate_bocm_date(target_date)
    raw_payload_sha256 = sha256_bytes(payload)
    html = payload.decode("utf-8", errors="replace")
    candidates = []
    if final_url:
        candidates.extend(BOCM_ISSUE_RE.findall(final_url))
    candidates.extend(BOCM_ISSUE_RE.findall(html))
    expected_yyyymmdd = parsed_date.strftime("%Y%m%d")
    for yyyymmdd, issue_number in candidates:
        if yyyymmdd == expected_yyyymmdd:
            issue_identifier = f"bocm-{yyyymmdd}-{issue_number}"
            return BOCMIssueDiscovery(
                target_date=target_date,
                raw_payload_sha256=raw_payload_sha256,
                status="success",
                issue_identifier=issue_identifier,
                issue_number=issue_number,
                issue_url=build_bocm_issue_url(target_date, issue_number),
            )
    if "no se han encontrado resultados" in _normalize_for_search(html):
        return BOCMIssueDiscovery(
            target_date=target_date,
            raw_payload_sha256=raw_payload_sha256,
            status=NO_PUBLICATION_STATUS,
        )
    raise ValueError(f"BOCM search response did not resolve an issue for date {target_date}")


def parse_bocm_issue_page(
    payload: bytes,
    *,
    target_date: str,
    issue_identifier: str,
    issue_url: str,
) -> BOCMIssuePage:
    validate_bocm_date(target_date)
    stripped_payload = payload.lstrip()
    if stripped_payload.startswith(b"<sumario") or stripped_payload.startswith(b"<?xml"):
        return _parse_bocm_issue_xml(
            payload,
            target_date=target_date,
            issue_identifier=issue_identifier,
            issue_url=issue_url,
        )
    html = payload.decode("utf-8", errors="replace")
    links = _extract_links(html)
    titles: dict[str, str] = {}
    urls_by_identifier: dict[str, dict[str, str]] = {}
    departments_by_identifier: dict[str, str | None] = {}
    current_department: str | None = None
    expected_prefix = f"BOCM-{target_date.replace('-', '')}-"
    for fragment in _issue_fragments(html):
        department = _extract_heading(fragment) or current_department
        current_department = department or current_department
        for href, label in _extract_links(fragment):
            identifier = _identifier_from_text(href) or _identifier_from_text(label)
            if identifier is None or not identifier.startswith(expected_prefix):
                continue
            urls = urls_by_identifier.setdefault(identifier, {})
            official_url = urljoin(BOCM_BASE_URL, href)
            lower_url = official_url.lower()
            if lower_url.endswith(".xml"):
                urls["xml"] = official_url
            elif lower_url.endswith(".json"):
                urls["jsonld"] = official_url
            elif lower_url.endswith(".pdf"):
                urls["pdf"] = official_url
            else:
                urls["html"] = official_url
                titles.setdefault(identifier, _clean_html_text(label))
                departments_by_identifier.setdefault(identifier, department)
    if not urls_by_identifier:
        for href, label in links:
            identifier = _identifier_from_text(href) or _identifier_from_text(label)
            if identifier is None or not identifier.startswith(expected_prefix):
                continue
            urls = urls_by_identifier.setdefault(identifier, {})
            official_url = urljoin(BOCM_BASE_URL, href)
            lower_url = official_url.lower()
            if lower_url.endswith(".xml"):
                urls["xml"] = official_url
            elif lower_url.endswith(".json"):
                urls["jsonld"] = official_url
            elif lower_url.endswith(".pdf"):
                urls["pdf"] = official_url
            else:
                urls["html"] = official_url
                titles.setdefault(identifier, _clean_html_text(label))
    documents = [
        _metadata_from_issue_link(
            identifier,
            target_date=target_date,
            title=titles.get(identifier) or identifier,
            department=departments_by_identifier.get(identifier),
            issue_identifier=issue_identifier,
            issue_url=issue_url,
            urls=urls,
        )
        for identifier, urls in sorted(urls_by_identifier.items())
        if "html" in urls or "xml" in urls or "jsonld" in urls
    ]
    return BOCMIssuePage(
        target_date=target_date,
        issue_identifier=issue_identifier,
        issue_url=issue_url,
        raw_payload_sha256=sha256_bytes(payload),
        documents=documents,
    )


def _parse_bocm_issue_xml(
    payload: bytes,
    *,
    target_date: str,
    issue_identifier: str,
    issue_url: str,
) -> BOCMIssuePage:
    root = ElementTree.fromstring(payload)
    documents: list[BOCMDocumentMetadata] = []
    seen_identifiers: set[str] = set()
    expected_prefix = f"BOCM-{target_date.replace('-', '')}-"
    for section in root.findall(".//seccion"):
        section_name = _normalize_text_value(section.attrib.get("nombre"))
        for agency in section.findall(".//organismo"):
            department = _normalize_text_value(agency.attrib.get("nombre"))
            for provision in agency.findall(".//disposicion"):
                identifier = _xml_text(provision, "identificador")
                if identifier is None or not identifier.upper().startswith(expected_prefix):
                    continue
                normalized_identifier = identifier.upper()
                if normalized_identifier in seen_identifiers:
                    continue
                seen_identifiers.add(normalized_identifier)
                title = _xml_text(provision, "titulo") or identifier
                document_type = _normalize_text_value(_xml_text(provision, "rango"))
                url_html = _xml_text(provision, "url_html") or build_bocm_document_html_url(
                    identifier
                )
                url_xml = _xml_text(provision, "url_xml") or build_bocm_document_xml_url(identifier)
                url_pdf = _xml_text(provision, "url_pdf")
                documents.append(
                    _metadata_from_issue_link(
                        identifier,
                        target_date=target_date,
                        title=title,
                        department=department,
                        issue_identifier=issue_identifier,
                        issue_url=issue_url,
                        urls={
                            "html": url_html,
                            "xml": url_xml,
                            "jsonld": build_bocm_document_json_url(identifier),
                            "pdf": url_pdf or build_bocm_document_pdf_url(identifier),
                        },
                        extra_raw_metadata={"issue_xml_sha256": sha256_bytes(payload)},
                        document_type=document_type,
                        section=section_name,
                    )
                )
    return BOCMIssuePage(
        target_date=target_date,
        issue_identifier=issue_identifier,
        issue_url=issue_url,
        raw_payload_sha256=sha256_bytes(payload),
        documents=documents,
    )


def parse_bocm_document_xml(payload: bytes) -> BOCMDocumentMetadata:
    raw_hash = sha256_bytes(payload)
    root = ElementTree.fromstring(payload)
    official_identifier = _xml_text(root, ".//identificador")
    if not official_identifier:
        raise ValueError("BOCM XML document has no identifier")
    publication_date = _normalize_bocm_xml_date(_xml_text(root, ".//fecha_publicacion"))
    title = _xml_text(root, ".//titulo") or official_identifier
    department = _normalize_text_value(_xml_text(root, ".//departamento"))
    document_type = _normalize_text_value(_xml_text(root, ".//rango"))
    return _metadata_from_issue_link(
        official_identifier,
        target_date=publication_date,
        title=title,
        department=department,
        issue_identifier=None,
        issue_url=None,
        urls={
            "html": build_bocm_document_html_url(official_identifier),
            "xml": build_bocm_document_xml_url(official_identifier),
            "jsonld": build_bocm_document_json_url(official_identifier),
            "pdf": build_bocm_document_pdf_url(official_identifier),
        },
        extra_raw_metadata={"xml_sha256": raw_hash},
        document_type=document_type,
    )


def parse_bocm_document_jsonld(payload: bytes) -> BOCMDocumentMetadata:
    raw_hash = sha256_bytes(payload)
    data = json.loads(payload)
    official_identifier = str(data.get("legislationIdentifier") or "").strip()
    if not official_identifier:
        raise ValueError("BOCM JSON-LD document has no legislationIdentifier")
    publication_date = str(data.get("datePublished") or "").strip()
    validate_bocm_date(publication_date)
    title = str(data.get("name") or official_identifier).strip()
    department = _normalize_text_value(data.get("legislationResponsible"))
    document_type = _normalize_text_value(data.get("legislationType"))
    url_html = str(data.get("@id") or build_bocm_document_html_url(official_identifier)).strip()
    return _metadata_from_issue_link(
        official_identifier,
        target_date=publication_date,
        title=title,
        department=department,
        issue_identifier=None,
        issue_url=None,
        urls={
            "html": url_html,
            "xml": build_bocm_document_xml_url(official_identifier),
            "jsonld": build_bocm_document_json_url(official_identifier),
            "pdf": build_bocm_document_pdf_url(official_identifier),
        },
        extra_raw_metadata={"jsonld_sha256": raw_hash, "jsonld": data},
        document_type=document_type,
    )


def _metadata_from_issue_link(
    official_identifier: str,
    *,
    target_date: str,
    title: str,
    department: str | None,
    issue_identifier: str | None,
    issue_url: str | None,
    urls: dict[str, str],
    extra_raw_metadata: dict | None = None,
    document_type: str | None = None,
    section: str | None = None,
) -> BOCMDocumentMetadata:
    official_identifier = official_identifier.upper()
    url_html = urls.get("html") or build_bocm_document_html_url(official_identifier)
    url_xml = urls.get("xml") or build_bocm_document_xml_url(official_identifier)
    url_jsonld = urls.get("jsonld") or build_bocm_document_json_url(official_identifier)
    url_pdf = urls.get("pdf")
    raw_metadata = {
        "bocm_official_id": official_identifier,
        "issue_identifier": issue_identifier,
        "issue_url": issue_url,
        "url_jsonld": url_jsonld,
    }
    if extra_raw_metadata:
        raw_metadata.update(extra_raw_metadata)
    return BOCMDocumentMetadata(
        external_id=f"BOCM:{official_identifier}",
        official_identifier=official_identifier,
        publication_date=target_date,
        title=_clean_html_text(title),
        department=department,
        section=section or issue_identifier,
        document_type=document_type,
        url_html=url_html,
        url_xml=url_xml,
        url_pdf=url_pdf,
        raw_metadata=raw_metadata,
    )


def _extract_links(html: str) -> list[tuple[str, str]]:
    return [(match.group("href"), match.group("label")) for match in LINK_RE.finditer(html)]


def _issue_fragments(html: str) -> list[str]:
    article_fragments = re.findall(r"<article\b.*?</article>", html, flags=re.I | re.S)
    return article_fragments or [html]


def _extract_heading(fragment: str) -> str | None:
    match = re.search(r"<h[1-6]\b[^>]*>(.*?)</h[1-6]>", fragment, flags=re.I | re.S)
    if not match:
        return None
    return _normalize_text_value(_clean_html_text(match.group(1)))


def _identifier_from_text(value: str) -> str | None:
    match = BOCM_DOCUMENT_ID_RE.search(value)
    if not match:
        return None
    return match.group(0).upper()


def _clean_html_text(value: str) -> str:
    return re.sub(r"\s+", " ", unescape(TAG_RE.sub(" ", value))).strip()


def _normalize_text_value(value: object | None) -> str | None:
    if value is None:
        return None
    text = unicodedata.normalize("NFKD", str(value))
    ascii_text = text.encode("ascii", "ignore").decode("ascii")
    cleaned = re.sub(r"\s+", " ", ascii_text).strip()
    return cleaned.upper() if cleaned else None


def _normalize_for_search(value: str) -> str:
    text = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return text.lower()


def _xml_text(root: ElementTree.Element, path: str) -> str | None:
    element = root.find(path)
    if element is None or element.text is None:
        return None
    return element.text.strip()


def _normalize_bocm_xml_date(value: str | None) -> str:
    if value is None:
        raise ValueError("BOCM XML document has no publication date")
    normalized = value.strip().replace("/", "-")
    return date.fromisoformat(normalized).isoformat()
