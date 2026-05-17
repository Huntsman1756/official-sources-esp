from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
from xml.etree import ElementTree

import httpx

from official_sources.integrity.hashing import sha256_bytes
from official_sources.normalization.text import normalize_document_text
from official_sources.sources.boe.http_policy import BOERequestAudit, BOERequestPolicy
from official_sources.storage.repository import OfficialSourcesRepository, utc_now

BOE_ALLOWED_HOSTS = {"www.boe.es", "boe.es"}
BOE_ARTIFACT_FIELDS = {
    "xml": ("url_xml", "document.xml", "application/xml"),
    "html": ("url_html", "document.html", "text/html"),
    "pdf": ("url_pdf", "document.pdf", "application/pdf"),
}


class BOEArtifactDownloadError(ValueError):
    pass


@dataclass(frozen=True)
class ArtifactHTTPResponse:
    content: bytes
    status_code: int
    audit: BOERequestAudit


def validate_boe_artifact_url(url: str) -> str:
    parsed = urlsplit(url)
    if parsed.scheme != "https":
        raise BOEArtifactDownloadError("BOE artifact URLs must use HTTPS")
    if parsed.hostname not in BOE_ALLOWED_HOSTS:
        raise BOEArtifactDownloadError("BOE artifact URLs must use an official BOE host")
    if not parsed.path:
        raise BOEArtifactDownloadError("BOE artifact URLs must include a path")
    return url


