from __future__ import annotations

import re
import time
from collections.abc import Callable
from dataclasses import dataclass
from xml.etree import ElementTree

import httpx

from official_sources.integrity.hashing import sha256_bytes, sha256_text
from official_sources.normalization.text import clean_text
from official_sources.sources.boe.http_policy import BOERequestAudit, BOERequestPolicy
from official_sources.storage.repository import OfficialSourcesRepository

CONSOLIDATED_IDENTIFIER_RE = re.compile(r"^BOE-A-\d{4}-\d+$")
CONSOLIDATED_BLOCK_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
CONSOLIDATED_ENDPOINT = "https://www.boe.es/datosabiertos/api/legislacion-consolidada/id/{id}"
CONSOLIDATED_INDEX_ENDPOINT = (
    "https://www.boe.es/datosabiertos/api/legislacion-consolidada/id/{id}/texto/indice"
)
CONSOLIDATED_BLOCK_ENDPOINT = (
    "https://www.boe.es/datosabiertos/api/legislacion-consolidada/id/{id}/texto/bloque/{block_id}"
)
BLOCK_TYPE_MAP = {
    "preambulo": "preamble",
    "preámbulo": "preamble",
    "articulo": "article",
    "artículo": "article",
    "disposicion_adicional": "additional_provision",
    "disposición_adicional": "additional_provision",
    "disposicion_transitoria": "transitional_provision",
    "disposición_transitoria": "transitional_provision",
    "disposicion_derogatoria": "derogatory_provision",
    "disposición_derogatoria": "derogatory_provision",
    "disposicion_final": "final_provision",
    "disposición_final": "final_provision",
    "anexo": "annex",
}


@dataclass(frozen=True)
class ConsolidatedTextBlock:
    block_type: str
    block_identifier: str
    title: str | None
    content: str
    order_index: int


@dataclass(frozen=True)
class ParsedConsolidatedLaw:
    official_identifier: str
    title: str
    law_type: str | None
    jurisdiction: str
    department: str | None
    publication_date: str | None
    consolidation_status: str | None
    official_url: str
    raw_payload_hash: str
    raw_metadata: dict[str, str | None]
    blocks: list[ConsolidatedTextBlock]


@dataclass(frozen=True)
class ConsolidatedLawIndexBlock:
    official_block_id: str
    block_type: str
    block_identifier: str
    title: str | None
    order_index: int
    parent_block_id: str | None
    block_path: str
    api_url: str
    version_date: str | None
    raw_metadata: dict[str, str | None]


@dataclass(frozen=True)
class ParsedConsolidatedLawIndex:
    official_identifier: str
    version_date: str | None
    api_url: str
    raw_payload_hash: str
    source_snapshot_hash: str
    blocks: list[ConsolidatedLawIndexBlock]


@dataclass(frozen=True)
class ParsedConsolidatedLawBlock:
    official_identifier: str
    official_block_id: str
    block_type: str
    block_identifier: str
    title: str | None
    content: str
    version_date: str | None
    api_url: str
    raw_payload_hash: str
    source_snapshot_hash: str
    raw_metadata: dict[str, str | None]


def validate_consolidated_identifier(identifier: str) -> str:
    if not CONSOLIDATED_IDENTIFIER_RE.match(identifier):
        raise ValueError("Consolidated law identifiers must use BOE-A-YYYY-NNNNN format")
    return identifier


def validate_consolidated_block_id(block_id: str) -> str:
    if not CONSOLIDATED_BLOCK_ID_RE.match(block_id):
        raise ValueError("Consolidated law block IDs must be a safe BOE block path segment")
    return block_id


class BOEConsolidatedClient:
    def __init__(
        self,
        client: httpx.Client | None = None,
        timeout: float = 30.0,
        *,
        request_policy: BOERequestPolicy | None = None,
        sleeper: Callable[[float], None] | None = None,
    ) -> None:
        self.client = client
        self.timeout = timeout
        self.request_policy = request_policy or BOERequestPolicy.from_env()
        self.sleeper = sleeper or time.sleep
        self.last_request_audit = BOERequestAudit()

    def fetch_law(self, identifier: str) -> bytes:
        identifier = validate_consolidated_identifier(identifier)
        url = CONSOLIDATED_ENDPOINT.format(id=identifier)
        return self._get_xml(url)

    def fetch_index(self, identifier: str) -> bytes:
        identifier = validate_consolidated_identifier(identifier)
        url = CONSOLIDATED_INDEX_ENDPOINT.format(id=identifier)
        return self._get_xml(url)

    def fetch_block(self, identifier: str, block_id: str) -> bytes:
        identifier = validate_consolidated_identifier(identifier)
        block_id = validate_consolidated_block_id(block_id)
        url = CONSOLIDATED_BLOCK_ENDPOINT.format(id=identifier, block_id=block_id)
        return self._get_xml(url)

    def _get_xml(self, url: str) -> bytes:
        headers = {"Accept": "application/xml"}
        if self.client is not None:
            result = self.request_policy.get(
                url,
                headers=headers,
                client=self.client,
                sleeper=self.sleeper,
            )
        else:
            with httpx.Client(follow_redirects=False, timeout=self.timeout) as client:
                result = self.request_policy.get(
                    url,
                    headers=headers,
                    client=client,
                    sleeper=self.sleeper,
                )
        self.last_request_audit = result.audit
        result.raise_for_status()
        return result.content


