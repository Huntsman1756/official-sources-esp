from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import unicodedata
from collections import Counter
from datetime import date, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any, TextIO

import httpx

from official_sources.api_monitor import (
    APIMonitorError,
    build_api_monitor_output_path,
    monitor_api_source_code,
    write_api_jsonl,
)
from official_sources.downstream_export import export_downstream_evidence_files
from official_sources.hermes_drift_audit import (
    HermesDriftAuditError,
    collect_local_observation,
    default_release_contract_path,
    evaluate_hermes_drift,
    load_audit_contract,
    load_release_contract,
    merge_release_contract,
    render_markdown_report,
    require_external_release_contract,
)
from official_sources.hermes_freshness_report import (
    HermesFreshnessReportError,
    evaluate_freshness,
    load_observation,
    load_observation_jsonl,
    load_runtime_observation,
    parse_timestamp,
)
from official_sources.hermes_freshness_observation_producer import (
    HermesFreshnessObservationProducerError,
    collect_freshness_observations,
    write_observations_jsonl,
)
from official_sources.hermes_freshness_report import (
    render_markdown_report as render_freshness_markdown_report,
)
from official_sources.hermes_scheduled_freshness_report import (
    DEFAULT_CRITICAL_SOURCES,
    DEFAULT_EXPECTED_SOURCES,
    run_scheduled_freshness_report,
)
from official_sources.hermes_scheduled_audit import run_scheduled_strict_audit
from official_sources.html_monitor import (
    HTMLMonitorError,
    build_html_monitor_output_path,
    monitor_html_source_code,
    write_html_jsonl,
)
from official_sources.integrity.hashing import sha256_bytes
from official_sources.rss_monitor import (
    RSSMonitorError,
    build_rss_monitor_output_path,
    monitor_source_code,
    write_jsonl,
)
from official_sources.source_registry import SourceRegistryError, get_source, list_sources
from official_sources.sources.bdns.business import filter_bdns_business_grants
from official_sources.sources.bdns.client import (
    BDNS_DEFAULT_PAGE_SIZE,
    build_bdns_catalog_url,
    build_bdns_concessions_search_url,
    parse_bdns_date_filter,
    validate_bdns_catalog_name,
    validate_bdns_limit,
    validate_bdns_max_pages,
    validate_bdns_num_conv,
)
from official_sources.sources.bdns.ingestion import (
    ingest_bdns_call,
    ingest_bdns_catalog,
    ingest_bdns_concessions,
    ingest_bdns_latest,
    preview_bdns_catalog,
    preview_bdns_concessions,
    search_bdns_calls,
)
from official_sources.sources.boa.client import validate_boa_date
from official_sources.sources.boa.ingestion import ingest_boa_date
from official_sources.sources.bocm.client import validate_bocm_date
from official_sources.sources.bocm.ingestion import ingest_bocm_date
from official_sources.sources.bocyl.artifacts import BOCYL_ARTIFACT_FIELDS, BOCYLArtifactDownloader
from official_sources.sources.bocyl.client import validate_bocyl_date
from official_sources.sources.bocyl.ingestion import ingest_bocyl_date
from official_sources.sources.boe.artifacts import (
    BOE_ARTIFACT_FIELDS,
    BOEArtifactDownloader,
    BOEArtifactDownloadError,
)
from official_sources.sources.boe.client import BOEClient, validate_boe_date
from official_sources.sources.boe.consolidated import (
    BOEConsolidatedClient,
    BOEConsolidatedService,
    validate_consolidated_block_id,
    validate_consolidated_identifier,
)
from official_sources.sources.boe.http_policy import BOERequestPolicy
from official_sources.sources.boe.ingestion import NO_PUBLICATION_STATUS, ingest_boe_summary
from official_sources.sources.boja.artifacts import BOJA_ARTIFACT_FIELDS, BOJAArtifactDownloader
from official_sources.sources.boja.client import validate_boja_date
from official_sources.sources.boja.enrichment import enrich_boja_evidence_urls
from official_sources.sources.boja.ingestion import ingest_boja_date
from official_sources.sources.bopv.client import validate_bopv_date
from official_sources.sources.bopv.ingestion import ingest_bopv_date
from official_sources.sources.borm.artifacts import BORM_ARTIFACT_FIELDS, BORMArtifactDownloader
from official_sources.sources.borm.client import validate_borm_date
from official_sources.sources.borm.ingestion import ingest_borm_date
from official_sources.sources.dogc.client import validate_dogc_date
from official_sources.sources.dogc.ingestion import ingest_dogc_date
from official_sources.sources.dogv.artifacts import DOGV_ARTIFACT_FIELDS, DOGVArtifactDownloader
from official_sources.sources.dogv.client import validate_dogv_date
from official_sources.sources.dogv.ingestion import ingest_dogv_date
from official_sources.sources.placsp.client import (
    PLACSP_DEFAULT_LIMIT,
    build_placsp_feed_url,
    validate_placsp_feed_type,
    validate_placsp_limit,
)
from official_sources.sources.placsp.ingestion import ingest_placsp_feed, preview_placsp_feed
from official_sources.storage.backup import SQLiteBackupError, backup_sqlite_database
from official_sources.storage.database import connect, initialize_database, sqlite_runtime_pragmas
from official_sources.storage.migrations.runner import (
    MigrationChecksumError,
    MigrationRunner,
    validate_database,
)
from official_sources.storage.repository import (
    DOWNSTREAM_PROJECT_FITS,
    EVIDENCE_LABELS,
    EVIDENCE_REVIEW_STATUSES,
    MANUAL_DECISIONS,
    NEEDS_PDF_VALUES,
    OfficialSourcesRepository,
)

SOURCE_CANDIDATE_SOURCE_CODES = (
    "BOE",
    "BOJA",
    "DOGV",
    "BOCM",
    "BOCYL",
    "BDNS",
    "BOPV",
    "BOA",
    "BORM",
    "DOGC",
)
SOURCE_CANDIDATE_PROFILES = (
    "la-ayuda",
    "boja-ayudas",
    "dogv-ayudas",
    "bocyl-ayudas",
    "bopv-ayudas",
    "boa-ayudas",
    "borm-ayudas",
    "dogc-ayudas",
)
OPPOSITION_ALERT_SOURCE_CODES = (
    "BOE",
    "BOJA",
    "DOGV",
    "BOCYL",
    "BOPV",
    "BORM",
    "BOA",
    "DOGC",
)
OPPOSITION_ALERT_TYPES = (
    "convocatoria",
    "bolsa",
    "bases",
    "lista_provisional",
    "lista_definitiva",
    "tribunal",
    "fecha_examen",
    "plazo",
    "subsanacion",
    "correccion",
    "nombramiento",
    "adjudicacion",
    "other",
)

