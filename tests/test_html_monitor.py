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
    build_bop_araba_alava_html_url,
    build_bop_avila_html_url,
    build_bop_barcelona_html_url,
    build_bop_bizkaia_html_url,
    build_bop_burgos_html_url,
    build_bop_cadiz_html_url,
    build_bop_castellon_html_url,
    build_bop_ciudad_real_html_url,
    build_bop_cordoba_html_url,
    build_bop_cuenca_html_url,
    build_bop_gipuzkoa_html_url,
    build_bop_girona_html_url,
    build_bop_granada_html_url,
    build_bop_huesca_html_url,
    build_bop_jaen_html_url,
    build_bop_las_palmas_html_url,
    build_bop_leon_html_url,
    build_bop_lleida_html_url,
    build_bop_malaga_html_url,
    build_bop_palencia_html_url,
    build_bop_pontevedra_html_url,
    build_bop_salamanca_html_url,
    build_bop_santa_cruz_tenerife_html_url,
    build_bop_segovia_html_url,
    build_bop_sevilla_html_url,
    build_bop_soria_html_url,
    build_bop_tarragona_html_url,
    build_bop_teruel_html_url,
    build_bop_toledo_html_url,
    build_bop_valencia_html_url,
    build_bop_valladolid_html_url,
    build_bop_zamora_html_url,
    build_bop_zaragoza_html_url,
    build_bopa_html_url,
    build_docm_html_url,
    build_html_entry_hash,
    build_html_monitor_output_path,
    monitor_html_source,
    parse_bon_html,
    parse_bop_a_coruna_html,
    parse_bop_albacete_html,
    parse_bop_alicante_response,
    parse_bop_araba_alava_html,
    parse_bop_avila_html,
    parse_bop_barcelona_html,
    parse_bop_bizkaia_detail_html,
    parse_bop_burgos_html,
    parse_bop_cadiz_html,
    parse_bop_castellon_html,
    parse_bop_ciudad_real_html,
    parse_bop_cordoba_html,
    parse_bop_cuenca_html,
    parse_bop_gipuzkoa_html,
    parse_bop_girona_html,
    parse_bop_huesca_html,
    parse_bop_jaen_html,
    parse_bop_las_palmas_html,
    parse_bop_leon_html,
    parse_bop_lleida_html,
    parse_bop_malaga_html,
    parse_bop_palencia_html,
    parse_bop_pontevedra_html,
    parse_bop_salamanca_html,
    parse_bop_santa_cruz_tenerife_html,
    parse_bop_segovia_html,
    parse_bop_sevilla_html,
    parse_bop_soria_html,
    parse_bop_tarragona_html,
    parse_bop_teruel_html,
    parse_bop_toledo_html,
    parse_bop_valencia_html,
    parse_bop_valladolid_html,
    parse_bop_zamora_html,
    parse_bop_zaragoza_html,
    parse_bopa_html,
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
        "BOP_ARABA_ALAVA",
        "BOP_AVILA",
        "BOP_BARCELONA",
        "BON",
        "BOP_BIZKAIA",
        "BOP_BURGOS",
        "BOP_CADIZ",
        "BOP_CASTELLON",
        "BOP_CIUDAD_REAL",
        "BOP_CORDOBA",
        "BOP_GIRONA",
        "BOP_GIPUZKOA",
        "BOP_GRANADA",
        "BOP_HUESCA",
        "BOP_JAEN",
        "BOP_LAS_PALMAS",
        "BOP_LEON",
        "BOP_LLEIDA",
        "BOP_MALAGA",
        "BOP_PALENCIA",
        "BOP_PONTEVEDRA",
        "BOP_SEGOVIA",
        "BOP_SEVILLA",
        "BOP_SANTA_CRUZ_TENERIFE",
        "BOP_SORIA",
        "BOP_TARRAGONA",
        "BOP_TERUEL",
        "BOP_TOLEDO",
        "BOP_VALENCIA",
        "BOP_VALLADOLID",
        "BOP_ZAMORA",
        "BOPA",
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


def test_build_bop_araba_alava_html_url_is_one_date_request():
    assert build_bop_araba_alava_html_url(
        "http://www.araba.eus/botha/Inicio/SGBO5001.aspx?FechaBotha={date_ddmmyyyy}",
        target_date="2026-05-29",
    ) == "http://www.araba.eus/botha/Inicio/SGBO5001.aspx?FechaBotha=29%2F05%2F2026"


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


def test_build_bop_burgos_html_url_is_one_date_request():
    assert build_bop_burgos_html_url(
        "http://bopbur.diputaciondeburgos.es/hemeroteca/{date}?mostrar-anuncio=1",
        target_date="2026-05-29",
    ) == "http://bopbur.diputaciondeburgos.es/hemeroteca/2026-05-29?mostrar-anuncio=1"