class BOEConsolidatedService:
    def __init__(
        self,
        repository: OfficialSourcesRepository,
        *,
        client: BOEConsolidatedClient | None = None,
    ) -> None:
        self.repository = repository
        self.client = client or BOEConsolidatedClient()

    def fetch_and_store(self, identifier: str) -> dict:
        payload = self.client.fetch_law(identifier)
        parsed = parse_consolidated_law(payload)
        source = self.repository.ensure_official_source_boe()
        law = self.repository.upsert_consolidated_law(
            source_id=source["id"],
            external_id=parsed.official_identifier,
            official_identifier=parsed.official_identifier,
            title=parsed.title,
            law_type=parsed.law_type,
            jurisdiction=parsed.jurisdiction,
            department=parsed.department,
            publication_date=parsed.publication_date,
            consolidation_status=parsed.consolidation_status,
            official_url=parsed.official_url,
            raw_metadata=parsed.raw_metadata,
        )
        version_identifier = f"{parsed.official_identifier}:{parsed.publication_date or 'current'}"
        version = self.repository.upsert_consolidated_law_version(
            consolidated_law_id=law["id"],
            version_identifier=version_identifier,
            version_date=parsed.publication_date,
            valid_from=parsed.publication_date,
            valid_to=None,
            is_current=True,
            official_url=parsed.official_url,
            raw_payload_hash=parsed.raw_payload_hash,
            source_snapshot_hash=parsed.raw_payload_hash,
        )
        self.repository.replace_consolidated_law_text_blocks(
            consolidated_law_id=law["id"],
            version_id=version["id"],
            blocks=[
                {
                    "block_type": block.block_type,
                    "block_identifier": block.block_identifier,
                    "title": block.title,
                    "content": block.content,
                    "content_sha256": sha256_text(block.content),
                    "source_snapshot_hash": parsed.raw_payload_hash,
                    "order_index": block.order_index,
                }
                for block in parsed.blocks
            ],
        )
        return law

    def fetch_and_store_index(self, identifier: str) -> dict:
        payload = self.client.fetch_index(identifier)
        parsed = parse_consolidated_law_index(identifier, payload)
        law = self._ensure_law_shell(parsed.official_identifier)
        version = self.repository.upsert_consolidated_law_version(
            consolidated_law_id=law["id"],
            version_identifier=f"{parsed.official_identifier}:text-index",
            version_date=parsed.version_date,
            valid_from=None,
            valid_to=None,
            is_current=True,
            official_url=parsed.api_url,
            raw_payload_hash=parsed.raw_payload_hash,
            source_snapshot_hash=parsed.source_snapshot_hash,
        )
        for block in parsed.blocks:
            self.repository.upsert_consolidated_law_text_block(
                consolidated_law_id=law["id"],
                version_id=version["id"],
                official_block_id=block.official_block_id,
                parent_block_id=block.parent_block_id,
                block_path=block.block_path,
                api_url=block.api_url,
                block_type=block.block_type,
                block_identifier=block.block_identifier,
                title=block.title,
                content="",
                content_sha256=sha256_text(""),
                raw_payload_hash=parsed.raw_payload_hash,
                source_snapshot_hash=parsed.source_snapshot_hash,
                order_index=block.order_index,
                raw_metadata=block.raw_metadata,
            )
        return {
            "official_identifier": parsed.official_identifier,
            "version_date": parsed.version_date,
            "source_snapshot_hash": parsed.source_snapshot_hash,
            "block_count": len(parsed.blocks),
        }

    def fetch_and_store_block(self, identifier: str, block_id: str) -> dict:
        payload = self.client.fetch_block(identifier, block_id)
        parsed = parse_consolidated_law_block(identifier, block_id, payload)
        law = self._ensure_law_shell(parsed.official_identifier)
        version = self.repository.upsert_consolidated_law_version(
            consolidated_law_id=law["id"],
            version_identifier=f"{parsed.official_identifier}:block:{parsed.official_block_id}",
            version_date=parsed.version_date,
            valid_from=None,
            valid_to=None,
            is_current=True,
            official_url=parsed.api_url,
            raw_payload_hash=parsed.raw_payload_hash,
            source_snapshot_hash=parsed.source_snapshot_hash,
        )
        return self.repository.upsert_consolidated_law_text_block(
            consolidated_law_id=law["id"],
            version_id=version["id"],
            official_block_id=parsed.official_block_id,
            parent_block_id=None,
            block_path=parsed.official_block_id,
            api_url=parsed.api_url,
            block_type=parsed.block_type,
            block_identifier=parsed.block_identifier,
            title=parsed.title,
            content=parsed.content,
            content_sha256=sha256_text(parsed.content),
            raw_payload_hash=parsed.raw_payload_hash,
            source_snapshot_hash=parsed.source_snapshot_hash,
            order_index=0,
            raw_metadata=parsed.raw_metadata,
        )

    def _ensure_law_shell(self, identifier: str) -> dict:
        existing = self.repository.get_consolidated_law_by_identifier(identifier)
        if existing is not None:
            return existing
        source = self.repository.ensure_official_source_boe()
        return self.repository.upsert_consolidated_law(
            source_id=source["id"],
            external_id=identifier,
            official_identifier=identifier,
            title=identifier,
            law_type=None,
            jurisdiction="state",
            department=None,
            publication_date=None,
            consolidation_status=None,
            official_url=CONSOLIDATED_ENDPOINT.format(id=identifier),
            raw_metadata={"placeholder": "created_from_consolidated_text_endpoint"},
        )


