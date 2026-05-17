from __future__ import annotations

import json
import sqlite3
from datetime import UTC, date, datetime
from typing import Any

from official_sources.integrity.hashing import sha256_bytes, sha256_text


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return dict(row)


class OfficialSourcesRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def ensure_official_source_boe(self) -> dict[str, Any]:
        return self.upsert_official_source(
            code="BOE",
            name="Boletin Oficial del Estado",
            jurisdiction="state",
            region_code="ES",
            base_url="https://www.boe.es",
            access_type="official_api",
            reliability_level="canonical",
        )

    def upsert_official_source(
        self,
        *,
        code: str,
        name: str,
        jurisdiction: str,
        region_code: str,
        base_url: str,
        access_type: str,
        reliability_level: str,
    ) -> dict[str, Any]:
        now = utc_now()
        self.connection.execute(
            """
            INSERT INTO official_sources (
                code, name, jurisdiction, region_code, base_url, access_type,
                reliability_level, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(code) DO UPDATE SET
                name = excluded.name,
                jurisdiction = excluded.jurisdiction,
                region_code = excluded.region_code,
                base_url = excluded.base_url,
                access_type = excluded.access_type,
                reliability_level = excluded.reliability_level,
                updated_at = excluded.updated_at
            """,
            (
                code,
                name,
                jurisdiction,
                region_code,
                base_url,
                access_type,
                reliability_level,
                now,
                now,
            ),
        )
        self.connection.commit()
        source = self.get_source_by_code(code)
        assert source is not None
        return source

    def get_source_by_code(self, code: str) -> dict[str, Any]:
        row = self.connection.execute(
            "SELECT * FROM official_sources WHERE code = ?",
            (code,),
        ).fetchone()
        result = row_to_dict(row)
        if result is None:
            raise KeyError(f"Unknown source code: {code}")
        return result

    def upsert_document(
        self,
        *,
        source_id: int,
        external_id: str,
        publication_date: str,
        title: str,
        department: str | None = None,
        section: str | None = None,
        document_type: str | None = None,
        url_html: str | None = None,
        url_xml: str | None = None,
        url_pdf: str | None = None,
        raw_metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        now = utc_now()
        raw_metadata_json = json.dumps(raw_metadata or {}, sort_keys=True)
        self.connection.execute(
            """
            INSERT INTO official_documents (
                source_id, external_id, publication_date, title, department, section,
                document_type, url_html, url_xml, url_pdf, raw_metadata_json,
                created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(source_id, external_id) DO UPDATE SET
                publication_date = excluded.publication_date,
                title = excluded.title,
                department = excluded.department,
                section = excluded.section,
                document_type = excluded.document_type,
                url_html = excluded.url_html,
                url_xml = excluded.url_xml,
                url_pdf = excluded.url_pdf,
                raw_metadata_json = excluded.raw_metadata_json,
                updated_at = excluded.updated_at
            """,
            (
                source_id,
                external_id,
                publication_date,
                title,
                department,
                section,
                document_type,
                url_html,
                url_xml,
                url_pdf,
                raw_metadata_json,
                now,
                now,
            ),
        )
        self.connection.commit()
        document = self.get_document_by_external_id(external_id)
        assert document is not None
        return document

    def get_document_by_external_id(self, external_id: str) -> dict[str, Any] | None:
        return row_to_dict(
            self.connection.execute(
                """
                SELECT d.*, s.code AS source_code, s.name AS source_name
                FROM official_documents d
                JOIN official_sources s ON s.id = d.source_id
                WHERE d.external_id = ?
                """,
                (external_id,),
            ).fetchone()
        )

    def search_documents(
        self,
        *,
        keyword: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        values: list[Any] = []
        if keyword:
            clauses.append("(d.title LIKE ? OR d.external_id LIKE ?)")
            like = f"%{keyword}%"
            values.extend([like, like])
        if date_from:
            clauses.append("d.publication_date >= ?")
            values.append(date_from)
        if date_to:
            clauses.append("d.publication_date <= ?")
            values.append(date_to)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        values.append(limit)
        rows = self.connection.execute(
            f"""
            SELECT d.*, s.code AS source_code
            FROM official_documents d
            JOIN official_sources s ON s.id = d.source_id
            {where}
            ORDER BY d.publication_date DESC, d.external_id ASC
            LIMIT ?
            """,
            values,
        ).fetchall()
        return [dict(row) for row in rows]

    def list_documents_by_date(self, target_date: str) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            """
            SELECT d.*, s.code AS source_code
            FROM official_documents d
            JOIN official_sources s ON s.id = d.source_id
            WHERE d.publication_date = ?
            ORDER BY d.external_id ASC
            """,
            (target_date,),
        ).fetchall()
        return [dict(row) for row in rows]

    def upsert_document_file(
        self,
        *,
        document_id: int,
        file_type: str,
        official_url: str,
        payload: bytes,
        ingestion_run_id: int | None,
        local_path: str | None = None,
        media_type: str | None = None,
        source_snapshot_hash: str | None = None,
    ) -> dict[str, Any]:
        now = utc_now()
        current_hash = sha256_bytes(payload)
        snapshot_hash = source_snapshot_hash or current_hash
        existing = row_to_dict(
            self.connection.execute(
                """
                SELECT * FROM document_files
                WHERE document_id = ? AND file_type = ? AND official_url = ?
                """,
                (document_id, file_type, official_url),
            ).fetchone()
        )
        if existing is None:
            cursor = self.connection.execute(
                """
                INSERT INTO document_files (
                    document_id, file_type, official_url, local_path, media_type,
                    size_bytes, sha256, source_snapshot_hash, first_seen_at, last_seen_at,
                    last_integrity_check_at, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    document_id,
                    file_type,
                    official_url,
                    local_path,
                    media_type,
                    len(payload),
                    current_hash,
                    snapshot_hash,
                    now,
                    now,
                    now,
                    now,
                    now,
                ),
            )
            file_id = cursor.lastrowid
            self._create_integrity_check(
                document_file_id=file_id,
                ingestion_run_id=ingestion_run_id,
                previous_sha256=None,
                current_sha256=current_hash,
                changed=False,
                change_reason="new_file",
            )
        else:
            changed = existing["sha256"] != current_hash
            previous_hash = existing["sha256"] if changed else existing["previous_hash"]
            content_changed_at = now if changed else existing["content_changed_at"]
            change_detected_by = ingestion_run_id if changed else existing["change_detected_by"]
            self.connection.execute(
                """
                UPDATE document_files
                SET local_path = ?, media_type = ?, size_bytes = ?, sha256 = ?,
                    source_snapshot_hash = ?, last_seen_at = ?,
                    last_integrity_check_at = ?, content_changed_at = ?,
                    previous_hash = ?, change_detected_by = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    local_path,
                    media_type,
                    len(payload),
                    current_hash,
                    snapshot_hash,
                    now,
                    now,
                    content_changed_at,
                    previous_hash,
                    change_detected_by,
                    now,
                    existing["id"],
                ),
            )
            file_id = existing["id"]
            self._create_integrity_check(
                document_file_id=file_id,
                ingestion_run_id=ingestion_run_id,
                previous_sha256=existing["sha256"],
                current_sha256=current_hash,
                changed=changed,
                change_reason="hash_changed" if changed else "unchanged",
            )
        self.connection.commit()
        return self.get_document_file(file_id)

    def _create_integrity_check(
        self,
        *,
        document_file_id: int,
        ingestion_run_id: int | None,
        previous_sha256: str | None,
        current_sha256: str,
        changed: bool,
        change_reason: str,
        notes: str | None = None,
    ) -> None:
        now = utc_now()
        self.connection.execute(
            """
            INSERT INTO integrity_checks (
                document_file_id, ingestion_run_id, checked_at, previous_sha256,
                current_sha256, changed, change_reason, notes, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                document_file_id,
                ingestion_run_id,
                now,
                previous_sha256,
                current_sha256,
                1 if changed else 0,
                change_reason,
                notes,
                now,
            ),
        )

    def get_document_file(self, file_id: int) -> dict[str, Any]:
        row = self.connection.execute(
            "SELECT * FROM document_files WHERE id = ?", (file_id,)
        ).fetchone()
        result = row_to_dict(row)
        if result is None:
            raise KeyError(f"Unknown document file: {file_id}")
        return result

    def list_document_files(self, document_id: int) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            "SELECT * FROM document_files WHERE document_id = ? ORDER BY id",
            (document_id,),
        ).fetchall()
        return [dict(row) for row in rows]

    def list_document_files_by_date(self, target_date: str) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            """
            SELECT f.*, d.external_id, d.publication_date
            FROM document_files f
            JOIN official_documents d ON d.id = f.document_id
            WHERE d.publication_date = ?
            ORDER BY d.external_id ASC, f.file_type ASC
            """,
            (target_date,),
        ).fetchall()
        return [dict(row) for row in rows]

    def list_integrity_checks(self, document_file_id: int) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            "SELECT * FROM integrity_checks WHERE document_file_id = ? ORDER BY id",
            (document_file_id,),
        ).fetchall()
        return [dict(row) for row in rows]

    def create_document_text(
        self,
        *,
        document_id: int,
        source_file_id: int,
        text_type: str,
        language: str,
        content: str,
        extraction_method: str,
    ) -> dict[str, Any]:
        now = utc_now()
        cursor = self.connection.execute(
            """
            INSERT INTO document_texts (
                document_id, source_file_id, text_type, language, content,
                content_sha256, extraction_method, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                document_id,
                source_file_id,
                text_type,
                language,
                content,
                sha256_text(content),
                extraction_method,
                now,
                now,
            ),
        )
        self.connection.commit()
        return row_to_dict(
            self.connection.execute(
                "SELECT * FROM document_texts WHERE id = ?",
                (cursor.lastrowid,),
            ).fetchone()
        )

    def create_artifact_download_attempt(
        self,
        *,
        document_id: int,
        ingestion_run_id: int | None,
        file_type: str,
        official_url: str | None,
        status: str,
        http_status: int | None,
        error_message: str | None,
        started_at: str,
        finished_at: str,
        retry_count: int = 0,
        throttle_triggered: bool = False,
    ) -> dict[str, Any]:
        cursor = self.connection.execute(
            """
            INSERT INTO artifact_download_attempts (
                document_id, ingestion_run_id, file_type, official_url, status,
                http_status, error_message, throttle_triggered, retry_count,
                started_at, finished_at, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                document_id,
                ingestion_run_id,
                file_type,
                official_url,
                status,
                http_status,
                error_message,
                1 if throttle_triggered else 0,
                retry_count,
                started_at,
                finished_at,
                utc_now(),
            ),
        )
        self.connection.commit()
        result = row_to_dict(
            self.connection.execute(
                "SELECT * FROM artifact_download_attempts WHERE id = ?",
                (cursor.lastrowid,),
            ).fetchone()
        )
        assert result is not None
        return result

    def list_artifact_download_attempts(
        self,
        *,
        document_id: int | None = None,
        target_date: str | None = None,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        values: list[Any] = []
        if document_id is not None:
            clauses.append("a.document_id = ?")
            values.append(document_id)
        if target_date is not None:
            clauses.append("d.publication_date = ?")
            values.append(target_date)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = self.connection.execute(
            f"""
            SELECT a.*, d.publication_date, d.external_id
            FROM artifact_download_attempts a
            JOIN official_documents d ON d.id = a.document_id
            {where}
            ORDER BY a.id ASC
            """,
            values,
        ).fetchall()
        return [dict(row) for row in rows]

    def count_artifact_download_attempts_by_date(self, target_date: str) -> dict[str, int]:
        rows = self.connection.execute(
            """
            SELECT a.status, COUNT(*) AS count
            FROM artifact_download_attempts a
            JOIN official_documents d ON d.id = a.document_id
            WHERE d.publication_date = ?
            GROUP BY a.status
            """,
            (target_date,),
        ).fetchall()
        counts = {"success": 0, "skipped": 0, "failed": 0, "changed": 0}
        for row in rows:
            counts[row["status"]] = row["count"]
        return counts

    def upsert_consolidated_law(
        self,
        *,
        source_id: int,
        external_id: str,
        official_identifier: str,
        title: str,
        law_type: str | None,
        jurisdiction: str,
        department: str | None,
        publication_date: str | None,
        consolidation_status: str | None,
        official_url: str,
        raw_metadata: dict[str, Any],
    ) -> dict[str, Any]:
        now = utc_now()
        self.connection.execute(
            """
            INSERT INTO consolidated_laws (
                source_id, external_id, official_identifier, title, law_type,
                jurisdiction, department, publication_date, consolidation_status,
                official_url, raw_metadata_json, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(official_identifier) DO UPDATE SET
                title = excluded.title,
                law_type = excluded.law_type,
                jurisdiction = excluded.jurisdiction,
                department = excluded.department,
                publication_date = excluded.publication_date,
                consolidation_status = excluded.consolidation_status,
                official_url = excluded.official_url,
                raw_metadata_json = excluded.raw_metadata_json,
                updated_at = excluded.updated_at
            """,
            (
                source_id,
                external_id,
                official_identifier,
                title,
                law_type,
                jurisdiction,
                department,
                publication_date,
                consolidation_status,
                official_url,
                json.dumps(raw_metadata, sort_keys=True),
                now,
                now,
            ),
        )
        self.connection.commit()
        law = self.get_consolidated_law_by_identifier(official_identifier)
        assert law is not None
        return law

    def get_consolidated_law_by_identifier(self, official_identifier: str) -> dict[str, Any] | None:
        return row_to_dict(
            self.connection.execute(
                """
                SELECT l.*, s.code AS source_code, s.name AS source_name
                FROM consolidated_laws l
                JOIN official_sources s ON s.id = l.source_id
                WHERE l.official_identifier = ?
                """,
                (official_identifier,),
            ).fetchone()
        )

    def upsert_consolidated_law_version(
        self,
        *,
        consolidated_law_id: int,
        version_identifier: str,
        version_date: str | None,
        valid_from: str | None,
        valid_to: str | None,
        is_current: bool,
        official_url: str,
        raw_payload_hash: str,
        source_snapshot_hash: str,
    ) -> dict[str, Any]:
        now = utc_now()
        existing = row_to_dict(
            self.connection.execute(
                """
                SELECT * FROM consolidated_law_versions
                WHERE consolidated_law_id = ? AND version_identifier = ?
                """,
                (consolidated_law_id, version_identifier),
            ).fetchone()
        )
        previous_hash = None
        content_changed_at = None
        changed = False
        if existing is not None:
            changed = existing["source_snapshot_hash"] != source_snapshot_hash
            previous_hash = (
                existing["source_snapshot_hash"] if changed else existing["previous_hash"]
            )
            content_changed_at = now if changed else existing["content_changed_at"]
        self.connection.execute(
            """
            INSERT INTO consolidated_law_versions (
                consolidated_law_id, version_identifier, version_date, valid_from,
                valid_to, is_current, official_url, raw_payload_hash,
                source_snapshot_hash, previous_hash, content_changed_at,
                created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(consolidated_law_id, version_identifier) DO UPDATE SET
                version_date = excluded.version_date,
                valid_from = excluded.valid_from,
                valid_to = excluded.valid_to,
                is_current = excluded.is_current,
                official_url = excluded.official_url,
                raw_payload_hash = excluded.raw_payload_hash,
                source_snapshot_hash = excluded.source_snapshot_hash,
                previous_hash = excluded.previous_hash,
                content_changed_at = excluded.content_changed_at,
                updated_at = excluded.updated_at
            """,
            (
                consolidated_law_id,
                version_identifier,
                version_date,
                valid_from,
                valid_to,
                1 if is_current else 0,
                official_url,
                raw_payload_hash,
                source_snapshot_hash,
                previous_hash,
                content_changed_at,
                now,
                now,
            ),
        )
        version = self.get_consolidated_law_version(consolidated_law_id, version_identifier)
        self._create_consolidated_law_integrity_check(
            consolidated_law_version_id=version["id"],
            previous_sha256=existing["source_snapshot_hash"] if existing else None,
            current_sha256=source_snapshot_hash,
            changed=changed,
            change_reason="hash_changed"
            if changed
            else ("new_version" if existing is None else "unchanged"),
        )
        self.connection.commit()
        return self.get_consolidated_law_version(consolidated_law_id, version_identifier)

    def get_consolidated_law_version(
        self,
        consolidated_law_id: int,
        version_identifier: str,
    ) -> dict[str, Any]:
        row = self.connection.execute(
            """
            SELECT * FROM consolidated_law_versions
            WHERE consolidated_law_id = ? AND version_identifier = ?
            """,
            (consolidated_law_id, version_identifier),
        ).fetchone()
        result = row_to_dict(row)
        if result is None:
            raise KeyError(f"Unknown consolidated law version: {version_identifier}")
        return result

    def list_consolidated_law_versions(self, consolidated_law_id: int) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            """
            SELECT * FROM consolidated_law_versions
            WHERE consolidated_law_id = ?
            ORDER BY id
            """,
            (consolidated_law_id,),
        ).fetchall()
        return [dict(row) for row in rows]

    def replace_consolidated_law_text_blocks(
        self,
        *,
        consolidated_law_id: int,
        version_id: int,
        blocks: list[dict[str, Any]],
    ) -> None:
        self.connection.execute(
            """
            DELETE FROM consolidated_law_text_blocks
            WHERE consolidated_law_id = ? AND version_id = ?
            """,
            (consolidated_law_id, version_id),
        )
        for block in blocks:
            self.upsert_consolidated_law_text_block(
                consolidated_law_id=consolidated_law_id,
                version_id=version_id,
                official_block_id=block.get("official_block_id", block["block_identifier"]),
                block_type=block["block_type"],
                block_identifier=block["block_identifier"],
                title=block["title"],
                content=block["content"],
                content_sha256=block["content_sha256"],
                source_snapshot_hash=block["source_snapshot_hash"],
                order_index=block["order_index"],
                parent_block_id=block.get("parent_block_id"),
                block_path=block.get("block_path", block["block_identifier"]),
                api_url=block.get("api_url"),
                raw_payload_hash=block.get("raw_payload_hash", block["source_snapshot_hash"]),
                raw_metadata=block.get("raw_metadata"),
            )
        self.connection.commit()

    def upsert_consolidated_law_text_block(
        self,
        *,
        consolidated_law_id: int,
        version_id: int,
        official_block_id: str,
        block_type: str,
        block_identifier: str,
        title: str | None,
        content: str,
        content_sha256: str,
        source_snapshot_hash: str,
        order_index: int,
        parent_block_id: str | None = None,
        block_path: str | None = None,
        api_url: str | None = None,
        raw_payload_hash: str | None = None,
        raw_metadata: dict[str, Any] | None = None,
        change_detected_by: int | None = None,
    ) -> dict[str, Any]:
        now = utc_now()
        current_payload_hash = raw_payload_hash or source_snapshot_hash
        existing = row_to_dict(
            self.connection.execute(
                """
                SELECT * FROM consolidated_law_text_blocks
                WHERE consolidated_law_id = ? AND version_id = ? AND official_block_id = ?
                """,
                (consolidated_law_id, version_id, official_block_id),
            ).fetchone()
        )
        if existing is not None:
            existing_hash = existing["raw_payload_hash"] or existing["source_snapshot_hash"]
            changed = existing_hash != current_payload_hash
            previous_hash = existing_hash if changed else existing["previous_hash"]
            content_changed_at = now if changed else existing["content_changed_at"]
            detected_by = change_detected_by if changed else existing["change_detected_by"]
            self.connection.execute(
                """
                UPDATE consolidated_law_text_blocks
                SET parent_block_id = ?, block_path = ?, api_url = ?, block_type = ?,
                    block_identifier = ?, title = ?, content = ?, content_sha256 = ?,
                    raw_payload_hash = ?, source_snapshot_hash = ?, order_index = ?,
                    raw_metadata_json = ?, last_seen_at = ?, content_changed_at = ?,
                    previous_hash = ?, change_detected_by = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    parent_block_id,
                    block_path,
                    api_url,
                    block_type,
                    block_identifier,
                    title,
                    content,
                    content_sha256 or sha256_text(content),
                    current_payload_hash,
                    source_snapshot_hash,
                    order_index,
                    json.dumps(raw_metadata or {}, sort_keys=True),
                    now,
                    content_changed_at,
                    previous_hash,
                    detected_by,
                    now,
                    existing["id"],
                ),
            )
            block_row_id = existing["id"]
        else:
            cursor = self.connection.execute(
                """
                INSERT INTO consolidated_law_text_blocks (
                    consolidated_law_id, version_id, official_block_id, parent_block_id,
                    block_path, api_url, block_type, block_identifier, title, content,
                    content_sha256, raw_payload_hash, source_snapshot_hash, order_index,
                    raw_metadata_json, last_seen_at, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    consolidated_law_id,
                    version_id,
                    official_block_id,
                    parent_block_id,
                    block_path,
                    api_url,
                    block_type,
                    block_identifier,
                    title,
                    content,
                    content_sha256 or sha256_text(content),
                    current_payload_hash,
                    source_snapshot_hash,
                    order_index,
                    json.dumps(raw_metadata or {}, sort_keys=True),
                    now,
                    now,
                    now,
                ),
            )
            block_row_id = cursor.lastrowid
        self.connection.commit()
        result = row_to_dict(
            self.connection.execute(
                "SELECT * FROM consolidated_law_text_blocks WHERE id = ?",
                (block_row_id,),
            ).fetchone()
        )
        assert result is not None
        return result

    def list_consolidated_law_text_blocks(
        self,
        consolidated_law_id: int,
        version_id: int | None = None,
    ) -> list[dict[str, Any]]:
        clauses = ["consolidated_law_id = ?"]
        values: list[Any] = [consolidated_law_id]
        if version_id is not None:
            clauses.append("version_id = ?")
            values.append(version_id)
        rows = self.connection.execute(
            f"""
            SELECT * FROM consolidated_law_text_blocks
            WHERE {" AND ".join(clauses)}
            ORDER BY order_index ASC, id ASC
            """,
            values,
        ).fetchall()
        return [dict(row) for row in rows]

    def get_consolidated_law_text_block(
        self,
        consolidated_law_id: int,
        block_identifier: str,
    ) -> dict[str, Any] | None:
        return row_to_dict(
            self.connection.execute(
                """
                SELECT * FROM consolidated_law_text_blocks
                WHERE consolidated_law_id = ?
                    AND (block_identifier = ? OR official_block_id = ?)
                    AND content != ''
                ORDER BY updated_at DESC, order_index ASC
                LIMIT 1
                """,
                (consolidated_law_id, block_identifier, block_identifier),
            ).fetchone()
        )

    def _create_consolidated_law_integrity_check(
        self,
        *,
        consolidated_law_version_id: int,
        previous_sha256: str | None,
        current_sha256: str,
        changed: bool,
        change_reason: str,
        notes: str | None = None,
    ) -> None:
        now = utc_now()
        self.connection.execute(
            """
            INSERT INTO consolidated_law_integrity_checks (
                consolidated_law_version_id, checked_at, previous_sha256,
                current_sha256, changed, change_reason, notes, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                consolidated_law_version_id,
                now,
                previous_sha256,
                current_sha256,
                1 if changed else 0,
                change_reason,
                notes,
                now,
            ),
        )

    def list_consolidated_law_integrity_checks(
        self,
        consolidated_law_version_id: int,
    ) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            """
            SELECT * FROM consolidated_law_integrity_checks
            WHERE consolidated_law_version_id = ?
            ORDER BY id ASC
            """,
            (consolidated_law_version_id,),
        ).fetchall()
        return [dict(row) for row in rows]

    def get_document_text(
        self, document_id: int, text_type: str = "clean_text"
    ) -> dict[str, Any] | None:
        return row_to_dict(
            self.connection.execute(
                """
                SELECT * FROM document_texts
                WHERE document_id = ? AND text_type = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (document_id, text_type),
            ).fetchone()
        )

    def create_source_candidate(
        self,
        *,
        document_id: int,
        project_key: str,
        candidate_type: str,
        extraction_status: str,
        evidence_level: str,
        matched_fields: dict[str, Any],
        review_status: str = "human_review_required",
        review_notes: str | None = None,
    ) -> dict[str, Any]:
        now = utc_now()
        cursor = self.connection.execute(
            """
            INSERT INTO source_candidates (
                document_id, project_key, candidate_type, extraction_status,
                evidence_level, matched_fields_json, review_status, review_notes,
                created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                document_id,
                project_key,
                candidate_type,
                extraction_status,
                evidence_level,
                json.dumps(matched_fields, sort_keys=True),
                review_status,
                review_notes,
                now,
                now,
            ),
        )
        self.connection.commit()
        return row_to_dict(
            self.connection.execute(
                "SELECT * FROM source_candidates WHERE id = ?",
                (cursor.lastrowid,),
            ).fetchone()
        )

    def create_ingestion_run(self, *, source_code: str, target_date: str | None) -> dict[str, Any]:
        now = utc_now()
        cursor = self.connection.execute(
            """
            INSERT INTO ingestion_runs (
                source_code, run_date, target_date, status, started_at
            )
            VALUES (?, ?, ?, 'pending', ?)
            """,
            (source_code, date.today().isoformat(), target_date, now),
        )
        self.connection.commit()
        return self.get_ingestion_run(cursor.lastrowid)

    def finish_ingestion_run(
        self,
        *,
        run_id: int,
        status: str,
        documents_fetched: int,
        documents_new: int,
        documents_updated: int,
        error_message: str | None = None,
        retry_count: int = 0,
        throttle_triggered: bool = False,
        last_http_status: int | None = None,
    ) -> dict[str, Any]:
        self.connection.execute(
            """
            UPDATE ingestion_runs
            SET status = ?, documents_fetched = ?, documents_new = ?,
                documents_updated = ?, error_message = ?, throttle_triggered = ?,
                retry_count = ?, last_http_status = ?, finished_at = ?
            WHERE id = ?
            """,
            (
                status,
                documents_fetched,
                documents_new,
                documents_updated,
                error_message,
                1 if throttle_triggered else 0,
                retry_count,
                last_http_status,
                utc_now(),
                run_id,
            ),
        )
        self.connection.commit()
        return self.get_ingestion_run(run_id)

    def get_ingestion_run(self, run_id: int) -> dict[str, Any]:
        row = self.connection.execute(
            "SELECT * FROM ingestion_runs WHERE id = ?", (run_id,)
        ).fetchone()
        result = row_to_dict(row)
        if result is None:
            raise KeyError(f"Unknown ingestion run: {run_id}")
        return result

    def get_latest_ingestion_run(self, source_code: str, target_date: str) -> dict[str, Any] | None:
        return row_to_dict(
            self.connection.execute(
                """
                SELECT * FROM ingestion_runs
                WHERE source_code = ? AND target_date = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (source_code, target_date),
            ).fetchone()
        )
