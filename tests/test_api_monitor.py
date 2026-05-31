from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path

import pytest

import official_sources.api_monitor as api_monitor
from official_sources.api_monitor import (
    APIMonitorError,
    build_api_entry_hash,
    build_api_monitor_output_path,
    build_bop_caceres_announcements_api_url,
    build_bop_caceres_calendar_api_url,
    build_bop_huelva_api_url,
    build_bopv_api_url,
    build_bor_announcement_api_url,
    build_bor_calendar_api_url,
    build_bor_issue_api_url,
    monitor_api_source,
    parse_bop_caceres_announcements_response,
    parse_bop_caceres_calendar_issue_id,
    parse_bop_huelva_api_response,
    parse_bopv_api_response,
    parse_bor_calendar_issue_number,
    parse_bor_issue_response,
    select_api_access_method,
)
from official_sources.source_coverage import list_monitorable_sources
from official_sources.source_registry import get_source

FIXTURES = Path(__file__).parent / "fixtures"


def _fixture_bytes(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


def test_bopv_api_access_method_exists_in_registry():
    source = get_source("BOPV")
    method = select_api_access_method(source)

    assert method["type"] == "api"
    assert method["status"] == "validated"
    assert method["url"] == "https://api.euskadi.eus/bopv/administrative-acts/{year}/{month}"


def test_bor_api_access_method_exists_in_registry():
    source = get_source("BOR")
    method = select_api_access_method(source)

    assert method["type"] == "api"
    assert method["status"] == "validated"
    assert method["url"] == "https://ias1.larioja.org/boletin/ExportarBoletinServlet"


def test_bop_huelva_api_access_method_exists_in_registry():
    source = get_source("BOP_HUELVA")
    method = select_api_access_method(source)

    assert source["operational_status"] == "monitor_validated"
    assert source["monitor_support"] == "available"
    assert method["type"] == "api"
    assert method["status"] == "validated"
    assert method["url"] == "https://s2.diphuelva.es/lib/bope/anuncios_bop/ajaxAnuncios.php"
    assert source["candidate_creation_allowed"] is False
    assert source["evidence_grade_allowed"] is False


def test_bop_caceres_api_access_method_exists_in_registry():
    source = get_source("BOP_CACERES")
    method = select_api_access_method(source)

    assert source["operational_status"] == "monitor_validated"
    assert source["monitor_support"] == "available"
    assert method["type"] == "api"
    assert method["status"] == "validated"
    assert method["url"] == "https://bop.dip-caceres.es/bop/services"
    assert source["candidate_creation_allowed"] is False
    assert source["evidence_grade_allowed"] is False


def test_build_bor_api_urls_are_single_date_requests():
    base_url = "https://ias1.larioja.org/boletin/ExportarBoletinServlet"

    assert build_bor_calendar_api_url(base_url, target_date="2026-05-29") == (
        "https://ias1.larioja.org/boletin/ExportarBoletinServlet?tipo=3&mes=5&anio=2026"
    )
    assert build_bor_issue_api_url(base_url, target_date="2026-05-29", issue_number="101") == (
        "https://ias1.larioja.org/boletin/ExportarBoletinServlet?"
        "tipo=1&fecha=2026%2F05%2F29&numero=101"
    )
    assert build_bor_announcement_api_url(
        base_url,
        published_at="2026-05-29",
        html_ref="40629535-5-HTML-577687-X",
    ) == (
        "https://ias1.larioja.org/boletin/ExportarBoletinServlet?"
        "tipo=2&fecha=2026%2F05%2F29&referencia=40629535-5-HTML-577687-X"
    )


def test_build_bop_huelva_api_url_is_one_date_request():
    assert build_bop_huelva_api_url(
        "https://s2.diphuelva.es/lib/bope/anuncios_bop/ajaxAnuncios.php",
        target_date="2026-05-29",
    ) == ("https://s2.diphuelva.es/lib/bope/anuncios_bop/ajaxAnuncios.php?tipo=2&fecha=2026-05-29")


def test_build_bop_caceres_api_urls_are_date_and_issue_scoped():
    base_url = "https://bop.dip-caceres.es/bop/services"

    assert build_bop_caceres_calendar_api_url(base_url, target_date="2026-05-28") == (
        "https://bop.dip-caceres.es/bop/services/boletines/bopMesCalendario?mes=5&anio=2026"
    )
    assert build_bop_caceres_announcements_api_url(base_url, issue_id="6072") == (
        "https://bop.dip-caceres.es/bop/services/anuncios/anunciosAnunciantes?idBoletin=6072"
    )


def test_parse_bor_calendar_fixture_resolves_issue_number_for_date():
    assert (
        parse_bor_calendar_issue_number(
            _fixture_bytes("bor_calendar_may_2026.xml"),
            target_date="2026-05-29",
        )
        == "101"
    )
    assert (
        parse_bor_calendar_issue_number(
            _fixture_bytes("bor_calendar_may_2026.xml"),
            target_date="2026-05-30",
        )
        is None
    )


def test_parse_bop_caceres_calendar_fixture_resolves_issue_id_for_date():
    assert (
        parse_bop_caceres_calendar_issue_id(
            _fixture_bytes("bop_caceres_calendar_may_2026.json"),
            target_date="2026-05-28",
        )
        == "6072"
    )
    assert (
        parse_bop_caceres_calendar_issue_id(
            _fixture_bytes("bop_caceres_calendar_may_2026.json"),
            target_date="2026-05-29",
        )
        is None
    )


def test_parse_bor_issue_fixture_emits_metadata_only_records():
    raw = _fixture_bytes("bor_issue_2026_05_29.xml")
    base_url = "https://ias1.larioja.org/boletin/ExportarBoletinServlet"
    api_url = build_bor_issue_api_url(base_url, target_date="2026-05-29", issue_number="101")

    result = parse_bor_issue_response(
        raw,
        source_code="BOR",
        api_url=api_url,
        api_endpoint="/boletin/ExportarBoletinServlet",
        source_base_url=base_url,
        requested_date="2026-05-29",
        discovered_at="2026-05-29T00:00:00Z",
        monitor_run_id="run-bor",
    )

    assert result.raw_response_hash == hashlib.sha256(raw).hexdigest()
    assert len(result.records) == 1
    record = result.records[0]
    assert record["source_code"] == "BOR"
    assert record["api_url"] == api_url
    assert record["api_endpoint"] == "/boletin/ExportarBoletinServlet"
    assert record["title"] == (
        "Correccion de error en la Orden HGS/29/2026 por la que se establecen "
        "bases de ayudas sociales y al estudio"
    )
    assert record["published_at"] == "2026-05-29"
    assert record["document_id"] == "40629535-5-HTML-577687-X"
    assert record["api_id"] == "40629535-5-HTML-577687-X"
    assert record["issue_number"] == "101"
    assert record["official_url"] == (
        "https://ias1.larioja.org/boletin/ExportarBoletinServlet?"
        "tipo=2&fecha=2026%2F05%2F29&referencia=40629535-5-HTML-577687-X"
    )
    assert record["summary"] == "DISPOSICIONES GENERALES - CONSEJERIA DE HACIENDA"
    assert record["warnings"] == ["pdf_endpoint_not_downloaded"]
    assert record["classification_status"] == "unclassified"
    assert record["evidence_status"] == "not_evidence"
    assert record["candidate_status"] == "not_candidate"


def test_parse_minimal_bopv_api_fixture_emits_metadata_only_records():
    raw = _fixture_bytes("bopv_api_month_page.json")
    api_url = build_bopv_api_url(
        "https://api.euskadi.eus/bopv/administrative-acts/{year}/{month}",
        target_date="2026-05-24",
        limit=1,
    )

    result = parse_bopv_api_response(
        raw,
        source_code="BOPV",
        api_url=api_url,
        api_endpoint="/bopv/administrative-acts/{year}/{month}",
        discovered_at="2026-05-24T00:00:00Z",
        monitor_run_id="run-1",
    )

    assert result.raw_response_hash == hashlib.sha256(raw).hexdigest()
    assert len(result.records) == 1
    record = result.records[0]
    assert record["source_code"] == "BOPV"
    assert record["api_url"] == api_url
    assert record["api_endpoint"] == "/bopv/administrative-acts/{year}/{month}"
    assert record["title"].startswith("RESOLUCION 4520/2026")
    assert record["published_at"] == "2026-05-24T00:00:00Z"
    assert record["document_id"] == "2026/05/2104"
    assert record["api_id"] == "2026/05/2104"
    assert record["summary"] == "AUTORIDADES Y PERSONAL - OSAKIDETZA-SERVICIO VASCO DE SALUD"
    assert record["raw_response_hash"] == hashlib.sha256(raw).hexdigest()
    assert record["classification_status"] == "unclassified"
    assert record["evidence_status"] == "not_evidence"
    assert record["candidate_status"] == "not_candidate"
    assert "text" not in record


def test_parse_bop_huelva_fixture_emits_metadata_only_records():
    raw = _fixture_bytes("bop_huelva_ajax.json")
    api_url = build_bop_huelva_api_url(
        "https://s2.diphuelva.es/lib/bope/anuncios_bop/ajaxAnuncios.php",
        target_date="2026-05-29",
    )

    result = parse_bop_huelva_api_response(
        raw,
        source_code="BOP_HUELVA",
        api_url=api_url,
        api_endpoint="/lib/bope/anuncios_bop/ajaxAnuncios.php",
        requested_date="2026-05-29",
        discovered_at="2026-05-29T00:00:00Z",
        monitor_run_id="run-huelva",
    )

    assert result.raw_response_hash == hashlib.sha256(raw).hexdigest()
    assert len(result.records) == 1
    record = result.records[0]
    assert record["source_code"] == "BOP_HUELVA"
    assert record["api_url"] == api_url
    assert record["api_endpoint"] == "/lib/bope/anuncios_bop/ajaxAnuncios.php"
    assert record["title"] == (
        "Resolucion aprobando las bases especificas para una plaza de administrativo"
    )
    assert record["published_at"] == "2026-05-29"
    assert record["document_id"] == "360157"
    assert record["api_id"] == "10326"
    assert record["issue_number"] == "102"
    assert record["official_url"] == (
        "https://s2.diphuelva.es/servicios/bope_web/anuncio/?anuncio=360157"
    )
    assert record["summary"] == (
        "Administracion Local - Organismos Autonomos - Agencia Provincial Tributaria de Huelva"
    )
    assert record["warnings"] == ["pdf_endpoint_not_downloaded"]
    assert record["classification_status"] == "unclassified"
    assert record["evidence_status"] == "not_evidence"
    assert record["candidate_status"] == "not_candidate"
    assert "pdf_url" not in record


def test_parse_bop_caceres_announcements_fixture_emits_metadata_only_records():
    raw = _fixture_bytes("bop_caceres_announcements_6072.json")
    base_url = "https://bop.dip-caceres.es/bop/services"
    api_url = build_bop_caceres_announcements_api_url(base_url, issue_id="6072")

    result = parse_bop_caceres_announcements_response(
        raw,
        source_code="BOP_CACERES",
        api_url=api_url,
        api_endpoint="/anuncios/anunciosAnunciantes",
        requested_date="2026-05-28",
        discovered_at="2026-05-28T00:00:00Z",
        monitor_run_id="run-caceres",
    )

    assert result.raw_response_hash == hashlib.sha256(raw).hexdigest()
    assert len(result.records) == 1
    record = result.records[0]
    assert record["source_code"] == "BOP_CACERES"
    assert record["api_url"] == api_url
    assert record["api_endpoint"] == "/anuncios/anunciosAnunciantes"
    assert record["title"] == (
        "BOP-2026-2386 Convocatoria para la constitucion de una Bolsa de Trabajo Temporal"
    )
    assert record["published_at"] == "2026-05-28"
    assert record["document_id"] == "BOP-2026-2386"
    assert record["api_id"] == "147605"
    assert record["issue_number"] == "100"
    assert record["official_url"] == (
        "https://bop.dip-caceres.es/bop/anuncio.html?csv=BOP-2026-2386"
    )
    assert record["summary"] == (
        "Seccion I - Administracion Local - Provincia - Diputacion Provincial de Caceres"
    )
    assert record["warnings"] == ["pdf_endpoint_not_downloaded"]
    assert record["classification_status"] == "unclassified"
    assert record["evidence_status"] == "not_evidence"
    assert record["candidate_status"] == "not_candidate"
    assert "contenidoHtml" not in record


def test_api_entry_hash_prefers_source_published_at_and_official_url():
    assert (
        build_api_entry_hash(
            source_code="BOPV",
            published_at="2026-05-24T00:00:00Z",
            official_url="https://api.euskadi.eus/bopv/administrative-acts/2026/5/2104?lang=SPANISH",
            api_id="ignored",
        )
        == hashlib.sha256(
            b"BOPV"
            b"2026-05-24T00:00:00Z"
            b"https://api.euskadi.eus/bopv/administrative-acts/2026/5/2104?lang=SPANISH"
        ).hexdigest()
    )


def test_api_entry_hash_falls_back_to_api_id_without_official_url():
    assert (
        build_api_entry_hash(
            source_code="BOPV",
            published_at="2026-05-24T00:00:00Z",
            official_url=None,
            api_id="2026/05/2104",
        )
        == hashlib.sha256(b"BOPV2026/05/2104").hexdigest()
    )


def test_monitor_api_source_fetches_one_bounded_bopv_request():
    requested_urls = []

    def fetcher(url: str) -> bytes:
        requested_urls.append(url)
        return _fixture_bytes("bopv_api_month_page.json")

    result = monitor_api_source(
        get_source("BOPV"),
        fetcher=fetcher,
        target_date="2026-05-24",
        limit=1,
    )

    assert requested_urls == [
        "https://api.euskadi.eus/bopv/administrative-acts/2026/5"
        "?currentPage=1&itemsOfPage=1&lang=SPANISH"
    ]
    assert len(result.records) == 1
    assert result.records[0]["candidate_status"] == "not_candidate"
    assert result.records[0]["evidence_status"] == "not_evidence"


def test_monitor_api_source_fetches_bounded_bor_calendar_then_issue():
    requested_urls = []
    base_url = "https://ias1.larioja.org/boletin/ExportarBoletinServlet"

    def fetcher(url: str) -> bytes:
        requested_urls.append(url)
        if "tipo=3" in url:
            return _fixture_bytes("bor_calendar_may_2026.xml")
        return _fixture_bytes("bor_issue_2026_05_29.xml")

    result = monitor_api_source(
        get_source("BOR"),
        fetcher=fetcher,
        target_date="2026-05-29",
        limit=1,
    )

    assert requested_urls == [
        build_bor_calendar_api_url(base_url, target_date="2026-05-29"),
        build_bor_issue_api_url(base_url, target_date="2026-05-29", issue_number="101"),
    ]
    assert len(result.records) == 1
    assert result.records[0]["candidate_status"] == "not_candidate"
    assert result.records[0]["evidence_status"] == "not_evidence"


def test_monitor_api_source_fetches_one_bounded_bop_huelva_request():
    requested_urls = []

    def fetcher(url: str) -> bytes:
        requested_urls.append(url)
        return _fixture_bytes("bop_huelva_ajax.json")

    result = monitor_api_source(
        get_source("BOP_HUELVA"),
        fetcher=fetcher,
        target_date="2026-05-29",
        limit=1,
    )

    assert requested_urls == [
        "https://s2.diphuelva.es/lib/bope/anuncios_bop/ajaxAnuncios.php?tipo=2&fecha=2026-05-29"
    ]
    assert len(result.records) == 1
    assert result.records[0]["candidate_status"] == "not_candidate"
    assert result.records[0]["evidence_status"] == "not_evidence"


def test_monitor_api_source_fetches_bounded_bop_caceres_calendar_then_announcements():
    requested_urls = []
    base_url = "https://bop.dip-caceres.es/bop/services"

    def fetcher(url: str) -> bytes:
        requested_urls.append(url)
        if "bopMesCalendario" in url:
            return _fixture_bytes("bop_caceres_calendar_may_2026.json")
        return _fixture_bytes("bop_caceres_announcements_6072.json")

    result = monitor_api_source(
        get_source("BOP_CACERES"),
        fetcher=fetcher,
        target_date="2026-05-28",
        limit=1,
    )

    assert requested_urls == [
        build_bop_caceres_calendar_api_url(base_url, target_date="2026-05-28"),
        build_bop_caceres_announcements_api_url(base_url, issue_id="6072"),
    ]
    assert len(result.records) == 1
    assert result.records[0]["candidate_status"] == "not_candidate"
    assert result.records[0]["evidence_status"] == "not_evidence"


def test_api_monitor_refuses_source_without_api_access_method():
    with pytest.raises(APIMonitorError) as exc_info:
        select_api_access_method(get_source("BOCYL"))

    assert "does not have a validated api access method" in str(exc_info.value)


def test_api_monitor_has_no_candidate_evidence_pdf_or_artifact_code_paths():
    source = inspect.getsource(api_monitor)

    assert "create_source_candidate" not in source
    assert "evidence_grade" not in source
    assert "ArtifactDownloader" not in source
    assert ".pdf" not in source.lower()


def test_api_jsonl_output_path_is_source_and_date_scoped(tmp_path):
    assert build_api_monitor_output_path(tmp_path, "BOPV", "2026-05-24") == (
        tmp_path / "BOPV" / "2026-05-24" / "api_discovery.jsonl"
    )


def test_cli_api_monitor_refuses_all_source_runs(capsys):
    from official_sources.cli import run

    exit_code = run(["api", "monitor", "--source", "ALL", "--date", "2026-05-24"])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "one source at a time" in captured.err


def test_cli_api_monitor_refuses_non_api_sources(capsys):
    from official_sources.cli import run

    exit_code = run(["api", "monitor", "--source", "BOCYL", "--date", "2026-05-24"])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "does not have a validated api access method" in captured.err


def test_cli_api_monitor_preview_does_not_write_or_open_repository(tmp_path, monkeypatch, capsys):
    from official_sources import cli

    def fail_open_repository(_db_path: str):
        raise AssertionError("api monitor must not open SQLite")

    monkeypatch.setattr(cli, "_open_repository", fail_open_repository)

    exit_code = cli.run(
        [
            "api",
            "monitor",
            "--source",
            "BOR",
            "--date",
            "2026-05-29",
            "--limit",
            "1",
            "--output-root",
            str(tmp_path),
        ],
        api_fetcher=lambda url: (
            _fixture_bytes("bor_calendar_may_2026.xml")
            if "tipo=3" in url
            else _fixture_bytes("bor_issue_2026_05_29.xml")
        ),
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "mode=preview" in captured.out
    assert "discovery_metadata_only=true" in captured.out
    assert not list(tmp_path.rglob("*.jsonl"))


def test_cli_api_monitor_write_requires_explicit_write_flag_and_writes_jsonl(tmp_path, capsys):
    from official_sources.cli import run

    exit_code = run(
        [
            "api",
            "monitor",
            "--source",
            "BOR",
            "--date",
            "2026-05-29",
            "--limit",
            "1",
            "--write",
            "--output-root",
            str(tmp_path),
        ],
        api_fetcher=lambda url: (
            _fixture_bytes("bor_calendar_may_2026.xml")
            if "tipo=3" in url
            else _fixture_bytes("bor_issue_2026_05_29.xml")
        ),
    )
    captured = capsys.readouterr()
    output_path = tmp_path / "BOR" / "2026-05-29" / "api_discovery.jsonl"

    assert exit_code == 0
    assert f"output_path={output_path}" in captured.out
    records = [json.loads(line) for line in output_path.read_text(encoding="utf-8").splitlines()]
    assert len(records) == 1
    assert records[0]["source_code"] == "BOR"
    assert records[0]["candidate_status"] == "not_candidate"
    assert records[0]["evidence_status"] == "not_evidence"


def test_mcp_source_coverage_sees_api_sources_as_monitorable():
    result = list_monitorable_sources()
    sources = {source["source_code"]: source for source in result["sources"]}

    assert "api" in {method["type"] for method in sources["BOPV"]["access_methods"]}
    assert "api" in {method["type"] for method in sources["BOR"]["access_methods"]}
    assert "api" in {method["type"] for method in sources["BOP_CACERES"]["access_methods"]}
    assert "api" in {method["type"] for method in sources["BOP_HUELVA"]["access_methods"]}
