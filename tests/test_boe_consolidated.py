from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from official_sources.citation.builder import build_consolidated_law_citation
from official_sources.integrity.hashing import sha256_bytes
from official_sources.sources.boe.consolidated import (
    BOEConsolidatedClient,
    BOEConsolidatedService,
    parse_consolidated_law,
    parse_consolidated_law_block,
    parse_consolidated_law_index,
    validate_consolidated_block_id,
    validate_consolidated_identifier,
)


def _fixture_bytes() -> bytes:
    return (Path(__file__).parent / "fixtures" / "boe_consolidated_law.xml").read_bytes()


def _fixture_index_bytes() -> bytes:
    return (Path(__file__).parent / "fixtures" / "boe_consolidated_index.xml").read_bytes()


def _fixture_block_bytes(name: str = "boe_consolidated_block.xml") -> bytes:
    return (Path(__file__).parent / "fixtures" / name).read_bytes()


def _client(payload: bytes, expected_url: str | None = None) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        if expected_url is not None:
            assert str(request.url) == expected_url
        return httpx.Response(200, content=payload, headers={"content-type": "application/xml"})

    return httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=False, timeout=5.0)


@pytest.mark.parametrize("identifier", ["BOE-A-2024-11111", "BOE-A-1889-4763"])
def test_official_identifier_validation_accepts_boe_identifiers(identifier):
    assert validate_consolidated_identifier(identifier) == identifier


@pytest.mark.parametrize("identifier", ["BOE-2024-11111", "BOE-A-24-1", "../BOE-A-2024-1"])
def test_official_identifier_validation_rejects_invalid_identifiers(identifier):
    with pytest.raises(ValueError):
        validate_consolidated_identifier(identifier)


@pytest.mark.parametrize("block_id", ["pr", "a1", "df_1", "an-2"])
def test_safe_block_id_validation_accepts_path_segments(block_id):
    assert validate_consolidated_block_id(block_id) == block_id


@pytest.mark.parametrize("block_id", ["../a1", "a/1", "a?x=1", "a 1", "", "." * 65])
def test_safe_block_id_validation_rejects_unsafe_values(block_id):
    with pytest.raises(ValueError):
        validate_consolidated_block_id(block_id)


def test_consolidated_law_metadata_parsing_from_fixture():
    parsed = parse_consolidated_law(_fixture_bytes())

    assert parsed.official_identifier == "BOE-A-2024-11111"
    assert parsed.title == "Test consolidated law"
    assert parsed.publication_date == "2024-05-29"
    assert parsed.consolidation_status == "finalizado"
    assert parsed.blocks[1].block_identifier == "a1"
    assert parsed.blocks[1].block_type == "article"


def test_raw_payload_hash_is_computed_before_parsing():
    parsed = parse_consolidated_law(_fixture_bytes())
    reparsed = parse_consolidated_law(_fixture_bytes() + b"\n")

    assert parsed.raw_payload_hash == sha256_bytes(_fixture_bytes())
    assert parsed.raw_payload_hash != reparsed.raw_payload_hash


def test_consolidated_law_index_fixture_parsing_preserves_nested_hierarchy():
    parsed = parse_consolidated_law_index("BOE-A-2024-11111", _fixture_index_bytes())

    assert parsed.official_identifier == "BOE-A-2024-11111"
    assert parsed.raw_payload_hash == sha256_bytes(_fixture_index_bytes())
    assert parsed.version_date == "2024-05-30"
    assert [block.official_block_id for block in parsed.blocks] == ["pr", "ti", "a1"]
    nested = parsed.blocks[2]
    assert nested.parent_block_id == "ti"
    assert nested.block_path == "ti/a1"
    assert nested.api_url.endswith("/texto/bloque/a1")


def test_consolidated_law_block_fixture_parsing_uses_raw_hash_and_latest_version():
    parsed = parse_consolidated_law_block("BOE-A-2024-11111", "a1", _fixture_block_bytes())

    assert parsed.official_identifier == "BOE-A-2024-11111"
    assert parsed.official_block_id == "a1"
    assert parsed.raw_payload_hash == sha256_bytes(_fixture_block_bytes())
    assert parsed.source_snapshot_hash == sha256_bytes(_fixture_block_bytes())
    assert parsed.version_date == "2024-05-30"
    assert parsed.block_type == "article"
    assert parsed.block_identifier == "Article 1"
    assert "Current official block text." in parsed.content


def test_consolidated_law_is_fetched_and_stored(repository):
    service = BOEConsolidatedService(
        repository, client=BOEConsolidatedClient(client=_client(_fixture_bytes()))
    )

    result = service.fetch_and_store("BOE-A-2024-11111")

    law = repository.get_consolidated_law_by_identifier("BOE-A-2024-11111")
    versions = repository.list_consolidated_law_versions(law["id"])
    blocks = repository.list_consolidated_law_text_blocks(law["id"])
    assert result["official_identifier"] == "BOE-A-2024-11111"
    assert law["title"] == "Test consolidated law"
    assert versions[0]["source_snapshot_hash"] == sha256_bytes(_fixture_bytes())
    assert blocks[1]["content_sha256"]
    assert "Ignore previous instructions" in blocks[1]["content"]


