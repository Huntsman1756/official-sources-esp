from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from official_sources.hermes_bdns_observation import (
    BDNSObservationFetchResult,
    BDNSObservationResult,
    CommandResult,
    run_bdns_observation,
)


def _latest_payload() -> bytes:
    return json.dumps(
        {
            "content": [
                {
                    "numeroConvocatoria": "907362",
                    "descripcion": "Ayudas de prueba",
                    "fechaPublicacion": "2026-06-14",
                    "nivel1": "Ministerio",
                }
            ],
            "totalElements": 1,
            "totalPages": 1,
            "number": 0,
            "last": True,
        }
    ).encode("utf-8")


def test_bdns_observation_writes_api_runtime_jsonl_then_latest_observation(tmp_path):
    commands: list[tuple[list[str], Path]] = []

    def fake_fetch_latest(limit: int) -> BDNSObservationFetchResult:
        assert limit == 1
        return BDNSObservationFetchResult(
            content=_latest_payload(),
            final_url="https://www.infosubvenciones.es/bdnstrans/api/convocatorias/ultimas?page=1&pageSize=1",
            status_code=200,
            retry_count=0,
            throttle_triggered=False,
        )

    def fake_run_command(command: list[str], cwd: Path) -> CommandResult:
        commands.append((command, cwd))
        assert command[1:3] == ["hermes", "freshness-observations"]
        output_path = Path(command[command.index("--output") + 1])
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            '{"source":"BDNS","observed_at":"2026-06-13T10:15:00Z","timestamp_type":"observed"}\n',
            encoding="utf-8",
        )
        return CommandResult(returncode=0, stdout="observations_written=1\n", stderr="")

    result = run_bdns_observation(
        repo_root=tmp_path / "app",
        state_root=tmp_path / "state",
        official_sources_bin="/bin/official-sources",
        limit=1,
        fetch_latest=fake_fetch_latest,
        run_command=fake_run_command,
        now=lambda: datetime(2026, 6, 13, 10, 15, 0, tzinfo=UTC),
    )

    api_output_path = (
        tmp_path
        / "state"
        / "freshness-runtime"
        / "data"
        / "api_monitor"
        / "BDNS"
        / "2026-06-13"
        / "api_discovery.jsonl"
    ).resolve()
    observations_path = (
        tmp_path / "state" / "freshness-observations" / "latest-bdns.jsonl"
    ).resolve()
    records = [json.loads(line) for line in api_output_path.read_text(encoding="utf-8").splitlines()]

    assert result == BDNSObservationResult(
        exit_code=0,
        api_output_path=api_output_path,
        observations_path=observations_path,
        records_seen=1,
        latest_record_date="2026-06-14",
        fetch_status_code=200,
        observations_result=CommandResult(
            returncode=0,
            stdout="observations_written=1\n",
            stderr="",
        ),
    )
    assert records == [
        {
            "source_code": "BDNS",
            "discovered_at": "2026-06-13T10:15:00Z",
            "published_at": "2026-06-14",
            "timestamp_type": "observed",
            "observation_kind": "bdns_latest_observation",
            "official_identifier": "BDNS:907362",
            "source_url": "https://www.infosubvenciones.es/bdnstrans/api/convocatorias/ultimas?page=1&pageSize=1",
            "status_code": 200,
            "source_snapshot_hash": records[0]["source_snapshot_hash"],
            "records_seen": 1,
            "record_index": 1,
            "reason": "derived from operator-controlled BDNS latest API observation",
        }
    ]
    assert commands == [
        (
            [
                "/bin/official-sources",
                "hermes",
                "freshness-observations",
                "--runtime-root",
                str((tmp_path / "state" / "freshness-runtime").resolve()),
                "--source",
                "BDNS",
                "--output",
                str(observations_path),
            ],
            (tmp_path / "app").resolve(),
        )
    ]


