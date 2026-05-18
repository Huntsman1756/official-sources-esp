from __future__ import annotations

UP_SQL = """
CREATE TABLE IF NOT EXISTS candidate_evidence_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_candidate_id INTEGER NOT NULL REFERENCES source_candidates(id) ON DELETE CASCADE,
    evidence_review_status TEXT NOT NULL DEFAULT 'not_reviewed'
        CHECK(evidence_review_status IN (
            'not_reviewed',
            'evidence_selected',
            'evidence_downloaded',
            'evidence_reviewed',
            'needs_more_evidence',
            'false_positive',
            'out_of_scope'
        )),
    evidence_label TEXT
        CHECK(evidence_label IS NULL OR evidence_label IN (
            'likely_relevant',
            'unclear',
            'false_positive',
            'out_of_scope'
        )),
    evidence_notes TEXT,
    selected_for_evidence INTEGER NOT NULL DEFAULT 0 CHECK(selected_for_evidence IN (0, 1)),
    selected_for_pdf INTEGER NOT NULL DEFAULT 0 CHECK(selected_for_pdf IN (0, 1)),
    xml_available INTEGER NOT NULL DEFAULT 0 CHECK(xml_available IN (0, 1)),
    html_available INTEGER NOT NULL DEFAULT 0 CHECK(html_available IN (0, 1)),
    pdf_available INTEGER NOT NULL DEFAULT 0 CHECK(pdf_available IN (0, 1)),
    integrity_warning INTEGER NOT NULL DEFAULT 0 CHECK(integrity_warning IN (0, 1)),
    reviewed_by TEXT,
    reviewed_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(source_candidate_id)
);
"""
