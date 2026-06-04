from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field, replace
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from official_sources.source_registry import SourceRegistryError, list_sources

VERDICTS = {"GO", "WARNING", "NO-GO"}
STALE_PROJECT_STATE_VERDICTS = {"warning", "no_go"}
PROJECT_STATE_DATE_RE = re.compile(r"^Last updated:\s*(\d{4}-\d{2}-\d{2})\s*$", re.MULTILINE)


class HermesDriftAuditError(ValueError):
    pass


@dataclass(frozen=True)
class AuditContract:
    expected_project_state_min_date: date
    require_clean_worktree: bool
    expected_total_sources: int
    expected_inventory_only: tuple[str, ...]
    expected_head_sha: str | None = None
    expected_head_sha_source: str | None = None
    require_external_release_contract: bool = False
    forbid_unexpected_inventory_only: bool = True
    stale_project_state_verdict: str = "no_go"
    require_registry_parse: bool = False
    check_remote_head: bool = False
    remote_name: str = "origin"
    remote_ref: str = "refs/heads/main"
    journal_units: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.stale_project_state_verdict not in STALE_PROJECT_STATE_VERDICTS:
            raise HermesDriftAuditError(
                "stale_project_state_verdict must be one of: no_go, warning"
            )
        if self.expected_total_sources < 0:
            raise HermesDriftAuditError("expected_total_sources must be non-negative")
        if self.expected_head_sha is not None and not self.expected_head_sha.strip():
            raise HermesDriftAuditError("expected_head_sha must be non-empty when provided")


@dataclass(frozen=True)
class ReleaseContract:
    expected_head_sha: str
    expected_branch: str | None = None
    approved_at: str | None = None
    approved_reason: str | None = None


@dataclass(frozen=True)
class JournalEvidence:
    unit: str
    readable: bool
    error: str | None = None


@dataclass(frozen=True)
class AuditObservation:
    actual_head_sha: str | None
    git_worktree_clean: bool | None
    project_state_date: date | None
    sources: tuple[dict[str, Any], ...] | list[dict[str, Any]] = ()
    registry_parse_error: str | None = None
    journal_evidence: tuple[JournalEvidence, ...] = ()
    remote_head_observed_sha: str | None = None
    remote_observation_error: str | None = None
    collection_warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "sources", tuple(self.sources))


@dataclass(frozen=True)
class AuditResult:
    verdict: str
    reasons: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    required_human_actions: tuple[str, ...] = ()
    observed: dict[str, Any] = field(default_factory=dict)


def default_audit_contract_path() -> Path:
    return Path(__file__).resolve().parents[2] / "config" / "hermes" / "audit_contract.yaml"


def load_audit_contract(path: Path | None = None) -> AuditContract:
    contract_path = path or default_audit_contract_path()
    with contract_path.open(encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)
    if not isinstance(raw, dict):
        raise HermesDriftAuditError("audit contract must be a mapping")

    release = _required_mapping(raw, "release")
    sources = _required_mapping(raw, "sources")
    journal = raw.get("journal", {})
    if journal is None:
        journal = {}
    if not isinstance(journal, dict):
        raise HermesDriftAuditError("journal must be a mapping")

    expected_inventory_only = sources.get("expected_inventory_only", ())
    if not isinstance(expected_inventory_only, list):
        raise HermesDriftAuditError("sources.expected_inventory_only must be a list")
    journal_units = journal.get("units", ())
    if not isinstance(journal_units, (list, tuple)):
        raise HermesDriftAuditError("journal.units must be a list")

    return AuditContract(
        expected_project_state_min_date=_parse_date_value(
            _required_value(release, "expected_project_state_min_date"),
            "release.expected_project_state_min_date",
        ),
        require_clean_worktree=bool(release.get("require_clean_worktree", True)),
        expected_total_sources=int(_required_value(sources, "expected_total")),
        expected_inventory_only=tuple(
            str(value).strip().upper() for value in expected_inventory_only
        ),
        forbid_unexpected_inventory_only=bool(
            sources.get("forbid_unexpected_inventory_only", True)
        ),
        stale_project_state_verdict=str(release.get("stale_project_state_verdict", "no_go")),
        require_registry_parse=bool(sources.get("require_registry_parse", False)),
        check_remote_head=bool(release.get("check_remote_head", False)),
        remote_name=str(release.get("remote_name", "origin")),
        remote_ref=str(release.get("remote_ref", "refs/heads/main")),
        journal_units=tuple(str(unit) for unit in journal_units),
    )


