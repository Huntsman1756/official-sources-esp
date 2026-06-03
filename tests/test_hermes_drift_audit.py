from __future__ import annotations

import subprocess
from datetime import date
from io import StringIO
from pathlib import Path

from official_sources.hermes_drift_audit import (
    AuditContract,
    AuditObservation,
    JournalEvidence,
    evaluate_hermes_drift,
    render_markdown_report,
)


def _contract(**overrides) -> AuditContract:
    values = {
        "expected_head_sha": "9df078b1ae599bdeca8c573bddbb53ea6c33a16a",
        "expected_project_state_min_date": date(2026, 6, 2),
        "require_clean_worktree": True,
        "expected_total_sources": 67,
        "expected_inventory_only": ("DOUE",),
        "forbid_unexpected_inventory_only": True,
        "stale_project_state_verdict": "no_go",
    }
    values.update(overrides)
    return AuditContract(**values)


def _sources(*inventory_only: str, total: int = 67) -> list[dict[str, str]]:
    sources: list[dict[str, str]] = []
    for source_code in inventory_only:
        sources.append({"source_code": source_code, "operational_status": "inventory_only"})
    for index in range(total - len(sources)):
        sources.append(
            {
                "source_code": f"TEST_SOURCE_{index}",
                "operational_status": "monitor_validated",
            }
        )
    return sources


def _observation(**overrides) -> AuditObservation:
    values = {
        "actual_head_sha": "9df078b1ae599bdeca8c573bddbb53ea6c33a16a",
        "git_worktree_clean": True,
        "project_state_date": date(2026, 6, 2),
        "sources": _sources("DOUE"),
        "journal_evidence": (
            JournalEvidence(unit="official-sources-hermes-auditor.service", readable=True),
        ),
    }
    values.update(overrides)
    return AuditObservation(**values)


def test_matching_release_state_and_source_contract_returns_go():
    result = evaluate_hermes_drift(_contract(), _observation())

    assert result.verdict == "GO"
    assert result.reasons == ()
    assert result.required_human_actions == ()


def test_head_mismatch_returns_no_go_with_actionable_reason():
    result = evaluate_hermes_drift(
        _contract(),
        _observation(actual_head_sha="a5c050b588fce8277247e9bcde3c446d852e784a"),
    )

    assert result.verdict == "NO-GO"
    assert "VPS HEAD is a5c050b588fce8277247e9bcde3c446d852e784a" in result.reasons[0]
    assert "fast-forward checkout" in " ".join(result.required_human_actions)


def test_dirty_worktree_returns_no_go():
    result = evaluate_hermes_drift(_contract(), _observation(git_worktree_clean=False))

    assert result.verdict == "NO-GO"
    assert "git worktree is dirty" in result.reasons


def test_stale_project_state_can_warn_when_contract_uses_warning_strictness():
    result = evaluate_hermes_drift(
        _contract(stale_project_state_verdict="warning"),
        _observation(project_state_date=date(2026, 5, 31)),
    )

    assert result.verdict == "WARNING"
    assert (
        "PROJECT_STATE date is 2026-05-31, expected >= 2026-06-02"
        in result.warnings
    )


def test_wrong_source_count_returns_no_go():
    result = evaluate_hermes_drift(_contract(), _observation(sources=_sources("DOUE", total=66)))

    assert result.verdict == "NO-GO"
    assert "source count is 66, expected 67" in result.reasons


def test_unexpected_inventory_only_source_returns_no_go():
    result = evaluate_hermes_drift(
        _contract(),
        _observation(sources=_sources("DOUE", "BOP_TEST", total=67)),
    )

    assert result.verdict == "NO-GO"
    assert "unexpected inventory_only sources: BOP_TEST" in result.reasons


def test_journal_unavailable_returns_warning_without_masking_go_state():
    result = evaluate_hermes_drift(
        _contract(),
        _observation(
            journal_evidence=(
                JournalEvidence(
                    unit="official-sources-boe-daily.service",
                    readable=False,
                    error="permission denied",
                ),
            )
        ),
    )

    assert result.verdict == "WARNING"
    assert (
        "journal evidence unavailable for official-sources-boe-daily.service: permission denied"
        in result.warnings
    )


