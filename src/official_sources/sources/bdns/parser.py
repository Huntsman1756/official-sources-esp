from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from official_sources.integrity.hashing import sha256_bytes
from official_sources.sources.bdns.client import (
    BDNS_API_BASE_URL,
    build_bdns_call_detail_url,
    validate_bdns_catalog_name,
    validate_bdns_num_conv,
)

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


@dataclass(frozen=True)
class BDNSCatalogEntry:
    external_id: str
    catalog_name: str
    code: str
    name: str
    raw_metadata: dict[str, Any]


@dataclass(frozen=True)
class BDNSCatalogSnapshot:
    status: str
    catalog_name: str
    source_snapshot_hash: str
    source_url: str
    entries: list[BDNSCatalogEntry]
    entry_count: int


@dataclass(frozen=True)
class BDNSConcessionMetadata:
    external_id: str
    concession_code: str
    call_identifier: str | None
    concession_date: str | None
    amount: float | int | None
    raw_metadata: dict[str, Any]


@dataclass(frozen=True)
class BDNSConcessionPage:
    status: str
    source_snapshot_hash: str
    source_url: str
    concessions: list[BDNSConcessionMetadata]
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
            "document_metadata": _document_metadata(data.get("documentos")),
            "announcement_metadata": _announcement_metadata(data.get("anuncios")),
            "application_url": _clean_optional_text(data.get("sedeElectronica")),
            "base_regulation_url": _clean_optional_text(data.get("urlBasesReguladoras")),
            "detail_api_sha256": raw_hash,
            "source_metadata": data,
        },
    )


def parse_bdns_catalog(
    payload: bytes,
    *,
    catalog_name: str,
    source_url: str,
) -> BDNSCatalogSnapshot:
    catalog_name = validate_bdns_catalog_name(catalog_name)
    raw_hash = sha256_bytes(payload)
    data = json.loads(payload.decode("utf-8-sig"))
    items = _catalog_items(data)
    entries = [_catalog_entry(item, catalog_name=catalog_name) for item in items]
    return BDNSCatalogSnapshot(
        status="success" if entries else NO_RESULTS_STATUS,
        catalog_name=catalog_name,
        source_snapshot_hash=raw_hash,
        source_url=source_url,
        entries=entries,
        entry_count=len(entries),
    )


def parse_bdns_concession_page(
    payload: bytes,
    *,
    source_url: str,
    include_beneficiary_fields: bool = False,
) -> BDNSConcessionPage:
    raw_hash = sha256_bytes(payload)
    decoded = json.loads(payload.decode("utf-8-sig"))
    data = decoded if isinstance(decoded, dict) else {}
    items = _page_items(data)
    if not items:
        return BDNSConcessionPage(
            status=NO_RESULTS_STATUS,
            source_snapshot_hash=raw_hash,
            source_url=source_url,
            concessions=[],
            total_elements=int(data.get("totalElements") or 0),
            total_pages=int(data.get("totalPages") or 0),
            page_number=int(data.get("number") or 0),
            last=bool(data.get("last", True)),
        )
    concessions = [
        _concession_from_item(item, include_beneficiary_fields=include_beneficiary_fields)
        for item in items
    ]
    return BDNSConcessionPage(
        status="success",
        source_snapshot_hash=raw_hash,
        source_url=source_url,
        concessions=concessions,
        total_elements=int(data.get("totalElements") or len(concessions)),
        total_pages=int(data.get("totalPages") or 1),
        page_number=int(data.get("number") or 0),
        last=bool(data.get("last", False)),
    )


def _page_items(data: dict[str, Any]) -> list[dict[str, Any]]:
    raw_items = data.get("content")
    if raw_items is None:
        raw_items = data.get("items")
    if not isinstance(raw_items, list):
        return []
    return [item for item in raw_items if isinstance(item, dict)]


def _catalog_items(data: object) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if not isinstance(data, dict):
        return []
    for key in ("content", "items", "data", "results"):
        raw_items = data.get(key)
        if isinstance(raw_items, list):
            return [item for item in raw_items if isinstance(item, dict)]
    return []


