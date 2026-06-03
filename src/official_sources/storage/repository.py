from __future__ import annotations

import json
import sqlite3
from datetime import UTC, date, datetime
from typing import Any

from official_sources.integrity.hashing import sha256_bytes, sha256_text

EVIDENCE_REVIEW_STATUSES = {
    "not_reviewed",
    "evidence_selected",
    "evidence_downloaded",
    "evidence_reviewed",
    "needs_more_evidence",
    "false_positive",
    "out_of_scope",
}
EVIDENCE_LABELS = {
    "likely_relevant",
    "unclear",
    "false_positive",
    "out_of_scope",
}
MANUAL_DECISIONS = {
    "accept_for_downstream_pilot",
    "needs_more_evidence",
    "reject_false_positive",
    "out_of_scope",
    "defer",
}
NEEDS_PDF_VALUES = {"yes", "no"}
DOWNSTREAM_PROJECT_FITS = {"la-ayuda", "EduAyudas", "both", "neither", "unclear"}
EVIDENCE_SELECTED_STATUSES = {
    "evidence_selected",
    "evidence_downloaded",
    "evidence_reviewed",
}


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

    def ensure_official_source_boja(self) -> dict[str, Any]:
        return self.upsert_official_source(
            code="BOJA",
            name="Boletin Oficial de la Junta de Andalucia",
            jurisdiction="autonomous",
            region_code="ES-AN",
            base_url="https://datos.juntadeandalucia.es/api/v0/boja",
            access_type="official_api",
            reliability_level="canonical",
        )

    def ensure_official_source_bocm(self) -> dict[str, Any]:
        return self.upsert_official_source(
            code="BOCM",
            name="Boletin Oficial de la Comunidad de Madrid",
            jurisdiction="autonomous",
            region_code="ES-MD",
            base_url="https://www.bocm.es",
            access_type="official_html",
            reliability_level="canonical",
        )

    def ensure_official_source_dogv(self) -> dict[str, Any]:
        return self.upsert_official_source(
            code="DOGV",
            name="Diari Oficial de la Generalitat Valenciana",
            jurisdiction="autonomous",
            region_code="ES-VC",
            base_url="https://dogv.gva.es/dogv-portal",
            access_type="official_json",
            reliability_level="canonical",
        )

    def ensure_official_source_dogc(self) -> dict[str, Any]:
        return self.upsert_official_source(
            code="DOGC",
            name="Diari Oficial de la Generalitat de Catalunya",
            jurisdiction="autonomous",
            region_code="ES-CT",
            base_url="https://portaldogc.gencat.cat/eadop-rest/api/dogc",
            access_type="official_api",
            reliability_level="canonical",
        )

    def ensure_official_source_bocyl(self) -> dict[str, Any]:
        return self.upsert_official_source(
            code="BOCYL",
            name="Boletín Oficial de Castilla y León",
            jurisdiction="autonomous",
            region_code="ES-CL",
            base_url="https://jcyl.opendatasoft.com/api/explore/v2.1/catalog/datasets/bocyl",
            access_type="official_json",
            reliability_level="canonical",
        )

    def ensure_official_source_bopv(self) -> dict[str, Any]:
        return self.upsert_official_source(
            code="BOPV",
            name="Boletín Oficial del País Vasco / Euskal Herriko Agintaritzaren Aldizkaria",
            jurisdiction="autonomous",
            region_code="ES-PV",
            base_url="https://www.euskadi.eus/bopv2/datos",
            access_type="official_xml",
            reliability_level="canonical",
        )

    def ensure_official_source_borm(self) -> dict[str, Any]:
        return self.upsert_official_source(
            code="BORM",
            name="Boletin Oficial de la Region de Murcia",
            jurisdiction="autonomous",
            region_code="ES-MC",
            base_url="https://transparencia.carm.es/rest-services/services/restFile/BORMIndice.xml",
            access_type="official_xml",
            reliability_level="canonical",
        )

    def ensure_official_source_bdns(self) -> dict[str, Any]:
        return self.upsert_official_source(
            code="BDNS",
            name="Base de Datos Nacional de Subvenciones",
            jurisdiction="state",
            region_code="ES",
            base_url="https://www.infosubvenciones.es/bdnstrans/api",
            access_type="official_api",
            reliability_level="canonical",
        )

    def ensure_official_source_placsp(self) -> dict[str, Any]:
        return self.upsert_official_source(
            code="PLACSP",
            name="Plataforma de Contratacion del Sector Publico",
            jurisdiction="ES",
            region_code="ES",
            base_url="https://contrataciondelsectorpublico.gob.es/sindicacion",
            access_type="official_atom",
            reliability_level="canonical",
        )

    def ensure_official_source_boa(self) -> dict[str, Any]:
        return self.upsert_official_source(
            code="BOA",
            name="Boletín Oficial de Aragón",
            jurisdiction="autonomous",
            region_code="ES-AR",
            base_url="https://www.boa.aragon.es",
            access_type="official_json",
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
        source_code: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        values: list[Any] = []
        if source_code:
            clauses.append("s.code = ?")
            values.append(source_code)
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

    def list_documents_by_ids(self, document_ids: list[int]) -> list[dict[str, Any]]:
        if not document_ids:
            return []
        placeholders = ",".join("?" for _ in document_ids)
        rows = self.connection.execute(
            f"""
            SELECT d.*, s.code AS source_code
            FROM official_documents d
            JOIN official_sources s ON s.id = d.source_id
            WHERE d.id IN ({placeholders})
            ORDER BY d.publication_date DESC, d.external_id ASC
            """,
            document_ids,
        ).fetchall()
        return [dict(row) for row in rows]

    def upsert_bdns_catalog_entry(
        self,
        *,
        catalog_name: str,
        code: str,
        name: str,
        source_url: str,
        raw_metadata: dict[str, Any],
        source_snapshot_hash: str,
        ingestion_run_id: int | None = None,
    ) -> dict[str, Any]:
        now = utc_now()
        external_id = f"BDNS:catalog:{catalog_name}:{code}"
        raw_metadata_json = json.dumps(raw_metadata, sort_keys=True)
        content_hash = sha256_text(
            json.dumps(
                {
                    "catalog_name": catalog_name,
                    "code": code,
                    "name": name,
                    "raw_metadata": raw_metadata,
                },
                sort_keys=True,
            )
        )
        existing = self.get_bdns_catalog_entry(catalog_name, code)
        if existing is None:
            self.connection.execute(
                """
                INSERT INTO bdns_catalog_entries (
                    catalog_name, code, external_id, name, source_url, raw_metadata_json,
                    source_snapshot_hash, content_hash, first_seen_at, last_seen_at,
                    created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    catalog_name,
                    code,
                    external_id,
                    name,
                    source_url,
                    raw_metadata_json,
                    source_snapshot_hash,
                    content_hash,
                    now,
                    now,
                    now,
                    now,
                ),
            )
        else:
            changed = existing["content_hash"] != content_hash
            previous_hash = existing["content_hash"] if changed else existing["previous_hash"]
            content_changed_at = now if changed else existing["content_changed_at"]
            change_detected_by = ingestion_run_id if changed else existing["change_detected_by"]
            self.connection.execute(
                """
                UPDATE bdns_catalog_entries
                SET external_id = ?, name = ?, source_url = ?, raw_metadata_json = ?,
                    source_snapshot_hash = ?, content_hash = ?, previous_hash = ?,
                    last_seen_at = ?, content_changed_at = ?, change_detected_by = ?,
                    updated_at = ?
                WHERE catalog_name = ? AND code = ?
                """,
                (
                    external_id,
                    name,
                    source_url,
                    raw_metadata_json,
                    source_snapshot_hash,
                    content_hash,
                    previous_hash,
                    now,
                    content_changed_at,
                    change_detected_by,
                    now,
                    catalog_name,
                    code,
                ),
            )
        self.connection.commit()
        entry = self.get_bdns_catalog_entry(catalog_name, code)
        assert entry is not None
        return entry

    def get_bdns_catalog_entry(self, catalog_name: str, code: str) -> dict[str, Any] | None:
        return row_to_dict(
            self.connection.execute(
                """
                SELECT * FROM bdns_catalog_entries
                WHERE catalog_name = ? AND code = ?
                """,
                (catalog_name, code),
            ).fetchone()
        )

    def list_bdns_catalog_entries(
        self,
        *,
        catalog_name: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        values: list[Any] = []
        if catalog_name is not None:
            clauses.append("catalog_name = ?")
            values.append(catalog_name)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        limit_clause = ""
        if limit is not None:
            limit_clause = "LIMIT ?"
            values.append(limit)
        rows = self.connection.execute(
            f"""
            SELECT * FROM bdns_catalog_entries
            {where}
            ORDER BY catalog_name ASC, code ASC
            {limit_clause}
            """,
            values,
        ).fetchall()
        return [dict(row) for row in rows]

    def upsert_bdns_concession_entry(
        self,
        *,
        concession_code: str,
        external_id: str,
        call_identifier: str | None,
        source_url: str,
        source_snapshot_hash: str,
        raw_metadata: dict[str, Any],
        ingestion_run_id: int | None = None,
    ) -> dict[str, Any]:
        now = utc_now()
        raw_metadata_json = json.dumps(raw_metadata, sort_keys=True)
        content_hash = sha256_text(
            json.dumps(
                {
                    "concession_code": concession_code,
                    "external_id": external_id,
                    "call_identifier": call_identifier,
                    "raw_metadata": raw_metadata,
                },
                sort_keys=True,
            )
        )
        values = {
            "call_code": raw_metadata.get("bdns_call_code"),
            "call_internal_id": raw_metadata.get("bdns_call_internal_id"),
            "concession_date": raw_metadata.get("concession_date"),
            "registration_date": raw_metadata.get("registration_date"),
            "amount": raw_metadata.get("amount"),
            "aid_equivalent": raw_metadata.get("aid_equivalent"),
            "instrument": raw_metadata.get("instrument"),
            "department": raw_metadata.get("department"),
            "section": raw_metadata.get("section"),
            "beneficiary_name": raw_metadata.get("beneficiary_name"),
            "beneficiary_person_id": raw_metadata.get("beneficiary_person_id"),
            "base_regulation_url": raw_metadata.get("base_regulation_url"),
        }
        existing = self.get_bdns_concession_entry(concession_code)
        if existing is None:
            self.connection.execute(
                """
                INSERT INTO bdns_concession_entries (
                    concession_code, external_id, call_identifier, call_code,
                    call_internal_id, concession_date, registration_date, amount,
                    aid_equivalent, instrument, department, section, beneficiary_name,
                    beneficiary_person_id, base_regulation_url, raw_metadata_json,
                    source_url, source_snapshot_hash, content_hash, first_seen_at,
                    last_seen_at, created_at, updated_at
                )
                VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
                """,
                (
                    concession_code,
                    external_id,
                    call_identifier,
                    values["call_code"],
                    values["call_internal_id"],
                    values["concession_date"],
                    values["registration_date"],
                    values["amount"],
                    values["aid_equivalent"],
                    values["instrument"],
                    values["department"],
                    values["section"],
                    values["beneficiary_name"],
                    values["beneficiary_person_id"],
                    values["base_regulation_url"],
                    raw_metadata_json,
                    source_url,
                    source_snapshot_hash,
                    content_hash,
                    now,
                    now,
                    now,
                    now,
                ),
            )
        else:
            changed = existing["content_hash"] != content_hash
            previous_hash = existing["content_hash"] if changed else existing["previous_hash"]
            content_changed_at = now if changed else existing["content_changed_at"]
            change_detected_by = ingestion_run_id if changed else existing["change_detected_by"]
            self.connection.execute(
                """
                UPDATE bdns_concession_entries
                SET external_id = ?, call_identifier = ?, call_code = ?,
                    call_internal_id = ?, concession_date = ?, registration_date = ?,
                    amount = ?, aid_equivalent = ?, instrument = ?, department = ?,
                    section = ?, beneficiary_name = ?, beneficiary_person_id = ?,
                    base_regulation_url = ?, raw_metadata_json = ?, source_url = ?,
                    source_snapshot_hash = ?, content_hash = ?, previous_hash = ?,
                    last_seen_at = ?, content_changed_at = ?, change_detected_by = ?,
                    updated_at = ?
                WHERE concession_code = ?
                """,
                (
                    external_id,
                    call_identifier,
                    values["call_code"],
                    values["call_internal_id"],
                    values["concession_date"],
                    values["registration_date"],
                    values["amount"],
                    values["aid_equivalent"],
                    values["instrument"],
                    values["department"],
                    values["section"],
                    values["beneficiary_name"],
                    values["beneficiary_person_id"],
                    values["base_regulation_url"],
                    raw_metadata_json,
                    source_url,
                    source_snapshot_hash,
                    content_hash,
                    previous_hash,
                    now,
                    content_changed_at,
                    change_detected_by,
                    now,
                    concession_code,
                ),
            )
        self.connection.commit()
        entry = self.get_bdns_concession_entry(concession_code)
        assert entry is not None
        return entry

    def get_bdns_concession_entry(self, concession_code: str) -> dict[str, Any] | None:
        return row_to_dict(
            self.connection.execute(
                """
                SELECT * FROM bdns_concession_entries
                WHERE concession_code = ?
                """,
                (concession_code,),
            ).fetchone()
        )

    def list_bdns_concession_entries(
        self,
        *,
        call_identifier: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        values: list[Any] = []
        if call_identifier is not None:
            clauses.append("call_identifier = ?")
            values.append(call_identifier)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        limit_clause = ""
        if limit is not None:
            limit_clause = "LIMIT ?"
            values.append(limit)
        rows = self.connection.execute(
            f"""
            SELECT * FROM bdns_concession_entries
            {where}
            ORDER BY concession_date DESC, concession_code ASC
            {limit_clause}
            """,
            values,
        ).fetchall()
        return [dict(row) for row in rows]

    def list_bdns_grant_call_documents(self, *, limit: int | None = None) -> list[dict[str, Any]]:
        values: list[Any] = []
        limit_clause = ""
        if limit is not None:
            limit_clause = "LIMIT ?"
            values.append(limit)
        rows = self.connection.execute(
            f"""
            SELECT d.*, s.code AS source_code
            FROM official_documents d
            JOIN official_sources s ON s.id = d.source_id
            WHERE s.code = 'BDNS'
              AND d.document_type = 'grant_call'
            ORDER BY d.publication_date DESC, d.external_id ASC
            {limit_clause}
            """,
            values,
        ).fetchall()
        return [dict(row) for row in rows]

    def list_documents_by_candidate_ids(self, candidate_ids: list[int]) -> list[dict[str, Any]]:
        if not candidate_ids:
            return []
        placeholders = ",".join("?" for _ in candidate_ids)
        rows = self.connection.execute(
            f"""
            SELECT d.*, s.code AS source_code, c.id AS source_candidate_id
            FROM source_candidates c
            JOIN official_documents d ON d.id = c.document_id
            JOIN official_sources s ON s.id = d.source_id
            WHERE c.id IN ({placeholders})
            ORDER BY c.id ASC
            """,
            candidate_ids,
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

    def source_candidate_exists(self, *, document_id: int, project_key: str) -> bool:
        row = self.connection.execute(
            """
            SELECT 1 FROM source_candidates
            WHERE document_id = ? AND project_key = ?
            LIMIT 1
            """,
            (document_id, project_key),
        ).fetchone()
        return row is not None

    def get_source_candidate(self, source_candidate_id: int) -> dict[str, Any] | None:
        return row_to_dict(
            self.connection.execute(
                "SELECT * FROM source_candidates WHERE id = ?",
                (source_candidate_id,),
            ).fetchone()
        )

    def mark_candidate_evidence_review(
        self,
        *,
        source_candidate_id: int,
        evidence_label: str | None = None,
        evidence_review_status: str = "not_reviewed",
        evidence_notes: str | None = None,
        selected_for_evidence: bool | None = None,
        selected_for_pdf: bool | None = None,
        manual_decision: str | None = None,
        manual_notes: str | None = None,
        needs_pdf: str | None = None,
        downstream_project_fit: str | None = None,
        reviewed_by: str | None = None,
        reviewed_at: str | None = None,
    ) -> dict[str, Any]:
        if evidence_review_status not in EVIDENCE_REVIEW_STATUSES:
            raise ValueError(f"Unsupported evidence review status: {evidence_review_status}")
        if evidence_label is not None and evidence_label not in EVIDENCE_LABELS:
            raise ValueError(f"Unsupported evidence label: {evidence_label}")
        if manual_decision is not None and manual_decision not in MANUAL_DECISIONS:
            raise ValueError(f"Unsupported manual decision: {manual_decision}")
        if needs_pdf is not None and needs_pdf not in NEEDS_PDF_VALUES:
            raise ValueError(f"Unsupported needs PDF value: {needs_pdf}")
        if (
            downstream_project_fit is not None
            and downstream_project_fit not in DOWNSTREAM_PROJECT_FITS
        ):
            raise ValueError(f"Unsupported downstream project fit: {downstream_project_fit}")
        candidate = self.get_source_candidate(source_candidate_id)
        if candidate is None:
            raise KeyError(f"Unknown source candidate: {source_candidate_id}")
        availability = self._candidate_artifact_availability(candidate["document_id"])
        existing = row_to_dict(
            self.connection.execute(
                """
                SELECT * FROM candidate_evidence_reviews
                WHERE source_candidate_id = ?
                """,
                (source_candidate_id,),
            ).fetchone()
        )
        now = utc_now()
        review_timestamp = reviewed_at or now
        if existing is None:
            selected_evidence_value = (
                evidence_review_status in EVIDENCE_SELECTED_STATUSES
                if selected_for_evidence is None
                else selected_for_evidence
            )
            selected_pdf_value = False if selected_for_pdf is None else selected_for_pdf
            if needs_pdf == "yes":
                selected_pdf_value = True
            self.connection.execute(
                """
                INSERT INTO candidate_evidence_reviews (
                    source_candidate_id, evidence_review_status, evidence_label,
                    evidence_notes, selected_for_evidence, selected_for_pdf,
                    xml_available, html_available, pdf_available, integrity_warning,
                    manual_decision, manual_notes, needs_pdf, downstream_project_fit,
                    reviewed_by, reviewed_at, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    source_candidate_id,
                    evidence_review_status,
                    evidence_label,
                    evidence_notes,
                    1 if selected_evidence_value else 0,
                    1 if selected_pdf_value else 0,
                    1 if availability["xml_available"] else 0,
                    1 if availability["html_available"] else 0,
                    1 if availability["pdf_available"] else 0,
                    1 if availability["integrity_warning"] else 0,
                    manual_decision,
                    manual_notes,
                    needs_pdf,
                    downstream_project_fit,
                    reviewed_by,
                    review_timestamp,
                    now,
                    now,
                ),
            )
        else:
            selected_evidence_value = (
                bool(existing["selected_for_evidence"])
                if selected_for_evidence is None
                else selected_for_evidence
            )
            if (
                selected_for_evidence is None
                and evidence_review_status in EVIDENCE_SELECTED_STATUSES
            ):
                selected_evidence_value = True
            selected_pdf_value = (
                bool(existing["selected_for_pdf"]) if selected_for_pdf is None else selected_for_pdf
            )
            if needs_pdf == "yes":
                selected_pdf_value = True
            elif needs_pdf == "no" and selected_for_pdf is None:
                selected_pdf_value = False
            self.connection.execute(
                """
                UPDATE candidate_evidence_reviews
                SET evidence_review_status = ?,
                    evidence_label = ?,
                    evidence_notes = ?,
                    selected_for_evidence = ?,
                    selected_for_pdf = ?,
                    xml_available = ?,
                    html_available = ?,
                    pdf_available = ?,
                    integrity_warning = ?,
                    manual_decision = ?,
                    manual_notes = ?,
                    needs_pdf = ?,
                    downstream_project_fit = ?,
                    reviewed_by = ?,
                    reviewed_at = ?,
                    updated_at = ?
                WHERE source_candidate_id = ?
                """,
                (
                    evidence_review_status,
                    evidence_label if evidence_label is not None else existing["evidence_label"],
                    (evidence_notes if evidence_notes is not None else existing["evidence_notes"]),
                    1 if selected_evidence_value else 0,
                    1 if selected_pdf_value else 0,
                    1 if availability["xml_available"] else 0,
                    1 if availability["html_available"] else 0,
                    1 if availability["pdf_available"] else 0,
                    1 if availability["integrity_warning"] else 0,
                    (
                        manual_decision
                        if manual_decision is not None
                        else existing["manual_decision"]
                    ),
                    manual_notes if manual_notes is not None else existing["manual_notes"],
                    needs_pdf if needs_pdf is not None else existing["needs_pdf"],
                    (
                        downstream_project_fit
                        if downstream_project_fit is not None
                        else existing["downstream_project_fit"]
                    ),
                    reviewed_by if reviewed_by is not None else existing["reviewed_by"],
                    review_timestamp,
                    now,
                    source_candidate_id,
                ),
            )
        self.connection.commit()
        result = row_to_dict(
            self.connection.execute(
                """
                SELECT * FROM candidate_evidence_reviews
                WHERE source_candidate_id = ?
                """,
                (source_candidate_id,),
            ).fetchone()
        )
        assert result is not None
        return result

    def list_candidate_evidence_status(
        self,
        *,
        candidate_ids: list[int] | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        project_key: str | None = None,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        values: list[Any] = []
        if candidate_ids is not None:
            if not candidate_ids:
                return []
            placeholders = ",".join("?" for _ in candidate_ids)
            clauses.append(f"c.id IN ({placeholders})")
            values.extend(candidate_ids)
        if date_from is not None:
            clauses.append("d.publication_date >= ?")
            values.append(date_from)
        if date_to is not None:
            clauses.append("d.publication_date <= ?")
            values.append(date_to)
        if project_key is not None:
            clauses.append("c.project_key = ?")
            values.append(project_key)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = self.connection.execute(
            f"""
            SELECT
                c.id AS candidate_id,
                d.external_id AS official_identifier,
                d.title AS title,
                c.review_status AS review_status,
                COALESCE(r.evidence_review_status, 'not_reviewed')
                    AS evidence_review_status,
                r.evidence_label AS evidence_label,
                r.manual_decision AS manual_decision,
                r.manual_notes AS manual_notes,
                r.needs_pdf AS needs_pdf,
                r.downstream_project_fit AS downstream_project_fit,
                r.reviewed_by AS reviewed_by,
                r.reviewed_at AS reviewed_at,
                COALESCE(r.selected_for_evidence, 0) AS selected_for_evidence,
                COALESCE(r.selected_for_pdf, 0) AS selected_for_pdf,
                CASE WHEN EXISTS (
                    SELECT 1 FROM document_files f
                    WHERE f.document_id = d.id AND f.file_type = 'xml'
                ) THEN 1 ELSE 0 END AS xml_available,
                CASE WHEN EXISTS (
                    SELECT 1 FROM document_files f
                    WHERE f.document_id = d.id AND f.file_type = 'html'
                ) THEN 1 ELSE 0 END AS html_available,
                CASE WHEN EXISTS (
                    SELECT 1 FROM document_files f
                    WHERE f.document_id = d.id AND f.file_type = 'pdf'
                ) THEN 1 ELSE 0 END AS pdf_available,
                CASE WHEN COALESCE(r.integrity_warning, 0) = 1 OR EXISTS (
                    SELECT 1 FROM document_files f
                    WHERE f.document_id = d.id AND f.content_changed_at IS NOT NULL
                ) THEN 1 ELSE 0 END AS integrity_warning,
                COALESCE(
                    d.url_html,
                    d.url_xml,
                    d.url_pdf,
                    'https://www.boe.es/buscar/doc.php?id=' || d.external_id
                ) AS official_url
            FROM source_candidates c
            JOIN official_documents d ON d.id = c.document_id
            LEFT JOIN candidate_evidence_reviews r ON r.source_candidate_id = c.id
            {where}
            ORDER BY c.id ASC
            """,
            values,
        ).fetchall()
        return [dict(row) for row in rows]

    def get_candidate_evidence_object(self, source_candidate_id: int) -> dict[str, Any]:
        rows = self.list_candidate_evidence_status(candidate_ids=[source_candidate_id])
        if not rows:
            raise KeyError(f"Unknown source candidate: {source_candidate_id}")
        row = rows[0]
        return {
            "candidate": {
                "candidate_id": row["candidate_id"],
                "review_status": row["review_status"],
                "evidence_review_status": row["evidence_review_status"],
                "evidence_label": row["evidence_label"],
            },
            "evidence": {
                "xml_available": bool(row["xml_available"]),
                "html_available": bool(row["html_available"]),
                "pdf_available": bool(row["pdf_available"]),
                "pdf_policy": "on_demand",
                "integrity_warning": bool(row["integrity_warning"]),
            },
        }

    def _candidate_artifact_availability(self, document_id: int) -> dict[str, bool]:
        files = self.list_document_files(document_id)
        return {
            "xml_available": any(file_record["file_type"] == "xml" for file_record in files),
            "html_available": any(file_record["file_type"] == "html" for file_record in files),
            "pdf_available": any(file_record["file_type"] == "pdf" for file_record in files),
            "integrity_warning": any(file_record["content_changed_at"] for file_record in files),
        }

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

    def get_latest_summary_ingestion_run(
        self, source_code: str, target_date: str
    ) -> dict[str, Any] | None:
        return row_to_dict(
            self.connection.execute(
                """
                SELECT * FROM ingestion_runs
                WHERE source_code = ? AND target_date = ? AND (
                    last_http_status IS NOT NULL
                    OR (
                        status = 'failed'
                        AND (
                            error_message IS NULL
                            OR error_message != 'artifact download failures'
                        )
                    )
                )
                ORDER BY id DESC
                LIMIT 1
                """,
                (source_code, target_date),
            ).fetchone()
        )

    def summarize_artifact_download_attempts_by_date(self, target_date: str) -> dict[str, Any]:
        rows = self.connection.execute(
            """
            SELECT
                a.file_type,
                a.http_status,
                COUNT(*) AS count,
                SUM(a.retry_count) AS retry_count,
                SUM(CASE WHEN a.throttle_triggered = 1 THEN 1 ELSE 0 END) AS throttle_events
            FROM artifact_download_attempts a
            JOIN official_documents d ON d.id = a.document_id
            WHERE d.publication_date = ?
            GROUP BY a.file_type, a.http_status
            ORDER BY a.file_type ASC, a.http_status ASC
            """,
            (target_date,),
        ).fetchall()
        grouped_parts: dict[str, list[str]] = {}
        retry_count = 0
        throttle_events = 0
        for row in rows:
            status = "none" if row["http_status"] is None else row["http_status"]
            grouped_parts.setdefault(row["file_type"], []).append(
                f"{row['file_type']}:{status}:{row['count']}"
            )
            retry_count += int(row["retry_count"] or 0)
            throttle_events += int(row["throttle_events"] or 0)
        status_parts = []
        for file_type in ("xml", "html", "pdf"):
            status_parts.extend(grouped_parts.pop(file_type, []))
        for file_type in sorted(grouped_parts):
            status_parts.extend(grouped_parts[file_type])
        return {
            "http_status_summary": ",".join(status_parts) if status_parts else "none",
            "retry_count": retry_count,
            "throttle_events": throttle_events,
        }
