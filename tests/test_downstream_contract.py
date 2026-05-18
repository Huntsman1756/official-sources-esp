from __future__ import annotations

from pathlib import Path


def test_downstream_contract_exists_and_defines_operational_boundaries():
    path = Path(__file__).parents[1] / "docs" / "DOWNSTREAM_CONTRACT.md"

    assert path.exists()
    content = path.read_text(encoding="utf-8")
    assert "pending_review" in content
    assert "does not approve" in content
    assert "does not publish" in content
    assert "Required evidence object" in content
    assert "hashes_match" in content
    assert "source_snapshot_hash" in content
    assert "ingestion-time raw payload hash" in content
    assert "content_sha256" in content
    assert "latest-check/current artifact hash" in content
    assert "should not compare hash strings manually" in content
    assert "requires re-review, not automatic rejection" in content
    assert "preserve integrity warnings" in content
    assert "block automatic approval/publication" in content
    assert "Example downstream flow" in content
    assert '"evidence_review_status": "evidence_downloaded"' in content
    assert '"evidence_label": "likely_relevant"' in content
    assert '"xml_available": true' in content
    assert '"html_available": true' in content
    assert '"pdf_available": false' in content
    assert '"pdf_policy": "on_demand"' in content
    assert "likely_relevant is not approval" in content
    assert "PDF is on-demand" in content
    assert "PDF absence does not mean evidence is invalid" in content
    assert "PDF presence does not mean candidate is approved" in content


def test_pre_task_004b_downstream_checklist_exists():
    path = Path(__file__).parents[1] / "docs" / "reports" / "PRE_TASK_004B_DOWNSTREAM_CHECKLIST.md"

    assert path.exists()
    content = path.read_text(encoding="utf-8")
    assert "candidates/evidence table" in content
    assert "pending_review workflow" in content
    assert "source_snapshot_hash" in content
    assert "TASK-004B duration depends on downstream readiness" in content
