from __future__ import annotations

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS official_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    jurisdiction TEXT NOT NULL,
    region_code TEXT NOT NULL,
    base_url TEXT NOT NULL,
    access_type TEXT NOT NULL,
    reliability_level TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS official_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER NOT NULL REFERENCES official_sources(id),
    external_id TEXT NOT NULL,
    publication_date TEXT NOT NULL,
    title TEXT NOT NULL,
    department TEXT,
    section TEXT,
    document_type TEXT,
    url_html TEXT,
    url_xml TEXT,
    url_pdf TEXT,
    raw_metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(source_id, external_id)
);

CREATE TABLE IF NOT EXISTS document_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL REFERENCES official_documents(id),
    file_type TEXT NOT NULL CHECK(file_type IN ('pdf', 'xml', 'html', 'json', 'raw_api_response')),
    official_url TEXT NOT NULL,
    local_path TEXT,
    media_type TEXT,
    size_bytes INTEGER NOT NULL,
    sha256 TEXT NOT NULL,
    source_snapshot_hash TEXT NOT NULL,
    signature_status TEXT NOT NULL DEFAULT 'not_checked'
        CHECK(signature_status IN (
            'not_checked',
            'valid_signature',
            'invalid_signature',
            'no_signature',
            'unavailable'
        )),
    signature_checked_at TEXT,
    signature_validation_method TEXT,
    first_seen_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    last_integrity_check_at TEXT,
    content_changed_at TEXT,
    previous_hash TEXT,
    change_detected_by INTEGER REFERENCES ingestion_runs(id),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(document_id, file_type, official_url)
);

CREATE TABLE IF NOT EXISTS document_texts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL REFERENCES official_documents(id),
    source_file_id INTEGER NOT NULL REFERENCES document_files(id),
    text_type TEXT NOT NULL CHECK(text_type IN ('raw_text', 'clean_text', 'structured_text')),
    language TEXT NOT NULL,
    content TEXT NOT NULL,
    content_sha256 TEXT NOT NULL,
    extraction_method TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS document_references (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL REFERENCES official_documents(id),
    reference_type TEXT NOT NULL,
    referenced_external_id TEXT,
    referenced_title TEXT,
    reference_text TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS source_candidates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL REFERENCES official_documents(id),
    project_key TEXT NOT NULL,
    candidate_type TEXT NOT NULL,
    extraction_status TEXT NOT NULL CHECK(extraction_status IN (
        'raw_detected',
        'parsed_candidate',
        'evidence_linked',
        'human_review_required',
        'human_accepted',
        'rejected'
    )),
    evidence_level TEXT NOT NULL,
    matched_fields_json TEXT NOT NULL,
    review_status TEXT NOT NULL DEFAULT 'human_review_required'
        CHECK(review_status IN ('human_review_required', 'human_accepted', 'rejected')),
    review_notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ingestion_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_code TEXT NOT NULL,
    run_date TEXT NOT NULL,
    target_date TEXT,
    status TEXT NOT NULL CHECK(status IN ('pending', 'success', 'partial', 'failed')),
    documents_fetched INTEGER NOT NULL DEFAULT 0,
    documents_new INTEGER NOT NULL DEFAULT 0,
    documents_updated INTEGER NOT NULL DEFAULT 0,
    error_message TEXT,
    throttle_triggered INTEGER NOT NULL DEFAULT 0,
    retry_count INTEGER NOT NULL DEFAULT 0,
    last_http_status INTEGER,
    started_at TEXT NOT NULL,
    finished_at TEXT
);

CREATE TABLE IF NOT EXISTS integrity_checks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_file_id INTEGER NOT NULL REFERENCES document_files(id),
    ingestion_run_id INTEGER REFERENCES ingestion_runs(id),
    checked_at TEXT NOT NULL,
    previous_sha256 TEXT,
    current_sha256 TEXT NOT NULL,
    changed INTEGER NOT NULL CHECK(changed IN (0, 1)),
    change_reason TEXT,
    notes TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS artifact_download_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL REFERENCES official_documents(id),
    ingestion_run_id INTEGER REFERENCES ingestion_runs(id),
    file_type TEXT NOT NULL,
    official_url TEXT,
    status TEXT NOT NULL CHECK(status IN ('success', 'skipped', 'failed', 'changed')),
    http_status INTEGER,
    error_message TEXT,
    throttle_triggered INTEGER NOT NULL DEFAULT 0,
    retry_count INTEGER NOT NULL DEFAULT 0,
    started_at TEXT NOT NULL,
    finished_at TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS consolidated_laws (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER NOT NULL REFERENCES official_sources(id),
    external_id TEXT NOT NULL,
    official_identifier TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    law_type TEXT,
    jurisdiction TEXT NOT NULL,
    department TEXT,
    publication_date TEXT,
    consolidation_status TEXT,
    official_url TEXT NOT NULL,
    raw_metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS consolidated_law_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    consolidated_law_id INTEGER NOT NULL REFERENCES consolidated_laws(id),
    version_identifier TEXT NOT NULL,
    version_date TEXT,
    valid_from TEXT,
    valid_to TEXT,
    is_current INTEGER NOT NULL CHECK(is_current IN (0, 1)),
    official_url TEXT NOT NULL,
    raw_payload_hash TEXT NOT NULL,
    source_snapshot_hash TEXT NOT NULL,
    previous_hash TEXT,
    content_changed_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(consolidated_law_id, version_identifier)
);

CREATE TABLE IF NOT EXISTS consolidated_law_text_blocks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    consolidated_law_id INTEGER NOT NULL REFERENCES consolidated_laws(id),
    version_id INTEGER NOT NULL REFERENCES consolidated_law_versions(id),
    official_block_id TEXT,
    parent_block_id TEXT,
    block_path TEXT,
    api_url TEXT,
    block_type TEXT NOT NULL,
    block_identifier TEXT NOT NULL,
    title TEXT,
    content TEXT NOT NULL,
    content_sha256 TEXT NOT NULL,
    raw_payload_hash TEXT,
    source_snapshot_hash TEXT NOT NULL,
    order_index INTEGER NOT NULL,
    raw_metadata_json TEXT NOT NULL DEFAULT '{}',
    last_seen_at TEXT,
    content_changed_at TEXT,
    previous_hash TEXT,
    change_detected_by INTEGER REFERENCES ingestion_runs(id),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS consolidated_law_references (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    consolidated_law_id INTEGER NOT NULL REFERENCES consolidated_laws(id),
    referenced_identifier TEXT,
    reference_type TEXT NOT NULL,
    reference_text TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS consolidated_law_integrity_checks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    consolidated_law_version_id INTEGER NOT NULL REFERENCES consolidated_law_versions(id),
    checked_at TEXT NOT NULL,
    previous_sha256 TEXT,
    current_sha256 TEXT NOT NULL,
    changed INTEGER NOT NULL CHECK(changed IN (0, 1)),
    change_reason TEXT,
    notes TEXT,
    created_at TEXT NOT NULL
);
"""
