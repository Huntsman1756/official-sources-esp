from __future__ import annotations

from pathlib import Path

import httpx

from official_sources.storage.database import connect
from official_sources.storage.repository import OfficialSourcesRepository


def _fixture_bytes() -> bytes:
    return (Path(__file__).parent / "fixtures" / "boe_consolidated_law.xml").read_bytes()


def _fixture_index_bytes() -> bytes:
    return (Path(__file__).parent / "fixtures" / "boe_consolidated_index.xml").read_bytes()


def _fixture_block_bytes() -> bytes:
    return (Path(__file__).parent / "fixtures" / "boe_consolidated_block.xml").read_bytes()


def _client(payload: bytes | None = None) -> httpx.Client:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            content=payload or _fixture_bytes(),
            headers={"content-type": "application/xml"},
        )

    return httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=False, timeout=5.0)


def test_cli_consolidated_get_works_with_mocked_api(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "boe-consolidated-get",
            "--identifier",
            "BOE-A-2024-11111",
        ],
        consolidated_client=_client(),
    )

    connection = connect(str(db_path))
    repository = OfficialSourcesRepository(connection)
    law = repository.get_consolidated_law_by_identifier("BOE-A-2024-11111")
    captured = capsys.readouterr()
    assert exit_code == 0
    assert law["title"] == "Test consolidated law"
    assert "official_identifier=BOE-A-2024-11111" in captured.out


def test_cli_consolidated_get_rejects_invalid_identifier(tmp_path, capsys):
    from official_sources.cli import run

    exit_code = run(
        [
            "--db-path",
            str(tmp_path / "db.sqlite"),
            "boe-consolidated-get",
            "--identifier",
            "../BOE-A-2024-11111",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "BOE-A-YYYY-NNNNN" in captured.err


def test_cli_consolidated_index_get_works_with_mocked_api(tmp_path, capsys):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "boe-consolidated-index-get",
            "--identifier",
            "BOE-A-2024-11111",
        ],
        consolidated_client=_client(_fixture_index_bytes()),
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "official_identifier=BOE-A-2024-11111" in captured.out
    assert "index_blocks=3" in captured.out


def test_cli_consolidated_block_get_works_with_mocked_api_and_does_not_print_content_by_default(
    tmp_path, capsys
):
    from official_sources.cli import run

    db_path = tmp_path / "db.sqlite"

    exit_code = run(
        [
            "--db-path",
            str(db_path),
            "boe-consolidated-block-get",
            "--identifier",
            "BOE-A-2024-11111",
            "--block-id",
            "a1",
        ],
        consolidated_client=_client(_fixture_block_bytes()),
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "block_id=a1" in captured.out
    assert "Current official block text." not in captured.out


def test_cli_consolidated_block_get_print_content_is_explicit(tmp_path, capsys):
    from official_sources.cli import run

    exit_code = run(
        [
            "--db-path",
            str(tmp_path / "db.sqlite"),
            "boe-consolidated-block-get",
            "--identifier",
            "BOE-A-2024-11111",
            "--block-id",
            "a1",
            "--print-content",
        ],
        consolidated_client=_client(_fixture_block_bytes()),
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Current official block text." in captured.out


def test_cli_consolidated_index_get_rejects_invalid_identifier(tmp_path, capsys):
    from official_sources.cli import run

    exit_code = run(
        [
            "--db-path",
            str(tmp_path / "db.sqlite"),
            "boe-consolidated-index-get",
            "--identifier",
            "BOE-A-24-1",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "BOE-A-YYYY-NNNNN" in captured.err


def test_cli_consolidated_block_get_rejects_unsafe_block_id(tmp_path, capsys):
    from official_sources.cli import run

    exit_code = run(
        [
            "--db-path",
            str(tmp_path / "db.sqlite"),
            "boe-consolidated-block-get",
            "--identifier",
            "BOE-A-2024-11111",
            "--block-id",
            "../a1",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "safe BOE block path segment" in captured.err
