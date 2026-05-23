from __future__ import annotations

from pathlib import Path
from urllib.parse import urlsplit

import httpx

from official_sources.sources.boe.artifacts import (
    BOEArtifactDownloader,
    BOEArtifactDownloadError,
)
from official_sources.storage.repository import OfficialSourcesRepository

BOCYL_ALLOWED_HOSTS = {"bocyl.jcyl.es", "www.bocyl.jcyl.es"}
BOCYL_ARTIFACT_FIELDS = {
    "xml": ("url_xml", "document.xml", "application/xml"),
    "html": ("url_html", "document.html", "text/html"),
    "pdf": ("url_pdf", "document.pdf", "application/pdf"),
}


class BOCYLArtifactDownloadError(BOEArtifactDownloadError):
    pass


def validate_bocyl_artifact_url(url: str) -> str:
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"}:
        raise BOCYLArtifactDownloadError("BOCYL artifact URLs must use HTTP or HTTPS")
    if parsed.hostname not in BOCYL_ALLOWED_HOSTS:
        raise BOCYLArtifactDownloadError("BOCYL artifact URLs must use an official BOCYL host")
    if not parsed.path:
        raise BOCYLArtifactDownloadError("BOCYL artifact URLs must include a path")
    return url


class BOCYLArtifactDownloader(BOEArtifactDownloader):
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
        return BOCYL_ARTIFACT_FIELDS

    def _validate_artifact_url(self, url: str) -> str:
        return validate_bocyl_artifact_url(url)

    def _artifact_error(self, message: str) -> BOCYLArtifactDownloadError:
        return BOCYLArtifactDownloadError(message)

    def _artifact_error_prefix(self) -> str:
        return "BOCYL"

    def _cache_source_dir(self) -> str:
        return "bocyl"
