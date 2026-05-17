from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from official_sources.integrity.hashing import sha256_bytes


@dataclass(frozen=True)
class BOEDocumentMetadata:
    external_id: str
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
class BOESummary:
    publication_date: str
    raw_payload_sha256: str
    raw: dict[str, Any]
    documents: list[BOEDocumentMetadata]


def parse_boe_summary(payload: bytes) -> BOESummary:
    raw = json.loads(payload.decode("utf-8"))
    summary = raw.get("data", {}).get("sumario", {})
    metadata = summary.get("metadatos", {})
    publication_date = _format_boe_date(metadata.get("fecha_publicacion"))
    documents = _extract_documents(summary, publication_date)
    return BOESummary(
        publication_date=publication_date,
        raw_payload_sha256=sha256_bytes(payload),
        raw=raw,
        documents=documents,
    )


def _format_boe_date(value: str | None) -> str:
    if not value or len(value) != 8:
        raise ValueError("BOE summary does not include a valid publication date")
    return f"{value[:4]}-{value[4:6]}-{value[6:]}"


def _extract_documents(summary: dict[str, Any], publication_date: str) -> list[BOEDocumentMetadata]:
    documents: list[BOEDocumentMetadata] = []
    for diary in _as_list(summary.get("diario")):
        for section in _as_list(diary.get("seccion")):
            section_name = section.get("nombre") or section.get("codigo")
            for department in _as_list(section.get("departamento")):
                department_name = department.get("nombre")
                for item in _as_list(department.get("item")):
                    external_id = item.get("identificador") or item.get("id")
                    title = item.get("titulo") or item.get("title")
                    if not external_id or not title:
                        continue
                    documents.append(
                        BOEDocumentMetadata(
                            external_id=external_id,
                            publication_date=publication_date,
                            title=title,
                            department=department_name,
                            section=section_name,
                            document_type=item.get("tipo_disposicion") or item.get("rango"),
                            url_html=_extract_url(item, "url_html"),
                            url_xml=_extract_url(item, "url_xml"),
                            url_pdf=_extract_url(item, "url_pdf"),
                            raw_metadata=item,
                        )
                    )
    return documents


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _extract_url(item: dict[str, Any], key: str) -> str | None:
    value = item.get(key)
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for nested_key in ("texto", "url", "#text"):
            nested_value = value.get(nested_key)
            if isinstance(nested_value, str):
                return nested_value
    return None