def parse_consolidated_law(payload: bytes) -> ParsedConsolidatedLaw:
    raw_hash = sha256_bytes(payload)
    root = ElementTree.fromstring(payload)
    metadata = root.find("./data/metadatos")
    if metadata is None:
        raise ValueError("BOE consolidated response does not include metadata")
    identifier = _required_text(metadata, "identificador")
    validate_consolidated_identifier(identifier)
    publication_date = _format_boe_date(_optional_text(metadata, "fecha_publicacion"))
    official_url = _optional_text(metadata, "url_html") or CONSOLIDATED_ENDPOINT.format(
        id=identifier
    )
    raw_metadata = {
        child.tag: clean_text(" ".join(child.itertext())) if list(child) else _node_text(child)
        for child in metadata
    }
    return ParsedConsolidatedLaw(
        official_identifier=identifier,
        title=_required_text(metadata, "titulo"),
        law_type=_optional_text(metadata, "rango"),
        jurisdiction="state",
        department=_optional_text(metadata, "departamento"),
        publication_date=publication_date,
        consolidation_status=_optional_text(metadata, "estado_consolidacion"),
        official_url=official_url,
        raw_payload_hash=raw_hash,
        raw_metadata=raw_metadata,
        blocks=_parse_blocks(root),
    )


def parse_consolidated_law_index(
    identifier: str,
    payload: bytes,
) -> ParsedConsolidatedLawIndex:
    identifier = validate_consolidated_identifier(identifier)
    raw_hash = sha256_bytes(payload)
    root = ElementTree.fromstring(payload)
    blocks: list[ConsolidatedLawIndexBlock] = []
    for block in root.findall("./data/bloque"):
        _append_index_block(
            block,
            blocks=blocks,
            parent_block_id=None,
            parent_path="",
            order_index=len(blocks),
            identifier=identifier,
        )
    version_dates = [block.version_date for block in blocks if block.version_date]
    return ParsedConsolidatedLawIndex(
        official_identifier=identifier,
        version_date=max(version_dates) if version_dates else None,
        api_url=CONSOLIDATED_INDEX_ENDPOINT.format(id=identifier),
        raw_payload_hash=raw_hash,
        source_snapshot_hash=raw_hash,
        blocks=blocks,
    )


def parse_consolidated_law_block(
    identifier: str,
    block_id: str,
    payload: bytes,
) -> ParsedConsolidatedLawBlock:
    identifier = validate_consolidated_identifier(identifier)
    block_id = validate_consolidated_block_id(block_id)
    raw_hash = sha256_bytes(payload)
    root = ElementTree.fromstring(payload)
    block = root.find("./data/bloque")
    if block is None:
        raise ValueError("BOE consolidated block response does not include a block")
    official_block_id = block.attrib.get("id") or _direct_child_text(block, "id") or block_id
    validate_consolidated_block_id(official_block_id)
    title = block.attrib.get("titulo") or _direct_child_text(block, "titulo")
    versions = block.findall("version")
    selected = versions[-1] if versions else block
    content = clean_text(" ".join(selected.itertext()))
    if title and content.startswith(title):
        content = clean_text(content[len(title) :])
    version_date = _format_boe_date(
        selected.attrib.get("fecha_publicacion") or selected.attrib.get("fecha_vigencia")
    )
    return ParsedConsolidatedLawBlock(
        official_identifier=identifier,
        official_block_id=official_block_id,
        block_type=_normalize_block_type(block.attrib.get("tipo"), title),
        block_identifier=title or official_block_id,
        title=title,
        content=content,
        version_date=version_date,
        api_url=CONSOLIDATED_BLOCK_ENDPOINT.format(id=identifier, block_id=official_block_id),
        raw_payload_hash=raw_hash,
        source_snapshot_hash=raw_hash,
        raw_metadata=_block_raw_metadata(block),
    )


