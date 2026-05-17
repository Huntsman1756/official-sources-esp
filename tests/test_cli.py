from __future__ import annotations

from pathlib import Path

import httpx

from official_sources.integrity.hashing import sha256_bytes
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
    assert "download_attempts=1" in captured.out
    assert "download_failed=1" in captured.out
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
