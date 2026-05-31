from __future__ import annotations

import json
from pathlib import Path

from official_sources.storage.database import connect
from official_sources.storage.repository import OfficialSourcesRepository


def _fixture_bytes(name: str) -> bytes:
    return (Path(__file__).parent / "fixtures" / name).read_bytes()


def test_ingest_bdns_latest_cli_creates_ingestion_run(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"

    exit_code = run(
        ["--db-path", str(db_path), "ingest-bdns-latest", "--limit", "1"],
        bdns_latest_fetcher=lambda _limit: _fixture_bytes("bdns_latest_convocatorias.json"),
    )

    connection = connect(str(db_path))
    repository = OfficialSourcesRepository(connection)
    run_record = repository.get_latest_ingestion_run("BDNS", "latest")
    document = repository.get_document_by_external_id("BDNS:907362")
    captured = capsys.readouterr()

    assert exit_code == 0
    assert run_record["status"] == "success"
    assert run_record["documents_fetched"] == 1
    assert document["source_code"] == "BDNS"
    assert "command_started=ingest-bdns-latest source_code=BDNS target=latest" in captured.out
    assert "status=success" in captured.out
    assert "documents_fetched=1" in captured.out
    assert "documents_new=1" in captured.out
    assert "documents_updated=0" in captured.out
    assert "bdns_result=success" in captured.out
    assert "page_count=1" in captured.out
    assert "pagination_limit_reached=false" in captured.out
    assert "sample_identifiers=BDNS:907362" in captured.out
    assert "source_snapshot_hash=" in captured.out


def test_ingest_bdns_call_cli_creates_call_detail(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"

    exit_code = run(
        ["--db-path", str(db_path), "ingest-bdns-call", "--num-conv", "907042"],
        bdns_call_fetcher=lambda _num_conv: _fixture_bytes("bdns_convocatoria_detail.json"),
    )

    connection = connect(str(db_path))
    repository = OfficialSourcesRepository(connection)
    run_record = repository.get_latest_ingestion_run("BDNS", "907042")
    document = repository.get_document_by_external_id("BDNS:907042")
    captured = capsys.readouterr()

    assert exit_code == 0
    assert run_record["status"] == "success"
    assert document["raw_metadata_json"]
    assert "command_started=ingest-bdns-call source_code=BDNS num_conv=907042" in captured.out
    assert "official_identifier=BDNS:907042" in captured.out
    assert "bdns_result=success" in captured.out
    assert "sample_identifiers=BDNS:907042" in captured.out


def test_ingest_bdns_call_cli_reports_not_found(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"

    exit_code = run(
        ["--db-path", str(db_path), "ingest-bdns-call", "--num-conv", "999999"],
        bdns_call_fetcher=lambda _num_conv: _fixture_bytes("bdns_not_found.json"),
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "status=failed" in captured.out
    assert "bdns_result=not_found" in captured.out


def test_search_bdns_calls_cli_requires_page_limits(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "search-bdns-calls",
            "--date-from",
            "20/05/2026",
            "--date-to",
            "20/05/2026",
            "--page-size",
            "10",
            "--max-pages",
            "11",
        ],
        bdns_search_fetcher=lambda **_kwargs: _fixture_bytes("bdns_search_convocatorias.json"),
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "max-pages" in captured.err


def test_search_bdns_calls_cli_reports_pagination_and_samples(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "search-bdns-calls",
            "--date-from",
            "20/05/2026",
            "--date-to",
            "20/05/2026",
            "--page-size",
            "10",
            "--max-pages",
            "1",
        ],
        bdns_search_fetcher=lambda **_kwargs: _fixture_bytes("bdns_search_convocatorias.json"),
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "status=success" in captured.out
    assert "bdns_result=success" in captured.out
    assert "page_count=1" in captured.out
    assert "pagination_limit_reached=false" in captured.out
    assert "sample_identifiers=BDNS:907042" in captured.out


def test_search_bdns_calls_cli_reports_no_results(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "search-bdns-calls",
            "--page-size",
            "10",
            "--max-pages",
            "2",
        ],
        bdns_search_fetcher=lambda **_kwargs: _fixture_bytes("bdns_empty_results.json"),
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "status=success" in captured.out
    assert "bdns_result=no_results" in captured.out
    assert "documents_fetched=0" in captured.out
    assert "page_count=1" in captured.out
    assert "sample_identifiers=none" in captured.out


def test_preview_bdns_catalog_cli_reports_metadata_without_ingestion(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"

    exit_code = run(
        ["--db-path", str(db_path), "preview-bdns-catalog", "--catalog", "sectores"],
        bdns_catalog_fetcher=lambda _catalog, **_kwargs: (
            b'[{"codigo":"S01","descripcion":"Sector"}]'
        ),
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "command_started=preview-bdns-catalog source_code=BDNS catalog=sectores" in captured.out
    assert "status=success" in captured.out
    assert "bdns_result=success" in captured.out
    assert "catalog_name=sectores" in captured.out
    assert "entry_count=1" in captured.out
    assert "documents_fetched=0" in captured.out
    assert "sample_identifiers=BDNS:catalog:sectores:S01" in captured.out


def test_preview_bdns_catalog_cli_requires_id_admon_for_organos(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"

    exit_code = run(
        ["--db-path", str(db_path), "preview-bdns-catalog", "--catalog", "organos"],
        bdns_catalog_fetcher=lambda _catalog, **_kwargs: b"[]",
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "id-admon is required" in captured.err


def test_ingest_bdns_catalog_cli_stores_entries(tmp_path, capsys):
    from official_sources.cli import run
    from official_sources.storage.database import connect
    from official_sources.storage.repository import OfficialSourcesRepository

    db_path = tmp_path / "db.sqlite"

    exit_code = run(
        ["--db-path", str(db_path), "ingest-bdns-catalog", "--catalog", "sectores"],
        bdns_catalog_fetcher=lambda _catalog, **_kwargs: (
            b'[{"codigo":"S01","descripcion":"Sector"}]'
        ),
    )

    repository = OfficialSourcesRepository(connect(str(db_path)))
    entry = repository.get_bdns_catalog_entry("sectores", "S01")
    captured = capsys.readouterr()

    assert exit_code == 0
    assert entry["name"] == "Sector"
    assert "command_started=ingest-bdns-catalog source_code=BDNS catalog=sectores" in captured.out
    assert "status=success" in captured.out
    assert "documents_fetched=1" in captured.out
    assert "documents_new=1" in captured.out
    assert "catalog_name=sectores" in captured.out
    assert "entry_count=1" in captured.out


def test_export_bdns_grants_cli_writes_enriched_jsonl(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    output_path = tmp_path / "bdns-grants.jsonl"

    assert (
        run(
            ["--db-path", str(db_path), "ingest-bdns-catalog", "--catalog", "sectores"],
            bdns_catalog_fetcher=lambda _catalog, **_kwargs: (
                b'[{"codigo":"94","descripcion":"Actividades asociativas"}]'
            ),
        )
        == 0
    )
    assert (
        run(
            ["--db-path", str(db_path), "ingest-bdns-call", "--num-conv", "907042"],
            bdns_call_fetcher=lambda _num_conv: _fixture_bytes("bdns_convocatoria_detail.json"),
        )
        == 0
    )

    exit_code = run(
        ["--db-path", str(db_path), "export-bdns-grants", "--output", str(output_path)]
    )

    captured = capsys.readouterr()
    records = [json.loads(line) for line in output_path.read_text(encoding="utf-8").splitlines()]

    assert exit_code == 0
    assert "command_started=export-bdns-grants source_code=BDNS" in captured.out
    assert f"output_path={output_path}" in captured.out
    assert "records_exported=1" in captured.out
    assert records[0]["official_identifier"] == "BDNS:907042"
    assert records[0]["catalog_enrichment"]["sectores"][0]["name"] == (
        "Actividades asociativas"
    )
    assert records[0]["document_metadata"] == []
    assert records[0]["source_snapshot_hash"]


def test_export_bdns_business_grants_cli_writes_ranked_profile_jsonl(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    output_path = tmp_path / "bdns-business-grants.jsonl"

    assert (
        run(
            ["--db-path", str(db_path), "ingest-bdns-call", "--num-conv", "907042"],
            bdns_call_fetcher=lambda _num_conv: _fixture_bytes("bdns_convocatoria_detail.json"),
        )
        == 0
    )

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "export-bdns-business-grants",
            "--output",
            str(output_path),
            "--min-score",
            "0.7",
        ]
    )

    captured = capsys.readouterr()
    records = [json.loads(line) for line in output_path.read_text(encoding="utf-8").splitlines()]

    assert exit_code == 0
    assert "command_started=export-bdns-business-grants source_code=BDNS" in captured.out
    assert "records_exported=1" in captured.out
    assert records[0]["profile"] == "business_grants"
    assert records[0]["official_identifier"] == "BDNS:907042"
    assert records[0]["business_relevance_score"] >= 0.75
    assert "beneficiary:pyme" in records[0]["business_relevance_reasons"]
    assert records[0]["review_status"] == "manual_review_required"


def test_export_bdns_business_dashboard_cli_writes_static_html(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    output_path = tmp_path / "bdns-business-radar.html"

    assert (
        run(
            ["--db-path", str(db_path), "ingest-bdns-call", "--num-conv", "907042"],
            bdns_call_fetcher=lambda _num_conv: _fixture_bytes("bdns_convocatoria_detail.json"),
        )
        == 0
    )

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "export-bdns-business-dashboard",
            "--output",
            str(output_path),
            "--min-score",
            "0.7",
        ]
    )

    html = output_path.read_text(encoding="utf-8")
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "command_started=export-bdns-business-dashboard source_code=BDNS" in captured.out
    assert "records_rendered=1" in captured.out
    assert "BDNS Business Grants Radar" in html
    assert "BDNS:907042" in html
    assert "business_grants" in html


def test_ingest_bdns_concesiones_cli_is_blocked_by_privacy_guardrail(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"

    exit_code = run(["--db-path", str(db_path), "ingest-bdns-concesiones"])

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "global BDNS concesiones ingestion is disabled" in captured.err


def test_preview_bdns_concesiones_cli_reports_sanitized_samples(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    payload = json.dumps(
        {
            "content": [
                {
                    "codConcesion": "SB152503815",
                    "numeroConvocatoria": "877699",
                    "fechaConcesion": "2026-05-29",
                    "beneficiario": "Persona Fisica",
                    "idPersona": 22127337,
                }
            ],
            "last": True,
        }
    ).encode()

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "preview-bdns-concesiones",
            "--num-conv",
            "877699",
            "--page-size",
            "1",
        ],
        bdns_concessions_fetcher=lambda **_kwargs: payload,
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "command_started=preview-bdns-concesiones source_code=BDNS num_conv=877699" in (
        captured.out
    )
    assert "documents_fetched=0" in captured.out
    assert "entry_count=1" in captured.out
    assert "sample_identifiers=BDNS:concesion:SB152503815" in captured.out


def test_ingest_bdns_concesiones_cli_stores_sanitized_entries(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    payload = json.dumps(
        {
            "content": [
                {
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
    ).encode()

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "ingest-bdns-concesiones",
            "--num-conv",
            "877699",
            "--page-size",
            "1",
            "--max-pages",
            "1",
        ],
        bdns_concessions_fetcher=lambda **_kwargs: payload,
    )

    repository = OfficialSourcesRepository(connect(str(db_path)))
    entry = repository.get_bdns_concession_entry("SB152503815")
    raw_metadata = json.loads(entry["raw_metadata_json"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert entry["call_identifier"] == "BDNS:877699"
    assert entry["beneficiary_name"] is None
    assert entry["beneficiary_person_id"] is None
    assert raw_metadata["source_metadata"]["beneficiario"] == "<redacted>"
    assert "command_started=ingest-bdns-concesiones source_code=BDNS num_conv=877699" in (
        captured.out
    )
    assert "documents_fetched=1" in captured.out
    assert "documents_new=1" in captured.out


def test_export_bdns_concessions_cli_writes_sanitized_jsonl(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    output_path = tmp_path / "bdns-concessions.jsonl"
    payload = json.dumps(
        {
            "content": [
                {
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
    ).encode()

    assert (
        run(
            [
                "--db-path",
                str(db_path),
                "ingest-bdns-concesiones",
                "--num-conv",
                "877699",
                "--page-size",
                "1",
                "--max-pages",
                "1",
            ],
            bdns_concessions_fetcher=lambda **_kwargs: payload,
        )
        == 0
    )

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "export-bdns-concessions",
            "--num-conv",
            "877699",
            "--output",
            str(output_path),
        ]
    )

    captured = capsys.readouterr()
    records = [json.loads(line) for line in output_path.read_text(encoding="utf-8").splitlines()]

    assert exit_code == 0
    assert "command_started=export-bdns-concessions source_code=BDNS num_conv=877699" in (
        captured.out
    )
    assert "records_exported=1" in captured.out
    assert records[0]["external_id"] == "BDNS:concesion:SB152503815"
    assert records[0]["call_identifier"] == "BDNS:877699"
    assert records[0]["beneficiary_name"] is None
    assert records[0]["beneficiary_person_id"] is None
    assert "Persona Fisica" not in json.dumps(records)
