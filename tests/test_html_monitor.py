from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path

import pytest

import official_sources.html_monitor as html_monitor
from official_sources.html_monitor import (
    HTMLMonitorError,
    build_bon_html_url,
    build_bop_a_coruna_html_url,
    build_bop_alicante_html_url,
    build_bop_avila_html_url,
    build_bop_barcelona_html_url,
    build_bop_bizkaia_html_url,
    build_bop_castellon_html_url,
    build_bop_cordoba_html_url,
    build_bop_granada_html_url,
    build_bop_malaga_html_url,
    build_bop_palencia_html_url,
    build_bop_pontevedra_html_url,
    build_bop_sevilla_html_url,
    build_bop_soria_html_url,
    build_bop_valencia_html_url,
    build_bop_valladolid_html_url,
    build_docm_html_url,
    build_html_entry_hash,
    build_html_monitor_output_path,
    monitor_html_source,
    parse_bon_html,
    parse_bop_a_coruna_html,
    parse_bop_albacete_html,
    parse_bop_alicante_response,
    parse_bop_avila_html,
    parse_bop_barcelona_html,
    parse_bop_bizkaia_detail_html,
    parse_bop_castellon_html,
    parse_bop_cordoba_html,
    parse_bop_malaga_html,
    parse_bop_palencia_html,
    parse_bop_pontevedra_html,
    parse_bop_sevilla_html,
    parse_bop_soria_html,
    parse_bop_valencia_html,
    parse_bop_valladolid_html,
    parse_docm_html,
    select_html_access_method,
)
from official_sources.source_coverage import list_monitorable_sources
from official_sources.source_registry import get_source, load_source_registry

FIXTURES = Path(__file__).parent / "fixtures"


