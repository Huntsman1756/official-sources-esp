from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date
from html import unescape
from typing import Any
from urllib.parse import urljoin

from official_sources.integrity.hashing import sha256_bytes

BOJA_PORTAL_BASE_URL = "https://www.juntadeandalucia.es"


@dataclass(frozen=True)
class BOJADocumentMetadata:
    external_id: str
    official_id: str
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
class BOJASearchResponse:
    target_date: str
    raw_payload_sha256: str
    total_hits: int
    raw: dict[str, Any]
    documents: list[BOJADocumentMetadata]


def parse_boja_search_response(payload: bytes, *, target_date: str) -> BOJASearchResponse:
    raw = json.loads(payload.decode("utf-8"))
    results = raw.get("results") or []
    if not isinstance(results, list):
        raise ValueError("BOJA API response results must be a list")
    return BOJASearchResponse(
        target_date=target_date,
        raw_payload_sha256=sha256_bytes(payload),
        total_hits=_int_value(raw.get("total_hits", raw.get("hits", len(results)))),
        raw=raw,
        documents=[document for document in _extract_documents(results) if document is not None],
    )


def _extract_documents(results: list[Any]) -> list[BOJADocumentMetadata | None]:
    documents: list[BOJADocumentMetadata | None] = []
    for item in results:
        if not isinstance(item, dict):
            continue
        official_id = str(item.get("id") or "").strip()
        title = _title_from_item(item)
        if not official_id or not title:
            continue
        publication_date = _format_boja_date(item.get("date"))
        public_url = _url_or_none(item.get("publicUrl"))
        pdf_url = _absolute_portal_url(_url_or_none(item.get("pathPdf")))
        documents.append(
            BOJADocumentMetadata(
                external_id=f"BOJA:{official_id}",
                official_id=official_id,
                publication_date=publication_date,
                title=title,
                department=_str_or_none(item.get("organisation")),
                section=_str_or_none(item.get("titleSec")),
                document_type=_str_or_none(item.get("type") or item.get("subtitle")),
                url_html=public_url,
                url_xml=None,
                url_pdf=pdf_url,
                raw_metadata={**item, "boja_official_id": official_id},
            )
        )
    return documents


def _format_boja_date(value: Any) -> str:
    if not isinstance(value, str):
        raise ValueError("BOJA document does not include a valid publication date")
    value = value.strip()
    if re.fullmatch(r"\d{2}/\d{2}/\d{4}", value):
        day, month, year = value.split("/")
        return f"{year}-{month}-{day}"
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        date.fromisoformat(value)
        return value
    raise ValueError("BOJA document does not include a valid publication date")


def _title_from_item(item: dict[str, Any]) -> str | None:
    value = item.get("title") or item.get("summaryNoHtml") or item.get("summary")
    if not isinstance(value, str):
        return None
    text = re.sub(r"<[^>]+>", " ", value)
    text = unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text or None


def _absolute_portal_url(value: str | None) -> str | None:
    if value is None:
        return None
    return urljoin(f"{BOJA_PORTAL_BASE_URL}/", value)


def _url_or_none(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    value = value.strip()
    return value or None


def _str_or_none(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    value = value.strip()
    return value or None


def _int_value(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