class BOEArtifactDownloader:
    def __init__(
        self,
        repository: OfficialSourcesRepository,
        *,
        cache_dir: str | Path = "data/artifacts",
        client: httpx.Client | None = None,
        timeout: float = 30.0,
        request_policy: BOERequestPolicy | None = None,
        sleeper: Callable[[float], None] | None = None,
    ) -> None:
        self.repository = repository
        self.cache_dir = Path(cache_dir)
        self.client = client
        self.timeout = timeout
        self.request_policy = request_policy or BOERequestPolicy.from_env()
        self.sleeper = sleeper or time.sleep

    def download_document_artifacts(
        self,
        *,
        external_id: str,
        artifact_types: list[str] | None = None,
        ingestion_run_id: int | None,
    ) -> dict[str, dict]:
        document = self.repository.get_document_by_external_id(external_id)
        if document is None:
            raise KeyError(f"Unknown document: {external_id}")
        selected_types = artifact_types or list(BOE_ARTIFACT_FIELDS)
        results: dict[str, dict] = {}
        for artifact_type in selected_types:
            started_at = utc_now()
            if artifact_type not in BOE_ARTIFACT_FIELDS:
                self._record_attempt(
                    document_id=document["id"],
                    ingestion_run_id=ingestion_run_id,
                    file_type=artifact_type,
                    official_url=None,
                    status="failed",
                    http_status=None,
                    error_message=f"Unsupported BOE artifact type: {artifact_type}",
                    started_at=started_at,
                )
                raise BOEArtifactDownloadError(f"Unsupported BOE artifact type: {artifact_type}")
            field_name, filename, media_type = BOE_ARTIFACT_FIELDS[artifact_type]
            official_url = document[field_name]
            if not official_url:
                self._record_attempt(
                    document_id=document["id"],
                    ingestion_run_id=ingestion_run_id,
                    file_type=artifact_type,
                    official_url=None,
                    status="skipped",
                    http_status=None,
                    error_message=None,
                    started_at=started_at,
                )
                continue
            previous = self._existing_hash(document["id"], artifact_type, official_url)
            try:
                validated_url = validate_boe_artifact_url(official_url)
                response = self._download_response(validated_url)
            except BOEArtifactDownloadError as exc:
                self._record_attempt(
                    document_id=document["id"],
                    ingestion_run_id=ingestion_run_id,
                    file_type=artifact_type,
                    official_url=official_url,
                    status="failed",
                    http_status=getattr(exc, "http_status", None),
                    error_message=str(exc),
                    retry_count=getattr(exc, "retry_count", 0),
                    throttle_triggered=getattr(exc, "throttle_triggered", False),
                    started_at=started_at,
                )
                raise
            payload = response.content
            local_path = self._write_artifact(
                publication_date=document["publication_date"],
                external_id=document["external_id"],
                filename=filename,
                payload=payload,
            )
            file_record = self.repository.upsert_document_file(
                document_id=document["id"],
                file_type=artifact_type,
                official_url=official_url,
                local_path=str(local_path),
                media_type=media_type,
                payload=payload,
                source_snapshot_hash=sha256_bytes(payload),
                ingestion_run_id=ingestion_run_id,
            )
            if artifact_type in {"xml", "html"}:
                self._store_extracted_text(
                    document["id"], file_record["id"], artifact_type, payload
                )
            attempt_status = (
                "changed"
                if previous is not None and previous != file_record["sha256"]
                else "success"
            )
            self._record_attempt(
                document_id=document["id"],
                ingestion_run_id=ingestion_run_id,
                file_type=artifact_type,
                official_url=official_url,
                status=attempt_status,
                http_status=response.status_code,
                error_message=None,
                retry_count=response.audit.retry_count,
                throttle_triggered=response.audit.throttle_triggered,
                started_at=started_at,
            )
            results[artifact_type] = file_record
        return results

    def _download_response(self, url: str) -> ArtifactHTTPResponse:
        if self.client is not None:
            result = self.request_policy.get(
                url,
                client=self.client,
                sleeper=self.sleeper,
            )
        else:
            with httpx.Client(follow_redirects=False, timeout=self.timeout) as client:
                result = self.request_policy.get(
                    url,
                    client=client,
                    sleeper=self.sleeper,
                )
        if not 200 <= result.status_code < 300:
            exc = BOEArtifactDownloadError(
                f"BOE artifact download returned HTTP {result.status_code}"
            )
            exc.http_status = result.status_code
            exc.retry_count = result.audit.retry_count
            exc.throttle_triggered = result.audit.throttle_triggered
            raise exc
        return ArtifactHTTPResponse(
            content=result.content,
            status_code=result.status_code,
            audit=result.audit,
        )

    def _existing_hash(
        self,
        document_id: int,
        artifact_type: str,
        official_url: str,
    ) -> str | None:
        for file_record in self.repository.list_document_files(document_id):
            if (
                file_record["file_type"] == artifact_type
                and file_record["official_url"] == official_url
            ):
                return file_record["sha256"]
        return None

    def _record_attempt(
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
        retry_count: int = 0,
        throttle_triggered: bool = False,
    ) -> None:
        self.repository.create_artifact_download_attempt(
            document_id=document_id,
            ingestion_run_id=ingestion_run_id,
            file_type=file_type,
            official_url=official_url,
            status=status,
            http_status=http_status,
            error_message=error_message,
            retry_count=retry_count,
            throttle_triggered=throttle_triggered,
            started_at=started_at,
            finished_at=utc_now(),
        )

    def _write_artifact(
        self,
        *,
        publication_date: str,
        external_id: str,
        filename: str,
        payload: bytes,
    ) -> Path:
        year, month, day = publication_date.split("-")
        directory = self.cache_dir / "boe" / year / month / day / external_id
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / filename
        path.write_bytes(payload)
        return path

    def _store_extracted_text(
        self,
        document_id: int,
        source_file_id: int,
        artifact_type: str,
        payload: bytes,
    ) -> None:
        if artifact_type == "xml":
            content = extract_text_from_xml(payload)
        else:
            content = extract_text_from_html(payload)
        if not content:
            return
        normalized = normalize_document_text(content)
        self.repository.create_document_text(
            document_id=document_id,
            source_file_id=source_file_id,
            text_type=normalized.text_type,
            language=normalized.language,
            content=normalized.content,
            extraction_method=f"{artifact_type}_deterministic_text_extraction",
        )


def extract_text_from_xml(payload: bytes) -> str:
    root = ElementTree.fromstring(payload)
    return " ".join(part.strip() for part in root.itertext() if part.strip())


class _TextOnlyHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._ignored_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"script", "style"}:
            self._ignored_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style"} and self._ignored_depth:
            self._ignored_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._ignored_depth:
            return
        stripped = data.strip()
        if stripped:
            self.parts.append(stripped)


def extract_text_from_html(payload: bytes) -> str:
    parser = _TextOnlyHTMLParser()
    parser.feed(payload.decode("utf-8", errors="replace"))
    return " ".join(parser.parts)