def test_bdns_observation_fails_if_no_records_are_observed(tmp_path):
    def fake_fetch_latest(limit: int) -> BDNSObservationFetchResult:
        return BDNSObservationFetchResult(
            content=b'{"content":[],"totalElements":0,"totalPages":0,"number":0,"last":true}',
            final_url="https://example.test/empty",
            status_code=200,
            retry_count=0,
            throttle_triggered=False,
        )

    result = run_bdns_observation(
        repo_root=tmp_path / "app",
        state_root=tmp_path / "state",
        official_sources_bin="/bin/official-sources",
        fetch_latest=fake_fetch_latest,
        now=lambda: datetime(2026, 6, 13, 10, 15, 0, tzinfo=UTC),
    )

    assert result.exit_code == 2
    assert result.records_seen == 0
    assert not result.api_output_path.exists()
    assert "BDNS latest observation returned no records" in result.observations_result.stderr


def test_bdns_observation_fails_if_fetch_status_is_not_success(tmp_path):
    def fake_fetch_latest(limit: int) -> BDNSObservationFetchResult:
        return BDNSObservationFetchResult(
            content=_latest_payload(),
            final_url="https://example.test/server-error",
            status_code=500,
            retry_count=0,
            throttle_triggered=False,
        )

    result = run_bdns_observation(
        repo_root=tmp_path / "app",
        state_root=tmp_path / "state",
        official_sources_bin="/bin/official-sources",
        fetch_latest=fake_fetch_latest,
        now=lambda: datetime(2026, 6, 13, 10, 15, 0, tzinfo=UTC),
    )

    assert result.exit_code == 2
    assert result.records_seen == 0
    assert result.fetch_status_code == 500
    assert not result.api_output_path.exists()
    assert "BDNS latest observation returned HTTP 500" in result.observations_result.stderr


def test_bdns_observation_fails_if_latest_observation_output_is_missing(tmp_path):
    def fake_fetch_latest(limit: int) -> BDNSObservationFetchResult:
        return BDNSObservationFetchResult(
            content=_latest_payload(),
            final_url="https://example.test/latest",
            status_code=200,
            retry_count=0,
            throttle_triggered=False,
        )

    def fake_run_command(command: list[str], cwd: Path) -> CommandResult:
        return CommandResult(returncode=0, stdout="observations_written=1\n", stderr="")

    result = run_bdns_observation(
        repo_root=tmp_path / "app",
        state_root=tmp_path / "state",
        official_sources_bin="/bin/official-sources",
        fetch_latest=fake_fetch_latest,
        run_command=fake_run_command,
        now=lambda: datetime(2026, 6, 13, 10, 15, 0, tzinfo=UTC),
    )

    assert result.exit_code == 2
    assert result.records_seen == 1
    assert result.api_output_path.exists()
    assert "BDNS freshness observation JSONL was not written" in result.observations_result.stderr


def test_cli_bdns_observation_invokes_manual_wrapper(tmp_path, capsys, monkeypatch):
    from official_sources import cli

    calls = []

    def fake_run_bdns_observation(**kwargs):
        calls.append(kwargs)
        return BDNSObservationResult(
            exit_code=0,
            api_output_path=tmp_path
            / "state"
            / "freshness-runtime"
            / "data"
            / "api_monitor"
            / "BDNS"
            / "2026-06-13"
            / "api_discovery.jsonl",
            observations_path=tmp_path
            / "state"
            / "freshness-observations"
            / "latest-bdns.jsonl",
            records_seen=1,
            latest_record_date="2026-06-14",
            fetch_status_code=200,
            observations_result=CommandResult(
                returncode=0,
                stdout="observations_written=1\n",
                stderr="",
            ),
        )

    monkeypatch.setattr(cli, "run_bdns_observation", fake_run_bdns_observation)

    exit_code = cli.run(
        [
            "hermes",
            "bdns-observation",
            "--repo-root",
            str(tmp_path / "app"),
            "--state-root",
            str(tmp_path / "state"),
            "--official-sources-bin",
            "/bin/official-sources",
            "--limit",
            "1",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "api_output_path=" in captured.out
    assert "observations_path=" in captured.out
    assert "bdns_observation_exit_code=0" in captured.out
    assert "records_seen=1" in captured.out
    assert "latest_record_date=2026-06-14" in captured.out
    assert "fetch_status_code=200" in captured.out
    assert calls == [
        {
            "repo_root": tmp_path / "app",
            "state_root": tmp_path / "state",
            "official_sources_bin": "/bin/official-sources",
            "limit": 1,
        }
    ]
