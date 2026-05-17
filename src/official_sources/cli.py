from __future__ import annotations

import argparse
import os
import sys
from datetime import date
from pathlib import Path
from typing import TextIO

import httpx

from official_sources.integrity.hashing import sha256_bytes
from official_sources.sources.boe.artifacts import (
    BOE_ARTIFACT_FIELDS,
    BOEArtifactDownloader,
    BOEArtifactDownloadError,
)
from official_sources.sources.boe.client import validate_boe_date
from official_sources.sources.boe.consolidated import (
    BOEConsolidatedClient,
    BOEConsolidatedService,
    validate_consolidated_block_id,
    validate_consolidated_identifier,
)
from official_sources.sources.boe.ingestion import NO_PUBLICATION_STATUS, ingest_boe_summary
from official_sources.storage.backup import SQLiteBackupError, backup_sqlite_database
from official_sources.storage.database import connect, initialize_database
from official_sources.storage.migrations.runner import (
    MigrationChecksumError,
    MigrationRunner,
    validate_database,
)
from official_sources.storage.repository import OfficialSourcesRepository


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

    ingest = subparsers.add_parser("ingest-boe-summary", help="Ingest one BOE daily summary.")
    ingest.add_argument(
        "--date",
        required=True,
        help="Target date in YYYY-MM-DD format or today.",
    )

    download = subparsers.add_parser(
        "download-boe-artifacts", help="Download stored official BOE artifact URLs."
    )
    download.add_argument(
        "--date", required=True, help="Target date in YYYY-MM-DD format or today."
    )
    download.add_argument(
        "--types",
        default="xml,html,pdf",
        help="Comma-separated artifact types.",
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
    return parser


def run(
    argv: list[str] | None = None,
    *,
    summary_fetcher=None,
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

    repository = _open_repository(args.db_path)
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

    try:
        target_date = resolve_target_date(args.date)
    except ValueError as exc:
        print(str(exc), file=stderr)
        return 2
    print(f"command_started={args.command} source_code=BOE target_date={target_date}", file=stdout)

    if args.command == "ingest-boe-summary":
        return _run_ingest(repository, target_date, summary_fetcher, stdout)
    if args.command == "download-boe-artifacts":
        try:
            artifact_types = _parse_artifact_types(args.types)
        except BOEArtifactDownloadError as exc:
            print(str(exc), file=stderr)
            return 2
        return _run_download(
            repository,
            target_date=target_date,
            artifact_types=artifact_types,
            artifact_dir=Path(args.artifact_dir),
            client=artifact_client,
            stdout=stdout,
            stderr=stderr,
        )
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
        print(
            " ".join(
                [
                    f"database_path={db_path}",
                    f"current_version={result.current_version}",
                    f"latest_version={result.latest_version}",
                    f"pending_migrations={len(result.pending_versions)}",
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


def _parse_artifact_types(value: str) -> list[str]:
    artifact_types = [item.strip() for item in value.split(",") if item.strip()]
    unsupported = sorted(set(artifact_types) - set(BOE_ARTIFACT_FIELDS))
    if unsupported:
        raise BOEArtifactDownloadError(f"Unsupported artifact types: {', '.join(unsupported)}")
    return artifact_types


def _run_download(
    repository: OfficialSourcesRepository,
    *,
    target_date: str,
    artifact_types: list[str],
    artifact_dir: Path,
    client: httpx.Client | None,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    documents = repository.list_documents_by_date(target_date)
    latest_run = repository.get_latest_ingestion_run("BOE", target_date)
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
    run_record = repository.create_ingestion_run(source_code="BOE", target_date=target_date)
    downloader = BOEArtifactDownloader(repository, cache_dir=artifact_dir, client=client)
    counts = {"downloaded": 0, "skipped": 0, "changed": 0, "failed": 0, "retries": 0}
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
                continue
            counts["downloaded"] += 1
            after = result[artifact_type]
            attempts = repository.list_artifact_download_attempts(document_id=document["id"])
            counts["retries"] += attempts[-1]["retry_count"] if attempts else 0
            previous_hash = before.get((artifact_type, after["official_url"]))
            if previous_hash is not None and previous_hash != after["sha256"]:
                counts["changed"] += 1
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
    counts = {"unchanged": 0, "changed": 0, "missing": 0}
    for file_record in repository.list_document_files_by_date(target_date):
        local_path = file_record["local_path"]
        if not local_path or not Path(local_path).exists():
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
    latest_run = repository.get_latest_ingestion_run("BOE", target_date)
    documents = repository.list_documents_by_date(target_date)
    files = repository.list_document_files_by_date(target_date)
    warnings = sum(1 for file_record in files if file_record["content_changed_at"])
    download_counts = repository.count_artifact_download_attempts_by_date(target_date)
    download_attempts = sum(download_counts.values())
    counts = {
        "ingestion_status": latest_run["status"] if latest_run else "none",
        "last_http_status": _status_value(latest_run["last_http_status"] if latest_run else None),
        "documents": len(documents),
        "xml_files": _count_files(files, "xml"),
        "html_files": _count_files(files, "html"),
        "pdf_files": _count_files(files, "pdf"),
        "download_attempts": download_attempts,
        "download_success": download_counts["success"],
        "download_skipped": download_counts["skipped"],
        "download_changed": download_counts["changed"],
        "download_failed": download_counts["failed"],
        "integrity_warnings": warnings,
        "failed_downloads": download_counts["failed"],
    }
    print(_format_counts(counts), file=stdout)
    return 0


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


def _status_value(value: object) -> object:
    return "none" if value is None else value