def _fixture_bytes(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


def test_bop_a_coruna_html_access_method_exists_in_registry():
    source = get_source("BOP_A_CORUNA")
    method = select_html_access_method(source)

    assert source["operational_status"] == "monitor_validated"
    assert source["monitor_support"] == "available"
    assert method["type"] == "html"
    assert method["status"] == "validated"
    assert method["url"] == (
        "https://bop.dacoruna.gal/bopportal/cambioBoletin.do?fechaInput={date_ddmmyyyy}"
    )
    assert source["candidate_creation_allowed"] is False
    assert source["evidence_grade_allowed"] is False


def test_selected_provincial_html_access_methods_exist_in_registry():
    for source_code in (
        "BOP_ALBACETE",
        "BOP_ALICANTE",
        "BOP_AVILA",
        "BOP_BARCELONA",
        "BON",
        "BOP_BIZKAIA",
        "BOP_CASTELLON",
        "BOP_CORDOBA",
        "BOP_GRANADA",
        "BOP_MALAGA",
        "BOP_PALENCIA",
        "BOP_PONTEVEDRA",
        "BOP_SEVILLA",
        "BOP_SORIA",
        "BOP_VALENCIA",
        "BOP_VALLADOLID",
        "DOCM",
    ):
        source = get_source(source_code)
        method = select_html_access_method(source)

        assert source["operational_status"] == "monitor_validated"
        assert source["monitor_support"] == "available"
        assert method["type"] == "html"
        assert method["status"] == "validated"
        assert source["candidate_creation_allowed"] is False
        assert source["evidence_grade_allowed"] is False


def test_build_bop_a_coruna_html_url_is_one_date_request():
    assert (
        build_bop_a_coruna_html_url(
            "https://bop.dacoruna.gal/bopportal/cambioBoletin.do?fechaInput={date_ddmmyyyy}",
            target_date="2026-05-25",
        )
        == "https://bop.dacoruna.gal/bopportal/cambioBoletin.do?fechaInput=25%2F05%2F2026"
    )


def test_build_bop_alicante_html_url_is_one_date_request():
    url = build_bop_alicante_html_url(
        "https://sede.diputacionalicante.es/wp-content/themes/"
        "Desarrollo-Diputacion/webservices/wseConsultaAjax.php",
        target_date="2026-05-25",
    )

    assert "nemo=BOP_CON" in url
    assert "usuario=-" in url
    assert "%3CfechaPub%3E25%2F05%2F2026%3C%2FfechaPub%3E" in url


def test_build_bop_avila_html_url_is_one_date_request():
    assert (
        build_bop_avila_html_url(
            "https://www.diputacionavila.es/boletin-oficial/{yyyy}/{dd_mm_yyyy}.html",
            target_date="2026-05-29",
        )
        == "https://www.diputacionavila.es/boletin-oficial/2026/29-05-2026.html"
    )


def test_build_bop_barcelona_html_url_is_one_date_request():
    assert (
        build_bop_barcelona_html_url(
            "https://bop.diba.cat/butlleti-del-dia",
            target_date="2026-05-25",
        )
        == "https://bop.diba.cat/butlleti-del-dia"
    )


def test_build_bon_html_url_is_one_month_index_request():
    url = build_bon_html_url(
        "https://bon.navarra.es/es/indice-boletines",
        target_date="2026-05-29",
    )

    assert url.startswith("https://bon.navarra.es/es/indice-boletines?")
    assert "BoletinSelectorMesPortlet_anyo=2026" in url
    assert "BoletinSelectorMesPortlet_mes=5" in url


def test_build_bop_bizkaia_html_url_is_one_landing_request():
    assert (
        build_bop_bizkaia_html_url(
            "https://www.bizkaia.eus/es/bob",
            target_date="2026-05-25",
        )
        == "https://www.bizkaia.eus/es/bob"
    )


def test_build_bop_castellon_html_url_is_one_landing_request():
    assert (
        build_bop_castellon_html_url(
            "https://bop.dipcas.es/PortalBOP/",
            target_date="2026-05-25",
        )
        == "https://bop.dipcas.es/PortalBOP/"
    )


def test_build_bop_malaga_html_url_is_one_date_request():
    assert (
        build_bop_malaga_html_url(
            "https://www.bopmalaga.es/",
            target_date="2026-05-25",
        )
        == "https://www.bopmalaga.es/"
    )


def test_build_bop_cordoba_html_url_is_one_date_request():
    assert (
        build_bop_cordoba_html_url(
            "https://bop.dipucordoba.es/dia/{dd_mm_yyyy}",
            target_date="2026-05-28",
        )
        == "https://bop.dipucordoba.es/dia/28-05-2026"
    )


def test_build_bop_granada_html_url_is_one_date_request():
    assert (
        build_bop_granada_html_url(
            "https://bop.dipgra.es/publica/consulta-de-bops/buscador/BOP-{dd_mm_yyyy}/",
            target_date="2026-05-29",
        )
        == "https://bop.dipgra.es/publica/consulta-de-bops/buscador/BOP-29-05-2026/"
    )


def test_build_bop_pontevedra_html_url_is_one_date_request():
    assert (
        build_bop_pontevedra_html_url(
            "https://boppo.depo.gal/detalle/-/boppo/{yyyy}/{mm}/{dd}",
            target_date="2026-05-29",
        )
        == "https://boppo.depo.gal/detalle/-/boppo/2026/05/29"
    )


def test_build_bop_palencia_html_url_is_one_date_request():
    assert (
        build_bop_palencia_html_url(
            "https://www.diputaciondepalencia.es/servicios/boletin-oficial-provincia",
            target_date="2026-05-29",
        )
        == "https://www.diputaciondepalencia.es/servicios/boletin-oficial-provincia"
    )


def test_build_bop_sevilla_html_url_is_one_landing_request():
    assert (
        build_bop_sevilla_html_url(
            "https://bopsevilla.dipusevilla.es/publica/consulta-de-bops/",
            target_date="2026-05-25",
        )
        == "https://bopsevilla.dipusevilla.es/publica/consulta-de-bops/"
    )


def test_build_bop_soria_html_url_is_one_date_request():
    assert (
        build_bop_soria_html_url(
            "https://bop.dipsoria.es/index.php/mod.boloficial/mem.listadodia/fecha.{dd_mm_yyyy}",
            target_date="2026-05-29",
        )
        == "https://bop.dipsoria.es/index.php/mod.boloficial/mem.listadodia/fecha.29-05-2026"
    )


def test_build_bop_valencia_html_url_is_one_landing_request():
    assert (
        build_bop_valencia_html_url(
            "https://bop.dival.es/bop/drvisapi.dll",
            target_date="2026-05-25",
        )
        == "https://bop.dival.es/bop/drvisapi.dll"
    )


def test_build_bop_valladolid_html_url_is_one_date_request():
    assert build_bop_valladolid_html_url(
        "https://bop.sede.diputaciondevalladolid.es/ultimobop?"
        "p_p_id=BOPVisualizaBoletin_WAR_BOPVisualizaBoletin&"
        "p_p_lifecycle=0&p_p_state=normal&p_p_mode=view&"
        "p_p_col_id=column-1&p_p_col_count=3&"
        "_BOPVisualizaBoletin_WAR_BOPVisualizaBoletin_fecha={date}",
        target_date="2026-05-29",
    ) == (
        "https://bop.sede.diputaciondevalladolid.es/ultimobop?"
        "p_p_id=BOPVisualizaBoletin_WAR_BOPVisualizaBoletin&"
        "p_p_lifecycle=0&p_p_state=normal&p_p_mode=view&"
        "p_p_col_id=column-1&p_p_col_count=3&"
        "_BOPVisualizaBoletin_WAR_BOPVisualizaBoletin_fecha=2026-05-29"
    )


def test_build_docm_html_url_is_one_date_request():
    assert (
        build_docm_html_url(
            "https://docm.jccm.es/docm/cambiarBoletin.do?fecha={yyyymmdd}",
            target_date="2026-05-29",
        )
        == "https://docm.jccm.es/docm/cambiarBoletin.do?fecha=20260529"
    )


def test_parse_bop_a_coruna_fixture_emits_metadata_only_records():
    raw = _fixture_bytes("bop_a_coruna_latest.html")
    page_url = "https://bop.dacoruna.gal/bopportal/cambioBoletin.do?fechaInput=25%2F05%2F2026"

    result = parse_bop_a_coruna_html(
        raw,
        source_code="BOP_A_CORUNA",
        page_url=page_url,
        published_at="2026-05-25",
        discovered_at="2026-05-25T00:00:00Z",
        monitor_run_id="run-1",
    )

    assert result.raw_page_hash == hashlib.sha256(raw).hexdigest()
    assert len(result.records) == 1
    record = result.records[0]
    assert record["source_code"] == "BOP_A_CORUNA"
    assert record["page_url"] == page_url
    assert record["page_format"] == "html"
    assert record["document_id"] == "2026/3193"
    assert record["entry_id"] == "717669"
    assert record["title"] == "Resolucion de perdida del derecho al accesit del premio provincial"
    assert record["published_at"] == "2026-05-25"
    assert record["official_url"] == "https://bop.dacoruna.gal/bopportal/2026_0000003193.html"
    assert record["raw_page_hash"] == hashlib.sha256(raw).hexdigest()
    assert record["classification_status"] == "unclassified"
    assert record["evidence_status"] == "not_evidence"
    assert record["candidate_status"] == "not_candidate"
    assert "pdf_url" not in record


def test_parse_bop_barcelona_fixture_emits_metadata_only_records():
    raw = _fixture_bytes("bop_barcelona_latest.html")
    page_url = "https://bop.diba.cat/butlleti-del-dia"

    result = parse_bop_barcelona_html(
        raw,
        source_code="BOP_BARCELONA",
        page_url=page_url,
        requested_date="2026-05-25",
        discovered_at="2026-05-25T00:00:00Z",
        monitor_run_id="run-barcelona",
    )

    assert result.raw_page_hash == hashlib.sha256(raw).hexdigest()
    assert len(result.records) == 1
    record = result.records[0]
    assert record["source_code"] == "BOP_BARCELONA"
    assert record["page_url"] == page_url
    assert record["page_format"] == "html"
    assert record["entry_id"] == "202610094158"
    assert record["document_id"] == "202610094158"
    assert record["title"] == "Ajuntament de Barcelona - Aprovacio inicial"
    assert record["published_at"] == "2026-05-25"
    assert (
        record["official_url"]
        == "https://bop.diba.cat/anunci/3947743/ajuntament-de-barcelona-aprovacio-inicial"
    )
    assert record["candidate_status"] == "not_candidate"
    assert record["evidence_status"] == "not_evidence"
    assert record["classification_status"] == "unclassified"
    assert "pdf_url" not in record


def test_parse_bon_fixture_emits_metadata_only_records():
    raw = _fixture_bytes("bon_summary_2026_104.html")
    page_url = "https://bon.navarra.es/es/boletin/-/sumario/2026/104"

    result = parse_bon_html(
        raw,
        source_code="BON",
        page_url=page_url,
        requested_date="2026-05-29",
        discovered_at="2026-05-29T00:00:00Z",
        monitor_run_id="run-bon",
    )

    assert result.raw_page_hash == hashlib.sha256(raw).hexdigest()
    assert len(result.records) == 1
    record = result.records[0]
    assert record["source_code"] == "BON"
    assert record["page_url"] == page_url
    assert record["page_format"] == "html"
    assert record["entry_id"] == "2026.104.22"
    assert record["document_id"] == "2026.104.22"
    assert record["title"] == (
        "RESOLUCION 220E/2026, de 4 de mayo, por la que se aprueba la convocatoria "
        "de 2026 de ayudas a entidades locales de Navarra. Codigo BDNS: 903411."
    )
    assert record["published_at"] == "2026-05-29"
    assert record["official_url"] == "https://bon.navarra.es/es/anuncio/-/texto/2026/104/22"
    assert record["summary"] == (
        "1. Comunidad Foral de Navarra - 1.4. Subvenciones, ayudas y becas"
    )
    assert record["issue_number"] == "104"
    assert record["warnings"] == []
    assert record["candidate_status"] == "not_candidate"
    assert record["evidence_status"] == "not_evidence"
    assert record["classification_status"] == "unclassified"
    assert "pdf_url" not in record


def test_parse_bop_bizkaia_detail_fixture_emits_metadata_only_records():
    raw = _fixture_bytes("bop_bizkaia_detail.html")
    page_url = (
        "https://www.bizkaia.eus/es/bob/resultados?p_p_id=IYBIWBCC&"
        "p_p_lifecycle=0&p_p_state=normal&p_p_mode=view&"
        "_IYBIWBCC_mvcRenderCommandName=%2Fdetail&"
        "_IYBIWBCC_bdate=20260525&_IYBIWBCC_bnum=96"
    )

    result = parse_bop_bizkaia_detail_html(
        raw,
        source_code="BOP_BIZKAIA",
        page_url=page_url,
        requested_date="2026-05-25",
        discovered_at="2026-05-25T00:00:00Z",
        monitor_run_id="run-bizkaia",
    )

    assert result.raw_page_hash == hashlib.sha256(raw).hexdigest()
    assert len(result.records) == 1
    record = result.records[0]
    assert record["source_code"] == "BOP_BIZKAIA"
    assert record["page_url"] == page_url
    assert record["page_format"] == "html"
    assert record["entry_id"] == "I-600"
    assert record["document_id"] == "I-600"
    assert record["title"] == "Departamento de Hacienda y Finanzas - Anuncio de subasta, 42/2026."
    assert record["published_at"] == "2026-05-25"
    assert record["official_url"] == (
        "https://www.bizkaia.eus/lehendakaritza/Bao_bob/2026/05/25/I-600_cas.pdf"
    )
    assert record["warnings"] == ["pdf_endpoint_not_downloaded"]
    assert record["candidate_status"] == "not_candidate"
    assert record["evidence_status"] == "not_evidence"
    assert record["classification_status"] == "unclassified"
    assert "pdf_url" not in record


def test_parse_bop_castellon_fixture_emits_metadata_only_records():
    raw = _fixture_bytes("bop_castellon_latest.html")
    page_url = "https://bop.dipcas.es/PortalBOP/"

    result = parse_bop_castellon_html(
        raw,
        source_code="BOP_CASTELLON",
        page_url=page_url,
        requested_date="2026-05-25",
        discovered_at="2026-05-25T00:00:00Z",
        monitor_run_id="run-castellon",
    )

    assert result.raw_page_hash == hashlib.sha256(raw).hexdigest()
    assert len(result.records) == 1
    record = result.records[0]
    assert record["source_code"] == "BOP_CASTELLON"
    assert record["page_url"] == page_url
    assert record["page_format"] == "html"
    assert record["entry_id"] == "165893"
    assert record["document_id"] == "165893"
    assert record["title"] == (
        "RESOLUCION DE ARCHIVO DE EXPEDIENTE POR DESISTIMIENTO DEL INTERESADO. "
        "EXPDTE: ATALFE/2023/188/12"
    )
    assert record["published_at"] == "2026-05-30"
    assert record["official_url"] == (
        "https://bop.dipcas.es/PortalBOP/api/descargarAnuncio?idAnuncio=165893&idioma=es"
    )
    assert record["warnings"] == ["pdf_endpoint_not_downloaded"]
    assert record["candidate_status"] == "not_candidate"
    assert record["evidence_status"] == "not_evidence"
    assert record["classification_status"] == "unclassified"
    assert "pdf_url" not in record


def test_parse_bop_albacete_fixture_emits_metadata_only_records():
    raw = _fixture_bytes("bop_albacete_latest.html")
    page_url = "https://bop.dipualba.es"

    result = parse_bop_albacete_html(
        raw,
        source_code="BOP_ALBACETE",
        page_url=page_url,
        requested_date="2026-05-25",
        discovered_at="2026-05-25T00:00:00Z",
        monitor_run_id="run-albacete",
    )

    assert result.raw_page_hash == hashlib.sha256(raw).hexdigest()
    assert len(result.records) == 1
    record = result.records[0]
    assert record["source_code"] == "BOP_ALBACETE"
    assert record["page_url"] == page_url
    assert record["page_format"] == "html"
    assert record["entry_id"] == "297598"
    assert record["document_id"] == "297598"
    assert record["title"] == (
        "Información pública para conocimiento de usuarios de concesiones de aguas "
        "superficiales de la parte española"
    )
    assert record["published_at"] == "2026-05-25"
    assert record["official_url"] == (
        "https://bop.dipualba.es/servicesajax/descargararchivopaginaBOP/297598"
    )
    assert record["candidate_status"] == "not_candidate"
    assert record["evidence_status"] == "not_evidence"
    assert record["classification_status"] == "unclassified"
    assert "pdf_url" not in record


def test_parse_bop_valencia_fixture_emits_metadata_only_records():
    raw = _fixture_bytes("bop_valencia_latest.html")
    page_url = "https://bop.dival.es/bop/drvisapi.dll"

    result = parse_bop_valencia_html(
        raw,
        source_code="BOP_VALENCIA",
        page_url=page_url,
        requested_date="2026-05-25",
        discovered_at="2026-05-25T00:00:00Z",
        monitor_run_id="run-valencia",
    )

    assert result.raw_page_hash == hashlib.sha256(raw).hexdigest()
    assert len(result.records) == 1
    record = result.records[0]
    assert record["source_code"] == "BOP_VALENCIA"
    assert record["page_url"] == page_url
    assert record["page_format"] == "html"
    assert record["entry_id"] == "2026/06245"
    assert record["document_id"] == "2026/06245"
    assert (
        record["title"] == "Anunci de la Diputacio Provincial de Valencia sobre aprovacio de bases."
    )
    assert record["published_at"] == "2026-05-25"
    assert record["official_url"] is None
    assert record["warnings"] == ["entry_hash_fallback_missing_official_url"]
    assert record["candidate_status"] == "not_candidate"
    assert record["evidence_status"] == "not_evidence"
    assert record["classification_status"] == "unclassified"
    assert "pdf_url" not in record


def test_parse_bop_malaga_fixture_emits_metadata_only_records():
    raw = _fixture_bytes("bop_malaga_latest.html")
    page_url = "https://www.bopmalaga.es/"

    result = parse_bop_malaga_html(
        raw,
        source_code="BOP_MALAGA",
        page_url=page_url,
        requested_date="2026-05-25",
        discovered_at="2026-05-25T00:00:00Z",
        monitor_run_id="run-malaga",
    )

    assert result.raw_page_hash == hashlib.sha256(raw).hexdigest()
    assert len(result.records) == 1
    record = result.records[0]
    assert record["source_code"] == "BOP_MALAGA"
    assert record["page_url"] == page_url
    assert record["page_format"] == "html"
    assert record["entry_id"] == "620/2026"
    assert record["document_id"] == "620/2026"
    assert record["title"] == "Malaga. Convocatoria para seleccion de personal funcionario."
    assert record["published_at"] == "2026-05-25"
    assert (
        record["official_url"]
        == "https://www.bopmalaga.es/edicto.php?edicto=20260525-00620-2026-00"
    )
    assert record["candidate_status"] == "not_candidate"
    assert record["evidence_status"] == "not_evidence"
    assert record["classification_status"] == "unclassified"
    assert "pdf_url" not in record


def test_parse_bop_pontevedra_fixture_emits_metadata_only_records():
    raw = _fixture_bytes("bop_pontevedra_detail.html")
    page_url = "https://boppo.depo.gal/detalle/-/boppo/2026/05/29"

    result = parse_bop_pontevedra_html(
        raw,
        source_code="BOP_PONTEVEDRA",
        page_url=page_url,
        requested_date="2026-05-29",
        discovered_at="2026-05-29T00:00:00Z",
        monitor_run_id="run-pontevedra",
    )

    assert result.raw_page_hash == hashlib.sha256(raw).hexdigest()
    assert len(result.records) == 1
    record = result.records[0]
    assert record["source_code"] == "BOP_PONTEVEDRA"
    assert record["page_url"] == page_url
    assert record["page_format"] == "html"
    assert record["entry_id"] == "2026043804"
    assert record["document_id"] == "2026043804"
    assert record["title"] == (
        "DAR CONTA E ACEPTAR AS RENUNCIAS E LIBERAR O CREDITO DE ENTIDADES "
        "COLABORADORAS DO PROXECTO +EMPREGA NOS CONCELLOS 2025 PARA FINANCIAR "
        "CONTRATOS FORMATIVOS. (EXPTE. 2025050276)"
    )
    assert record["published_at"] == "2026-05-29"
    assert record["official_url"] == (
        "https://boppo.depo.gal/web/boppo/detalle/-/boppo/2026/05/29/2026043804"
    )
    assert record["summary"] == "Deputacion Provincial"
    assert record["warnings"] == ["pdf_endpoint_not_downloaded"]
    assert record["candidate_status"] == "not_candidate"
    assert record["evidence_status"] == "not_evidence"
    assert record["classification_status"] == "unclassified"
    assert "pdf_url" not in record


def test_parse_bop_palencia_fixture_emits_bulletin_level_metadata_only_record():
    raw = _fixture_bytes("bop_palencia_latest.html")
    page_url = "https://www.diputaciondepalencia.es/servicios/boletin-oficial-provincia"

    result = parse_bop_palencia_html(
        raw,
        source_code="BOP_PALENCIA",
        page_url=page_url,
        requested_date="2026-05-29",
        discovered_at="2026-05-29T00:00:00Z",
        monitor_run_id="run-palencia",
    )

    assert result.raw_page_hash == hashlib.sha256(raw).hexdigest()
    assert len(result.records) == 1
    record = result.records[0]
    assert record["source_code"] == "BOP_PALENCIA"
    assert record["page_url"] == page_url
    assert record["page_format"] == "html"
    assert record["entry_id"] == "20260529-bop-64-Ordinario"
    assert record["document_id"] == "20260529-bop-64-Ordinario"
    assert record["title"] == "BOP No 64 del Viernes, 29 de Mayo de 2026"
    assert record["published_at"] == "2026-05-29"
    assert record["official_url"] == (
        "https://www.diputaciondepalencia.es/servicios/boletin-oficial-provincia/"
        "bop-no-64-viernes-29-mayo-2026"
    )
    assert record["warnings"] == ["pdf_endpoint_not_downloaded"]
    assert record["candidate_status"] == "not_candidate"
    assert record["evidence_status"] == "not_evidence"
    assert record["classification_status"] == "unclassified"
    assert "pdf_url" not in record


def test_parse_bop_avila_fixture_emits_metadata_only_records():
    raw = _fixture_bytes("bop_avila_detail.html")
    page_url = "https://www.diputacionavila.es/boletin-oficial/2026/29-05-2026.html"

    result = parse_bop_avila_html(
        raw,
        source_code="BOP_AVILA",
        page_url=page_url,
        requested_date="2026-05-29",
        discovered_at="2026-05-29T00:00:00Z",
        monitor_run_id="run-avila",
    )

    assert result.raw_page_hash == hashlib.sha256(raw).hexdigest()
    assert len(result.records) == 1
    record = result.records[0]
    assert record["source_code"] == "BOP_AVILA"
    assert record["page_url"] == page_url
    assert record["page_format"] == "html"
    assert record["entry_id"] == "29-05-2026_116626"
    assert record["document_id"] == "29-05-2026_116626"
    assert record["title"] == (
        "APROBACION DEFINITIVA EXPEDIENTES DE CREDITO EXTRAORDINARIO 1-2026 "
        "Y SUPLEMENTO DE CREDITO 1-2026"
    )
    assert record["published_at"] == "2026-05-29"
    assert record["official_url"] == (
        "https://www.diputacionavila.es/bops/2026/29-05-2026/29-05-2026_116626.pdf"
    )
    assert record["warnings"] == ["pdf_endpoint_not_downloaded"]
    assert record["candidate_status"] == "not_candidate"
    assert record["evidence_status"] == "not_evidence"
    assert record["classification_status"] == "unclassified"
    assert "pdf_url" not in record


def test_parse_bop_cordoba_fixture_emits_metadata_only_records():
    raw = _fixture_bytes("bop_cordoba_next_payload.html")
    page_url = "https://bop.dipucordoba.es/dia/28-05-2026"

    result = parse_bop_cordoba_html(
        raw,
        source_code="BOP_CORDOBA",
        page_url=page_url,
        requested_date="2026-05-28",
        discovered_at="2026-05-28T00:00:00Z",
        monitor_run_id="run-cordoba",
    )

    assert result.raw_page_hash == hashlib.sha256(raw).hexdigest()
    assert len(result.records) == 1
    record = result.records[0]
    assert record["source_code"] == "BOP_CORDOBA"
    assert record["page_url"] == page_url
    assert record["page_format"] == "nextjs-rsc-html"
    assert record["entry_id"] == "119762"
    assert record["document_id"] == "BOP-A-2026-1795"
    assert (
        record["title"]
        == "Bases de la convocatoria para cubrir 19 plazas de Auxiliar Administrativo"
    )
    assert record["published_at"] == "2026-05-28"
    assert record["official_url"] == (
        "https://bop.dipucordoba.es/visor-pdf/28-05-2026/BOP-A-2026-1795.pdf"
    )
    assert record["summary"] == "Diputación de Córdoba"
    assert record["warnings"] == ["pdf_endpoint_not_downloaded"]
    assert record["candidate_status"] == "not_candidate"
    assert record["evidence_status"] == "not_evidence"
    assert record["classification_status"] == "unclassified"
    assert "pdf_url" not in record


def test_parse_bop_soria_fixture_emits_metadata_only_records():
    raw = _fixture_bytes("bop_soria_detail.html")
    page_url = (
        "https://bop.dipsoria.es/index.php/mod.boloficial/mem.detalle/id.54776/relcategoria.210"
    )

    result = parse_bop_soria_html(
        raw,
        source_code="BOP_SORIA",
        page_url=page_url,
        requested_date="2026-05-29",
        discovered_at="2026-05-29T00:00:00Z",
        monitor_run_id="run-soria",
    )

    assert result.raw_page_hash == hashlib.sha256(raw).hexdigest()
    assert len(result.records) == 1
    record = result.records[0]
    assert record["source_code"] == "BOP_SORIA"
    assert record["page_url"] == page_url
    assert record["page_format"] == "html"
    assert record["entry_id"] == "1018"
    assert record["document_id"] == "1018"
    assert record["title"] == "Proyecto OPDE Trevago 1 hibridacion"
    assert record["published_at"] == "2026-05-29"
    assert record["official_url"] == (
        "http://bop.dipsoria.es/index.php/mod.documentos/mem.descargar/"
        "fichero.documentos_1018_f741c556%232E%23pdf"
    )
    assert record["summary"] == (
        "I. ADMINISTRACION DEL ESTADO - SUBDELEGACION DEL GOBIERNO EN SORIA - "
        "AREA FUNCIONAL DE INDUSTRIA Y ENERGIA"
    )
    assert record["warnings"] == ["pdf_endpoint_not_downloaded"]
    assert record["candidate_status"] == "not_candidate"
    assert record["evidence_status"] == "not_evidence"
    assert record["classification_status"] == "unclassified"
    assert "pdf_url" not in record


def test_parse_docm_fixture_emits_metadata_only_records():
    raw = _fixture_bytes("docm_summary_2026_05_29.html")
    page_url = "https://docm.jccm.es/docm/cambiarBoletin.do?fecha=20260529"

    result = parse_docm_html(
        raw,
        source_code="DOCM",
        page_url=page_url,
        requested_date="2026-05-29",
        discovered_at="2026-05-29T00:00:00Z",
        monitor_run_id="run-docm",
    )

    assert result.raw_page_hash == hashlib.sha256(raw).hexdigest()
    assert len(result.records) == 1
    record = result.records[0]
    assert record["source_code"] == "DOCM"
    assert record["page_url"] == page_url
    assert record["page_format"] == "html"
    assert record["entry_id"] == "DOCM:2026/4101"
    assert record["document_id"] == "2026/4101"
    assert record["title"] == (
        "Presupuestos Generales. Orden 75/2026, de 26 de mayo, por la que se "
        "regulan normas presupuestarias."
    )
    assert record["published_at"] == "2026-05-29"
    assert record["official_url"] == (
        "https://docm.jccm.es/docm/verArchivoHtml.do?"
        "ruta=2026/05/29/html/2026_4101.html&tipo=rutaDocm"
    )
    assert record["summary"] == "I.- DISPOSICIONES GENERALES - Consejería de Hacienda"
    assert record["issue_number"] == "101"
    assert record["page"] == "21205"
    assert record["warnings"] == ["pdf_endpoint_not_downloaded"]
    assert record["candidate_status"] == "not_candidate"
    assert record["evidence_status"] == "not_evidence"
    assert record["classification_status"] == "unclassified"
    assert "pdf_url" not in record


def test_parse_bop_sevilla_fixture_emits_metadata_only_records():
    raw = _fixture_bytes("bop_sevilla_latest.html")
    page_url = "https://bopsevilla.dipusevilla.es/publica/consulta-de-bops/buscador/BOP-28-05-2026/"

    result = parse_bop_sevilla_html(
        raw,
        source_code="BOP_SEVILLA",
        page_url=page_url,
        requested_date="2026-05-25",
        discovered_at="2026-05-25T00:00:00Z",
        monitor_run_id="run-sevilla",
    )

    assert result.raw_page_hash == hashlib.sha256(raw).hexdigest()
    assert len(result.records) == 1
    record = result.records[0]
    assert record["source_code"] == "BOP_SEVILLA"
    assert record["page_url"] == page_url
    assert record["page_format"] == "html"
    assert record["entry_id"] == "BOP-SE-2026-101002"
    assert record["document_id"] == "BOP-SE-2026-101002"
    assert record["title"] == (
        "Bases para la selección de personal laboral fijo en la categoría de Técnico OPEM "
        "y creación de bolsa de trabajo"
    )
    assert record["published_at"] == "2026-05-28"
    assert record["official_url"] == (
        "https://bopsevilla.dipusevilla.es/publica/buscador-anuncios/anuncio/"
        "Bases-para-la-seleccion-de-personal-laboral-fijo-en-la-categoria-de-Tecnico-OPEM/"
    )
    assert record["summary"] == "La Algaba"
    assert record["candidate_status"] == "not_candidate"
    assert record["evidence_status"] == "not_evidence"
    assert record["classification_status"] == "unclassified"
    assert "pdf_url" not in record


def test_parse_bop_granada_fixture_emits_metadata_only_records():
    raw = _fixture_bytes("bop_granada_latest.html")
    page_url = "https://bop.dipgra.es/publica/consulta-de-bops/buscador/BOP-29-05-2026/"

    result = parse_bop_sevilla_html(
        raw,
        source_code="BOP_GRANADA",
        page_url=page_url,
        requested_date="2026-05-29",
        discovered_at="2026-05-29T00:00:00Z",
        monitor_run_id="run-granada",
    )

    assert result.raw_page_hash == hashlib.sha256(raw).hexdigest()
    assert len(result.records) == 1
    record = result.records[0]
    assert record["source_code"] == "BOP_GRANADA"
    assert record["page_url"] == page_url
    assert record["page_format"] == "html"
    assert record["entry_id"] == "BOP-GRA-2026-102004"
    assert record["document_id"] == "BOP-GRA-2026-102004"
    assert record["title"] == (
        "BASES PARA LA SELECCION Y CONSTITUCION BOLSA DE AUXILIARES "
        "ADMINISTRATIVOS MEDIANTE EL PROCEDIMIENTO DE OPOSICION LIBRE, DE LA "
        "QUE EXTRAER NOMBRAMIENTOS COMO FUNCIONARIOS INTERINOS."
    )
    assert record["published_at"] == "2026-05-29"
    assert record["official_url"] == (
        "https://bop.dipgra.es/publica/buscador-anuncios/anuncio/"
        "BASES-PARA-LA-SELECCION-Y-CONSTITUCION-BOLSA-DE-AUXILIARES-"
        "ADMINISTRATIVOS-MEDIANTE-EL-PROCEDIMIENTO-DE-OPOSICION-LIBRE-DE-LA-"
        "QUE-EXTRAER-NOMBRAMIENTOS-COMO-FUNCIONARIOS-INTERINOS/"
    )
    assert record["summary"] == "AYUNTAMIENTO DE ALPUJARRA DE LA SIERRA"
    assert record["candidate_status"] == "not_candidate"
    assert record["evidence_status"] == "not_evidence"
    assert record["classification_status"] == "unclassified"
    assert "pdf_url" not in record


def test_parse_bop_valladolid_fixture_emits_metadata_only_records():
    raw = _fixture_bytes("bop_valladolid_latest.html")
    page_url = (
        "https://bop.sede.diputaciondevalladolid.es/ultimobop?"
        "_BOPVisualizaBoletin_WAR_BOPVisualizaBoletin_fecha=2026-05-29"
    )

    result = parse_bop_valladolid_html(
        raw,
        source_code="BOP_VALLADOLID",
        page_url=page_url,
        requested_date="2026-05-29",
        discovered_at="2026-05-29T00:00:00Z",
        monitor_run_id="run-valladolid",
    )

    assert result.raw_page_hash == hashlib.sha256(raw).hexdigest()
    assert len(result.records) == 1
    record = result.records[0]
    assert record["source_code"] == "BOP_VALLADOLID"
    assert record["page_url"] == page_url
    assert record["page_format"] == "html"
    assert record["entry_id"] == "BOPVA-A-2026-01573"
    assert record["document_id"] == "BOPVA-A-2026-01573"
    assert record["title"] == (
        "Convocatoria de concurso-oposicion para la seleccion con caracter temporal de un "
        "puesto de tecnico medio economista en la oficina presupuestaria."
    )
    assert record["published_at"] == "2026-05-29"
    assert record["official_url"] == (
        "https://bop.sede.diputaciondevalladolid.es/boletines/2026/mayo/29/BOPVA-A-2026-01573.pdf"
    )
    assert record["summary"] == "AYUNTAMIENTO DE VALLADOLID"
    assert record["warnings"] == ["pdf_endpoint_not_downloaded"]
    assert record["candidate_status"] == "not_candidate"
    assert record["evidence_status"] == "not_evidence"
    assert record["classification_status"] == "unclassified"
    assert "pdf_url" not in record


def test_parse_bop_alicante_fixture_emits_metadata_only_records():
    raw = _fixture_bytes("bop_alicante_bop_con.json")
    page_url = build_bop_alicante_html_url(
        "https://sede.diputacionalicante.es/wp-content/themes/"
        "Desarrollo-Diputacion/webservices/wseConsultaAjax.php",
        target_date="2026-05-25",
    )

    result = parse_bop_alicante_response(
        raw,
        source_code="BOP_ALICANTE",
        page_url=page_url,
        requested_date="2026-05-25",
        discovered_at="2026-05-25T00:00:00Z",
        monitor_run_id="run-alicante",
    )

    assert result.raw_page_hash == hashlib.sha256(raw).hexdigest()
    assert len(result.records) == 1
    record = result.records[0]
    assert record["source_code"] == "BOP_ALICANTE"
    assert record["page_url"] == page_url
    assert record["page_format"] == "json-backed-html"
    assert record["entry_id"] == "96-3923"
    assert record["document_id"] == "3923"
    assert record["title"] == (
        "APROVACIÓ DEFINITIVA ORDENANÇA FISCAL REGULADORA DE LA TAXA PER "
        "EXPEDICIÓ DE DOCUMENTS ADMINISTRATIUS"
    )
    assert record["published_at"] == "2026-05-25"
    assert record["official_url"] == (
        "https://www.dip-alicante.es/bop2/pdftotal/2026/05/25_96/2026_003923.pdf"
    )
    assert record["summary"] == "III. ADMINISTRACIÓN LOCAL - AYUNTAMIENTO ADSUBIA"
    assert record["candidate_status"] == "not_candidate"
    assert record["evidence_status"] == "not_evidence"
    assert record["classification_status"] == "unclassified"
    assert "pdf_url" not in record


def test_html_entry_hash_prefers_source_published_at_and_official_url():
    assert (
        build_html_entry_hash(
            source_code="BOP_A_CORUNA",
            published_at="2026-05-25",
            official_url="https://bop.dacoruna.gal/bopportal/2026_0000003193.html",
            document_id="ignored",
            title="ignored",
        )
        == hashlib.sha256(
            b"BOP_A_CORUNA2026-05-25https://bop.dacoruna.gal/bopportal/2026_0000003193.html"
        ).hexdigest()
    )


def test_monitor_html_source_fetches_one_bounded_request():
    requested_urls = []

    def fetcher(url: str) -> bytes:
        requested_urls.append(url)
        return _fixture_bytes("bop_a_coruna_latest.html")

    result = monitor_html_source(
        get_source("BOP_A_CORUNA"),
        fetcher=fetcher,
        target_date="2026-05-25",
        limit=1,
    )

    assert requested_urls == [
        "https://bop.dacoruna.gal/bopportal/cambioBoletin.do?fechaInput=25%2F05%2F2026"
    ]
    assert len(result.records) == 1
    assert result.records[0]["candidate_status"] == "not_candidate"
    assert result.records[0]["evidence_status"] == "not_evidence"


def test_monitor_html_source_supports_selected_provincial_sources():
    fixtures = {
        "BOP_ALBACETE": "bop_albacete_latest.html",
        "BOP_ALICANTE": "bop_alicante_bop_con.json",
        "BOP_AVILA": "bop_avila_detail.html",
        "BOP_BARCELONA": "bop_barcelona_latest.html",
        "BOP_CASTELLON": "bop_castellon_latest.html",
        "BOP_CORDOBA": "bop_cordoba_next_payload.html",
        "BOP_GRANADA": "bop_granada_latest.html",
        "BOP_MALAGA": "bop_malaga_latest.html",
        "BOP_PONTEVEDRA": "bop_pontevedra_detail.html",
        "BOP_VALENCIA": "bop_valencia_latest.html",
        "BOP_VALLADOLID": "bop_valladolid_latest.html",
        "DOCM": "docm_summary_2026_05_29.html",
    }

    for source_code, fixture_name in fixtures.items():
        requested_urls = []

        def fetcher(
            url: str,
            *,
            fixture_name: str = fixture_name,
            requested_urls: list[str] = requested_urls,
        ) -> bytes:
            requested_urls.append(url)
            return _fixture_bytes(fixture_name)

        result = monitor_html_source(
            get_source(source_code),
            fetcher=fetcher,
            target_date="2026-05-25",
            limit=1,
        )

        assert len(requested_urls) == 1
        assert len(result.records) == 1
        assert result.records[0]["source_code"] == source_code
        assert result.records[0]["candidate_status"] == "not_candidate"
        assert result.records[0]["evidence_status"] == "not_evidence"
        assert result.records[0]["classification_status"] == "unclassified"


def test_monitor_bop_bizkaia_fetches_landing_then_public_detail():
    requested_urls = []
    detail_url = (
        "https://www.bizkaia.eus/es/bob/resultados?p_p_id=IYBIWBCC&"
        "p_p_lifecycle=0&p_p_state=normal&p_p_mode=view&"
        "_IYBIWBCC_mvcRenderCommandName=%2Fdetail&"
        "_IYBIWBCC_bdate=20260525&_IYBIWBCC_bnum=96"
    )

    def fetcher(url: str) -> bytes:
        requested_urls.append(url)
        if url == "https://www.bizkaia.eus/es/bob":
            return _fixture_bytes("bop_bizkaia_landing.html")
        if url == detail_url:
            return _fixture_bytes("bop_bizkaia_detail.html")
        raise AssertionError(f"unexpected URL: {url}")

    result = monitor_html_source(
        get_source("BOP_BIZKAIA"),
        fetcher=fetcher,
        target_date="2026-05-25",
        limit=1,
    )

    assert requested_urls == ["https://www.bizkaia.eus/es/bob", detail_url]
    assert len(result.records) == 1
    assert result.records[0]["source_code"] == "BOP_BIZKAIA"
    assert result.records[0]["candidate_status"] == "not_candidate"
    assert result.records[0]["evidence_status"] == "not_evidence"
    assert result.records[0]["classification_status"] == "unclassified"


def test_monitor_bop_sevilla_fetches_landing_then_public_detail():
    requested_urls = []
    landing_url = "https://bopsevilla.dipusevilla.es/publica/consulta-de-bops/"
    detail_url = (
        "https://bopsevilla.dipusevilla.es/publica/consulta-de-bops/buscador/BOP-28-05-2026/"
    )

    def fetcher(url: str) -> bytes:
        requested_urls.append(url)
        if url == landing_url:
            return _fixture_bytes("bop_sevilla_landing.html")
        if url == detail_url:
            return _fixture_bytes("bop_sevilla_latest.html")
        raise AssertionError(f"unexpected URL: {url}")

    result = monitor_html_source(
        get_source("BOP_SEVILLA"),
        fetcher=fetcher,
        target_date="2026-05-25",
        limit=1,
    )

    assert requested_urls == [landing_url, detail_url]
    assert len(result.records) == 1
    assert result.records[0]["source_code"] == "BOP_SEVILLA"
    assert result.records[0]["candidate_status"] == "not_candidate"
    assert result.records[0]["evidence_status"] == "not_evidence"
    assert result.records[0]["classification_status"] == "unclassified"


def test_monitor_bop_soria_fetches_date_page_then_public_detail():
    requested_urls = []
    date_url = "https://bop.dipsoria.es/index.php/mod.boloficial/mem.listadodia/fecha.29-05-2026"
    detail_url = (
        "https://bop.dipsoria.es/index.php/mod.boloficial/mem.detalle/id.54776/relcategoria.210"
    )

    def fetcher(url: str) -> bytes:
        requested_urls.append(url)
        if url == date_url:
            return _fixture_bytes("bop_soria_date.html")
        if url == detail_url:
            return _fixture_bytes("bop_soria_detail.html")
        raise AssertionError(f"unexpected URL: {url}")

    result = monitor_html_source(
        get_source("BOP_SORIA"),
        fetcher=fetcher,
        target_date="2026-05-29",
        limit=1,
    )

    assert requested_urls == [date_url, detail_url]
    assert len(result.records) == 1
    assert result.records[0]["source_code"] == "BOP_SORIA"
    assert result.records[0]["candidate_status"] == "not_candidate"
    assert result.records[0]["evidence_status"] == "not_evidence"
    assert result.records[0]["classification_status"] == "unclassified"


def test_monitor_bon_fetches_month_index_then_issue_summary():
    requested_urls = []
    index_url = build_bon_html_url(
        "https://bon.navarra.es/es/indice-boletines",
        target_date="2026-05-29",
    )
    summary_url = "https://bon.navarra.es/es/boletin/-/sumario/2026/104"

    def fetcher(url: str) -> bytes:
        requested_urls.append(url)
        if url == index_url:
            return _fixture_bytes("bon_index_may_2026.html")
        if url == summary_url:
            return _fixture_bytes("bon_summary_2026_104.html")
        raise AssertionError(f"unexpected URL: {url}")

    result = monitor_html_source(
        get_source("BON"),
        fetcher=fetcher,
        target_date="2026-05-29",
        limit=1,
    )

    assert requested_urls == [index_url, summary_url]
    assert len(result.records) == 1
    assert result.records[0]["source_code"] == "BON"
    assert result.records[0]["candidate_status"] == "not_candidate"
    assert result.records[0]["evidence_status"] == "not_evidence"
    assert result.records[0]["classification_status"] == "unclassified"


def test_monitor_bop_palencia_returns_latest_only_when_date_matches():
    requested_urls = []
    landing_url = "https://www.diputaciondepalencia.es/servicios/boletin-oficial-provincia"

    def fetcher(url: str) -> bytes:
        requested_urls.append(url)
        return _fixture_bytes("bop_palencia_latest.html")

    result = monitor_html_source(
        get_source("BOP_PALENCIA"),
        fetcher=fetcher,
        target_date="2026-05-29",
        limit=1,
    )

    assert requested_urls == [landing_url]
    assert len(result.records) == 1
    assert result.records[0]["source_code"] == "BOP_PALENCIA"
    assert result.records[0]["published_at"] == "2026-05-29"
    assert result.records[0]["candidate_status"] == "not_candidate"
    assert result.records[0]["evidence_status"] == "not_evidence"


def test_html_monitor_refuses_source_without_validated_html_access_method():
    with pytest.raises(HTMLMonitorError) as exc_info:
        select_html_access_method(get_source("BOP_ZARAGOZA"))

    assert "does not have a validated html access method" in str(exc_info.value)


def test_html_monitor_has_no_candidate_evidence_or_artifact_code_paths():
    source = inspect.getsource(html_monitor)

    assert "create_source_candidate" not in source
    assert "ArtifactDownloader" not in source
    assert "download_pdf" not in source.lower()
    assert "evidence_grade" not in source


def test_fetch_html_sends_read_only_user_agent(monkeypatch):
    requested_headers = []

    class FakeResponse:
        url = "https://example.test"
        content = b"<html></html>"

        def raise_for_status(self) -> None:
            return None

    class FakeClient:
        def __init__(self, **_kwargs):
            return None

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def get(self, _url, *, headers):
            requested_headers.append(headers)
            return FakeResponse()

    monkeypatch.setattr(html_monitor.httpx, "Client", FakeClient)

    assert html_monitor.fetch_html("https://example.test") == b"<html></html>"
    assert requested_headers[0]["User-Agent"] == "official-sources-html-monitor/0.1"


def test_fetch_html_wraps_httpx_errors(monkeypatch):
    class FailingClient:
        def __init__(self, **_kwargs):
            return None

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def get(self, _url, *, headers):
            raise html_monitor.httpx.ConnectTimeout("timed out")

    monkeypatch.setattr(html_monitor.httpx, "Client", FailingClient)

    with pytest.raises(HTMLMonitorError) as exc_info:
        html_monitor.fetch_html("https://example.test")

    assert "html monitor fetch failed for https://example.test" in str(exc_info.value)


def test_html_jsonl_output_path_is_source_and_date_scoped(tmp_path):
    assert build_html_monitor_output_path(tmp_path, "BOP_A_CORUNA", "2026-05-25") == (
        tmp_path / "BOP_A_CORUNA" / "2026-05-25" / "html_discovery.jsonl"
    )


def test_cli_html_monitor_refuses_all_source_runs(capsys):
    from official_sources.cli import run

    exit_code = run(["html", "monitor", "--source", "ALL", "--date", "2026-05-25"])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "one source at a time" in captured.err


def test_cli_html_monitor_refuses_source_without_validated_html(capsys):
    from official_sources.cli import run

    exit_code = run(["html", "monitor", "--source", "BOP_ZARAGOZA", "--date", "2026-05-25"])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "does not have a validated html access method" in captured.err


def test_cli_html_monitor_preview_does_not_write_or_open_repository(tmp_path, monkeypatch, capsys):
    from official_sources import cli

    def fail_open_repository(_db_path: str):
        raise AssertionError("html monitor must not open SQLite")

    monkeypatch.setattr(cli, "_open_repository", fail_open_repository)

    exit_code = cli.run(
        [
            "html",
            "monitor",
            "--source",
            "BOP_A_CORUNA",
            "--date",
            "2026-05-25",
            "--limit",
            "1",
            "--output-root",
            str(tmp_path),
        ],
        html_fetcher=lambda _url: _fixture_bytes("bop_a_coruna_latest.html"),
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "mode=preview" in captured.out
    assert "discovery_metadata_only=true" in captured.out
    assert not list(tmp_path.rglob("*.jsonl"))


def test_cli_html_monitor_write_requires_explicit_write_flag_and_writes_jsonl(tmp_path, capsys):
    from official_sources.cli import run

    exit_code = run(
        [
            "html",
            "monitor",
            "--source",
            "BOP_A_CORUNA",
            "--date",
            "2026-05-25",
            "--limit",
            "1",
            "--write",
            "--output-root",
            str(tmp_path),
        ],
        html_fetcher=lambda _url: _fixture_bytes("bop_a_coruna_latest.html"),
    )
    captured = capsys.readouterr()
    output_path = tmp_path / "BOP_A_CORUNA" / "2026-05-25" / "html_discovery.jsonl"

    assert exit_code == 0
    assert f"output_path={output_path}" in captured.out
    records = [json.loads(line) for line in output_path.read_text(encoding="utf-8").splitlines()]
    assert len(records) == 1
    assert records[0]["source_code"] == "BOP_A_CORUNA"
    assert records[0]["candidate_status"] == "not_candidate"
    assert records[0]["evidence_status"] == "not_evidence"


def test_mcp_source_coverage_sees_bop_a_coruna_as_html_monitorable():
    result = list_monitorable_sources()
    sources = {source["source_code"]: source for source in result["sources"]}
    for source_code in (
        "BOP_A_CORUNA",
        "BOP_ALBACETE",
        "BOP_ALICANTE",
        "BOP_BARCELONA",
        "BOP_BIZKAIA",
        "BOP_CASTELLON",
        "BOP_MALAGA",
        "BOP_SEVILLA",
        "BOP_VALENCIA",
    ):
        method_types = {method["type"] for method in sources[source_code]["access_methods"]}

        assert "html" in method_types
        assert sources[source_code]["candidate_creation_allowed"] is False
        assert sources[source_code]["evidence_grade_allowed"] is False


def test_existing_source_registry_validation_still_passes():
    registry = load_source_registry()

    assert len(registry["sources"]) == 65
