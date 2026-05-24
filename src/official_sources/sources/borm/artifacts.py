from __future__ import annotations

from pathlib import Path
from urllib.parse import urlsplit

import httpx

from official_sources.sources.boe.artifacts import (
    ArtifactHTTPResponse,
    BOEArtifactDownloader,
    BOEArtifactDownloadError,
)
from official_sources.storage.repository import OfficialSourcesRepository

BORM_ALLOWED_HOSTS = {"www.borm.es", "borm.es"}
BORM_ARTIFACT_FIELDS = {
    "pdf": ("url_pdf", "document.pdf", "application/pdf"),
}
BORM_PDF_REQUEST_HEADERS = {
    "Accept": "application/pdf",
    "User-Agent": "official-sources/1.0",
}


class BORMArtifactDownloadError(BOEArtifactDownloadError):
    pass


def validate_borm_artifact_url(url: str) -> str:
    parsed = urlsplit(url)
    if parsed.scheme != "https":
        raise BORMArtifactDownloadError("BORM artifact URLs must use HTTPS")
    if parsed.hostname not in BORM_ALLOWED_HOSTS:
        raise BORMArtifactDownloadError("BORM artifact URLs must use an official BORM host")
    if not parsed.path.startswith("/services/anuncio/") or not parsed.path.endswith("/pdf"):
        raise BORMArtifactDownloadError(
            "BORM artifact URLs must use an official BORM PDF service path"
        )
    return url


class BORMArtifactDownloader(BOEArtifactDownloader):
    def __init__(
        self,
        repository: OfficialSourcesRepository,
        *,
        cache_dir: str | Path = "data/artifacts",
        client: httpx.Client | None = None,
        timeout: float = 30.0,
    ) -> None:
        super().__init__(
            repository,
            cache_dir=cache_dir,
            client=client,
            timeout=timeout,
        )

    def _artifact_fields(self) -> dict[str, tuple[str, str, str]]:
        return BORM_ARTIFACT_FIELDS

    def _download_response(self, url: str) -> ArtifactHTTPResponse:
        if self.client is not None:
            result = self.request_policy.get(
                url,
                headers=BORM_PDF_REQUEST_HEADERS,
                client=self.client,
                sleeper=self.sleeper,
            )
        else:
            with httpx.Client(follow_redirects=True, timeout=self.timeout) as client:
                result = self.request_policy.get(
                    url,
                    headers=BORM_PDF_REQUEST_HEADERS,
                    client=client,
                    sleeper=self.sleeper,
                )
        if not 200 <= result.status_code < 300:
            exc = self._artifact_error(
                f"{self._artifact_error_prefix()} artifact download returned HTTP "
                f"{result.status_code}"
            )
            exc.http_status = result.status_code
            exc.retry_count = result.audit.retry_count
            exc.throttle_triggered = result.audit.throttle_triggered
            raise exc
        validate_borm_artifact_url(str(result.request.url))
        response = ArtifactHTTPResponse(
            content=result.content,
            status_code=result.status_code,
            audit=result.audit,
        )
        return response

    def _validate_artifact_url(self, url: str) -> str:
        return validate_borm_artifact_url(url)

    def _artifact_error(self, message: str) -> BORMArtifactDownloadError:
        return BORMArtifactDownloadError(message)

    def _artifact_error_prefix(self) -> str:
        return "BORM"

    def _cache_source_dir(self) -> str:
        return "borm"
