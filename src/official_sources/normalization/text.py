from __future__ import annotations

import re
from dataclasses import dataclass

from official_sources.integrity.hashing import sha256_text


@dataclass(frozen=True)
class NormalizedText:
    text_type: str
    language: str
    content: str
    content_sha256: str
    extraction_method: str


def clean_text(content: str) -> str:
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in content.strip().splitlines()]
    return "\n".join(line for line in lines if line)


def normalize_document_text(content: str, language: str = "es") -> NormalizedText:
    normalized = clean_text(content)
    return NormalizedText(
        text_type="clean_text",
        language=language,
        content=normalized,
        content_sha256=sha256_text(normalized),
        extraction_method="deterministic_whitespace_cleanup",
    )
