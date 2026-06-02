from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Any
from urllib.parse import unquote

from official_sources.integrity.hashing import sha256_bytes

NO_RESULTS_STATUS = "no_results"


@dataclass(frozen=True)
class PLACSPTenderMetadata:
    external_id: str
    official_identifier: str
    publication_date: str
    title: str
    department: str | None
    section: str | None
    document_type: str
    url_html: str | None
    url_xml: None
    url_pdf: None
    raw_metadata: dict[str, Any]


@dataclass(frozen=True)
class PLACSPFeedPage:
    status: str
    source_snapshot_hash: str
    source_url: str
    feed_type: str
    tenders: list[PLACSPTenderMetadata]
    entry_count: int
    deleted_entries: list[dict[str, str | None]]
    next_url: str | None


def parse_placsp_atom(
    payload: bytes,
    *,
    source_url: str,
    feed_type: str,
) -> PLACSPFeedPage:
    raw_hash = sha256_bytes(payload)
    root = ET.fromstring(payload)
    if _local_name(root.tag) != "feed":
        raise ValueError("PLACSP payload is not an Atom feed.")

    entries = [_entry_from_atom(entry, feed_type=feed_type) for entry in _children(root, "entry")]
    tenders = [entry for entry in entries if entry is not None]
    return PLACSPFeedPage(
        status="success" if tenders else NO_RESULTS_STATUS,
        source_snapshot_hash=raw_hash,
        source_url=source_url,
        feed_type=feed_type,
        tenders=tenders,
        entry_count=len(tenders),
        deleted_entries=_deleted_entries(root),
        next_url=_next_link(root),
    )


def _entry_from_atom(entry: ET.Element, *, feed_type: str) -> PLACSPTenderMetadata | None:
    atom_id = _text(_first_child(entry, "id"))
    if not atom_id:
        return None
    stable_id = _stable_entry_id(atom_id)
    cfs = _first_descendant(entry, "ContractFolderStatus")
    link = _entry_link(entry)
    title = _text(_first_child(entry, "title")) or _text(_first_descendant(cfs, "Name"))
    if not title:
        raise ValueError(f"PLACSP entry is missing title: {atom_id}")
    updated = _text(_first_child(entry, "updated")) or _text(_first_child(entry, "published"))
    if not updated:
        raise ValueError(f"PLACSP entry is missing updated/published date: {atom_id}")
    party = _first_descendant(cfs, "LocatedContractingParty")
    department = _text(_first_descendant(party, "Name"))
    status_code = _text(_first_descendant(cfs, "ContractFolderStatusCode"))
    contract_folder_id = _text(_first_descendant(cfs, "ContractFolderID"))
    raw_metadata = {
        "source_family": "procurement_platform",
        "resource_type": "public_procurement_tender",
        "feed_type": feed_type,
        "atom_id": atom_id,
        "atom_summary": _text(_first_child(entry, "summary")),
        "contract_folder_id": contract_folder_id,
        "status_code": status_code,
        "contract_type_code": _text(_first_descendant(cfs, "TypeCode")),
        "procedure_code": _text(_first_descendant(cfs, "ProcedureCode")),
        "submission_deadline_date": _text(_first_descendant(cfs, "EndDate")),
        "submission_deadline_time": _text(_first_descendant(cfs, "EndTime")),
        "estimated_contract_amount": _text(
            _first_descendant(cfs, "EstimatedOverallContractAmount")
        ),
        "tax_exclusive_amount": _text(_first_descendant(cfs, "TaxExclusiveAmount")),
        "cpv_codes": _texts(cfs, "ItemClassificationCode"),
        "award_date": _text(_first_descendant(cfs, "AwardDate")),
        "winning_party_name": _winning_party_name(cfs),
        "document_metadata": _document_metadata(cfs),
    }
    return PLACSPTenderMetadata(
        external_id=f"PLACSP:{stable_id}",
        official_identifier=f"PLACSP:{stable_id}",
        publication_date=updated[:10],
        title=title,
        department=department,
        section=None,
        document_type="public_procurement_tender",
        url_html=link,
        url_xml=None,
        url_pdf=None,
        raw_metadata=raw_metadata,
    )


def _stable_entry_id(atom_id: str) -> str:
    match = re.search(r"/(\d+)(?:$|[?#])", atom_id)
    if match:
        return match.group(1)
    return re.sub(r"[^A-Za-z0-9_.:-]+", "-", atom_id).strip("-")


def _entry_link(entry: ET.Element) -> str | None:
    for child in _children(entry, "link"):
        href = child.attrib.get("href")
        if href:
            return unquote(href)
    return None


def _next_link(root: ET.Element) -> str | None:
    for child in _children(root, "link"):
        if child.attrib.get("rel") == "next":
            return child.attrib.get("href")
    return None


def _deleted_entries(root: ET.Element) -> list[dict[str, str | None]]:
    deleted = []
    for entry in _children(root, "deleted-entry"):
        comment = _first_child(entry, "comment")
        deleted.append(
            {
                "ref": entry.attrib.get("ref"),
                "when": entry.attrib.get("when"),
                "comment_type": comment.attrib.get("type") if comment is not None else None,
            }
        )
    return deleted


def _winning_party_name(cfs: ET.Element | None) -> str | None:
    tender_result = _first_descendant(cfs, "TenderResult")
    winning_party = _first_descendant(tender_result, "WinningParty")
    return _text(_first_descendant(winning_party, "Name"))


def _document_metadata(cfs: ET.Element | None) -> list[dict[str, str | None]]:
    if cfs is None:
        return []
    documents = []
    for element in cfs.iter():
        if not _local_name(element.tag).endswith("DocumentReference"):
            continue
        document_id = _text(_first_descendant(element, "ID"))
        official_url = _text(_first_descendant(element, "URI"))
        file_name = _text(_first_descendant(element, "FileName"))
        document_hash = _text(_first_descendant(element, "DocumentHash"))
        if not (document_id or official_url):
            continue
        documents.append(
            {
                "document_id": document_id,
                "file_name": file_name or document_id,
                "official_url": official_url,
                "document_hash": document_hash,
                "source_type": _local_name(element.tag),
            }
        )
    return documents


def _texts(root: ET.Element | None, local_name: str) -> list[str]:
    if root is None:
        return []
    values = []
    for element in root.iter():
        if _local_name(element.tag) == local_name:
            value = _text(element)
            if value and value not in values:
                values.append(value)
    return values


def _first_descendant(root: ET.Element | None, local_name: str) -> ET.Element | None:
    if root is None:
        return None
    for element in root.iter():
        if _local_name(element.tag) == local_name:
            return element
    return None


def _first_child(root: ET.Element | None, local_name: str) -> ET.Element | None:
    if root is None:
        return None
    for child in list(root):
        if _local_name(child.tag) == local_name:
            return child
    return None


def _children(root: ET.Element, local_name: str) -> list[ET.Element]:
    return [child for child in list(root) if _local_name(child.tag) == local_name]


def _text(element: ET.Element | None) -> str | None:
    if element is None or element.text is None:
        return None
    text = element.text.strip()
    return text or None


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]
