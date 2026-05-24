from __future__ import annotations

import json
from pathlib import Path

import pytest

from official_sources.citation.builder import build_citation
from official_sources.integrity.hashing import sha256_bytes
from official_sources.sources.borm.client import build_borm_index_xml_url, validate_borm_date
from official_sources.sources.borm.ingestion import ingest_borm_date
from official_sources.sources.borm.parser import (
    parse_borm_date_response,
    parse_borm_document_metadata,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _fixture_bytes(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


def _borm_record_xml(
    *,
    publication_type: str = "BOLETIN",
    announcement_id: str,
    issue_number: str,
    publication_date: str = "2026-05-11",
    title: str = "Resolucion de prueba.",
) -> str:
    return f"""
  <resultado>
    <Publicacion>{publication_type}</Publicacion>
    <ID_Anuncio>{announcement_id}</ID_Anuncio>
    <ID_Objeto_Digital_Anuncio>84{announcement_id}</ID_Objeto_Digital_Anuncio>
    <Num_Publicacion>{issue_number}</Num_Publicacion>
    <Fec_Publicacion>{publication_date} 00:00:00</Fec_Publicacion>
    <Sumario>{title}</Sumario>
    <Administracion>Comunidad Autonoma</Administracion>
    <Seccion>I. Comunidad Autonoma</Seccion>
    <Apartado>2. Autoridades y Personal</Apartado>
    <Anunciante>Consejeria de Prueba</Anunciante>
    <Num_Disposicion>0</Num_Disposicion>
    <Ejercicio_Publicacion>2026</Ejercicio_Publicacion>
    <Rango>RESOLUCION</Rango>
    <Fec_Disposicion>2026-05-10 00:00:00</Fec_Disposicion>
    <Ejercicio_Disposicion>2026</Ejercicio_Disposicion>
    <Categoria />
    <NPE>A-110526-{announcement_id}</NPE>
    <URL_HTML>https://www.borm.es/#/home/anuncio/11-05-2026/{announcement_id}</URL_HTML>
    <URL_PDF>https://www.borm.es/services/anuncio/84{announcement_id}/pdf</URL_PDF>
    <NUM_PAGINAS>1</NUM_PAGINAS>
  </resultado>
"""


def _borm_payload(*records: str) -> bytes:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n<resultados>\n'
        + "\n".join(records)
        + "\n</resultados>"
    ).encode()


@pytest.mark.parametrize("value", ["2026-05-20", "1980-01-01"])
def test_borm_date_validation_accepts_iso_dates(value):
    assert validate_borm_date(value).isoformat() == value


@pytest.mark.parametrize("value", ["20260520", "2026-02-30", "not-a-date"])
def test_borm_date_validation_rejects_invalid_dates(value):
    with pytest.raises(ValueError):
        validate_borm_date(value)


def test_borm_source_record_creation(repository):
    source = repository.ensure_official_source_borm()

    assert source["code"] == "BORM"
    assert source["name"] == "Boletin Oficial de la Region de Murcia"
    assert source["jurisdiction"] == "autonomous"
    assert source["region_code"] == "ES-MC"
    assert source["access_type"] == "official_xml"
    assert source["reliability_level"] == "canonical"


def test_date_response_parses_documents_and_preserves_urls():
    payload = _fixture_bytes("borm_date_with_documents.xml")

    issue = parse_borm_date_response(payload, target_date="2026-05-20")

    assert issue.status == "success"
    assert issue.issue_identifier == "114/2026"
    assert issue.raw_payload_sha256 == sha256_bytes(payload)
    assert len(issue.documents) == 2
    assert issue.documents[0].external_id == "BORM:A-200526-2260"
    assert issue.documents[0].official_identifier == "A-200526-2260"
    assert issue.documents[0].publication_date == "2026-05-20"
    assert issue.documents[0].department == "Consejeria de Salud - Servicio Murciano de Salud"
    assert issue.documents[0].section == "I. Comunidad Autonoma"
    assert issue.documents[0].document_type == "RESOLUCION"
    assert issue.documents[0].url_html == "https://www.borm.es/#/home/anuncio/20-05-2026/2260"
    assert issue.documents[0].url_xml is None
    assert issue.documents[0].url_pdf == "https://www.borm.es/services/anuncio/842942/pdf"
    assert issue.documents[0].raw_metadata["issue_identifier"] == "114/2026"
    assert issue.documents[0].raw_metadata["announcement_id"] == "2260"
    assert issue.documents[0].raw_metadata["digital_object_id"] == "842942"


def test_date_response_records_no_publication():
    payload = _fixture_bytes("borm_date_no_publication.xml")

    issue = parse_borm_date_response(payload, target_date="2026-05-17")

    assert issue.status == "no_publication"
    assert issue.issue_identifier is None
    assert issue.documents == []
    assert issue.raw_payload_sha256 == sha256_bytes(payload)


def test_date_response_accepts_same_date_supplement_issue():
    payload = _borm_payload(
        _borm_record_xml(announcement_id="2052", issue_number="106"),
        _borm_record_xml(
            publication_type="SUPLEMENTO",
            announcement_id="2076",
            issue_number="2",
            title="Decreto por el que se declara un dia de luto oficial.",
        ),
    )

    issue = parse_borm_date_response(payload, target_date="2026-05-11")

    assert issue.status == "success"
    assert issue.issue_identifier == "106/2026,2/2026"
    assert issue.issue_identifiers == ["106/2026", "2/2026"]
    assert len(issue.documents) == 2
    assert issue.documents[0].raw_metadata["publication_type"] == "BOLETIN"
    assert issue.documents[0].raw_metadata["issue_identifier"] == "106/2026"
    assert issue.documents[1].raw_metadata["publication_type"] == "SUPLEMENTO"
    assert issue.documents[1].raw_metadata["issue_identifier"] == "2/2026"


def test_date_response_rejects_mixed_boletin_issue_identifiers():
    payload = _borm_payload(
        _borm_record_xml(announcement_id="2052", issue_number="106"),
        _borm_record_xml(announcement_id="2076", issue_number="2"),
    )

    with pytest.raises(ValueError, match="mixed issue identifiers"):
        parse_borm_date_response(payload, target_date="2026-05-11")


def test_date_response_filters_wrong_date_current_index_records():
    payload = _borm_payload(
        _borm_record_xml(announcement_id="2052", issue_number="106"),
        _borm_record_xml(
            announcement_id="9999",
            issue_number="999",
            publication_date="2026-05-12",
        ),
    )

    issue = parse_borm_date_response(payload, target_date="2026-05-11")

    assert issue.status == "success"
    assert issue.issue_identifier == "106/2026"
    assert [document.official_identifier for document in issue.documents] == ["A-110526-2052"]


def test_document_metadata_normalizes_identifier_and_citation_fields():
    payload = _fixture_bytes("borm_document_metadata.xml")

    metadata = parse_borm_document_metadata(payload)

    assert metadata.external_id == "BORM:A-200526-2260"
    assert metadata.official_identifier == "A-200526-2260"
    assert metadata.publication_date == "2026-05-20"
    assert metadata.title.startswith("Resolucion de la Directora Gerente")
    assert metadata.department == "Consejeria de Salud - Servicio Murciano de Salud"
    assert metadata.section == "I. Comunidad Autonoma"
    assert metadata.document_type == "RESOLUCION"
    assert metadata.raw_metadata["metadata_sha256"] == sha256_bytes(payload)


def test_raw_hash_is_computed_before_parsing():
    payload = _fixture_bytes("borm_date_with_documents.xml")

    parsed = parse_borm_date_response(payload, target_date="2026-05-20")
    reparsed = parse_borm_date_response(payload + b"\n", target_date="2026-05-20")

    assert parsed.raw_payload_sha256 != reparsed.raw_payload_sha256


def test_borm_ingestion_stores_documents_without_artifacts_or_candidates(repository):
    payload = _fixture_bytes("borm_date_with_documents.xml")

    run = ingest_borm_date(repository, target_date="2026-05-20", date_payload=payload)

    document = repository.get_document_by_external_id("BORM:A-200526-2260")
    raw_file_count = repository.connection.execute(
        "SELECT COUNT(*) AS count FROM document_files WHERE file_type = 'raw_api_response'"
    ).fetchone()["count"]
    pdf_file_count = repository.connection.execute(
        "SELECT COUNT(*) AS count FROM document_files WHERE file_type = 'pdf'"
    ).fetchone()["count"]
    candidate_count = repository.connection.execute(
        "SELECT COUNT(*) AS count FROM source_candidates"
    ).fetchone()["count"]
    attempt_count = repository.connection.execute(
        "SELECT COUNT(*) AS count FROM artifact_download_attempts"
    ).fetchone()["count"]

    assert run["status"] == "success"
    assert run["issue_identifier"] == "114/2026"
    assert run["documents_fetched"] == 2
    assert run["documents_new"] == 2
    assert document["source_code"] == "BORM"
    assert document["url_html"] == "https://www.borm.es/#/home/anuncio/20-05-2026/2260"
    assert document["url_pdf"] == "https://www.borm.es/services/anuncio/842942/pdf"
    assert raw_file_count == 2
    assert pdf_file_count == 0
    assert candidate_count == 0
    assert attempt_count == 0
    assert run["source_snapshot_hash"] == sha256_bytes(payload)


def test_borm_ingestion_stores_same_date_supplement_without_artifacts_or_candidates(repository):
    payload = _borm_payload(
        _borm_record_xml(announcement_id="2052", issue_number="106"),
        _borm_record_xml(
            publication_type="SUPLEMENTO",
            announcement_id="2076",
            issue_number="2",
            title="Decreto por el que se declara un dia de luto oficial.",
        ),
    )

    run = ingest_borm_date(repository, target_date="2026-05-11", date_payload=payload)

    supplement = repository.get_document_by_external_id("BORM:A-110526-2076")
    candidate_count = repository.connection.execute(
        "SELECT COUNT(*) AS count FROM source_candidates"
    ).fetchone()["count"]
    attempt_count = repository.connection.execute(
        "SELECT COUNT(*) AS count FROM artifact_download_attempts"
    ).fetchone()["count"]
    pdf_file_count = repository.connection.execute(
        "SELECT COUNT(*) AS count FROM document_files WHERE file_type = 'pdf'"
    ).fetchone()["count"]

    assert run["status"] == "success"
    assert run["issue_identifier"] == "106/2026,2/2026"
    assert run["issue_identifiers"] == ["106/2026", "2/2026"]
    assert run["documents_fetched"] == 2
    assert run["documents_new"] == 2
    raw_metadata = json.loads(supplement["raw_metadata_json"])
    assert raw_metadata["publication_type"] == "SUPLEMENTO"
    assert raw_metadata["issue_identifier"] == "2/2026"
    assert candidate_count == 0
    assert attempt_count == 0
    assert pdf_file_count == 0


def test_borm_ingestion_records_no_publication(repository):
    run = ingest_borm_date(
        repository,
        target_date="2026-05-17",
        date_payload=_fixture_bytes("borm_date_no_publication.xml"),
    )

    assert run["status"] == "no_publication"
    assert run["documents_fetched"] == 0
    assert run["issue_identifier"] is None
    assert repository.list_documents_by_date("2026-05-17") == []


def test_borm_ingestion_supports_citation_generation(repository):
    run = ingest_borm_date(
        repository,
        target_date="2026-05-20",
        date_payload=_fixture_bytes("borm_date_with_documents.xml"),
    )

    citation = build_citation(repository, "BORM:A-200526-2260")

    assert run["status"] == "success"
    assert citation["source_code"] == "BORM"
    assert citation["external_id"] == "BORM:A-200526-2260"
    assert citation["official_url"] == "https://www.borm.es/#/home/anuncio/20-05-2026/2260"


def test_borm_index_xml_url_uses_official_open_data_endpoint():
    assert (
        build_borm_index_xml_url()
        == "https://transparencia.carm.es/rest-services/services/restFile/BORMIndice.xml"
    )
