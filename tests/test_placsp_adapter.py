from __future__ import annotations

import json
from pathlib import Path

from official_sources.integrity.hashing import sha256_bytes
from official_sources.sources.placsp.client import (
    build_placsp_dataset_url,
    build_placsp_feed_url,
    validate_placsp_feed_type,
    validate_placsp_limit,
    validate_placsp_period,
)
from official_sources.sources.placsp.ingestion import ingest_placsp_feed, preview_placsp_feed
from official_sources.sources.placsp.parser import parse_placsp_atom

FIXTURES = Path(__file__).parent / "fixtures"


def _fixture_bytes(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


def test_placsp_source_record_creation(repository):
    source = repository.ensure_official_source_placsp()

    assert source["code"] == "PLACSP"
    assert source["name"] == "Plataforma de Contratacion del Sector Publico"
    assert source["jurisdiction"] == "ES"
    assert source["region_code"] == "ES"
    assert source["access_type"] == "official_atom"
    assert source["reliability_level"] == "canonical"


def test_placsp_urls_are_limited_to_official_syndication_datasets():
    assert validate_placsp_feed_type("profiles") == "profiles"
    assert validate_placsp_period("202606") == "202606"
    assert validate_placsp_limit(25) == 25
    assert build_placsp_feed_url("profiles") == (
        "https://contrataciondelsectorpublico.gob.es/sindicacion/sindicacion_643/"
        "licitacionesPerfilesContratanteCompleto3.atom"
    )
    assert build_placsp_dataset_url("aggregated", period="202605") == (
        "https://contrataciondelsectorpublico.gob.es/sindicacion/sindicacion_1044/"
        "PlataformasAgregadasSinMenores_202605.zip"
    )


def test_placsp_atom_parser_preserves_contract_metadata_and_document_hashes():
    payload = _fixture_bytes("placsp_feed_sample.atom")

    page = parse_placsp_atom(
        payload,
        source_url=build_placsp_feed_url("profiles"),
        feed_type="profiles",
    )

    assert page.status == "success"
    assert page.source_snapshot_hash == sha256_bytes(payload)
    assert page.next_url == "https://contrataciondelestado.es/sindicacion/sindicacion_643/next.atom"
    assert page.deleted_entries == [
        {
            "ref": "https://contrataciondelestado.es/sindicacion/licitacionesPerfilContratante/19791334",
            "when": "2026-06-01T19:49:12.019+02:00",
            "comment_type": "ANULADA",
        }
    ]
    tender = page.tenders[0]
    assert tender.external_id == "PLACSP:18802405"
    assert tender.official_identifier == "PLACSP:18802405"
    assert tender.publication_date == "2026-06-01"
    assert tender.title == (
        "Servicio de Teleasistencia de los Servicios Sociales de atención Primaria"
    )
    assert tender.department == "Presidencia de la Mancomunidad de los Valles del Saja y Corona"
    assert tender.url_html == (
        "https://contrataciondelestado.es/wps/poc?uri=deeplink:detalle_licitacion&idEvl=abc"
    )
    assert tender.raw_metadata["source_family"] == "procurement_platform"
    assert tender.raw_metadata["contract_folder_id"] == "240/2025"
    assert tender.raw_metadata["status_code"] == "RES"
    assert tender.raw_metadata["cpv_codes"] == ["85310000"]
    assert tender.raw_metadata["document_metadata"][0]["document_hash"] == "abc123"


def test_placsp_preview_does_not_store_documents():
    payload = _fixture_bytes("placsp_feed_sample.atom")

    result = preview_placsp_feed(feed_payload=payload, feed_type="profiles")

    assert result["status"] == "success"
    assert result["placsp_result"] == "success"
    assert result["documents_fetched"] == 0
    assert result["entry_count"] == 1
    assert result["deleted_entry_count"] == 1
    assert result["sample_identifiers"] == ["PLACSP:18802405"]


def test_placsp_feed_ingestion_stores_metadata_without_candidates_or_artifacts(repository):
    payload = _fixture_bytes("placsp_feed_sample.atom")

    run = ingest_placsp_feed(
        repository,
        feed_type="profiles",
        feed_payload=payload,
        limit=10,
    )

    document = repository.get_document_by_external_id("PLACSP:18802405")
    raw_metadata = json.loads(document["raw_metadata_json"])
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
    assert run["placsp_result"] == "success"
    assert run["documents_fetched"] == 1
    assert run["documents_new"] == 1
    assert run["source_snapshot_hash"] == sha256_bytes(payload)
    assert document["source_code"] == "PLACSP"
    assert document["document_type"] == "public_procurement_tender"
    assert raw_metadata["document_metadata"][0]["official_url"].startswith(
        "https://contrataciondelestado.es/FileSystem/"
    )
    assert raw_file_count == 1
    assert candidate_count == 0
    assert attempt_count == 0


def test_placsp_preview_cli_outputs_metadata_only_result(tmp_path, capsys):
    from official_sources.cli import run

    payload = _fixture_bytes("placsp_feed_sample.atom")

    def fetcher(**_kwargs):
        return payload

    exit_code = run(
        [
            "--db-path",
            str(tmp_path / "official-sources.sqlite"),
            "preview-placsp-feed",
            "--feed-type",
            "profiles",
            "--limit",
            "5",
        ],
        placsp_feed_fetcher=fetcher,
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert (
        "command_started=preview-placsp-feed source_code=PLACSP feed_type=profiles"
        in captured.out
    )
    assert "status=success" in captured.out
    assert "placsp_result=success" in captured.out
    assert "documents_fetched=0" in captured.out
    assert "sample_identifiers=PLACSP:18802405" in captured.out


def test_placsp_ingest_cli_stores_feed_metadata(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "official-sources.sqlite"
    payload = _fixture_bytes("placsp_feed_sample.atom")

    def fetcher(**_kwargs):
        return payload

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "ingest-placsp-feed",
            "--feed-type",
            "profiles",
            "--limit",
            "5",
        ],
        placsp_feed_fetcher=fetcher,
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert (
        "command_started=ingest-placsp-feed source_code=PLACSP feed_type=profiles"
        in captured.out
    )
    assert "documents_fetched=1" in captured.out
