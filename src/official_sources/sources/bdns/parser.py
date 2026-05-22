from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from official_sources.integrity.hashing import sha256_bytes
from official_sources.sources.bdns.client import build_bdns_call_detail_url, validate_bdns_num_conv

NO_RESULTS_STATUS = "no_results"


class BDNSNotFoundError(ValueError):
    pass


@dataclass(frozen=True)
class BDNSCallMetadata:
    external_id: str
    official_identifier: str
    publication_date: str
    title: str
    department: str | None
    section: str | None
    document_type: str | None
    url_html: str
    url_xml: None
    url_pdf: None
    raw_metadata: dict[str, Any]


@dataclass(frozen=True)
class BDNSCallPage:
    status: str
    source_snapshot_hash: str
    source_url: str
    calls: list[BDNSCallMetadata]
    total_elements: int
    total_pages: int
    page_number: int
    last: bool


def parse_bdns_call_page(payload: bytes, *, source_url: str) -> BDNSCallPage:
    raw_hash = sha256_bytes(payload)
    data = json.loads(payload.decode("utf-8-sig"))
    items = _page_items(data)
    if not items:
        return BDNSCallPage(
            status=NO_RESULTS_STATUS,
            source_snapshot_hash=raw_hash,
            source_url=source_url,
            calls=[],
            total_elements=int(data.get("totalElements") or 0),
            total_pages=int(data.get("totalPages") or 0),
            page_number=int(data.get("number") or 0),
            last=bool(data.get("last", True)),
        )
    return BDNSCallPage(
        status="success",
        source_snapshot_hash=raw_hash,
        source_url=source_url,
        calls=[_call_from_list_item(item) for item in items],
        total_elements=int(data.get("totalElements") or len(items)),
        total_pages=int(data.get("totalPages") or 1),
        page_number=int(data.get("number") or 0),
        last=bool(data.get("last", False)),
    )


def parse_bdns_call_detail(payload: bytes, *, num_conv: str) -> BDNSCallMetadata:
    raw_hash = sha256_bytes(payload)
    data = json.loads(payload.decode("utf-8-sig"))
    if data.get("status") == 404 or _clean_optional_text(data.get("error")) == "Not Found":
        raise BDNSNotFoundError(f"BDNS call detail not found: {num_conv}")
    code = _first_text(data.get("codigoBDNS"), data.get("codigoBdns"), data.get("codigo"), num_conv)
    if not code:
        raise ValueError("BDNS call detail is missing codigoBDNS.")
    validate_bdns_num_conv(code)
    title = _required_text(data.get("descripcion"), "BDNS call detail")
    organ = data.get("organo") if isinstance(data.get("organo"), dict) else {}
    department = _first_text(organ.get("nivel3"), organ.get("nivel2"), organ.get("nivel1"))
    publication_date = _first_text(
        data.get("fechaPublicacion"),
        data.get("fechaRecepcion"),
        data.get("fechaRegistro"),
    )
    if not publication_date:
        raise ValueError("BDNS call detail is missing a publication or registration date.")
    return BDNSCallMetadata(
        external_id=f"BDNS:{code}",
        official_identifier=f"BDNS:{code}",
        publication_date=publication_date,
        title=title,
        department=department,
        section=_first_text(organ.get("nivel1"), organ.get("nivel2")),
        document_type=_clean_optional_text(data.get("tipoConvocatoria")),
        url_html=build_bdns_call_detail_url(code),
        url_xml=None,
        url_pdf=None,
        raw_metadata={
            "source_family": "grants_registry",
            "resource_type": "grant_call",
            "bdns_code": code,
            "bdns_internal_id": data.get("id"),
            "registration_date": _clean_optional_text(data.get("fechaRecepcion")),
            "application_start_date": _clean_optional_text(data.get("fechaInicioSolicitud")),
            "application_end_date": _clean_optional_text(data.get("fechaFinSolicitud")),
            "budget": data.get("presupuestoTotal")
            or data.get("presupuesto")
            or data.get("importeTotal")
            or data.get("importe"),
            "beneficiary_type": _descriptions(data.get("tiposBeneficiarios")),
            "instrument_type": _descriptions(data.get("instrumentos")),
            "sector_activity": _descriptions(data.get("sectores")),
            "territorial_scope": _descriptions(data.get("regiones")),
            "application_url": _clean_optional_text(data.get("sedeElectronica")),
            "base_regulation_url": _clean_optional_text(data.get("urlBasesReguladoras")),
            "detail_api_sha256": raw_hash,
            "source_metadata": data,
        },
    )


def _page_items(data: dict[str, Any]) -> list[dict[str, Any]]:
    raw_items = data.get("content")
    if raw_items is None:
        raw_items = data.get("items")
    if not isinstance(raw_items, list):
        return []
    return [item for item in raw_items if isinstance(item, dict)]


def _call_from_list_item(item: dict[str, Any]) -> BDNSCallMetadata:
    code = _first_text(
        item.get("numeroConvocatoria"),
        item.get("codigoBDNS"),
        item.get("codigoBdns"),
        item.get("codigo"),
        item.get("id"),
    )
    if not code:
        raise ValueError("BDNS call list item is missing numeroConvocatoria.")
    validate_bdns_num_conv(code)
    title = _required_text(item.get("descripcion"), "BDNS call list item")
    publication_date = _first_text(
        item.get("fechaPublicacion"),
        item.get("fechaRecepcion"),
        item.get("fechaRegistro"),
    )
    if not publication_date:
        raise ValueError("BDNS call list item is missing a publication or registration date.")
    return BDNSCallMetadata(
        external_id=f"BDNS:{code}",
        official_identifier=f"BDNS:{code}",
        publication_date=publication_date,
        title=title,
        department=_first_text(item.get("nivel3"), item.get("nivel2"), item.get("nivel1")),
        section=_first_text(item.get("nivel1"), item.get("nivel2")),
        document_type="grant_call",
        url_html=build_bdns_call_detail_url(code),
        url_xml=None,
        url_pdf=None,
        raw_metadata={
            "source_family": "grants_registry",
            "resource_type": "grant_call",
            "bdns_code": code,
            "bdns_internal_id": item.get("id"),
            "registration_date": _clean_optional_text(item.get("fechaRecepcion")),
            "source_metadata": item,
        },
    )


def _descriptions(value: object | None) -> list[str]:
    if not isinstance(value, list):
        return []
    descriptions: list[str] = []
    for item in value:
        if isinstance(item, dict):
            description = _clean_optional_text(item.get("descripcion"))
            if description:
                descriptions.append(description)
    return descriptions


def _required_text(value: object | None, context: str) -> str:
    cleaned = _clean_optional_text(value)
    if not cleaned:
        raise ValueError(f"{context} is missing a required value")
    return cleaned


def _first_text(*values: object | None) -> str | None:
    for value in values:
        cleaned = _clean_optional_text(value)
        if cleaned:
            return cleaned
    return None


def _clean_optional_text(value: object | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