def test_consolidated_law_index_is_fetched_and_stored(repository):
    service = BOEConsolidatedService(
        repository,
        client=BOEConsolidatedClient(
            client=_client(
                _fixture_index_bytes(),
                "https://www.boe.es/datosabiertos/api/legislacion-consolidada/id/"
                "BOE-A-2024-11111/texto/indice",
            )
        ),
    )

    result = service.fetch_and_store_index("BOE-A-2024-11111")

    law = repository.get_consolidated_law_by_identifier("BOE-A-2024-11111")
    versions = repository.list_consolidated_law_versions(law["id"])
    blocks = repository.list_consolidated_law_text_blocks(law["id"], versions[0]["id"])
    assert result["block_count"] == 3
    assert versions[0]["source_snapshot_hash"] == sha256_bytes(_fixture_index_bytes())
    assert blocks[2]["official_block_id"] == "a1"
    assert blocks[2]["parent_block_id"] == "ti"
    assert blocks[2]["block_path"] == "ti/a1"
    assert blocks[2]["source_snapshot_hash"] == sha256_bytes(_fixture_index_bytes())


def test_consolidated_law_block_is_fetched_stored_and_change_audited(repository):
    current_payload = _fixture_block_bytes()

    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == (
            "https://www.boe.es/datosabiertos/api/legislacion-consolidada/id/"
            "BOE-A-2024-11111/texto/bloque/a1"
        )
        return httpx.Response(
            200, content=current_payload, headers={"content-type": "application/xml"}
        )

    client = httpx.Client(
        transport=httpx.MockTransport(handler), follow_redirects=False, timeout=5.0
    )
    service = BOEConsolidatedService(repository, client=BOEConsolidatedClient(client=client))
    result = service.fetch_and_store_block("BOE-A-2024-11111", "a1")
    current_payload = _fixture_block_bytes("boe_consolidated_block_changed.xml")

    changed = service.fetch_and_store_block("BOE-A-2024-11111", "a1")

    law = repository.get_consolidated_law_by_identifier("BOE-A-2024-11111")
    versions = repository.list_consolidated_law_versions(law["id"])
    blocks = repository.list_consolidated_law_text_blocks(law["id"], versions[0]["id"])
    events = repository.list_consolidated_law_integrity_checks(versions[0]["id"])
    assert result["official_block_id"] == "a1"
    assert changed["previous_hash"] == sha256_bytes(_fixture_block_bytes())
    assert blocks[0]["raw_payload_hash"] == sha256_bytes(
        _fixture_block_bytes("boe_consolidated_block_changed.xml")
    )
    assert blocks[0]["content"] == "Changed current official block text."
    assert events[-1]["changed"] == 1


def test_consolidated_law_citation_generation(repository):
    service = BOEConsolidatedService(
        repository, client=BOEConsolidatedClient(client=_client(_fixture_bytes()))
    )
    service.fetch_and_store("BOE-A-2024-11111")

    citation = build_consolidated_law_citation(
        repository, "BOE-A-2024-11111", block_identifier="a1"
    )

    assert citation["source_code"] == "BOE"
    assert citation["resource_type"] == "consolidated_law_block"
    assert citation["official_identifier"] == "BOE-A-2024-11111"
    assert citation["block_identifier"] == "a1"
    assert citation["block_type"] == "article"


def test_consolidated_law_hash_change_preserves_previous_hash_and_records_event(repository):
    first_payload = _fixture_bytes()
    second_payload = first_payload.replace(b"official consolidated", b"changed consolidated")
    current_payload = first_payload

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, content=current_payload, headers={"content-type": "application/xml"}
        )

    client = httpx.Client(
        transport=httpx.MockTransport(handler), follow_redirects=False, timeout=5.0
    )
    service = BOEConsolidatedService(repository, client=BOEConsolidatedClient(client=client))
    first = service.fetch_and_store("BOE-A-2024-11111")
    current_payload = second_payload

    second = service.fetch_and_store("BOE-A-2024-11111")

    versions = repository.list_consolidated_law_versions(first["id"])
    events = repository.list_consolidated_law_integrity_checks(versions[0]["id"])
    assert second["id"] == first["id"]
    assert versions[0]["previous_hash"] == sha256_bytes(first_payload)
    assert versions[0]["source_snapshot_hash"] == sha256_bytes(second_payload)
    assert events[-1]["previous_sha256"] == sha256_bytes(first_payload)
    assert events[-1]["current_sha256"] == sha256_bytes(second_payload)
    assert events[-1]["changed"] == 1