def default_release_contract_path() -> Path:
    return Path("/etc/official-sources/hermes-audit-contract.yaml")


def load_release_contract(path: Path) -> ReleaseContract:
    with path.open(encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)
    if not isinstance(raw, dict):
        raise HermesDriftAuditError("release contract must be a mapping")
    release = _required_mapping(raw, "release")
    expected_head_sha = str(_required_value(release, "expected_head_sha")).strip()
    if not expected_head_sha:
        raise HermesDriftAuditError("release.expected_head_sha is required")
    return ReleaseContract(
        expected_head_sha=expected_head_sha,
        expected_branch=_optional_string(release.get("expected_branch")),
        approved_at=_optional_string(release.get("approved_at")),
        approved_reason=_optional_string(release.get("approved_reason")),
    )


def merge_release_contract(
    audit_contract: AuditContract,
    release_contract: ReleaseContract,
    release_contract_path: Path,
) -> AuditContract:
    return replace(
        audit_contract,
        expected_head_sha=release_contract.expected_head_sha,
        expected_head_sha_source=str(release_contract_path),
    )


def require_external_release_contract(audit_contract: AuditContract) -> AuditContract:
    return replace(audit_contract, require_external_release_contract=True)


def collect_local_observation(
    *,
    repo_root: Path,
    registry_path: Path | None,
    project_state_path: Path | None,
    contract: AuditContract,
) -> AuditObservation:
    resolved_repo = repo_root.resolve()
    actual_head_sha, head_error = _git_output(resolved_repo, "rev-parse", "HEAD")
    worktree_output, worktree_error = _git_output(resolved_repo, "status", "--porcelain")
    git_worktree_clean: bool | None = None
    if worktree_error is None:
        git_worktree_clean = not bool(worktree_output.strip())

    remote_head_observed_sha: str | None = None
    remote_observation_error: str | None = None
    if contract.check_remote_head:
        remote_output, remote_error = _git_output(
            resolved_repo,
            "ls-remote",
            contract.remote_name,
            contract.remote_ref,
        )
        if remote_error is None and remote_output.strip():
            remote_head_observed_sha = remote_output.split()[0]
        else:
            remote_observation_error = remote_error or "git ls-remote returned no rows"

    state_path = project_state_path or resolved_repo / "PROJECT_STATE.md"
    project_state_date, project_state_error = _read_project_state_date(state_path)

    registry_parse_error: str | None = None
    sources: tuple[dict[str, Any], ...] = ()
    try:
        sources = tuple(list_sources(registry_path or resolved_repo / "config" / "sources.yaml"))
    except (OSError, SourceRegistryError, yaml.YAMLError) as exc:
        registry_parse_error = str(exc)

    journal_evidence = tuple(_collect_journal_evidence(unit) for unit in contract.journal_units)
    warnings = tuple(
        warning
        for warning in (
            f"git rev-parse HEAD failed: {head_error}" if head_error else None,
            f"git status --porcelain failed: {worktree_error}" if worktree_error else None,
            f"PROJECT_STATE date could not be read: {project_state_error}"
            if project_state_error
            else None,
        )
        if warning
    )

    return AuditObservation(
        actual_head_sha=actual_head_sha if head_error is None else None,
        git_worktree_clean=git_worktree_clean,
        project_state_date=project_state_date,
        sources=sources,
        registry_parse_error=registry_parse_error,
        journal_evidence=journal_evidence,
        remote_head_observed_sha=remote_head_observed_sha,
        remote_observation_error=remote_observation_error,
        collection_warnings=warnings,
    )