LA_AYUDA_PROFILE_KEYWORDS = [
    "beca",
    "becas",
    "ayuda",
    "ayudas",
    "subvención",
    "subvenciones",
    "bases reguladoras",
    "convocatoria",
    "convocatoria de ayudas",
    "convocatoria de subvenciones",
    "ayudas al estudio",
    "becas de carácter general",
    "estudiantes",
    "alquiler",
    "bono",
    "bono alquiler",
    "bono social",
    "familia numerosa",
    "discapacidad",
    "transporte",
    "vivienda",
]
BOJA_AYUDAS_PROFILE_KEYWORDS = [
    "beca",
    "becas",
    "ayuda",
    "ayudas",
    "subvenciones",
    "bases reguladoras",
    "convocatoria",
    "convocatoria de ayudas",
    "convocatoria de subvenciones",
    "ayudas al estudio",
    "subvenciones para alumnado",
    "ayudas para alumnado",
    "ayudas para estudiantes",
    "alumnado",
    "estudiantes",
    "necesidades especificas",
    "material escolar",
    "libros de texto",
    "transporte escolar",
    "comedor escolar",
    "discapacidad",
    "vivienda",
    "alquiler",
    "joven",
    "jovenes",
]
DOGV_AYUDAS_PROFILE_KEYWORDS = [
    "beca",
    "becas",
    "ayuda",
    "ayudas",
    "subvencion",
    "subvenciones",
    "bases reguladoras",
    "convocatoria",
    "convocatoria de ayudas",
    "convocatoria de subvenciones",
    "ayudas al estudio",
    "ayudas para alumnado",
    "ayudas para estudiantes",
    "alumnado",
    "estudiantes",
    "comedor escolar",
    "transporte escolar",
    "libros de texto",
    "material escolar",
    "necesidades educativas",
    "formacion profesional",
    "universidad",
    "universidades",
    "familias",
    "joven",
    "jovenes",
    "vivienda",
    "alquiler",
    "empleo",
    "formacion",
    "discapacidad",
]
BOCYL_AYUDAS_PROFILE_KEYWORDS = [
    "beca",
    "becas",
    "ayuda",
    "ayudas",
    "subvencion",
    "subvenciones",
    "bases reguladoras",
    "convocatoria",
    "convocatoria de ayudas",
    "convocatoria de subvenciones",
    "ayudas al estudio",
    "ayudas para alumnado",
    "ayudas para estudiantes",
    "ayudas directas a personas",
    "alumnado",
    "estudiantes",
    "comedor escolar",
    "transporte escolar",
    "libros de texto",
    "material escolar",
    "necesidades educativas",
    "formacion profesional",
    "universidad",
    "universidades",
    "ayudas para familias",
    "familia numerosa",
    "familias numerosas",
    "joven",
    "jovenes",
    "vivienda",
    "alquiler",
    "bono alquiler",
    "bono alquiler joven",
    "empleo",
    "formacion",
    "discapacidad",
]
AUTONOMOUS_AYUDAS_PROFILE_KEYWORDS = [
    "beca",
    "becas",
    "ayuda",
    "ayudas",
    "subvencion",
    "subvenciones",
    "bases reguladoras",
    "convocatoria",
    "convocatoria de ayudas",
    "convocatoria de subvenciones",
    "ayudas al estudio",
    "ayudas para alumnado",
    "ayudas para estudiantes",
    "ayudas directas a personas",
    "alumnado",
    "estudiantes",
    "comedor escolar",
    "transporte escolar",
    "libros de texto",
    "material escolar",
    "necesidades educativas",
    "formacion profesional",
    "universidad",
    "universidades",
    "ayudas para familias",
    "familias",
    "joven",
    "jovenes",
    "alquiler joven",
    "bono alquiler",
    "bono alquiler joven",
    "vivienda",
    "alquiler",
    "empleo",
    "formacion",
    "discapacidad",
]
BOPV_AYUDAS_PROFILE_KEYWORDS = [
    *AUTONOMOUS_AYUDAS_PROFILE_KEYWORDS,
    "beka",
    "bekak",
    "ikasle",
    "ikasleak",
    "laguntza",
    "laguntzak",
    "dirulaguntza",
    "dirulaguntzak",
    "unibertsitate",
    "gazte",
    "gazteak",
]
DOGC_AYUDAS_PROFILE_KEYWORDS = [
    *AUTONOMOUS_AYUDAS_PROFILE_KEYWORDS,
    "ajut",
    "ajuts",
    "beca",
    "beques",
    "alumnat",
    "estudiants",
    "families",
    "joves",
    "lloguer jove",
    "bo lloguer jove",
    "transport escolar",
    "menjador escolar",
]
LA_AYUDA_DEFAULT_EXCLUDED_SECTIONS = ["V-A"]
GENERIC_WEAK_KEYWORDS = {"convocatoria", "transporte"}
BOJA_GENERIC_WEAK_KEYWORDS = {
    "ayuda",
    "ayudas",
    "subvenciones",
    "bases reguladoras",
    "convocatoria",
    "vivienda",
    "alquiler",
}
BOJA_HIGH_INTENT_KEYWORDS = {
    "beca",
    "becas",
    "ayudas al estudio",
    "subvenciones para alumnado",
    "ayudas para alumnado",
    "ayudas para estudiantes",
    "alumnado",
    "estudiantes",
    "necesidades especificas",
    "material escolar",
    "libros de texto",
    "transporte escolar",
    "comedor escolar",
    "discapacidad",
    "joven",
    "jovenes",
}
BOJA_EDUCATION_DEPARTMENT_TERMS = {
    "desarrollo educativo",
    "formacion profesional",
    "universidad",
    "universidades",
}
BOJA_NOISE_DEPARTMENT_TERMS = {
    "ayuntamientos",
    "agricultura",
    "pesca",
    "agua",
    "industria",
    "energia",
    "minas",
    "infraestructuras",
    "fomento",
    "vivienda",
    "turismo",
    "cultura",
    "deporte",
    "empresas publicas",
}
BOJA_NOISE_TEXT_TERMS = {
    "licitacion",
    "contratacion",
    "concesion administrativa",
    "expropiacion",
    "urbanismo",
    "cooperativas",
    "asociaciones empresariales",
    "entidades locales",
    "diputaciones",
}
DOGV_GENERIC_WEAK_KEYWORDS = {
    "ayuda",
    "ayudas",
    "subvencion",
    "subvenciones",
    "bases reguladoras",
    "convocatoria",
    "convocatoria de ayudas",
    "convocatoria de subvenciones",
    "vivienda",
    "empleo",
    "formacion",
    "alquiler",
}
DOGV_HIGH_INTENT_KEYWORDS = {
    "beca",
    "becas",
    "ayudas al estudio",
    "ayudas para alumnado",
    "ayudas para estudiantes",
    "alumnado",
    "estudiantes",
    "comedor escolar",
    "transporte escolar",
    "libros de texto",
    "material escolar",
    "necesidades educativas",
    "formacion profesional",
    "universidad",
    "universidades",
    "familias",
    "joven",
    "jovenes",
    "discapacidad",
}
DOGV_DIRECT_TITLE_TERMS = {
    "ayudas al estudio",
    "ayudas para alumnado",
    "ayudas para estudiantes",
    "alumnado",
    "estudiantes",
    "comedor escolar",
    "transporte escolar",
    "libros de texto",
    "material escolar",
    "necesidades educativas",
    "familias",
    "joven",
    "jovenes",
    "discapacidad",
    "beca",
    "becas",
}
DOGV_NOISE_SECTION_TERMS = {
    "autoridades y personal",
    "ofertas de empleo publico",
    "oposiciones y concursos",
    "nombramientos y ceses",
}
DOGV_PUBLIC_EMPLOYMENT_TERMS = {
    "oposicion",
    "oposiciones",
    "bolsa de empleo",
    "bolsas de empleo",
    "pruebas selectivas",
    "lista provisional",
    "listas provisionales",
    "lista definitiva",
    "listas definitivas",
    "relacion provisional",
    "relacion definitiva",
    "tribunal",
    "tribunales",
    "nombramiento",
    "nombramientos",
    "cese",
    "ceses",
}
DOGV_CLOSED_OR_RESULT_TERMS = {
    "concesion",
    "concedidas",
    "personas beneficiarias",
    "empresas beneficiarias",
    "entidades beneficiarias",
    "resolucion de concesion",
    "relacion de beneficiarios",
    "relacion de personas beneficiarias",
}
DOGV_AWARD_OR_PROCEDURE_TERMS = {
    "premio",
    "premios",
    "concurso",
    "certamen",
    "admision",
    "matricula",
    "pruebas de acceso",
    "instrucciones",
    "procedimiento de admision",
    "convenio",
    "colaboracion",
    "transferencia de credito",
    "generacion de credito",
    "ampliacion de credito",
}
DOGV_LOCAL_ENTITY_TERMS = {
    "entidades locales",
    "entidad local",
    "ayuntamiento",
    "ayuntamientos",
    "municipio",
    "municipios",
    "diputacion",
    "diputaciones",
    "administracion local",
}
DOGV_SECTOR_COMPANY_TERMS = {
    "empresa",
    "empresas",
    "sector agrario",
    "agraria",
    "agricultura",
    "ganaderia",
    "pesca",
    "vinedo",
    "vina",
    "vitivinicola",
    "industria",
    "industrial",
    "energia",
    "infraestructuras",
    "competitividad empresarial",
    "turismo",
    "comercio",
}
DOGV_PROCUREMENT_TERMS = {
    "contratacion",
    "licitacion",
}
BOCYL_GENERIC_WEAK_KEYWORDS = {
    "ayuda",
    "ayudas",
    "subvencion",
    "subvenciones",
    "bases reguladoras",
    "convocatoria",
    "convocatoria de ayudas",
    "convocatoria de subvenciones",
    "vivienda",
    "empleo",
    "formacion",
    "alquiler",
}
BOCYL_HIGH_INTENT_KEYWORDS = {
    "beca",
    "becas",
    "ayudas al estudio",
    "ayudas para alumnado",
    "ayudas para estudiantes",
    "ayudas directas a personas",
    "alumnado",
    "estudiantes",
    "comedor escolar",
    "transporte escolar",
    "libros de texto",
    "material escolar",
    "necesidades educativas",
    "formacion profesional",
    "universidad",
    "universidades",
    "ayudas para familias",
    "familia numerosa",
    "familias numerosas",
    "joven",
    "jovenes",
    "bono alquiler",
    "bono alquiler joven",
    "discapacidad",
}
BOCYL_DIRECT_TITLE_TERMS = {
    "beca",
    "becas",
    "ayudas al estudio",
    "ayudas para alumnado",
    "ayudas para estudiantes",
    "ayudas directas a personas",
    "alumnado",
    "estudiantes",
    "comedor escolar",
    "transporte escolar",
    "libros de texto",
    "material escolar",
    "necesidades educativas",
    "ayudas para familias",
    "familia numerosa",
    "familias numerosas",
    "joven",
    "jovenes",
    "bono alquiler joven",
    "alquiler joven",
    "discapacidad",
}
BOCYL_ENVIRONMENTAL_OR_PLANNING_TERMS = {
    "medio ambiente",
    "ordenacion del territorio",
    "urbanismo",
    "planeamiento",
    "plan general",
    "licencia ambiental",
    "licencias",
    "evaluacion ambiental",
    "impacto ambiental",
    "montes",
    "caza",
    "pesca",
    "forestal",
    "ambiental",
}
BOCYL_INSTITUTIONAL_OR_SECTOR_TERMS = {
    "entidades locales",
    "entidad local",
    "ayuntamiento",
    "ayuntamientos",
    "municipio",
    "municipios",
    "diputacion",
    "diputaciones",
    "empresas",
    "empresa",
    "sector",
    "agricultura",
    "ganaderia",
    "industria",
    "industrial",
    "comercio",
    "turismo",
    "cultura",
    "deporte",
}
AUTONOMOUS_GENERIC_WEAK_KEYWORDS = {
    "ayuda",
    "ayudas",
    "subvencion",
    "subvenciones",
    "bases reguladoras",
    "convocatoria",
    "convocatoria de ayudas",
    "convocatoria de subvenciones",
    "vivienda",
    "empleo",
    "formacion",
    "alquiler",
    "ajut",
    "ajuts",
    "laguntza",
    "laguntzak",
    "dirulaguntza",
    "dirulaguntzak",
}
AUTONOMOUS_HIGH_INTENT_KEYWORDS = {
    "beca",
    "becas",
    "beques",
    "beka",
    "bekak",
    "ayudas al estudio",
    "ayudas para alumnado",
    "ayudas para estudiantes",
    "ayudas directas a personas",
    "alumnado",
    "alumnat",
    "ikasle",
    "ikasleak",
    "estudiantes",
    "estudiants",
    "comedor escolar",
    "menjador escolar",
    "transporte escolar",
    "transport escolar",
    "libros de texto",
    "material escolar",
    "necesidades educativas",
    "formacion profesional",
    "universidad",
    "universidades",
    "ayudas para familias",
    "familia numerosa",
    "familias",
    "families",
    "joven",
    "jovenes",
    "joves",
    "gazte",
    "gazteak",
    "alquiler joven",
    "bono alquiler joven",
    "lloguer jove",
    "bo lloguer jove",
    "discapacidad",
}
AUTONOMOUS_DIRECT_TITLE_TERMS = {
    "beca",
    "becas",
    "beques",
    "beka",
    "bekak",
    "ayudas al estudio",
    "ayudas para alumnado",
    "ayudas para estudiantes",
    "ayudas directas a personas",
    "alumnado",
    "alumnat",
    "ikasle",
    "ikasleak",
    "estudiantes",
    "estudiants",
    "comedor escolar",
    "menjador escolar",
    "transporte escolar",
    "transport escolar",
    "libros de texto",
    "material escolar",
    "necesidades educativas",
    "familias",
    "families",
    "joven",
    "jovenes",
    "joves",
    "gazte",
    "gazteak",
    "alquiler joven",
    "bono alquiler joven",
    "lloguer jove",
    "bo lloguer jove",
    "discapacidad",
}
AUTONOMOUS_EMPLOYMENT_NOISE_TERMS = {
    "oposicion",
    "oposiciones",
    "bolsa de empleo",
    "bolsas de empleo",
    "pruebas selectivas",
    "lista provisional",
    "listas provisionales",
    "lista definitiva",
    "listas definitivas",
    "tribunal",
    "tribunales",
    "nombramiento",
    "nombramientos",
    "autoridades y personal",
    "ofertas de empleo publico",
}
AUTONOMOUS_PROCEDURAL_NOISE_TERMS = {
    "contratacion",
    "licitacion",
    "urbanismo",
    "medio ambiente",
    "industria",
    "energia",
    "agricultura",
    "ganaderia",
    "entidades locales",
    "ayuntamientos",
    "empresas",
    "empresa",
    "concesion",
    "concesion ya resuelta",
    "resolucion de concesion",
    "relacion de beneficiarios",
    "relacion de personas beneficiarias",
    "beneficiarios de las ayudas",
    "beneficiarias de las ayudas",
    "anuncio",
    "procedimiento",
}
BORM_DIRECT_TITLE_TERMS = {
    "beca",
    "becas",
    "ayudas al estudio",
    "ayudas para alumnado",
    "ayudas para estudiantes",
    "ayudas economicas",
    "ayudas directas",
    "alumnado",
    "estudiantes",
    "comedor escolar",
    "transporte escolar",
    "libros de texto",
    "material escolar",
    "necesidades educativas",
    "movilidad internacional",
    "ayudas a la movilidad",
    "familias",
    "discapacidad",
}
BORM_PERSON_CONTEXT_TERMS = {
    "alumnado",
    "estudiante",
    "estudiantes",
    "familia",
    "familias",
    "joven",
    "jovenes",
    "personas con discapacidad",
    "discapacidad",
    "movilidad internacional",
}
BORM_PUBLIC_EMPLOYMENT_OR_CONTEST_TERMS = {
    "profesorado ayudante doctor",
    "concurso publico",
    "concursos de profesorado",
    "bolsa de trabajo",
    "bolsas de trabajo",
    "bolsa de empleo",
    "bolsas de empleo",
    "procesos selectivos",
    "pruebas selectivas",
    "certamen",
    "certamenes",
    "premio",
    "premios",
    "lista provisional",
    "lista definitiva",
    "nombramiento",
    "tribunal",
}
BORM_ENTITY_PROJECT_NOISE_TERMS = {
    "entidades del tercer sector",
    "entidades",
    "proyectos",
    "asociaciones",
    "ayuntamientos",
    "empresas",
}
BORM_PROCEDURAL_NOISE_TERMS = {
    "autorizacion del convenio",
    "convenio de colaboracion",
    "concesion directa",
    "concesion complementaria",
    "orden de concesion",
    "autoriza la concesion",
    "modifica la orden",
}
TRANSPORT_SUPPORT_KEYWORDS = {
    "ayuda",
    "ayudas",
    "subvención",
    "subvenciones",
    "beca",
    "becas",
    "estudiantes",
}
STRONG_PHRASES = {
    "bases reguladoras",
    "convocatoria de ayudas",
    "convocatoria de subvenciones",
    "ayudas al estudio",
    "becas de carácter general",
    "bono alquiler",
    "bono social",
    "familia numerosa",
    "subvenciones para alumnado",
    "ayudas para alumnado",
    "ayudas para estudiantes",
    "formacion profesional",
    "necesidades especificas",
    "material escolar",
    "libros de texto",
    "transporte escolar",
    "comedor escolar",
    "necesidades educativas",
}
STRONG_KEYWORDS = {
    "beca",
    "becas",
    "ayuda",
    "ayudas",
    "subvención",
    "subvenciones",
    "alquiler",
    "discapacidad",
    "educación",
    "estudiantes",
    "vivienda",
    "educacion",
    "universidad",
    "universidades",
    "alumnado",
    "familias",
    "joven",
    "jovenes",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="official-sources")
    parser.add_argument(
        "--db-path",
        default=os.environ.get(
            "OFFICIAL_SOURCES_DB_PATH",
            os.environ.get("OFFICIAL_SOURCES_DB", "official-sources.sqlite"),
        ),
        help="SQLite database path.",
    )
    parser.add_argument(
        "--artifact-dir",
        default=os.environ.get("OFFICIAL_SOURCES_ARTIFACT_DIR", "data/artifacts"),
        help="Local artifact cache directory.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    db = subparsers.add_parser("db", help="Inspect, migrate, and validate the SQLite schema.")
    db_subparsers = db.add_subparsers(dest="db_command", required=True)
    db_subparsers.add_parser("status", help="Show current and pending schema migrations.")
    db_subparsers.add_parser("migrate", help="Apply pending schema migrations.")
    db_subparsers.add_parser("validate", help="Validate the database schema.")
    backup = db_subparsers.add_parser("backup", help="Create a safe SQLite database backup.")
    backup.add_argument("--output", required=True, help="Backup SQLite file path.")
    backup.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing backup file explicitly.",
    )
    backup.add_argument(
        "--quick-check",
        action="store_true",
        help="Verify source and backup with PRAGMA quick_check. This is the default.",
    )
    backup.add_argument(
        "--full-check",
        action="store_true",
        help="Verify source and backup with PRAGMA integrity_check.",
    )
    backup.add_argument(
        "--no-verify",
        action="store_true",
        help="Skip backup verification explicitly.",
    )
    backup.add_argument(
        "--min-size-bytes",
        type=int,
        default=1024,
        help="Minimum acceptable backup size in bytes.",
    )

    sources = subparsers.add_parser("sources", help="Read the executable source registry.")
    sources_subparsers = sources.add_subparsers(dest="sources_command", required=True)
    sources_subparsers.add_parser("list", help="List registered official sources.")
    source_status = sources_subparsers.add_parser("status", help="Show one registered source.")
    source_status.add_argument("--source", required=True, help="Source code, for example BOCYL.")

    rss = subparsers.add_parser("rss", help="RSS/Atom discovery monitor commands.")
    rss_subparsers = rss.add_subparsers(dest="rss_command", required=True)
    rss_monitor = rss_subparsers.add_parser(
        "monitor",
        help="Preview or write metadata-only RSS/Atom discovery records for one source.",
    )
    rss_monitor.add_argument(
        "--source",
        required=True,
        help="Single source code, for example BOCYL.",
    )
    rss_monitor.add_argument("--date", required=True, help="Monitor date in YYYY-MM-DD format.")
    rss_monitor.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Maximum discovery records to emit. Default: 50.",
    )
    rss_monitor.add_argument(
        "--write",
        action="store_true",
        help="Write metadata-only JSONL output. Default is preview only.",
    )
    rss_monitor.add_argument(
        "--output-root",
        default="data/rss_monitor",
        help="Root directory for explicit --write JSONL output.",
    )

    api = subparsers.add_parser("api", help="API discovery monitor commands.")
    api_subparsers = api.add_subparsers(dest="api_command", required=True)
    api_monitor = api_subparsers.add_parser(
        "monitor",
        help="Preview or write metadata-only API discovery records for one source.",
    )
    api_monitor.add_argument(
        "--source",
        required=True,
        help="Single source code, for example BOPV.",
    )
    api_monitor.add_argument("--date", required=True, help="Monitor date in YYYY-MM-DD format.")
    api_monitor.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Maximum discovery records to request. Default: 50.",
    )
    api_monitor.add_argument(
        "--write",
        action="store_true",
        help="Write metadata-only JSONL output. Default is preview only.",
    )
    api_monitor.add_argument(
        "--output-root",
        default="data/api_monitor",
        help="Root directory for explicit --write JSONL output.",
    )

    html = subparsers.add_parser("html", help="HTML discovery monitor commands.")
    html_subparsers = html.add_subparsers(dest="html_command", required=True)
    html_monitor = html_subparsers.add_parser(
        "monitor",
        help="Preview or write metadata-only HTML discovery records for one source.",
    )
    html_monitor.add_argument(
        "--source",
        required=True,
        help="Single source code, for example BOP_A_CORUNA.",
    )
    html_monitor.add_argument("--date", required=True, help="Monitor date in YYYY-MM-DD format.")
    html_monitor.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Maximum discovery records to emit. Default: 50.",
    )
    html_monitor.add_argument(
        "--write",
        action="store_true",
        help="Write metadata-only JSONL output. Default is preview only.",
    )
    html_monitor.add_argument(
        "--output-root",
        default="data/html_monitor",
        help="Root directory for explicit --write JSONL output.",
    )

    hermes = subparsers.add_parser("hermes", help="Read-only Hermes drift auditor commands.")
    hermes_subparsers = hermes.add_subparsers(dest="hermes_command", required=True)
    hermes_audit = hermes_subparsers.add_parser(
        "audit",
        help="Evaluate release/source drift without mutating the repository.",
    )
    hermes_audit.add_argument(
        "--contract",
        default=None,
        help=(
            "Path to the Hermes audit contract YAML. Defaults to config/hermes/audit_contract.yaml."
        ),
    )
    hermes_audit.add_argument(
        "--repo-root",
        default=".",
        help="Repository root to audit. Default: current directory.",
    )
    hermes_audit.add_argument(
        "--registry",
        default=None,
        help="Path to config/sources.yaml. Default: <repo-root>/config/sources.yaml.",
    )
    hermes_audit.add_argument(
        "--project-state",
        default=None,
        help="Path to PROJECT_STATE.md. Default: <repo-root>/PROJECT_STATE.md.",
    )
    hermes_audit.add_argument(
        "--output",
        default=None,
        help="Optional markdown report path to write. Stdout is always emitted.",
    )
    hermes_audit.add_argument(
        "--release-contract",
        default=None,
        help=(
            "External release contract YAML containing release.expected_head_sha. "
            "Default in strict mode: /etc/official-sources/hermes-audit-contract.yaml."
        ),
    )
    hermes_audit.add_argument(
        "--strict-release-contract",
        action="store_true",
        help="Require an external release contract for the HEAD gate.",
    )
    hermes_audit.add_argument(
        "--fail-on-no-go",
        action="store_true",
        help="Return exit code 1 when the audit verdict is NO-GO.",
    )
    hermes_scheduled_audit = hermes_subparsers.add_parser(
        "scheduled-audit",
        help="Run the scheduled strict release audit and write VPS watchdog evidence.",
    )
    hermes_scheduled_audit.add_argument(
        "--repo-root",
        default="/opt/official-sources/app",
        help="Repository root to audit. Default: /opt/official-sources/app.",
    )
    hermes_scheduled_audit.add_argument(
        "--state-root",
        default="/var/lib/hermes-official-sources-auditor",
        help="State directory for scheduled Hermes reports and logs.",
    )
    hermes_scheduled_audit.add_argument(
        "--release-contract",
        default="/etc/official-sources/hermes-audit-contract.yaml",
        help="External release contract YAML containing release.expected_head_sha.",
    )
    hermes_scheduled_audit.add_argument(
        "--official-sources-bin",
        default=None,
        help=(
            "official-sources executable used for the strict audit. "
            "Default: <repo-root>/.venv/bin/official-sources."
        ),
    )
    hermes_scheduled_freshness = hermes_subparsers.add_parser(
        "scheduled-freshness-report",
        help="Run the Hermes freshness report-only integration without service enforcement.",
    )
    hermes_scheduled_freshness.add_argument(
        "--repo-root",
        default="/opt/official-sources/app",
        help="Repository/runtime root containing data/... monitor state. Default: /opt/official-sources/app.",
    )
    hermes_scheduled_freshness.add_argument(
        "--state-root",
        default="/var/lib/hermes-official-sources-auditor",
        help="Hermes state root. Freshness reports are written below freshness-reports/.",
    )
    hermes_scheduled_freshness.add_argument(
        "--official-sources-bin",
        default=None,
        help=(
            "official-sources executable used for the freshness report. "
            "Default: <repo-root>/.venv/bin/official-sources."
        ),
    )
    hermes_scheduled_freshness.add_argument(
        "--default-threshold-hours",
        type=int,
        default=72,
        help="Freshness threshold for runtime inputs. Default: 72.",
    )
    hermes_scheduled_freshness.add_argument(
        "--critical-source",
        action="append",
        default=None,
        help="Critical source code for fail-closed freshness verdicts. Can be repeated.",
    )
    hermes_scheduled_freshness.add_argument(
        "--expected-source",
        action="append",
        default=None,
        help="Expected source code for missing-input reporting. Can be repeated.",
    )
    hermes_freshness = hermes_subparsers.add_parser(
        "freshness-report",
        help="Render a read-only Hermes source freshness report from local state.",
    )
    freshness_input = hermes_freshness.add_mutually_exclusive_group(required=True)
    freshness_input.add_argument(
        "--state",
        help="JSON freshness state fixture to read. No live fetches or materialization are run.",
    )
    freshness_input.add_argument(
        "--runtime-root",
        help=(
            "Repository/runtime root containing data/rss_monitor, data/api_monitor, and "
            "data/html_monitor read-only outputs."
        ),
    )
    freshness_input.add_argument(
        "--observations-jsonl",
        help=(
            "Freshness observation JSONL produced from existing runtime state. "
            "No live fetches or materialization are run."
        ),
    )
    hermes_freshness.add_argument(
        "--now",
        required=True,
        help="Evaluation timestamp in ISO-8601 format, for example 2026-06-13T12:00:00Z.",
    )
    hermes_freshness.add_argument(
        "--default-threshold-hours",
        type=int,
        default=72,
        help="Freshness threshold for runtime inputs. Default: 72.",
    )
    hermes_freshness.add_argument(
        "--critical-source",
        action="append",
        default=[],
        help="Source code that should return NO-GO when missing or stale. Can be repeated.",
    )
    hermes_freshness.add_argument(
        "--expected-source",
        action="append",
        default=[],
        help="Source code expected in runtime inputs; missing values are reported explicitly.",
    )
    hermes_freshness.add_argument(
        "--output",
        default=None,
        help="Optional markdown report path to write. Stdout is always emitted.",
    )
    hermes_freshness_observations = hermes_subparsers.add_parser(
        "freshness-observations",
        help=(
            "Produce freshness observation JSONL from existing runtime state only. "
            "No live fetches, materialization, or product writes are run."
        ),
    )
    hermes_freshness_observations.add_argument(
        "--runtime-root",
        required=True,
        help=(
            "Repository/runtime root containing data/rss_monitor, data/api_monitor, and "
            "data/html_monitor read-only outputs."
        ),
    )
    hermes_freshness_observations.add_argument(
        "--db-path",
        default=None,
        help="Optional SQLite database to inspect read-only for ingestion_runs freshness observations.",
    )
    hermes_freshness_observations.add_argument(
        "--source",
        action="append",
        default=[],
        help="Optional source code filter. Can be repeated.",
    )
    hermes_freshness_observations.add_argument(
        "--output",
        required=True,
        help="Freshness observation JSONL path to write.",
    )

    ingest = subparsers.add_parser("ingest-boe-summary", help="Ingest one BOE daily summary.")
    ingest.add_argument(
        "--date",
        required=True,
        help="Target date in YYYY-MM-DD format or today.",
    )
    ingest_boja = subparsers.add_parser(
        "ingest-boja-date",
        help="Ingest BOJA official API metadata for one date.",
    )
    ingest_boja.add_argument(
        "--date",
        required=True,
        help="Target date in YYYY-MM-DD format or today.",
    )
    ingest_bocm = subparsers.add_parser(
        "ingest-bocm-date",
        help="Ingest BOCM metadata for one date using official issue discovery.",
    )
    ingest_bocm.add_argument(
        "--date",
        required=True,
        help="Target date in YYYY-MM-DD format or today.",
    )
    ingest_dogv = subparsers.add_parser(
        "ingest-dogv-date",
        help="Ingest DOGV official JSON metadata for one date.",
    )
    ingest_dogv.add_argument(
        "--date",
        required=True,
        help="Target date in YYYY-MM-DD format or today.",
    )
    ingest_dogc = subparsers.add_parser(
        "ingest-dogc-date",
        help="Ingest DOGC official API metadata for one date.",
    )
    ingest_dogc.add_argument(
        "--date",
        required=True,
        help="Target date in YYYY-MM-DD format or today.",
    )
    ingest_bocyl = subparsers.add_parser(
        "ingest-bocyl-date",
        help="Ingest BOCYL official JSON metadata for one date.",
    )
    ingest_bocyl.add_argument(
        "--date",
        required=True,
        help="Target date in YYYY-MM-DD format or today.",
    )
    ingest_bopv = subparsers.add_parser(
        "ingest-bopv-date",
        help="Ingest BOPV/EHAA metadata for one date using official calendar and issue XML.",
    )
    ingest_bopv.add_argument(
        "--date",
        required=True,
        help="Target date in YYYY-MM-DD format or today.",
    )
    ingest_boa = subparsers.add_parser(
        "ingest-boa-date",
        help="Ingest BOA official JSON metadata for one date.",
    )
    ingest_boa.add_argument(
        "--date",
        required=True,
        help="Target date in YYYY-MM-DD format or today.",
    )
    ingest_borm = subparsers.add_parser(
        "ingest-borm-date",
        help="Ingest BORM official XML index metadata for one date.",
    )
    ingest_borm.add_argument(
        "--date",
        required=True,
        help="Target date in YYYY-MM-DD format or today.",
    )
    ingest_monitor = subparsers.add_parser(
        "ingest-monitor-date",
        help=(
            "Materialize one validated RSS/HTML/API monitor result into the selected "
            "SQLite database for one source and date. Writes ingestion_runs, runtime "
            "official_sources, and official_documents; does not write evidence, candidates, "
            "registry config, publication, or product outputs."
        ),
    )
    ingest_monitor.add_argument(
        "--source",
        required=True,
        help="Single source code with a validated monitor, for example BOIB or DOCM.",
    )
    ingest_monitor.add_argument("--date", required=True, help="Target date in YYYY-MM-DD format.")
    ingest_monitor.add_argument(
        "--monitor",
        choices=("auto", "rss", "html", "api"),
        default="auto",
        help="Monitor parser to use. Default: auto from the registry access method.",
    )
    ingest_monitor.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Maximum monitor records to materialize. Default: 50.",
    )
    ingest_bdns_latest = subparsers.add_parser(
        "ingest-bdns-latest",
        help="Ingest latest BDNS public grant calls with an explicit small limit.",
    )
    ingest_bdns_latest.add_argument(
        "--limit",
        type=int,
        default=BDNS_DEFAULT_PAGE_SIZE,
        help="Maximum latest convocatorias to ingest. Default: 10. Hard max: 100.",
    )
    ingest_bdns_call = subparsers.add_parser(
        "ingest-bdns-call",
        help="Ingest one BDNS convocatoria detail by numConv/codigoBDNS.",
    )
    ingest_bdns_call.add_argument(
        "--num-conv",
        required=True,
        help="BDNS convocatoria number / codigoBDNS.",
    )
    preview_placsp_feed = subparsers.add_parser(
        "preview-placsp-feed",
        help="Preview one PLACSP Atom feed page without storing tender metadata.",
    )
    preview_placsp_feed.add_argument(
        "--feed-type",
        default="profiles",
        help="PLACSP feed type. Default: profiles.",
    )
    preview_placsp_feed.add_argument(
        "--limit",
        type=int,
        default=PLACSP_DEFAULT_LIMIT,
        help="Maximum feed entries to preview. Default: 50. Hard max: 500.",
    )
    ingest_placsp_feed = subparsers.add_parser(
        "ingest-placsp-feed",
        help="Ingest one PLACSP Atom feed page as metadata-only tender records.",
    )
    ingest_placsp_feed.add_argument(
        "--feed-type",
        default="profiles",
        help="PLACSP feed type. Default: profiles.",
    )
    ingest_placsp_feed.add_argument(
        "--limit",
        type=int,
        default=PLACSP_DEFAULT_LIMIT,
        help="Maximum feed entries to ingest. Default: 50. Hard max: 500.",
    )
    search_bdns = subparsers.add_parser(
        "search-bdns-calls",
        help="Search BDNS convocatorias with strict pagination limits.",
    )
    search_bdns.add_argument("--date-from", help="Start date in DD/MM/YYYY format.")
    search_bdns.add_argument("--date-to", help="End date in DD/MM/YYYY format.")
    search_bdns.add_argument(
        "--page-size",
        type=int,
        default=BDNS_DEFAULT_PAGE_SIZE,
        help="Page size for BDNS search. Default: 10. Hard max: 100.",
    )
    search_bdns.add_argument(
        "--max-pages",
        type=int,
        default=1,
        help="Maximum pages to fetch. Default: 1. Hard max: 10.",
    )
    preview_bdns_catalog = subparsers.add_parser(
        "preview-bdns-catalog",
        help="Preview a safe BDNS metadata catalog without ingesting documents.",
    )
    preview_bdns_catalog.add_argument(
        "--catalog",
        required=True,
        help="BDNS metadata catalog name, for example organos, sectores, or regiones.",
    )
    preview_bdns_catalog.add_argument(
        "--vpd",
        default="GE",
        help="BDNS portal ID for catalogs that require it. Default: GE.",
    )
    preview_bdns_catalog.add_argument(
        "--id-admon",
        help="Administrative body type for organos: C, A, L, or O.",
    )
    preview_bdns_catalog.add_argument(
        "--ambito",
        help="Scope for reglamentos catalogs when needed.",
    )
    ingest_bdns_catalog = subparsers.add_parser(
        "ingest-bdns-catalog",
        help="Ingest a safe BDNS metadata catalog into reusable local evidence.",
    )
    ingest_bdns_catalog.add_argument(
        "--catalog",
        required=True,
        help="BDNS metadata catalog name, for example sectores, finalidades, or organos.",
    )
    ingest_bdns_catalog.add_argument(
        "--vpd",
        default="GE",
        help="BDNS portal ID for catalogs that require it. Default: GE.",
    )
    ingest_bdns_catalog.add_argument(
        "--id-admon",
        help="Administrative body type for organos: C, A, L, or O.",
    )
    ingest_bdns_catalog.add_argument(
        "--ambito",
        help="Scope for reglamentos catalogs when needed.",
    )
    export_bdns_grants = subparsers.add_parser(
        "export-bdns-grants",
        help="Export enriched BDNS grant-call metadata as JSONL for downstream staging.",
    )
    export_bdns_grants.add_argument(
        "--output",
        required=True,
        help="JSONL output path.",
    )
    export_bdns_grants.add_argument(
        "--limit",
        type=int,
        help="Optional maximum number of BDNS grant calls to export.",
    )
    export_bdns_business_grants = subparsers.add_parser(
        "export-bdns-business-grants",
        help="Export ranked BDNS business-grants profile records as JSONL.",
    )
    export_bdns_business_grants.add_argument(
        "--output",
        required=True,
        help="JSONL output path.",
    )
    export_bdns_business_grants.add_argument(
        "--min-score",
        type=float,
        default=0.35,
        help="Minimum business relevance score. Default: 0.35.",
    )
    export_bdns_business_grants.add_argument(
        "--limit",
        type=int,
        help="Optional maximum number of records to export.",
    )
    export_bdns_business_dashboard = subparsers.add_parser(
        "export-bdns-business-dashboard",
        help="Export a static HTML BDNS business-grants radar dashboard.",
    )
    export_bdns_business_dashboard.add_argument(
        "--output",
        required=True,
        help="HTML output path.",
    )
    export_bdns_business_dashboard.add_argument(
        "--min-score",
        type=float,
        default=0.35,
        help="Minimum business relevance score. Default: 0.35.",
    )
    export_bdns_business_dashboard.add_argument(
        "--limit",
        type=int,
        default=200,
        help="Maximum records to render. Default: 200.",
    )
    export_bdns_concessions = subparsers.add_parser(
        "export-bdns-concessions",
        help="Export sanitized stored BDNS concessions as JSONL for downstream staging.",
    )
    export_bdns_concessions.add_argument(
        "--output",
        required=True,
        help="JSONL output path.",
    )
    export_bdns_concessions.add_argument(
        "--num-conv",
        help="Optional BDNS convocatoria number / codigoBDNS to filter concessions.",
    )
    export_bdns_concessions.add_argument(
        "--limit",
        type=int,
        help="Optional maximum number of BDNS concessions to export.",
    )
    preview_bdns_concesiones = subparsers.add_parser(
        "preview-bdns-concesiones",
        help="Preview BDNS concesiones for one convocatoria without storing entries.",
    )
    preview_bdns_concesiones.add_argument(
        "--num-conv",
        required=True,
        help="BDNS convocatoria number / codigoBDNS to scope the concessions search.",
    )
    preview_bdns_concesiones.add_argument(
        "--page-size",
        type=int,
        default=BDNS_DEFAULT_PAGE_SIZE,
        help="Page size for BDNS concessions preview. Default: 10. Hard max: 100.",
    )
    preview_bdns_concesiones.add_argument(
        "--vpd",
        default="GE",
        help="BDNS portal ID. Default: GE.",
    )
    preview_bdns_concesiones.add_argument(
        "--include-beneficiary-fields",
        action="store_true",
        help="Store beneficiary name/person ID in the preview metadata.",
    )
    ingest_bdns_concesiones = subparsers.add_parser(
        "ingest-bdns-concesiones",
        help="Ingest BDNS concesiones for one convocatoria with strict pagination limits.",
    )
    ingest_bdns_concesiones.add_argument(
        "--num-conv",
        help="BDNS convocatoria number / codigoBDNS to scope the concessions search.",
    )
    ingest_bdns_concesiones.add_argument(
        "--page-size",
        type=int,
        default=BDNS_DEFAULT_PAGE_SIZE,
        help="Page size for BDNS concessions ingestion. Default: 10. Hard max: 100.",
    )
    ingest_bdns_concesiones.add_argument(
        "--max-pages",
        type=int,
        default=1,
        help="Maximum pages to fetch. Default: 1. Hard max: 10.",
    )
    ingest_bdns_concesiones.add_argument(
        "--vpd",
        default="GE",
        help="BDNS portal ID. Default: GE.",
    )
    ingest_bdns_concesiones.add_argument(
        "--include-beneficiary-fields",
        action="store_true",
        help="Store beneficiary name/person ID. Default redacts these fields.",
    )
    enrich_boja = subparsers.add_parser(
        "enrich-boja-evidence-urls",
        help="Enrich stored BOJA documents with official evidence URLs for explicit IDs.",
    )
    enrich_boja.add_argument(
        "--candidate-ids",
        help="Comma-separated BOJA source_candidate IDs to enrich.",
    )
    enrich_boja.add_argument(
        "--document-ids",
        help="Comma-separated BOJA official_documents IDs to enrich.",
    )
    ingest_range = subparsers.add_parser(
        "ingest-boe-range",
        help=(
            "Ingest BOE daily summaries for a controlled inclusive date range. "
            "Artifacts are never downloaded by this command."
        ),
    )
    ingest_range.add_argument("--date-from", required=True, help="Start date in YYYY-MM-DD format.")
    ingest_range.add_argument("--date-to", required=True, help="End date in YYYY-MM-DD format.")
    ingest_range.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip dates already recorded as success or no_publication.",
    )
    ingest_range.add_argument(
        "--max-days",
        type=int,
        default=90,
        help="Maximum inclusive range length. Default: 90.",
    )
    ingest_range.add_argument(
        "--force",
        action="store_true",
        help="Allow ranges above 365 days only with --confirm-large-range.",
    )
    ingest_range.add_argument(
        "--confirm-large-range",
        action="store_true",
        help="Explicit acknowledgment required with --force for ranges above 365 days.",
    )
    ingest_range.add_argument(
        "--continue-on-no-publication",
        action="store_true",
        help="Continue when a date is recorded as controlled no_publication.",
    )
    ingest_range.add_argument(
        "--stop-on-error",
        action="store_true",
        help="Stop immediately on real ingestion failures.",
    )
    ingest_range.add_argument(
        "--sleep-seconds",
        type=float,
        default=1.0,
        help="Limiter period between BOE summary requests. Default: 1 second.",
    )

    download = subparsers.add_parser(
        "download-boe-artifacts", help="Download stored official BOE artifact URLs."
    )
    download.add_argument(
        "--source",
        choices=["BOE", "BOJA", "DOGV", "BOCYL", "BORM"],
        default="BOE",
        help="Official source for scoped artifact download. Default: BOE.",
    )
    download.add_argument("--date", help="Target date in YYYY-MM-DD format or today.")
    download.add_argument(
        "--candidate-ids",
        help="Comma-separated source_candidate IDs to download artifacts for.",
    )
    download.add_argument(
        "--document-ids",
        help="Comma-separated official_documents IDs to download artifacts for.",
    )
    download.add_argument(
        "--types",
        default="xml,html",
        help="Comma-separated artifact types. Default: xml,html. PDF requires explicit request.",
    )

    source_download = subparsers.add_parser(
        "download-source-artifacts",
        help="Download stored official source artifact URLs with explicit source scope.",
    )
    source_download.add_argument(
        "--source",
        choices=["BOE", "BOJA", "DOGV", "BOCYL", "BORM"],
        required=True,
        help="Official source for scoped artifact download.",
    )
    source_download.add_argument("--date", help="Target date in YYYY-MM-DD format or today.")
    source_download.add_argument(
        "--candidate-ids",
        help="Comma-separated source_candidate IDs to download artifacts for.",
    )
    source_download.add_argument(
        "--document-ids",
        help="Comma-separated official_documents IDs to download artifacts for.",
    )
    source_download.add_argument(
        "--types",
        default="xml,html",
        help="Comma-separated artifact types. DOGV currently requires explicit pdf.",
    )

    evidence_status = subparsers.add_parser(
        "candidate-evidence-status",
        help="Show read-only operational evidence status for source candidates.",
    )
    evidence_status.add_argument(
        "--candidate-ids",
        help="Comma-separated source_candidate IDs to inspect.",
    )
    evidence_status.add_argument("--date-from", help="Start date in YYYY-MM-DD format.")
    evidence_status.add_argument("--date-to", help="End date in YYYY-MM-DD format.")
    evidence_status.add_argument(
        "--profile",
        choices=["la-ayuda"],
        help="Filter candidates by documented profile project key.",
    )
    evidence_status.add_argument("--project-key", help="Filter candidates by project key.")

    mark_evidence = subparsers.add_parser(
        "mark-candidate-evidence",
        help="Record operational evidence review metadata for one source candidate.",
    )
    mark_evidence.add_argument("--candidate-id", type=int, required=True)
    mark_evidence.add_argument(
        "--evidence-label",
        choices=sorted(EVIDENCE_LABELS),
    )
    mark_evidence.add_argument(
        "--evidence-review-status",
        choices=sorted(EVIDENCE_REVIEW_STATUSES),
        default="not_reviewed",
    )
    mark_evidence.add_argument("--notes")
    mark_evidence.add_argument("--selected-for-evidence", action="store_true")
    mark_evidence.add_argument("--selected-for-pdf", action="store_true")
    mark_evidence.add_argument("--manual-decision", choices=sorted(MANUAL_DECISIONS))
    mark_evidence.add_argument("--manual-notes")
    mark_evidence.add_argument("--needs-pdf", choices=sorted(NEEDS_PDF_VALUES))
    mark_evidence.add_argument("--downstream-project-fit", choices=sorted(DOWNSTREAM_PROJECT_FITS))
    mark_evidence.add_argument("--reviewed-by")
    mark_evidence.add_argument("--reviewed-at")

    export_evidence = subparsers.add_parser(
        "export-downstream-evidence",
        help="Export reviewed source-candidate evidence JSON files for downstream staging.",
    )
    export_evidence.add_argument(
        "--candidate-ids",
        required=True,
        help="Comma-separated source_candidate IDs to export.",
    )
    export_evidence.add_argument(
        "--output-dir",
        required=True,
        help="Directory where grouped downstream evidence JSON files will be written.",
    )

    check = subparsers.add_parser("integrity-check", help="Recompute local artifact hashes.")
    check.add_argument(
        "--date",
        required=True,
        help="Target date in YYYY-MM-DD format or today.",
    )

    status = subparsers.add_parser("status", help="Show BOE operational status for a date.")
    status.add_argument(
        "--date",
        required=True,
        help="Target date in YYYY-MM-DD format or today.",
    )
    consolidated_get = subparsers.add_parser(
        "boe-consolidated-get",
        help="Fetch and store one BOE consolidated law by official identifier.",
    )
    consolidated_get.add_argument(
        "--identifier",
        required=True,
        help="BOE consolidated law identifier, for example BOE-A-2024-11111.",
    )
    consolidated_index_get = subparsers.add_parser(
        "boe-consolidated-index-get",
        help="Fetch and store the official BOE consolidated law text index.",
    )
    consolidated_index_get.add_argument(
        "--identifier",
        required=True,
        help="BOE consolidated law identifier, for example BOE-A-2024-11111.",
    )
    consolidated_block_get = subparsers.add_parser(
        "boe-consolidated-block-get",
        help="Fetch and store one official BOE consolidated law text block.",
    )
    consolidated_block_get.add_argument(
        "--identifier",
        required=True,
        help="BOE consolidated law identifier, for example BOE-A-2024-11111.",
    )
    consolidated_block_get.add_argument(
        "--block-id",
        required=True,
        help="Official BOE consolidated law block identifier.",
    )
    consolidated_block_get.add_argument(
        "--print-content",
        action="store_true",
        help="Print official block text content after the compact status line.",
    )
    _add_find_candidates_parser(
        subparsers,
        "find-source-candidates",
        description=(
            "find-source-candidates = preferred generic command. Creates human-review "
            "candidates by keyword matching locally stored official-source titles and metadata "
            "only. This is not legal classification and may produce false positives."
        ),
        help=(
            "find-source-candidates = preferred generic command for locally stored "
            "official-source metadata."
        ),
    )
    _add_find_candidates_parser(
        subparsers,
        "find-boe-candidates",
        description=(
            "find-boe-candidates = backwards-compatible BOE-default/source-aware command. "
            "Prefer find-source-candidates for new source families. It matches locally stored "
            "official-source titles and metadata only, is not legal classification, and may "
            "produce false positives."
        ),
        help=("Legacy BOE-default source-aware candidate finder. Prefer find-source-candidates."),
    )
    opposition_alerts = subparsers.add_parser(
        "dry-run-opposition-alerts",
        description=(
            "Read-only alert-grade dry-run for oposiciones/public employment notices. "
            "It scans locally stored official_documents metadata only and never writes "
            "source_candidates, artifacts, or external product output."
        ),
        help="Preview alert-grade oposiciones notices from stored metadata without DB writes.",
    )
    opposition_alerts.add_argument("--date-from", required=True, help="Start date in YYYY-MM-DD.")
    opposition_alerts.add_argument("--date-to", required=True, help="End date in YYYY-MM-DD.")
    opposition_alerts.add_argument(
        "--source",
        required=True,
        help=(
            "Comma-separated source codes to scan. Supported: "
            f"{', '.join(OPPOSITION_ALERT_SOURCE_CODES)}."
        ),
    )
    opposition_alerts.add_argument(
        "--limit",
        type=int,
        default=200,
        help="Maximum alert records to emit. Default: 200.",
    )
    opposition_alerts.add_argument(
        "--format",
        choices=["json", "jsonl"],
        default="json",
        help="Output format. Default: json.",
    )
    return parser


