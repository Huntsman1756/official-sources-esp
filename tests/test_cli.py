from __future__ import annotations

import json
from pathlib import Path

import httpx

from official_sources.integrity.hashing import sha256_bytes
from official_sources.sources.boe.client import BOESummaryNotFoundError
from official_sources.sources.boe.http_policy import BOERequestAudit
from official_sources.storage.database import connect, initialize_database
from official_sources.storage.repository import OfficialSourcesRepository


def _fixture_bytes(name: str) -> bytes:
    return (Path(__file__).parent / "fixtures" / name).read_bytes()


def _artifact_client(payloads: dict[str, bytes]) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=payloads[str(request.url)])

    return httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=False, timeout=5.0)


def _seed_document(db_path: Path) -> dict:
    connection = connect(str(db_path))
    initialize_database(connection)
    repository = OfficialSourcesRepository(connection)
    source = repository.ensure_official_source_boe()
    return repository.upsert_document(
        source_id=source["id"],
        external_id="BOE-A-2024-11111",
        publication_date="2024-05-29",
        title="Document with artifacts",
        url_xml="https://www.boe.es/diario_boe/xml.php?id=BOE-A-2024-11111",
        url_html="https://www.boe.es/diario_boe/txt.php?id=BOE-A-2024-11111",
        url_pdf="https://www.boe.es/boe/dias/2024/05/29/pdfs/BOE-A-2024-11111.pdf",
    )


def _seed_boja_document(db_path: Path, *, url_pdf: str | None = None) -> dict:
    connection = connect(str(db_path))
    initialize_database(connection)
    repository = OfficialSourcesRepository(connection)
    source = repository.ensure_official_source_boja()
    return repository.upsert_document(
        source_id=source["id"],
        external_id="BOJA:disposition.2026.94.5",
        publication_date="2026-05-19",
        title="BOJA scholarship document",
        department="Universidades",
        section="1. Disposiciones generales",
        url_pdf=url_pdf,
    )


def _seed_dogv_document(
    db_path: Path,
    *,
    external_id: str = "DOGV:DOGV-C-2026-16062",
    url_pdf: str | None = "https://dogv.gva.es/datos/2026/05/20/pdf/2026_16062_es.pdf",
) -> dict:
    connection = connect(str(db_path))
    initialize_database(connection)
    repository = OfficialSourcesRepository(connection)
    source = repository.ensure_official_source_dogv()
    return repository.upsert_document(
        source_id=source["id"],
        external_id=external_id,
        publication_date="2026-05-20",
        title="DOGV scholarship document",
        department="Universitat Politecnica de Valencia",
        section="III. ACTOS ADMINISTRATIVOS / B) SUBVENCIONES Y BECAS",
        url_html="https://dogv.gva.es/es/resultat-dogv?signatura=2026/16062",
        url_xml="https://dogv.gva.es/dogv-portal/export/disposicion/xml/dinamico/477349?lang=es",
        url_pdf=url_pdf,
    )


def _seed_bocyl_document(
    db_path: Path,
    *,
    external_id: str = "BOCYL:BOCYL-D-15052026-91-8",
    url_html: str | None = "http://bocyl.jcyl.es/html/2026/05/15/html/BOCYL-D-15052026-91-8.do",
    url_xml: str | None = "http://bocyl.jcyl.es/xml/BOCYL-D-15052026-91-8.xml",
    url_pdf: str | None = "http://bocyl.jcyl.es/pdf/BOCYL-D-15052026-91-8.pdf",
) -> dict:
    connection = connect(str(db_path))
    initialize_database(connection)
    repository = OfficialSourcesRepository(connection)
    source = repository.ensure_official_source_bocyl()
    return repository.upsert_document(
        source_id=source["id"],
        external_id=external_id,
        publication_date="2026-05-15",
        title="BOCYL scholarship document",
        department="UNIVERSIDAD DE SALAMANCA",
        section="III. OTRAS DISPOSICIONES",
        url_html=url_html,
        url_xml=url_xml,
        url_pdf=url_pdf,
    )


def _seed_borm_document(
    db_path: Path,
    *,
    external_id: str = "BORM:A-140526-2138",
    url_pdf: str | None = "https://www.borm.es/services/anuncio/842820/pdf",
) -> dict:
    connection = connect(str(db_path))
    initialize_database(connection)
    repository = OfficialSourcesRepository(connection)
    source = repository.ensure_official_source_borm()
    return repository.upsert_document(
        source_id=source["id"],
        external_id=external_id,
        publication_date="2026-05-14",
        title="BORM youth mobility aid document",
        department="Consejeria de Turismo, Cultura, Juventud y Deportes",
        section="I. Comunidad Autonoma",
        url_html="https://www.borm.es/#/home/anuncio/14-05-2026/2138",
        url_pdf=url_pdf,
    )


