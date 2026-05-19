from __future__ import annotations

from pathlib import Path

import httpx

from official_sources.storage.database import connect, initialize_database
from official_sources.storage.repository import OfficialSourcesRepository


def _fixture_bytes(name: str) -> bytes:
    return (Path(__file__).parent / "fixtures" / name).read_bytes()


def _artifact_client(payloads: dict[str, bytes]) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=payloads[str(request.url)], request=request)

    return httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=False, timeout=5.0)


def _seed_candidate(db_path: Path) -> tuple[dict, dict]:
    connection = connect(str(db_path))
    initialize_database(connection)
    repository = OfficialSourcesRepository(connection)
    source = repository.ensure_official_source_boe()
    document = repository.upsert_document(
        source_id=source["id"],
        external_id="BOE-A-2024-11111",
        publication_date="2024-05-29",
        title="Convocatoria de ayudas",
        url_xml="https://www.boe.es/diario_boe/xml.php?id=BOE-A-2024-11111",
        url_html="https://www.boe.es/diario_boe/txt.php?id=BOE-A-2024-11111",
        url_pdf="https://www.boe.es/boe/dias/2024/05/29/pdfs/BOE-A-2024-11111.pdf",
    )
    candidate = repository.create_source_candidate(
        document_id=document["id"],
        project_key="la-ayuda",
        candidate_type="keyword_match",
        extraction_status="raw_detected",
        evidence_level="metadata_keyword_match",
        matched_fields={"keywords": ["ayudas"]},
    )
    return document, candidate


def test_mark_candidate_evidence_records_label_without_changing_review_status(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    _document, candidate = _seed_candidate(db_path)

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "mark-candidate-evidence",
            "--candidate-id",
            str(candidate["id"]),
            "--evidence-label",
            "likely_relevant",
            "--evidence-review-status",
            "evidence_downloaded",
            "--notes",
            "XML/HTML downloaded for evidence review",
            "--selected-for-evidence",
        ]
    )

    connection = connect(str(db_path))
    stored_candidate = connection.execute("SELECT * FROM source_candidates").fetchone()
    review = connection.execute("SELECT * FROM candidate_evidence_reviews").fetchone()
    captured = capsys.readouterr()
    assert exit_code == 0
    assert stored_candidate["review_status"] == "human_review_required"
    assert review["source_candidate_id"] == candidate["id"]
    assert review["evidence_label"] == "likely_relevant"
    assert review["evidence_review_status"] == "evidence_downloaded"
    assert review["selected_for_evidence"] == 1
    assert "review_status=human_review_required" in captured.out
    assert "approved=false" in captured.out


def test_mark_candidate_evidence_records_manual_review_metadata(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    _document, candidate = _seed_candidate(db_path)

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "mark-candidate-evidence",
            "--candidate-id",
            str(candidate["id"]),
            "--evidence-label",
            "unclear",
            "--evidence-review-status",
            "needs_more_evidence",
            "--manual-decision",
            "needs_more_evidence",
            "--manual-notes",
            "PDF required before downstream fit decision",
            "--needs-pdf",
            "yes",
            "--downstream-project-fit",
            "unclear",
            "--reviewed-by",
            "Dani",
            "--reviewed-at",
            "2026-05-17",
        ]
    )

    connection = connect(str(db_path))
    stored_candidate = connection.execute("SELECT * FROM source_candidates").fetchone()
    review = connection.execute("SELECT * FROM candidate_evidence_reviews").fetchone()
    captured = capsys.readouterr()
    assert exit_code == 0
    assert stored_candidate["review_status"] == "human_review_required"
    assert review["manual_decision"] == "needs_more_evidence"
    assert review["manual_notes"] == "PDF required before downstream fit decision"
    assert review["needs_pdf"] == "yes"
    assert review["downstream_project_fit"] == "unclear"
    assert review["reviewed_by"] == "Dani"
    assert review["reviewed_at"] == "2026-05-17"
    assert "manual_decision=needs_more_evidence" in captured.out
    assert "needs_pdf=yes" in captured.out
    assert "downstream_project_fit=unclear" in captured.out