def test_build_bop_cadiz_html_url_is_landing_request():
    assert (
        build_bop_cadiz_html_url("https://www.bopcadiz.es/boletin/", target_date="2026-05-29")
        == "https://www.bopcadiz.es/boletin/"
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


def test_build_bop_ciudad_real_html_url_is_one_date_request():
    assert build_bop_ciudad_real_html_url(
        "https://bop.dipucr.es/bop/{yyyy}/{mm}/{dd}",
        target_date="2026-05-29",
    ) == "https://bop.dipucr.es/bop/2026/05/29"


def test_build_bop_cuenca_html_url_is_one_date_request():
    assert build_bop_cuenca_html_url(
        "https://www.dipucuenca.es/boletin-oficial-de-la-provincia?"
        "p_r_p_startDate={date_ddmmyyyy}&p_r_p_endDate={date_ddmmyyyy}",
        target_date="2026-05-29",
    ) == (
        "https://www.dipucuenca.es/boletin-oficial-de-la-provincia?"
        "p_r_p_startDate=29%2F05%2F2026&p_r_p_endDate=29%2F05%2F2026"
    )


def test_build_bop_girona_html_url_is_latest_landing_request():
    assert (
        build_bop_girona_html_url("https://www.ddgi.cat/bop/", target_date="2026-05-29")
        == "https://www.ddgi.cat/bop/"
    )


def test_build_bop_gipuzkoa_html_url_is_one_date_request():
    assert build_bop_gipuzkoa_html_url(
        "https://egoitza.gipuzkoa.eus/gao-bog/castell/bog/{yyyy}/{mm}/{dd}/bc{yymmdd}.htm",
        target_date="2026-05-29",
    ) == "https://egoitza.gipuzkoa.eus/gao-bog/castell/bog/2026/05/29/bc260529.htm"


def test_build_bop_huesca_html_url_is_latest_bulletin_request():
    url = (
        "https://bop.dphuesca.es/index.php/mod.bopanuncios/mem.ultimoboletin/"
        "idmenu.50004/seccion.portal/chk.b6a0e09090757bcdf5de25060e5c4cf5.html"
    )

    assert build_bop_huesca_html_url(url, target_date="2026-06-01") == url


def test_build_bop_las_palmas_html_url_is_one_date_request():
    assert build_bop_las_palmas_html_url(
        "https://www.boplaspalmas.net/nbop2/sumario.php?"
        "codigopub=1&fecha_mas_reciente={date}",
        target_date="2026-05-29",
    ) == (
        "https://www.boplaspalmas.net/nbop2/sumario.php?"
        "codigopub=1&fecha_mas_reciente=2026-05-29"
    )


def test_build_bop_salamanca_html_url_is_one_date_request():
    assert build_bop_salamanca_html_url(
        "https://sede.diputaciondesalamanca.gob.es/opencms/opencms/sede/BOP/"
        "index.jsp?fechaBoletin={date}",
        target_date="2026-05-29",
    ) == (
        "https://sede.diputaciondesalamanca.gob.es/opencms/opencms/sede/BOP/"
        "index.jsp?fechaBoletin=2026-05-29"
    )


def test_build_bop_santa_cruz_tenerife_html_url_is_one_date_request():
    assert build_bop_santa_cruz_tenerife_html_url(
        "http://www.bopsantacruzdetenerife.es/bopsc2/sumario.php?"
        "codigopub=1&fecha_mas_reciente={date}",
        target_date="2026-05-29",
    ) == (
        "http://www.bopsantacruzdetenerife.es/bopsc2/sumario.php?"
        "codigopub=1&fecha_mas_reciente=2026-05-29"
    )


def test_build_bop_teruel_html_url_is_one_current_bulletin_request():
    assert build_bop_teruel_html_url(
        "https://236ws.dpteruel.es/DPT/bopt.nsf/inicio.xsp",
        target_date="2026-05-29",
    ) == "https://236ws.dpteruel.es/DPT/bopt.nsf/inicio.xsp"


def test_build_bop_granada_html_url_is_one_date_request():
    assert (
        build_bop_granada_html_url(
            "https://bop.dipgra.es/publica/consulta-de-bops/buscador/BOP-{dd_mm_yyyy}/",
            target_date="2026-05-29",
        )
        == "https://bop.dipgra.es/publica/consulta-de-bops/buscador/BOP-29-05-2026/"
    )


def test_build_bop_jaen_html_url_is_one_date_request():
    assert (
        build_bop_jaen_html_url(
            "https://bop.dipujaen.es/bop/{dd_mm_yyyy}", target_date="2026-05-29"
        )
        == "https://bop.dipujaen.es/bop/29-05-2026"
    )


def test_build_bop_leon_html_url_is_one_date_request():
    assert build_bop_leon_html_url(
        "https://bop.dipuleon.es/publica/consulta-de-bops/buscador/BOP-{dd_mm_yyyy}/",
        target_date="2026-05-29",
    ) == "https://bop.dipuleon.es/publica/consulta-de-bops/buscador/BOP-29-05-2026/"


def test_build_bop_lleida_html_url_is_latest_landing_request():
    assert (
        build_bop_lleida_html_url(
            "https://ebop.diputaciolleida.cat/bop/",
            target_date="2026-05-29",
        )
        == "https://ebop.diputaciolleida.cat/bop/"
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


def test_build_bop_segovia_html_url_is_landing_request():
    assert (
        build_bop_segovia_html_url("https://www.dipsegovia.es/bop", target_date="2026-05-29")
        == "https://www.dipsegovia.es/bop"
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


def test_build_bop_tarragona_html_url_is_one_date_request():
    assert build_bop_tarragona_html_url(
        "https://aplicacions.dipta.cat/bopt/web/anteriores/{date}",
        target_date="2026-05-29",
    ) == "https://aplicacions.dipta.cat/bopt/web/anteriores/2026-05-29"


def test_build_bop_toledo_html_url_is_one_date_request():
    assert build_bop_toledo_html_url(
        "https://bop.diputoledo.es/webEbop/ebopResumen.jsp?"
        "publication_date={date_ddmmyyyy}&publication_date_to={date_ddmmyyyy}",
        target_date="2026-05-29",
    ) == (
        "https://bop.diputoledo.es/webEbop/ebopResumen.jsp?"
        "publication_date=29%2F05%2F2026&publication_date_to=29%2F05%2F2026"
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


def test_build_bop_zaragoza_html_url_is_latest_landing_request():
    assert (
        build_bop_zaragoza_html_url("https://boletin.dpz.es/BOPZ/", target_date="2026-06-01")
        == "https://boletin.dpz.es/BOPZ/"
    )


def test_build_bop_zamora_html_url_is_latest_landing_request():
    assert (
        build_bop_zamora_html_url(
            "https://www.diputaciondezamora.es/opencms/servicios/BOP/bop/index.html",
            target_date="2026-05-29",
        )
        == "https://www.diputaciondezamora.es/opencms/servicios/BOP/bop/index.html"
    )


def test_build_bopa_html_url_is_one_date_request():
    assert build_bopa_html_url(
        "https://miprincipado.asturias.es/bopa-sumario",
        target_date="2026-05-29",
    ) == (
        "https://miprincipado.asturias.es/bopa-sumario?"
        "p_r_p_summaryDate=29%2F05%2F2026&p_r_p_summaryIsSearch=false"
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


def test_parse_bop_jaen_fixture_emits_metadata_only_records():
    raw = _fixture_bytes("bop_jaen_detail.html")
    page_url = "https://bop.dipujaen.es/bop/29-05-2026"

    result = parse_bop_jaen_html(
        raw,
        source_code="BOP_JAEN",
        page_url=page_url,
        requested_date="2026-05-29",
        discovered_at="2026-05-29T00:00:00Z",
        monitor_run_id="run-jaen",
    )

    assert result.raw_page_hash == hashlib.sha256(raw).hexdigest()
    assert len(result.records) == 1
    record = result.records[0]
    assert record["source_code"] == "BOP_JAEN"
    assert record["entry_id"] == "2553"
    assert record["document_id"] == "BOP-2026-2553"
    assert record["title"] == (
        "Convocatoria de Subvenciones del Area de Agricultura a favor de entidades "
        "sin animo de lucro."
    )
    assert record["published_at"] == "2026-05-29"
    assert record["issue_number"] == "103"
    assert record["summary"] == (
        "Administracion Local - DIPUTACION PROVINCIAL DE JAEN - Area de Agricultura"
    )
    assert record["warnings"] == ["pdf_endpoint_not_downloaded"]
    assert record["candidate_status"] == "not_candidate"
    assert record["evidence_status"] == "not_evidence"
    assert "pdf_url" not in record


def test_parse_bop_burgos_html_emits_announcement_metadata():
    raw = b"""
    <h1 class="title-numberdate">
      <span class="title-number"><a href="/bopbur-2026-100">num. 100</a></span>
      <span class="title-date"><a href="/bopbur-2026-100">viernes, 29 de mayo de 2026</a></span>
    </h1>
    <li id="bopbur-anuncio-202602204" class="bopbur-anuncio bopbur-anuncio-level-4">
      <p>Tablas salariales definitivas para el a&ntilde;o 2025</p>
      <p class="bopbur-filefield-file">
        <a href="/bopbur-2026-100-anuncio-202602204.pdf">
          Anuncio 202602204 (BOPBUR-2026-02204 - 207,08 KB)
        </a>
      </p>
    </li>
    """
    page_url = "http://bopbur.diputaciondeburgos.es/bopbur-2026-100"

    result = parse_bop_burgos_html(
        raw,
        source_code="BOP_BURGOS",
        page_url=page_url,
        requested_date="2026-05-29",
        discovered_at="2026-05-29T00:00:00Z",
        monitor_run_id="run-burgos",
    )

    assert result.raw_page_hash == hashlib.sha256(raw).hexdigest()
    assert len(result.records) == 1
    record = result.records[0]
    assert record["source_code"] == "BOP_BURGOS"
    assert record["entry_id"] == "202602204"
    assert record["document_id"] == "BOPBUR-2026-02204"
    assert record["title"] == "Tablas salariales definitivas para el año 2025"
    assert record["published_at"] == "2026-05-29"
    assert record["issue_number"] == "100"
    assert record["official_url"] == (
        "http://bopbur.diputaciondeburgos.es/bopbur-2026-100-anuncio-202602204.pdf"
    )
    assert record["warnings"] == ["pdf_endpoint_not_downloaded"]
    assert record["candidate_status"] == "not_candidate"
    assert record["evidence_status"] == "not_evidence"
    assert "pdf_url" not in record


def test_parse_bop_araba_alava_html_emits_announcement_metadata():
    raw = b"""
    <a title='Boletin N61' href='../Inicio/SGBO5001.aspx?FechaBotha=29/05/2026'>29</a>
    <div class='titulo_bloque_resultados' id='TitSeccion2'>Municipios</div>
    <div class='titulo_bloque_resultados' id='TitSeccion3'>AYUNTAMIENTO DE ALEGRIA-DULANTZI</div>
    <div class="datos_anuncio">
      <a id="grdAnuncios__ctl9_Hyperlink1"
         href="../Busquedas/Resultado.aspx?File=Boletines/2026/061/2026_061_01490_C.xml&amp;hl="
         target="_blank">Cobro del Impuesto sobre Bienes Inmuebles de naturaleza urbana</a>
      <a class="icono" href="../Boletines/2026/061/2026_061_01490_C.pdf">PDF</a>
    </div>
    """
    page_url = "http://www.araba.eus/botha/Inicio/SGBO5001.aspx?FechaBotha=29%2F05%2F2026"

    result = parse_bop_araba_alava_html(
        raw,
        source_code="BOP_ARABA_ALAVA",
        page_url=page_url,
        requested_date="2026-05-29",
        discovered_at="2026-05-29T00:00:00Z",
        monitor_run_id="run-araba",
    )

    assert result.raw_page_hash == hashlib.sha256(raw).hexdigest()
    assert len(result.records) == 1
    record = result.records[0]
    assert record["source_code"] == "BOP_ARABA_ALAVA"
    assert record["entry_id"] == "01490"
    assert record["document_id"] == "2026_061_01490_C"
    assert record["title"] == "Cobro del Impuesto sobre Bienes Inmuebles de naturaleza urbana"
    assert record["published_at"] == "2026-05-29"
    assert record["issue_number"] == "61"
    assert record["official_url"] == (
        "http://www.araba.eus/botha/Busquedas/Resultado.aspx?"
        "File=Boletines/2026/061/2026_061_01490_C.xml&hl="
    )
    assert record["summary"] == "Municipios - AYUNTAMIENTO DE ALEGRIA-DULANTZI"
    assert record["candidate_status"] == "not_candidate"
    assert record["evidence_status"] == "not_evidence"
    assert "pdf_url" not in record


def test_parse_bop_cadiz_html_emits_announcement_metadata():
    raw = b"""
    <p class="fecha"> Fri May 29 08:00:00 CEST 2026
      <a href="/.boletines_pdf/2026/05_mayo/SU-101_29-05-26.pdf">Sumario PDF</a>
    </p>
    <h2>Boletin numero 101 del ano 2026</h2>
    <div>
      <h3>ADMINISTRACION LOCAL</h3>
      <p><a href="/export/sites/default/.boletines_pdf/2026/05_mayo/BOP101_29-05-26.pdf#page=6">
        <strong>127.737.- Ayuntamiento de Vejer de la Frontera.</strong>
        Delegacion de la autorizacion de matrimonio civil.
      </a></p>
    </div>
    """
    page_url = "https://www.bopcadiz.es/boletin/Boletin-numero-101-del-ano-2026"

    result = parse_bop_cadiz_html(
        raw,
        source_code="BOP_CADIZ",
        page_url=page_url,
        requested_date="2026-05-29",
        discovered_at="2026-05-29T00:00:00Z",
        monitor_run_id="run-cadiz",
    )

    assert result.raw_page_hash == hashlib.sha256(raw).hexdigest()
    assert len(result.records) == 1
    record = result.records[0]
    assert record["source_code"] == "BOP_CADIZ"
    assert record["entry_id"] == "127.737"
    assert record["document_id"] == "127.737"
    assert record["title"] == "Delegacion de la autorizacion de matrimonio civil."
    assert record["published_at"] == "2026-05-29"
    assert record["issue_number"] == "101"
    assert record["summary"] == "ADMINISTRACION LOCAL - Ayuntamiento de Vejer de la Frontera."
    assert record["warnings"] == ["pdf_endpoint_not_downloaded"]
    assert record["candidate_status"] == "not_candidate"
    assert record["evidence_status"] == "not_evidence"
    assert "pdf_url" not in record


def test_parse_bop_ciudad_real_html_emits_announcement_metadata():
    raw = b"""
    <h2>Ultimo Boletin publicado: 29-05-2026</h2>
    <div class="cabecera_bop"><span>Numero 101 - Viernes 29 de Mayo de 2026</span></div>
    <h3 class="admons">DIPUTACION PROVINCIAL</h3><div>
      <p class="clasificaciones">SERVICIO DE PERSONAL</p>
      <ul class="anuncios">
        <li id="1666">
          <p><a href="https://se1.dipucr.es:4443/SIGEM_BuscadorDocsWeb/getDocument.do?entidad=005&amp;doc=7567560">
            Nombramiento de Maestro/a de Albanileria.
          </a><br><span class="nAnuncio">Anuncio N 1666</span>
          - <span class="nPagina">Pag. 4946</span></p>
        </li>
      </ul>
    </div>
    """
    page_url = "https://bop.dipucr.es/bop/2026/05/29"

    result = parse_bop_ciudad_real_html(
        raw,
        source_code="BOP_CIUDAD_REAL",
        page_url=page_url,
        requested_date="2026-05-29",
        discovered_at="2026-05-29T00:00:00Z",
        monitor_run_id="run-ciudad-real",
    )

    assert result.raw_page_hash == hashlib.sha256(raw).hexdigest()
    assert len(result.records) == 1
    record = result.records[0]
    assert record["source_code"] == "BOP_CIUDAD_REAL"
    assert record["entry_id"] == "1666"
    assert record["document_id"] == "7567560"
    assert record["title"] == "Nombramiento de Maestro/a de Albanileria."
    assert record["published_at"] == "2026-05-29"
    assert record["issue_number"] == "101"
    assert record["summary"] == "DIPUTACION PROVINCIAL - SERVICIO DE PERSONAL"
    assert record["warnings"] == ["pdf_endpoint_not_downloaded"]
    assert record["candidate_status"] == "not_candidate"
    assert record["evidence_status"] == "not_evidence"
    assert "pdf_url" not in record


def test_parse_bop_ciudad_real_latin1_html_preserves_accents_and_issue_number():
    raw = """
    <h2>Último Boletín publicado: 01-06-2026</h2>
    <div class="cabecera_bop"><span>Número 102 - Lunes 1 de Junio de 2026</span></div>
    <h3 class="admons">ADMINISTRACIÓN LOCAL</h3><div>
      <p class="clasificaciones">AYUNTAMIENTO DE DAIMIEL</p>
      <ul class="anuncios">
        <li id="1699">
          <p><a href="https://se1.dipucr.es:4443/SIGEM_BuscadorDocsWeb/getDocument.do?entidad=005&amp;doc=7569763">
            Aprobación definitiva de la modificación de créditos.
          </a><br><span class="nAnuncio">Anuncio N 1699</span></p>
        </li>
      </ul>
    </div>
    """.encode("iso-8859-1")
    page_url = "https://bop.dipucr.es/bop/2026/06/01"

    result = parse_bop_ciudad_real_html(
        raw,
        source_code="BOP_CIUDAD_REAL",
        page_url=page_url,
        requested_date="2026-06-01",
        discovered_at="2026-06-01T00:00:00Z",
        monitor_run_id="run-ciudad-real-latin1",
    )

    assert len(result.records) == 1
    record = result.records[0]
    assert record["issue_number"] == "102"
    assert record["title"] == "Aprobación definitiva de la modificación de créditos."
    assert record["summary"] == "ADMINISTRACIÓN LOCAL - AYUNTAMIENTO DE DAIMIEL"


def test_parse_bop_leon_html_emits_bulletin_metadata_only():
    raw = b"""
    <h1><strong>BOP n&uacute;m. 101</strong> del 29/05/2026</h1>
    <div class="cve">BOP-LE-2026-101</div>
    <a href="/export/sites/bop/.galleries/DOCUMENTOS-Sumarios-en-PDF/final.pdf">PDF</a>
    <a href="/export/sites/bop/.galleries/Documentos-BOPs-en-PDF/bop-29_05_2026.pdf">PDF</a>
    """
    page_url = "https://bop.dipuleon.es/publica/consulta-de-bops/buscador/BOP-29-05-2026/"

    result = parse_bop_leon_html(
        raw,
        source_code="BOP_LEON",
        page_url=page_url,
        requested_date="2026-05-29",
        discovered_at="2026-05-29T00:00:00Z",
        monitor_run_id="run-leon",
    )

    assert result.raw_page_hash == hashlib.sha256(raw).hexdigest()
    assert len(result.records) == 1
    record = result.records[0]
    assert record["source_code"] == "BOP_LEON"
    assert record["entry_id"] == "BOP-LE-2026-101"
    assert record["document_id"] == "BOP-LE-2026-101"
    assert "101" in record["title"]
    assert record["published_at"] == "2026-05-29"
    assert record["issue_number"] == "101"
    assert record["official_url"] == page_url
    assert record["warnings"] == ["bulletin_level_only", "pdf_endpoint_not_downloaded"]
    assert record["candidate_status"] == "not_candidate"
    assert record["evidence_status"] == "not_evidence"
    assert "pdf_url" not in record


def test_parse_bop_lleida_fixture_emits_metadata_only_records():
    raw = _fixture_bytes("bop_lleida_latest.html")
    page_url = "https://ebop.diputaciolleida.cat/bop/"

    result = parse_bop_lleida_html(
        raw,
        source_code="BOP_LLEIDA",
        page_url=page_url,
        requested_date="2026-05-29",
        discovered_at="2026-05-29T00:00:00Z",
        monitor_run_id="run-lleida",
    )

    assert result.raw_page_hash == hashlib.sha256(raw).hexdigest()
    assert len(result.records) == 1
    record = result.records[0]
    assert record["source_code"] == "BOP_LLEIDA"
    assert record["entry_id"] == "202610104236"
    assert record["document_id"] == "202610104236"
    assert record["title"] == (
        "4236 - AJUNTAMENT D'ALBESA (ALBESA) - Nomenament funcionaria de carrera"
    )
    assert record["published_at"] == "2026-05-29"
    assert record["issue_number"] == "101/0"
    assert record["summary"] == "Administracio Local - Ajuntaments"
    assert record["warnings"] == ["pdf_endpoint_not_downloaded"]
    assert record["candidate_status"] == "not_candidate"
    assert record["evidence_status"] == "not_evidence"
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


def test_parse_bop_segovia_html_emits_matching_date_card_metadata():
    raw = b"""
    <a href="https://www.dipsegovia.es/bop?p_p_id=as_asac_bulletins_portlet_BulletinsPortlet_INSTANCE_qGil9HCkBMcI&amp;p_p_lifecycle=0&amp;_as_asac_bulletins_portlet_BulletinsPortlet_INSTANCE_qGil9HCkBMcI_mvcPath=%2Fpublisher%2Fdetail.jsp&amp;_as_asac_bulletins_portlet_BulletinsPortlet_INSTANCE_qGil9HCkBMcI_articleId=17714746"
       title="Ir a viernes, 29 de mayo 2026" rel="nofollow">
      <span class="card-subtitle">viernes, 29 de mayo 2026</span>
    </a>
    <a href="https://www.dipsegovia.es/bop?articleId=17799999" title="Ir a lunes, 01 de junio 2026">
      <span class="card-subtitle">lunes, 01 de junio 2026</span>
    </a>
    """
    page_url = "https://www.dipsegovia.es/bop"

    result = parse_bop_segovia_html(
        raw,
        source_code="BOP_SEGOVIA",
        page_url=page_url,
        requested_date="2026-05-29",
        discovered_at="2026-05-29T00:00:00Z",
        monitor_run_id="run-segovia",
    )

    assert result.raw_page_hash == hashlib.sha256(raw).hexdigest()
    assert len(result.records) == 1
    record = result.records[0]
    assert record["source_code"] == "BOP_SEGOVIA"
    assert record["entry_id"] == "17714746"
    assert record["document_id"] == "17714746"
    assert record["title"] == "viernes, 29 de mayo 2026"
    assert record["published_at"] == "2026-05-29"
    assert record["official_url"].endswith("articleId=17714746")
    assert record["warnings"] == ["bulletin_level_only"]
    assert record["candidate_status"] == "not_candidate"
    assert record["evidence_status"] == "not_evidence"


def test_parse_bop_gipuzkoa_html_emits_announcement_metadata():
    raw = b"""
    <title>Boletin Oficial de Gipuzkoa Numero 99 Fecha 29-05-2026</title>
    <div id="sumario"><h2>Boletin 29-05-2026, Numero 99</h2>
    <ul id="secciones">
      <li class="seccion">
        <p>2. ADMINISTRACION DEL TERRITORIO HISTORICO DE GIPUZKOA</p>
        <ul class="organismos">
          <li class="organismo">
            <a name="6212">DEPARTAMENTO DE GOBERNANZA</a>
            <ul class="anuncios">
              <li>
                <div class="titulo_anuncio">Declarar desierto el proceso selectivo.</div>
                <div class="enlace_html"><a class="descarga_html" href="c2603368.htm">HTML</a></div>
                <div class="enlace_pdf"><a class="descarga_pdf" href="c2603368.pdf">PDF</a></div>
              </li>
            </ul>
          </li>
        </ul>
      </li>
    </ul>
    """
    page_url = "https://egoitza.gipuzkoa.eus/gao-bog/castell/bog/2026/05/29/bc260529.htm"

    result = parse_bop_gipuzkoa_html(
        raw,
        source_code="BOP_GIPUZKOA",
        page_url=page_url,
        requested_date="2026-05-29",
        discovered_at="2026-05-29T00:00:00Z",
        monitor_run_id="run-gipuzkoa",
    )

    assert result.raw_page_hash == hashlib.sha256(raw).hexdigest()
    assert len(result.records) == 1
    record = result.records[0]
    assert record["source_code"] == "BOP_GIPUZKOA"
    assert record["entry_id"] == "c2603368"
    assert record["document_id"] == "c2603368"
    assert record["title"] == "Declarar desierto el proceso selectivo."
    assert record["published_at"] == "2026-05-29"
    assert record["issue_number"] == "99"
    assert record["summary"] == (
        "2. ADMINISTRACION DEL TERRITORIO HISTORICO DE GIPUZKOA - "
        "DEPARTAMENTO DE GOBERNANZA"
    )
    assert record["candidate_status"] == "not_candidate"
    assert record["evidence_status"] == "not_evidence"
    assert "pdf_url" not in record


def test_parse_bop_girona_html_emits_pdf_link_metadata_only_records():
    raw = b"""
    <h1>Bop numero: 102/0 - 29/05/2026</h1>
    <h2 class="seccioTau">Administracio local - Ajuntaments</h2>
    <li class="edicte">
      <a href="https://ssl4.ddgi.cat/bopV1/pdf/2026/102/202610204663.pdf"
         target="new" class="linkAjuda">
        4663 - <span>AJUNTAMENT D'AMER</span> - Aprovacio definitiva dels expedients
      </a>
    </li>
    """
    page_url = "https://www.ddgi.cat/bop/"

    result = parse_bop_girona_html(
        raw,
        source_code="BOP_GIRONA",
        page_url=page_url,
        requested_date="2026-05-29",
        discovered_at="2026-05-29T00:00:00Z",
        monitor_run_id="run-girona",
    )

    assert result.raw_page_hash == hashlib.sha256(raw).hexdigest()
    assert len(result.records) == 1
    record = result.records[0]
    assert record["source_code"] == "BOP_GIRONA"
    assert record["entry_id"] == "202610204663"
    assert record["document_id"] == "202610204663"
    assert record["title"] == "Aprovacio definitiva dels expedients"
    assert record["published_at"] == "2026-05-29"
    assert record["issue_number"] == "102"
    assert record["official_url"] == "https://ssl4.ddgi.cat/bopV1/pdf/2026/102/202610204663.pdf"
    assert record["summary"] == "Administracio local - Ajuntaments - AJUNTAMENT D'AMER"
    assert record["warnings"] == ["pdf_endpoint_not_downloaded"]
    assert record["candidate_status"] == "not_candidate"
    assert record["evidence_status"] == "not_evidence"


def test_parse_bop_huesca_html_emits_pdf_link_metadata_only_records():
    raw = b"""
    <strong title="">Ejercicio:</strong> 2026<br />
    <strong title="">Numero:</strong> 101<br />
    <strong title="">Fecha:</strong> 01-06-2026<br />
    <p> 1.&nbsp;&nbsp;<strong>Seccion: ADMINISTRACION LOCAL</strong> </p>
    <p> * <strong>Subseccion: DIPUTACION PROVINCIAL DE HUESCA</strong> </p>
    <p><strong>+&nbsp;2026 / 2267&nbsp;&nbsp;-&nbsp;&nbsp;
      BOLETIN OFICIAL DE LA PROVINCIA</strong></p>
    <p> OTROS<br />
      <em>Puesta en funcionamiento de una nueva plataforma de gestion del BOPH</em><br />
      <a href="/index.php/idbopanuncio.256954/demo.html">Pulse aqui</a> (PDF)
    </p>
    """
    page_url = (
        "https://bop.dphuesca.es/index.php/mod.bopanuncios/mem.ultimoboletin/"
        "idmenu.50004/seccion.portal/chk.b6a0e09090757bcdf5de25060e5c4cf5.html"
    )

    result = parse_bop_huesca_html(
        raw,
        source_code="BOP_HUESCA",
        page_url=page_url,
        requested_date="2026-06-01",
        discovered_at="2026-06-01T00:00:00Z",
        monitor_run_id="run-huesca",
    )

    assert result.raw_page_hash == hashlib.sha256(raw).hexdigest()
    assert len(result.records) == 1
    record = result.records[0]
    assert record["source_code"] == "BOP_HUESCA"
    assert record["entry_id"] == "256954"
    assert record["document_id"] == "256954"
    assert record["title"] == "Puesta en funcionamiento de una nueva plataforma de gestion del BOPH"
    assert record["published_at"] == "2026-06-01"
    assert record["issue_number"] == "101"
    assert record["official_url"].endswith(
        "idbopanuncio.256954/demo.html"
    )
    assert record["summary"] == (
        "ADMINISTRACION LOCAL - DIPUTACION PROVINCIAL DE HUESCA - "
        "BOLETIN OFICIAL DE LA PROVINCIA - OTROS"
    )
    assert record["warnings"] == ["pdf_endpoint_not_downloaded"]
    assert record["candidate_status"] == "not_candidate"
    assert record["evidence_status"] == "not_evidence"


def test_parse_bop_tarragona_html_emits_announcement_metadata():
    raw = b"""
    <time datetime="2026-05-29">viernes <span>29 de mayo</span> de 2026</time>
    <div class="card bg-white mb-4 shadow-sm rounded-0">
      <div class="card-body">
        <h3 class="card-title h6">
          <a href="/bopt/web/anuncio/359557/comissio-paritaria" class="stretched-link">
            GENERALITAT CATALUNYA - EMPRESA I TREBALL - TARRAGONA
          </a>
        </h3>
        <p>Comissio Paritaria del Conveni collectiu de treball</p>
      </div>
    </div>
    """
    page_url = "https://aplicacions.dipta.cat/bopt/web/anteriores/2026-05-29"

    result = parse_bop_tarragona_html(
        raw,
        source_code="BOP_TARRAGONA",
        page_url=page_url,
        requested_date="2026-05-29",
        discovered_at="2026-05-29T00:00:00Z",
        monitor_run_id="run-tarragona",
    )

    assert result.raw_page_hash == hashlib.sha256(raw).hexdigest()
    assert len(result.records) == 1
    record = result.records[0]
    assert record["source_code"] == "BOP_TARRAGONA"
    assert record["entry_id"] == "359557"
    assert record["document_id"] == "359557"
    assert record["title"] == "Comissio Paritaria del Conveni collectiu de treball"
    assert record["published_at"] == "2026-05-29"
    assert record["official_url"] == (
        "https://aplicacions.dipta.cat/bopt/web/anuncio/359557/comissio-paritaria"
    )
    assert record["summary"] == "GENERALITAT CATALUNYA - EMPRESA I TREBALL - TARRAGONA"
    assert record["warnings"] == []
    assert record["candidate_status"] == "not_candidate"
    assert record["evidence_status"] == "not_evidence"


def test_parse_bop_las_palmas_html_emits_bulletin_metadata():
    raw = b"""
    <strong>SUMARIO DEL BOLET&Iacute;N N&ordm; </strong>
    <font color="navy" size="3">64</font>
    <font color="navy" size="3">, DE FECHA </font>
    <font color="navy" size="3">29-5-26</font>
    <a href="../boletines/2026/29-5-26/29-5-26.pdf">Descargar Bolet&iacute;n</a>
    <b><i>EXCMO. AYUNTAMIENTO DE ARRECIFE</i></b><br>
    - Aprobacion definitiva de bases reguladoras<br>
    """
    page_url = (
        "https://www.boplaspalmas.net/nbop2/sumario.php?"
        "codigopub=1&fecha_mas_reciente=2026-05-29"
    )

    result = parse_bop_las_palmas_html(
        raw,
        source_code="BOP_LAS_PALMAS",
        page_url=page_url,
        requested_date="2026-05-29",
        discovered_at="2026-05-29T00:00:00Z",
        monitor_run_id="run-laspalmas",
    )

    assert result.raw_page_hash == hashlib.sha256(raw).hexdigest()
    assert len(result.records) == 1
    record = result.records[0]
    assert record["source_code"] == "BOP_LAS_PALMAS"
    assert record["title"] == "Sumario del boletin 64 de fecha 29-5-26"
    assert record["published_at"] == "2026-05-29"
    assert record["document_id"] == "29-5-26"
    assert record["issue_number"] == "64"
    assert record["official_url"] == (
        "https://www.boplaspalmas.net/boletines/2026/29-5-26/29-5-26.pdf"
    )
    assert record["warnings"] == ["pdf_endpoint_not_downloaded"]
    assert record["candidate_status"] == "not_candidate"
    assert record["evidence_status"] == "not_evidence"


def test_parse_bop_salamanca_html_emits_bulletin_metadata():
    raw = b"""
    <h2>Bolet&iacute;n del d&iacute;a 29/05/2026</h2>
    <h1>BOP</h1>
    <p align="center"><a href="/documentacion/bop/2026/20260529/BOP-SA-20260529-999.pdf">
      Descargar bolet&iacute;n completo
    </a></p>
    <a href="documentos/Modelo-Anexo-tasa-BOP.pdf">Anexo tasa</a>
    <div><strong>SUMARIO</strong></div>
    """
    page_url = (
        "https://sede.diputaciondesalamanca.gob.es/opencms/opencms/sede/BOP/"
        "index.jsp?fechaBoletin=2026-05-29"
    )

    result = parse_bop_salamanca_html(
        raw,
        source_code="BOP_SALAMANCA",
        page_url=page_url,
        requested_date="2026-05-29",
        discovered_at="2026-05-29T00:00:00Z",
        monitor_run_id="run-salamanca",
    )

    assert result.raw_page_hash == hashlib.sha256(raw).hexdigest()
    assert len(result.records) == 1
    record = result.records[0]
    assert record["source_code"] == "BOP_SALAMANCA"
    assert record["title"] == "Boletín del día 29/05/2026"
    assert record["published_at"] == "2026-05-29"
    assert record["document_id"] == "BOP-SA-20260529-999"
    assert record["issue_number"] == "999"
    assert record["official_url"] == (
        "https://sede.diputaciondesalamanca.gob.es/documentacion/bop/2026/20260529/"
        "BOP-SA-20260529-999.pdf"
    )
    assert record["warnings"] == ["pdf_endpoint_not_downloaded"]
    assert record["candidate_status"] == "not_candidate"
    assert record["evidence_status"] == "not_evidence"


def test_parse_bop_santa_cruz_tenerife_html_emits_bulletin_metadata():
    raw = b"""
    <strong>SUMARIO DEL BOLET&Iacute;N N&ordm; </strong>
    <font color="navy" size="3">64</font>
    <font color="navy" size="3">, DE FECHA </font>
    <font color="navy" size="3">29-5-26</font>
    <a href="../boletines/2026/29-5-26/29-5-26.pdf">Descargar Bolet&iacute;n</a>
    <b><i>PUERTOS DE TENERIFE</i></b><br>
    - Anuncio relativo a informacion publica<br>
    """
    page_url = (
        "http://www.bopsantacruzdetenerife.es/bopsc2/sumario.php?"
        "codigopub=1&fecha_mas_reciente=2026-05-29"
    )

    result = parse_bop_santa_cruz_tenerife_html(
        raw,
        source_code="BOP_SANTA_CRUZ_TENERIFE",
        page_url=page_url,
        requested_date="2026-05-29",
        discovered_at="2026-05-29T00:00:00Z",
        monitor_run_id="run-sctfe",
    )

    assert result.raw_page_hash == hashlib.sha256(raw).hexdigest()
    assert len(result.records) == 1
    record = result.records[0]
    assert record["source_code"] == "BOP_SANTA_CRUZ_TENERIFE"
    assert record["title"] == "Sumario del boletin 64 de fecha 29-5-26"
    assert record["published_at"] == "2026-05-29"
    assert record["document_id"] == "29-5-26"
    assert record["issue_number"] == "64"
    assert record["official_url"] == (
        "http://www.bopsantacruzdetenerife.es/boletines/2026/29-5-26/29-5-26.pdf"
    )
    assert record["warnings"] == ["pdf_endpoint_not_downloaded"]
    assert record["candidate_status"] == "not_candidate"
    assert record["evidence_status"] == "not_evidence"


def test_parse_bop_teruel_html_emits_current_bulletin_metadata():
    raw = b"""
    <h2 class="bop-dia">BOP del d&iacute;a</h2>
    <span id="computedFieldfechatexto">29 de Mayo de 2026</span>.
    <br>BOP n&uacute;mero &nbsp;<span id="computedField1">100</span>.
    <a class="ver-boletin"
       href="https://236ws.dpteruel.es/DPT/bopt.nsf/Redireccion?OpenPage&dia=20260529">
       Ver bolet&iacute;n
    </a>
    """
    page_url = "https://236ws.dpteruel.es/DPT/bopt.nsf/inicio.xsp"

    result = parse_bop_teruel_html(
        raw,
        source_code="BOP_TERUEL",
        page_url=page_url,
        requested_date="2026-05-29",
        discovered_at="2026-05-29T00:00:00Z",
        monitor_run_id="run-teruel",
    )

    assert result.raw_page_hash == hashlib.sha256(raw).hexdigest()
    assert len(result.records) == 1
    record = result.records[0]
    assert record["source_code"] == "BOP_TERUEL"
    assert record["title"] == "BOP del dia 29 de Mayo de 2026"
    assert record["published_at"] == "2026-05-29"
    assert record["document_id"] == "20260529"
    assert record["issue_number"] == "100"
    assert record["official_url"] == (
        "https://236ws.dpteruel.es/DPT/bopt.nsf/Redireccion?OpenPage&dia=20260529"
    )
    assert record["warnings"] == ["pdf_endpoint_not_downloaded"]
    assert record["candidate_status"] == "not_candidate"
    assert record["evidence_status"] == "not_evidence"


def test_parse_bop_cuenca_html_emits_matching_date_card_metadata():
    raw = b"""
    <a href="https://www.dipucuenca.es/boletin-oficial-de-la-provincia?p_p_id=as_asac_bulletins_web_BulletinsWebPortlet_INSTANCE_LuthFM11tPwH&amp;p_p_lifecycle=0&amp;_as_asac_bulletins_web_BulletinsWebPortlet_INSTANCE_LuthFM11tPwH_mvcPath=%2Fpublisher%2Fdetail.jsp&amp;_as_asac_bulletins_web_BulletinsWebPortlet_INSTANCE_LuthFM11tPwH_articleId=2102048"
       title="Ir a viernes, 29 de mayo 2026" rel="nofollow">
      <span class="hide-accessible">viernes, 29 de mayo 2026</span>
    </a>
    <div class="card-body">
      <span class="card-text">61</span>
      <a href="https://www.dipucuenca.es/boletin-oficial-de-la-provincia?articleId=2102048">
        <span class="card-subtitle">viernes, 29 de mayo 2026</span>
      </a>
    </div>
    """
    page_url = (
        "https://www.dipucuenca.es/boletin-oficial-de-la-provincia?"
        "p_r_p_startDate=29%2F05%2F2026&p_r_p_endDate=29%2F05%2F2026"
    )

    result = parse_bop_cuenca_html(
        raw,
        source_code="BOP_CUENCA",
        page_url=page_url,
        requested_date="2026-05-29",
        discovered_at="2026-05-29T00:00:00Z",
        monitor_run_id="run-cuenca",
    )

    assert result.raw_page_hash == hashlib.sha256(raw).hexdigest()
    assert len(result.records) == 1
    record = result.records[0]
    assert record["source_code"] == "BOP_CUENCA"
    assert record["entry_id"] == "2102048"
    assert record["document_id"] == "2102048"
    assert record["title"] == "viernes, 29 de mayo 2026"
    assert record["published_at"] == "2026-05-29"
    assert record["issue_number"] == "61"
    assert record["warnings"] == ["bulletin_level_only"]
    assert record["candidate_status"] == "not_candidate"
    assert record["evidence_status"] == "not_evidence"


def test_parse_bop_toledo_html_emits_announcement_metadata():
    raw = b"""
    <h1>Boletin numero 100 publicado el dia 29/05/2026</h1>
    <h3 class="publisherBlock">Anunciante : CENTRO REGIONAL DE LA UNED</h3>
    <div id="26052369>" class="announce">
      <ul class="announceResumenList">
        <li><strong>Numero de insercion : </strong>2397
          <a href="DocGet?id=26052369;0&amp;insert_number=2397&amp;insert_year=2026">Ver anuncio</a>
          <strong>Tipo de anuncio : </strong>Resolucion
        </li>
        <li><strong>Resumen/Asunto : </strong>RECTIFICACION BASES PROCESO SELECTIVO UNED.</li>
      </ul>
    </div>
    """
    page_url = (
        "https://bop.diputoledo.es/webEbop/ebopResumen.jsp?"
        "publication_date=29%2F05%2F2026&publication_date_to=29%2F05%2F2026"
    )

    result = parse_bop_toledo_html(
        raw,
        source_code="BOP_TOLEDO",
        page_url=page_url,
        requested_date="2026-05-29",
        discovered_at="2026-05-29T00:00:00Z",
        monitor_run_id="run-toledo",
    )

    assert result.raw_page_hash == hashlib.sha256(raw).hexdigest()
    assert len(result.records) == 1
    record = result.records[0]
    assert record["source_code"] == "BOP_TOLEDO"
    assert record["entry_id"] == "26052369"
    assert record["document_id"] == "2397"
    assert record["title"] == "RECTIFICACION BASES PROCESO SELECTIVO UNED."
    assert record["published_at"] == "2026-05-29"
    assert record["issue_number"] == "100"
    assert record["official_url"] == (
        "https://bop.diputoledo.es/webEbop/DocGet?id=26052369;0&insert_number=2397&insert_year=2026"
    )
    assert record["summary"] == "CENTRO REGIONAL DE LA UNED - Resolucion"
    assert record["warnings"] == ["pdf_endpoint_not_downloaded"]
    assert record["candidate_status"] == "not_candidate"
    assert record["evidence_status"] == "not_evidence"
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


def test_parse_bop_zaragoza_html_emits_announcement_metadata():
    raw = b"""
    <input type="hidden" name="fechaVista" value="01/06/2026" />
    <input type="hidden" name="numBop" value="122"/>
    <input type="hidden" name="fechaPub" value="lunes 1 de junio de 2026" />
    <h3>Seccion tercera</h3>
    <p class="parrafo" style="margin-bottom:0px">
      DIPUTACION PROVINCIAL DE ZARAGOZA (DPZ).- AREA DE PRESIDENCIA
    </p>
    <p class="parrafo"><a class="enlaceEdicto" href="#"
      onclick="javascript:abreVentanaDetalleEdicto('893727')">
      DECRETO 1467/2026.- ELEVAR A DEFINITIVA LA LISTA PROVISIONAL.
    </a></p>
    """
    page_url = "https://boletin.dpz.es/BOPZ/"

    result = parse_bop_zaragoza_html(
        raw,
        source_code="BOP_ZARAGOZA",
        page_url=page_url,
        requested_date="2026-06-01",
        discovered_at="2026-06-01T00:00:00Z",
        monitor_run_id="run-zaragoza",
    )

    assert result.raw_page_hash == hashlib.sha256(raw).hexdigest()
    assert len(result.records) == 1
    record = result.records[0]
    assert record["source_code"] == "BOP_ZARAGOZA"
    assert record["entry_id"] == "893727"
    assert record["document_id"] == "893727"
    assert record["title"] == "DECRETO 1467/2026.- ELEVAR A DEFINITIVA LA LISTA PROVISIONAL."
    assert record["published_at"] == "2026-06-01"
    assert record["issue_number"] == "122"
    assert record["summary"] == (
        "Seccion tercera - DIPUTACION PROVINCIAL DE ZARAGOZA (DPZ).- AREA DE PRESIDENCIA"
    )
    assert "obtenerContenidoEdicto.do?idEdicto=893727" in record["official_url"]
    assert record["warnings"] == []
    assert record["candidate_status"] == "not_candidate"
    assert record["evidence_status"] == "not_evidence"


def test_parse_bop_zamora_fixture_emits_metadata_only_records():
    raw = _fixture_bytes("bop_zamora_detail.html")
    page_url = (
        "https://www.diputaciondezamora.es/opencms/servicios/BOP/indice-bop/"
        "6256e9b6-5a81-11f1-9953-e5884f57ec76/"
    )

    result = parse_bop_zamora_html(
        raw,
        source_code="BOP_ZAMORA",
        page_url=page_url,
        requested_date="2026-05-29",
        discovered_at="2026-05-29T00:00:00Z",
        monitor_run_id="run-zamora",
    )

    assert result.raw_page_hash == hashlib.sha256(raw).hexdigest()
    assert len(result.records) == 1
    record = result.records[0]
    assert record["source_code"] == "BOP_ZAMORA"
    assert record["entry_id"] == "202601351"
    assert record["document_id"] == "202601351"
    assert record["title"] == (
        "Informacion publica relativa a la solicitud de autorizacion administrativa previa."
    )
    assert record["published_at"] == "2026-05-29"
    assert record["issue_number"] == "63"
    assert record["summary"] == (
        "II. ADMINISTRACION AUTONOMICA - JUNTA DE CASTILLA Y LEON - "
        "Servicio Territorial de Industria"
    )
    assert record["warnings"] == ["pdf_endpoint_not_downloaded"]
    assert record["candidate_status"] == "not_candidate"
    assert record["evidence_status"] == "not_evidence"
    assert "pdf_url" not in record


def test_parse_bopa_fixture_emits_metadata_only_records():
    raw = _fixture_bytes("bopa_summary_2026_05_29.html")
    page_url = (
        "https://miprincipado.asturias.es/bopa-sumario?"
        "p_r_p_summaryDate=29%2F05%2F2026&p_r_p_summaryIsSearch=false"
    )

    result = parse_bopa_html(
        raw,
        source_code="BOPA",
        page_url=page_url,
        requested_date="2026-05-29",
        discovered_at="2026-05-29T00:00:00Z",
        monitor_run_id="run-bopa",
    )

    assert result.raw_page_hash == hashlib.sha256(raw).hexdigest()
    assert len(result.records) == 1
    record = result.records[0]
    assert record["source_code"] == "BOPA"
    assert record["entry_id"] == "2026-04395"
    assert record["document_id"] == "2026-04395"
    assert record["title"] == "Ley del Principado de Asturias 3/2026, de Colegios Profesionales."
    assert record["published_at"] == "2026-05-29"
    assert record["summary"] == (
        "I. Principado de Asturias - DISPOSICIONES GENERALES - "
        "PRESIDENCIA DEL PRINCIPADO DE ASTURIAS"
    )
    assert record["warnings"] == ["pdf_endpoint_not_downloaded"]
    assert record["candidate_status"] == "not_candidate"
    assert record["evidence_status"] == "not_evidence"
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


def test_monitor_new_single_fetch_sources_emit_metadata_only_records():
    cases = {
        "BOP_JAEN": ("2026-05-29", "bop_jaen_detail.html"),
        "BOP_LLEIDA": ("2026-05-29", "bop_lleida_latest.html"),
        "BOPA": ("2026-05-29", "bopa_summary_2026_05_29.html"),
    }

    for source_code, (target_date, fixture_name) in cases.items():
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
            target_date=target_date,
            limit=1,
        )

        assert len(requested_urls) == 1
        assert len(result.records) == 1
        assert result.records[0]["source_code"] == source_code
        assert result.records[0]["candidate_status"] == "not_candidate"
        assert result.records[0]["evidence_status"] == "not_evidence"


def test_monitor_bop_cadiz_uses_landing_when_it_already_contains_summary():
    requested_urls = []
    landing_url = "https://www.bopcadiz.es/"
    source = {
        **get_source("BOP_CADIZ"),
        "access_methods": [{"type": "html", "url": landing_url, "status": "validated"}],
    }

    def fetcher(url: str) -> bytes:
        requested_urls.append(url)
        return b"""
        <p class="fecha"> Fri May 29 08:00:00 CEST 2026</p>
        <h2>Boletin numero 101 del ano 2026</h2>
        <h3>ADMINISTRACION LOCAL</h3>
        <p><a href="/export/sites/default/.boletines_pdf/2026/05_mayo/BOP101_29-05-26.pdf#page=6">
          <strong>127.737.- Ayuntamiento de Vejer de la Frontera.</strong>
          Delegacion de la autorizacion de matrimonio civil.
        </a></p>
        """

    result = monitor_html_source(source, fetcher=fetcher, target_date="2026-05-29", limit=1)

    assert requested_urls == [landing_url]
    assert len(result.records) == 1
    assert result.records[0]["source_code"] == "BOP_CADIZ"
    assert result.records[0]["candidate_status"] == "not_candidate"
    assert result.records[0]["evidence_status"] == "not_evidence"


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


def test_monitor_bop_zamora_fetches_landing_then_matching_issue_detail():
    requested_urls = []
    landing_url = "https://www.diputaciondezamora.es/opencms/servicios/BOP/bop/index.html"
    detail_url = (
        "https://www.diputaciondezamora.es/opencms/servicios/BOP/indice-bop/"
        "6256e9b6-5a81-11f1-9953-e5884f57ec76/"
    )

    def fetcher(url: str) -> bytes:
        requested_urls.append(url)
        if url == landing_url:
            return _fixture_bytes("bop_zamora_landing.html")
        if url == detail_url:
            return _fixture_bytes("bop_zamora_detail.html")
        raise AssertionError(f"unexpected URL: {url}")

    result = monitor_html_source(
        get_source("BOP_ZAMORA"),
        fetcher=fetcher,
        target_date="2026-05-29",
        limit=1,
    )

    assert requested_urls == [landing_url, detail_url]
    assert len(result.records) == 1
    assert result.records[0]["source_code"] == "BOP_ZAMORA"
    assert result.records[0]["candidate_status"] == "not_candidate"
    assert result.records[0]["evidence_status"] == "not_evidence"


def test_monitor_bop_burgos_fetches_date_then_issue_detail():
    requested_urls = []
    landing_url = "http://bopbur.diputaciondeburgos.es/hemeroteca/2026-05-29?mostrar-anuncio=1"
    detail_url = "http://bopbur.diputaciondeburgos.es/bopbur-2026-100"

    def fetcher(url: str) -> bytes:
        requested_urls.append(url)
        if url == landing_url:
            return b'<a href="/bopbur-2026-100">Ver boletin completo</a>'
        if url == detail_url:
            return b"""
            <span class="title-number"><a href="/bopbur-2026-100">num. 100</a></span>
            <span class="title-date">viernes, 29 de mayo de 2026</span>
            <li id="bopbur-anuncio-202602204" class="bopbur-anuncio">
              <p>Tablas salariales</p>
              <a href="/sites/default/files/private/publicado/bopbur-2026-100/anuncio.pdf">
                Anuncio 202602204 (BOPBUR-2026-02204 - 207 KB)
              </a>
            </li>
            """
        raise AssertionError(f"unexpected URL: {url}")

    result = monitor_html_source(
        get_source("BOP_BURGOS"),
        fetcher=fetcher,
        target_date="2026-05-29",
        limit=1,
    )

    assert requested_urls == [landing_url, detail_url]
    assert len(result.records) == 1
    assert result.records[0]["source_code"] == "BOP_BURGOS"
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
    client_options = []

    class FakeResponse:
        url = "https://example.test"
        content = b"<html></html>"

        def raise_for_status(self) -> None:
            return None

    class FakeClient:
        def __init__(self, **kwargs):
            client_options.append(kwargs)
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
    assert client_options[0]["verify"] is not False
    assert client_options[0]["verify"] is not True


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