def _add_find_candidates_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
    command_name: str,
    *,
    description: str,
    help: str,
) -> argparse.ArgumentParser:
    candidates = subparsers.add_parser(command_name, description=description, help=help)
    candidates.add_argument("--date-from", required=True, help="Start date in YYYY-MM-DD format.")
    candidates.add_argument("--date-to", required=True, help="End date in YYYY-MM-DD format.")
    candidates.add_argument(
        "--source",
        choices=SOURCE_CANDIDATE_SOURCE_CODES,
        default="BOE",
        help=(
            "Official source code to scan. Supported: "
            f"{', '.join(SOURCE_CANDIDATE_SOURCE_CODES)}. Default: BOE."
        ),
    )
    candidates.add_argument(
        "--keywords",
        help="Comma-separated keywords. Matches titles and metadata only, not full content.",
    )
    candidates.add_argument(
        "--profile",
        choices=SOURCE_CANDIDATE_PROFILES,
        help=(
            "Use a documented keyword/filter profile. Currently supported: "
            f"{', '.join(SOURCE_CANDIDATE_PROFILES)}."
        ),
    )
    candidates.add_argument(
        "--include-sections",
        help="Comma-separated BOE section filters, for example III,V-B.",
    )
    candidates.add_argument(
        "--exclude-sections",
        help="Comma-separated BOE section filters to exclude, for example V-A.",
    )
    candidates.add_argument(
        "--include-departments",
        help="Comma-separated department substrings to include.",
    )
    candidates.add_argument(
        "--exclude-departments",
        help="Comma-separated department substrings to exclude.",
    )
    candidates.add_argument("--project-key", default="generic", help="Project key.")
    candidates.add_argument(
        "--candidate-type",
        default="keyword_match",
        help="Candidate type stored for human review.",
    )
    candidates.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview matches without writing source_candidates.",
    )
    candidates.add_argument(
        "--no-write",
        action="store_true",
        help="Alias for --dry-run. Preview matches without writing source_candidates.",
    )
    candidates.add_argument(
        "--write",
        action="store_true",
        help="Explicitly write source_candidates. Without this flag, use --dry-run or --no-write.",
    )
    candidates.add_argument(
        "--limit",
        type=int,
        default=50,
        help=(
            "Maximum sample matches to print in dry-run mode, or maximum candidates to create "
            "in explicit write mode. Default: 50."
        ),
    )
    return candidates


