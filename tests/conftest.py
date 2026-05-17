from __future__ import annotations

import json
from pathlib import Path

import pytest

from official_sources.storage.database import connect, initialize_database
from official_sources.storage.repository import OfficialSourcesRepository

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def repository() -> OfficialSourcesRepository:
    connection = connect(":memory:")
    initialize_database(connection)
    repo = OfficialSourcesRepository(connection)
    repo.ensure_official_source_boe()
    return repo


@pytest.fixture
def boe_summary_payload() -> bytes:
    return (FIXTURES / "boe_summary_20240529.json").read_bytes()


@pytest.fixture
def boe_summary_json() -> dict:
    return json.loads((FIXTURES / "boe_summary_20240529.json").read_text(encoding="utf-8"))


@pytest.fixture
def instruction_like_text() -> str:
    return (FIXTURES / "instruction_like_text.txt").read_text(encoding="utf-8")
