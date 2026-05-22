from __future__ import annotations

import json
from pathlib import Path

import pytest

from official_sources.citation.builder import build_citation
from official_sources.integrity.hashing import sha256_bytes
from official_sources.sources.bdns.client import (
    build_bdns_call_detail_url,
    build_bdns_latest_url,
    build_bdns_search_url,
    parse_bdns_date_filter,
)
from official_sources.sources.bdns.ingestion import (
    ingest_bdns_call,
    ingest_bdns_latest,
    search_bdns_calls,
)
from official_sources.sources.bdns.parser import (
    parse_bdns_call_detail,
    parse_bdns_call_page,
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
