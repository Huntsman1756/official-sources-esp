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


def test_cli_help_works(capsys):
    from official_sources.cli import run

    exit_code = run(["--help"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "ingest-boe-summary" in captured.out
    assert "download-boe-artifacts" in captured.out


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
            "xml,html,pdf",
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
            "--date",
            "2024-05-29",
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
            "xml,html,pdf",
        ],
        artifact_client=_artifact_client(
            {
                document["url_xml"]: _fixture_bytes("boe_document.xml"),
                document["url_html"]: _fixture_bytes("boe_document.html"),
                document["url_pdf"]: _fixture_bytes("boe_document.pdf"),
            }
        ),
    )

    exit_code = run(["--db-path", str(db_path), "status", "--date", "2024-05-29"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "documents=1" in captured.out
    assert "xml_files=1" in captured.out
    assert "html_files=1" in captured.out
    assert "pdf_files=1" in captured.out
    assert "artifact_download_attempts=3" in captured.out
    assert "artifact_download_success=3" in captured.out
    assert "artifact_http_status_summary=xml:200:1,html:200:1,pdf:200:1" in captured.out


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
            "xml,html,pdf",
        ],
        artifact_client=_artifact_client(
            {
                document["url_xml"]: _fixture_bytes("boe_document.xml"),
                document["url_html"]: _fixture_bytes("boe_document.html"),
                document["url_pdf"]: _fixture_bytes("boe_document.pdf"),
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
    assert "artifact_http_status_summary=xml:200:1,html:200:1,pdf:200:1" in captured.out
    assert "artifact_retry_count=0" in captured.out


def test_cli_does_not_expose_mcp_write_tools_or_downstream_publication():
    import inspect

    import official_sources.cli as cli

    source = inspect.getsource(cli)

    assert "FastMCP" not in source
    assert "mcp.tool" not in source
    assert "human_accepted" not in source
    assert "publish" not in source.lower()
    assert "downstream" not in source.lower()


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