def evaluate_hermes_drift(contract: AuditContract, observation: AuditObservation) -> AuditResult:
    reasons: list[str] = []
    warnings: list[str] = list(observation.collection_warnings)

    _evaluate_release_state(contract, observation, reasons, warnings)
    _evaluate_source_contract(contract, observation, reasons, warnings)
    _evaluate_journal_evidence(observation, warnings)

    if reasons:
        verdict = "NO-GO"
    elif warnings:
        verdict = "WARNING"
    else:
        verdict = "GO"

    return AuditResult(
        verdict=verdict,
        reasons=tuple(reasons),
        warnings=tuple(warnings),
        required_human_actions=tuple(_required_actions(reasons, warnings)),
        observed={
            "expected_head_sha": contract.expected_head_sha,
            "expected_head_sha_source": contract.expected_head_sha_source,
            "actual_head_sha": observation.actual_head_sha,
            "remote_head_observed_sha": observation.remote_head_observed_sha,
            "git_worktree_clean": observation.git_worktree_clean,
            "project_state_date": (
                observation.project_state_date.isoformat()
                if observation.project_state_date
                else None
            ),
            "source_count": len(observation.sources),
            "inventory_only_sources": _inventory_only_sources(observation.sources),
        },
    )


def render_markdown_report(result: AuditResult) -> str:
    lines = [
        "# Hermes Drift Audit",
        "",
        f"VERDICT: {result.verdict}",
        "",
        "Observed:",
    ]
    for key, value in result.observed.items():
        lines.append(f"- {key}: {value}")

    lines.extend(["", "Failed gates:"])
    if result.reasons:
        lines.extend(f"- {reason}" for reason in result.reasons)
    else:
        lines.append("- none")

    lines.extend(["", "Warnings:"])
    if result.warnings:
        lines.extend(f"- {warning}" for warning in result.warnings)
    else:
        lines.append("- none")

    lines.extend(["", "Required human action:"])
    if result.required_human_actions:
        lines.extend(f"- {action}" for action in result.required_human_actions)
    else:
        lines.append("- none")

    return "\n".join(lines) + "\n"


def _evaluate_release_state(
    contract: AuditContract,
    observation: AuditObservation,
    reasons: list[str],
    warnings: list[str],
) -> None:
    if contract.expected_head_sha is None:
        if contract.require_external_release_contract:
            reasons.append("external release contract is required but unavailable")
        else:
            warnings.append("external release contract unavailable; HEAD gate not enforced")
    elif observation.actual_head_sha is None:
        reasons.append("observed checkout HEAD could not be observed")
    elif observation.actual_head_sha != contract.expected_head_sha:
        reasons.append(
            "observed checkout HEAD is "
            f"{observation.actual_head_sha}, expected {contract.expected_head_sha}"
        )

    if contract.require_clean_worktree:
        if observation.git_worktree_clean is False:
            reasons.append("git worktree is dirty")
        elif observation.git_worktree_clean is None:
            warnings.append("git worktree cleanliness could not be observed")

    if observation.project_state_date is None:
        warnings.append("PROJECT_STATE date could not be observed")
    elif observation.project_state_date < contract.expected_project_state_min_date:
        message = (
            f"PROJECT_STATE date is {observation.project_state_date.isoformat()}, expected >= "
            f"{contract.expected_project_state_min_date.isoformat()}"
        )
        if contract.stale_project_state_verdict == "no_go":
            reasons.append(message)
        else:
            warnings.append(message)

    if observation.remote_observation_error:
        warnings.append(
            f"remote head could not be observed: {observation.remote_observation_error}"
        )
    elif (
        observation.remote_head_observed_sha is not None
        and contract.expected_head_sha is not None
        and observation.remote_head_observed_sha != contract.expected_head_sha
    ):
        warnings.append(
            "git ls-remote observed remote head differs from expected release SHA: "
            f"{observation.remote_head_observed_sha}"
        )