def _append_index_block(
    block: ElementTree.Element,
    *,
    blocks: list[ConsolidatedLawIndexBlock],
    parent_block_id: str | None,
    parent_path: str,
    order_index: int,
    identifier: str,
) -> None:
    official_block_id = _direct_child_text(block, "id") or block.attrib.get("id")
    if not official_block_id:
        raise ValueError("BOE consolidated index block does not include an id")
    validate_consolidated_block_id(official_block_id)
    title = _direct_child_text(block, "titulo") or block.attrib.get("titulo")
    version_date = _format_boe_date(_direct_child_text(block, "fecha_actualizacion"))
    block_path = f"{parent_path}/{official_block_id}" if parent_path else official_block_id
    api_url = _direct_child_text(block, "url") or CONSOLIDATED_BLOCK_ENDPOINT.format(
        id=identifier,
        block_id=official_block_id,
    )
    blocks.append(
        ConsolidatedLawIndexBlock(
            official_block_id=official_block_id,
            block_type=_normalize_block_type(block.attrib.get("tipo"), title),
            block_identifier=title or official_block_id,
            title=title,
            order_index=order_index,
            parent_block_id=parent_block_id,
            block_path=block_path,
            api_url=api_url,
            version_date=version_date,
            raw_metadata=_block_raw_metadata(block),
        )
    )
    for child in block.findall("bloque"):
        _append_index_block(
            child,
            blocks=blocks,
            parent_block_id=official_block_id,
            parent_path=block_path,
            order_index=len(blocks),
            identifier=identifier,
        )


def _parse_blocks(root: ElementTree.Element) -> list[ConsolidatedTextBlock]:
    blocks: list[ConsolidatedTextBlock] = []
    for index, block in enumerate(root.findall("./data/texto/bloque")):
        identifier = block.attrib.get("id") or f"block-{index + 1}"
        title = _optional_text(block, "titulo")
        version = block.find("version")
        content_source = version if version is not None else block
        content = clean_text(" ".join(content_source.itertext()))
        if title and content.startswith(title):
            content = clean_text(content[len(title) :])
        blocks.append(
            ConsolidatedTextBlock(
                block_type=_normalize_block_type(block.attrib.get("tipo"), title),
                block_identifier=identifier,
                title=title,
                content=content,
                order_index=index,
            )
        )
    if not blocks:
        text = root.find("./data/texto")
        if text is not None:
            content = clean_text(" ".join(text.itertext()))
            if content:
                blocks.append(
                    ConsolidatedTextBlock(
                        block_type="unknown",
                        block_identifier="full_text",
                        title="Full text",
                        content=content,
                        order_index=0,
                    )
                )
    return blocks


def _normalize_block_type(raw_type: str | None, title: str | None) -> str:
    value = (raw_type or title or "").strip().lower().replace(" ", "_")
    if value.startswith("art"):
        return "article"
    if value.startswith("anexo"):
        return "annex"
    return BLOCK_TYPE_MAP.get(value, "unknown")


def _required_text(parent: ElementTree.Element, tag: str) -> str:
    value = _optional_text(parent, tag)
    if not value:
        raise ValueError(f"BOE consolidated response missing required field: {tag}")
    return value


def _optional_text(parent: ElementTree.Element, tag: str) -> str | None:
    node = parent.find(tag)
    if node is None:
        return None
    return _node_text(node)


def _direct_child_text(parent: ElementTree.Element, tag: str) -> str | None:
    for child in parent:
        if child.tag == tag:
            return _node_text(child)
    return None


def _node_text(node: ElementTree.Element) -> str | None:
    content = clean_text(" ".join(node.itertext()))
    return content or None


def _block_raw_metadata(block: ElementTree.Element) -> dict[str, str | None]:
    metadata: dict[str, str | None] = {f"@{key}": value for key, value in block.attrib.items()}
    for child in block:
        if child.tag in {"bloque", "version"}:
            continue
        metadata[child.tag] = _node_text(child)
    return metadata


def _format_boe_date(value: str | None) -> str | None:
    if value is None:
        return None
    if len(value) == 8 and value.isdigit():
        return f"{value[:4]}-{value[4:6]}-{value[6:]}"
    return value