def _catalog_entry(item: dict[str, Any], *, catalog_name: str) -> BDNSCatalogEntry:
    code = _first_text(
        item.get("codigo"),
        item.get("codigoBDNS"),
        item.get("codigoBdns"),
        item.get("id"),
        item.get("clave"),
    )
    if not code:
        raise ValueError(f"BDNS catalog {catalog_name} item is missing a code.")
    name = _required_text(
        _first_text(
            item.get("descripcion"),
            item.get("nombre"),
            item.get("denominacion"),
            item.get("texto"),
        ),
        f"BDNS catalog {catalog_name} item",
    )
    return BDNSCatalogEntry(
        external_id=f"BDNS:catalog:{catalog_name}:{code}",
        catalog_name=catalog_name,
        code=code,
        name=name,
        raw_metadata=item,
    )


def _concession_from_item(
    item: dict[str, Any],
    *,
    include_beneficiary_fields: bool,
) -> BDNSConcessionMetadata:
    code = _first_text(item.get("codConcesion"), item.get("codigoConcesion"), item.get("id"))
    if not code:
        raise ValueError("BDNS concession item is missing codConcesion.")
    call_code = _first_text(
        item.get("numeroConvocatoria"),
        item.get("codigoBDNS"),
        item.get("codigoBdns"),
        item.get("codigo"),
    )
    if call_code:
        validate_bdns_num_conv(call_code)
    beneficiary_name = (
        _clean_optional_text(item.get("beneficiario")) if include_beneficiary_fields else None
    )
    beneficiary_person_id = item.get("idPersona") if include_beneficiary_fields else None
    source_metadata = dict(item)
    if not include_beneficiary_fields:
        if "beneficiario" in source_metadata:
            source_metadata["beneficiario"] = "<redacted>"
        if "idPersona" in source_metadata:
            source_metadata["idPersona"] = None
    return BDNSConcessionMetadata(
        external_id=f"BDNS:concesion:{code}",
        concession_code=code,
        call_identifier=f"BDNS:{call_code}" if call_code else None,
        concession_date=_clean_optional_text(item.get("fechaConcesion")),
        amount=item.get("importe"),
        raw_metadata={
            "source_family": "grants_registry",
            "resource_type": "grant_award",
            "bdns_award_code": code,
            "bdns_award_id": item.get("id"),
            "bdns_call_code": call_code,
            "bdns_call_internal_id": item.get("idConvocatoria"),
            "concession_date": _clean_optional_text(item.get("fechaConcesion")),
            "registration_date": _clean_optional_text(item.get("fechaAlta")),
            "amount": item.get("importe"),
            "aid_equivalent": item.get("ayudaEquivalente"),
            "instrument": _clean_optional_text(item.get("instrumento")),
            "department": _first_text(item.get("nivel3"), item.get("nivel2"), item.get("nivel1")),
            "section": _first_text(item.get("nivel1"), item.get("nivel2")),
            "base_regulation_url": _clean_optional_text(item.get("urlBR")),
            "has_project": item.get("tieneProyecto"),
            "beneficiary_name": beneficiary_name,
            "beneficiary_person_id": beneficiary_person_id,
            "source_metadata": source_metadata,
        },
    )


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


def _document_metadata(value: object | None) -> list[dict[str, str | None]]:
    if not isinstance(value, list):
        return []
    documents: list[dict[str, str | None]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        document_id = _first_text(
            item.get("idDocumento"),
            item.get("id"),
            item.get("codigo"),
        )
        if not document_id:
            continue
        documents.append(
            {
                "document_id": document_id,
                "title": _first_text(
                    item.get("descripcion"),
                    item.get("titulo"),
                    item.get("nombre"),
                ),
                "file_name": _first_text(
                    item.get("nombreFichero"),
                    item.get("nombreArchivo"),
                    item.get("filename"),
                ),
                "official_url": (
                    f"{BDNS_API_BASE_URL}/convocatorias/documentos?idDocumento={document_id}"
                ),
                "source_type": "documentos",
            }
        )
    return documents


def _announcement_metadata(value: object | None) -> list[dict[str, str | None]]:
    if not isinstance(value, list):
        return []
    announcements: list[dict[str, str | None]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        announcement_id = _first_text(
            item.get("idAnuncio"),
            item.get("id"),
            item.get("codigo"),
        )
        title = _first_text(item.get("descripcion"), item.get("titulo"), item.get("nombre"))
        official_url = _first_text(item.get("url"), item.get("urlAnuncio"), item.get("enlace"))
        if not announcement_id and not official_url:
            continue
        announcements.append(
            {
                "announcement_id": announcement_id,
                "title": title,
                "official_url": official_url,
                "source_type": "anuncios",
            }
        )
    return announcements


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
