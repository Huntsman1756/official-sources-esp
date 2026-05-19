from __future__ import annotations

UP_SQL = """
ALTER TABLE candidate_evidence_reviews
    ADD COLUMN manual_decision TEXT
        CHECK(manual_decision IS NULL OR manual_decision IN (
            'accept_for_downstream_pilot',
            'needs_more_evidence',
            'reject_false_positive',
            'out_of_scope',
            'defer'
        ));

ALTER TABLE candidate_evidence_reviews
    ADD COLUMN manual_notes TEXT;

ALTER TABLE candidate_evidence_reviews
    ADD COLUMN needs_pdf TEXT
        CHECK(needs_pdf IS NULL OR needs_pdf IN ('yes', 'no'));

ALTER TABLE candidate_evidence_reviews
    ADD COLUMN downstream_project_fit TEXT
        CHECK(downstream_project_fit IS NULL OR downstream_project_fit IN (
            'la-ayuda',
            'EduAyudas',
            'both',
            'neither',
            'unclear'
        ));
"""
