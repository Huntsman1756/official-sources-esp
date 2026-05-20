from __future__ import annotations

from pathlib import Path
from urllib.parse import urlsplit

import httpx

from official_sources.sources.boe.artifacts import (
    BOEArtifactDownloader,
    BOEArtifactDownloadError,
)
from official_sources.storage.repository import OfficialSourcesRepository

BOJA_ALLOWED_HOSTS = {"www.juntadeandalucia.es", "juntadeandalucia.es"}
BOJA_ARTIFACT_FIELDS = {
    "pdf": ("url_pdf", "document.pdf", "application/pdf"),
}


class BOJAArtifactDownloadError(BOEArtifactDownloadError):
    pass


def validate_boja_artifact_url(url: str) -> str:
    parsed = urlsplit(url)
    if parsed.scheme != "https":
        raise BOJAArtifactDownloadError("BOJA artifact URLs must use HTTPS")
    if parsed.hostname not in BOJA_ALLOWED_HOSTS:
        raise BOJAArtifactDownloadError("BOJA artifact URLs must use an official BOJA host")
    if not parsed.path.startswith("/eboja/"):
        raise BOJAArtifactDownloadError("BOJA artifact URLs must use an official eBOJA path")
    if not parsed.path.lower().endswith(".pdf"):
        raise BOJAArtifactDownloadError("BOJA artifact URL must point to a PDF")
    return url


class BOJAArtifactDownloader(BOEArtifactDownloader):
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
        return BOJA_ARTIFACT_FIELDS

    def _validate_artifact_url(self, url: str) -> str:
        return validate_boja_artifact_url(url)

    def _artifact_error(self, message: str) -> BOJAArtifactDownloadError:
        return BOJAArtifactDownloadError(message)

    def _artifact_error_prefix(self) -> str:
        return "BOJA"

    def _cache_source_dir(self) -> str:
        return "boja"