def run(
    argv: list[str] | None = None,
    *,
    summary_fetcher=None,
    boja_fetcher=None,
    boja_detail_fetcher=None,
    bocm_fetcher=None,
    bocyl_fetcher=None,
    bopv_fetcher=None,
    boa_fetcher=None,
    borm_fetcher=None,
    dogv_fetcher=None,
    dogc_fetcher=None,
    dogc_document_fetcher=None,
    bdns_latest_fetcher=None,
    bdns_call_fetcher=None,
    bdns_search_fetcher=None,
    bdns_catalog_fetcher=None,
    bdns_concessions_fetcher=None,
    placsp_feed_fetcher=None,
    rss_fetcher=None,
    api_fetcher=None,
    html_fetcher=None,
    artifact_client: httpx.Client | None = None,
    consolidated_client: httpx.Client | None = None,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    stdout = stdout or sys.stdout
    stderr = stderr or sys.stderr
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return int(exc.code)

    if args.command == "db":
        return _run_db_command(args, stdout, stderr)
    if args.command == "sources":
        return _run_sources_command(args, stdout, stderr)
    if args.command == "rss":
        return _run_rss_command(args, rss_fetcher, stdout, stderr)
    if args.command == "api":
        return _run_api_command(args, api_fetcher, stdout, stderr)
    if args.command == "html":
        return _run_html_command(args, html_fetcher, stdout, stderr)
    if args.command == "hermes":
        return _run_hermes_command(args, stdout, stderr)

    repository = _open_repository(args.db_path)
    if args.command == "ingest-boja-date":
        return _run_ingest_boja(repository, args, boja_fetcher, stdout, stderr)
    if args.command == "ingest-bocm-date":
        return _run_ingest_bocm(repository, args, bocm_fetcher, stdout, stderr)
    if args.command == "ingest-bocyl-date":
        return _run_ingest_bocyl(repository, args, bocyl_fetcher, stdout, stderr)
    if args.command == "ingest-bopv-date":
        return _run_ingest_bopv(repository, args, bopv_fetcher, stdout, stderr)
    if args.command == "ingest-boa-date":
        return _run_ingest_boa(repository, args, boa_fetcher, stdout, stderr)
    if args.command == "ingest-borm-date":
        return _run_ingest_borm(repository, args, borm_fetcher, stdout, stderr)
    if args.command == "ingest-dogv-date":
        return _run_ingest_dogv(repository, args, dogv_fetcher, stdout, stderr)
    if args.command == "ingest-dogc-date":
        return _run_ingest_dogc(
            repository, args, dogc_fetcher, dogc_document_fetcher, stdout, stderr
        )
    if args.command == "ingest-monitor-date":
        return _run_ingest_monitor_date(
            repository,
            args,
            rss_fetcher,
            api_fetcher,
            html_fetcher,
            stdout,
            stderr,
        )
    if args.command == "ingest-bdns-latest":
        return _run_ingest_bdns_latest(repository, args, bdns_latest_fetcher, stdout, stderr)
    if args.command == "ingest-bdns-call":
        return _run_ingest_bdns_call(repository, args, bdns_call_fetcher, stdout, stderr)
    if args.command == "preview-placsp-feed":
        return _run_preview_placsp_feed(repository, args, placsp_feed_fetcher, stdout, stderr)
    if args.command == "ingest-placsp-feed":
        return _run_ingest_placsp_feed(repository, args, placsp_feed_fetcher, stdout, stderr)
    if args.command == "search-bdns-calls":
        return _run_search_bdns_calls(repository, args, bdns_search_fetcher, stdout, stderr)
    if args.command == "preview-bdns-catalog":
        return _run_preview_bdns_catalog(repository, args, bdns_catalog_fetcher, stdout, stderr)
    if args.command == "ingest-bdns-catalog":
        return _run_ingest_bdns_catalog(repository, args, bdns_catalog_fetcher, stdout, stderr)
    if args.command == "export-bdns-grants":
        return _run_export_bdns_grants(repository, args, stdout, stderr)
    if args.command == "export-bdns-business-grants":
        return _run_export_bdns_business_grants(repository, args, stdout, stderr)
    if args.command == "export-bdns-business-dashboard":
        return _run_export_bdns_business_dashboard(repository, args, stdout, stderr)
    if args.command == "export-bdns-concessions":
        return _run_export_bdns_concessions(repository, args, stdout, stderr)
    if args.command == "preview-bdns-concesiones":
        return _run_preview_bdns_concesiones(
            repository, args, bdns_concessions_fetcher, stdout, stderr
        )
    if args.command == "ingest-bdns-concesiones":
        return _run_ingest_bdns_concesiones(
            repository, args, bdns_concessions_fetcher, stdout, stderr
        )
    if args.command == "enrich-boja-evidence-urls":
        return _run_enrich_boja_evidence_urls(repository, args, boja_detail_fetcher, stdout, stderr)
    if args.command == "ingest-boe-range":
        return _run_ingest_range(repository, args, stdout, stderr)
    if args.command in {"find-source-candidates", "find-boe-candidates"}:
        return _run_find_candidates(repository, args, stdout, stderr)
    if args.command == "dry-run-opposition-alerts":
        return _run_dry_run_opposition_alerts(repository, args, stdout, stderr)
    if args.command == "candidate-evidence-status":
        return _run_candidate_evidence_status(repository, args, stdout, stderr)
    if args.command == "mark-candidate-evidence":
        return _run_mark_candidate_evidence(repository, args, stdout, stderr)
    if args.command == "export-downstream-evidence":
        return _run_export_downstream_evidence(repository, args, stdout, stderr)
    if args.command == "boe-consolidated-get":
        return _run_consolidated_get(
            repository, args.identifier, consolidated_client, stdout, stderr
        )
    if args.command == "boe-consolidated-index-get":
        return _run_consolidated_index_get(
            repository, args.identifier, consolidated_client, stdout, stderr
        )
    if args.command == "boe-consolidated-block-get":
        return _run_consolidated_block_get(
            repository,
            args.identifier,
            args.block_id,
            args.print_content,
            consolidated_client,
            stdout,
            stderr,
        )

    if args.command in {"download-boe-artifacts", "download-source-artifacts"}:
        dogv_error = _validate_dogv_download_args(args)
        if dogv_error:
            print(dogv_error, file=stderr)
            return 2
        bocyl_error = _validate_bocyl_download_args(args)
        if bocyl_error:
            print(bocyl_error, file=stderr)
            return 2
        borm_error = _validate_borm_download_args(args)
        if borm_error:
            print(borm_error, file=stderr)
            return 2
        try:
            artifact_types = _parse_artifact_types(args.types, source_code=args.source)
        except BOEArtifactDownloadError as exc:
            print(str(exc), file=stderr)
            return 2
        if args.source in {"BOJA", "DOGV", "BOCYL", "BORM"} and args.date:
            print(
                f"{args.source} artifact downloads require --candidate-ids or --document-ids",
                file=stderr,
            )
            return 2
        if "pdf" in artifact_types and not (args.candidate_ids or args.document_ids):
            print("PDF downloads require --candidate-ids or --document-ids", file=stderr)
            return 2
        try:
            target_date, documents = _resolve_download_selection(
                repository,
                args,
                source_code=args.source,
            )
        except ValueError as exc:
            print(str(exc), file=stderr)
            return 2
        target_label = target_date or "scoped"
        print(
            f"command_started={args.command} source_code={args.source} target_date={target_label}",
            file=stdout,
        )
        return _run_download(
            repository,
            source_code=args.source,
            target_date=target_date,
            documents=documents,
            artifact_types=artifact_types,
            artifact_dir=Path(args.artifact_dir),
            client=artifact_client,
            stdout=stdout,
            stderr=stderr,
        )
    try:
        target_date = resolve_target_date(args.date)
    except ValueError as exc:
        print(str(exc), file=stderr)
        return 2
    print(f"command_started={args.command} source_code=BOE target_date={target_date}", file=stdout)

    if args.command == "ingest-boe-summary":
        return _run_ingest(repository, target_date, summary_fetcher, stdout)
    if args.command == "integrity-check":
        return _run_integrity_check(repository, target_date, stdout, stderr)
    if args.command == "status":
        return _run_status(repository, target_date, stdout)
    print(f"Unknown command: {args.command}", file=stderr)
    return 2


def main() -> None:
    raise SystemExit(run())


def resolve_target_date(value: str) -> str:
    if value == "today":
        return date.today().isoformat()
    return validate_boe_date(value).isoformat()


def resolve_boja_target_date(value: str) -> str:
    if value == "today":
        return date.today().isoformat()
    return validate_boja_date(value).isoformat()


def resolve_bocm_target_date(value: str) -> str:
    if value == "today":
        return date.today().isoformat()
    return validate_bocm_date(value).isoformat()


def resolve_dogv_target_date(value: str) -> str:
    if value == "today":
        return date.today().isoformat()
    return validate_dogv_date(value).isoformat()


def resolve_dogc_target_date(value: str) -> str:
    if value == "today":
        return date.today().isoformat()
    return validate_dogc_date(value).isoformat()


def resolve_bocyl_target_date(value: str) -> str:
    if value == "today":
        return date.today().isoformat()
    return validate_bocyl_date(value).isoformat()


def resolve_bopv_target_date(value: str) -> str:
    if value == "today":
        return date.today().isoformat()
    return validate_bopv_date(value).isoformat()


def resolve_boa_target_date(value: str) -> str:
    if value == "today":
        return date.today().isoformat()
    return validate_boa_date(value).isoformat()


def resolve_borm_target_date(value: str) -> str:
    if value == "today":
        return date.today().isoformat()
    return validate_borm_date(value).isoformat()


def _run_sources_command(
    args: argparse.Namespace,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    try:
        if args.sources_command == "list":
            print("source_code operational_status monitor_support backfill_support", file=stdout)
            for source in list_sources():
                print(
                    (
                        f"{source['source_code']} {source['operational_status']} "
                        f"{source['monitor_support']} {source['backfill_support']}"
                    ),
                    file=stdout,
                )
            return 0
        if args.sources_command == "status":
            source = get_source(args.source)
            print(f"source_code={source['source_code']}", file=stdout)
            print(f"name={source['name']}", file=stdout)
            print(f"jurisdiction={source['jurisdiction']}", file=stdout)
            print(f"jurisdiction_level={source['jurisdiction_level']}", file=stdout)
            print(f"official_landing_url={source['official_landing_url']}", file=stdout)
            print(f"operational_status={source['operational_status']}", file=stdout)
            print(f"monitor_support={source['monitor_support']}", file=stdout)
            print(f"backfill_support={source['backfill_support']}", file=stdout)
            print(f"mcp_support={source['mcp_support']}", file=stdout)
            print(f"candidate_creation_allowed={source['candidate_creation_allowed']}", file=stdout)
            print(f"evidence_grade_allowed={source['evidence_grade_allowed']}", file=stdout)
            return 0
    except SourceRegistryError as exc:
        print(str(exc), file=stderr)
        return 2
    print(f"Unknown sources command: {args.sources_command}", file=stderr)
    return 2


def _run_hermes_command(
    args: argparse.Namespace,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    if args.hermes_command == "freshness-observations":
        try:
            observations = collect_freshness_observations(
                runtime_root=Path(args.runtime_root),
                db_path=Path(args.db_path) if args.db_path else None,
                source_codes=tuple(args.source),
            )
            if not observations:
                print("no freshness observations found", file=stderr)
                return 2
            write_observations_jsonl(observations, Path(args.output))
        except (OSError, HermesFreshnessObservationProducerError) as exc:
            print(str(exc), file=stderr)
            return 2
        print(f"observations_written={len(observations)}", file=stdout)
        print(f"output={args.output}", file=stdout)
        return 0
    if args.hermes_command == "freshness-report":
        try:
            now = parse_timestamp(args.now)
            if args.state:
                observation = load_observation(Path(args.state), now=now)
            elif args.observations_jsonl:
                observation = load_observation_jsonl(
                    Path(args.observations_jsonl),
                    now=now,
                    default_threshold_hours=args.default_threshold_hours,
                    critical_sources=tuple(args.critical_source),
                    expected_sources=tuple(args.expected_source),
                )
            else:
                observation = load_runtime_observation(
                    Path(args.runtime_root),
                    now=now,
                    default_threshold_hours=args.default_threshold_hours,
                    critical_sources=tuple(args.critical_source),
                    expected_sources=tuple(args.expected_source),
                )
            result = evaluate_freshness(observation)
            report = render_freshness_markdown_report(result)
        except (OSError, HermesFreshnessReportError) as exc:
            print(str(exc), file=stderr)
            return 2
        print(report, end="", file=stdout)
        if args.output:
            Path(args.output).write_text(report, encoding="utf-8")
        return 0
    if args.hermes_command == "scheduled-audit":
        result = run_scheduled_strict_audit(
            repo_root=Path(args.repo_root),
            state_root=Path(args.state_root),
            release_contract=Path(args.release_contract),
            official_sources_bin=args.official_sources_bin,
        )
        print(f"report_path={result.report_path}", file=stdout)
        print(f"strict_report_path={result.strict_report_path}", file=stdout)
        print(f"log_path={result.log_path}", file=stdout)
        print(f"strict_exit_code={result.exit_code}", file=stdout)
        return result.exit_code
    if args.hermes_command == "scheduled-freshness-report":
        result = run_scheduled_freshness_report(
            repo_root=Path(args.repo_root),
            state_root=Path(args.state_root),
            official_sources_bin=args.official_sources_bin,
            default_threshold_hours=args.default_threshold_hours,
            critical_sources=tuple(args.critical_source or DEFAULT_CRITICAL_SOURCES),
            expected_sources=tuple(args.expected_source or DEFAULT_EXPECTED_SOURCES),
        )
        print(f"report_path={result.report_path}", file=stdout)
        print(f"freshness_exit_code={result.exit_code}", file=stdout)
        if result.freshness_result.stderr.strip():
            print(result.freshness_result.stderr.strip(), file=stderr)
        return result.exit_code
    if args.hermes_command != "audit":
        print(f"Unknown hermes command: {args.hermes_command}", file=stderr)
        return 2
    try:
        contract = load_audit_contract(Path(args.contract) if args.contract else None)
        release_contract_path = (
            Path(args.release_contract)
            if args.release_contract
            else default_release_contract_path()
        )
        if release_contract_path.exists():
            release_contract = load_release_contract(release_contract_path)
            contract = merge_release_contract(contract, release_contract, release_contract_path)
        elif args.strict_release_contract:
            contract = require_external_release_contract(contract)
        observation = collect_local_observation(
            repo_root=Path(args.repo_root),
            registry_path=Path(args.registry) if args.registry else None,
            project_state_path=Path(args.project_state) if args.project_state else None,
            contract=contract,
        )
        result = evaluate_hermes_drift(contract, observation)
        report = render_markdown_report(result)
    except HermesDriftAuditError as exc:
        print(str(exc), file=stderr)
        return 2

    print(report, end="", file=stdout)
    if args.output:
        Path(args.output).write_text(report, encoding="utf-8")
    if args.fail_on_no_go and result.verdict == "NO-GO":
        return 1
    return 0


def _run_rss_command(
    args: argparse.Namespace,
    rss_fetcher,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    if args.rss_command != "monitor":
        print(f"Unknown rss command: {args.rss_command}", file=stderr)
        return 2

    source_code = args.source.strip().upper()
    if source_code in {"ALL", "*"} or "," in args.source:
        print("rss monitor accepts one source at a time; broad runs are not allowed", file=stderr)
        return 2

    try:
        result = monitor_source_code(
            source_code,
            fetcher=rss_fetcher,
            target_date=args.date,
            limit=args.limit,
        )
    except RSSMonitorError as exc:
        print(str(exc), file=stderr)
        return 2

    mode = "write" if args.write else "preview"
    print(
        (
            f"command_started=rss monitor source_code={source_code} "
            f"date={args.date} mode={mode} records={len(result.records)} "
            f"feed_format={result.feed_format}"
        ),
        file=stdout,
    )
    if args.write:
        output_path = build_rss_monitor_output_path(Path(args.output_root), source_code, args.date)
        write_jsonl(result.records, output_path)
        print(f"output_path={output_path}", file=stdout)
    else:
        for record in result.records:
            print(json.dumps(record, ensure_ascii=False, sort_keys=True), file=stdout)
    return 0


def _run_api_command(
    args: argparse.Namespace,
    api_fetcher,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    if args.api_command != "monitor":
        print(f"Unknown api command: {args.api_command}", file=stderr)
        return 2

    source_code = args.source.strip().upper()
    if source_code in {"ALL", "*"} or "," in args.source:
        print("api monitor accepts one source at a time; broad runs are not allowed", file=stderr)
        return 2

    try:
        result = monitor_api_source_code(
            source_code,
            fetcher=api_fetcher,
            target_date=args.date,
            limit=args.limit,
        )
    except (APIMonitorError, SourceRegistryError) as exc:
        print(str(exc), file=stderr)
        return 2

    mode = "write" if args.write else "preview"
    print(
        (
            f"command_started=api monitor source_code={source_code} "
            f"date={args.date} mode={mode} records={len(result.records)} "
            "discovery_metadata_only=true"
        ),
        file=stdout,
    )
    if args.write:
        output_path = build_api_monitor_output_path(Path(args.output_root), source_code, args.date)
        write_api_jsonl(result.records, output_path)
        print(f"output_path={output_path}", file=stdout)
    else:
        for record in result.records:
            print(json.dumps(record, ensure_ascii=False, sort_keys=True), file=stdout)
    return 0


def _run_html_command(
    args: argparse.Namespace,
    html_fetcher,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    if args.html_command != "monitor":
        print(f"Unknown html command: {args.html_command}", file=stderr)
        return 2

    source_code = args.source.strip().upper()
    if source_code in {"ALL", "*"} or "," in args.source:
        print("html monitor accepts one source at a time; broad runs are not allowed", file=stderr)
        return 2

    try:
        result = monitor_html_source_code(
            source_code,
            fetcher=html_fetcher,
            target_date=args.date,
            limit=args.limit,
        )
    except (HTMLMonitorError, SourceRegistryError) as exc:
        print(str(exc), file=stderr)
        return 2

    mode = "write" if args.write else "preview"
    print(
        (
            f"command_started=html monitor source_code={source_code} "
            f"date={args.date} mode={mode} records={len(result.records)} "
            "discovery_metadata_only=true"
        ),
        file=stdout,
    )
    if args.write:
        output_path = build_html_monitor_output_path(Path(args.output_root), source_code, args.date)
        write_html_jsonl(result.records, output_path)
        print(f"output_path={output_path}", file=stdout)
    else:
        for record in result.records:
            print(json.dumps(record, ensure_ascii=False, sort_keys=True), file=stdout)
    return 0


def _run_ingest_monitor_date(
    repository: OfficialSourcesRepository,
    args: argparse.Namespace,
    rss_fetcher,
    api_fetcher,
    html_fetcher,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    source_code = args.source.strip().upper()
    if source_code in {"ALL", "*"} or "," in args.source:
        print("ingest-monitor-date accepts one source at a time", file=stderr)
        return 2
    try:
        target_date = date.fromisoformat(args.date).isoformat()
    except ValueError:
        print("--date must use YYYY-MM-DD format", file=stderr)
        return 2
    if args.limit < 1:
        print("--limit must be greater than zero", file=stderr)
        return 2

    try:
        source = get_source(source_code)
        monitor_kind = _select_monitor_ingestion_kind(source, args.monitor)
    except (SourceRegistryError, ValueError) as exc:
        print(str(exc), file=stderr)
        return 2

    run = repository.create_ingestion_run(source_code=source_code, target_date=target_date)
    print(
        (
            f"command_started=ingest-monitor-date source_code={source_code} "
            f"target_date={target_date} monitor={monitor_kind} "
            f"db_path={_compact_token(args.db_path)} writes=sqlite_materialization"
        ),
        file=stdout,
    )
    sources_upserted = 0
    source_created = False
    documents_new = 0
    documents_updated = 0
    documents_fetched = 0
    failure_record_index: int | None = None
    try:
        result = _run_monitor_for_ingestion(
            source_code,
            monitor_kind=monitor_kind,
            target_date=target_date,
            limit=args.limit,
            rss_fetcher=rss_fetcher,
            api_fetcher=api_fetcher,
            html_fetcher=html_fetcher,
        )
        documents_fetched = len(result.records)
        source_exists = _runtime_source_exists(repository, source_code)
        source_record = _upsert_registry_source(repository, source, monitor_kind=monitor_kind)
        sources_upserted = 1
        source_created = not source_exists
        for record_index, record in enumerate(result.records, start=1):
            failure_record_index = record_index
            external_id = _monitor_document_external_id(source_code, record)
            existing = repository.get_document_by_external_id(external_id)
            repository.upsert_document(
                source_id=source_record["id"],
                external_id=external_id,
                publication_date=_monitor_publication_date(record, target_date),
                title=_monitor_document_title(record, external_id),
                department=_monitor_department(record),
                section=_monitor_section(record),
                document_type=_monitor_document_type(record, monitor_kind),
                url_html=_monitor_url(record, "html"),
                url_xml=_monitor_url(record, "xml"),
                url_pdf=_monitor_url(record, "pdf"),
                raw_metadata={
                    "ingestion_source": "validated_monitor",
                    "command": "ingest-monitor-date",
                    "ingestion_run_id": run["id"],
                    "monitor_kind": monitor_kind,
                    "monitor_target_date": target_date,
                    "monitor_record": record,
                    "operator_controlled": True,
                },
            )
            if existing is None:
                documents_new += 1
            else:
                documents_updated += 1
            failure_record_index = None
        run_record = repository.finish_ingestion_run(
            run_id=run["id"],
            status="success" if result.records else "no_publication",
            documents_fetched=documents_fetched,
            documents_new=documents_new,
            documents_updated=documents_updated,
            error_message=None
            if result.records
            else f"Monitor returned no records for {target_date}",
            last_http_status=200,
        )
    except Exception as exc:
        error_message = str(exc)
        if failure_record_index is not None:
            error_message = f"record_index={failure_record_index}: {error_message}"
        run_record = repository.finish_ingestion_run(
            run_id=run["id"],
            status="failed",
            documents_fetched=documents_fetched,
            documents_new=documents_new,
            documents_updated=documents_updated,
            error_message=error_message,
            last_http_status=None,
        )

    documents_upserted = run_record["documents_new"] + run_record["documents_updated"]
    partial_materialization = run_record["status"] == "failed" and documents_upserted > 0
    print(
        " ".join(
            [
                f"status={run_record['status']}",
                f"ingestion_run_id={run_record['id']}",
                f"db_path={_compact_token(args.db_path)}",
                f"sources_upserted={sources_upserted}",
                f"source_created={str(source_created).lower()}",
                f"documents_fetched={run_record['documents_fetched']}",
                f"documents_new={run_record['documents_new']}",
                f"documents_updated={run_record['documents_updated']}",
                f"documents_upserted={documents_upserted}",
                f"partial_materialization={str(partial_materialization).lower()}",
                f"failure_record_index={failure_record_index or 'none'}",
                "candidate_creation_allowed=false",
                "evidence_created=false",
                "artifact_downloads=false",
                "product_writes=false",
                "registry_config_mutated=false",
            ]
            + (
                [f"error_message={_compact_token(run_record['error_message'])}"]
                if run_record.get("error_message")
                else []
            )
        ),
        file=stdout,
    )
    return 0 if run_record["status"] in {"success", "no_publication"} else 1


def _select_monitor_ingestion_kind(source: dict[str, Any], requested: str) -> str:
    if requested != "auto":
        return requested
    for access_method in source.get("access_methods", []):
        if access_method.get("status") != "validated":
            continue
        method_type = access_method.get("type")
        if method_type in {"rss", "atom"}:
            return "rss"
        if method_type == "html":
            return "html"
        if method_type in {"api", "xml"}:
            return "api"
    raise ValueError(f"{source.get('source_code', 'source')} has no validated monitor method")


def _runtime_source_exists(repository: OfficialSourcesRepository, source_code: str) -> bool:
    try:
        repository.get_source_by_code(source_code)
    except KeyError:
        return False
    return True


def _run_monitor_for_ingestion(
    source_code: str,
    *,
    monitor_kind: str,
    target_date: str,
    limit: int,
    rss_fetcher,
    api_fetcher,
    html_fetcher,
):
    if monitor_kind == "rss":
        return monitor_source_code(
            source_code,
            fetcher=rss_fetcher,
            target_date=target_date,
            limit=limit,
        )
    if monitor_kind == "api":
        return monitor_api_source_code(
            source_code,
            fetcher=api_fetcher,
            target_date=target_date,
            limit=limit,
        )
    if monitor_kind == "html":
        return monitor_html_source_code(
            source_code,
            fetcher=html_fetcher,
            target_date=target_date,
            limit=limit,
        )
    raise ValueError(f"Unsupported monitor kind: {monitor_kind}")


def _upsert_registry_source(
    repository: OfficialSourcesRepository,
    source: dict[str, Any],
    *,
    monitor_kind: str,
) -> dict[str, Any]:
    source_code = source["source_code"]
    region_code = str(source.get("jurisdiction") or "").strip() or "ES"
    return repository.upsert_official_source(
        code=source_code,
        name=source["name"],
        jurisdiction=source.get("jurisdiction_level") or source.get("jurisdiction") or "other",
        region_code=region_code,
        base_url=source.get("official_landing_url") or _monitor_source_base_url(source),
        access_type=f"official_{monitor_kind}",
        reliability_level="canonical",
    )


def _monitor_source_base_url(source: dict[str, Any]) -> str:
    for access_method in source.get("access_methods", []):
        url = str(access_method.get("url", "")).strip()
        if url:
            return url
    return "https://example.invalid"


def _monitor_document_external_id(source_code: str, record: dict[str, Any]) -> str:
    raw_identifier = (
        record.get("document_id")
        or record.get("api_id")
        or record.get("entry_id")
        or record.get("entry_hash")
        or record.get("official_url")
    )
    identifier = str(raw_identifier or "").strip()
    if not identifier:
        identifier = sha256_bytes(json.dumps(record, sort_keys=True).encode("utf-8"))[:16]
    if identifier.startswith(f"{source_code}:"):
        return identifier
    return f"{source_code}:{identifier}"


def _monitor_publication_date(record: dict[str, Any], target_date: str) -> str:
    value = str(record.get("pub" + "lished_at") or "").strip()
    if not value:
        return target_date
    try:
        return date.fromisoformat(value[:10]).isoformat()
    except ValueError:
        pass
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return target_date
    return parsed.date().isoformat()


def _monitor_document_title(record: dict[str, Any], external_id: str) -> str:
    title = str(record.get("title") or "").strip()
    return title or f"Official monitor record {external_id}"


def _monitor_department(record: dict[str, Any]) -> str | None:
    for key in ("department", "issuing_authority", "agency"):
        value = str(record.get(key) or "").strip()
        if value:
            return value
    title = str(record.get("title") or "").strip()
    if ":" in title:
        prefix = title.split(":", 1)[0].strip()
        if 2 <= len(prefix) <= 80 and prefix.upper() == prefix:
            return prefix
    summary = str(record.get("summary") or "").strip()
    if "<" not in summary and ">" not in summary and len(summary) <= 180 and " - " in summary:
        return summary.rsplit(" - ", 1)[-1].strip() or None
    return None


def _monitor_section(record: dict[str, Any]) -> str | None:
    for key in ("section", "category"):
        value = str(record.get(key) or "").strip()
        if value:
            return value
    summary = str(record.get("summary") or "").strip()
    if "<" in summary or ">" in summary:
        return None
    if len(summary) <= 180 and " - " in summary:
        return summary.split(" - ", 1)[0].strip() or None
    return summary or None


def _monitor_document_type(record: dict[str, Any], monitor_kind: str) -> str:
    explicit = str(record.get("document_type") or "").strip()
    return explicit or f"{monitor_kind}_monitor_record"


def _monitor_url(record: dict[str, Any], url_type: str) -> str | None:
    official_url = str(record.get("official_url") or "").strip()
    if not official_url:
        return None
    lower_url = official_url.lower()
    if url_type == "pdf":
        return official_url if ".pdf" in lower_url or "pdf" in lower_url.split("?")[0] else None
    if url_type == "xml":
        return official_url if ".xml" in lower_url or "format=xml" in lower_url else None
    if url_type == "html":
        if _monitor_url(record, "pdf") or _monitor_url(record, "xml"):
            return None
        return official_url
    return None


def _open_repository(db_path: str) -> OfficialSourcesRepository:
    connection = connect(db_path)
    initialize_database(connection)
    repository = OfficialSourcesRepository(connection)
    repository.ensure_official_source_boe()
    return repository


def _run_db_command(
    args: argparse.Namespace,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    db_command = args.db_command
    db_path = args.db_path
    if db_command == "backup":
        verification_flags = [args.quick_check, args.full_check, args.no_verify]
        if sum(1 for enabled in verification_flags if enabled) > 1:
            print(
                "--quick-check, --full-check, and --no-verify cannot be used together",
                file=stderr,
            )
            return 2
        verification_mode = "quick_check"
        if args.full_check:
            verification_mode = "full_check"
        elif args.no_verify:
            verification_mode = "none"
        try:
            result = backup_sqlite_database(
                db_path,
                args.output,
                force=args.force,
                verification_mode=verification_mode,
                min_size_bytes=args.min_size_bytes,
            )
        except SQLiteBackupError as exc:
            print(str(exc), file=stderr)
            return 1
        except Exception as exc:
            print(f"db backup failed: {exc}", file=stderr)
            return 1
        print(
            " ".join(
                [
                    f"database_path={result.source_path}",
                    f"backup_path={result.output_path}",
                    f"pages={result.page_count}",
                    f"verification={result.verification_mode}",
                    f"source_check={result.source_check}",
                    f"backup_check={result.backup_check}",
                    f"size_bytes={result.size_bytes}",
                    "status=success",
                ]
            ),
            file=stdout,
        )
        return 0
    try:
        _validate_database_path(db_path)
        connection = connect(db_path)
    except Exception as exc:
        print(str(exc), file=stderr)
        return 2
    runner = MigrationRunner()
    if db_command == "status":
        try:
            result = runner.status(connection)
        except MigrationChecksumError as exc:
            print(str(exc), file=stderr)
            return 1
        status = "up_to_date" if not result.pending_versions else "pending"
        pragmas = sqlite_runtime_pragmas(connection)
        print(
            " ".join(
                [
                    f"database_path={db_path}",
                    f"current_version={result.current_version}",
                    f"latest_version={result.latest_version}",
                    f"pending_migrations={len(result.pending_versions)}",
                    f"journal_mode={pragmas['journal_mode']}",
                    f"synchronous={pragmas['synchronous']}",
                    f"status={status}",
                ]
            ),
            file=stdout,
        )
        return 0
    if db_command == "migrate":
        try:
            result = runner.migrate(connection)
        except MigrationChecksumError as exc:
            print(str(exc), file=stderr)
            return 1
        except Exception as exc:
            print(f"db migrate failed: {exc}", file=stderr)
            return 1
        status = "up_to_date" if not result.applied_versions else "migrated"
        applied = ",".join(str(version) for version in result.applied_versions) or "none"
        print(
            " ".join(
                [
                    f"database_path={db_path}",
                    f"current_version={result.current_version}",
                    f"latest_version={result.latest_version}",
                    f"applied_migrations={applied}",
                    f"status={status}",
                ]
            ),
            file=stdout,
        )
        return 0
    if db_command == "validate":
        result = validate_database(connection)
        status = "valid" if result.valid else "invalid"
        print(
            " ".join(
                [
                    f"database_path={db_path}",
                    f"current_version={result.current_version}",
                    f"latest_version={result.latest_version}",
                    f"status={status}",
                ]
            ),
            file=stdout,
        )
        for problem in result.problems:
            print(problem, file=stderr)
        return 0 if result.valid else 1
    print(f"Unknown db command: {db_command}", file=stderr)
    return 2


def _validate_database_path(db_path: str) -> None:
    path = Path(db_path)
    if path.exists() and path.is_dir():
        raise ValueError("Database path points to a directory")
    if path.parent and not path.parent.exists():
        raise ValueError(f"Database parent directory does not exist: {path.parent}")


def _run_ingest(
    repository: OfficialSourcesRepository,
    target_date: str,
    summary_fetcher,
    stdout: TextIO,
) -> int:
    run_record = ingest_boe_summary(
        repository,
        target_date=target_date,
        fetcher=summary_fetcher,
    )
    print(
        " ".join(
            [
                f"status={run_record['status']}",
                f"documents_fetched={run_record['documents_fetched']}",
                f"documents_new={run_record['documents_new']}",
                f"documents_updated={run_record['documents_updated']}",
                f"retry_count={run_record['retry_count']}",
                f"throttle_triggered={run_record['throttle_triggered']}",
                f"last_http_status={_status_value(run_record['last_http_status'])}",
            ]
        ),
        file=stdout,
    )
    return 0 if run_record["status"] in {"success", NO_PUBLICATION_STATUS} else 1


def _run_ingest_boja(
    repository: OfficialSourcesRepository,
    args: argparse.Namespace,
    fetcher,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    try:
        target_date = resolve_boja_target_date(args.date)
    except ValueError as exc:
        print(str(exc), file=stderr)
        return 2
    print(
        f"command_started={args.command} source_code=BOJA target_date={target_date}",
        file=stdout,
    )
    run_record = ingest_boja_date(repository, target_date=target_date, fetcher=fetcher)
    print(
        " ".join(
            [
                f"status={run_record['status']}",
                f"pages_fetched={run_record.get('pages_fetched', 0)}",
                f"pagination_complete={_bool_token(run_record.get('pagination_complete'))}",
                f"documents_fetched={run_record['documents_fetched']}",
                f"documents_new={run_record['documents_new']}",
                f"documents_updated={run_record['documents_updated']}",
                f"retry_count={run_record['retry_count']}",
                f"throttle_triggered={run_record['throttle_triggered']}",
                f"last_http_status={_status_value(run_record['last_http_status'])}",
            ]
        ),
        file=stdout,
    )
    return 0 if run_record["status"] in {"success", NO_PUBLICATION_STATUS} else 1


def _run_ingest_bocm(
    repository: OfficialSourcesRepository,
    args: argparse.Namespace,
    fetcher,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    try:
        target_date = resolve_bocm_target_date(args.date)
    except ValueError as exc:
        print(str(exc), file=stderr)
        return 2
    print(
        f"command_started={args.command} source_code=BOCM target_date={target_date}",
        file=stdout,
    )
    run_record = ingest_bocm_date(repository, target_date=target_date, fetcher=fetcher)
    print(
        " ".join(
            [
                f"status={run_record['status']}",
                f"issue_identifier={run_record.get('issue_identifier') or 'none'}",
                f"documents_fetched={run_record['documents_fetched']}",
                f"documents_new={run_record['documents_new']}",
                f"documents_updated={run_record['documents_updated']}",
                f"retry_count={run_record['retry_count']}",
                f"throttle_triggered={run_record['throttle_triggered']}",
                f"last_http_status={_status_value(run_record['last_http_status'])}",
                f"source_snapshot_hash={run_record.get('source_snapshot_hash') or 'none'}",
            ]
            + (
                [f"error_message={_compact_token(run_record['error_message'])}"]
                if run_record.get("error_message")
                else []
            )
        ),
        file=stdout,
    )
    return 0 if run_record["status"] in {"success", NO_PUBLICATION_STATUS} else 1


def _run_ingest_dogv(
    repository: OfficialSourcesRepository,
    args: argparse.Namespace,
    fetcher,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    try:
        target_date = resolve_dogv_target_date(args.date)
    except ValueError as exc:
        print(str(exc), file=stderr)
        return 2
    print(
        f"command_started={args.command} source_code=DOGV target_date={target_date}",
        file=stdout,
    )
    run_record = ingest_dogv_date(repository, target_date=target_date, fetcher=fetcher)
    print(
        " ".join(
            [
                f"status={run_record['status']}",
                f"issue_identifier={run_record.get('issue_identifier') or 'none'}",
                f"documents_fetched={run_record['documents_fetched']}",
                f"documents_new={run_record['documents_new']}",
                f"documents_updated={run_record['documents_updated']}",
                f"retry_count={run_record['retry_count']}",
                f"throttle_triggered={run_record['throttle_triggered']}",
                f"last_http_status={_status_value(run_record['last_http_status'])}",
                f"source_snapshot_hash={run_record.get('source_snapshot_hash') or 'none'}",
            ]
            + (
                [f"error_message={_compact_token(run_record['error_message'])}"]
                if run_record.get("error_message")
                else []
            )
        ),
        file=stdout,
    )
    return 0 if run_record["status"] in {"success", NO_PUBLICATION_STATUS} else 1


def _run_ingest_dogc(
    repository: OfficialSourcesRepository,
    args: argparse.Namespace,
    fetcher,
    document_fetcher,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    try:
        target_date = resolve_dogc_target_date(args.date)
    except ValueError as exc:
        print(str(exc), file=stderr)
        return 2
    print(
        f"command_started={args.command} source_code=DOGC target_date={target_date}",
        file=stdout,
    )
    run_record = ingest_dogc_date(
        repository,
        target_date=target_date,
        fetcher=fetcher,
        document_fetcher=document_fetcher,
    )
    print(
        " ".join(
            [
                f"status={run_record['status']}",
                f"issue_identifier={run_record.get('issue_identifier') or 'none'}",
                f"documents_fetched={run_record['documents_fetched']}",
                f"documents_new={run_record['documents_new']}",
                f"documents_updated={run_record['documents_updated']}",
                f"retry_count={run_record['retry_count']}",
                f"throttle_triggered={run_record['throttle_triggered']}",
                f"last_http_status={_status_value(run_record['last_http_status'])}",
                f"source_snapshot_hash={run_record.get('source_snapshot_hash') or 'none'}",
            ]
            + (
                [f"error_message={_compact_token(run_record['error_message'])}"]
                if run_record.get("error_message")
                else []
            )
        ),
        file=stdout,
    )
    return 0 if run_record["status"] in {"success", NO_PUBLICATION_STATUS} else 1


def _run_ingest_bocyl(
    repository: OfficialSourcesRepository,
    args: argparse.Namespace,
    fetcher,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    try:
        target_date = resolve_bocyl_target_date(args.date)
    except ValueError as exc:
        print(str(exc), file=stderr)
        return 2
    print(
        f"command_started={args.command} source_code=BOCYL target_date={target_date}",
        file=stdout,
    )
    run_record = ingest_bocyl_date(repository, target_date=target_date, fetcher=fetcher)
    print(
        " ".join(
            [
                f"status={run_record['status']}",
                f"issue_identifier={run_record.get('issue_identifier') or 'none'}",
                f"documents_fetched={run_record['documents_fetched']}",
                f"documents_new={run_record['documents_new']}",
                f"documents_updated={run_record['documents_updated']}",
                f"retry_count={run_record['retry_count']}",
                f"throttle_triggered={run_record['throttle_triggered']}",
                f"last_http_status={_status_value(run_record['last_http_status'])}",
                f"source_snapshot_hash={run_record.get('source_snapshot_hash') or 'none'}",
            ]
            + (
                [f"error_message={_compact_token(run_record['error_message'])}"]
                if run_record.get("error_message")
                else []
            )
        ),
        file=stdout,
    )
    return 0 if run_record["status"] in {"success", NO_PUBLICATION_STATUS} else 1


def _run_ingest_bopv(
    repository: OfficialSourcesRepository,
    args: argparse.Namespace,
    fetcher,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    try:
        target_date = resolve_bopv_target_date(args.date)
    except ValueError as exc:
        print(str(exc), file=stderr)
        return 2
    print(
        f"command_started={args.command} source_code=BOPV target_date={target_date}",
        file=stdout,
    )
    run_record = ingest_bopv_date(repository, target_date=target_date, fetcher=fetcher)
    print(
        " ".join(
            [
                f"status={run_record['status']}",
                f"issue_identifier={run_record.get('issue_identifier') or 'none'}",
                f"documents_fetched={run_record['documents_fetched']}",
                f"documents_new={run_record['documents_new']}",
                f"documents_updated={run_record['documents_updated']}",
                f"retry_count={run_record['retry_count']}",
                f"throttle_triggered={run_record['throttle_triggered']}",
                f"last_http_status={_status_value(run_record['last_http_status'])}",
                f"source_snapshot_hash={run_record.get('source_snapshot_hash') or 'none'}",
            ]
            + (
                [f"error_message={_compact_token(run_record['error_message'])}"]
                if run_record.get("error_message")
                else []
            )
        ),
        file=stdout,
    )
    return 0 if run_record["status"] in {"success", NO_PUBLICATION_STATUS} else 1


def _run_ingest_boa(
    repository: OfficialSourcesRepository,
    args: argparse.Namespace,
    fetcher,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    try:
        target_date = resolve_boa_target_date(args.date)
    except ValueError as exc:
        print(str(exc), file=stderr)
        return 2
    print(
        f"command_started={args.command} source_code=BOA target_date={target_date}",
        file=stdout,
    )
    run_record = ingest_boa_date(repository, target_date=target_date, fetcher=fetcher)
    print(
        " ".join(
            [
                f"status={run_record['status']}",
                f"issue_identifier={run_record.get('issue_identifier') or 'none'}",
                f"documents_fetched={run_record['documents_fetched']}",
                f"documents_new={run_record['documents_new']}",
                f"documents_updated={run_record['documents_updated']}",
                f"retry_count={run_record['retry_count']}",
                f"throttle_triggered={run_record['throttle_triggered']}",
                f"last_http_status={_status_value(run_record['last_http_status'])}",
                f"source_snapshot_hash={run_record.get('source_snapshot_hash') or 'none'}",
            ]
            + (
                [f"error_message={_compact_token(run_record['error_message'])}"]
                if run_record.get("error_message")
                else []
            )
        ),
        file=stdout,
    )
    return 0 if run_record["status"] in {"success", NO_PUBLICATION_STATUS} else 1


def _run_ingest_borm(
    repository: OfficialSourcesRepository,
    args: argparse.Namespace,
    fetcher,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    try:
        target_date = resolve_borm_target_date(args.date)
    except ValueError as exc:
        print(str(exc), file=stderr)
        return 2
    print(
        f"command_started={args.command} source_code=BORM target_date={target_date}",
        file=stdout,
    )
    run_record = ingest_borm_date(repository, target_date=target_date, fetcher=fetcher)
    print(
        " ".join(
            [
                f"status={run_record['status']}",
                f"issue_identifier={run_record.get('issue_identifier') or 'none'}",
                f"documents_fetched={run_record['documents_fetched']}",
                f"documents_new={run_record['documents_new']}",
                f"documents_updated={run_record['documents_updated']}",
                f"retry_count={run_record['retry_count']}",
                f"throttle_triggered={run_record['throttle_triggered']}",
                f"last_http_status={_status_value(run_record['last_http_status'])}",
                f"source_snapshot_hash={run_record.get('source_snapshot_hash') or 'none'}",
            ]
            + (
                [f"error_message={_compact_token(run_record['error_message'])}"]
                if run_record.get("error_message")
                else []
            )
        ),
        file=stdout,
    )
    return 0 if run_record["status"] in {"success", NO_PUBLICATION_STATUS} else 1


def _run_ingest_bdns_latest(
    repository: OfficialSourcesRepository,
    args: argparse.Namespace,
    fetcher,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    try:
        limit = validate_bdns_limit(args.limit, option_name="limit")
    except ValueError as exc:
        print(str(exc), file=stderr)
        return 2
    print(
        f"command_started={args.command} source_code=BDNS target=latest limit={limit}",
        file=stdout,
    )
    run_record = ingest_bdns_latest(repository, limit=limit, fetcher=fetcher)
    _print_bdns_run_record(run_record, stdout)
    return 0 if run_record["status"] == "success" else 1


def _run_ingest_bdns_call(
    repository: OfficialSourcesRepository,
    args: argparse.Namespace,
    fetcher,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    try:
        num_conv = validate_bdns_num_conv(args.num_conv)
    except ValueError as exc:
        print(str(exc), file=stderr)
        return 2
    print(
        f"command_started={args.command} source_code=BDNS num_conv={num_conv}",
        file=stdout,
    )
    run_record = ingest_bdns_call(repository, num_conv=num_conv, fetcher=fetcher)
    _print_bdns_run_record(run_record, stdout)
    return 0 if run_record["status"] == "success" else 1


def _run_preview_placsp_feed(
    repository: OfficialSourcesRepository,
    args: argparse.Namespace,
    fetcher,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    try:
        feed_type = validate_placsp_feed_type(args.feed_type)
        limit = validate_placsp_limit(args.limit)
        build_placsp_feed_url(feed_type)
    except ValueError as exc:
        print(str(exc), file=stderr)
        return 2
    print(
        f"command_started={args.command} source_code=PLACSP feed_type={feed_type} limit={limit}",
        file=stdout,
    )
    run_record = preview_placsp_feed(feed_type=feed_type, limit=limit, fetcher=fetcher)
    _print_placsp_run_record(run_record, stdout)
    return 0 if run_record["status"] == "success" else 1


def _run_ingest_placsp_feed(
    repository: OfficialSourcesRepository,
    args: argparse.Namespace,
    fetcher,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    try:
        feed_type = validate_placsp_feed_type(args.feed_type)
        limit = validate_placsp_limit(args.limit)
        build_placsp_feed_url(feed_type)
    except ValueError as exc:
        print(str(exc), file=stderr)
        return 2
    print(
        f"command_started={args.command} source_code=PLACSP feed_type={feed_type} limit={limit}",
        file=stdout,
    )
    run_record = ingest_placsp_feed(
        repository,
        feed_type=feed_type,
        limit=limit,
        fetcher=fetcher,
    )
    _print_placsp_run_record(run_record, stdout)
    return 0 if run_record["status"] == "success" else 1


def _run_search_bdns_calls(
    repository: OfficialSourcesRepository,
    args: argparse.Namespace,
    fetcher,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    try:
        date_from = parse_bdns_date_filter(args.date_from) if args.date_from else None
        date_to = parse_bdns_date_filter(args.date_to) if args.date_to else None
        page_size = validate_bdns_limit(args.page_size, option_name="page-size")
        max_pages = validate_bdns_max_pages(args.max_pages)
    except ValueError as exc:
        print(str(exc), file=stderr)
        return 2
    print(
        (
            f"command_started={args.command} source_code=BDNS "
            f"date_from={date_from or 'none'} date_to={date_to or 'none'} "
            f"page_size={page_size} max_pages={max_pages}"
        ),
        file=stdout,
    )
    run_record = search_bdns_calls(
        repository,
        date_from=date_from,
        date_to=date_to,
        page_size=page_size,
        max_pages=max_pages,
        fetcher=fetcher,
    )
    _print_bdns_run_record(run_record, stdout)
    return 0 if run_record["status"] == "success" else 1


def _run_preview_bdns_catalog(
    _repository: OfficialSourcesRepository,
    args: argparse.Namespace,
    fetcher,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    try:
        catalog_name = validate_bdns_catalog_name(args.catalog)
        build_bdns_catalog_url(
            catalog_name,
            vpd=args.vpd,
            id_admon=args.id_admon,
            ambito=args.ambito,
        )
    except ValueError as exc:
        print(str(exc), file=stderr)
        return 2
    print(
        f"command_started={args.command} source_code=BDNS catalog={catalog_name}",
        file=stdout,
    )
    run_record = preview_bdns_catalog(
        catalog_name,
        fetcher=fetcher,
        vpd=args.vpd,
        id_admon=args.id_admon,
        ambito=args.ambito,
    )
    _print_bdns_run_record(run_record, stdout)
    return 0 if run_record["status"] == "success" else 1


def _run_ingest_bdns_catalog(
    repository: OfficialSourcesRepository,
    args: argparse.Namespace,
    fetcher,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    try:
        catalog_name = validate_bdns_catalog_name(args.catalog)
        build_bdns_catalog_url(
            catalog_name,
            vpd=args.vpd,
            id_admon=args.id_admon,
            ambito=args.ambito,
        )
    except ValueError as exc:
        print(str(exc), file=stderr)
        return 2
    print(
        f"command_started={args.command} source_code=BDNS catalog={catalog_name}",
        file=stdout,
    )
    run_record = ingest_bdns_catalog(
        repository,
        catalog_name,
        fetcher=fetcher,
        vpd=args.vpd,
        id_admon=args.id_admon,
        ambito=args.ambito,
    )
    _print_bdns_run_record(run_record, stdout)
    return 0 if run_record["status"] == "success" else 1


def _run_export_bdns_grants(
    repository: OfficialSourcesRepository,
    args: argparse.Namespace,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    if args.limit is not None and args.limit < 1:
        print("limit must be at least 1.", file=stderr)
        return 2
    output_path = Path(args.output)
    print("command_started=export-bdns-grants source_code=BDNS", file=stdout)
    try:
        records = [
            _bdns_grant_export_record(document)
            for document in repository.list_bdns_grant_call_documents(limit=args.limit)
        ]
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8", newline="\n") as handle:
            for record in records:
                handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    except Exception as exc:
        print(f"export-bdns-grants failed: {exc}", file=stderr)
        return 1
    print(f"output_path={output_path} records_exported={len(records)}", file=stdout)
    return 0


def _run_export_bdns_business_grants(
    repository: OfficialSourcesRepository,
    args: argparse.Namespace,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    validation_error = _validate_business_export_args(args.min_score, args.limit)
    if validation_error:
        print(validation_error, file=stderr)
        return 2
    output_path = Path(args.output)
    print(
        (
            "command_started=export-bdns-business-grants source_code=BDNS "
            f"min_score={args.min_score}"
        ),
        file=stdout,
    )
    try:
        records = _bdns_business_grant_records(
            repository,
            min_score=args.min_score,
            limit=args.limit,
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8", newline="\n") as handle:
            for record in records:
                handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    except Exception as exc:
        print(f"export-bdns-business-grants failed: {exc}", file=stderr)
        return 1
    print(f"output_path={output_path} records_exported={len(records)}", file=stdout)
    return 0


def _run_export_bdns_business_dashboard(
    repository: OfficialSourcesRepository,
    args: argparse.Namespace,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    validation_error = _validate_business_export_args(args.min_score, args.limit)
    if validation_error:
        print(validation_error, file=stderr)
        return 2
    output_path = Path(args.output)
    print(
        (
            "command_started=export-bdns-business-dashboard source_code=BDNS "
            f"min_score={args.min_score}"
        ),
        file=stdout,
    )
    try:
        records = _bdns_business_grant_records(
            repository,
            min_score=args.min_score,
            limit=args.limit,
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            _render_bdns_business_dashboard(records, min_score=args.min_score),
            encoding="utf-8",
            newline="\n",
        )
    except Exception as exc:
        print(f"export-bdns-business-dashboard failed: {exc}", file=stderr)
        return 1
    print(f"output_path={output_path} records_rendered={len(records)}", file=stdout)
    return 0


def _run_export_bdns_concessions(
    repository: OfficialSourcesRepository,
    args: argparse.Namespace,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    if args.limit is not None and args.limit < 1:
        print("limit must be at least 1.", file=stderr)
        return 2
    call_identifier = None
    if args.num_conv:
        try:
            call_identifier = f"BDNS:{validate_bdns_num_conv(args.num_conv)}"
        except ValueError as exc:
            print(str(exc), file=stderr)
            return 2
    output_path = Path(args.output)
    print(
        (
            "command_started=export-bdns-concessions source_code=BDNS "
            f"num_conv={args.num_conv or 'all'}"
        ),
        file=stdout,
    )
    try:
        records = [
            _bdns_concession_export_record(entry)
            for entry in repository.list_bdns_concession_entries(
                call_identifier=call_identifier,
                limit=args.limit,
            )
        ]
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8", newline="\n") as handle:
            for record in records:
                handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    except Exception as exc:
        print(f"export-bdns-concessions failed: {exc}", file=stderr)
        return 1
    print(f"output_path={output_path} records_exported={len(records)}", file=stdout)
    return 0


def _run_preview_bdns_concesiones(
    _repository: OfficialSourcesRepository,
    args: argparse.Namespace,
    fetcher,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    try:
        num_conv = validate_bdns_num_conv(args.num_conv)
        page_size = validate_bdns_limit(args.page_size, option_name="page-size")
        build_bdns_concessions_search_url(
            num_conv=num_conv,
            page_size=page_size,
            vpd=args.vpd,
        )
    except ValueError as exc:
        print(str(exc), file=stderr)
        return 2
    print(
        (
            f"command_started={args.command} source_code=BDNS num_conv={num_conv} "
            f"page_size={page_size}"
        ),
        file=stdout,
    )
    run_record = preview_bdns_concessions(
        num_conv=num_conv,
        page_size=page_size,
        fetcher=fetcher,
        vpd=args.vpd,
        include_beneficiary_fields=args.include_beneficiary_fields,
    )
    _print_bdns_run_record(run_record, stdout)
    return 0 if run_record["status"] == "success" else 1


def _run_ingest_bdns_concesiones(
    repository: OfficialSourcesRepository,
    args: argparse.Namespace,
    fetcher,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    if not args.num_conv:
        print(
            "num-conv is required; global BDNS concesiones ingestion is disabled.",
            file=stderr,
        )
        return 2
    try:
        num_conv = validate_bdns_num_conv(args.num_conv)
        page_size = validate_bdns_limit(args.page_size, option_name="page-size")
        max_pages = validate_bdns_max_pages(args.max_pages)
        build_bdns_concessions_search_url(
            num_conv=num_conv,
            page_size=page_size,
            vpd=args.vpd,
        )
    except ValueError as exc:
        print(str(exc), file=stderr)
        return 2
    print(
        (
            f"command_started={args.command} source_code=BDNS num_conv={num_conv} "
            f"page_size={page_size} max_pages={max_pages} "
            f"include_beneficiary_fields={_bool_token(args.include_beneficiary_fields)}"
        ),
        file=stdout,
    )
    run_record = ingest_bdns_concessions(
        repository,
        num_conv=num_conv,
        page_size=page_size,
        max_pages=max_pages,
        fetcher=fetcher,
        vpd=args.vpd,
        include_beneficiary_fields=args.include_beneficiary_fields,
    )
    _print_bdns_run_record(run_record, stdout)
    return 0 if run_record["status"] == "success" else 1


def _bdns_grant_export_record(document: dict[str, Any]) -> dict[str, Any]:
    raw_metadata = json.loads(document["raw_metadata_json"] or "{}")
    return {
        "source_code": "BDNS",
        "external_id": document["external_id"],
        "official_identifier": document["external_id"],
        "publication_date": document["publication_date"],
        "title": document["title"],
        "department": document["department"],
        "section": document["section"],
        "document_type": document["document_type"],
        "official_url": document["url_html"],
        "bdns_code": raw_metadata.get("bdns_code"),
        "bdns_internal_id": raw_metadata.get("bdns_internal_id"),
        "registration_date": raw_metadata.get("registration_date"),
        "application_start_date": raw_metadata.get("application_start_date"),
        "application_end_date": raw_metadata.get("application_end_date"),
        "budget": raw_metadata.get("budget"),
        "beneficiary_type": raw_metadata.get("beneficiary_type") or [],
        "instrument_type": raw_metadata.get("instrument_type") or [],
        "sector_activity": raw_metadata.get("sector_activity") or [],
        "territorial_scope": raw_metadata.get("territorial_scope") or [],
        "catalog_enrichment": raw_metadata.get("catalog_enrichment") or {},
        "document_metadata": raw_metadata.get("document_metadata") or [],
        "announcement_metadata": raw_metadata.get("announcement_metadata") or [],
        "application_url": raw_metadata.get("application_url"),
        "base_regulation_url": raw_metadata.get("base_regulation_url"),
        "source_snapshot_hash": raw_metadata.get("detail_api_sha256"),
        "export_schema": "bdns_grant_call_v1",
    }


def _bdns_business_grant_records(
    repository: OfficialSourcesRepository,
    *,
    min_score: float,
    limit: int | None,
) -> list[dict[str, Any]]:
    documents = repository.list_bdns_grant_call_documents(limit=None)
    return filter_bdns_business_grants(documents, min_score=min_score, limit=limit)


def _validate_business_export_args(min_score: float, limit: int | None) -> str | None:
    if min_score < 0 or min_score > 1:
        return "min-score must be between 0 and 1."
    if limit is not None and limit < 1:
        return "limit must be at least 1."
    return None


def _render_bdns_business_dashboard(records: list[dict[str, Any]], *, min_score: float) -> str:
    rows = "\n".join(_render_bdns_business_row(record) for record in records)
    data_json = html.escape(json.dumps(records, ensure_ascii=False), quote=False)
    if records:
        content = (
            "<table><thead><tr><th>Score</th><th>Convocatoria</th><th>Plazo</th>"
            "<th>Presupuesto</th><th>Razones</th></tr></thead><tbody>"
            f"{rows}</tbody></table>"
        )
    else:
        content = '<div class="empty">No hay convocatorias BDNS por encima del umbral.</div>'
    return f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>BDNS Business Grants Radar</title>
  <style>
    body {{
      font-family: system-ui, -apple-system, Segoe UI, sans-serif;
      margin: 32px;
      color: #17202a;
    }}
    header {{ border-bottom: 1px solid #ccd3dc; margin-bottom: 24px; padding-bottom: 16px; }}
    h1 {{ font-size: 28px; margin: 0 0 8px; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{
      border-bottom: 1px solid #e2e6ea;
      padding: 10px;
      text-align: left;
      vertical-align: top;
    }}
    th {{ font-size: 12px; text-transform: uppercase; color: #52606d; }}
    .score {{ font-weight: 700; }}
    .reasons {{ font-size: 12px; color: #52606d; }}
    .empty {{ padding: 24px; background: #f6f8fa; border: 1px solid #e2e6ea; }}
  </style>
</head>
<body>
  <header>
    <h1>BDNS Business Grants Radar</h1>
    <div>Perfil: business_grants · umbral minimo: {min_score:.2f} · registros: {len(records)}</div>
  </header>
  <main>
    {content}
  </main>
  <script type="application/json" id="bdns-business-grants-data">{data_json}</script>
</body>
</html>
"""


def _render_bdns_business_row(record: dict[str, Any]) -> str:
    reasons = ", ".join(record["business_relevance_reasons"])
    url = record["official_url"] or "#"
    return (
        "<tr>"
        f'<td class="score">{record["business_relevance_score"]:.2f}</td>'
        f'<td><a href="{html.escape(url)}">{html.escape(record["official_identifier"])}</a><br>'
        f"{html.escape(record['title'])}</td>"
        f"<td>{html.escape(str(record['application_end_date'] or ''))}</td>"
        f"<td>{html.escape(str(record['budget'] or ''))}</td>"
        f'<td class="reasons">{html.escape(reasons)}</td>'
        "</tr>"
    )


def _bdns_concession_export_record(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_code": "BDNS",
        "external_id": entry["external_id"],
        "concession_code": entry["concession_code"],
        "call_identifier": entry["call_identifier"],
        "call_code": entry["call_code"],
        "call_internal_id": entry["call_internal_id"],
        "concession_date": entry["concession_date"],
        "registration_date": entry["registration_date"],
        "amount": entry["amount"],
        "aid_equivalent": entry["aid_equivalent"],
        "instrument": entry["instrument"],
        "department": entry["department"],
        "section": entry["section"],
        "beneficiary_name": entry["beneficiary_name"],
        "beneficiary_person_id": entry["beneficiary_person_id"],
        "base_regulation_url": entry["base_regulation_url"],
        "source_url": entry["source_url"],
        "source_snapshot_hash": entry["source_snapshot_hash"],
        "content_hash": entry["content_hash"],
        "first_seen_at": entry["first_seen_at"],
        "last_seen_at": entry["last_seen_at"],
        "export_schema": "bdns_concession_v1",
    }


def _print_bdns_run_record(run_record: dict, stdout: TextIO) -> None:
    sample_identifiers = run_record.get("sample_identifiers") or []
    print(
        " ".join(
            [
                f"status={run_record['status']}",
                f"bdns_result={run_record.get('bdns_result') or run_record['status']}",
                f"official_identifier={run_record.get('official_identifier') or 'none'}",
                f"catalog_name={run_record.get('catalog_name') or 'none'}",
                f"entry_count={run_record.get('entry_count', 0)}",
                f"documents_fetched={run_record['documents_fetched']}",
                f"documents_new={run_record['documents_new']}",
                f"documents_updated={run_record['documents_updated']}",
                f"page_count={run_record.get('page_count', 0)}",
                "pagination_limit_reached="
                f"{_bool_token(run_record.get('pagination_limit_reached'))}",
                "sample_identifiers="
                f"{','.join(sample_identifiers) if sample_identifiers else 'none'}",
                f"retry_count={run_record['retry_count']}",
                f"throttle_triggered={run_record['throttle_triggered']}",
                f"last_http_status={_status_value(run_record['last_http_status'])}",
                f"source_snapshot_hash={run_record.get('source_snapshot_hash') or 'none'}",
            ]
            + (
                [f"error_message={_compact_token(run_record['error_message'])}"]
                if run_record.get("error_message")
                else []
            )
        ),
        file=stdout,
    )


def _print_placsp_run_record(run_record: dict, stdout: TextIO) -> None:
    sample_identifiers = run_record.get("sample_identifiers") or []
    print(
        " ".join(
            [
                f"status={run_record['status']}",
                f"placsp_result={run_record.get('placsp_result') or run_record['status']}",
                f"entry_count={run_record.get('entry_count', run_record['documents_fetched'])}",
                f"deleted_entry_count={run_record.get('deleted_entry_count', 0)}",
                f"documents_fetched={run_record['documents_fetched']}",
                f"documents_new={run_record['documents_new']}",
                f"documents_updated={run_record['documents_updated']}",
                "sample_identifiers="
                f"{','.join(sample_identifiers) if sample_identifiers else 'none'}",
                f"retry_count={run_record['retry_count']}",
                f"throttle_triggered={run_record['throttle_triggered']}",
                f"last_http_status={_status_value(run_record['last_http_status'])}",
                f"source_snapshot_hash={run_record.get('source_snapshot_hash') or 'none'}",
                f"next_url={run_record.get('next_url') or 'none'}",
            ]
            + (
                [f"error_message={_compact_token(run_record['error_message'])}"]
                if run_record.get("error_message")
                else []
            )
        ),
        file=stdout,
    )


def _run_enrich_boja_evidence_urls(
    repository: OfficialSourcesRepository,
    args: argparse.Namespace,
    fetcher,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    try:
        candidate_ids = _parse_id_list(args.candidate_ids, option_name="--candidate-ids")
        document_ids = _parse_id_list(args.document_ids, option_name="--document-ids")
        result = enrich_boja_evidence_urls(
            repository,
            candidate_ids=candidate_ids,
            document_ids=document_ids,
            fetcher=fetcher,
        )
    except ValueError as exc:
        print(str(exc), file=stderr)
        return 2
    print("command_started=enrich-boja-evidence-urls source_code=BOJA target=scoped", file=stdout)
    print(_format_counts(result), file=stdout)
    return 0 if result["failed"] == 0 else 1


def _parse_artifact_types(value: str, *, source_code: str = "BOE") -> list[str]:
    artifact_types = [item.strip() for item in value.split(",") if item.strip()]
    supported = _artifact_fields_for_source(source_code)
    unsupported = sorted(set(artifact_types) - set(supported))
    if unsupported:
        raise BOEArtifactDownloadError(
            f"Unsupported {source_code} artifact types: {', '.join(unsupported)}"
        )
    return artifact_types


def _validate_dogv_download_args(args: argparse.Namespace) -> str | None:
    if args.source != "DOGV":
        return None
    if args.types != "pdf":
        return "DOGV artifact downloads require --types pdf"
    if not args.candidate_ids:
        return "DOGV artifact downloads require --candidate-ids"
    if args.document_ids:
        return "DOGV artifact downloads require --candidate-ids; --document-ids is not supported"
    try:
        candidate_ids = _parse_id_list(args.candidate_ids, option_name="--candidate-ids")
    except ValueError as exc:
        return str(exc)
    if len(candidate_ids) > 10:
        return "DOGV artifact downloads are limited to 10 candidate IDs"
    return None


def _validate_bocyl_download_args(args: argparse.Namespace) -> str | None:
    if args.source != "BOCYL":
        return None
    if not args.candidate_ids:
        return "BOCYL artifact downloads require --candidate-ids"
    if args.document_ids:
        return "BOCYL artifact downloads require --candidate-ids; --document-ids is not supported"
    try:
        candidate_ids = _parse_id_list(args.candidate_ids, option_name="--candidate-ids")
    except ValueError as exc:
        return str(exc)
    if len(candidate_ids) > 10:
        return "BOCYL artifact downloads are limited to 10 candidate IDs"
    return None


def _validate_borm_download_args(args: argparse.Namespace) -> str | None:
    if args.source != "BORM":
        return None
    if args.types != "pdf":
        return "BORM artifact downloads require --types pdf"
    if args.document_ids:
        return "BORM artifact downloads require --candidate-ids; --document-ids is not supported"
    if not args.candidate_ids:
        return "BORM artifact downloads require --candidate-ids"
    try:
        candidate_ids = _parse_id_list(args.candidate_ids, option_name="--candidate-ids")
    except ValueError as exc:
        return str(exc)
    if len(candidate_ids) > 12:
        return "BORM artifact downloads are limited to 12 candidate IDs"
    return None


def _parse_id_list(value: str | None, *, option_name: str) -> list[int]:
    if not value:
        return []
    try:
        ids = [int(item.strip()) for item in value.split(",") if item.strip()]
    except ValueError as exc:
        raise ValueError(f"{option_name} must be a comma-separated list of integers") from exc
    if not ids or any(item <= 0 for item in ids):
        raise ValueError(f"{option_name} must contain positive integer IDs")
    return list(dict.fromkeys(ids))


def _resolve_download_selection(
    repository: OfficialSourcesRepository,
    args: argparse.Namespace,
    *,
    source_code: str = "BOE",
) -> tuple[str | None, list[dict[str, Any]]]:
    candidate_ids = _parse_id_list(args.candidate_ids, option_name="--candidate-ids")
    document_ids = _parse_id_list(args.document_ids, option_name="--document-ids")
    scoped = bool(candidate_ids or document_ids)
    if args.date and scoped:
        raise ValueError("--date cannot be combined with --candidate-ids or --document-ids")
    if candidate_ids and document_ids:
        raise ValueError("--candidate-ids cannot be combined with --document-ids")
    if candidate_ids:
        documents = repository.list_documents_by_candidate_ids(candidate_ids)
        if len(documents) != len(candidate_ids):
            raise ValueError("One or more --candidate-ids were not found")
        _ensure_documents_match_source(documents, source_code)
        return None, documents
    if document_ids:
        documents = repository.list_documents_by_ids(document_ids)
        if len(documents) != len(document_ids):
            raise ValueError("One or more --document-ids were not found")
        _ensure_documents_match_source(documents, source_code)
        return None, documents
    if not args.date:
        raise ValueError("--date, --candidate-ids, or --document-ids is required")
    target_date = resolve_target_date(args.date)
    documents = repository.search_documents(
        date_from=target_date,
        date_to=target_date,
        source_code=source_code,
        limit=100000,
    )
    _ensure_documents_match_source(documents, source_code)
    return target_date, documents


def _ensure_documents_match_source(documents: list[dict[str, Any]], source_code: str) -> None:
    mismatched = sorted(
        {
            str(document.get("source_code") or "unknown")
            for document in documents
            if document.get("source_code") != source_code
        }
    )
    if mismatched:
        raise ValueError(
            f"Selected documents must belong to source {source_code}; found {','.join(mismatched)}"
        )


def _run_download(
    repository: OfficialSourcesRepository,
    *,
    source_code: str,
    target_date: str | None,
    documents: list[dict[str, Any]],
    artifact_types: list[str],
    artifact_dir: Path,
    client: httpx.Client | None,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    latest_run = (
        repository.get_latest_ingestion_run(source_code, target_date)
        if target_date is not None
        else None
    )
    if latest_run and latest_run["status"] == NO_PUBLICATION_STATUS:
        print(
            _format_counts(
                {
                    "downloaded": 0,
                    "skipped": 0,
                    "changed": 0,
                    "failed": 0,
                    "retries": 0,
                    "status": NO_PUBLICATION_STATUS,
                    "last_http_status": _status_value(latest_run["last_http_status"]),
                }
            ),
            file=stdout,
        )
        return 0
    run_record = repository.create_ingestion_run(source_code=source_code, target_date=target_date)
    downloader = _artifact_downloader_for_source(
        source_code,
        repository,
        artifact_dir=artifact_dir,
        client=client,
    )
    counts = {
        "selected_documents": len(documents),
        "artifact_types": ",".join(artifact_types),
        "downloaded": 0,
        "skipped": 0,
        "changed": 0,
        "failed": 0,
        "missing_artifact_url": 0,
        "retries": 0,
        "throttle_events": 0,
    }
    http_status_counts: Counter[str] = Counter()
    for document in documents:
        for artifact_type in artifact_types:
            before = _file_hashes(repository, document["id"])
            try:
                result = downloader.download_document_artifacts(
                    external_id=document["external_id"],
                    artifact_types=[artifact_type],
                    ingestion_run_id=run_record["id"],
                )
            except Exception as exc:
                counts["failed"] += 1
                print(f"{document['external_id']} {artifact_type}: {exc}", file=stderr)
                continue
            if artifact_type not in result:
                counts["skipped"] += 1
                if not document[_artifact_url_field(source_code, artifact_type)]:
                    counts["missing_artifact_url"] += 1
                continue
            counts["downloaded"] += 1
            after = result[artifact_type]
            attempts = repository.list_artifact_download_attempts(document_id=document["id"])
            latest_attempt = attempts[-1] if attempts else None
            if latest_attempt:
                counts["retries"] += latest_attempt["retry_count"]
                counts["throttle_events"] += latest_attempt["throttle_triggered"]
                status_value = _status_value(latest_attempt["http_status"])
                http_status_counts[f"{artifact_type}:{status_value}"] += 1
            previous_hash = before.get((artifact_type, after["official_url"]))
            if previous_hash is not None and previous_hash != after["sha256"]:
                counts["changed"] += 1
    counts["http_status_summary"] = _format_counter(http_status_counts)
    status = "success" if counts["failed"] == 0 else "partial"
    repository.finish_ingestion_run(
        run_id=run_record["id"],
        status=status,
        documents_fetched=len(documents),
        documents_new=0,
        documents_updated=counts["downloaded"],
        error_message=None if counts["failed"] == 0 else "artifact download failures",
    )
    print(_format_counts(counts), file=stdout)
    return 0 if counts["failed"] == 0 and counts["changed"] == 0 else 1


def _artifact_downloader_for_source(
    source_code: str,
    repository: OfficialSourcesRepository,
    *,
    artifact_dir: Path,
    client: httpx.Client | None,
) -> BOEArtifactDownloader:
    if source_code == "BOJA":
        return BOJAArtifactDownloader(repository, cache_dir=artifact_dir, client=client)
    if source_code == "DOGV":
        return DOGVArtifactDownloader(repository, cache_dir=artifact_dir, client=client)
    if source_code == "BOCYL":
        return BOCYLArtifactDownloader(repository, cache_dir=artifact_dir, client=client)
    if source_code == "BORM":
        return BORMArtifactDownloader(repository, cache_dir=artifact_dir, client=client)
    return BOEArtifactDownloader(repository, cache_dir=artifact_dir, client=client)


def _artifact_url_field(source_code: str, artifact_type: str) -> str:
    fields = _artifact_fields_for_source(source_code)
    return fields[artifact_type][0]


def _artifact_fields_for_source(source_code: str) -> dict[str, tuple[str, str, str]]:
    if source_code == "BOJA":
        return BOJA_ARTIFACT_FIELDS
    if source_code == "DOGV":
        return DOGV_ARTIFACT_FIELDS
    if source_code == "BOCYL":
        return BOCYL_ARTIFACT_FIELDS
    if source_code == "BORM":
        return BORM_ARTIFACT_FIELDS
    return BOE_ARTIFACT_FIELDS


def _file_hashes(
    repository: OfficialSourcesRepository,
    document_id: int,
) -> dict[tuple[str, str], str]:
    return {
        (file_record["file_type"], file_record["official_url"]): file_record["sha256"]
        for file_record in repository.list_document_files(document_id)
    }


def _run_integrity_check(
    repository: OfficialSourcesRepository,
    target_date: str,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    counts = {"unchanged": 0, "changed": 0, "missing": 0, "non_local_metadata": 0}
    for file_record in repository.list_document_files_by_date(target_date):
        local_path = file_record["local_path"]
        if not local_path:
            counts["non_local_metadata"] += 1
            continue
        if not Path(local_path).exists():
            counts["missing"] += 1
            print(f"missing file_id={file_record['id']}", file=stderr)
            continue
        payload = Path(local_path).read_bytes()
        current_hash = sha256_bytes(payload)
        if current_hash == file_record["sha256"]:
            counts["unchanged"] += 1
        else:
            counts["changed"] += 1
        repository.upsert_document_file(
            document_id=file_record["document_id"],
            file_type=file_record["file_type"],
            official_url=file_record["official_url"],
            local_path=local_path,
            media_type=file_record["media_type"],
            payload=payload,
            source_snapshot_hash=current_hash,
            ingestion_run_id=None,
        )
    print(_format_counts(counts), file=stdout)
    return 0 if counts["changed"] == 0 and counts["missing"] == 0 else 1


def _run_status(repository: OfficialSourcesRepository, target_date: str, stdout: TextIO) -> int:
    summary_run = repository.get_latest_summary_ingestion_run("BOE", target_date)
    documents = repository.list_documents_by_date(target_date)
    files = repository.list_document_files_by_date(target_date)
    warnings = sum(1 for file_record in files if file_record["content_changed_at"])
    download_counts = repository.count_artifact_download_attempts_by_date(target_date)
    artifact_summary = repository.summarize_artifact_download_attempts_by_date(target_date)
    download_attempts = sum(download_counts.values())
    summary_status = summary_run["status"] if summary_run else "none"
    summary_last_http_status = _status_value(
        summary_run["last_http_status"] if summary_run else None
    )
    summary_retry_count = summary_run["retry_count"] if summary_run else 0
    summary_throttle_triggered = summary_run["throttle_triggered"] if summary_run else 0
    counts = {
        "ingestion_status": summary_status,
        "last_http_status": summary_last_http_status,
        "summary_ingestion_status": summary_status,
        "summary_last_http_status": summary_last_http_status,
        "summary_retry_count": summary_retry_count,
        "summary_throttle_triggered": summary_throttle_triggered,
        "documents": len(documents),
        "xml_files": _count_files(files, "xml"),
        "html_files": _count_files(files, "html"),
        "pdf_files": _count_files(files, "pdf"),
        "download_attempts": download_attempts,
        "download_success": download_counts["success"],
        "download_skipped": download_counts["skipped"],
        "download_changed": download_counts["changed"],
        "download_failed": download_counts["failed"],
        "artifact_download_attempts": download_attempts,
        "artifact_download_success": download_counts["success"],
        "artifact_download_skipped": download_counts["skipped"],
        "artifact_download_changed": download_counts["changed"],
        "artifact_download_failed": download_counts["failed"],
        "artifact_http_status_summary": artifact_summary["http_status_summary"],
        "artifact_retry_count": artifact_summary["retry_count"],
        "artifact_throttle_events": artifact_summary["throttle_events"],
        "integrity_warnings": warnings,
        "failed_downloads": download_counts["failed"],
    }
    print(_format_counts(counts), file=stdout)
    return 0


def _run_candidate_evidence_status(
    repository: OfficialSourcesRepository,
    args: argparse.Namespace,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    try:
        candidate_ids = _parse_id_list(args.candidate_ids, option_name="--candidate-ids")
    except ValueError as exc:
        print(str(exc), file=stderr)
        return 2
    has_date_filter = bool(args.date_from or args.date_to)
    if candidate_ids and has_date_filter:
        print("--candidate-ids cannot be combined with --date-from or --date-to", file=stderr)
        return 2
    if bool(args.date_from) != bool(args.date_to):
        print("--date-from and --date-to must be provided together", file=stderr)
        return 2
    if not candidate_ids and not has_date_filter:
        print("--candidate-ids or --date-from/--date-to is required", file=stderr)
        return 2
    if args.profile and args.project_key and args.profile != args.project_key:
        print("--profile and --project-key cannot select different project keys", file=stderr)
        return 2
    date_from = None
    date_to = None
    if has_date_filter:
        try:
            date_from = validate_boe_date(args.date_from).isoformat()
            date_to = validate_boe_date(args.date_to).isoformat()
        except ValueError as exc:
            print(str(exc), file=stderr)
            return 2
        if date_from > date_to:
            print("--date-from must be earlier than or equal to --date-to", file=stderr)
            return 2
    rows = repository.list_candidate_evidence_status(
        candidate_ids=candidate_ids or None,
        date_from=date_from,
        date_to=date_to,
        project_key=args.project_key or args.profile,
    )
    if candidate_ids and len(rows) != len(candidate_ids):
        print("One or more --candidate-ids were not found", file=stderr)
        return 2
    print(_format_counts({"candidates": len(rows)}), file=stdout)
    for row in rows:
        print("candidate_evidence " + _format_candidate_evidence_row(row), file=stdout)
    return 0


def _run_mark_candidate_evidence(
    repository: OfficialSourcesRepository,
    args: argparse.Namespace,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    if args.candidate_id <= 0:
        print("--candidate-id must be a positive integer", file=stderr)
        return 2
    try:
        review = repository.mark_candidate_evidence_review(
            source_candidate_id=args.candidate_id,
            evidence_label=args.evidence_label,
            evidence_review_status=args.evidence_review_status,
            evidence_notes=args.notes,
            selected_for_evidence=args.selected_for_evidence or None,
            selected_for_pdf=args.selected_for_pdf or None,
            manual_decision=args.manual_decision,
            manual_notes=args.manual_notes,
            needs_pdf=args.needs_pdf,
            downstream_project_fit=args.downstream_project_fit,
            reviewed_by=args.reviewed_by,
            reviewed_at=args.reviewed_at,
        )
    except (KeyError, ValueError) as exc:
        print(str(exc), file=stderr)
        return 2
    candidate = repository.get_source_candidate(args.candidate_id)
    assert candidate is not None
    print(
        _format_counts(
            {
                "candidate_id": args.candidate_id,
                "review_status": candidate["review_status"],
                "evidence_review_status": review["evidence_review_status"],
                "evidence_label": review["evidence_label"] or "none",
                "manual_decision": review["manual_decision"] or "none",
                "needs_pdf": review["needs_pdf"] or "none",
                "downstream_project_fit": review["downstream_project_fit"] or "none",
                "reviewed_by": review["reviewed_by"] or "none",
                "reviewed_at": review["reviewed_at"] or "none",
                "selected_for_evidence": _bool_token(review["selected_for_evidence"]),
                "selected_for_pdf": _bool_token(review["selected_for_pdf"]),
                "xml_available": _bool_token(review["xml_available"]),
                "html_available": _bool_token(review["html_available"]),
                "pdf_available": _bool_token(review["pdf_available"]),
                "integrity_warning": _bool_token(review["integrity_warning"]),
                "approved": "false",
            }
        ),
        file=stdout,
    )
    return 0


def _run_export_downstream_evidence(
    repository: OfficialSourcesRepository,
    args: argparse.Namespace,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    try:
        candidate_ids = _parse_id_list(args.candidate_ids, option_name="--candidate-ids")
    except ValueError as exc:
        print(str(exc), file=stderr)
        return 2
    try:
        paths = export_downstream_evidence_files(
            repository,
            candidate_ids,
            Path(args.output_dir),
        )
    except KeyError as exc:
        print(str(exc), file=stderr)
        return 2
    print(
        _format_counts(
            {
                "command": "export-downstream-evidence",
                "candidate_ids": ",".join(str(candidate_id) for candidate_id in candidate_ids),
                "files_written": len(paths),
                "output_dir": str(Path(args.output_dir)),
            }
        ),
        file=stdout,
    )
    for path in paths:
        print(f"exported_file={path}", file=stdout)
    return 0


def _run_ingest_range(
    repository: OfficialSourcesRepository,
    args: argparse.Namespace,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    try:
        date_from = validate_boe_date(args.date_from)
        date_to = validate_boe_date(args.date_to)
    except ValueError as exc:
        print(str(exc), file=stderr)
        return 2
    if date_from > date_to:
        print("--date-from must be earlier than or equal to --date-to", file=stderr)
        return 2
    days = (date_to - date_from).days + 1
    if args.max_days <= 0:
        print("--max-days must be greater than zero", file=stderr)
        return 2
    if days > args.max_days:
        print(f"Date range contains {days} days, exceeding --max-days={args.max_days}", file=stderr)
        return 2
    if days > 365 and not args.force:
        print("Date ranges above 365 days require --force", file=stderr)
        return 2
    if days > 365 and args.force and not args.confirm_large_range:
        print("Date ranges above 365 days require --confirm-large-range with --force", file=stderr)
        return 2

    base_policy = BOERequestPolicy.from_env()
    requests_per_second = 0 if args.sleep_seconds <= 0 else 1 / args.sleep_seconds
    client = BOEClient(
        request_policy=BOERequestPolicy(
            requests_per_second=requests_per_second,
            max_retries=base_policy.max_retries,
            backoff_base_seconds=base_policy.backoff_base_seconds,
            backoff_max_seconds=base_policy.backoff_max_seconds,
            jitter_seconds=base_policy.jitter_seconds,
        )
    )
    fetcher = _SharedBOEFetcher(client)
    counts = {"processed": 0, "skipped": 0, "success": 0, "no_publication": 0, "failed": 0}
    for current in _inclusive_dates(date_from, date_to):
        target_date = current.isoformat()
        existing = repository.get_latest_summary_ingestion_run("BOE", target_date)
        if (
            args.skip_existing
            and existing
            and existing["status"] in {"success", NO_PUBLICATION_STATUS}
        ):
            counts["skipped"] += 1
            continue
        run_record = ingest_boe_summary(repository, target_date=target_date, fetcher=fetcher)
        counts["processed"] += 1
        status = run_record["status"]
        if status == "success":
            counts["success"] += 1
        elif status == NO_PUBLICATION_STATUS:
            counts["no_publication"] += 1
            if not args.continue_on_no_publication:
                print(_format_counts({**counts, "stopped_on": target_date}), file=stdout)
                return 1
        else:
            counts["failed"] += 1
            if args.stop_on_error:
                print(_format_counts({**counts, "stopped_on": target_date}), file=stdout)
                return 1
    print(_format_counts({**counts, "days": days}), file=stdout)
    return 0 if counts["failed"] == 0 else 1


def _run_find_candidates(
    repository: OfficialSourcesRepository,
    args: argparse.Namespace,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    try:
        date_from = validate_boe_date(args.date_from).isoformat()
        date_to = validate_boe_date(args.date_to).isoformat()
    except ValueError as exc:
        print(str(exc), file=stderr)
        return 2
    if date_from > date_to:
        print("--date-from must be earlier than or equal to --date-to", file=stderr)
        return 2
    keywords = _candidate_keywords(args)
    if not keywords:
        print("--keywords or --profile must include at least one keyword", file=stderr)
        return 2
    if args.limit <= 0:
        print("--limit must be greater than zero", file=stderr)
        return 2
    dry_run = bool(args.dry_run or args.no_write)
    if args.write and dry_run:
        print("--write cannot be combined with --dry-run or --no-write", file=stderr)
        return 2
    if not args.write and not dry_run:
        print(
            "Use --dry-run/--no-write for preview or --write for explicit candidate creation",
            file=stderr,
        )
        return 2
    filters = _candidate_filters(args)
    documents = repository.search_documents(
        date_from=date_from,
        date_to=date_to,
        source_code=args.source,
        limit=100000,
    )
    excluded_by_section = 0
    excluded_by_department = 0
    excluded_by_keyword_rules = 0
    total_matches = 0
    matched_items: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for document in documents:
        matches = _candidate_keyword_matches(document, keywords, profile=args.profile)
        if not matches:
            continue
        total_matches += 1
        exclusion_reason = _candidate_exclusion_reason(document, matches, filters)
        if exclusion_reason == "section":
            excluded_by_section += 1
            continue
        if exclusion_reason == "department":
            excluded_by_department += 1
            continue
        if exclusion_reason == "keyword_rules":
            excluded_by_keyword_rules += 1
            continue
        matches = _candidate_evidence_metadata(document, matches, profile=args.profile)
        matched_items.append((document, matches))
    created = 0
    skipped_existing = 0
    if args.write:
        for document, matches in matched_items:
            if created >= args.limit:
                break
            if repository.source_candidate_exists(
                document_id=document["id"],
                project_key=args.project_key,
            ):
                skipped_existing += 1
                continue
            repository.create_source_candidate(
                document_id=document["id"],
                project_key=args.project_key,
                candidate_type=args.candidate_type,
                extraction_status="raw_detected",
                evidence_level="metadata_keyword_match",
                matched_fields=matches,
            )
            created += 1
    keyword_counts: Counter[str] = Counter()
    section_counts: Counter[str] = Counter()
    department_counts: Counter[str] = Counter()
    for document, matches in matched_items:
        keyword_counts.update(matches["keywords"])
        if document.get("section"):
            section_counts[_compact_token(document["section"])] += 1
        if document.get("department"):
            department_counts[_compact_token(document["department"])] += 1
    print(
        _format_counts(
            {
                "documents_scanned": len(documents),
                "source": args.source,
                "matches_total": total_matches,
                "matches_after_filters": len(matched_items),
                "documents_matched": len(matched_items),
                "candidates_created": created,
                "candidates_skipped_existing": skipped_existing,
                "review_status": "human_review_required",
                "write_mode": "dry_run" if dry_run else "write",
                "write_limit": args.limit if args.write else "none",
                "matches_by_keyword": _format_counter(keyword_counts),
                "matches_by_section": _format_counter(section_counts),
                "matches_by_department": _format_counter(department_counts),
                "excluded_by_section": excluded_by_section,
                "excluded_by_department": excluded_by_department,
                "excluded_by_keyword_rules": excluded_by_keyword_rules,
                "sample_count": min(len(matched_items), args.limit),
            }
        ),
        file=stdout,
    )
    for index, (document, matches) in enumerate(matched_items[: args.limit], start=1):
        print(
            "sample "
            + _format_counts(
                {
                    "index": index,
                    "date": document["publication_date"],
                    "publication_date": document["publication_date"],
                    "official_identifier": document["external_id"],
                    "external_id": document["external_id"],
                    "keywords": ",".join(matches["keywords"]),
                    "matched_keywords": ",".join(matches["keywords"]),
                    "section": _compact_token(document.get("section") or "none"),
                    "department": _compact_token(document.get("department") or "none"),
                    "score": matches["score"],
                    "score_reasons": ",".join(matches["score_reasons"]),
                    "official_url": _candidate_official_url(document),
                    "title": _quote_value(document.get("title") or ""),
                }
            ),
            file=stdout,
        )
    return 0


def _run_dry_run_opposition_alerts(
    repository: OfficialSourcesRepository,
    args: argparse.Namespace,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    try:
        date_from = validate_boe_date(args.date_from).isoformat()
        date_to = validate_boe_date(args.date_to).isoformat()
    except ValueError as exc:
        print(str(exc), file=stderr)
        return 2
    if date_from > date_to:
        print("--date-from must be earlier than or equal to --date-to", file=stderr)
        return 2
    if args.limit <= 0:
        print("--limit must be greater than zero", file=stderr)
        return 2
    try:
        source_codes = _parse_opposition_alert_sources(args.source)
    except ValueError as exc:
        print(str(exc), file=stderr)
        return 2

    documents: list[dict[str, Any]] = []
    source_names: dict[str, str] = {}
    for source_code in source_codes:
        source = repository.get_source_by_code(source_code)
        source_names[source_code] = source["name"]
        documents.extend(
            repository.search_documents(
                date_from=date_from,
                date_to=date_to,
                source_code=source_code,
                limit=100000,
            )
        )

    alerts: list[dict[str, Any]] = []
    excluded_by_rule = Counter()
    for document in documents:
        classification = _classify_opposition_alert(document)
        if not classification["matched"]:
            if classification["matched_rules"]:
                excluded_by_rule.update(classification["matched_rules"])
            continue
        alerts.append(
            _opposition_alert_record(
                document,
                source_name=source_names[document["source_code"]],
                classification=classification,
            )
        )
        if len(alerts) >= args.limit:
            break

    alerts_by_source = Counter(alert["source_code"] for alert in alerts)
    alerts_by_type = Counter(alert["alert_type"] for alert in alerts)
    alerts_by_scope = Counter(alert["alert_scope"] for alert in alerts)
    alerts_by_confidence = Counter(alert["confidence"] for alert in alerts)
    summary = {
        "mode": "dry_run",
        "grade": "alert-grade",
        "documents_scanned": len(documents),
        "alerts_found": len(alerts),
        "limit": args.limit,
        "date_from": date_from,
        "date_to": date_to,
        "sources": source_codes,
        "alerts_by_source": dict(sorted(alerts_by_source.items())),
        "alerts_by_type": dict(sorted(alerts_by_type.items())),
        "alerts_by_scope": dict(sorted(alerts_by_scope.items())),
        "alerts_by_confidence": dict(sorted(alerts_by_confidence.items())),
        "excluded_by_rule": dict(sorted(excluded_by_rule.items())),
        "writes": {
            "db": False,
            "source_candidates": False,
            "artifacts": False,
            "external_output": False,
        },
    }
    if args.format == "jsonl":
        print(json.dumps({"record_type": "summary", **summary}, sort_keys=True), file=stdout)
        for alert in alerts:
            print(json.dumps({"record_type": "alert", **alert}, sort_keys=True), file=stdout)
        return 0
    print(json.dumps({"summary": summary, "alerts": alerts}, indent=2, sort_keys=True), file=stdout)
    return 0


def _parse_opposition_alert_sources(value: str) -> list[str]:
    source_codes = [item.strip().upper() for item in value.split(",") if item.strip()]
    if not source_codes:
        raise ValueError("--source must include at least one source code")
    unsupported = [
        source_code
        for source_code in source_codes
        if source_code not in OPPOSITION_ALERT_SOURCE_CODES
    ]
    if unsupported:
        supported = ", ".join(OPPOSITION_ALERT_SOURCE_CODES)
        raise ValueError(
            f"Unsupported --source value(s): {', '.join(unsupported)}. Supported: {supported}"
        )
    return list(dict.fromkeys(source_codes))


OPPOSITION_ALERT_RULES: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    (
        "lista_definitiva",
        "lista_definitiva",
        ("lista definitiva", "relacion definitiva", "definitiva de aspirantes"),
    ),
    (
        "lista_provisional",
        "lista_provisional",
        ("lista provisional", "relacion provisional", "provisional de aspirantes"),
    ),
    (
        "fecha_examen",
        "fecha_examen",
        ("fecha de examen", "fecha del examen", "primer ejercicio", "lugar de celebracion"),
    ),
    (
        "subsanacion",
        "subsanacion",
        ("subsanacion", "subsanar", "plazo de subsanacion"),
    ),
    (
        "correccion",
        "correccion",
        ("correccion de errores", "correccion", "error material"),
    ),
    (
        "tribunal",
        "tribunal",
        ("tribunal calificador", "miembros del tribunal", "designacion del tribunal"),
    ),
    (
        "bolsa",
        "bolsa",
        ("bolsa de trabajo", "bolsa de empleo", "bolsa de empleo temporal"),
    ),
    (
        "nombramiento",
        "nombramiento",
        ("nombramiento", "nombramientos", "nombra"),
    ),
    (
        "convocatoria",
        "convocatoria",
        ("convocatoria", "se convoca", "proceso selectivo", "pruebas selectivas"),
    ),
    (
        "bases",
        "bases",
        ("bases reguladoras", "bases de la convocatoria", "bases especificas"),
    ),
    (
        "plazo",
        "plazo",
        ("plazo de presentacion", "plazo de solicitudes", "plazo para presentar"),
    ),
    (
        "adjudicacion",
        "adjudicacion",
        ("adjudicacion de destinos", "adjudicacion de puestos", "adjudican destinos"),
    ),
)
OPPOSITION_ALERT_BROAD_RULES: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    (
        "universidad_profesorado",
        "universidad_profesorado",
        (
            "profesorado permanente",
            "profesor ayudante doctor",
            "profesora agregada",
            "profesor titular",
            "cuerpos docentes universitarios",
            "profesor permanente laboral",
        ),
    ),
    (
        "libre_designacion",
        "libre_designacion",
        ("libre designacion",),
    ),
    (
        "provision_puestos",
        "provision_puestos",
        ("provision de puestos", "provision de puesto", "provision de un puesto"),
    ),
    (
        "concurso_meritos",
        "concurso_meritos",
        ("concurso de meritos",),
    ),
    (
        "ope",
        "ope",
        ("oferta publica de empleo", "ofertas publicas de empleo", "oferta de empleo publico"),
    ),
)
OPPOSITION_ALERT_PROCESS_CONTEXT = (
    "proceso selectivo",
    "oposicion",
    "oposiciones",
    "concurso-oposicion",
    "concurso oposicion",
    "pruebas selectivas",
    "personal funcionario",
    "personal laboral",
    "aspirantes",
    "admitidos",
    "excluidos",
    "empleo publico",
    "bolsa de trabajo",
    "bolsa de empleo",
    "plazas",
    "cuerpo",
    "escala",
    "subescala",
    "turno libre",
    "promocion interna",
    "tribunal calificador",
    "fecha de examen",
)
OPPOSITION_ALERT_NOISE_TERMS = (
    "beca",
    "becas",
    "ayuda",
    "ayudas",
    "contratacion publica",
    "contratacion",
    "licitacion",
    "contrato",
    "contrato de servicios",
    "expropiacion",
    "expropiaciones",
    "levantamiento de actas",
    "actas previas",
    "ocupacion",
    "informacion publica",
    "subvencion",
    "subvenciones",
    "premios",
    "convenio",
    "convenios",
    "urbanismo",
    "medio ambiente",
    "autorizacion ambiental",
    "procedimiento nacional de oposicion",
)
OPPOSITION_ALERT_EXCLUDING_NOISE_TERMS = (
    "beca",
    "becas",
    "ayuda",
    "ayudas",
    "contratacion publica",
    "contratacion",
    "licitacion",
    "contrato",
    "contrato de servicios",
    "expropiacion",
    "expropiaciones",
    "levantamiento de actas",
    "actas previas",
    "ocupacion",
    "informacion publica",
    "subvencion",
    "subvenciones",
    "premios",
    "convenio",
    "convenios",
    "urbanismo",
    "autorizacion ambiental",
    "procedimiento nacional de oposicion",
)
OPPOSITION_ALERT_GENERIC_CALL_TERMS = {
    "convocatoria",
    "se convoca",
}
OPPOSITION_ALERT_STRONG_TYPES = {
    "convocatoria",
    "bolsa",
    "lista_provisional",
    "lista_definitiva",
    "tribunal",
    "fecha_examen",
    "subsanacion",
}
OPPOSITION_ALERT_CONTEXT_REQUIRED_TYPES = {
    "correccion",
    "plazo",
    "adjudicacion",
}
OPPOSITION_ALERT_STRICT_TYPES = {
    "convocatoria",
    "bolsa",
    "bases",
    "lista_provisional",
    "lista_definitiva",
    "tribunal",
    "fecha_examen",
    "plazo",
    "subsanacion",
    "correccion",
}
OPPOSITION_ALERT_BROAD_TYPES = {
    "ope",
    "provision_puestos",
    "libre_designacion",
    "concurso_meritos",
    "nombramiento",
    "adjudicacion",
    "universidad_profesorado",
}


def _classify_opposition_alert(document: dict[str, Any]) -> dict[str, Any]:
    title = _normalize_search_text(str(document.get("title") or ""))
    combined_text = _normalize_search_text(
        " ".join(
            [
                str(document.get("title") or ""),
                str(document.get("department") or ""),
                str(document.get("section") or ""),
                str(document.get("document_type") or ""),
            ]
        )
    )
    matched_terms: list[str] = []
    matched_rules: list[str] = []
    alert_type = "other"
    for candidate_type, rule_name, terms in OPPOSITION_ALERT_RULES:
        found_terms = [term for term in terms if _keyword_matches(combined_text, term)]
        if found_terms:
            alert_type = candidate_type
            matched_terms.extend(found_terms)
            matched_rules.append(f"strong_{rule_name}")
            break
    broad_alert_type = ""
    broad_terms: list[str] = []
    broad_rule = ""
    for candidate_type, rule_name, terms in OPPOSITION_ALERT_BROAD_RULES:
        found_terms = [term for term in terms if _keyword_matches(combined_text, term)]
        if found_terms:
            broad_alert_type = candidate_type
            broad_terms = found_terms
            broad_rule = f"broad_{rule_name}"
            break
    if alert_type in {"other", "convocatoria", "nombramiento"} and broad_alert_type:
        alert_type = broad_alert_type
        matched_terms.extend(broad_terms)
        matched_rules.append(broad_rule)
    has_process_context = any(
        _keyword_matches(combined_text, term) for term in OPPOSITION_ALERT_PROCESS_CONTEXT
    )
    noise_terms = [
        term for term in OPPOSITION_ALERT_NOISE_TERMS if _keyword_matches(combined_text, term)
    ]
    excluding_noise_terms = [
        term
        for term in OPPOSITION_ALERT_EXCLUDING_NOISE_TERMS
        if _keyword_matches(combined_text, term)
    ]
    if excluding_noise_terms:
        return {
            "matched": False,
            "alert_type": "other",
            "confidence": "low",
            "matched_terms": excluding_noise_terms,
            "matched_rules": [
                f"excluded_noise:{_compact_token(term)}" for term in excluding_noise_terms
            ],
        }
    if noise_terms and not has_process_context:
        return {
            "matched": False,
            "alert_type": "other",
            "confidence": "low",
            "matched_terms": noise_terms,
            "matched_rules": [f"excluded_noise:{_compact_token(term)}" for term in noise_terms],
        }
    generic_call_only = (
        alert_type == "convocatoria"
        and bool(matched_terms)
        and all(term in OPPOSITION_ALERT_GENERIC_CALL_TERMS for term in matched_terms)
    )
    if generic_call_only and not has_process_context:
        return {
            "matched": False,
            "alert_type": "other",
            "confidence": "low",
            "matched_terms": matched_terms,
            "matched_rules": [*matched_rules, "excluded_missing_process_context"],
        }
    if alert_type in OPPOSITION_ALERT_CONTEXT_REQUIRED_TYPES and not has_process_context:
        return {
            "matched": False,
            "alert_type": "other",
            "confidence": "low",
            "matched_terms": matched_terms,
            "matched_rules": [*matched_rules, "excluded_missing_process_context"],
        }
    if alert_type == "other":
        context_terms = [
            term
            for term in OPPOSITION_ALERT_PROCESS_CONTEXT
            if _keyword_matches(combined_text, term)
        ]
        if not context_terms:
            return {
                "matched": False,
                "alert_type": "other",
                "confidence": "low",
                "matched_terms": [],
                "matched_rules": [],
            }
        matched_terms.extend(context_terms)
        matched_rules.append("medium_process_context")
        confidence = "medium"
    elif alert_type in OPPOSITION_ALERT_STRONG_TYPES:
        confidence = "high"
    else:
        confidence = "medium"
    alert_scope = _opposition_alert_scope(
        source_code=str(document.get("source_code") or ""),
        alert_type=alert_type,
        combined_text=combined_text,
        has_process_context=has_process_context,
    )
    if alert_scope == "review_only" and confidence == "high":
        confidence = "medium"
    if noise_terms:
        matched_terms.extend(noise_terms)
        matched_rules.extend(f"noise_present:{_compact_token(term)}" for term in noise_terms)
        if confidence == "high":
            confidence = "medium"
    return {
        "matched": True,
        "alert_type": alert_type,
        "confidence": confidence,
        "matched_terms": list(dict.fromkeys(matched_terms)),
        "matched_rules": list(dict.fromkeys(matched_rules)),
        "normalized_title": title,
        "alert_scope": alert_scope,
    }


def _opposition_alert_scope(
    *,
    source_code: str,
    alert_type: str,
    combined_text: str,
    has_process_context: bool,
) -> str:
    strict_terms = (
        "proceso selectivo",
        "pruebas selectivas",
        "oposicion",
        "oposiciones",
        "concurso-oposicion",
        "concurso oposicion",
        "bolsa de trabajo",
        "bolsa de empleo",
        "lista provisional",
        "lista definitiva",
        "admitidos",
        "excluidos",
        "tribunal calificador",
        "fecha de examen",
        "turno libre",
        "promocion interna",
    )
    if alert_type in OPPOSITION_ALERT_STRICT_TYPES and any(
        _keyword_matches(combined_text, term) for term in strict_terms
    ):
        return "strict"
    if alert_type in {"bolsa", "lista_provisional", "lista_definitiva", "tribunal", "fecha_examen"}:
        return "strict"
    if alert_type in OPPOSITION_ALERT_BROAD_TYPES:
        if alert_type == "nombramiento" and not has_process_context:
            return "review_only"
        return "broad"
    if alert_type == "convocatoria" and has_process_context:
        if source_code in {"BOE", "BOPV"} and not any(
            _keyword_matches(combined_text, term) for term in strict_terms
        ):
            return "review_only"
        return "strict"
    if alert_type == "other" and has_process_context:
        if source_code in {"BOE", "BOPV"}:
            return "review_only"
        return "broad"
    return "review_only"


def _opposition_alert_record(
    document: dict[str, Any],
    *,
    source_name: str,
    classification: dict[str, Any],
) -> dict[str, Any]:
    official_url = _candidate_official_url(document)
    alert_type = classification["alert_type"]
    normalized_title = classification.get("normalized_title") or _normalize_search_text(
        str(document.get("title") or "")
    )
    dedupe_key = _opposition_alert_dedupe_key(document, official_url, alert_type, normalized_title)
    return {
        "source_document_id": document["id"],
        "source_candidate_id": None,
        "source_code": document["source_code"],
        "source_name": source_name,
        "territory_code": _opposition_alert_territory_code(document["source_code"]),
        "territory_name": _opposition_alert_territory_name(document["source_code"]),
        "publication_date": document["publication_date"],
        "title": document.get("title") or "",
        "normalized_title": normalized_title,
        "official_url": official_url,
        "bulletin_identifier": None,
        "document_identifier": document.get("external_id"),
        "issuing_body": document.get("department"),
        "section": document.get("section"),
        "alert_type": alert_type,
        "alert_scope": classification["alert_scope"],
        "confidence": classification["confidence"],
        "matched_terms": classification["matched_terms"],
        "matched_rules": classification["matched_rules"],
        "dedupe_key": dedupe_key,
        "related_group_key": _opposition_alert_related_group_key(document, alert_type),
        "review_status": "new",
        "evidence_grade_status": "none",
        "metadata_json": {},
    }


def _opposition_alert_dedupe_key(
    document: dict[str, Any],
    official_url: str,
    alert_type: str,
    normalized_title: str,
) -> str:
    source_code = document["source_code"]
    external_id = document.get("external_id")
    if external_id:
        return f"{source_code}:{_compact_token(str(external_id))}:{alert_type}"
    if official_url:
        return f"{source_code}:{_compact_token(official_url)}:{alert_type}"
    department = _compact_token(document.get("department") or "none")
    return (
        f"{source_code}:{document['publication_date']}:{_compact_token(normalized_title)}:"
        f"{department}:{alert_type}"
    )


def _opposition_alert_related_group_key(document: dict[str, Any], alert_type: str) -> str:
    title = _compact_token(_normalize_search_text(str(document.get("title") or "")))
    department = _compact_token(document.get("department") or "none")
    territory = _opposition_alert_territory_code(document["source_code"])
    return f"{territory}:{department}:{title}:{alert_type}"


def _opposition_alert_territory_code(source_code: str) -> str:
    return {
        "BOE": "ES",
        "BOJA": "ES-AN",
        "DOGV": "ES-VC",
        "BOCYL": "ES-CL",
        "BOPV": "ES-PV",
        "BORM": "ES-MC",
        "BOA": "ES-AR",
        "DOGC": "ES-CT",
    }.get(source_code, "unknown")


def _opposition_alert_territory_name(source_code: str) -> str:
    return {
        "BOE": "Espana",
        "BOJA": "Andalucia",
        "DOGV": "Comunitat Valenciana",
        "BOCYL": "Castilla y Leon",
        "BOPV": "Pais Vasco",
        "BORM": "Region de Murcia",
        "BOA": "Aragon",
        "DOGC": "Catalunya",
    }.get(source_code, "Unknown")


class _SharedBOEFetcher:
    retry_count = 0
    throttle_triggered = False
    last_http_status: int | None = None

    def __init__(self, client: BOEClient) -> None:
        self.client = client

    def __call__(self, target_date: str) -> bytes:
        try:
            payload = self.client.fetch_summary(target_date)
        finally:
            self.retry_count = self.client.last_request_audit.retry_count
            self.throttle_triggered = self.client.last_request_audit.throttle_triggered
            self.last_http_status = self.client.last_request_audit.last_http_status
        return payload


def _inclusive_dates(date_from: date, date_to: date):
    current = date_from
    while current <= date_to:
        yield current
        current += timedelta(days=1)


def _candidate_keywords(args: argparse.Namespace) -> list[str]:
    keywords: list[str] = []
    if args.profile == "la-ayuda":
        keywords.extend(LA_AYUDA_PROFILE_KEYWORDS)
    if args.profile == "boja-ayudas":
        keywords.extend(BOJA_AYUDAS_PROFILE_KEYWORDS)
    if args.profile == "dogv-ayudas":
        keywords.extend(DOGV_AYUDAS_PROFILE_KEYWORDS)
    if args.profile == "bocyl-ayudas":
        keywords.extend(BOCYL_AYUDAS_PROFILE_KEYWORDS)
    if args.profile in {"boa-ayudas", "borm-ayudas"}:
        keywords.extend(AUTONOMOUS_AYUDAS_PROFILE_KEYWORDS)
    if args.profile == "bopv-ayudas":
        keywords.extend(BOPV_AYUDAS_PROFILE_KEYWORDS)
    if args.profile == "dogc-ayudas":
        keywords.extend(DOGC_AYUDAS_PROFILE_KEYWORDS)
    if args.keywords:
        keywords.extend(keyword.strip() for keyword in args.keywords.split(",") if keyword.strip())
    return list(dict.fromkeys(keywords))


def _candidate_filters(args: argparse.Namespace) -> dict[str, list[str]]:
    excluded_sections = _parse_filter_values(args.exclude_sections)
    if args.profile == "la-ayuda" and not excluded_sections:
        excluded_sections = LA_AYUDA_DEFAULT_EXCLUDED_SECTIONS.copy()
    return {
        "profile": [args.profile] if args.profile else [],
        "include_sections": _parse_filter_values(args.include_sections),
        "exclude_sections": excluded_sections,
        "include_departments": _parse_filter_values(args.include_departments),
        "exclude_departments": _parse_filter_values(args.exclude_departments),
    }


def _parse_filter_values(value: str | None) -> list[str]:
    if not value:
        return []
    return [_normalize_search_text(item) for item in value.split(",") if item.strip()]


def _candidate_keyword_matches(
    document: dict[str, Any],
    keywords: list[str],
    *,
    profile: str | None = None,
) -> dict[str, Any]:
    fields = {
        "title": document.get("title") or "",
        "department": document.get("department") or "",
        "section": document.get("section") or "",
        "document_type": document.get("document_type") or "",
        "raw_metadata": document.get("raw_metadata_json") or "",
    }
    matched: dict[str, list[str]] = {}
    for field, value in fields.items():
        normalized_value = _normalize_search_text(str(value))
        field_matches = [
            keyword for keyword in keywords if _keyword_matches(normalized_value, keyword)
        ]
        if field_matches:
            matched[field] = list(dict.fromkeys(field_matches))
    if not matched:
        return {}
    matched_set = {keyword for matches in matched.values() for keyword in matches}
    matched_keywords = [keyword for keyword in keywords if keyword in matched_set]
    score, score_reasons = _score_candidate_match(matched_keywords, profile=profile)
    return {
        "keywords": matched_keywords,
        "matched_fields": matched,
        "score": score,
        "score_reasons": score_reasons,
        "warning": "Keyword matching uses BOE titles and metadata only; it is not classification.",
    }


def _candidate_exclusion_reason(
    document: dict[str, Any],
    matches: dict[str, Any],
    filters: dict[str, list[str]],
) -> str | None:
    section_aliases = _section_aliases(document.get("section") or "")
    department = _normalize_search_text(document.get("department") or "")
    if filters["include_sections"] and not any(
        _filter_matches_section(section_aliases, expected)
        for expected in filters["include_sections"]
    ):
        return "section"
    if any(
        _filter_matches_section(section_aliases, expected)
        for expected in filters["exclude_sections"]
    ):
        return "section"
    if filters["include_departments"] and not any(
        expected in department for expected in filters["include_departments"]
    ):
        return "department"
    if any(expected in department for expected in filters["exclude_departments"]):
        return "department"
    if filters["profile"] == ["la-ayuda"] and _weak_only_match(matches["keywords"]):
        return "keyword_rules"
    if filters["profile"] == ["boja-ayudas"] and _boja_profile_exclusion_reason(
        document,
        matches,
    ):
        return "keyword_rules"
    if filters["profile"] == ["dogv-ayudas"] and _dogv_profile_exclusion_reason(
        document,
        matches,
    ):
        return "keyword_rules"
    if filters["profile"] == ["bocyl-ayudas"] and _bocyl_profile_exclusion_reason(
        document,
        matches,
    ):
        return "keyword_rules"
    if filters["profile"] == ["borm-ayudas"] and _borm_profile_exclusion_reason(
        document,
        matches,
    ):
        return "keyword_rules"
    if (
        filters["profile"]
        and filters["profile"][0]
        in {
            "bopv-ayudas",
            "boa-ayudas",
            "dogc-ayudas",
        }
        and _autonomous_profile_exclusion_reason(document, matches)
    ):
        return "keyword_rules"
    return None


def _candidate_evidence_metadata(
    document: dict[str, Any],
    matches: dict[str, Any],
    *,
    profile: str | None,
) -> dict[str, Any]:
    return {
        **matches,
        "profile": profile or "custom",
        "official_identifier": document["external_id"],
        "publication_date": document["publication_date"],
        "title": document.get("title") or "",
        "section": document.get("section"),
        "department": document.get("department"),
        "official_url": _candidate_official_url(document),
    }


def _normalize_search_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.lower())
    ascii_text = "".join(
        character for character in normalized if not unicodedata.combining(character)
    )
    return re.sub(r"\s+", " ", ascii_text).strip()


def _keyword_matches(normalized_value: str, keyword: str) -> bool:
    normalized_keyword = _normalize_search_text(keyword)
    if not normalized_keyword:
        return False
    phrase_pattern = r"\s+".join(re.escape(part) for part in normalized_keyword.split())
    pattern = rf"(?<!\w){phrase_pattern}(?!\w)"
    return re.search(pattern, normalized_value) is not None


def _score_candidate_match(
    keywords: list[str],
    *,
    profile: str | None,
) -> tuple[int, list[str]]:
    score = 0
    reasons: list[str] = []
    normalized_keywords = {_normalize_search_text(keyword): keyword for keyword in keywords}
    for normalized_keyword, original_keyword in sorted(normalized_keywords.items()):
        reason_key = _compact_token(original_keyword)
        if normalized_keyword in {_normalize_search_text(item) for item in STRONG_PHRASES}:
            score += 3
            reasons.append(f"strong_phrase:{reason_key}")
        elif normalized_keyword in {_normalize_search_text(item) for item in STRONG_KEYWORDS}:
            score += 2
            reasons.append(f"strong_keyword:{reason_key}")
        elif normalized_keyword in GENERIC_WEAK_KEYWORDS:
            score += 1
            reasons.append(f"weak_keyword:{reason_key}")
        else:
            score += 1
            reasons.append(f"keyword:{reason_key}")
    if profile == "la-ayuda" and _weak_only_match(keywords):
        score -= 1
        reasons.append("weak_only_generic_match:-1")
    if profile == "boja-ayudas" and _boja_weak_only_match(keywords):
        score -= 2
        reasons.append("boja_weak_only_generic_match:-2")
    if profile == "dogv-ayudas" and _dogv_weak_only_match(keywords):
        score -= 2
        reasons.append("dogv_weak_only_generic_match:-2")
    if profile == "bocyl-ayudas" and _bocyl_weak_only_match(keywords):
        score -= 2
        reasons.append("bocyl_weak_only_generic_match:-2")
    if profile in {
        "bopv-ayudas",
        "boa-ayudas",
        "borm-ayudas",
        "dogc-ayudas",
    } and _autonomous_weak_only_match(keywords):
        score -= 2
        reasons.append("autonomous_weak_only_generic_match:-2")
    return score, reasons


def _weak_only_match(keywords: list[str]) -> bool:
    normalized_keywords = {_normalize_search_text(keyword) for keyword in keywords}
    if not normalized_keywords:
        return True
    if normalized_keywords <= GENERIC_WEAK_KEYWORDS:
        return True
    transport_support = {_normalize_search_text(keyword) for keyword in TRANSPORT_SUPPORT_KEYWORDS}
    return "transporte" in normalized_keywords and not (normalized_keywords & transport_support)


def _boja_profile_exclusion_reason(
    document: dict[str, Any],
    matches: dict[str, Any],
) -> str | None:
    keywords = matches["keywords"]
    normalized_keywords = {_normalize_search_text(keyword) for keyword in keywords}
    combined_text = _normalize_search_text(
        " ".join(
            [
                str(document.get("title") or ""),
                str(document.get("department") or ""),
                str(document.get("section") or ""),
                str(document.get("document_type") or ""),
                str(document.get("raw_metadata_json") or ""),
            ]
        )
    )
    if _boja_weak_only_match(keywords):
        return "boja_weak_only"
    if {"vivienda", "alquiler"} & normalized_keywords and not (
        {"joven", "jovenes", "estudiantes", "alumnado"} & normalized_keywords
        or any(term in combined_text for term in {"joven", "jovenes", "estudiantes", "alumnado"})
    ):
        return "boja_housing_noise"
    high_intent = {_normalize_search_text(keyword) for keyword in BOJA_HIGH_INTENT_KEYWORDS}
    education_departments = {
        _normalize_search_text(term) for term in BOJA_EDUCATION_DEPARTMENT_TERMS
    }
    noise_departments = {_normalize_search_text(term) for term in BOJA_NOISE_DEPARTMENT_TERMS}
    noise_text_terms = {_normalize_search_text(term) for term in BOJA_NOISE_TEXT_TERMS}
    has_high_intent = bool(normalized_keywords & high_intent) or any(
        term in combined_text for term in education_departments
    )
    has_noise_term = any(term in combined_text for term in noise_departments | noise_text_terms)
    if has_noise_term and not has_high_intent:
        return "boja_institutional_or_sector_noise"
    return None


def _boja_weak_only_match(keywords: list[str]) -> bool:
    normalized_keywords = {_normalize_search_text(keyword) for keyword in keywords}
    if not normalized_keywords:
        return True
    high_intent = {_normalize_search_text(keyword) for keyword in BOJA_HIGH_INTENT_KEYWORDS}
    return not bool(normalized_keywords & high_intent)


def _dogv_profile_exclusion_reason(
    document: dict[str, Any],
    matches: dict[str, Any],
) -> str | None:
    keywords = matches["keywords"]
    title = _normalize_search_text(str(document.get("title") or ""))
    department = _normalize_search_text(str(document.get("department") or ""))
    section = _normalize_search_text(str(document.get("section") or ""))
    document_type = _normalize_search_text(str(document.get("document_type") or ""))
    raw_metadata = _normalize_search_text(str(document.get("raw_metadata_json") or ""))
    combined_text = " ".join([title, department, section, document_type, raw_metadata])
    title_has_direct_signal = _dogv_title_has_direct_signal(title)
    housing_context = _dogv_has_housing_context(title)

    if _dogv_weak_only_match(keywords):
        return "dogv_weak_only"
    if any(term in section for term in _normalized_set(DOGV_NOISE_SECTION_TERMS)):
        return "dogv_public_employment_section"
    if any(term in title for term in _normalized_set(DOGV_PUBLIC_EMPLOYMENT_TERMS)):
        return "dogv_public_employment_notice"
    if any(term in combined_text for term in _normalized_set(DOGV_PROCUREMENT_TERMS)):
        return "dogv_procurement_noise"
    if any(term in title for term in _normalized_set(DOGV_CLOSED_OR_RESULT_TERMS)):
        return "dogv_closed_or_result_notice"
    if any(term in title for term in _normalized_set(DOGV_AWARD_OR_PROCEDURE_TERMS)):
        return "dogv_award_or_procedure_noise"
    if {"vivienda", "alquiler"} & {
        _normalize_search_text(keyword) for keyword in keywords
    } and not housing_context:
        return "dogv_housing_noise"
    title_has_local_entity_noise = any(
        term in title for term in _normalized_set(DOGV_LOCAL_ENTITY_TERMS)
    )
    if any(term in combined_text for term in _normalized_set(DOGV_LOCAL_ENTITY_TERMS)) and not (
        title_has_direct_signal and not title_has_local_entity_noise
    ):
        return "dogv_local_entity_noise"
    title_has_sector_company_noise = any(
        term in title for term in _normalized_set(DOGV_SECTOR_COMPANY_TERMS)
    )
    if any(term in combined_text for term in _normalized_set(DOGV_SECTOR_COMPANY_TERMS)) and not (
        title_has_direct_signal and not title_has_sector_company_noise
    ):
        return "dogv_sector_or_company_noise"
    if not title_has_direct_signal and "subvenciones y becas" not in section:
        return "dogv_no_direct_signal"
    return None


def _dogv_weak_only_match(keywords: list[str]) -> bool:
    normalized_keywords = {_normalize_search_text(keyword) for keyword in keywords}
    if not normalized_keywords:
        return True
    high_intent = _normalized_set(DOGV_HIGH_INTENT_KEYWORDS)
    return not bool(normalized_keywords & high_intent)


def _dogv_title_has_direct_signal(title: str) -> bool:
    if any(term in title for term in _normalized_set(DOGV_DIRECT_TITLE_TERMS)):
        return True
    return _dogv_has_housing_context(title)


def _dogv_has_housing_context(title: str) -> bool:
    has_housing = any(term in title for term in {"vivienda", "alquiler"})
    has_person_context = any(
        term in title
        for term in {
            "joven",
            "jovenes",
            "familia",
            "familias",
            "estudiante",
            "estudiantes",
            "alumnado",
        }
    )
    return has_housing and has_person_context


def _bocyl_profile_exclusion_reason(
    document: dict[str, Any],
    matches: dict[str, Any],
) -> str | None:
    keywords = matches["keywords"]
    title = _normalize_search_text(str(document.get("title") or ""))
    department = _normalize_search_text(str(document.get("department") or ""))
    section = _normalize_search_text(str(document.get("section") or ""))
    document_type = _normalize_search_text(str(document.get("document_type") or ""))
    raw_metadata = _normalize_search_text(str(document.get("raw_metadata_json") or ""))
    combined_text = " ".join([title, department, section, document_type, raw_metadata])
    title_has_direct_signal = _bocyl_title_has_direct_signal(title)

    if _bocyl_weak_only_match(keywords):
        return "bocyl_weak_only"
    if not title_has_direct_signal and any(
        term in combined_text for term in _normalized_set(BOCYL_ENVIRONMENTAL_OR_PLANNING_TERMS)
    ):
        return "bocyl_environmental_or_planning_noise"
    if {"vivienda", "alquiler"} & {
        _normalize_search_text(keyword) for keyword in keywords
    } and not _bocyl_has_housing_context(title):
        return "bocyl_housing_noise"
    title_has_institutional_noise = any(
        term in title for term in _normalized_set(BOCYL_INSTITUTIONAL_OR_SECTOR_TERMS)
    )
    if any(
        term in combined_text for term in _normalized_set(BOCYL_INSTITUTIONAL_OR_SECTOR_TERMS)
    ) and not (title_has_direct_signal and not title_has_institutional_noise):
        return "bocyl_institutional_or_sector_noise"
    if not title_has_direct_signal:
        return "bocyl_no_direct_signal"
    return None


def _bocyl_weak_only_match(keywords: list[str]) -> bool:
    normalized_keywords = {_normalize_search_text(keyword) for keyword in keywords}
    if not normalized_keywords:
        return True
    high_intent = _normalized_set(BOCYL_HIGH_INTENT_KEYWORDS)
    return not bool(normalized_keywords & high_intent)


def _bocyl_title_has_direct_signal(title: str) -> bool:
    if any(term in title for term in _normalized_set(BOCYL_DIRECT_TITLE_TERMS)):
        return True
    if "formacion profesional" in title and any(
        term in title for term in {"beca", "becas", "ayuda", "ayudas"}
    ):
        return True
    return _bocyl_has_housing_context(title)


def _bocyl_has_housing_context(title: str) -> bool:
    has_housing = any(term in title for term in {"vivienda", "alquiler"})
    has_person_context = any(
        term in title
        for term in {
            "joven",
            "jovenes",
            "familia",
            "familias",
            "estudiante",
            "estudiantes",
            "alumnado",
            "discapacidad",
            "bono alquiler",
        }
    )
    return has_housing and has_person_context


def _autonomous_profile_exclusion_reason(
    document: dict[str, Any],
    matches: dict[str, Any],
) -> str | None:
    keywords = matches["keywords"]
    title = _normalize_search_text(str(document.get("title") or ""))
    department = _normalize_search_text(str(document.get("department") or ""))
    section = _normalize_search_text(str(document.get("section") or ""))
    document_type = _normalize_search_text(str(document.get("document_type") or ""))
    combined_text = " ".join([title, department, section, document_type])
    title_has_direct_signal = _autonomous_title_has_direct_signal(title)

    if _autonomous_weak_only_match(keywords):
        return "autonomous_weak_only"
    if any(term in combined_text for term in _normalized_set(AUTONOMOUS_EMPLOYMENT_NOISE_TERMS)):
        return "autonomous_employment_noise"
    if {"vivienda", "alquiler"} & {
        _normalize_search_text(keyword) for keyword in keywords
    } and not _autonomous_has_housing_context(title):
        return "autonomous_housing_noise"
    title_has_procedural_noise = any(
        term in title for term in _normalized_set(AUTONOMOUS_PROCEDURAL_NOISE_TERMS)
    )
    if any(
        term in combined_text for term in _normalized_set(AUTONOMOUS_PROCEDURAL_NOISE_TERMS)
    ) and not (title_has_direct_signal and not title_has_procedural_noise):
        return "autonomous_procedural_or_sector_noise"
    if not title_has_direct_signal:
        return "autonomous_no_direct_signal"
    return None


def _borm_profile_exclusion_reason(
    document: dict[str, Any],
    matches: dict[str, Any],
) -> str | None:
    keywords = matches["keywords"]
    title = _normalize_search_text(str(document.get("title") or ""))
    department = _normalize_search_text(str(document.get("department") or ""))
    section = _normalize_search_text(str(document.get("section") or ""))
    document_type = _normalize_search_text(str(document.get("document_type") or ""))
    combined_text = " ".join([title, department, section, document_type])
    title_has_direct_signal = _borm_title_has_direct_signal(title)

    if _autonomous_weak_only_match(keywords):
        return "borm_weak_only"
    if any(
        term in combined_text for term in _normalized_set(BORM_PUBLIC_EMPLOYMENT_OR_CONTEST_TERMS)
    ):
        return "borm_employment_or_contest_noise"
    if any(term in title for term in _normalized_set(BORM_PROCEDURAL_NOISE_TERMS)):
        return "borm_procedural_noise"
    if (
        any(term in title for term in _normalized_set(BORM_ENTITY_PROJECT_NOISE_TERMS))
        and not title_has_direct_signal
    ):
        return "borm_entity_project_noise"
    if not title_has_direct_signal:
        return "borm_no_direct_signal"
    return None


def _borm_title_has_direct_signal(title: str) -> bool:
    if any(term in title for term in _normalized_set(BORM_DIRECT_TITLE_TERMS)):
        return True
    aid_context = {
        "ayuda",
        "ayudas",
        "subvencion",
        "subvenciones",
        "beca",
        "becas",
        "convocatoria de ayudas",
        "convocatoria de subvenciones",
    }
    if not any(term in title for term in aid_context):
        return False
    return any(term in title for term in _normalized_set(BORM_PERSON_CONTEXT_TERMS))


def _autonomous_weak_only_match(keywords: list[str]) -> bool:
    normalized_keywords = {_normalize_search_text(keyword) for keyword in keywords}
    if not normalized_keywords:
        return True
    high_intent = _normalized_set(AUTONOMOUS_HIGH_INTENT_KEYWORDS)
    return not bool(normalized_keywords & high_intent)


def _autonomous_title_has_direct_signal(title: str) -> bool:
    if any(term in title for term in _normalized_set(AUTONOMOUS_DIRECT_TITLE_TERMS)):
        return True
    aid_context = {
        "ayuda",
        "ayudas",
        "subvencion",
        "subvenciones",
        "beca",
        "becas",
        "beka",
        "bekak",
        "bases reguladoras",
        "dirulaguntza",
        "dirulaguntzak",
    }
    if "formacion profesional" in title and any(term in title for term in aid_context):
        return True
    if {"universidad", "universidades", "unibertsitate"} & set(title.split()) and any(
        term in title for term in aid_context
    ):
        return True
    return _autonomous_has_housing_context(title)


def _autonomous_has_housing_context(title: str) -> bool:
    has_housing = any(
        term in title
        for term in {
            "vivienda",
            "alquiler",
            "lloguer",
        }
    )
    has_person_context = any(
        term in title
        for term in {
            "joven",
            "jovenes",
            "jove",
            "joves",
            "familia",
            "familias",
            "families",
            "estudiante",
            "estudiantes",
            "estudiant",
            "estudiants",
            "alumnado",
            "alumnat",
            "discapacidad",
            "bono alquiler",
            "bo lloguer",
        }
    )
    return has_housing and has_person_context


def _normalized_set(values: set[str]) -> set[str]:
    return {_normalize_search_text(value) for value in values}


def _section_aliases(section: str) -> set[str]:
    normalized = _normalize_search_text(section)
    aliases = {normalized}
    compact = normalized.replace(".", " ").replace("-", " ")
    compact = re.sub(r"\s+", " ", compact).strip()
    aliases.add(compact)
    if normalized in {"i", "ii", "iii", "iv", "v"}:
        aliases.add(normalized)
    if "contratacion del sector publico" in normalized:
        aliases.add("v-a")
        aliases.add("v a")
    if "otros anuncios oficiales" in normalized:
        aliases.add("v-b")
        aliases.add("v b")
    return aliases


def _filter_matches_section(section_aliases: set[str], expected: str) -> bool:
    expected_aliases = _section_aliases(expected)
    return bool(section_aliases & expected_aliases)


def _candidate_official_url(document: dict[str, Any]) -> str:
    return (
        document.get("url_html")
        or document.get("url_xml")
        or document.get("url_pdf")
        or f"https://www.boe.es/buscar/doc.php?id={document['external_id']}"
    )


def _run_consolidated_get(
    repository: OfficialSourcesRepository,
    identifier: str,
    consolidated_client: httpx.Client | None,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    try:
        validate_consolidated_identifier(identifier)
    except ValueError as exc:
        print(str(exc), file=stderr)
        return 2
    print(
        f"command_started=boe-consolidated-get source_code=BOE identifier={identifier}", file=stdout
    )
    service = BOEConsolidatedService(
        repository,
        client=BOEConsolidatedClient(client=consolidated_client),
    )
    try:
        law = service.fetch_and_store(identifier)
    except Exception as exc:
        print(f"boe-consolidated-get failed: {exc}", file=stderr)
        return 1
    versions = repository.list_consolidated_law_versions(law["id"])
    blocks = repository.list_consolidated_law_text_blocks(law["id"])
    print(
        " ".join(
            [
                f"official_identifier={law['official_identifier']}",
                f"versions={len(versions)}",
                f"text_blocks={len(blocks)}",
            ]
        ),
        file=stdout,
    )
    return 0


def _run_consolidated_index_get(
    repository: OfficialSourcesRepository,
    identifier: str,
    consolidated_client: httpx.Client | None,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    try:
        validate_consolidated_identifier(identifier)
    except ValueError as exc:
        print(str(exc), file=stderr)
        return 2
    print(
        f"command_started=boe-consolidated-index-get source_code=BOE identifier={identifier}",
        file=stdout,
    )
    service = BOEConsolidatedService(
        repository,
        client=BOEConsolidatedClient(client=consolidated_client),
    )
    try:
        result = service.fetch_and_store_index(identifier)
    except Exception as exc:
        print(f"boe-consolidated-index-get failed: {exc}", file=stderr)
        return 1
    print(
        " ".join(
            [
                f"official_identifier={result['official_identifier']}",
                f"version_date={result['version_date']}",
                f"index_blocks={result['block_count']}",
            ]
        ),
        file=stdout,
    )
    return 0


def _run_consolidated_block_get(
    repository: OfficialSourcesRepository,
    identifier: str,
    block_id: str,
    print_content: bool,
    consolidated_client: httpx.Client | None,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    try:
        validate_consolidated_identifier(identifier)
        validate_consolidated_block_id(block_id)
    except ValueError as exc:
        print(str(exc), file=stderr)
        return 2
    print(
        " ".join(
            [
                "command_started=boe-consolidated-block-get",
                "source_code=BOE",
                f"identifier={identifier}",
                f"block_id={block_id}",
            ]
        ),
        file=stdout,
    )
    service = BOEConsolidatedService(
        repository,
        client=BOEConsolidatedClient(client=consolidated_client),
    )
    try:
        block = service.fetch_and_store_block(identifier, block_id)
    except Exception as exc:
        print(f"boe-consolidated-block-get failed: {exc}", file=stderr)
        return 1
    print(
        " ".join(
            [
                f"official_identifier={identifier}",
                f"block_id={block['official_block_id']}",
                f"block_type={block['block_type']}",
                f"version_id={block['version_id']}",
                f"source_snapshot_hash={block['source_snapshot_hash']}",
            ]
        ),
        file=stdout,
    )
    if print_content:
        print(block["content"], file=stdout)
    return 0


def _count_files(files: list[dict], file_type: str) -> int:
    return sum(1 for file_record in files if file_record["file_type"] == file_type)


def _format_counts(counts: dict) -> str:
    return " ".join(f"{key}={value}" for key, value in counts.items())


def _format_candidate_evidence_row(row: dict[str, Any]) -> str:
    return _format_counts(
        {
            "candidate_id": row["candidate_id"],
            "official_identifier": row["official_identifier"],
            "title": _quote_value(row["title"]),
            "review_status": row["review_status"],
            "evidence_review_status": row["evidence_review_status"],
            "evidence_label": row["evidence_label"] or "none",
            "manual_decision": row["manual_decision"] or "none",
            "needs_pdf": row["needs_pdf"] or "none",
            "downstream_project_fit": row["downstream_project_fit"] or "none",
            "reviewed_by": row["reviewed_by"] or "none",
            "reviewed_at": row["reviewed_at"] or "none",
            "xml_available": _bool_token(row["xml_available"]),
            "html_available": _bool_token(row["html_available"]),
            "pdf_available": _bool_token(row["pdf_available"]),
            "integrity_warning": _bool_token(row["integrity_warning"]),
            "selected_for_pdf": _bool_token(row["selected_for_pdf"]),
            "official_url": row["official_url"],
        }
    )


def _bool_token(value: object) -> str:
    return "true" if bool(value) else "false"


def _status_value(value: object) -> object:
    return "none" if value is None else value


def _format_counter(counter: Counter[str]) -> str:
    if not counter:
        return "none"
    return ",".join(f"{key}:{value}" for key, value in sorted(counter.items()))


def _compact_token(value: object) -> str:
    return str(value).strip().replace(" ", "_") or "none"


def _quote_value(value: object) -> str:
    text = str(value).replace('"', "'")
    return f'"{text}"'


if __name__ == "__main__":
    main()