def _evaluate_source_contract(
    contract: AuditContract,
    observation: AuditObservation,
    reasons: list[str],
    warnings: list[str],
) -> None:
    if observation.registry_parse_error:
        message = f"source registry could not be parsed: {observation.registry_parse_error}"
        if contract.require_registry_parse:
            reasons.append(message)
        else:
            warnings.append(message)
        return

    source_count = len(observation.sources)
    if source_count != contract.expected_total_sources:
        reasons.append(
            f"source count is {source_count}, expected {contract.expected_total_sources}"
        )

    inventory_only = set(_inventory_only_sources(observation.sources))
    expected_inventory_only = set(contract.expected_inventory_only)
    unexpected_inventory_only = sorted(inventory_only - expected_inventory_only)
    missing_inventory_only = sorted(expected_inventory_only - inventory_only)

    if contract.forbid_unexpected_inventory_only and unexpected_inventory_only:
        reasons.append(
            "unexpected inventory_only sources: " + ", ".join(unexpected_inventory_only)
        )
    if missing_inventory_only:
        reasons.append(
            "expected inventory_only sources missing: " + ", ".join(missing_inventory_only)
        )


def _evaluate_journal_evidence(observation: AuditObservation, warnings: list[str]) -> None:
    for evidence in observation.journal_evidence:
        if evidence.readable:
            continue
        suffix = f": {evidence.error}" if evidence.error else ""
        warnings.append(f"journal evidence unavailable for {evidence.unit}{suffix}")


def _required_actions(reasons: list[str], warnings: list[str]) -> list[str]:
    actions: list[str] = []
    combined = "\n".join([*reasons, *warnings])
    if "observed checkout HEAD is" in combined or "observed checkout HEAD could not" in combined:
        actions.append("inspect VPS checkout and decide whether to fast-forward checkout")
    if "external release contract" in combined:
        actions.append("provide the external Hermes release contract or disable strict mode")
    if "git worktree is dirty" in combined:
        actions.append("inspect dirty diff on VPS before any release claim")
    if "PROJECT_STATE date" in combined:
        actions.append("refresh PROJECT_STATE.md or lower the expected date only with evidence")
    if "source count" in combined or "inventory_only" in combined or "source registry" in combined:
        actions.append("compare config/sources.yaml against the declared source contract")
    if "journal evidence unavailable" in combined:
        actions.append("grant narrow journal read access or keep the explicit WARNING")
    return _dedupe(actions)


def _inventory_only_sources(
    sources: tuple[dict[str, Any], ...] | list[dict[str, Any]],
) -> list[str]:
    return sorted(
        str(source.get("source_code"))
        for source in sources
        if source.get("operational_status") == "inventory_only"
    )


def _required_mapping(raw: dict[str, Any], key: str) -> dict[str, Any]:
    value = raw.get(key)
    if not isinstance(value, dict):
        raise HermesDriftAuditError(f"{key} must be a mapping")
    return value


def _required_value(raw: dict[str, Any], key: str) -> Any:
    if key not in raw:
        raise HermesDriftAuditError(f"{key} is required")
    return raw[key]


def _optional_string(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _parse_date_value(value: Any, label: str) -> date:
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except ValueError as exc:
        raise HermesDriftAuditError(f"{label} must be YYYY-MM-DD") from exc


def _read_project_state_date(path: Path) -> tuple[date | None, str | None]:
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        return None, str(exc)
    match = PROJECT_STATE_DATE_RE.search(content)
    if not match:
        return None, "Last updated line not found"
    return date.fromisoformat(match.group(1)), None


def _git_output(repo_root: Path, *args: str) -> tuple[str | None, str | None]:
    return _run_readonly_command(("git", *args), cwd=repo_root)


def _collect_journal_evidence(unit: str) -> JournalEvidence:
    _, error = _run_readonly_command(
        ("journalctl", "-u", unit, "-n", "1", "--no-pager"),
        cwd=None,
    )
    if error is None:
        return JournalEvidence(unit=unit, readable=True)
    return JournalEvidence(unit=unit, readable=False, error=error)


def _run_readonly_command(
    command: tuple[str, ...],
    *,
    cwd: Path | None,
    timeout_seconds: int = 8,
) -> tuple[str | None, str | None]:
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return None, str(exc)
    if completed.returncode != 0:
        error = (completed.stderr or completed.stdout or "").strip()
        return None, error or f"{command[0]} exited {completed.returncode}"
    return completed.stdout.strip(), None


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
