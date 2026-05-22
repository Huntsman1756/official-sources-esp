from __future__ import annotations

import json
from pathlib import Path

from official_sources.integrity.hashing import sha256_bytes
from official_sources.storage.database import connect, initialize_database
from official_sources.storage.repository import OfficialSourcesRepository


def _repository(tmp_path: Path) -> OfficialSourcesRepository:
    connection = connect(str(tmp_path / "db.sqlite"))
    initialize_database(connection)
    return OfficialSourcesRepository(connection)


def _seed_reviewed_candidate(
    repository: OfficialSourcesRepository,
    *,
    source_code: str = "DOGV",
    external_id: str = "DOGV:DOGV-C-2026-14923",
    url_pdf: str = "https://dogv.gva.es/datos/2026/05/14/pdf/2026_14923_es.pdf",
) -> dict:
    if source_code == "DOGV":
        source = repository.ensure_official_source_dogv()
    elif source_code == "BOJA":
        source = repository.ensure_official_source_boja()
        external_id = "BOJA:disposition.2026.94.5"
        url_pdf = "https://www.juntadeandalucia.es/boja/2026/94/5.pdf"
    else:
        source = repository.ensure_official_source_boe()
        external_id = "BOE-A-2024-11111"
        url_pdf = "https://www.boe.es/boe/dias/2024/05/29/pdfs/BOE-A-2024-11111.pdf"
    document = repository.upsert_document(
        source_id=source["id"],
        external_id=external_id,
        publication_date="2026-05-14",
        title="Ayudas adicionales dirigidas a trabajadores afectados por EREs",
        department="Labora",
        section="III. Actos administrativos",
        url_html="https://dogv.gva.es/es/resultat-dogv?signatura=2026/14923",
        url_xml="https://dogv.gva.es/dogv-portal/export/disposicion/xml/dinamico/476000?lang=es",
        url_pdf=url_pdf,
        raw_metadata={"metadata_url": "https://dogv.gva.es/es/resultat-dogv?signatura=2026/14923"},
    )
    repository.upsert_document_file(
        document_id=document["id"],
        file_type="pdf",
        official_url=url_pdf,
        payload=b"%PDF-1.4 official evidence",
        ingestion_run_id=None,
        media_type="application/pdf",
    )
    candidate = repository.create_source_candidate(
        document_id=document["id"],
        project_key="dogv-ayudas",
        candidate_type="keyword_match",
        extraction_status="raw_detected",
        evidence_level="metadata_keyword_match",
        matched_fields={"keywords": ["ayudas", "empleo"]},
    )
    repository.mark_candidate_evidence_review(
        source_candidate_id=candidate["id"],
        evidence_review_status="evidence_reviewed",
        evidence_label="likely_relevant",
        manual_decision="accept_for_downstream_pilot",
        downstream_project_fit="la-ayuda",
        reviewed_by="Dani",
        reviewed_at="2026-05-21",
        selected_for_pdf=False,
    )
    return candidate


def test_dogv_downstream_export_includes_nullable_version_date(tmp_path):
    from official_sources.downstream_export import build_downstream_evidence_export

    repository = _repository(tmp_path)
    candidate = _seed_reviewed_candidate(repository)

    exported = build_downstream_evidence_export(repository, candidate["id"])

    assert "version_date" in exported
    assert exported["version_date"] is None
    assert exported["citation"]["version_date"] is None
    assert exported["source_code"] == "DOGV"
    assert exported["official_sources_candidate"]["candidate_id"] == candidate["id"]
    assert exported["integrity"]["hashes_match"] is True
    assert exported["artifacts"]["pdf_available"] is True
    assert "local_path" not in json.dumps(exported)
    assert "raw_pdf_text" not in json.dumps(exported)


def test_downstream_export_preserves_integrity_fields(tmp_path):
    from official_sources.downstream_export import build_downstream_evidence_export

    repository = _repository(tmp_path)
    candidate = _seed_reviewed_candidate(repository)

    exported = build_downstream_evidence_export(repository, candidate["id"])

    pdf_hash = sha256_bytes(b"%PDF-1.4 official evidence")
    assert exported["integrity"]["source_snapshot_hash"] == pdf_hash
    assert exported["integrity"]["content_sha256"] == pdf_hash
    assert exported["integrity"]["has_integrity_warning"] is False
    assert exported["integrity"]["integrity_warning_reason"] is None
    assert exported["artifacts"]["pdf"]["sha256"] == pdf_hash


def test_boe_and_boja_downstream_exports_keep_version_date_contract(tmp_path):
    from official_sources.downstream_export import build_downstream_evidence_export

    repository = _repository(tmp_path)
    boe_candidate = _seed_reviewed_candidate(repository, source_code="BOE")
    boja_candidate = _seed_reviewed_candidate(repository, source_code="BOJA")

    boe_export = build_downstream_evidence_export(repository, boe_candidate["id"])
    boja_export = build_downstream_evidence_export(repository, boja_candidate["id"])

    assert "version_date" in boe_export
    assert boe_export["version_date"] is None
    assert "version_date" in boja_export
    assert boja_export["version_date"] is None


def test_export_downstream_evidence_cli_writes_grouped_json_with_version_date(tmp_path):
    from official_sources.cli import run

    repository = _repository(tmp_path)
    candidate = _seed_reviewed_candidate(repository)
    output_dir = tmp_path / "exports"

    exit_code = run(
        [
            "--db-path",
            str(tmp_path / "db.sqlite"),
            "export-downstream-evidence",
            "--candidate-ids",
            str(candidate["id"]),
            "--output-dir",
            str(output_dir),
        ]
    )

    exported_files = list((output_dir / "la-ayuda").glob("*.json"))
    assert exit_code == 0
    assert len(exported_files) == 1
    assert exported_files[0].name == "1_DOGV_DOGV-C-2026-14923.json"
    payload = json.loads(exported_files[0].read_text())
    assert payload["version_date"] is None
    assert payload["official_sources_candidate"]["candidate_id"] == candidate["id"]