def test_candidate_evidence_status_lists_artifact_availability_without_full_text(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    artifact_dir = tmp_path / "artifacts"
    document, candidate = _seed_candidate(db_path)
    client = _artifact_client(
        {
            document["url_xml"]: _fixture_bytes("boe_document.xml"),
            document["url_html"]: _fixture_bytes("boe_document.html"),
        }
    )
    run(
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
        artifact_client=client,
    )
    run(
        [
            "--db-path",
            str(db_path),
            "mark-candidate-evidence",
            "--candidate-id",
            str(candidate["id"]),
            "--evidence-label",
            "likely_relevant",
            "--evidence-review-status",
            "evidence_downloaded",
            "--manual-decision",
            "accept_for_downstream_pilot",
            "--needs-pdf",
            "no",
            "--downstream-project-fit",
            "EduAyudas",
        ]
    )
    capsys.readouterr()

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "candidate-evidence-status",
            "--candidate-ids",
            str(candidate["id"]),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert f"candidate_id={candidate['id']}" in captured.out
    assert "official_identifier=BOE-A-2024-11111" in captured.out
    assert "review_status=human_review_required" in captured.out
    assert "evidence_review_status=evidence_downloaded" in captured.out
    assert "evidence_label=likely_relevant" in captured.out
    assert "xml_available=true" in captured.out
    assert "html_available=true" in captured.out
    assert "pdf_available=false" in captured.out
    assert "integrity_warning=false" in captured.out
    assert "selected_for_pdf=false" in captured.out
    assert "manual_decision=accept_for_downstream_pilot" in captured.out
    assert "needs_pdf=no" in captured.out
    assert "downstream_project_fit=EduAyudas" in captured.out
    assert "official_url=https://www.boe.es/diario_boe/txt.php?id=BOE-A-2024-11111" in captured.out
    assert "Ignore previous instructions" not in captured.out


def test_candidate_evidence_status_can_filter_by_date_and_profile(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    _document, candidate = _seed_candidate(db_path)

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "candidate-evidence-status",
            "--date-from",
            "2024-05-29",
            "--date-to",
            "2024-05-29",
            "--profile",
            "la-ayuda",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert f"candidate_id={candidate['id']}" in captured.out
    assert "evidence_review_status=not_reviewed" in captured.out
    assert "evidence_label=none" in captured.out


def test_pdf_download_requires_explicit_candidate_or_document_ids(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    _seed_candidate(db_path)

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "download-boe-artifacts",
            "--date",
            "2024-05-29",
            "--types",
            "pdf",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "PDF downloads require --candidate-ids or --document-ids" in captured.err


def test_explicit_pdf_download_creates_artifact_audit_rows(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"
    artifact_dir = tmp_path / "artifacts"
    document, candidate = _seed_candidate(db_path)

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
            "pdf",
        ],
        artifact_client=_artifact_client({document["url_pdf"]: _fixture_bytes("boe_document.pdf")}),
    )

    connection = connect(str(db_path))
    repository = OfficialSourcesRepository(connection)
    files = repository.list_document_files(document["id"])
    attempts = repository.list_artifact_download_attempts(document_id=document["id"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert {file_record["file_type"] for file_record in files} == {"pdf"}
    assert attempts[-1]["file_type"] == "pdf"
    assert attempts[-1]["status"] == "success"
    assert "artifact_types=pdf" in captured.out


def test_candidate_evidence_object_contains_availability_fields(tmp_path):
    db_path = tmp_path / "db.sqlite"
    document, candidate = _seed_candidate(db_path)
    connection = connect(str(db_path))
    repository = OfficialSourcesRepository(connection)
    repository.mark_candidate_evidence_review(
        source_candidate_id=candidate["id"],
        evidence_label="likely_relevant",
        evidence_review_status="evidence_downloaded",
    )
    repository.upsert_document_file(
        document_id=document["id"],
        file_type="xml",
        official_url=document["url_xml"],
        payload=b"<document>ok</document>",
        ingestion_run_id=None,
    )
    repository.upsert_document_file(
        document_id=document["id"],
        file_type="html",
        official_url=document["url_html"],
        payload=b"<html>ok</html>",
        ingestion_run_id=None,
    )

    evidence = repository.get_candidate_evidence_object(candidate["id"])

    assert evidence["candidate"]["candidate_id"] == candidate["id"]
    assert evidence["candidate"]["review_status"] == "human_review_required"
    assert evidence["candidate"]["evidence_review_status"] == "evidence_downloaded"
    assert evidence["candidate"]["evidence_label"] == "likely_relevant"
    assert evidence["evidence"] == {
        "xml_available": True,
        "html_available": True,
        "pdf_available": False,
        "pdf_policy": "on_demand",
        "integrity_warning": False,
    }
