from __future__ import annotations

from pathlib import Path
from urllib.parse import urlsplit

import httpx

from official_sources.sources.boe.artifacts import (
    BOEArtifactDownloader,
    BOEArtifactDownloadError,
)
from official_sources.storage.repository import OfficialSourcesRepository

DOGV_ALLOWED_HOSTS = {"dogv.gva.es"}
DOGV_ARTIFACT_FIELDS = {
    "pdf": ("url_pdf", "document.pdf", "application/pdf"),
}


class DOGVArtifactDownloadError(BOEArtifactDownloadError):
    pass


def validate_dogv_artifact_url(url: str) -> str:
    parsed = urlsplit(url)
    if parsed.scheme != "https":
        raise DOGVArtifactDownloadError("DOGV artifact URLs must use HTTPS")
    if parsed.hostname not in DOGV_ALLOWED_HOSTS:
        raise DOGVArtifactDownloadError("DOGV artifact URLs must use an official DOGV host")
    if not parsed.path.startswith("/datos/"):
        raise DOGVArtifactDownloadError("DOGV artifact URLs must use an official DOGV data path")
    if not parsed.path.lower().endswith(".pdf"):
        raise DOGVArtifactDownloadError("DOGV artifact URL must point to a PDF")
    return url


class DOGVArtifactDownloader(BOEArtifactDownloader):
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
        return DOGV_ARTIFACT_FIELDS

    def _validate_artifact_url(self, url: str) -> str:
        return validate_dogv_artifact_url(url)

    def _artifact_error(self, message: str) -> DOGVArtifactDownloadError:
        return DOGVArtifactDownloadError(message)

    def _artifact_error_prefix(self) -> str:
        return "DOGV"

    def _cache_source_dir(self) -> str:
        return "dogv"
