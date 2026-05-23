from __future__ import annotations

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


def test_find_boe_candidates_boja_profile_allows_young_housing_context(tmp_path, capsys):
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
    assert "matches_after_filters=1" in captured.out
    assert "matched_keywords=ayudas,vivienda,alquiler,jovenes" in captured.out
    assert "BOJA:young-rent" in captured.out


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