def test_registry_parse_failure_never_returns_silent_go():
    result = evaluate_hermes_drift(
        _contract(),
        _observation(sources=(), registry_parse_error="sources must be a non-empty list"),
    )

    assert result.verdict == "WARNING"
    assert (
        "source registry could not be parsed: sources must be a non-empty list" in result.warnings
    )


def test_report_renders_final_verdict_failed_gates_and_required_actions():
    result = evaluate_hermes_drift(
        _contract(),
        _observation(actual_head_sha="a5c050b588fce8277247e9bcde3c446d852e784a"),
    )

    report = render_markdown_report(result)

    assert "VERDICT: NO-GO" in report
    assert "Failed gates:" in report
    assert "Required human action:" in report


def test_remote_head_mismatch_is_warning_only():
    result = evaluate_hermes_drift(
        _contract(),
        _observation(remote_head_observed_sha="a5c050b588fce8277247e9bcde3c446d852e784a"),
    )

    assert result.verdict == "WARNING"
    assert result.reasons == ()
    assert (
        "git ls-remote observed remote head differs from expected release SHA: "
        "a5c050b588fce8277247e9bcde3c446d852e784a"
    ) in result.warnings


def test_hermes_audit_cli_collects_local_read_only_state(tmp_path):
    from official_sources.cli import run

    repo_root = _write_minimal_git_repo(tmp_path)
    head_sha = _git(repo_root, "rev-parse", "HEAD")
    contract_path = repo_root / "config" / "hermes" / "audit_contract.yaml"
    contract_path.parent.mkdir(parents=True)
    contract_path.write_text(
        "\n".join(
            [
                "release:",
                f'  expected_head_sha: "{head_sha}"',
                '  expected_project_state_min_date: "2026-06-02"',
                "  require_clean_worktree: false",
                "sources:",
                "  expected_total: 1",
                "  expected_inventory_only:",
                "    - DOUE",
                "  forbid_unexpected_inventory_only: true",
                "journal:",
                "  units: []",
                "",
            ]
        ),
        encoding="utf-8",
    )

    stdout = StringIO()
    exit_code = run(
        [
            "hermes",
            "audit",
            "--contract",
            str(contract_path),
            "--repo-root",
            str(repo_root),
            "--registry",
            str(repo_root / "config" / "sources.yaml"),
            "--project-state",
            str(repo_root / "PROJECT_STATE.md"),
        ],
        stdout=stdout,
    )

    assert exit_code == 0
    assert "VERDICT: GO" in stdout.getvalue()


def _write_minimal_git_repo(tmp_path: Path) -> Path:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "config").mkdir()
    (repo_root / "PROJECT_STATE.md").write_text(
        "# Project State\n\nLast updated: 2026-06-02\n",
        encoding="utf-8",
    )
    (repo_root / "config" / "sources.yaml").write_text(
        """
sources:
  - source_code: DOUE
    name: Diario Oficial de la Union Europea
    jurisdiction: EU
    jurisdiction_level: european
    official_landing_url: https://eur-lex.europa.eu/oj/direct-access.html
    access_methods:
      - type: manual
        status: inventory
        notes: EU source kept as inventory-only.
    operational_status: inventory_only
    mcp_support: false
    monitor_support: none
    backfill_support: none
    evidence_adapter: false
    candidate_creation_allowed: false
    evidence_grade_allowed: false
    last_verified_at: "2026-06-02"
    limitations: []
    notes: Structural EU source outside Spanish territory coverage.
""".lstrip(),
        encoding="utf-8",
    )
    _git(repo_root, "init")
    _git(repo_root, "add", ".")
    _git(
        repo_root,
        "-c",
        "user.name=Test User",
        "-c",
        "user.email=test@example.invalid",
        "commit",
        "-m",
        "initial",
    )
    return repo_root


def _git(repo_root: Path, *args: str) -> str:
    completed = subprocess.run(
        ("git", *args),
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()
