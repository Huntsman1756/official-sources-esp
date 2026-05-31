from __future__ import annotations

import json
from pathlib import Path

import pytest

from official_sources.citation.builder import build_citation
from official_sources.integrity.hashing import sha256_bytes
from official_sources.sources.bdns.client import (
    build_bdns_call_detail_url,
    build_bdns_catalog_url,
    build_bdns_concessions_search_url,
    build_bdns_latest_url,
    build_bdns_search_url,
    parse_bdns_date_filter,
    validate_bdns_catalog_name,
)
from official_sources.sources.bdns.ingestion import (
    ingest_bdns_call,
    ingest_bdns_catalog,
    ingest_bdns_concessions,
    ingest_bdns_latest,
    preview_bdns_catalog,
    preview_bdns_concessions,
    search_bdns_calls,
)
from official_sources.sources.bdns.parser import (
    parse_bdns_call_detail,
    parse_bdns_call_page,
    parse_bdns_catalog,
    parse_bdns_concession_page,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _fixture_bytes(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


def _payload(value: dict) -> bytes:
    return json.dumps(value).encode("utf-8")


def test_bdns_source_record_creation(repository):
    source = repository.ensure_official_source_bdns()

    assert source["code"] == "BDNS"
    assert source["name"] == "Base de Datos Nacional de Subvenciones"
    assert source["jurisdiction"] == "state"
    assert source["region_code"] == "ES"
    assert source["access_type"] == "official_api"
    assert source["reliability_level"] == "canonical"


def test_bdns_date_filter_accepts_spanish_dates_only():
    assert parse_bdns_date_filter("20/05/2026") == "20/05/2026"

    with pytest.raises(ValueError):
        parse_bdns_date_filter("2026-05-20")


def test_bdns_concessions_search_url_requires_scoped_call_filter():
    assert build_bdns_concessions_search_url(num_conv="877699", page_size=2) == (
        "https://www.infosubvenciones.es/bdnstrans/api/concesiones/busqueda"
        "?page=1&pageSize=2&vpd=GE&numeroConvocatoria=877699"
    )

    with pytest.raises(ValueError):
        build_bdns_concessions_search_url(num_conv="", page_size=2)


def test_bdns_concession_parsing_redacts_beneficiary_by_default():
    payload = _payload(
        {
            "content": [
                {
                    "id": 152503815,
                    "codConcesion": "SB152503815",
                    "numeroConvocatoria": "877699",
                    "idConvocatoria": 1079260,
                    "fechaConcesion": "2026-05-29",
                    "fechaAlta": "2026-05-31",
                    "importe": 17243.86,
                    "ayudaEquivalente": 17243.86,
                    "instrumento": "SUBVENCION",
                    "nivel1": "AUTONOMICA",
                    "nivel2": "ILLES BALEARS",
                    "nivel3": "DIRECCION GENERAL",
                    "convocatoria": "Convocatoria de prueba",
                    "urlBR": "https://example.test/bases",
                    "beneficiario": "Persona Fisica",
                    "idPersona": 22127337,
                }
            ],
            "totalElements": 1,
            "totalPages": 1,
            "number": 0,
            "last": True,
        }
    )

    page = parse_bdns_concession_page(
        payload,
        source_url=build_bdns_concessions_search_url(num_conv="877699", page_size=2),
    )

    assert page.status == "success"
    assert page.source_snapshot_hash == sha256_bytes(payload)
    assert page.concessions[0].external_id == "BDNS:concesion:SB152503815"
    assert page.concessions[0].call_identifier == "BDNS:877699"
    assert page.concessions[0].raw_metadata["beneficiary_name"] is None
    assert page.concessions[0].raw_metadata["beneficiary_person_id"] is None
    assert page.concessions[0].raw_metadata["source_metadata"]["beneficiario"] == "<redacted>"


def test_bdns_concession_parsing_can_include_beneficiary_fields_explicitly():
    payload = _payload(
        {
            "content": [
                {
                    "id": 152503815,
                    "codConcesion": "SB152503815",
                    "numeroConvocatoria": "877699",
                    "fechaConcesion": "2026-05-29",
                    "beneficiario": "Entidad Beneficiaria",
                    "idPersona": 22127337,
                }
            ]
        }
    )

    page = parse_bdns_concession_page(
        payload,
        source_url=build_bdns_concessions_search_url(num_conv="877699", page_size=2),
        include_beneficiary_fields=True,
    )

    assert page.concessions[0].raw_metadata["beneficiary_name"] == "Entidad Beneficiaria"
    assert page.concessions[0].raw_metadata["beneficiary_person_id"] == 22127337


def test_bdns_concessions_preview_does_not_store_entries():
    payload = _payload(
        {
            "content": [
                {
                    "id": 152503815,
                    "codConcesion": "SB152503815",
                    "numeroConvocatoria": "877699",
                    "fechaConcesion": "2026-05-29",
                    "beneficiario": "Persona Fisica",
                    "idPersona": 22127337,
                }
            ]
        }
    )

    result = preview_bdns_concessions(
        num_conv="877699",
        page_size=1,
        concessions_payload=payload,
    )

    assert result["status"] == "success"
    assert result["documents_fetched"] == 0
    assert result["entry_count"] == 1
    assert result["sample_identifiers"] == ["BDNS:concesion:SB152503815"]


def test_bdns_concessions_ingestion_stores_sanitized_entries_by_default(repository):
    payload = _payload(
        {
            "content": [
                {
                    "id": 152503815,
                    "codConcesion": "SB152503815",
                    "numeroConvocatoria": "877699",
                    "fechaConcesion": "2026-05-29",
                    "fechaAlta": "2026-05-31",
                    "importe": 17243.86,
                    "ayudaEquivalente": 17243.86,
                    "beneficiario": "Persona Fisica",
                    "idPersona": 22127337,
                }
            ],
            "last": True,
        }
    )

    run = ingest_bdns_concessions(
        repository,
        num_conv="877699",
        page_size=1,
        max_pages=1,
        fetcher=lambda **_kwargs: payload,
    )

    entry = repository.get_bdns_concession_entry("SB152503815")

    assert run["status"] == "success"
    assert run["documents_fetched"] == 1
    assert run["documents_new"] == 1
    assert entry["external_id"] == "BDNS:concesion:SB152503815"
    assert entry["call_identifier"] == "BDNS:877699"
    assert entry["beneficiary_name"] is None
    assert entry["beneficiary_person_id"] is None


def test_bdns_catalog_urls_are_limited_to_safe_metadata_endpoints():
    assert validate_bdns_catalog_name("organos") == "organos"
    assert build_bdns_catalog_url("sectores") == (
        "https://www.infosubvenciones.es/bdnstrans/api/sectores"
    )
    assert build_bdns_catalog_url("finalidades") == (
        "https://www.infosubvenciones.es/bdnstrans/api/finalidades?vpd=GE"
    )
    assert build_bdns_catalog_url("organos", id_admon="L") == (
        "https://www.infosubvenciones.es/bdnstrans/api/organos?vpd=GE&idAdmon=L"
    )

    with pytest.raises(ValueError):
        validate_bdns_catalog_name("concesiones")

    with pytest.raises(ValueError):
        build_bdns_catalog_url("organos")


def test_bdns_catalog_parsing_preserves_identifier_and_hash():
    payload = _payload(
        [
            {
                "codigo": "EA0042931",
                "descripcion": "Direccion General de Politica Energetica y Minas",
                "nivel": 3,
            }
        ]
    )

    catalog = parse_bdns_catalog(
        payload,
        catalog_name="organos",
        source_url=build_bdns_catalog_url("organos", id_admon="C"),
    )

    assert catalog.status == "success"
    assert catalog.catalog_name == "organos"
    assert catalog.source_snapshot_hash == sha256_bytes(payload)
    assert catalog.entry_count == 1
    assert catalog.entries[0].external_id == "BDNS:catalog:organos:EA0042931"
    assert catalog.entries[0].name == "Direccion General de Politica Energetica y Minas"
    assert catalog.entries[0].raw_metadata["nivel"] == 3


def test_bdns_catalog_preview_does_not_store_documents():
    payload = _payload(
        {
            "content": [
                {
                    "id": 11,
                    "descripcion": "Comercio",
                }
            ]
        }
    )

    result = preview_bdns_catalog(
        "sectores",
        catalog_payload=payload,
    )

    assert result["status"] == "success"
    assert result["bdns_result"] == "success"
    assert result["catalog_name"] == "sectores"
    assert result["entry_count"] == 1
    assert result["sample_identifiers"] == ["BDNS:catalog:sectores:11"]
    assert result["documents_fetched"] == 0


def test_bdns_catalog_ingestion_stores_reusable_entries(repository):
    payload = _payload(
        [
            {
                "codigo": "S01",
                "descripcion": "Agricultura",
            },
            {
                "codigo": "S02",
                "descripcion": "Industria",
            },
        ]
    )

    run = ingest_bdns_catalog(
        repository,
        "sectores",
        catalog_payload=payload,
    )

    first_entry = repository.get_bdns_catalog_entry("sectores", "S01")
    entries = repository.list_bdns_catalog_entries(catalog_name="sectores")

    assert run["status"] == "success"
    assert run["bdns_result"] == "success"
    assert run["documents_fetched"] == 2
    assert run["documents_new"] == 2
    assert run["documents_updated"] == 0
    assert run["catalog_name"] == "sectores"
    assert run["entry_count"] == 2
    assert run["source_snapshot_hash"] == sha256_bytes(payload)
    assert run["sample_identifiers"] == [
        "BDNS:catalog:sectores:S01",
        "BDNS:catalog:sectores:S02",
    ]
    assert len(entries) == 2
    assert first_entry["external_id"] == "BDNS:catalog:sectores:S01"
    assert first_entry["name"] == "Agricultura"
    assert first_entry["source_snapshot_hash"] == sha256_bytes(payload)
    assert first_entry["content_changed_at"] is None


def test_bdns_catalog_ingestion_tracks_changed_entries(repository):
    original_payload = _payload([{"codigo": "S01", "descripcion": "Agricultura"}])
    changed_payload = _payload([{"codigo": "S01", "descripcion": "Sector agrario"}])

    ingest_bdns_catalog(repository, "sectores", catalog_payload=original_payload)
    run = ingest_bdns_catalog(repository, "sectores", catalog_payload=changed_payload)

    entry = repository.get_bdns_catalog_entry("sectores", "S01")

    assert run["status"] == "success"
    assert run["documents_fetched"] == 1
    assert run["documents_new"] == 0
    assert run["documents_updated"] == 1
    assert entry["name"] == "Sector agrario"
    assert entry["previous_hash"] is not None
    assert entry["content_changed_at"] is not None


def test_bdns_organos_catalog_ingestion_scopes_codes_by_id_admon(repository):
    payload = _payload([{"codigo": "12", "descripcion": "Organo estatal"}])

    run = ingest_bdns_catalog(
        repository,
        "organos",
        catalog_payload=payload,
        id_admon="C",
    )

    entry = repository.get_bdns_catalog_entry("organos", "C:12")

    assert run["status"] == "success"
    assert run["sample_identifiers"] == ["BDNS:catalog:organos:C:12"]
    assert entry["external_id"] == "BDNS:catalog:organos:C:12"
    assert entry["name"] == "Organo estatal"


def test_latest_calls_parsing_preserves_identifier_and_hash():
    payload = _fixture_bytes("bdns_latest_convocatorias.json")

    page = parse_bdns_call_page(payload, source_url=build_bdns_latest_url(page_size=1))

    assert page.status == "success"
    assert page.source_snapshot_hash == sha256_bytes(payload)
    assert page.total_elements == 2
    assert len(page.calls) == 1
    assert page.calls[0].external_id == "BDNS:907362"
    assert page.calls[0].official_identifier == "BDNS:907362"
    assert page.calls[0].publication_date == "2026-05-21"
    assert page.calls[0].title == "Convocatoria Pyme Innova 2026 - Camara Tortosa"
    assert page.calls[0].department == "CAMARA DE COMERCIO DE TORTOSA"
    assert page.calls[0].url_html == build_bdns_call_detail_url("907362")
    assert page.calls[0].raw_metadata["resource_type"] == "grant_call"


def test_search_result_parsing_handles_content_shape():
    payload = _fixture_bytes("bdns_search_convocatorias.json")

    page = parse_bdns_call_page(
        payload,
        source_url=build_bdns_search_url(
            date_from="20/05/2026",
            date_to="20/05/2026",
            page_size=10,
        ),
    )

    assert page.status == "success"
    assert page.calls[0].external_id == "BDNS:907042"
    assert page.calls[0].raw_metadata["bdns_internal_id"] == 1108603
    assert page.calls[0].raw_metadata["source_family"] == "grants_registry"


def test_list_parsing_accepts_items_shape_and_codigo_bdns_variant():
    payload = _payload(
        {
            "items": [
                {
                    "codigoBdns": "907777",
                    "descripcion": "Convocatoria con codigoBdns",
                    "fechaRecepcion": "2026-05-19",
                    "nivel2": "ORGANO CONVOCANTE",
                }
            ],
            "totalElements": 1,
            "totalPages": 1,
            "number": 0,
            "last": True,
        }
    )

    page = parse_bdns_call_page(payload, source_url=build_bdns_search_url(page_size=10))

    assert page.status == "success"
    assert page.calls[0].external_id == "BDNS:907777"
    assert page.calls[0].publication_date == "2026-05-19"
    assert page.calls[0].department == "ORGANO CONVOCANTE"


def test_list_parsing_accepts_id_when_num_conv_aliases_are_absent():
    payload = _payload(
        {
            "content": [
                {
                    "id": 907778,
                    "descripcion": "Convocatoria con id como identificador",
                    "fechaRegistro": "2026-05-18",
                }
            ]
        }
    )

    page = parse_bdns_call_page(payload, source_url=build_bdns_latest_url(page_size=1))

    assert page.status == "success"
    assert page.calls[0].external_id == "BDNS:907778"
    assert page.calls[0].publication_date == "2026-05-18"


def test_detail_by_num_conv_parsing_preserves_fields_and_urls():
    payload = _fixture_bytes("bdns_convocatoria_detail.json")

    detail = parse_bdns_call_detail(payload, num_conv="907042")

    assert detail.external_id == "BDNS:907042"
    assert detail.official_identifier == "BDNS:907042"
    assert detail.publication_date == "2026-05-20"
    assert detail.department == "DEPARTAMENTO DE TURISMO, COMERCIO Y CONSUMO"
    assert detail.document_type == "Concurrencia competitiva - canonica"
    assert detail.url_html == build_bdns_call_detail_url("907042")
    assert detail.raw_metadata["budget"] == 934000
    assert detail.raw_metadata["application_start_date"] == "2026-05-21"
    assert detail.raw_metadata["application_end_date"] == "2026-06-30"
    assert detail.raw_metadata["application_url"] == (
        "https://www.euskadi.eus/ayuda_subvencion/2026/ctp-2026/web01-tramite/es/"
    )
    assert detail.raw_metadata["base_regulation_url"] == "https://www.euskadi.eus/bases-reguladoras"


def test_detail_parsing_structures_document_metadata_without_downloading():
    payload = _payload(
        {
            "codigoBDNS": "907781",
            "descripcion": "Convocatoria con documentos",
            "fechaPublicacion": "2026-05-18",
            "documentos": [
                {
                    "idDocumento": 123,
                    "descripcion": "Bases reguladoras",
                    "nombreFichero": "bases.pdf",
                }
            ],
            "anuncios": [
                {
                    "id": 456,
                    "descripcion": "Extracto publicado",
                    "url": "https://www.boe.es/diario_boe/txt.php?id=BOE-B-2026-1",
                }
            ],
        }
    )

    detail = parse_bdns_call_detail(payload, num_conv="907781")

    assert detail.raw_metadata["document_metadata"] == [
        {
            "document_id": "123",
            "title": "Bases reguladoras",
            "file_name": "bases.pdf",
            "official_url": (
                "https://www.infosubvenciones.es/bdnstrans/api/convocatorias/documentos"
                "?idDocumento=123"
            ),
            "source_type": "documentos",
        }
    ]
    assert detail.raw_metadata["announcement_metadata"] == [
        {
            "announcement_id": "456",
            "title": "Extracto publicado",
            "official_url": "https://www.boe.es/diario_boe/txt.php?id=BOE-B-2026-1",
            "source_type": "anuncios",
        }
    ]


@pytest.mark.parametrize(
    ("amount_field", "amount_value"),
    [
        ("presupuestoTotal", 1234),
        ("presupuesto", "1.234,56"),
        ("importeTotal", 9876.5),
        ("importe", "5000"),
    ],
)
def test_detail_parsing_accepts_amount_variants(amount_field, amount_value):
    detail_payload = {
        "codigo": "907779",
        "descripcion": "Convocatoria con importe variable",
        "fechaRegistro": "2026-05-17",
        amount_field: amount_value,
    }

    detail = parse_bdns_call_detail(_payload(detail_payload), num_conv="907779")

    assert detail.raw_metadata["budget"] == amount_value
    assert detail.department is None
    assert detail.section is None
    assert detail.document_type is None


def test_empty_results_parse_as_no_results():
    page = parse_bdns_call_page(
        _fixture_bytes("bdns_empty_results.json"),
        source_url=build_bdns_search_url(page_size=10),
    )

    assert page.status == "no_results"
    assert page.calls == []


def test_missing_num_conv_detail_records_failed_ingestion(repository):
    run = ingest_bdns_call(
        repository,
        num_conv="999999",
        detail_payload=_fixture_bytes("bdns_not_found.json"),
    )

    assert run["status"] == "failed"
    assert run["documents_fetched"] == 0
    assert repository.get_document_by_external_id("BDNS:999999") is None


def test_detail_without_num_conv_is_classified_as_not_found(repository):
    run = ingest_bdns_call(
        repository,
        num_conv="999999",
        detail_payload=_fixture_bytes("bdns_not_found.json"),
    )

    assert run["bdns_result"] == "not_found"


def test_malformed_detail_payload_is_classified_as_failed(repository):
    run = ingest_bdns_call(
        repository,
        num_conv="999998",
        detail_payload=_payload({"codigoBDNS": "999998", "fechaPublicacion": "2026-05-16"}),
    )

    assert run["status"] == "failed"
    assert run["bdns_result"] == "failed"


def test_bdns_latest_ingestion_stores_calls_without_candidates_or_artifacts(repository):
    payload = _fixture_bytes("bdns_latest_convocatorias.json")

    run = ingest_bdns_latest(repository, limit=1, latest_payload=payload)

    document = repository.get_document_by_external_id("BDNS:907362")
    raw_file_count = repository.connection.execute(
        "SELECT COUNT(*) AS count FROM document_files WHERE file_type = 'raw_api_response'"
    ).fetchone()["count"]
    candidate_count = repository.connection.execute(
        "SELECT COUNT(*) AS count FROM source_candidates"
    ).fetchone()["count"]
    attempt_count = repository.connection.execute(
        "SELECT COUNT(*) AS count FROM artifact_download_attempts"
    ).fetchone()["count"]

    assert run["status"] == "success"
    assert run["documents_fetched"] == 1
    assert run["documents_new"] == 1
    assert document["source_code"] == "BDNS"
    assert document["document_type"] == "grant_call"
    assert raw_file_count == 1
    assert candidate_count == 0
    assert attempt_count == 0
    assert run["source_snapshot_hash"] == sha256_bytes(payload)
    assert run["bdns_result"] == "success"
    assert run["page_count"] == 1
    assert run["pagination_limit_reached"] is False
    assert run["sample_identifiers"] == ["BDNS:907362"]


def test_bdns_call_ingestion_supports_citation_generation(repository):
    run = ingest_bdns_call(
        repository,
        num_conv="907042",
        detail_payload=_fixture_bytes("bdns_convocatoria_detail.json"),
    )

    citation = build_citation(repository, "BDNS:907042")

    assert run["status"] == "success"
    assert citation["source_code"] == "BDNS"
    assert citation["external_id"] == "BDNS:907042"
    assert citation["official_url"] == build_bdns_call_detail_url("907042")


def test_bdns_call_ingestion_enriches_catalog_codes_from_local_catalogs(repository):
    ingest_bdns_catalog(
        repository,
        "sectores",
        catalog_payload=_payload(
            [
                {
                    "codigo": "94",
                    "descripcion": "Actividades asociativas normalizadas",
                }
            ]
        ),
    )

    run = ingest_bdns_call(
        repository,
        num_conv="907042",
        detail_payload=_fixture_bytes("bdns_convocatoria_detail.json"),
    )

    document = repository.get_document_by_external_id("BDNS:907042")
    raw_metadata = json.loads(document["raw_metadata_json"])

    assert run["status"] == "success"
    assert raw_metadata["sector_activity"] == ["Actividades asociativas"]
    assert raw_metadata["catalog_enrichment"]["sectores"] == [
        {
            "catalog_name": "sectores",
            "code": "94",
            "name": "Actividades asociativas normalizadas",
            "external_id": "BDNS:catalog:sectores:94",
        }
    ]


def test_bdns_search_ingestion_enriches_catalog_codes_from_local_catalogs(repository):
    ingest_bdns_catalog(
        repository,
        "sectores",
        catalog_payload=_payload([{"codigo": "94", "descripcion": "Actividades asociativas"}]),
    )
    search_payload = _payload(
        {
            "content": [
                {
                    "codigoBDNS": "907780",
                    "descripcion": "Convocatoria con sector",
                    "fechaPublicacion": "2026-05-16",
                    "sectores": [{"codigo": "94", "descripcion": "Sector original"}],
                }
            ],
            "totalElements": 1,
            "totalPages": 1,
            "number": 0,
            "last": True,
        }
    )

    run = search_bdns_calls(
        repository,
        date_from=None,
        date_to=None,
        page_size=1,
        max_pages=1,
        fetcher=lambda **_kwargs: search_payload,
    )

    document = repository.get_document_by_external_id("BDNS:907780")
    raw_metadata = json.loads(document["raw_metadata_json"])

    assert run["status"] == "success"
    assert raw_metadata["catalog_enrichment"]["sectores"][0]["code"] == "94"
    assert raw_metadata["catalog_enrichment"]["sectores"][0]["name"] == "Actividades asociativas"


def test_bdns_search_enforces_pagination_limit(repository):
    with pytest.raises(ValueError):
        search_bdns_calls(
            repository,
            date_from="20/05/2026",
            date_to="20/05/2026",
            page_size=10,
            max_pages=0,
        )

    with pytest.raises(ValueError):
        search_bdns_calls(
            repository,
            date_from="20/05/2026",
            date_to="20/05/2026",
            page_size=10,
            max_pages=11,
        )


def test_bdns_search_stops_at_max_pages_and_reports_limit(repository):
    payload = _payload(
        {
            "content": [
                {
                    "codigoBDNS": "907780",
                    "descripcion": "Pagina uno",
                    "fechaPublicacion": "2026-05-16",
                }
            ],
            "totalElements": 2,
            "totalPages": 2,
            "number": 0,
            "last": False,
        }
    )
    calls = []

    def fetcher(**kwargs):
        calls.append(kwargs["page"])
        return payload

    run = search_bdns_calls(
        repository,
        date_from="20/05/2026",
        date_to="20/05/2026",
        page_size=1,
        max_pages=1,
        fetcher=fetcher,
    )

    candidate_count = repository.connection.execute(
        "SELECT COUNT(*) AS count FROM source_candidates"
    ).fetchone()["count"]
    attempt_count = repository.connection.execute(
        "SELECT COUNT(*) AS count FROM artifact_download_attempts"
    ).fetchone()["count"]

    assert calls == [1]
    assert run["status"] == "success"
    assert run["documents_fetched"] == 1
    assert run["page_count"] == 1
    assert run["pagination_limit_reached"] is True
    assert run["bdns_result"] == "success"
    assert run["sample_identifiers"] == ["BDNS:907780"]
    assert candidate_count == 0
    assert attempt_count == 0


def test_bdns_search_empty_result_reports_no_results(repository):
    run = search_bdns_calls(
        repository,
        date_from="20/05/2026",
        date_to="20/05/2026",
        page_size=10,
        max_pages=2,
        fetcher=lambda **_kwargs: _fixture_bytes("bdns_empty_results.json"),
    )

    assert run["status"] == "success"
    assert run["bdns_result"] == "no_results"
    assert run["documents_fetched"] == 0
    assert run["page_count"] == 1
    assert run["pagination_limit_reached"] is False
    assert run["sample_identifiers"] == []


def test_bdns_mvp_does_not_ingest_concesiones(repository):
    assert not hasattr(repository, "ensure_official_source_bdns_concesiones")
