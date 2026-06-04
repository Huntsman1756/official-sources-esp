from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path


def test_cli_scheduled_audit_returns_runner_exit_code(tmp_path, monkeypatch):
    from official_sources import cli
    from official_sources.hermes_scheduled_audit import (
        CommandResult,
        ScheduledStrictAuditResult,
    )

    captured: dict[str, object] = {}

    def fake_run_scheduled_strict_audit(**kwargs):
        captured.update(kwargs)
        return ScheduledStrictAuditResult(
            exit_code=1,
            report_path=tmp_path / "report.md",
            strict_report_path=tmp_path / "strict.md",
            log_path=tmp_path / "report.log",
            strict_result=CommandResult(returncode=1, stdout="VERDICT: NO-GO\n", stderr=""),
            watchdog_results=(),
        )

    monkeypatch.setattr(cli, "run_scheduled_strict_audit", fake_run_scheduled_strict_audit)

    exit_code = cli.run(
        [
            "hermes",
            "scheduled-audit",
            "--repo-root",
            str(tmp_path / "app"),
            "--state-root",
            str(tmp_path / "state"),
            "--release-contract",
            str(tmp_path / "contract.yaml"),
            "--official-sources-bin",
            "official-sources",
        ]
    )

    assert exit_code == 1
    assert captured["repo_root"] == tmp_path / "app"
    assert captured["state_root"] == tmp_path / "state"
    assert captured["release_contract"] == tmp_path / "contract.yaml"
    assert captured["official_sources_bin"] == "official-sources"


def test_scheduled_strict_audit_propagates_no_go_and_preserves_watchdog_report(tmp_path):
    from official_sources.hermes_scheduled_audit import (
        CommandResult,
        run_scheduled_strict_audit,
    )

    repo_root = tmp_path / "app"
    repo_root.mkdir()
    state_root = tmp_path / "state"
    release_contract = tmp_path / "hermes-audit-contract.yaml"
    release_contract.write_text(
        'release:\n  expected_head_sha: "expected-sha"\n',
        encoding="utf-8",
    )
    calls: list[tuple[tuple[str, ...], Path]] = []

    def fake_run(command: list[str], cwd: Path) -> CommandResult:
        calls.append((tuple(command), cwd))
        if command[:3] == [
            "/opt/official-sources/app/.venv/bin/official-sources",
            "hermes",
            "audit",
        ]:
            return CommandResult(
                returncode=1,
                stdout="VERDICT: NO-GO\n\nFailed gates:\n- actual HEAD != expected\n",
                stderr="",
            )
        return CommandResult(returncode=0, stdout="0 loaded units listed\n", stderr="")

    result = run_scheduled_strict_audit(
        repo_root=repo_root,
        state_root=state_root,
        release_contract=release_contract,
        official_sources_bin="/opt/official-sources/app/.venv/bin/official-sources",
        run_command=fake_run,
        now=lambda: datetime(2026, 6, 4, 12, 30, tzinfo=UTC),
    )

    assert result.exit_code == 1
    assert calls[0][0] == (
        "/opt/official-sources/app/.venv/bin/official-sources",
        "hermes",
        "audit",
        "--repo-root",
        str(repo_root),
        "--registry",
        str(repo_root / "config" / "sources.yaml"),
        "--project-state",
        str(repo_root / "PROJECT_STATE.md"),
        "--release-contract",
        str(release_contract),
        "--strict-release-contract",
        "--fail-on-no-go",
        "--output",
        str(state_root / "reports" / "strict-release-audit-20260604-123000.md"),
    )
    assert any(command[:3] == ("systemctl", "--failed", "--no-pager") for command, _cwd in calls)

    rendered = result.report_path.read_text(encoding="utf-8")
    assert "Strict release audit exit code: 1" in rendered
    assert "VERDICT: NO-GO" in rendered
    assert "Failed gates:" in rendered
    assert "systemctl --failed --no-pager" in rendered


def test_scheduled_strict_audit_keeps_warning_as_success_when_cli_exit_is_zero(tmp_path):
    from official_sources.hermes_scheduled_audit import (
        CommandResult,
        run_scheduled_strict_audit,
    )

    repo_root = tmp_path / "app"
    repo_root.mkdir()
    state_root = tmp_path / "state"
    release_contract = tmp_path / "hermes-audit-contract.yaml"
    release_contract.write_text("release: {}\n", encoding="utf-8")

    def fake_run(command: list[str], cwd: Path) -> CommandResult:
        if command[:3] == ["official-sources", "hermes", "audit"]:
            return CommandResult(
                returncode=0,
                stdout="VERDICT: WARNING\n\nFailed gates:\n- none\n",
                stderr="",
            )
        return CommandResult(returncode=0, stdout="watchdog ok\n", stderr="")

    result = run_scheduled_strict_audit(
        repo_root=repo_root,
        state_root=state_root,
        release_contract=release_contract,
        official_sources_bin="official-sources",
        run_command=fake_run,
        now=lambda: datetime(2026, 6, 4, 12, 31, tzinfo=UTC),
    )

    assert result.exit_code == 0
    assert "VERDICT: WARNING" in result.report_path.read_text(encoding="utf-8")
