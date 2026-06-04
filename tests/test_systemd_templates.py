from __future__ import annotations

from pathlib import Path

SYSTEMD_DIR = Path(__file__).parents[1] / "deploy" / "systemd"


def test_systemd_files_exist():
    expected = {
        "official-sources-boe-daily.service",
        "official-sources-boe-daily.timer",
        "official-sources-hermes-auditor.service",
        "official-sources-hermes-auditor.timer",
        "official-sources-integrity-check.service",
        "official-sources-integrity-check.timer",
        "run-official-sources-hermes-auditor.sh",
    }

    assert {path.name for path in SYSTEMD_DIR.iterdir()} == expected


def test_systemd_files_do_not_contain_secrets_or_public_network_services():
    combined = "\n".join(path.read_text(encoding="utf-8") for path in SYSTEMD_DIR.iterdir())

    assert "SECRET" not in combined.upper()
    assert "PASSWORD" not in combined.upper()
    assert "API_KEY" not in combined.upper()
    assert "ListenStream" not in combined
    assert "nginx" not in combined.lower()
    assert "tailscale" not in combined.lower()


def test_systemd_daily_template_runs_cli_operations():
    content = (SYSTEMD_DIR / "official-sources-boe-daily.service").read_text(encoding="utf-8")

    assert "official-sources ingest-boe-summary --date today" in content
    assert "official-sources download-boe-artifacts --date today --types xml,html" in content
    assert "--date today --types xml,html,pdf" not in content
    assert "official-sources status --date today" in content


def test_systemd_services_use_private_vps_layout_and_dedicated_user():
    for service_name in [
        "official-sources-boe-daily.service",
        "official-sources-hermes-auditor.service",
        "official-sources-integrity-check.service",
    ]:
        content = (SYSTEMD_DIR / service_name).read_text(encoding="utf-8")

        assert "User=official-sources" in content
        assert "Group=official-sources" in content
        assert "WorkingDirectory=/opt/official-sources/app" in content
        assert "EnvironmentFile=/opt/official-sources/.env" in content
        assert "/opt/official-sources/app/.venv/bin/official-sources" in content


def test_hermes_systemd_template_runs_scheduled_strict_audit_wrapper():
    service = (SYSTEMD_DIR / "official-sources-hermes-auditor.service").read_text(
        encoding="utf-8"
    )
    timer = (SYSTEMD_DIR / "official-sources-hermes-auditor.timer").read_text(encoding="utf-8")
    wrapper = (SYSTEMD_DIR / "run-official-sources-hermes-auditor.sh").read_text(
        encoding="utf-8"
    )

    assert "SupplementaryGroups=systemd-journal" in service
    assert (
        "ExecStart=/opt/hermes-official-sources-auditor/bin/"
        "run-official-sources-hermes-auditor.sh"
    ) in service
    assert "OnCalendar=*-*-* 00:15:00 UTC" in timer
    assert "hermes scheduled-audit" in wrapper
    assert "--release-contract \"${RELEASE_CONTRACT}\"" in wrapper
    assert "--official-sources-bin \"${OFFICIAL_SOURCES_BIN}\"" in wrapper