def test_cli_help_works(capsys):
    from official_sources.cli import run

    exit_code = run(["--help"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "ingest-boe-summary" in captured.out
    assert "download-source-artifacts" in captured.out
    assert "download-boe-artifacts" in captured.out


def test_download_source_artifacts_help_lists_dogv(capsys):
    from official_sources.cli import run

    exit_code = run(["download-source-artifacts", "--help"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "DOGV" in captured.out
    assert "--candidate-ids" in captured.out
    assert "--types" in captured.out


def test_download_source_artifacts_help_lists_bocyl(capsys):
    from official_sources.cli import run

    exit_code = run(["download-source-artifacts", "--help"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "BOCYL" in captured.out


def test_download_source_artifacts_help_lists_borm(capsys):
    from official_sources.cli import run

    exit_code = run(["download-source-artifacts", "--help"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "BORM" in captured.out


def test_cli_invalid_date_rejected(tmp_path, capsys):
    from official_sources.cli import run

    exit_code = run(
        ["--db-path", str(tmp_path / "db.sqlite"), "ingest-boe-summary", "--date", "20240529"]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "YYYY-MM-DD" in captured.err


def test_ingest_boe_summary_creates_ingestion_run(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    exit_code = run(
        ["--db-path", str(db_path), "ingest-boe-summary", "--date", "2024-05-29"],
        summary_fetcher=lambda _date: _fixture_bytes("boe_summary_20240529.json"),
    )

    connection = connect(str(db_path))
    repository = OfficialSourcesRepository(connection)
    run_record = repository.get_latest_ingestion_run("BOE", "2024-05-29")
    captured = capsys.readouterr()
    assert exit_code == 0
    assert run_record["status"] == "success"
    assert "documents_fetched=1" in captured.out


def test_ingest_boe_summary_records_retry_and_throttle_information(tmp_path):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"

    class Fetcher:
        retry_count = 2
        throttle_triggered = True
        last_http_status = 200

        def __call__(self, _date: str) -> bytes:
            return _fixture_bytes("boe_summary_20240529.json")

    exit_code = run(
        ["--db-path", str(db_path), "ingest-boe-summary", "--date", "2024-05-29"],
        summary_fetcher=Fetcher(),
    )

    connection = connect(str(db_path))
    repository = OfficialSourcesRepository(connection)
    run_record = repository.get_latest_ingestion_run("BOE", "2024-05-29")
    assert exit_code == 0
    assert run_record["retry_count"] == 2
    assert run_record["throttle_triggered"] == 1
    assert run_record["last_http_status"] == 200


def test_ingest_boe_summary_404_exits_zero_and_reports_no_publication(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"

    def not_found_fetcher(_date: str) -> bytes:
        raise BOESummaryNotFoundError(
            "2026-05-17",
            BOERequestAudit(retry_count=0, throttle_triggered=False, last_http_status=404),
        )

    exit_code = run(
        ["--db-path", str(db_path), "ingest-boe-summary", "--date", "2026-05-17"],
        summary_fetcher=not_found_fetcher,
    )

    connection = connect(str(db_path))
    repository = OfficialSourcesRepository(connection)
    run_record = repository.get_latest_ingestion_run("BOE", "2026-05-17")
    captured = capsys.readouterr()
    assert exit_code == 0
    assert run_record["status"] == "no_publication"
    assert run_record["last_http_status"] == 404
    assert run_record["retry_count"] == 0
    assert run_record["throttle_triggered"] == 0
    assert "status=no_publication" in captured.out
    assert "last_http_status=404" in captured.out


def test_ingest_boe_summary_non_sunday_404_exits_nonzero_and_reports_failed(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"

    def not_found_fetcher(_date: str) -> bytes:
        raise BOESummaryNotFoundError(
            "2025-01-01",
            BOERequestAudit(retry_count=0, throttle_triggered=False, last_http_status=404),
        )

    exit_code = run(
        ["--db-path", str(db_path), "ingest-boe-summary", "--date", "2025-01-01"],
        summary_fetcher=not_found_fetcher,
    )

    connection = connect(str(db_path))
    repository = OfficialSourcesRepository(connection)
    run_record = repository.get_latest_ingestion_run("BOE", "2025-01-01")
    captured = capsys.readouterr()
    assert exit_code == 1
    assert run_record["status"] == "failed"
    assert run_record["last_http_status"] == 404
    assert "status=failed" in captured.out
    assert "last_http_status=404" in captured.out


def test_ingest_monitor_date_materializes_rss_records(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    command = [
        "--db-path",
        str(db_path),
        "ingest-monitor-date",
        "--source",
        "BOIB",
        "--date",
        "2026-05-24",
        "--limit",
        "1",
    ]
    exit_code = run(
        command,
        rss_fetcher=lambda _url: _fixture_bytes("rss_monitor_minimal.xml"),
    )

    connection = connect(str(db_path))
    document = connection.execute(
        """
        SELECT
            s.code,
            s.region_code,
            d.external_id,
            d.publication_date,
            d.url_html,
            d.raw_metadata_json
        FROM official_documents d
        JOIN official_sources s ON s.id = d.source_id
        WHERE s.code = 'BOIB'
        """
    ).fetchone()
    run_record = OfficialSourcesRepository(connection).get_latest_ingestion_run(
        "BOIB", "2026-05-24"
    )
    captured = capsys.readouterr()
    assert exit_code == 0
    assert document["code"] == "BOIB"
    assert document["region_code"] == "ES-IB"
    assert document["external_id"].startswith("BOIB:")
    assert document["publication_date"] == "2026-05-22"
    assert document["url_html"]
    assert run_record["documents_new"] == 1
    raw_metadata = json.loads(document["raw_metadata_json"])
    assert raw_metadata["command"] == "ingest-monitor-date"
    assert raw_metadata["ingestion_run_id"] == run_record["id"]
    assert raw_metadata["monitor_kind"] == "rss"
    assert raw_metadata["monitor_target_date"] == "2026-05-24"
    assert raw_metadata["operator_controlled"] is True
    assert raw_metadata["monitor_record"]["source_code"] == "BOIB"
    assert "db_path=" in captured.out
    assert "writes=sqlite_materialization" in captured.out
    assert "ingestion_run_id=" in captured.out
    assert "sources_upserted=1" in captured.out
    assert "source_created=true" in captured.out
    assert "documents_upserted=1" in captured.out
    assert "candidate_creation_allowed=false" in captured.out
    assert "evidence_created=false" in captured.out
    assert "artifact_downloads=false" in captured.out
    assert "product_writes=false" in captured.out
    assert "registry_config_mutated=false" in captured.out

    second_exit_code = run(
        command,
        rss_fetcher=lambda _url: _fixture_bytes("rss_monitor_minimal.xml"),
    )
    second_run_record = OfficialSourcesRepository(connection).get_latest_ingestion_run(
        "BOIB", "2026-05-24"
    )
    document_count = connection.execute(
        """
        SELECT COUNT(*)
        FROM official_documents d
        JOIN official_sources s ON s.id = d.source_id
        WHERE s.code = 'BOIB'
        """
    ).fetchone()[0]
    second_captured = capsys.readouterr()
    assert second_exit_code == 0
    assert document_count == 1
    assert second_run_record["documents_new"] == 0
    assert second_run_record["documents_updated"] == 1
    assert "source_created=false" in second_captured.out
    assert "documents_new=0" in second_captured.out
    assert "documents_updated=1" in second_captured.out
    assert "documents_upserted=1" in second_captured.out


def test_ingest_monitor_date_reports_partial_failure_counts(tmp_path, capsys, monkeypatch):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    feed = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>BOIB</title>
    <link>https://www.caib.es/eboibfront/</link>
    <description>BOIB test feed</description>
    <item>
      <title>First monitor record</title>
      <link>https://www.caib.es/eboibfront/record-1</link>
      <description>First metadata-only record.</description>
      <pubDate>Fri, 22 May 2026 18:05:45 GMT</pubDate>
      <guid>https://www.caib.es/eboibfront/record-1</guid>
    </item>
    <item>
      <title>Second monitor record</title>
      <link>https://www.caib.es/eboibfront/record-2</link>
      <description>Second metadata-only record.</description>
      <pubDate>Fri, 22 May 2026 19:05:45 GMT</pubDate>
      <guid>https://www.caib.es/eboibfront/record-2</guid>
    </item>
  </channel>
</rss>
"""
    original_upsert_document = OfficialSourcesRepository.upsert_document
    call_count = 0

    def flaky_upsert_document(self, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 2:
            raise RuntimeError("simulated second document failure")
        return original_upsert_document(self, **kwargs)

    monkeypatch.setattr(OfficialSourcesRepository, "upsert_document", flaky_upsert_document)

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "ingest-monitor-date",
            "--source",
            "BOIB",
            "--date",
            "2026-05-24",
            "--limit",
            "2",
        ],
        rss_fetcher=lambda _url: feed,
    )

    connection = connect(str(db_path))
    run_record = OfficialSourcesRepository(connection).get_latest_ingestion_run(
        "BOIB", "2026-05-24"
    )
    document_count = connection.execute(
        """
        SELECT COUNT(*)
        FROM official_documents d
        JOIN official_sources s ON s.id = d.source_id
        WHERE s.code = 'BOIB'
        """
    ).fetchone()[0]
    captured = capsys.readouterr()
    assert exit_code == 1
    assert document_count == 1
    assert run_record["status"] == "failed"
    assert run_record["documents_fetched"] == 2
    assert run_record["documents_new"] == 1
    assert run_record["documents_updated"] == 0
    assert "documents_new=1" in captured.out
    assert "documents_updated=0" in captured.out
    assert "documents_upserted=1" in captured.out
    assert "partial_materialization=true" in captured.out
    assert "failure_record_index=2" in captured.out
    assert "error_message=record_index=2:" in captured.out


def test_ingest_monitor_date_materializes_html_records(tmp_path):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "ingest-monitor-date",
            "--source",
            "BOPA",
            "--date",
            "2026-05-29",
            "--limit",
            "1",
        ],
        html_fetcher=lambda _url: _fixture_bytes("bopa_summary_2026_05_29.html"),
    )

    connection = connect(str(db_path))
    document = connection.execute(
        """
        SELECT s.region_code, d.external_id, d.publication_date, d.title, d.url_pdf, d.url_html
        FROM official_documents d
        JOIN official_sources s ON s.id = d.source_id
        WHERE s.code = 'BOPA'
        """
    ).fetchone()
    assert exit_code == 0
    assert document["region_code"] == "ES-AS"
    assert document["external_id"] == "BOPA:2026-04395"
    assert document["publication_date"] == "2026-05-29"
    assert document["title"]
    assert document["url_pdf"] or document["url_html"]


def test_ingest_monitor_date_records_docm_html_snapshot_file(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    raw = _fixture_bytes("docm_summary_2026_05_29.html")
    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "ingest-monitor-date",
            "--source",
            "DOCM",
            "--date",
            "2026-05-29",
            "--limit",
            "1",
        ],
        html_fetcher=lambda _url: raw,
    )

    connection = connect(str(db_path))
    repository = OfficialSourcesRepository(connection)
    document = connection.execute(
        """
        SELECT d.id, d.external_id, d.publication_date, d.url_html
        FROM official_documents d
        JOIN official_sources s ON s.id = d.source_id
        WHERE s.code = 'DOCM'
        """
    ).fetchone()
    files = repository.list_document_files(document["id"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert document["external_id"] == "DOCM:2026/4101"
    assert document["publication_date"] == "2026-05-29"
    assert document["url_html"] == (
        "https://docm.jccm.es/docm/verArchivoHtml.do?"
        "ruta=2026/05/29/html/2026_4101.html&tipo=rutaDocm"
    )
    assert len(files) == 1
    file_record = files[0]
    assert file_record["file_type"] == "raw_api_response"
    assert file_record["official_url"] == (
        "https://docm.jccm.es/docm/cambiarBoletin.do?fecha=20260529"
    )
    assert file_record["media_type"] == "text/html"
    assert file_record["size_bytes"] == len(raw)
    assert file_record["sha256"] == sha256_bytes(raw)
    assert file_record["source_snapshot_hash"] == sha256_bytes(raw)
    integrity_checks = repository.list_integrity_checks(file_record["id"])
    assert len(integrity_checks) == 1
    assert integrity_checks[0]["ingestion_run_id"] is not None
    assert integrity_checks[0]["changed"] == 0
    assert integrity_checks[0]["change_reason"] == "new_file"
    assert "artifact_downloads=false" in captured.out
    assert "evidence_created=false" in captured.out
    assert "candidate_creation_allowed=false" in captured.out


def test_ingest_monitor_date_records_bopa_html_snapshot_file(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    raw = _fixture_bytes("bopa_summary_2026_05_29.html")
    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "ingest-monitor-date",
            "--source",
            "BOPA",
            "--date",
            "2026-05-29",
            "--limit",
            "1",
        ],
        html_fetcher=lambda _url: raw,
    )

    connection = connect(str(db_path))
    repository = OfficialSourcesRepository(connection)
    document = connection.execute(
        """
        SELECT d.id, d.external_id, d.publication_date, d.url_html
        FROM official_documents d
        JOIN official_sources s ON s.id = d.source_id
        WHERE s.code = 'BOPA'
        """
    ).fetchone()
    files = repository.list_document_files(document["id"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert document["external_id"] == "BOPA:2026-04395"
    assert document["publication_date"] == "2026-05-29"
    assert document["url_html"]
    assert len(files) == 1
    file_record = files[0]
    assert file_record["file_type"] == "raw_api_response"
    assert file_record["official_url"] == (
        "https://miprincipado.asturias.es/bopa-sumario?"
        "p_r_p_summaryDate=29%2F05%2F2026&p_r_p_summaryIsSearch=false"
    )
    assert file_record["media_type"] == "text/html"
    assert file_record["size_bytes"] == len(raw)
    assert file_record["sha256"] == sha256_bytes(raw)
    assert file_record["source_snapshot_hash"] == sha256_bytes(raw)
    integrity_checks = repository.list_integrity_checks(file_record["id"])
    assert len(integrity_checks) == 1
    assert integrity_checks[0]["ingestion_run_id"] is not None
    assert integrity_checks[0]["changed"] == 0
    assert integrity_checks[0]["change_reason"] == "new_file"
    assert "artifact_downloads=false" in captured.out
    assert "evidence_created=false" in captured.out
    assert "candidate_creation_allowed=false" in captured.out


def test_ingest_monitor_date_materializes_api_records(tmp_path):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"

    def api_fetcher(url: str) -> bytes:
        if "tipo=3" in url:
            return _fixture_bytes("bor_calendar_may_2026.xml")
        return _fixture_bytes("bor_issue_2026_05_29.xml")

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "ingest-monitor-date",
            "--source",
            "BOR",
            "--date",
            "2026-05-29",
            "--limit",
            "1",
        ],
        api_fetcher=api_fetcher,
    )

    connection = connect(str(db_path))
    document = connection.execute(
        """
        SELECT s.region_code, d.external_id, d.publication_date, d.department, d.section, d.url_html
        FROM official_documents d
        JOIN official_sources s ON s.id = d.source_id
        WHERE s.code = 'BOR'
        """
    ).fetchone()
    assert exit_code == 0
    assert document["region_code"] == "ES-RI"
    assert document["external_id"] == "BOR:40629535-5-HTML-577687-X"
    assert document["publication_date"] == "2026-05-29"
    assert document["department"] == "CONSEJERIA DE HACIENDA"
    assert document["section"] == "DISPOSICIONES GENERALES"
    assert document["url_html"]


def test_status_reports_no_publication_and_last_http_status(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"

    def not_found_fetcher(_date: str) -> bytes:
        raise BOESummaryNotFoundError(
            "2026-05-17",
            BOERequestAudit(retry_count=0, throttle_triggered=False, last_http_status=404),
        )

    run(
        ["--db-path", str(db_path), "ingest-boe-summary", "--date", "2026-05-17"],
        summary_fetcher=not_found_fetcher,
    )
    capsys.readouterr()

    exit_code = run(["--db-path", str(db_path), "status", "--date", "2026-05-17"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "ingestion_status=no_publication" in captured.out
    assert "last_http_status=404" in captured.out
    assert "summary_ingestion_status=no_publication" in captured.out
    assert "summary_last_http_status=404" in captured.out
    assert "documents=0" in captured.out


def test_status_reports_summary_failure_without_http_status(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"

    def failing_fetcher(_date: str) -> bytes:
        raise RuntimeError("network unavailable")

    run(
        ["--db-path", str(db_path), "ingest-boe-summary", "--date", "2024-05-29"],
        summary_fetcher=failing_fetcher,
    )
    capsys.readouterr()

    exit_code = run(["--db-path", str(db_path), "status", "--date", "2024-05-29"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "summary_ingestion_status=failed" in captured.out
    assert "summary_last_http_status=none" in captured.out


def test_download_boe_artifacts_skips_after_no_publication(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    artifact_dir = tmp_path / "artifacts"
    calls = 0

    def not_found_fetcher(_date: str) -> bytes:
        raise BOESummaryNotFoundError(
            "2026-05-17",
            BOERequestAudit(retry_count=0, throttle_triggered=False, last_http_status=404),
        )

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, content=b"unused", request=request)

    artifact_client = httpx.Client(transport=httpx.MockTransport(handler))
    run(
        ["--db-path", str(db_path), "ingest-boe-summary", "--date", "2026-05-17"],
        summary_fetcher=not_found_fetcher,
    )
    capsys.readouterr()

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "--artifact-dir",
            str(artifact_dir),
            "download-boe-artifacts",
            "--date",
            "2026-05-17",
            "--types",
            "xml,html",
        ],
        artifact_client=artifact_client,
    )

    connection = connect(str(db_path))
    repository = OfficialSourcesRepository(connection)
    latest = repository.get_latest_ingestion_run("BOE", "2026-05-17")
    download_counts = repository.count_artifact_download_attempts_by_date("2026-05-17")
    captured = capsys.readouterr()
    assert exit_code == 0
    assert calls == 0
    assert latest["status"] == "no_publication"
    assert sum(download_counts.values()) == 0
    assert "status=no_publication" in captured.out
    assert "last_http_status=404" in captured.out


def test_ingest_boe_summary_500_after_retries_still_fails(tmp_path):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"

    def server_error_fetcher(_date: str) -> bytes:
        request = httpx.Request("GET", "https://www.boe.es/datosabiertos/api/boe/sumario/20260517")
        response = httpx.Response(500, request=request)
        exc = httpx.HTTPStatusError("server error", request=request, response=response)
        exc.retry_count = 5
        exc.throttle_triggered = True
        raise exc

    exit_code = run(
        ["--db-path", str(db_path), "ingest-boe-summary", "--date", "2026-05-17"],
        summary_fetcher=server_error_fetcher,
    )

    connection = connect(str(db_path))
    repository = OfficialSourcesRepository(connection)
    run_record = repository.get_latest_ingestion_run("BOE", "2026-05-17")
    assert exit_code == 1
    assert run_record["status"] == "failed"
    assert run_record["last_http_status"] == 500
    assert run_record["retry_count"] == 5
    assert run_record["throttle_triggered"] == 1


def test_ingest_boe_summary_malformed_200_still_fails(tmp_path):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"

    class MalformedFetcher:
        retry_count = 0
        throttle_triggered = False
        last_http_status = 200

        def __call__(self, _date: str) -> bytes:
            return b'{"data":{"sumario":{"metadatos":{"fecha_publicacion":"bad"}}}}'

    exit_code = run(
        ["--db-path", str(db_path), "ingest-boe-summary", "--date", "2026-05-17"],
        summary_fetcher=MalformedFetcher(),
    )

    connection = connect(str(db_path))
    repository = OfficialSourcesRepository(connection)
    run_record = repository.get_latest_ingestion_run("BOE", "2026-05-17")
    assert exit_code == 1
    assert run_record["status"] == "failed"
    assert run_record["last_http_status"] == 200


def test_download_boe_artifacts_downloads_xml_html_and_pdf(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    artifact_dir = tmp_path / "artifacts"
    document = _seed_document(db_path)
    client = _artifact_client(
        {
            document["url_xml"]: _fixture_bytes("boe_document.xml"),
            document["url_html"]: _fixture_bytes("boe_document.html"),
            document["url_pdf"]: _fixture_bytes("boe_document.pdf"),
        }
    )

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "--artifact-dir",
            str(artifact_dir),
            "download-boe-artifacts",
            "--document-ids",
            str(document["id"]),
            "--types",
            "xml,html,pdf",
        ],
        artifact_client=client,
    )

    connection = connect(str(db_path))
    repository = OfficialSourcesRepository(connection)
    stored = repository.list_document_files(document["id"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert {item["file_type"] for item in stored} == {"xml", "html", "pdf"}
    assert "downloaded=3" in captured.out
    assert (artifact_dir / "boe" / "2024" / "05" / "29" / document["external_id"]).exists()


def test_download_boe_artifacts_candidate_ids_download_only_selected_documents(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    artifact_dir = tmp_path / "artifacts"
    connection = connect(str(db_path))
    initialize_database(connection)
    repository = OfficialSourcesRepository(connection)
    source = repository.ensure_official_source_boe()
    selected = repository.upsert_document(
        source_id=source["id"],
        external_id="BOE-A-2024-11111",
        publication_date="2024-05-29",
        title="Selected",
        url_xml="https://www.boe.es/diario_boe/xml.php?id=BOE-A-2024-11111",
        url_html="https://www.boe.es/diario_boe/txt.php?id=BOE-A-2024-11111",
        url_pdf="https://www.boe.es/boe/dias/2024/05/29/pdfs/BOE-A-2024-11111.pdf",
    )
    other = repository.upsert_document(
        source_id=source["id"],
        external_id="BOE-A-2024-22222",
        publication_date="2024-05-29",
        title="Other",
        url_xml="https://www.boe.es/diario_boe/xml.php?id=BOE-A-2024-22222",
        url_html="https://www.boe.es/diario_boe/txt.php?id=BOE-A-2024-22222",
    )
    candidate = repository.create_source_candidate(
        document_id=selected["id"],
        project_key="la-ayuda",
        candidate_type="keyword_match",
        extraction_status="raw_detected",
        evidence_level="metadata_keyword_match",
        matched_fields={"keywords": ["ayudas"]},
    )
    seen_urls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_urls.append(str(request.url))
        return httpx.Response(200, content=b"<document>ok</document>", request=request)

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "--artifact-dir",
            str(artifact_dir),
            "download-boe-artifacts",
            "--candidate-ids",
            str(candidate["id"]),
            "--types",
            "xml,html",
        ],
        artifact_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    captured = capsys.readouterr()
    selected_files = repository.list_document_files(selected["id"])
    other_files = repository.list_document_files(other["id"])
    assert exit_code == 0
    assert len(seen_urls) == 2
    assert selected["url_xml"] in seen_urls
    assert selected["url_html"] in seen_urls
    assert selected["url_pdf"] not in seen_urls
    assert {item["file_type"] for item in selected_files} == {"xml", "html"}
    assert other_files == []
    assert "selected_documents=1" in captured.out
    assert "downloaded=2" in captured.out


def test_download_boe_artifacts_document_ids_default_to_xml_html_not_pdf(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    artifact_dir = tmp_path / "artifacts"
    document = _seed_document(db_path)
    seen_urls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_urls.append(str(request.url))
        return httpx.Response(200, content=b"<document>ok</document>", request=request)

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "--artifact-dir",
            str(artifact_dir),
            "download-boe-artifacts",
            "--document-ids",
            str(document["id"]),
        ],
        artifact_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    connection = connect(str(db_path))
    repository = OfficialSourcesRepository(connection)
    stored = repository.list_document_files(document["id"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert document["url_xml"] in seen_urls
    assert document["url_html"] in seen_urls
    assert document["url_pdf"] not in seen_urls
    assert {item["file_type"] for item in stored} == {"xml", "html"}
    assert "artifact_types=xml,html" in captured.out


def test_download_boe_artifacts_supports_scoped_boja_pdf_candidate_download(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    artifact_dir = tmp_path / "artifacts"
    pdf_url = "https://www.juntadeandalucia.es/eboja/2026/94/BOJA26-094-00005.pdf"
    document = _seed_boja_document(db_path, url_pdf=pdf_url)
    connection = connect(str(db_path))
    repository = OfficialSourcesRepository(connection)
    candidate = repository.create_source_candidate(
        document_id=document["id"],
        project_key="boja-ayudas",
        candidate_type="keyword_match",
        extraction_status="raw_detected",
        evidence_level="metadata_keyword_match",
        matched_fields={"keywords": ["becas"]},
    )
    seen_urls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_urls.append(str(request.url))
        return httpx.Response(200, content=b"%PDF-1.4 BOJA", request=request)

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "--artifact-dir",
            str(artifact_dir),
            "download-boe-artifacts",
            "--source",
            "BOJA",
            "--candidate-ids",
            str(candidate["id"]),
            "--types",
            "pdf",
        ],
        artifact_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    stored = repository.list_document_files(document["id"])
    attempts = repository.list_artifact_download_attempts(document_id=document["id"])
    candidate_count = connection.execute("SELECT COUNT(*) FROM source_candidates").fetchone()[0]
    captured = capsys.readouterr()
    assert exit_code == 0
    assert seen_urls == [pdf_url]
    assert candidate_count == 1
    assert stored[0]["file_type"] == "pdf"
    assert stored[0]["sha256"] == sha256_bytes(b"%PDF-1.4 BOJA")
    assert attempts[-1]["status"] == "success"
    assert attempts[-1]["file_type"] == "pdf"
    assert "source_code=BOJA" in captured.out
    assert "selected_documents=1" in captured.out
    assert "downloaded=1" in captured.out
    assert "missing_artifact_url=0" in captured.out
    assert (artifact_dir / "boja" / "2026" / "05" / "19" / "BOJA_disposition.2026.94.5").exists()


def test_download_boe_artifacts_boja_missing_pdf_url_is_skipped(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    document = _seed_boja_document(db_path)
    connection = connect(str(db_path))
    repository = OfficialSourcesRepository(connection)
    candidate = repository.create_source_candidate(
        document_id=document["id"],
        project_key="boja-ayudas",
        candidate_type="keyword_match",
        extraction_status="raw_detected",
        evidence_level="metadata_keyword_match",
        matched_fields={"keywords": ["becas"]},
    )

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "download-boe-artifacts",
            "--source",
            "BOJA",
            "--candidate-ids",
            str(candidate["id"]),
            "--types",
            "pdf",
        ]
    )

    attempts = repository.list_artifact_download_attempts(document_id=document["id"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert repository.list_document_files(document["id"]) == []
    assert attempts[-1]["status"] == "skipped"
    assert attempts[-1]["official_url"] is None
    assert "skipped=1" in captured.out
    assert "missing_artifact_url=1" in captured.out


def test_download_boe_artifacts_boja_source_rejects_non_boja_candidate(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    document = _seed_document(db_path)
    connection = connect(str(db_path))
    repository = OfficialSourcesRepository(connection)
    candidate = repository.create_source_candidate(
        document_id=document["id"],
        project_key="la-ayuda",
        candidate_type="keyword_match",
        extraction_status="raw_detected",
        evidence_level="metadata_keyword_match",
        matched_fields={"keywords": ["ayudas"]},
    )

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "download-boe-artifacts",
            "--source",
            "BOJA",
            "--candidate-ids",
            str(candidate["id"]),
            "--types",
            "pdf",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "Selected documents must belong to source BOJA" in captured.err


def test_download_boe_artifacts_boja_rejects_date_level_download(tmp_path, capsys):
    from official_sources.cli import run

    exit_code = run(
        [
            "--db-path",
            str(tmp_path / "db.sqlite"),
            "download-boe-artifacts",
            "--source",
            "BOJA",
            "--date",
            "2026-05-19",
            "--types",
            "pdf",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "BOJA artifact downloads require --candidate-ids or --document-ids" in captured.err


def test_download_boe_artifacts_boja_rejects_xml_html_for_now(tmp_path, capsys):
    from official_sources.cli import run

    exit_code = run(
        [
            "--db-path",
            str(tmp_path / "db.sqlite"),
            "download-boe-artifacts",
            "--source",
            "BOJA",
            "--candidate-ids",
            "1",
            "--types",
            "xml,html",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "Unsupported BOJA artifact types: html, xml" in captured.err


def test_download_source_artifacts_supports_scoped_dogv_pdf_candidate_download(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    artifact_dir = tmp_path / "artifacts"
    pdf_url = "https://dogv.gva.es/datos/2026/05/20/pdf/2026_16062_es.pdf"
    document = _seed_dogv_document(db_path, url_pdf=pdf_url)
    connection = connect(str(db_path))
    repository = OfficialSourcesRepository(connection)
    candidate = repository.create_source_candidate(
        document_id=document["id"],
        project_key="dogv-ayudas",
        candidate_type="keyword_match",
        extraction_status="raw_detected",
        evidence_level="metadata_keyword_match",
        matched_fields={"keywords": ["becas"]},
    )
    seen_urls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_urls.append(str(request.url))
        return httpx.Response(200, content=b"%PDF-1.4 DOGV", request=request)

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "--artifact-dir",
            str(artifact_dir),
            "download-source-artifacts",
            "--source",
            "DOGV",
            "--candidate-ids",
            str(candidate["id"]),
            "--types",
            "pdf",
        ],
        artifact_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    stored = repository.list_document_files(document["id"])
    attempts = repository.list_artifact_download_attempts(document_id=document["id"])
    candidate_count = connection.execute("SELECT COUNT(*) FROM source_candidates").fetchone()[0]
    captured = capsys.readouterr()
    assert exit_code == 0
    assert seen_urls == [pdf_url]
    assert candidate_count == 1
    assert stored[0]["file_type"] == "pdf"
    assert stored[0]["official_url"] == pdf_url
    assert stored[0]["sha256"] == sha256_bytes(b"%PDF-1.4 DOGV")
    assert attempts[-1]["status"] == "success"
    assert attempts[-1]["file_type"] == "pdf"
    assert "source_code=DOGV" in captured.out
    assert "selected_documents=1" in captured.out
    assert "downloaded=1" in captured.out
    assert "missing_artifact_url=0" in captured.out
    assert (artifact_dir / "dogv" / "2026" / "05" / "20" / "DOGV_DOGV-C-2026-16062").exists()


def test_download_source_artifacts_dogv_candidate_ids_download_only_selected_documents(
    tmp_path, capsys
):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    artifact_dir = tmp_path / "artifacts"
    selected = _seed_dogv_document(
        db_path,
        external_id="DOGV:DOGV-C-2026-16062",
        url_pdf="https://dogv.gva.es/datos/2026/05/20/pdf/2026_16062_es.pdf",
    )
    connection = connect(str(db_path))
    repository = OfficialSourcesRepository(connection)
    source = repository.ensure_official_source_dogv()
    other = repository.upsert_document(
        source_id=source["id"],
        external_id="DOGV:DOGV-C-2026-16067",
        publication_date="2026-05-20",
        title="Other DOGV scholarship document",
        url_pdf="https://dogv.gva.es/datos/2026/05/20/pdf/2026_16067_es.pdf",
    )
    candidate = repository.create_source_candidate(
        document_id=selected["id"],
        project_key="dogv-ayudas",
        candidate_type="keyword_match",
        extraction_status="raw_detected",
        evidence_level="metadata_keyword_match",
        matched_fields={"keywords": ["becas"]},
    )
    seen_urls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_urls.append(str(request.url))
        return httpx.Response(200, content=b"%PDF-1.4 DOGV", request=request)

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "--artifact-dir",
            str(artifact_dir),
            "download-source-artifacts",
            "--source",
            "DOGV",
            "--candidate-ids",
            str(candidate["id"]),
            "--types",
            "pdf",
        ],
        artifact_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert seen_urls == [selected["url_pdf"]]
    assert {item["file_type"] for item in repository.list_document_files(selected["id"])} == {"pdf"}
    assert repository.list_document_files(other["id"]) == []
    assert "selected_documents=1" in captured.out


def test_download_source_artifacts_dogv_missing_pdf_url_is_skipped(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    document = _seed_dogv_document(db_path, url_pdf=None)
    connection = connect(str(db_path))
    repository = OfficialSourcesRepository(connection)
    candidate = repository.create_source_candidate(
        document_id=document["id"],
        project_key="dogv-ayudas",
        candidate_type="keyword_match",
        extraction_status="raw_detected",
        evidence_level="metadata_keyword_match",
        matched_fields={"keywords": ["becas"]},
    )

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "download-source-artifacts",
            "--source",
            "DOGV",
            "--candidate-ids",
            str(candidate["id"]),
            "--types",
            "pdf",
        ]
    )

    attempts = repository.list_artifact_download_attempts(document_id=document["id"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert repository.list_document_files(document["id"]) == []
    assert attempts[-1]["status"] == "skipped"
    assert attempts[-1]["official_url"] is None
    assert "skipped=1" in captured.out
    assert "missing_artifact_url=1" in captured.out


def test_download_source_artifacts_dogv_source_rejects_non_dogv_candidate(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    document = _seed_document(db_path)
    connection = connect(str(db_path))
    repository = OfficialSourcesRepository(connection)
    candidate = repository.create_source_candidate(
        document_id=document["id"],
        project_key="la-ayuda",
        candidate_type="keyword_match",
        extraction_status="raw_detected",
        evidence_level="metadata_keyword_match",
        matched_fields={"keywords": ["ayudas"]},
    )

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "download-source-artifacts",
            "--source",
            "DOGV",
            "--candidate-ids",
            str(candidate["id"]),
            "--types",
            "pdf",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "Selected documents must belong to source DOGV" in captured.err


def test_download_source_artifacts_dogv_rejects_date_level_download(tmp_path, capsys):
    from official_sources.cli import run

    exit_code = run(
        [
            "--db-path",
            str(tmp_path / "db.sqlite"),
            "download-source-artifacts",
            "--source",
            "DOGV",
            "--date",
            "2026-05-20",
            "--types",
            "pdf",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "DOGV artifact downloads require --candidate-ids" in captured.err


def test_download_source_artifacts_dogv_requires_explicit_pdf_type(tmp_path, capsys):
    from official_sources.cli import run

    exit_code = run(
        [
            "--db-path",
            str(tmp_path / "db.sqlite"),
            "download-source-artifacts",
            "--source",
            "DOGV",
            "--candidate-ids",
            "1",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "DOGV artifact downloads require --types pdf" in captured.err


def test_download_source_artifacts_supports_scoped_bocyl_xml_html_candidate_download(
    tmp_path, capsys
):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    artifact_dir = tmp_path / "artifacts"
    document = _seed_bocyl_document(db_path)
    connection = connect(str(db_path))
    repository = OfficialSourcesRepository(connection)
    candidate = repository.create_source_candidate(
        document_id=document["id"],
        project_key="generic",
        candidate_type="keyword_match",
        extraction_status="raw_detected",
        evidence_level="metadata_keyword_match",
        matched_fields={"keywords": ["becas"]},
    )
    seen_urls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_urls.append(str(request.url))
        if str(request.url).endswith(".xml"):
            return httpx.Response(200, content=b"<document><title>BOCYL XML</title></document>")
        return httpx.Response(200, content=b"<html><body>BOCYL HTML</body></html>")

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "--artifact-dir",
            str(artifact_dir),
            "download-source-artifacts",
            "--source",
            "BOCYL",
            "--candidate-ids",
            str(candidate["id"]),
            "--types",
            "xml,html",
        ],
        artifact_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    stored = repository.list_document_files(document["id"])
    attempts = repository.list_artifact_download_attempts(document_id=document["id"])
    candidate_count = connection.execute("SELECT COUNT(*) FROM source_candidates").fetchone()[0]
    captured = capsys.readouterr()
    assert exit_code == 0
    assert seen_urls == [document["url_xml"], document["url_html"]]
    assert candidate_count == 1
    assert {item["file_type"] for item in stored} == {"xml", "html"}
    assert {item["official_url"] for item in stored} == {
        document["url_xml"],
        document["url_html"],
    }
    assert [item["status"] for item in attempts] == ["success", "success"]
    assert "source_code=BOCYL" in captured.out
    assert "selected_documents=1" in captured.out
    assert "downloaded=2" in captured.out
    assert "missing_artifact_url=0" in captured.out
    assert (artifact_dir / "bocyl" / "2026" / "05" / "15" / "BOCYL_BOCYL-D-15052026-91-8").exists()


def test_download_source_artifacts_bocyl_follows_official_redirects(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    artifact_dir = tmp_path / "artifacts"
    document = _seed_bocyl_document(db_path)
    connection = connect(str(db_path))
    repository = OfficialSourcesRepository(connection)
    candidate = repository.create_source_candidate(
        document_id=document["id"],
        project_key="generic",
        candidate_type="keyword_match",
        extraction_status="raw_detected",
        evidence_level="metadata_keyword_match",
        matched_fields={"keywords": ["becas"]},
    )

    def handler(request: httpx.Request) -> httpx.Response:
        if str(request.url).startswith("http://"):
            return httpx.Response(
                302,
                headers={"Location": str(request.url).replace("http://", "https://", 1)},
                request=request,
            )
        return httpx.Response(200, content=b"<document>BOCYL redirected XML</document>")

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "--artifact-dir",
            str(artifact_dir),
            "download-source-artifacts",
            "--source",
            "BOCYL",
            "--candidate-ids",
            str(candidate["id"]),
            "--types",
            "xml",
        ],
        artifact_client=httpx.Client(
            transport=httpx.MockTransport(handler),
            follow_redirects=True,
        ),
    )

    attempts = repository.list_artifact_download_attempts(document_id=document["id"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert repository.list_document_files(document["id"])[0]["file_type"] == "xml"
    assert attempts[-1]["http_status"] == 200
    assert "downloaded=1" in captured.out


def test_download_source_artifacts_bocyl_requires_candidate_ids(tmp_path, capsys):
    from official_sources.cli import run

    exit_code = run(
        [
            "--db-path",
            str(tmp_path / "db.sqlite"),
            "download-source-artifacts",
            "--source",
            "BOCYL",
            "--date",
            "2026-05-15",
            "--types",
            "xml,html",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "BOCYL artifact downloads require --candidate-ids" in captured.err


def test_download_source_artifacts_bocyl_rejects_non_bocyl_candidate(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    document = _seed_document(db_path)
    connection = connect(str(db_path))
    repository = OfficialSourcesRepository(connection)
    candidate = repository.create_source_candidate(
        document_id=document["id"],
        project_key="la-ayuda",
        candidate_type="keyword_match",
        extraction_status="raw_detected",
        evidence_level="metadata_keyword_match",
        matched_fields={"keywords": ["ayudas"]},
    )

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "download-source-artifacts",
            "--source",
            "BOCYL",
            "--candidate-ids",
            str(candidate["id"]),
            "--types",
            "xml,html",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "Selected documents must belong to source BOCYL" in captured.err


def test_download_source_artifacts_bocyl_missing_xml_url_is_skipped(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    document = _seed_bocyl_document(db_path, url_xml=None)
    connection = connect(str(db_path))
    repository = OfficialSourcesRepository(connection)
    candidate = repository.create_source_candidate(
        document_id=document["id"],
        project_key="generic",
        candidate_type="keyword_match",
        extraction_status="raw_detected",
        evidence_level="metadata_keyword_match",
        matched_fields={"keywords": ["becas"]},
    )

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "download-source-artifacts",
            "--source",
            "BOCYL",
            "--candidate-ids",
            str(candidate["id"]),
            "--types",
            "xml",
        ]
    )

    attempts = repository.list_artifact_download_attempts(document_id=document["id"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert repository.list_document_files(document["id"]) == []
    assert attempts[-1]["status"] == "skipped"
    assert attempts[-1]["official_url"] is None
    assert "skipped=1" in captured.out
    assert "missing_artifact_url=1" in captured.out


def test_download_source_artifacts_supports_scoped_borm_pdf_candidate_download(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    artifact_dir = tmp_path / "artifacts"
    pdf_url = "https://www.borm.es/services/anuncio/842820/pdf"
    document = _seed_borm_document(db_path, url_pdf=pdf_url)
    connection = connect(str(db_path))
    repository = OfficialSourcesRepository(connection)
    candidate = repository.create_source_candidate(
        document_id=document["id"],
        project_key="borm-ayudas",
        candidate_type="keyword_match",
        extraction_status="raw_detected",
        evidence_level="metadata_keyword_match",
        matched_fields={"keywords": ["ayudas"]},
    )
    seen_urls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_urls.append(str(request.url))
        return httpx.Response(200, content=b"%PDF-1.4 BORM", request=request)

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "--artifact-dir",
            str(artifact_dir),
            "download-source-artifacts",
            "--source",
            "BORM",
            "--candidate-ids",
            str(candidate["id"]),
            "--types",
            "pdf",
        ],
        artifact_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    stored = repository.list_document_files(document["id"])
    attempts = repository.list_artifact_download_attempts(document_id=document["id"])
    candidate_count = connection.execute("SELECT COUNT(*) FROM source_candidates").fetchone()[0]
    captured = capsys.readouterr()
    assert exit_code == 0
    assert seen_urls == [pdf_url]
    assert candidate_count == 1
    assert stored[0]["file_type"] == "pdf"
    assert stored[0]["official_url"] == pdf_url
    assert stored[0]["sha256"] == sha256_bytes(b"%PDF-1.4 BORM")
    assert attempts[-1]["status"] == "success"
    assert attempts[-1]["file_type"] == "pdf"
    assert "source_code=BORM" in captured.out
    assert "selected_documents=1" in captured.out
    assert "downloaded=1" in captured.out
    assert "missing_artifact_url=0" in captured.out
    assert (artifact_dir / "borm" / "2026" / "05" / "14" / "BORM_A-140526-2138").exists()


def test_download_source_artifacts_borm_candidate_ids_download_only_selected_documents(
    tmp_path, capsys
):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    artifact_dir = tmp_path / "artifacts"
    selected = _seed_borm_document(
        db_path,
        external_id="BORM:A-140526-2138",
        url_pdf="https://www.borm.es/services/anuncio/842820/pdf",
    )
    connection = connect(str(db_path))
    repository = OfficialSourcesRepository(connection)
    source = repository.ensure_official_source_borm()
    other = repository.upsert_document(
        source_id=source["id"],
        external_id="BORM:A-130526-2111",
        publication_date="2026-05-13",
        title="Other BORM school-material aid document",
        url_pdf="https://www.borm.es/services/anuncio/842793/pdf",
    )
    candidate = repository.create_source_candidate(
        document_id=selected["id"],
        project_key="borm-ayudas",
        candidate_type="keyword_match",
        extraction_status="raw_detected",
        evidence_level="metadata_keyword_match",
        matched_fields={"keywords": ["ayudas"]},
    )
    seen_urls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_urls.append(str(request.url))
        return httpx.Response(200, content=b"%PDF-1.4 BORM", request=request)

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "--artifact-dir",
            str(artifact_dir),
            "download-source-artifacts",
            "--source",
            "BORM",
            "--candidate-ids",
            str(candidate["id"]),
            "--types",
            "pdf",
        ],
        artifact_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert seen_urls == [selected["url_pdf"]]
    assert {item["file_type"] for item in repository.list_document_files(selected["id"])} == {"pdf"}
    assert repository.list_document_files(other["id"]) == []
    assert "selected_documents=1" in captured.out


def test_download_source_artifacts_borm_follows_official_redirects(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    artifact_dir = tmp_path / "artifacts"
    document = _seed_borm_document(db_path)
    connection = connect(str(db_path))
    repository = OfficialSourcesRepository(connection)
    candidate = repository.create_source_candidate(
        document_id=document["id"],
        project_key="borm-ayudas",
        candidate_type="keyword_match",
        extraction_status="raw_detected",
        evidence_level="metadata_keyword_match",
        matched_fields={"keywords": ["ayudas"]},
    )

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Accept"] == "application/pdf"
        assert request.headers["User-Agent"] == "official-sources/1.0"
        if str(request.url).endswith("/pdf"):
            return httpx.Response(
                302,
                headers={"Location": "https://www.borm.es/services/anuncio/842820/pdf?download=1"},
                request=request,
            )
        return httpx.Response(200, content=b"%PDF-1.4 BORM redirected", request=request)

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "--artifact-dir",
            str(artifact_dir),
            "download-source-artifacts",
            "--source",
            "BORM",
            "--candidate-ids",
            str(candidate["id"]),
            "--types",
            "pdf",
        ],
        artifact_client=httpx.Client(
            transport=httpx.MockTransport(handler),
            follow_redirects=True,
        ),
    )

    attempts = repository.list_artifact_download_attempts(document_id=document["id"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert repository.list_document_files(document["id"])[0]["file_type"] == "pdf"
    assert attempts[-1]["http_status"] == 200
    assert "downloaded=1" in captured.out


def test_download_source_artifacts_borm_missing_pdf_url_is_skipped(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    document = _seed_borm_document(db_path, url_pdf=None)
    connection = connect(str(db_path))
    repository = OfficialSourcesRepository(connection)
    candidate = repository.create_source_candidate(
        document_id=document["id"],
        project_key="borm-ayudas",
        candidate_type="keyword_match",
        extraction_status="raw_detected",
        evidence_level="metadata_keyword_match",
        matched_fields={"keywords": ["ayudas"]},
    )

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "download-source-artifacts",
            "--source",
            "BORM",
            "--candidate-ids",
            str(candidate["id"]),
            "--types",
            "pdf",
        ]
    )

    attempts = repository.list_artifact_download_attempts(document_id=document["id"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert repository.list_document_files(document["id"]) == []
    assert attempts[-1]["status"] == "skipped"
    assert attempts[-1]["official_url"] is None
    assert "skipped=1" in captured.out
    assert "missing_artifact_url=1" in captured.out


def test_download_source_artifacts_borm_source_rejects_non_borm_candidate(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    document = _seed_document(db_path)
    connection = connect(str(db_path))
    repository = OfficialSourcesRepository(connection)
    candidate = repository.create_source_candidate(
        document_id=document["id"],
        project_key="la-ayuda",
        candidate_type="keyword_match",
        extraction_status="raw_detected",
        evidence_level="metadata_keyword_match",
        matched_fields={"keywords": ["ayudas"]},
    )

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "download-source-artifacts",
            "--source",
            "BORM",
            "--candidate-ids",
            str(candidate["id"]),
            "--types",
            "pdf",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "Selected documents must belong to source BORM" in captured.err


def test_download_source_artifacts_borm_rejects_date_level_download(tmp_path, capsys):
    from official_sources.cli import run

    exit_code = run(
        [
            "--db-path",
            str(tmp_path / "db.sqlite"),
            "download-source-artifacts",
            "--source",
            "BORM",
            "--date",
            "2026-05-14",
            "--types",
            "pdf",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "BORM artifact downloads require --candidate-ids" in captured.err


def test_download_source_artifacts_borm_rejects_document_ids(tmp_path, capsys):
    from official_sources.cli import run

    exit_code = run(
        [
            "--db-path",
            str(tmp_path / "db.sqlite"),
            "download-source-artifacts",
            "--source",
            "BORM",
            "--document-ids",
            "1",
            "--types",
            "pdf",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert (
        "BORM artifact downloads require --candidate-ids; --document-ids is not supported"
        in captured.err
    )


def test_download_source_artifacts_borm_requires_explicit_pdf_type(tmp_path, capsys):
    from official_sources.cli import run

    exit_code = run(
        [
            "--db-path",
            str(tmp_path / "db.sqlite"),
            "download-source-artifacts",
            "--source",
            "BORM",
            "--candidate-ids",
            "1",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "BORM artifact downloads require --types pdf" in captured.err


def test_download_source_artifacts_borm_rejects_invalid_pdf_host(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    artifact_dir = tmp_path / "artifacts"
    document = _seed_borm_document(
        db_path, url_pdf="https://example.com/services/anuncio/842820/pdf"
    )
    connection = connect(str(db_path))
    repository = OfficialSourcesRepository(connection)
    candidate = repository.create_source_candidate(
        document_id=document["id"],
        project_key="borm-ayudas",
        candidate_type="keyword_match",
        extraction_status="raw_detected",
        evidence_level="metadata_keyword_match",
        matched_fields={"keywords": ["ayudas"]},
    )

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "--artifact-dir",
            str(artifact_dir),
            "download-source-artifacts",
            "--source",
            "BORM",
            "--candidate-ids",
            str(candidate["id"]),
            "--types",
            "pdf",
        ]
    )

    attempts = repository.list_artifact_download_attempts(document_id=document["id"])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert attempts[-1]["status"] == "failed"
    assert "official BORM host" in captured.err


def test_download_source_artifacts_borm_rejects_invalid_pdf_path(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    document = _seed_borm_document(db_path, url_pdf="https://www.borm.es/not-official/842820.pdf")
    connection = connect(str(db_path))
    repository = OfficialSourcesRepository(connection)
    candidate = repository.create_source_candidate(
        document_id=document["id"],
        project_key="borm-ayudas",
        candidate_type="keyword_match",
        extraction_status="raw_detected",
        evidence_level="metadata_keyword_match",
        matched_fields={"keywords": ["ayudas"]},
    )

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "download-source-artifacts",
            "--source",
            "BORM",
            "--candidate-ids",
            str(candidate["id"]),
            "--types",
            "pdf",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "official BORM PDF service path" in captured.err


def test_download_boe_artifacts_rejects_mixed_date_and_scoped_selection(tmp_path, capsys):
    from official_sources.cli import run

    exit_code = run(
        [
            "--db-path",
            str(tmp_path / "db.sqlite"),
            "download-boe-artifacts",
            "--date",
            "2024-05-29",
            "--document-ids",
            "1",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "--date cannot be combined" in captured.err


def test_download_boe_artifacts_rejects_non_boe_url(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    connection = connect(str(db_path))
    initialize_database(connection)
    repository = OfficialSourcesRepository(connection)
    source = repository.ensure_official_source_boe()
    repository.upsert_document(
        source_id=source["id"],
        external_id="BOE-A-2024-11111",
        publication_date="2024-05-29",
        title="Bad URL",
        url_xml="https://example.com/document.xml",
    )

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "--artifact-dir",
            str(tmp_path / "artifacts"),
            "download-boe-artifacts",
            "--date",
            "2024-05-29",
            "--types",
            "xml",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "failed=1" in captured.out
    assert "official BOE host" in captured.err


def test_status_reports_real_failed_downloads(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    connection = connect(str(db_path))
    initialize_database(connection)
    repository = OfficialSourcesRepository(connection)
    source = repository.ensure_official_source_boe()
    repository.upsert_document(
        source_id=source["id"],
        external_id="BOE-A-2024-11111",
        publication_date="2024-05-29",
        title="Bad URL",
        url_xml="https://example.com/document.xml",
    )
    run(
        [
            "--db-path",
            str(db_path),
            "download-boe-artifacts",
            "--date",
            "2024-05-29",
            "--types",
            "xml",
        ]
    )

    exit_code = run(["--db-path", str(db_path), "status", "--date", "2024-05-29"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "summary_ingestion_status=none" in captured.out
    assert "download_attempts=1" in captured.out
    assert "download_failed=1" in captured.out
    assert "artifact_download_attempts=1" in captured.out
    assert "artifact_download_failed=1" in captured.out
    assert "artifact_http_status_summary=xml:none:1" in captured.out
    assert "failed_downloads=1" in captured.out


def test_status_does_not_hardcode_failed_downloads():
    import inspect

    import official_sources.cli as cli

    source = inspect.getsource(cli)

    assert '"failed_downloads": 0' not in source


def test_integrity_check_detects_unchanged_local_artifact(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    artifact_dir = tmp_path / "artifacts"
    document = _seed_document(db_path)
    payload = _fixture_bytes("boe_document.xml")
    run(
        [
            "--db-path",
            str(db_path),
            "--artifact-dir",
            str(artifact_dir),
            "download-boe-artifacts",
            "--date",
            "2024-05-29",
            "--types",
            "xml",
        ],
        artifact_client=_artifact_client({document["url_xml"]: payload}),
    )

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "integrity-check",
            "--date",
            "2024-05-29",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "unchanged=1" in captured.out


def test_integrity_check_detects_changed_local_artifact(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    artifact_dir = tmp_path / "artifacts"
    document = _seed_document(db_path)
    original = _fixture_bytes("boe_document.xml")
    run(
        [
            "--db-path",
            str(db_path),
            "--artifact-dir",
            str(artifact_dir),
            "download-boe-artifacts",
            "--date",
            "2024-05-29",
            "--types",
            "xml",
        ],
        artifact_client=_artifact_client({document["url_xml"]: original}),
    )
    local_path = (
        artifact_dir / "boe" / "2024" / "05" / "29" / document["external_id"] / "document.xml"
    )
    local_path.write_bytes(b"<document><text>changed</text></document>")

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "integrity-check",
            "--date",
            "2024-05-29",
        ]
    )

    connection = connect(str(db_path))
    repository = OfficialSourcesRepository(connection)
    file_record = repository.list_document_files(document["id"])[0]
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "changed=1" in captured.out
    assert file_record["previous_hash"] == sha256_bytes(original)


def test_integrity_check_ignores_non_local_raw_metadata(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    artifact_dir = tmp_path / "artifacts"
    document = _seed_document(db_path)
    payload = _fixture_bytes("boe_document.xml")
    run(
        [
            "--db-path",
            str(db_path),
            "--artifact-dir",
            str(artifact_dir),
            "download-boe-artifacts",
            "--date",
            "2024-05-29",
            "--types",
            "xml",
        ],
        artifact_client=_artifact_client({document["url_xml"]: payload}),
    )
    connection = connect(str(db_path))
    repository = OfficialSourcesRepository(connection)
    repository.upsert_document_file(
        document_id=document["id"],
        file_type="raw_api_response",
        official_url="https://www.boe.es/datosabiertos/api/boe/sumario/20240529",
        local_path=None,
        media_type="application/json",
        payload=b'{"metadata":"source snapshot"}',
        ingestion_run_id=None,
    )

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "integrity-check",
            "--date",
            "2024-05-29",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "unchanged=1" in captured.out
    assert "missing=0" in captured.out
    assert "non_local_metadata=1" in captured.out
    assert "missing file_id=" not in captured.err


def test_integrity_check_still_fails_for_missing_local_artifact(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    artifact_dir = tmp_path / "artifacts"
    document = _seed_document(db_path)
    payload = _fixture_bytes("boe_document.xml")
    run(
        [
            "--db-path",
            str(db_path),
            "--artifact-dir",
            str(artifact_dir),
            "download-boe-artifacts",
            "--date",
            "2024-05-29",
            "--types",
            "xml",
        ],
        artifact_client=_artifact_client({document["url_xml"]: payload}),
    )
    local_path = (
        artifact_dir / "boe" / "2024" / "05" / "29" / document["external_id"] / "document.xml"
    )
    local_path.unlink()

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "integrity-check",
            "--date",
            "2024-05-29",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "missing=1" in captured.out
    assert "missing file_id=" in captured.err


def test_status_reports_expected_counts(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    artifact_dir = tmp_path / "artifacts"
    document = _seed_document(db_path)
    run(
        [
            "--db-path",
            str(db_path),
            "--artifact-dir",
            str(artifact_dir),
            "download-boe-artifacts",
            "--date",
            "2024-05-29",
            "--types",
            "xml,html",
        ],
        artifact_client=_artifact_client(
            {
                document["url_xml"]: _fixture_bytes("boe_document.xml"),
                document["url_html"]: _fixture_bytes("boe_document.html"),
            }
        ),
    )

    exit_code = run(["--db-path", str(db_path), "status", "--date", "2024-05-29"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "documents=1" in captured.out
    assert "xml_files=1" in captured.out
    assert "html_files=1" in captured.out
    assert "pdf_files=0" in captured.out
    assert "artifact_download_attempts=2" in captured.out
    assert "artifact_download_success=2" in captured.out
    assert "artifact_http_status_summary=xml:200:1,html:200:1" in captured.out


def test_status_reports_summary_http_status_after_summary_only(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    exit_code = run(
        ["--db-path", str(db_path), "ingest-boe-summary", "--date", "2024-05-29"],
        summary_fetcher=lambda _date: _fixture_bytes("boe_summary_20240529.json"),
    )
    capsys.readouterr()

    status_exit_code = run(["--db-path", str(db_path), "status", "--date", "2024-05-29"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert status_exit_code == 0
    assert "summary_ingestion_status=success" in captured.out
    assert "summary_last_http_status=200" in captured.out
    assert "summary_retry_count=0" in captured.out
    assert "summary_throttle_triggered=0" in captured.out
    assert "artifact_http_status_summary=none" in captured.out


def test_status_keeps_summary_http_status_after_artifact_downloads(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    artifact_dir = tmp_path / "artifacts"
    run(
        ["--db-path", str(db_path), "ingest-boe-summary", "--date", "2024-05-29"],
        summary_fetcher=lambda _date: _fixture_bytes("boe_summary_20240529.json"),
    )
    connection = connect(str(db_path))
    repository = OfficialSourcesRepository(connection)
    document = repository.get_document_by_external_id("BOE-A-2024-11111")
    run(
        [
            "--db-path",
            str(db_path),
            "--artifact-dir",
            str(artifact_dir),
            "download-boe-artifacts",
            "--date",
            "2024-05-29",
            "--types",
            "xml,html",
        ],
        artifact_client=_artifact_client(
            {
                document["url_xml"]: _fixture_bytes("boe_document.xml"),
                document["url_html"]: _fixture_bytes("boe_document.html"),
            }
        ),
    )
    capsys.readouterr()

    exit_code = run(["--db-path", str(db_path), "status", "--date", "2024-05-29"])
    validate_exit_code = run(["--db-path", str(db_path), "db", "validate"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert validate_exit_code == 0
    assert "summary_ingestion_status=success" in captured.out
    assert "summary_last_http_status=200" in captured.out
    assert "last_http_status=200" in captured.out
    assert "artifact_http_status_summary=xml:200:1,html:200:1" in captured.out
    assert "artifact_retry_count=0" in captured.out


def test_cli_does_not_expose_mcp_write_tools_or_downstream_publication():
    import inspect

    import official_sources.cli as cli

    source = inspect.getsource(cli)

    assert "FastMCP" not in source
    assert "mcp.tool" not in source
    assert "human_accepted" not in source
    assert "publish" not in source.lower()
    downstream_lines = [
        line
        for line in source.lower().splitlines()
        if "downstream" in line
        and "downstream_project" not in line
        and "downstream-project" not in line
        and "downstream project fit" not in line
    ]
    allowed_downstream_fragments = {
        "downstream_export",
        "export_downstream_evidence",
        "export-downstream-evidence",
        "downstream evidence json files",
        "downstream staging",
    }
    assert [
        line
        for line in downstream_lines
        if not any(fragment in line for fragment in allowed_downstream_fragments)
    ] == []


def test_cli_accepts_today_for_systemd_templates(tmp_path, capsys):
    from official_sources.cli import run

    exit_code = run(["--db-path", str(tmp_path / "db.sqlite"), "status", "--date", "today"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "target_date=" in captured.out


def test_ingest_boe_range_rejects_invalid_date(tmp_path, capsys):
    from official_sources.cli import run

    exit_code = run(
        [
            "--db-path",
            str(tmp_path / "db.sqlite"),
            "ingest-boe-range",
            "--date-from",
            "20240529",
            "--date-to",
            "2024-05-30",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "YYYY-MM-DD" in captured.err


def test_ingest_boe_range_rejects_reversed_dates(tmp_path, capsys):
    from official_sources.cli import run

    exit_code = run(
        [
            "--db-path",
            str(tmp_path / "db.sqlite"),
            "ingest-boe-range",
            "--date-from",
            "2024-05-30",
            "--date-to",
            "2024-05-29",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "--date-from" in captured.err


def test_ingest_boe_range_default_max_days_is_90(tmp_path, capsys):
    from official_sources.cli import run

    exit_code = run(
        [
            "--db-path",
            str(tmp_path / "db.sqlite"),
            "ingest-boe-range",
            "--date-from",
            "2024-01-01",
            "--date-to",
            "2024-04-01",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "--max-days=90" in captured.err


def test_ingest_boe_range_above_365_requires_force_and_ack(tmp_path, capsys):
    from official_sources.cli import run

    base = [
        "--db-path",
        str(tmp_path / "db.sqlite"),
        "ingest-boe-range",
        "--date-from",
        "2023-01-01",
        "--date-to",
        "2024-01-01",
        "--max-days",
        "400",
    ]

    assert run(base) == 2
    captured = capsys.readouterr()
    assert "--force" in captured.err
    assert run([*base, "--force"]) == 2
    captured = capsys.readouterr()
    assert "--confirm-large-range" in captured.err


def test_ingest_boe_range_inclusive_and_does_not_download_artifacts(tmp_path, capsys, monkeypatch):
    import official_sources.cli as cli

    db_path = tmp_path / "db.sqlite"
    calls = []

    class FakeClient:
        def __init__(self, *args, **kwargs):
            self.last_request_audit = BOERequestAudit(last_http_status=200)

        def fetch_summary(self, target_date):
            calls.append(target_date)
            return _fixture_bytes("boe_summary_20240529.json")

    monkeypatch.setattr(cli, "BOEClient", FakeClient)

    exit_code = cli.run(
        [
            "--db-path",
            str(db_path),
            "ingest-boe-range",
            "--date-from",
            "2024-05-29",
            "--date-to",
            "2024-05-30",
            "--max-days",
            "2",
        ]
    )

    connection = connect(str(db_path))
    repository = OfficialSourcesRepository(connection)
    captured = capsys.readouterr()
    assert exit_code == 0
    assert calls == ["2024-05-29", "2024-05-30"]
    assert "processed=2" in captured.out
    assert sum(repository.count_artifact_download_attempts_by_date("2024-05-29").values()) == 0


def test_ingest_boe_range_skip_existing_skips_success_dates(tmp_path, monkeypatch):
    import official_sources.cli as cli

    db_path = tmp_path / "db.sqlite"
    cli.run(
        ["--db-path", str(db_path), "ingest-boe-summary", "--date", "2024-05-29"],
        summary_fetcher=lambda _date: _fixture_bytes("boe_summary_20240529.json"),
    )
    calls = []

    class FakeClient:
        def __init__(self, *args, **kwargs):
            self.last_request_audit = BOERequestAudit(last_http_status=200)

        def fetch_summary(self, target_date):
            calls.append(target_date)
            return _fixture_bytes("boe_summary_20240529.json")

    monkeypatch.setattr(cli, "BOEClient", FakeClient)

    exit_code = cli.run(
        [
            "--db-path",
            str(db_path),
            "ingest-boe-range",
            "--date-from",
            "2024-05-29",
            "--date-to",
            "2024-05-29",
            "--skip-existing",
        ]
    )

    assert exit_code == 0
    assert calls == []


def test_ingest_boe_range_continue_on_no_publication(tmp_path, capsys, monkeypatch):
    import official_sources.cli as cli

    db_path = tmp_path / "db.sqlite"

    class FakeClient:
        def __init__(self, *args, **kwargs):
            self.last_request_audit = BOERequestAudit(last_http_status=404)

        def fetch_summary(self, target_date):
            if target_date == "2025-01-05":
                raise BOESummaryNotFoundError(target_date, self.last_request_audit)
            self.last_request_audit = BOERequestAudit(last_http_status=200)
            return _fixture_bytes("boe_summary_20240529.json")

    monkeypatch.setattr(cli, "BOEClient", FakeClient)

    exit_code = cli.run(
        [
            "--db-path",
            str(db_path),
            "ingest-boe-range",
            "--date-from",
            "2025-01-05",
            "--date-to",
            "2025-01-06",
            "--max-days",
            "2",
            "--continue-on-no-publication",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "no_publication=1" in captured.out
    assert "success=1" in captured.out


def test_ingest_boe_range_stop_on_error_stops_real_failures(tmp_path, capsys, monkeypatch):
    import official_sources.cli as cli

    class FakeClient:
        def __init__(self, *args, **kwargs):
            self.last_request_audit = BOERequestAudit(last_http_status=200)

        def fetch_summary(self, target_date):
            if target_date == "2024-05-30":
                raise RuntimeError("network unavailable")
            return _fixture_bytes("boe_summary_20240529.json")

    monkeypatch.setattr(cli, "BOEClient", FakeClient)

    exit_code = cli.run(
        [
            "--db-path",
            str(tmp_path / "db.sqlite"),
            "ingest-boe-range",
            "--date-from",
            "2024-05-29",
            "--date-to",
            "2024-05-31",
            "--max-days",
            "3",
            "--stop-on-error",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "processed=2" in captured.out
    assert "failed=1" in captured.out


def test_ingest_boe_range_sleep_seconds_configures_limiter(tmp_path, monkeypatch):
    import official_sources.cli as cli

    policies = []

    class FakeClient:
        def __init__(self, *args, **kwargs):
            policies.append(kwargs["request_policy"])
            self.last_request_audit = BOERequestAudit(last_http_status=200)

        def fetch_summary(self, _target_date):
            return _fixture_bytes("boe_summary_20240529.json")

    monkeypatch.setattr(cli, "BOEClient", FakeClient)

    exit_code = cli.run(
        [
            "--db-path",
            str(tmp_path / "db.sqlite"),
            "ingest-boe-range",
            "--date-from",
            "2024-05-29",
            "--date-to",
            "2024-05-29",
            "--sleep-seconds",
            "2",
        ]
    )

    assert exit_code == 0
    assert policies[0].requests_per_second == 0.5


def test_find_boe_candidates_matches_titles_and_metadata(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    connection = connect(str(db_path))
    initialize_database(connection)
    repository = OfficialSourcesRepository(connection)
    source = repository.ensure_official_source_boe()
    repository.upsert_document(
        source_id=source["id"],
        external_id="BOE-A-2024-11111",
        publication_date="2024-05-29",
        title="Convocatoria de becas",
        department="Ministerio de Educacion",
        raw_metadata={"materia": "estudiantes"},
    )

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "find-boe-candidates",
            "--date-from",
            "2024-05-29",
            "--date-to",
            "2024-05-29",
            "--keywords",
            "becas,estudiantes",
            "--project-key",
            "la-ayuda",
            "--write",
        ]
    )

    candidate = connection.execute("SELECT * FROM source_candidates").fetchone()
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "candidates_created=1" in captured.out
    assert candidate["review_status"] == "human_review_required"
    assert candidate["extraction_status"] == "raw_detected"
    assert "becas" in candidate["matched_fields_json"]
    assert "estudiantes" in candidate["matched_fields_json"]


def test_find_boe_candidates_requires_explicit_write_or_dry_run(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    connection = connect(str(db_path))
    initialize_database(connection)
    repository = OfficialSourcesRepository(connection)
    source = repository.ensure_official_source_boe()
    repository.upsert_document(
        source_id=source["id"],
        external_id="BOE-A-2024-11111",
        publication_date="2024-05-29",
        title="Convocatoria de ayudas",
    )

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "find-boe-candidates",
            "--date-from",
            "2024-05-29",
            "--date-to",
            "2024-05-29",
            "--keywords",
            "ayudas",
        ]
    )

    candidate_count = connection.execute(
        "SELECT COUNT(*) AS count FROM source_candidates"
    ).fetchone()["count"]
    captured = capsys.readouterr()
    assert exit_code == 2
    assert candidate_count == 0
    assert "--write" in captured.err
    assert "--dry-run" in captured.err


def test_find_boe_candidates_write_mode_respects_limit(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    connection = connect(str(db_path))
    initialize_database(connection)
    repository = OfficialSourcesRepository(connection)
    source = repository.ensure_official_source_boe()
    for index in range(3):
        repository.upsert_document(
            source_id=source["id"],
            external_id=f"BOE-A-2024-1111{index}",
            publication_date="2024-05-29",
            title=f"Convocatoria de ayudas {index}",
        )

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "find-boe-candidates",
            "--date-from",
            "2024-05-29",
            "--date-to",
            "2024-05-29",
            "--keywords",
            "ayudas",
            "--write",
            "--limit",
            "2",
        ]
    )

    rows = connection.execute(
        "SELECT review_status, matched_fields_json FROM source_candidates ORDER BY id"
    ).fetchall()
    captured = capsys.readouterr()
    assert exit_code == 0
    assert len(rows) == 2
    assert {row["review_status"] for row in rows} == {"human_review_required"}
    assert "matches_after_filters=3" in captured.out
    assert "candidates_created=2" in captured.out
    assert "write_limit=2" in captured.out


def test_find_boe_candidates_write_mode_skips_existing_candidates(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    connection = connect(str(db_path))
    initialize_database(connection)
    repository = OfficialSourcesRepository(connection)
    source = repository.ensure_official_source_boe()
    existing_document = repository.upsert_document(
        source_id=source["id"],
        external_id="BOE-A-2024-11110",
        publication_date="2024-05-29",
        title="Convocatoria de ayudas existing",
    )
    repository.create_source_candidate(
        document_id=existing_document["id"],
        project_key="generic",
        candidate_type="keyword_match",
        extraction_status="raw_detected",
        evidence_level="metadata_keyword_match",
        matched_fields={"keywords": ["ayudas"]},
    )
    for index in range(3):
        repository.upsert_document(
            source_id=source["id"],
            external_id=f"BOE-A-2024-1112{index}",
            publication_date="2024-05-29",
            title=f"Convocatoria de ayudas new {index}",
        )

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "find-boe-candidates",
            "--date-from",
            "2024-05-29",
            "--date-to",
            "2024-05-29",
            "--keywords",
            "ayudas",
            "--write",
            "--limit",
            "2",
        ]
    )

    rows = connection.execute(
        """
        SELECT d.external_id, COUNT(c.id) AS candidate_count
        FROM source_candidates c
        JOIN official_documents d ON d.id = c.document_id
        GROUP BY d.external_id
        ORDER BY d.external_id
        """
    ).fetchall()
    captured = capsys.readouterr()
    assert exit_code == 0
    assert sum(row["candidate_count"] for row in rows) == 3
    assert {row["external_id"] for row in rows} == {
        "BOE-A-2024-11110",
        "BOE-A-2024-11120",
        "BOE-A-2024-11121",
    }
    assert {row["candidate_count"] for row in rows} == {1}
    assert "candidates_created=2" in captured.out
    assert "candidates_skipped_existing=1" in captured.out


def test_find_boe_candidates_dry_run_does_not_create_candidates(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    connection = connect(str(db_path))
    initialize_database(connection)
    repository = OfficialSourcesRepository(connection)
    source = repository.ensure_official_source_boe()
    repository.upsert_document(
        source_id=source["id"],
        external_id="BOE-A-2024-11111",
        publication_date="2024-05-29",
        title="Convocatoria de becas",
        department="Ministerio de Educacion",
        section="III",
        raw_metadata={"materia": "estudiantes"},
    )

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "find-boe-candidates",
            "--date-from",
            "2024-05-29",
            "--date-to",
            "2024-05-29",
            "--keywords",
            "becas,estudiantes",
            "--project-key",
            "la-ayuda",
            "--dry-run",
            "--limit",
            "1",
        ]
    )

    candidate_count = connection.execute(
        "SELECT COUNT(*) AS count FROM source_candidates"
    ).fetchone()["count"]
    captured = capsys.readouterr()
    assert exit_code == 0
    assert candidate_count == 0
    assert "write_mode=dry_run" in captured.out
    assert "documents_scanned=1" in captured.out
    assert "documents_matched=1" in captured.out
    assert "candidates_created=0" in captured.out
    assert "matches_by_keyword=becas:1,estudiantes:1" in captured.out
    assert "matches_by_section=III:1" in captured.out
    assert "matches_by_department=Ministerio_de_Educacion:1" in captured.out
    assert "sample index=1" in captured.out
    assert "BOE-A-2024-11111" in captured.out


def test_find_boe_candidates_source_filter_supports_boja_dry_run(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    connection = connect(str(db_path))
    initialize_database(connection)
    repository = OfficialSourcesRepository(connection)
    boe_source = repository.ensure_official_source_boe()
    boja_source = repository.ensure_official_source_boja()
    repository.upsert_document(
        source_id=boe_source["id"],
        external_id="BOE-A-2024-11111",
        publication_date="2024-05-29",
        title="Convocatoria de ayudas estatales",
    )
    repository.upsert_document(
        source_id=boja_source["id"],
        external_id="BOJA:disposition.2026.94.5",
        publication_date="2024-05-29",
        title="Subvenciones para formacion profesional",
        department="Consejeria de Desarrollo Educativo y Formacion Profesional",
        section="3. Otras disposiciones",
    )

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "find-boe-candidates",
            "--source",
            "BOJA",
            "--date-from",
            "2024-05-29",
            "--date-to",
            "2024-05-29",
            "--profile",
            "la-ayuda",
            "--dry-run",
        ]
    )

    candidate_count = connection.execute(
        "SELECT COUNT(*) AS count FROM source_candidates"
    ).fetchone()["count"]
    captured = capsys.readouterr()
    assert exit_code == 0
    assert candidate_count == 0
    assert "source=BOJA" in captured.out
    assert "documents_scanned=1" in captured.out
    assert "matches_after_filters=1" in captured.out
    assert "BOJA:disposition.2026.94.5" in captured.out
    assert "BOE-A-2024-11111" not in captured.out


def test_dry_run_opposition_alerts_outputs_json_without_writes(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    connection = connect(str(db_path))
    initialize_database(connection)
    repository = OfficialSourcesRepository(connection)
    boe = repository.ensure_official_source_boe()
    borm = repository.ensure_official_source_borm()
    repository.upsert_document(
        source_id=boe["id"],
        external_id="BOE-A-2026-00001",
        publication_date="2026-05-20",
        title="Resolucion por la que se convoca proceso selectivo para personal funcionario",
        department="Ministerio de Hacienda",
        url_html="https://www.boe.es/buscar/doc.php?id=BOE-A-2026-00001",
    )
    repository.upsert_document(
        source_id=borm["id"],
        external_id="BORM:2026:001",
        publication_date="2026-05-20",
        title="Convocatoria para la constitucion de una bolsa de trabajo de auxiliares",
        department="Ayuntamiento de Murcia",
        url_html="https://www.borm.es/#/home/anuncio/20-05-2026/1",
    )
    repository.upsert_document(
        source_id=borm["id"],
        external_id="BORM:2026:002",
        publication_date="2026-05-20",
        title="Anuncio de licitacion del contrato de limpieza de edificios municipales",
        department="Ayuntamiento de Murcia",
        url_html="https://www.borm.es/#/home/anuncio/20-05-2026/2",
    )

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "dry-run-opposition-alerts",
            "--source",
            "BOE,BORM",
            "--date-from",
            "2026-05-20",
            "--date-to",
            "2026-05-20",
            "--format",
            "json",
            "--limit",
            "10",
        ]
    )

    candidate_count = connection.execute(
        "SELECT COUNT(*) AS count FROM source_candidates"
    ).fetchone()["count"]
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert candidate_count == 0
    assert payload["summary"]["documents_scanned"] == 3
    assert payload["summary"]["alerts_found"] == 2
    assert payload["summary"]["writes"]["source_candidates"] is False
    assert payload["summary"]["alerts_by_type"] == {"bolsa": 1, "convocatoria": 1}
    assert {alert["alert_type"] for alert in payload["alerts"]} == {"bolsa", "convocatoria"}
    assert {alert["alert_scope"] for alert in payload["alerts"]} == {"strict"}
    assert {alert["review_status"] for alert in payload["alerts"]} == {"new"}
    assert {alert["evidence_grade_status"] for alert in payload["alerts"]} == {"none"}
    assert all(alert["source_candidate_id"] is None for alert in payload["alerts"])


def test_dry_run_opposition_alerts_jsonl_and_contextual_exclusions(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    connection = connect(str(db_path))
    initialize_database(connection)
    repository = OfficialSourcesRepository(connection)
    source = repository.ensure_official_source_boe()
    repository.upsert_document(
        source_id=source["id"],
        external_id="BOE-A-2026-00002",
        publication_date="2026-05-20",
        title="Real Decreto por el que se nombra Directora General de Coordinacion",
        department="Ministerio de Politica Territorial",
        url_html="https://www.boe.es/buscar/doc.php?id=BOE-A-2026-00002",
    )
    repository.upsert_document(
        source_id=source["id"],
        external_id="BOE-A-2026-00003",
        publication_date="2026-05-20",
        title="Nombramiento de personal funcionario tras superar el proceso selectivo",
        department="Ministerio de Justicia",
        url_html="https://www.boe.es/buscar/doc.php?id=BOE-A-2026-00003",
    )

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "dry-run-opposition-alerts",
            "--source",
            "BOE",
            "--date-from",
            "2026-05-20",
            "--date-to",
            "2026-05-20",
            "--format",
            "jsonl",
            "--limit",
            "10",
        ]
    )

    captured = capsys.readouterr()
    rows = [json.loads(line) for line in captured.out.splitlines()]
    candidate_count = connection.execute(
        "SELECT COUNT(*) AS count FROM source_candidates"
    ).fetchone()["count"]
    assert exit_code == 0
    assert candidate_count == 0
    assert rows[0]["record_type"] == "summary"
    assert rows[0]["alerts_found"] == 2
    alerts = [row for row in rows[1:] if row["record_type"] == "alert"]
    alerts_by_id = {alert["document_identifier"]: alert for alert in alerts}
    assert alerts_by_id["BOE-A-2026-00002"]["alert_type"] == "nombramiento"
    assert alerts_by_id["BOE-A-2026-00002"]["alert_scope"] == "review_only"
    assert alerts_by_id["BOE-A-2026-00003"]["alert_type"] == "nombramiento"
    assert alerts_by_id["BOE-A-2026-00003"]["alert_scope"] == "broad"
    assert {alert["confidence"] for alert in alerts} == {"medium"}


def test_dry_run_opposition_alerts_excludes_generic_convocatoria_noise(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    connection = connect(str(db_path))
    initialize_database(connection)
    repository = OfficialSourcesRepository(connection)
    source = repository.ensure_official_source_boe()
    noisy_titles = [
        (
            "BOE-B-2026-10001",
            "Extracto por el que se aprueba la convocatoria de becas universitarias",
        ),
        (
            "BOE-B-2026-10002",
            "Resolucion por la que se convoca el levantamiento de actas previas "
            "en expediente de expropiacion forzosa",
        ),
        (
            "BOE-B-2026-10003",
            "Anuncio de licitacion del contrato de servicios para personal laboral",
        ),
        (
            "BOE-B-2026-10004",
            "Resolucion por la que se inicia el procedimiento nacional de oposicion "
            "de la DOP Ribera del Guadiana",
        ),
        (
            "BOE-B-2026-10005",
            "Convocatoria de subvenciones para entidades locales",
        ),
    ]
    for external_id, title in noisy_titles:
        repository.upsert_document(
            source_id=source["id"],
            external_id=external_id,
            publication_date="2026-05-20",
            title=title,
            department="Ministerio de Politica Territorial",
            url_html=f"https://www.boe.es/diario_boe/txt.php?id={external_id}",
        )

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "dry-run-opposition-alerts",
            "--source",
            "BOE",
            "--date-from",
            "2026-05-20",
            "--date-to",
            "2026-05-20",
            "--format",
            "json",
            "--limit",
            "10",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["summary"]["documents_scanned"] == len(noisy_titles)
    assert payload["summary"]["alerts_found"] == 0
    assert payload["alerts"] == []


def test_dry_run_opposition_alerts_detects_process_events_with_priority(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    connection = connect(str(db_path))
    initialize_database(connection)
    repository = OfficialSourcesRepository(connection)
    source = repository.ensure_official_source_borm()
    examples = [
        (
            "BORM:2026:201",
            "Resolucion por la que se convoca proceso selectivo para cubrir plazas "
            "del Cuerpo Superior de Administradores por turno libre",
            "convocatoria",
        ),
        (
            "BORM:2026:202",
            "Convocatoria para constituir una bolsa de trabajo de auxiliares administrativos",
            "bolsa",
        ),
        (
            "BORM:2026:203",
            "Orden por la que se aprueba la lista provisional de aspirantes admitidos "
            "y excluidos de las pruebas selectivas",
            "lista_provisional",
        ),
        (
            "BORM:2026:204",
            "Resolucion por la que se nombra a las personas miembros del tribunal "
            "calificador del proceso selectivo",
            "tribunal",
        ),
        (
            "BORM:2026:205",
            "Anuncio de fecha de examen del concurso-oposicion para personal funcionario",
            "fecha_examen",
        ),
    ]
    for external_id, title, _expected_type in examples:
        repository.upsert_document(
            source_id=source["id"],
            external_id=external_id,
            publication_date="2026-05-20",
            title=title,
            department="Consejeria de Hacienda",
            url_html=f"https://www.borm.es/#/home/anuncio/20-05-2026/{external_id[-3:]}",
        )

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "dry-run-opposition-alerts",
            "--source",
            "BORM",
            "--date-from",
            "2026-05-20",
            "--date-to",
            "2026-05-20",
            "--format",
            "json",
            "--limit",
            "10",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    alerts_by_id = {alert["document_identifier"]: alert for alert in payload["alerts"]}
    assert exit_code == 0
    assert payload["summary"]["alerts_found"] == len(examples)
    for external_id, _title, expected_type in examples:
        assert alerts_by_id[external_id]["alert_type"] == expected_type
        assert alerts_by_id[external_id]["alert_scope"] == "strict"
    assert alerts_by_id["BORM:2026:203"]["alert_type"] != "convocatoria"
    assert all(alert["confidence"] in {"high", "medium"} for alert in payload["alerts"])


def test_dry_run_opposition_alerts_assigns_broad_and_review_scopes(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    connection = connect(str(db_path))
    initialize_database(connection)
    repository = OfficialSourcesRepository(connection)
    source = repository.ensure_official_source_bopv()
    examples = [
        (
            "BOPV:2026:301",
            "Anuncio relativo a la Oferta de Empleo Publico para el año 2026",
            "ope",
            "broad",
        ),
        (
            "BOPV:2026:302",
            "Orden por la que se anuncia la convocatoria publica para la provision "
            "por el sistema de libre designacion de un puesto de trabajo",
            "libre_designacion",
            "broad",
        ),
        (
            "BOPV:2026:303",
            "Resolucion por la que se nombra profesora agregada de Universidad "
            "cuyo concurso de acceso a plazas fue convocado anteriormente",
            "universidad_profesorado",
            "broad",
        ),
        (
            "BOPV:2026:304",
            "Real Decreto por el que se nombra Directora General de Coordinacion",
            "nombramiento",
            "review_only",
        ),
    ]
    for external_id, title, _expected_type, _expected_scope in examples:
        repository.upsert_document(
            source_id=source["id"],
            external_id=external_id,
            publication_date="2026-05-20",
            title=title,
            department="Gobierno Vasco",
            url_html=f"https://www.euskadi.eus/bopv2/datos/2026/05/{external_id[-3:]}.shtml",
        )

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "dry-run-opposition-alerts",
            "--source",
            "BOPV",
            "--date-from",
            "2026-05-20",
            "--date-to",
            "2026-05-20",
            "--format",
            "json",
            "--limit",
            "10",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    alerts_by_id = {alert["document_identifier"]: alert for alert in payload["alerts"]}
    assert exit_code == 0
    assert payload["summary"]["alerts_found"] == len(examples)
    for external_id, _title, expected_type, expected_scope in examples:
        assert alerts_by_id[external_id]["alert_type"] == expected_type
        assert alerts_by_id[external_id]["alert_scope"] == expected_scope


def test_find_source_candidates_alias_supports_boja_dry_run(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    connection = connect(str(db_path))
    initialize_database(connection)
    repository = OfficialSourcesRepository(connection)
    boe_source = repository.ensure_official_source_boe()
    boja_source = repository.ensure_official_source_boja()
    repository.upsert_document(
        source_id=boe_source["id"],
        external_id="BOE-A-2024-11111",
        publication_date="2024-05-29",
        title="Convocatoria de ayudas estatales",
    )
    repository.upsert_document(
        source_id=boja_source["id"],
        external_id="BOJA:disposition.2026.94.5",
        publication_date="2024-05-29",
        title="Subvenciones para formacion profesional",
        department="Consejeria de Desarrollo Educativo y Formacion Profesional",
        section="3. Otras disposiciones",
    )

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "find-source-candidates",
            "--source",
            "BOJA",
            "--date-from",
            "2024-05-29",
            "--date-to",
            "2024-05-29",
            "--profile",
            "la-ayuda",
            "--dry-run",
        ]
    )

    candidate_count = connection.execute(
        "SELECT COUNT(*) AS count FROM source_candidates"
    ).fetchone()["count"]
    captured = capsys.readouterr()
    assert exit_code == 0
    assert candidate_count == 0
    assert "source=BOJA" in captured.out
    assert "documents_scanned=1" in captured.out
    assert "matches_after_filters=1" in captured.out
    assert "BOJA:disposition.2026.94.5" in captured.out
    assert "BOE-A-2024-11111" not in captured.out


def test_find_source_candidates_alias_supports_all_metadata_sources_dry_run(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    connection = connect(str(db_path))
    initialize_database(connection)
    repository = OfficialSourcesRepository(connection)
    sources = {
        "DOGV": repository.ensure_official_source_dogv(),
        "BOCM": repository.ensure_official_source_bocm(),
        "BDNS": repository.ensure_official_source_bdns(),
        "BOPV": repository.ensure_official_source_bopv(),
        "BOA": repository.ensure_official_source_boa(),
        "BORM": repository.ensure_official_source_borm(),
        "DOGC": repository.ensure_official_source_dogc(),
    }
    for source_code, source in sources.items():
        repository.upsert_document(
            source_id=source["id"],
            external_id=f"{source_code}:candidate-1",
            publication_date="2026-05-20",
            title=f"Convocatoria de ayudas {source_code}",
        )

    for source_code in sources:
        exit_code = run(
            [
                "--db-path",
                str(db_path),
                "find-source-candidates",
                "--source",
                source_code,
                "--date-from",
                "2026-05-20",
                "--date-to",
                "2026-05-20",
                "--keywords",
                "ayudas",
                "--dry-run",
            ]
        )

        captured = capsys.readouterr()
        assert exit_code == 0
        assert f"source={source_code}" in captured.out
        assert "documents_scanned=1" in captured.out
        assert f"{source_code}:candidate-1" in captured.out
        for other_source_code in sources.keys() - {source_code}:
            assert f"{other_source_code}:candidate-1" not in captured.out

    candidate_count = connection.execute(
        "SELECT COUNT(*) AS count FROM source_candidates"
    ).fetchone()["count"]
    assert candidate_count == 0


def test_find_source_candidates_supports_new_autonomous_profiles_and_filters_noise(
    tmp_path, capsys
):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    connection = connect(str(db_path))
    initialize_database(connection)
    repository = OfficialSourcesRepository(connection)
    source_factories = {
        "BOPV": repository.ensure_official_source_bopv,
        "BOA": repository.ensure_official_source_boa,
        "BORM": repository.ensure_official_source_borm,
        "DOGC": repository.ensure_official_source_dogc,
    }
    profiles = {
        "BOPV": "bopv-ayudas",
        "BOA": "boa-ayudas",
        "BORM": "borm-ayudas",
        "DOGC": "dogc-ayudas",
    }
    for source_code, ensure_source in source_factories.items():
        source = ensure_source()
        repository.upsert_document(
            source_id=source["id"],
            external_id=f"{source_code}:weak-generic",
            publication_date="2026-05-20",
            title="Resolucion de convocatoria de subvenciones",
            department="Departamento de Industria",
            section="Otras disposiciones",
        )
        repository.upsert_document(
            source_id=source["id"],
            external_id=f"{source_code}:employment-noise",
            publication_date="2026-05-20",
            title="Convocatoria de bolsas de empleo, nombramientos y tribunales",
            department="Funcion Publica",
            section="Autoridades y personal",
        )
        repository.upsert_document(
            source_id=source["id"],
            external_id=f"{source_code}:student-aid",
            publication_date="2026-05-20",
            title="Convocatoria de ayudas al estudio para alumnado universitario",
            department="Educacion",
            section="Ayudas",
        )
        repository.upsert_document(
            source_id=source["id"],
            external_id=f"{source_code}:young-rent",
            publication_date="2026-05-20",
            title="Convocatoria de bono alquiler joven para familias",
            department="Vivienda",
            section="Ayudas",
        )

        exit_code = run(
            [
                "--db-path",
                str(db_path),
                "find-source-candidates",
                "--source",
                source_code,
                "--date-from",
                "2026-05-20",
                "--date-to",
                "2026-05-20",
                "--profile",
                profiles[source_code],
                "--dry-run",
                "--limit",
                "10",
            ]
        )

        captured = capsys.readouterr()
        assert exit_code == 0
        assert f"source={source_code}" in captured.out
        assert "documents_scanned=4" in captured.out
        assert "matches_total=4" in captured.out
        assert "matches_after_filters=2" in captured.out
        assert "excluded_by_keyword_rules=2" in captured.out
        assert f"{source_code}:student-aid" in captured.out
        assert f"{source_code}:young-rent" in captured.out
        assert f"{source_code}:weak-generic" not in captured.out
        assert f"{source_code}:employment-noise" not in captured.out

    candidate_count = connection.execute(
        "SELECT COUNT(*) AS count FROM source_candidates"
    ).fetchone()["count"]
    assert candidate_count == 0


def test_find_source_candidates_boa_profile_filters_non_student_facing_noise(
    tmp_path, capsys
):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    connection = connect(str(db_path))
    initialize_database(connection)
    repository = OfficialSourcesRepository(connection)
    source = repository.ensure_official_source_boa()
    documents = [
        (
            "BOA:material-curricular",
            (
                "ORDEN ECU/817/2026, de 29 de mayo, por la que se convocan ayudas "
                "para la adquisicion y el uso de material curricular de alumnado "
                "escolarizado en etapas obligatorias de centros sostenidos con fondos "
                "publicos de la Comunidad Autonoma de Aragon para el curso 2026/2027."
            ),
            "DEPARTAMENTO DE EDUCACION, CIENCIA Y UNIVERSIDADES",
        ),
        (
            "BOA:comedor",
            (
                "ORDEN ECU/818/2026, de 29 de mayo, por la que se convocan becas "
                "que faciliten la utilizacion del servicio de comedor escolar por parte "
                "del alumnado de centros docentes sostenidos con fondos publicos de la "
                "Comunidad Autonoma de Aragon para el curso 2026/2027."
            ),
            "DEPARTAMENTO DE EDUCACION, CIENCIA Y UNIVERSIDADES",
        ),
        (
            "BOA:erasmus",
            (
                "EXTRACTO de la Orden ECU/815/2026, de 21 de mayo, por la que se "
                "convocan las becas complementarias a las del Programa Erasmus + y a "
                "las de otros programas de movilidad internacional para el curso "
                "academico 2026-2027."
            ),
            "DEPARTAMENTO DE EDUCACION, CIENCIA Y UNIVERSIDADES",
        ),
        (
            "BOA:young-creators",
            (
                "ORDEN DBF/799/2026, de 19 mayo, por la que se convoca el certamen "
                "IX Premio Jovenes Creadores Aragoneses para el ano 2026."
            ),
            (
                "VICEPRESIDENCIA DEL GOBIERNO Y DEPARTAMENTO DE DESREGULACION, "
                "BIENESTAR SOCIAL Y FAMILIA"
            ),
        ),
        (
            "BOA:ces-practices",
            (
                "RESOLUCION de 11 de mayo de 2026, del Presidente del Consejo "
                "Economico y Social de Aragon, por la que se convoca una beca de "
                "formacion y practicas en el Consejo Economico y Social de Aragon."
            ),
            "CONSEJO ECONOMICO Y SOCIAL",
        ),
        (
            "BOA:renuncia",
            (
                "ORDEN ECU/725/2026, de 7 de mayo, por la que se acepta la renuncia "
                "presentada por persona beneficiaria de ayuda adjudicada a personas "
                "becarias auxiliares de conversacion con destino en centros educativos."
            ),
            "DEPARTAMENTO DE EDUCACION, CIENCIA Y UNIVERSIDADES",
        ),
        (
            "BOA:atencion-temprana",
            (
                "ORDEN BSF/714/2026, de 28 de abril, por la que se hace publica la "
                "convocatoria de ayudas individuales de pago directo a las familias "
                "para atencion temprana, ano 2026."
            ),
            "DEPARTAMENTO DE BIENESTAR SOCIAL Y FAMILIA",
        ),
        (
            "BOA:calendario",
            (
                "RESOLUCION de 16 de abril de 2026, por la que se establece el "
                "calendario de admision y matriculacion de alumnado de Educacion "
                "Secundaria para personas adultas."
            ),
            "DEPARTAMENTO DE EDUCACION, CULTURA Y DEPORTE",
        ),
        (
            "BOA:student-associations",
            (
                "EXTRACTO de la Orden ECU/795/2026, de 18 de mayo, por la que se "
                "convocan subvenciones destinadas a las asociaciones de estudiantes "
                "sin animo de lucro en el ambito universitario para el ano 2026."
            ),
            "DEPARTAMENTO DE EDUCACION, CIENCIA Y UNIVERSIDADES",
        ),
    ]
    for external_id, title, department in documents:
        repository.upsert_document(
            source_id=source["id"],
            external_id=external_id,
            publication_date="2026-06-05",
            title=title,
            department=department,
            section="III. Otras Disposiciones y Acuerdos",
        )

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "find-source-candidates",
            "--source",
            "BOA",
            "--date-from",
            "2026-06-05",
            "--date-to",
            "2026-06-05",
            "--profile",
            "boa-ayudas",
            "--dry-run",
            "--limit",
            "20",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "documents_scanned=9" in captured.out
    assert "matches_total=9" in captured.out
    assert "matches_after_filters=3" in captured.out
    assert "excluded_by_keyword_rules=6" in captured.out
    assert "BOA:material-curricular" in captured.out
    assert "BOA:comedor" in captured.out
    assert "BOA:erasmus" in captured.out
    assert "BOA:young-creators" not in captured.out
    assert "BOA:ces-practices" not in captured.out
    assert "BOA:renuncia" not in captured.out
    assert "BOA:atencion-temprana" not in captured.out
    assert "BOA:calendario" not in captured.out
    assert "BOA:student-associations" not in captured.out

    candidate_count = connection.execute(
        "SELECT COUNT(*) AS count FROM source_candidates"
    ).fetchone()["count"]
    assert candidate_count == 0


def test_find_source_candidates_dogc_profile_filters_selection_and_internal_practice_noise(
    tmp_path, capsys
):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    connection = connect(str(db_path))
    initialize_database(connection)
    repository = OfficialSourcesRepository(connection)
    source = repository.ensure_official_source_dogc()
    documents = [
        (
            "DOGC:menjador",
            (
                "Edicte sobre aprovacio inicial de les bases per a la concessio "
                "d'ajuts individuals de menjador atorgats a l'alumnat "
                "d'ensenyaments obligatoris i d'educacio infantil de centres "
                "educatius sufragats amb fons publics per al curs escolar 2026-2027"
            ),
            "Consell Comarcal del Pla d'Urgell",
            "Administracio local",
        ),
        (
            "DOGC:mobilitat",
            (
                "Anunci sobre aprovacio inicial de les bases reguladores d'ajuts "
                "en forma de beques individuals per a la mobilitat de persones "
                "joves estudiants"
            ),
            "Ajuntament de Santa Coloma de Cervello",
            "Administracio local",
        ),
        (
            "DOGC:selection-noise",
            (
                "Anunci sobre aprovacio provisional de la llista d'admissions i "
                "exclusions del proces de seleccio corresponent a la modificacio "
                "de l'oferta publica d'ocupacio d'una placa de personal laboral fix "
                "adscrita a l'ambit de joves vulnerables"
            ),
            "Consell Comarcal del Valles Oriental",
            "Administracio local",
        ),
        (
            "DOGC:internal-practice",
            (
                "Resolucio per la qual s'aproven les bases especifiques que han de "
                "regir la concessio de beques per fer practiques al Departament de "
                "Politica Linguistica o a les seves entitats adscrites"
            ),
            "Departament de Politica Linguistica",
            "Altres disposicions",
        ),
    ]

    for external_id, title, department, section in documents:
        repository.upsert_document(
            source_id=source["id"],
            external_id=external_id,
            publication_date="2026-06-05",
            title=title,
            department=department,
            section=section,
        )

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "find-source-candidates",
            "--source",
            "DOGC",
            "--date-from",
            "2026-06-05",
            "--date-to",
            "2026-06-05",
            "--profile",
            "dogc-ayudas",
            "--dry-run",
            "--limit",
            "10",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "documents_scanned=4" in captured.out
    assert "matches_total=4" in captured.out
    assert "matches_after_filters=2" in captured.out
    assert "excluded_by_keyword_rules=2" in captured.out
    assert "DOGC:menjador" in captured.out
    assert "DOGC:mobilitat" in captured.out
    assert "DOGC:selection-noise" not in captured.out
    assert "DOGC:internal-practice" not in captured.out

    candidate_count = connection.execute(
        "SELECT COUNT(*) AS count FROM source_candidates"
    ).fetchone()["count"]
    assert candidate_count == 0


def test_find_source_candidates_docm_profile_filters_non_student_facing_noise(
    tmp_path, capsys
):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    connection = connect(str(db_path))
    initialize_database(connection)
    repository = OfficialSourcesRepository(connection)
    source = repository.ensure_official_source_docm()
    documents = [
        (
            "DOCM:school-transport",
            (
                "Ayudas y Subvenciones. Correccion de errores del Decreto por "
                "el que se aprueban las bases reguladoras de la concesion directa "
                "de las ayudas individuales de transporte escolar para el alumnado "
                "matriculado en centros docentes publicos no universitarios"
            ),
            "Consejeria de Educacion, Cultura y Deportes",
            "I.- DISPOSICIONES GENERALES",
        ),
        (
            "DOCM:study-aid",
            (
                "Ayudas y Subvenciones. Orden por la que se convocan ayudas al "
                "estudio para alumnado matriculado en formacion profesional"
            ),
            "Consejeria de Educacion, Cultura y Deportes",
            "III.- OTRAS DISPOSICIONES Y ACTOS",
        ),
        (
            "DOCM:entrepreneur-noise",
            (
                "Ayudas y Subvenciones. Orden por la que se establecen las bases "
                "reguladoras para la concesion de ayudas para la tutorizacion y "
                "asesoramiento a personas emprendedoras"
            ),
            "Consejeria de Economia, Empresas y Empleo",
            "I.- DISPOSICIONES GENERALES",
        ),
        (
            "DOCM:social-notification-noise",
            (
                "Notificaciones. Notificacion de la Delegacion Provincial de "
                "Bienestar Social por la que se acuerda la publicacion de la "
                "propuesta de resolucion desfavorable de la solicitud de ayuda de "
                "emergencia social"
            ),
            "Consejeria de Bienestar Social",
            "III.- OTRAS DISPOSICIONES Y ACTOS",
        ),
        (
            "DOCM:collaboration-noise",
            (
                "Universidades. Extracto de la Universidad de Castilla-La Mancha "
                "de la convocatoria de beca de colaboracion en las actividades "
                "promovidas por la Catedra Institucional de Profesionalizacion de "
                "la Contratacion Publica"
            ),
            "Universidad de Castilla-La Mancha",
            "III.- OTRAS DISPOSICIONES Y ACTOS",
        ),
    ]

    for external_id, title, department, section in documents:
        repository.upsert_document(
            source_id=source["id"],
            external_id=external_id,
            publication_date="2026-06-05",
            title=title,
            department=department,
            section=section,
        )

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "find-source-candidates",
            "--source",
            "DOCM",
            "--date-from",
            "2026-06-05",
            "--date-to",
            "2026-06-05",
            "--profile",
            "docm-ayudas",
            "--dry-run",
            "--limit",
            "10",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "documents_scanned=5" in captured.out
    assert "matches_total=5" in captured.out
    assert "matches_after_filters=2" in captured.out
    assert "excluded_by_keyword_rules=3" in captured.out
    assert "DOCM:school-transport" in captured.out
    assert "DOCM:study-aid" in captured.out
    assert "DOCM:entrepreneur-noise" not in captured.out
    assert "DOCM:social-notification-noise" not in captured.out
    assert "DOCM:collaboration-noise" not in captured.out

    candidate_count = connection.execute(
        "SELECT COUNT(*) AS count FROM source_candidates"
    ).fetchone()["count"]
    assert candidate_count == 0


def test_find_source_candidates_bopa_profile_filters_live_noise_and_keeps_student_aid(
    tmp_path, capsys
):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    connection = connect(str(db_path))
    initialize_database(connection)
    repository = OfficialSourcesRepository(connection)
    bopa_source = repository.upsert_official_source(
        code="BOPA",
        name="Boletin Oficial del Principado de Asturias",
        jurisdiction="ES",
        region_code="ES-AS",
        base_url="https://miprincipado.asturias.es/bopa-sumario",
        access_type="official_html",
        reliability_level="canonical",
    )
    examples = [
        (
            "BOPA:student-geology-aid",
            "Extracto de la Resolucion del Vicerrector de Estudiantes y Empleabilidad "
            "por la que se aprueba la convocatoria publica de ayudas a estudiantes "
            "destinadas a financiar campamentos geologicos de estudios de Grado",
            "UNIVERSIDAD DE OVIEDO",
            "I. Principado de Asturias",
        ),
        (
            "BOPA:collaboration-scholarship",
            "Extracto de la Resolucion por la que se aprueba la convocatoria de una "
            "beca de colaboracion para los servicios de normalizacion linguistica",
            "UNIVERSIDAD DE OVIEDO",
            "I. Principado de Asturias",
        ),
        (
            "BOPA:sports-university-aid",
            "Extracto de la Resolucion por la que se aprueba la convocatoria publica "
            "para la concesion de ayudas a los componentes de los equipos deportivos "
            "y campeonatos universitarios",
            "UNIVERSIDAD DE OVIEDO",
            "I. Principado de Asturias",
        ),
        (
            "BOPA:doctoral-convenio",
            "Convenio de colaboracion entre la Universidad de Oviedo y Banca March "
            "para la realizacion de una tesis doctoral con mencion industrial",
            "UNIVERSIDAD DE OVIEDO",
            "I. Principado de Asturias",
        ),
        (
            "BOPA:research-hiring",
            "Extracto de la Resolucion por la que se aprueba la convocatoria para la "
            "contratacion de personal investigador y personal tecnico de apoyo",
            "UNIVERSIDAD DE OVIEDO",
            "I. Principado de Asturias",
        ),
        (
            "BOPA:home-help",
            "Anuncio de exposicion del padron de beneficiarios del servicio de ayuda "
            "a domicilio",
            "Ayuntamiento",
            "V. Administracion local",
        ),
        (
            "BOPA:agrarian-subsidy",
            "Resolucion por la que se concede la subvencion Ecorregimen agroecologia "
            "en tierras de cultivo",
            "Consejeria de Medio Rural y Politica Agraria",
            "I. Principado de Asturias",
        ),
    ]
    for external_id, title, department, section in examples:
        repository.upsert_document(
            source_id=bopa_source["id"],
            external_id=external_id,
            publication_date="2026-06-05",
            title=title,
            department=department,
            section=section,
        )

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "find-source-candidates",
            "--source",
            "BOPA",
            "--date-from",
            "2026-06-05",
            "--date-to",
            "2026-06-05",
            "--profile",
            "bopa-ayudas",
            "--dry-run",
            "--limit",
            "10",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "source=BOPA" in captured.out
    assert "matches_total=7" in captured.out
    assert "matches_after_filters=3" in captured.out
    assert "excluded_by_keyword_rules=4" in captured.out
    assert "BOPA:student-geology-aid" in captured.out
    assert "BOPA:collaboration-scholarship" in captured.out
    assert "BOPA:sports-university-aid" in captured.out
    assert "BOPA:doctoral-convenio" not in captured.out
    assert "BOPA:research-hiring" not in captured.out
    assert "BOPA:home-help" not in captured.out
    assert "BOPA:agrarian-subsidy" not in captured.out

    candidate_count = connection.execute(
        "SELECT COUNT(*) AS count FROM source_candidates"
    ).fetchone()["count"]
    assert candidate_count == 0


def test_find_source_candidates_bopv_profile_keeps_direct_aid_despite_raw_noise(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    connection = connect(str(db_path))
    initialize_database(connection)
    repository = OfficialSourcesRepository(connection)
    source = repository.ensure_official_source_bopv()
    repository.upsert_document(
        source_id=source["id"],
        external_id="BOPV:fp-aid",
        publication_date="2026-05-20",
        title=(
            "ORDEN de la consejera de Educacion por la que se aprueban las bases "
            "reguladoras de la convocatoria de subvenciones para formacion profesional"
        ),
        department="Departamento de Educacion",
        section="Otras disposiciones",
        raw_metadata={"neighbor_section": "oposiciones y concursos"},
    )
    repository.upsert_document(
        source_id=source["id"],
        external_id="BOPV:university-aid",
        publication_date="2026-05-20",
        title=(
            "ORDEN del consejero de Ciencia, Universidades e Innovacion por la que se "
            "aprueban las bases reguladoras de ayudas para universidad"
        ),
        department="Departamento de Ciencia, Universidades e Innovacion",
        section="Otras disposiciones",
        raw_metadata={"neighbor_notice": "contratacion de empresas"},
    )
    repository.upsert_document(
        source_id=source["id"],
        external_id="BOPV:student-notification",
        publication_date="2026-05-20",
        title=("ANUNCIO de notificaciones relativas a resoluciones de subvenciones para alumnado"),
        department="Departamento de Educacion",
        section="Anuncios",
    )
    repository.upsert_document(
        source_id=source["id"],
        external_id="BOPV:beneficiary-result",
        publication_date="2026-05-20",
        title=(
            "RESOLUCION del consejero de Ciencia, Universidades e Innovacion "
            "por la que se hace publica la relacion de beneficiarios "
            "de las ayudas para estancias universitarias"
        ),
        department="Departamento de Ciencia, Universidades e Innovacion",
        section="Otras disposiciones",
    )

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "find-source-candidates",
            "--source",
            "BOPV",
            "--date-from",
            "2026-05-20",
            "--date-to",
            "2026-05-20",
            "--profile",
            "bopv-ayudas",
            "--dry-run",
            "--limit",
            "10",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "matches_after_filters=2" in captured.out
    assert "excluded_by_keyword_rules=2" in captured.out
    assert "BOPV:fp-aid" in captured.out
    assert "BOPV:university-aid" in captured.out
    assert "BOPV:student-notification" not in captured.out
    assert "BOPV:beneficiary-result" not in captured.out


def test_find_source_candidates_bopv_profile_supports_basque_student_terms(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    connection = connect(str(db_path))
    initialize_database(connection)
    repository = OfficialSourcesRepository(connection)
    source = repository.ensure_official_source_bopv()
    repository.upsert_document(
        source_id=source["id"],
        external_id="BOPV:generic-laguntza",
        publication_date="2026-05-20",
        title="EBAZPENA laguntza bati buruzkoa",
        department="Saila",
        section="Bestelako xedapenak",
    )
    repository.upsert_document(
        source_id=source["id"],
        external_id="BOPV:ikasle-aid",
        publication_date="2026-05-20",
        title="AGINDUA ikasleak laguntzeko dirulaguntzak deitzen dituena",
        department="Hezkuntza Saila",
        section="Bestelako xedapenak",
    )

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "find-source-candidates",
            "--source",
            "BOPV",
            "--date-from",
            "2026-05-20",
            "--date-to",
            "2026-05-20",
            "--profile",
            "bopv-ayudas",
            "--dry-run",
            "--limit",
            "10",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "matches_total=2" in captured.out
    assert "matches_after_filters=1" in captured.out
    assert "BOPV:ikasle-aid" in captured.out
    assert "BOPV:generic-laguntza" not in captured.out


def test_find_source_candidates_borm_profile_filters_noise_and_preserves_aids(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    connection = connect(str(db_path))
    initialize_database(connection)
    repository = OfficialSourcesRepository(connection)
    source = repository.ensure_official_source_borm()
    examples = [
        (
            "BORM:school-material",
            "Convocatoria de ayudas para la adquisicion de libros de texto y material escolar",
            "Fortuna",
        ),
        (
            "BORM:study-grant",
            "Convocatoria para la obtencion de ayudas al estudio para estudiantes universitarios",
            "Universidad de Murcia",
        ),
        (
            "BORM:youth-mobility",
            "Convocatoria de ayudas a la movilidad internacional para jovenes",
            "Cartagena",
        ),
        (
            "BORM:profesorado-noise",
            "Resolucion por la que se convoca concurso publico para plazas de "
            "Profesorado Ayudante Doctor",
            "Universidad de Murcia",
        ),
        (
            "BORM:job-pool-noise",
            "Bolsa de trabajo de Orientadores Laborales dirigidos a personas jovenes",
            "Alguazas",
        ),
        (
            "BORM:contest-noise",
            "Convocatoria del Certamen de Creacion Artistica Joven",
            "Molina de Segura",
        ),
        (
            "BORM:entity-project-noise",
            "Convocatoria de subvenciones dirigidas a entidades del Tercer Sector para proyectos",
            "Instituto Murciano de Accion Social",
        ),
        (
            "BORM:convenio-noise",
            "Autorizacion del convenio de colaboracion para la prestacion sanitaria",
            "Consejeria de Politica Social, Familias e Igualdad",
        ),
        (
            "BORM:concesion-result-noise",
            "Decreto-Ley por el que se autoriza la concesion directa de diversas subvenciones",
            "Consejo de Gobierno",
        ),
        (
            "BORM:disability-aid",
            "Convocatoria de subvenciones para integracion laboral de personas con discapacidad",
            "Servicio Regional de Empleo y Formacion",
        ),
    ]
    for external_id, title, department in examples:
        repository.upsert_document(
            source_id=source["id"],
            external_id=external_id,
            publication_date="2026-05-20",
            title=title,
            department=department,
            section="I. Comunidad Autonoma",
        )

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "find-source-candidates",
            "--source",
            "BORM",
            "--date-from",
            "2026-05-20",
            "--date-to",
            "2026-05-20",
            "--profile",
            "borm-ayudas",
            "--dry-run",
            "--limit",
            "20",
        ]
    )

    candidate_count = connection.execute(
        "SELECT COUNT(*) AS count FROM source_candidates"
    ).fetchone()["count"]
    captured = capsys.readouterr()

    assert exit_code == 0
    assert candidate_count == 0
    assert "matches_total=10" in captured.out
    assert "matches_after_filters=4" in captured.out
    assert "excluded_by_keyword_rules=6" in captured.out
    assert "BORM:school-material" in captured.out
    assert "BORM:study-grant" in captured.out
    assert "BORM:youth-mobility" in captured.out
    assert "BORM:disability-aid" in captured.out
    assert "BORM:profesorado-noise" not in captured.out
    assert "BORM:job-pool-noise" not in captured.out
    assert "BORM:contest-noise" not in captured.out
    assert "BORM:entity-project-noise" not in captured.out
    assert "BORM:convenio-noise" not in captured.out
    assert "BORM:concesion-result-noise" not in captured.out


def test_find_boe_candidates_boja_profile_excludes_generic_ayudas_only(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    connection = connect(str(db_path))
    initialize_database(connection)
    repository = OfficialSourcesRepository(connection)
    boja_source = repository.ensure_official_source_boja()
    repository.upsert_document(
        source_id=boja_source["id"],
        external_id="BOJA:generic-ayudas",
        publication_date="2026-05-20",
        title="Resolucion por la que se conceden ayudas a entidades locales",
        department="Ayuntamientos",
    )

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "find-boe-candidates",
            "--source",
            "BOJA",
            "--date-from",
            "2026-05-20",
            "--date-to",
            "2026-05-20",
            "--profile",
            "boja-ayudas",
            "--dry-run",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "source=BOJA" in captured.out
    assert "matches_total=1" in captured.out
    assert "matches_after_filters=0" in captured.out
    assert "excluded_by_keyword_rules=1" in captured.out
    assert "BOJA:generic-ayudas" not in captured.out


def test_find_boe_candidates_boja_profile_matches_education_signals(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    connection = connect(str(db_path))
    initialize_database(connection)
    repository = OfficialSourcesRepository(connection)
    boja_source = repository.ensure_official_source_boja()
    repository.upsert_document(
        source_id=boja_source["id"],
        external_id="BOJA:student-aid",
        publication_date="2026-05-20",
        title="Convocatoria de becas para estudiantes universitarios",
        department="Universidades",
    )

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "find-boe-candidates",
            "--source",
            "BOJA",
            "--date-from",
            "2026-05-20",
            "--date-to",
            "2026-05-20",
            "--profile",
            "boja-ayudas",
            "--dry-run",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "matches_after_filters=1" in captured.out
    assert "matched_keywords=becas,convocatoria,estudiantes" in captured.out
    assert "strong_keyword:becas" in captured.out
    assert "BOJA:student-aid" in captured.out


def test_find_boe_candidates_boja_profile_treats_transport_contextually(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    connection = connect(str(db_path))
    initialize_database(connection)
    repository = OfficialSourcesRepository(connection)
    boja_source = repository.ensure_official_source_boja()
    repository.upsert_document(
        source_id=boja_source["id"],
        external_id="BOJA:transport-generic",
        publication_date="2026-05-20",
        title="Subvenciones para transporte de mercancias",
        department="Consejeria de Fomento, Articulacion del Territorio y Vivienda",
    )
    repository.upsert_document(
        source_id=boja_source["id"],
        external_id="BOJA:transport-school",
        publication_date="2026-05-20",
        title="Ayudas para transporte escolar del alumnado",
        department="Consejeria de Desarrollo Educativo y Formacion Profesional",
    )

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "find-boe-candidates",
            "--source",
            "BOJA",
            "--date-from",
            "2026-05-20",
            "--date-to",
            "2026-05-20",
            "--profile",
            "boja-ayudas",
            "--dry-run",
            "--limit",
            "10",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "matches_total=2" in captured.out
    assert "matches_after_filters=1" in captured.out
    assert "BOJA:transport-school" in captured.out
    assert "BOJA:transport-generic" not in captured.out
    assert "transporte escolar" in captured.out


def test_find_boe_candidates_boja_profile_excludes_young_housing_without_student_context(
    tmp_path, capsys
):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    connection = connect(str(db_path))
    initialize_database(connection)
    repository = OfficialSourcesRepository(connection)
    boja_source = repository.ensure_official_source_boja()
    repository.upsert_document(
        source_id=boja_source["id"],
        external_id="BOJA:young-rent",
        publication_date="2026-05-20",
        title="Ayudas al alquiler para jovenes",
        department="Consejeria de Fomento, Articulacion del Territorio y Vivienda",
    )

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "find-boe-candidates",
            "--source",
            "BOJA",
            "--date-from",
            "2026-05-20",
            "--date-to",
            "2026-05-20",
            "--profile",
            "boja-ayudas",
            "--dry-run",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "matches_total=1" in captured.out
    assert "matches_after_filters=0" in captured.out
    assert "excluded_by_keyword_rules=1" in captured.out
    assert "BOJA:young-rent" not in captured.out


def test_find_boe_candidates_boja_profile_filters_live_noise_and_keeps_student_aid(
    tmp_path, capsys
):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    connection = connect(str(db_path))
    initialize_database(connection)
    repository = OfficialSourcesRepository(connection)
    boja_source = repository.ensure_official_source_boja()
    examples = [
        (
            "BOJA:employment-disability",
            "Resolucion por la que se aprueban las listas definitivas de personas aspirantes "
            "que superan el concurso-oposicion para personas con discapacidad intelectual",
            "Consejeria de Sanidad, Presidencia y Emergencias",
            "2. Autoridades y personal",
        ),
        (
            "BOJA:fpe-notification",
            "Anuncio mediante el que se publica relacion de solicitantes de ayuda de Formacion "
            "Profesional para el Empleo a los que no ha sido posible notificar resolucion de beca",
            "Consejeria de Empleo, Empresa y Trabajo Autonomo",
            "5. Anuncios",
        ),
        (
            "BOJA:language-certificate",
            "Resolucion por la que se regula el procedimiento para la obtencion del certificado "
            "de nivel Intermedio B2 de idiomas para el alumnado que cursa Bachillerato bilingue",
            "Consejeria de Desarrollo Educativo y Formacion Profesional",
            "3. Otras disposiciones",
        ),
        (
            "BOJA:admission-lottery",
            "Resolucion por la que se anuncia la hora y el lugar para la celebracion del sorteo "
            "publico establecido en el procedimiento de admision del alumnado en centros docentes",
            "Consejeria de Desarrollo Educativo y Formacion Profesional",
            "3. Otras disposiciones",
        ),
        (
            "BOJA:resolved-training-grant",
            "Resolucion por la que se resuelve la convocatoria de seis becas de formacion "
            "de personal bibliotecario adscritas a la biblioteca de la Universidad",
            "Universidades",
            "3. Otras disposiciones",
        ),
        (
            "BOJA:student-master-aid",
            "Extracto de la Resolucion por la que se convocan becas de atraccion de talento "
            "para estudiantes de Master",
            "Universidades",
            "1. Disposiciones generales",
        ),
    ]
    for external_id, title, department, section in examples:
        repository.upsert_document(
            source_id=boja_source["id"],
            external_id=external_id,
            publication_date="2026-05-20",
            title=title,
            department=department,
            section=section,
        )

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "find-boe-candidates",
            "--source",
            "BOJA",
            "--date-from",
            "2026-05-20",
            "--date-to",
            "2026-05-20",
            "--profile",
            "boja-ayudas",
            "--dry-run",
            "--limit",
            "10",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "matches_total=5" in captured.out
    assert "matches_after_filters=1" in captured.out
    assert "excluded_by_keyword_rules=4" in captured.out
    assert "BOJA:student-master-aid" in captured.out
    assert "BOJA:employment-disability" not in captured.out
    assert "BOJA:fpe-notification" not in captured.out
    assert "BOJA:language-certificate" not in captured.out
    assert "BOJA:admission-lottery" not in captured.out
    assert "BOJA:resolved-training-grant" not in captured.out


def test_find_source_candidates_dogv_profile_filters_noise_and_keeps_direct_aid(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    connection = connect(str(db_path))
    initialize_database(connection)
    repository = OfficialSourcesRepository(connection)
    dogv_source = repository.ensure_official_source_dogv()
    documents = [
        (
            "DOGV:generic-ayudas",
            "Resolucion de concesion de ayudas a entidades locales",
            "Vicepresidencia Segunda y Conselleria de Presidencia",
            "III. ACTOS ADMINISTRATIVOS / B) SUBVENCIONES Y BECAS",
        ),
        (
            "DOGV:sector-agrario",
            "Resolucion por la que se convocan subvenciones para el sector agrario",
            "Conselleria de Agricultura, Agua, Ganaderia y Pesca",
            "III. ACTOS ADMINISTRATIVOS / B) SUBVENCIONES Y BECAS",
        ),
        (
            "DOGV:oposiciones-vivienda",
            "Resolucion por la que se publica la relacion definitiva de personas "
            "que han superado las pruebas selectivas de la convocatoria 6/2025",
            "Entidad Valenciana de Vivienda y Suelo",
            "II. AUTORIDADES Y PERSONAL / A) OFERTAS DE EMPLEO PUBLICO, OPOSICIONES Y CONCURSOS",
        ),
        (
            "DOGV:concesion-result",
            "Resolucion de concesion de ayudas a empresas beneficiarias",
            "Conselleria de Industria, Turismo, Innovacion y Comercio",
            "III. ACTOS ADMINISTRATIVOS / B) SUBVENCIONES Y BECAS",
        ),
        (
            "DOGV:transporte-escolar",
            "Convocatoria de ayudas para transporte escolar del alumnado",
            "Conselleria de Educacion, Cultura y Universidades",
            "III. ACTOS ADMINISTRATIVOS / B) SUBVENCIONES Y BECAS",
        ),
        (
            "DOGV:ayudas-estudio",
            "Extracto de la resolucion por la que se convocan ayudas al estudio "
            "para estudiantes universitarios",
            "Universidad de Alicante",
            "III. ACTOS ADMINISTRATIVOS / B) SUBVENCIONES Y BECAS",
        ),
        (
            "DOGV:vivienda-jovenes",
            "Convocatoria de ayudas al alquiler de vivienda para jovenes",
            "Vicepresidencia Primera y Conselleria de Vivienda, Empleo, Juventud e Igualdad",
            "III. ACTOS ADMINISTRATIVOS / B) SUBVENCIONES Y BECAS",
        ),
        (
            "DOGV:empresa-sectorial",
            "Convocatoria de subvenciones para empresas del sector industrial",
            "Conselleria de Industria, Turismo, Innovacion y Comercio",
            "III. ACTOS ADMINISTRATIVOS / B) SUBVENCIONES Y BECAS",
        ),
        (
            "DOGV:vineyard-sector",
            "Extracto por el que se amplia el plazo de presentacion de solicitudes "
            "de pago de las ayudas a la reestructuracion y reconversion de vinedo",
            "Agencia Valenciana de Fomento y Garantia Agraria",
            "III. ACTOS ADMINISTRATIVOS / B) SUBVENCIONES Y BECAS",
        ),
        (
            "DOGV:fp-admission",
            "Resolucion por la que se dictan instrucciones del procedimiento de admision "
            "y matricula en formacion profesional",
            "Conselleria de Educacion, Cultura y Universidades",
            "III. ACTOS ADMINISTRATIVOS / C) OTROS ASUNTOS",
        ),
        (
            "DOGV:university-award",
            "Extracto por el que se convoca un premio al mejor trabajo fin de grado",
            "Universitat de Valencia",
            "III. ACTOS ADMINISTRATIVOS / B) SUBVENCIONES Y BECAS",
        ),
    ]
    for external_id, title, department, section in documents:
        repository.upsert_document(
            source_id=dogv_source["id"],
            external_id=external_id,
            publication_date="2026-05-20",
            title=title,
            department=department,
            section=section,
        )

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "find-source-candidates",
            "--source",
            "DOGV",
            "--date-from",
            "2026-05-20",
            "--date-to",
            "2026-05-20",
            "--profile",
            "dogv-ayudas",
            "--dry-run",
            "--limit",
            "10",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "documents_scanned=11" in captured.out
    assert "matches_total=11" in captured.out
    assert "matches_after_filters=3" in captured.out
    assert "excluded_by_keyword_rules=8" in captured.out
    assert "DOGV:transporte-escolar" in captured.out
    assert "DOGV:ayudas-estudio" in captured.out
    assert "DOGV:vivienda-jovenes" in captured.out
    assert "DOGV:generic-ayudas" not in captured.out
    assert "DOGV:sector-agrario" not in captured.out
    assert "DOGV:oposiciones-vivienda" not in captured.out
    assert "DOGV:concesion-result" not in captured.out
    assert "DOGV:empresa-sectorial" not in captured.out
    assert "DOGV:vineyard-sector" not in captured.out
    assert "DOGV:fp-admission" not in captured.out
    assert "DOGV:university-award" not in captured.out
    assert "score_reasons=" in captured.out


def test_find_source_candidates_dogv_profile_dry_run_does_not_write(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    connection = connect(str(db_path))
    initialize_database(connection)
    repository = OfficialSourcesRepository(connection)
    dogv_source = repository.ensure_official_source_dogv()
    repository.upsert_document(
        source_id=dogv_source["id"],
        external_id="DOGV:study-aid",
        publication_date="2026-05-20",
        title="Convocatoria de ayudas al estudio para alumnado universitario",
        department="Universidad de Alicante",
        section="III. ACTOS ADMINISTRATIVOS / B) SUBVENCIONES Y BECAS",
    )

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "find-source-candidates",
            "--source",
            "DOGV",
            "--date-from",
            "2026-05-20",
            "--date-to",
            "2026-05-20",
            "--profile",
            "dogv-ayudas",
            "--dry-run",
        ]
    )

    candidate_count = connection.execute(
        "SELECT COUNT(*) AS count FROM source_candidates"
    ).fetchone()["count"]
    captured = capsys.readouterr()
    assert exit_code == 0
    assert candidate_count == 0
    assert "write_mode=dry_run" in captured.out
    assert "DOGV:study-aid" in captured.out


def test_find_source_candidates_supports_bocyl_profile_and_filters_noise(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    connection = connect(str(db_path))
    initialize_database(connection)
    repository = OfficialSourcesRepository(connection)
    bocyl_source = repository.ensure_official_source_bocyl()
    documents = [
        (
            "BOCYL:vivienda-department-only",
            "RESOLUCION por la que se aprueba definitivamente la modificacion del plan general",
            "CONSEJERIA DE MEDIO AMBIENTE, VIVIENDA Y ORDENACION DEL TERRITORIO",
            "I. COMUNIDAD DE CASTILLA Y LEON",
        ),
        (
            "BOCYL:environmental-noise",
            "RESOLUCION relativa a evaluacion ambiental, montes, caza y pesca",
            "CONSEJERIA DE MEDIO AMBIENTE, VIVIENDA Y ORDENACION DEL TERRITORIO",
            "I. COMUNIDAD DE CASTILLA Y LEON",
        ),
        (
            "BOCYL:generic-subvenciones",
            "ORDEN por la que se establecen subvenciones para entidades locales",
            "CONSEJERIA DE AGRICULTURA, GANADERIA Y DESARROLLO RURAL",
            "I. COMUNIDAD DE CASTILLA Y LEON",
        ),
        (
            "BOCYL:professional-families-noise",
            "ORDEN por la que se habilita personal asesor para distintas familias profesionales",
            "CONSEJERIA DE EDUCACION",
            "I. COMUNIDAD DE CASTILLA Y LEON",
        ),
        (
            "BOCYL:study-aid",
            "ORDEN por la que se convocan ayudas al estudio para alumnado universitario",
            "CONSEJERIA DE EDUCACION",
            "I. COMUNIDAD DE CASTILLA Y LEON",
        ),
        (
            "BOCYL:young-rent",
            "ORDEN por la que se convocan ayudas para bono alquiler joven",
            "CONSEJERIA DE MEDIO AMBIENTE, VIVIENDA Y ORDENACION DEL TERRITORIO",
            "I. COMUNIDAD DE CASTILLA Y LEON",
        ),
    ]
    for external_id, title, department, section in documents:
        repository.upsert_document(
            source_id=bocyl_source["id"],
            external_id=external_id,
            publication_date="2026-05-20",
            title=title,
            department=department,
            section=section,
        )

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "find-source-candidates",
            "--source",
            "BOCYL",
            "--date-from",
            "2026-05-20",
            "--date-to",
            "2026-05-20",
            "--profile",
            "bocyl-ayudas",
            "--dry-run",
            "--limit",
            "10",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "source=BOCYL" in captured.out
    assert "documents_scanned=6" in captured.out
    assert "matches_total=5" in captured.out
    assert "matches_after_filters=2" in captured.out
    assert "excluded_by_keyword_rules=3" in captured.out
    assert "BOCYL:study-aid" in captured.out
    assert "BOCYL:young-rent" in captured.out
    assert "BOCYL:vivienda-department-only" not in captured.out
    assert "BOCYL:environmental-noise" not in captured.out
    assert "BOCYL:generic-subvenciones" not in captured.out
    assert "BOCYL:professional-families-noise" not in captured.out
    assert "ayudas al estudio" in captured.out
    assert "bono alquiler joven" in captured.out


def test_find_source_candidates_bocyl_profile_dry_run_does_not_write(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    connection = connect(str(db_path))
    initialize_database(connection)
    repository = OfficialSourcesRepository(connection)
    bocyl_source = repository.ensure_official_source_bocyl()
    repository.upsert_document(
        source_id=bocyl_source["id"],
        external_id="BOCYL:student-aid",
        publication_date="2026-05-20",
        title="Convocatoria de becas para estudiantes universitarios",
        department="CONSEJERIA DE EDUCACION",
        section="I. COMUNIDAD DE CASTILLA Y LEON",
    )

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "find-source-candidates",
            "--source",
            "BOCYL",
            "--date-from",
            "2026-05-20",
            "--date-to",
            "2026-05-20",
            "--profile",
            "bocyl-ayudas",
            "--dry-run",
        ]
    )

    candidate_count = connection.execute(
        "SELECT COUNT(*) AS count FROM source_candidates"
    ).fetchone()["count"]
    captured = capsys.readouterr()
    assert exit_code == 0
    assert candidate_count == 0
    assert "write_mode=dry_run" in captured.out
    assert "BOCYL:student-aid" in captured.out


def test_find_boe_candidates_default_source_remains_boe(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    connection = connect(str(db_path))
    initialize_database(connection)
    repository = OfficialSourcesRepository(connection)
    boe_source = repository.ensure_official_source_boe()
    boja_source = repository.ensure_official_source_boja()
    repository.upsert_document(
        source_id=boe_source["id"],
        external_id="BOE-A-2024-11111",
        publication_date="2024-05-29",
        title="Convocatoria de ayudas estatales",
    )
    repository.upsert_document(
        source_id=boja_source["id"],
        external_id="BOJA:disposition.2026.94.5",
        publication_date="2024-05-29",
        title="Convocatoria de ayudas autonomicas",
    )

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "find-boe-candidates",
            "--date-from",
            "2024-05-29",
            "--date-to",
            "2024-05-29",
            "--keywords",
            "ayudas",
            "--dry-run",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "source=BOE" in captured.out
    assert "documents_scanned=1" in captured.out
    assert "BOE-A-2024-11111" in captured.out
    assert "BOJA:disposition.2026.94.5" not in captured.out


def test_find_boe_candidates_no_write_alias_does_not_create_candidates(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    connection = connect(str(db_path))
    initialize_database(connection)
    repository = OfficialSourcesRepository(connection)
    source = repository.ensure_official_source_boe()
    repository.upsert_document(
        source_id=source["id"],
        external_id="BOE-A-2024-11111",
        publication_date="2024-05-29",
        title="Ayudas al alquiler",
    )

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "find-boe-candidates",
            "--date-from",
            "2024-05-29",
            "--date-to",
            "2024-05-29",
            "--keywords",
            "ayudas",
            "--no-write",
        ]
    )

    candidate_count = connection.execute(
        "SELECT COUNT(*) AS count FROM source_candidates"
    ).fetchone()["count"]
    captured = capsys.readouterr()
    assert exit_code == 0
    assert candidate_count == 0
    assert "write_mode=dry_run" in captured.out


def test_find_boe_candidates_ignores_documents_without_keyword_matches(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    connection = connect(str(db_path))
    initialize_database(connection)
    repository = OfficialSourcesRepository(connection)
    source = repository.ensure_official_source_boe()
    repository.upsert_document(
        source_id=source["id"],
        external_id="BOE-A-2024-11111",
        publication_date="2024-05-29",
        title="Plain administrative notice",
        department="Ministerio de Cultura",
    )

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "find-boe-candidates",
            "--date-from",
            "2024-05-29",
            "--date-to",
            "2024-05-29",
            "--keywords",
            "becas,ayudas",
            "--dry-run",
        ]
    )

    candidate_count = connection.execute(
        "SELECT COUNT(*) AS count FROM source_candidates"
    ).fetchone()["count"]
    captured = capsys.readouterr()
    assert exit_code == 0
    assert candidate_count == 0
    assert "documents_scanned=1" in captured.out
    assert "documents_matched=0" in captured.out
    assert "matches_by_keyword=none" in captured.out
    assert "sample index=" not in captured.out


def test_find_boe_candidates_rejects_non_positive_limit(tmp_path, capsys):
    from official_sources.cli import run

    exit_code = run(
        [
            "--db-path",
            str(tmp_path / "db.sqlite"),
            "find-boe-candidates",
            "--date-from",
            "2024-05-29",
            "--date-to",
            "2024-05-29",
            "--keywords",
            "ayuda",
            "--dry-run",
            "--limit",
            "0",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "--limit" in captured.err


def test_find_boe_candidates_does_not_approve_or_publish(tmp_path):
    import inspect

    import official_sources.cli as cli

    source = inspect.getsource(cli._run_find_candidates)

    assert "human_accepted" not in source
    assert "publish" not in source.lower()


def test_find_boe_candidates_help_contains_false_positive_warning(capsys):
    from official_sources.cli import run

    exit_code = run(["find-boe-candidates", "--help"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "metadata" in captured.out
    assert "false" in captured.out
    assert "positives" in captured.out
    assert "--dry-run" in captured.out
    assert "--no-write" in captured.out
    assert "--write" in captured.out
    assert "explicit" in captured.out
    assert "--limit" in captured.out


def test_find_source_candidates_help_is_available(capsys):
    from official_sources.cli import run

    exit_code = run(["find-source-candidates", "--help"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "preferred generic command" in captured.out.lower()
    assert "--source" in captured.out
    assert "BOE" in captured.out
    assert "BOJA" in captured.out
    assert "DOGV" in captured.out
    assert "BOCM" in captured.out
    assert "BDNS" in captured.out
    assert "--dry-run" in captured.out
    assert "--write" in captured.out


def test_find_boe_candidates_help_identifies_backwards_compatible_command(capsys):
    from official_sources.cli import run

    exit_code = run(["find-boe-candidates", "--help"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "backwards-compatible" in captured.out.lower()
    assert "boe-default" in captured.out.lower()


def test_find_boe_candidates_normalizes_accents_case_and_whitespace(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    connection = connect(str(db_path))
    initialize_database(connection)
    repository = OfficialSourcesRepository(connection)
    source = repository.ensure_official_source_boe()
    repository.upsert_document(
        source_id=source["id"],
        external_id="BOE-A-2024-22222",
        publication_date="2024-05-29",
        title="Convocatoria   de SUBVENCION para Educacion",
    )

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "find-boe-candidates",
            "--date-from",
            "2024-05-29",
            "--date-to",
            "2024-05-29",
            "--keywords",
            "subvención,educación",
            "--dry-run",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "matches_after_filters=1" in captured.out
    assert "matched_keywords=subvención,educación" in captured.out


def test_find_boe_candidates_word_boundaries_prevent_bono_carbono(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    connection = connect(str(db_path))
    initialize_database(connection)
    repository = OfficialSourcesRepository(connection)
    source = repository.ensure_official_source_boe()
    repository.upsert_document(
        source_id=source["id"],
        external_id="BOE-A-2024-22222",
        publication_date="2024-05-29",
        title="Proyecto sobre captura de carbono",
    )
    repository.upsert_document(
        source_id=source["id"],
        external_id="BOE-A-2024-33333",
        publication_date="2024-05-29",
        title="Convocatoria de bono alquiler",
    )

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "find-boe-candidates",
            "--date-from",
            "2024-05-29",
            "--date-to",
            "2024-05-29",
            "--keywords",
            "bono",
            "--dry-run",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "matches_total=1" in captured.out
    assert "BOE-A-2024-33333" in captured.out
    assert "BOE-A-2024-22222" not in captured.out


def test_find_boe_candidates_phrase_matching_and_scoring_are_explainable(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    connection = connect(str(db_path))
    initialize_database(connection)
    repository = OfficialSourcesRepository(connection)
    source = repository.ensure_official_source_boe()
    repository.upsert_document(
        source_id=source["id"],
        external_id="BOE-A-2024-22222",
        publication_date="2024-05-29",
        title="Bases reguladoras de ayudas al estudio",
        url_html="https://www.boe.es/diario_boe/txt.php?id=BOE-A-2024-22222",
    )

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "find-boe-candidates",
            "--date-from",
            "2024-05-29",
            "--date-to",
            "2024-05-29",
            "--keywords",
            "bases reguladoras,ayudas al estudio",
            "--dry-run",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "matched_keywords=bases reguladoras,ayudas al estudio" in captured.out
    assert "score=" in captured.out
    assert "score_reasons=" in captured.out
    assert "strong_phrase:bases_reguladoras" in captured.out
    assert "official_url=https://www.boe.es/diario_boe/txt.php?id=BOE-A-2024-22222" in captured.out


def test_find_boe_candidates_profile_excludes_procurement_and_generic_keywords(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    connection = connect(str(db_path))
    initialize_database(connection)
    repository = OfficialSourcesRepository(connection)
    source = repository.ensure_official_source_boe()
    repository.upsert_document(
        source_id=source["id"],
        external_id="BOE-B-2024-11111",
        publication_date="2024-05-29",
        title="Anuncio de licitación de servicios de transporte",
        department="Ministerio de Transportes",
        section="V. Anuncios - A. Contratación del Sector Público",
    )
    repository.upsert_document(
        source_id=source["id"],
        external_id="BOE-B-2024-22222",
        publication_date="2024-05-29",
        title="Anuncio sobre convocatoria de Junta",
        department="Otros entes",
        section="V. Anuncios - B. Otros anuncios oficiales",
    )
    repository.upsert_document(
        source_id=source["id"],
        external_id="BOE-B-2024-33333",
        publication_date="2024-05-29",
        title="Convocatoria de ayudas al transporte para estudiantes",
        department="Ministerio de Educacion",
        section="V. Anuncios - B. Otros anuncios oficiales",
    )

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "find-boe-candidates",
            "--date-from",
            "2024-05-29",
            "--date-to",
            "2024-05-29",
            "--profile",
            "la-ayuda",
            "--dry-run",
            "--limit",
            "10",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "documents_scanned=3" in captured.out
    assert "matches_total=3" in captured.out
    assert "matches_after_filters=1" in captured.out
    assert "excluded_by_section=1" in captured.out
    assert "excluded_by_keyword_rules=1" in captured.out
    assert "BOE-B-2024-33333" in captured.out
    assert "BOE-B-2024-11111" not in captured.out
    assert "BOE-B-2024-22222" not in captured.out


def test_find_boe_candidates_section_and_department_filters_work(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    connection = connect(str(db_path))
    initialize_database(connection)
    repository = OfficialSourcesRepository(connection)
    source = repository.ensure_official_source_boe()
    repository.upsert_document(
        source_id=source["id"],
        external_id="BOE-A-2024-11111",
        publication_date="2024-05-29",
        title="Convocatoria de ayudas",
        department="Ministerio de Educacion",
        section="III",
    )
    repository.upsert_document(
        source_id=source["id"],
        external_id="BOE-A-2024-22222",
        publication_date="2024-05-29",
        title="Convocatoria de ayudas",
        department="Ministerio de Cultura",
        section="III",
    )
    repository.upsert_document(
        source_id=source["id"],
        external_id="BOE-B-2024-33333",
        publication_date="2024-05-29",
        title="Convocatoria de ayudas",
        department="Ministerio de Educacion",
        section="V. Anuncios - A. Contratación del Sector Público",
    )

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "find-boe-candidates",
            "--date-from",
            "2024-05-29",
            "--date-to",
            "2024-05-29",
            "--keywords",
            "convocatoria de ayudas",
            "--include-sections",
            "III",
            "--include-departments",
            "Educacion",
            "--dry-run",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "matches_total=3" in captured.out
    assert "matches_after_filters=1" in captured.out
    assert "BOE-A-2024-11111" in captured.out
    assert "BOE-A-2024-22222" not in captured.out
    assert "BOE-B-2024-33333" not in captured.out
