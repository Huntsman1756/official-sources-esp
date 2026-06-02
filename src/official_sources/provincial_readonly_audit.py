from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import httpx

from official_sources.source_registry import list_sources

AUDIT_CATEGORIES = (
    "rss_or_api_detected",
    "open_data_detected",
    "static_html_viable",
    "stable_form_or_endpoint",
    "pdf_first",
    "js_or_headless_required",
    "blocked_or_high_friction",
    "unknown",
)
RECOMMENDATION_PRIORITY = (
    "BOP_BARCELONA",
    "BOP_MALAGA",
    "BOP_BIZKAIA",
    "BOP_VALENCIA",
    "BOP_SEVILLA",
    "BOP_ZARAGOZA",
)
MONITOR_CANDIDATE_CATEGORIES = {
    "rss_or_api_detected",
    "open_data_detected",
    "static_html_viable",
    "stable_form_or_endpoint",
}
DOCUMENTED_BLOCKER_MARKERS = (
    "zk/javascript",
    "javascript application",
    "js-capable",
    "headless",
    "blocked by",
    "blocking reason",
    "defer until",
    "deferred until",
    "relay egress",
    "manual-only",
)
JS_HEADLESS_MARKERS = (
    "zkau",
    ".zul",
    "enable javascript",
    "habilite javascript",
    "requires javascript",
    "angular",
    "reactroot",
    "app-root",
)
OPEN_DATA_MARKERS = (
    "datos abiertos",
    "dades obertes",
    "open data",
    "opendata",
)
FORM_MARKERS = (
    "<form",
    "buscador",
    "buscar",
    "consulta",
    "fecha",
    "cve",
    "registro",
)
STATIC_HTML_MARKERS = (
    "boletin",
    "butlleti",
    "boletim",
    "bop",
    "sumario",
    "anuncio",
    "edicto",
)
PDF_MARKERS = (".pdf", "pdf", "bop completo", "boletin completo")
LINK_RE = re.compile(
    r"""(?ix)
    (?:href|src)\s*=\s*
    (?:
        "([^"]+)"
        |
        '([^']+)'
    )
    """
)


@dataclass(frozen=True)
class AuditHTTPResponse:
    url: str
    final_url: str
    status_code: int | None
    headers: dict[str, str]
    body: bytes
    error: str | None


def list_auditable_provincial_sources() -> list[dict[str, Any]]:
    return [
        source
        for source in list_sources()
        if _is_auditable_provincial_source(source)
        and not _has_documented_blocker(source)
    ]


def audit_sources(
    sources: list[dict[str, Any]],
    *,
    fetcher=None,
    generated_at: str | None = None,
    timeout_seconds: float = 5.0,
    max_bytes: int = 200_000,
) -> dict[str, Any]:
    records = [
        classify_audit_response(
            source,
            (fetcher or fetch_homepage)(
                source["official_landing_url"],
                timeout_seconds=timeout_seconds,
                max_bytes=max_bytes,
            ),
        )
        for source in sources
    ]
    category_counts = Counter(record["detected_mechanism"] for record in records)
    normalized_counts = {
        category: category_counts[category]
        for category in AUDIT_CATEGORIES
        if category_counts[category]
    }
    recommended_candidates = _recommended_candidates(records)
    return {
        "task": "TASK-PROVINCIAL-READONLY-BATCH-AUDIT-001",
        "generated_at": generated_at or datetime.now(UTC).replace(microsecond=0).isoformat(),
        "scope": {
            "source_count": len(sources),
            "read_only": True,
            "max_requests_per_source": 1,
            "timeout_seconds": timeout_seconds,
            "max_bytes_per_source": max_bytes,
            "headless_browser": False,
            "login": False,
            "anti_bot_bypass": False,
            "registry_writes": False,
            "monitor_additions": False,
        },
        "count": len(records),
        "category_counts": normalized_counts,
        "recommended_candidates": recommended_candidates,
        "records": records,
    }


def classify_audit_response(
    source: dict[str, Any],
    response: AuditHTTPResponse,
) -> dict[str, Any]:
    body_text = response.body.decode("utf-8", errors="replace")
    lower = body_text.lower()
    final_url = response.final_url or response.url
    discovered_urls = _discovered_urls(final_url, body_text)
    status_code = response.status_code

    if response.error:
        category = "unknown"
        friction = "unknown"
        evidence = f"Fetch failed: {response.error}"
    elif status_code in {401, 403, 429}:
        category = "blocked_or_high_friction"
        friction = "blocked"
        evidence = f"HTTP {status_code} from landing page."
    elif status_code is not None and status_code >= 400:
        category = "unknown"
        friction = "high"
        evidence = f"HTTP {status_code} from landing page."
    elif _has_any(lower, JS_HEADLESS_MARKERS):
        category = "js_or_headless_required"
        friction = "high"
        evidence = "Landing page includes JavaScript/headless markers."
    elif _has_rss_or_api_signal(lower, discovered_urls):
        category = "rss_or_api_detected"
        friction = "low"
        evidence = "Landing page exposes RSS/Atom/API-like links or metadata."
    elif _has_open_data_signal(lower, discovered_urls):
        category = "open_data_detected"
        friction = "low"
        evidence = "Landing page exposes open-data/API vocabulary."
    elif _has_any(lower, FORM_MARKERS) or _has_endpoint_url(discovered_urls):
        category = "stable_form_or_endpoint"
        friction = "medium"
        evidence = "Landing page exposes form/search/endpoint signals."
    elif _has_any(lower, STATIC_HTML_MARKERS) and discovered_urls:
        category = "static_html_viable"
        friction = "low"
        evidence = "Landing page returns static HTML with bulletin-like links."
    elif _looks_pdf_first(lower, discovered_urls):
        category = "pdf_first"
        friction = "medium"
        evidence = "Landing page appears PDF-first."
    else:
        category = "unknown"
        friction = "unknown"
        evidence = "No low-risk metadata access mechanism detected from one landing-page request."

    monitor_candidate = category in MONITOR_CANDIDATE_CATEGORIES and friction in {"low", "medium"}
    return {
        "source_id": source["source_code"],
        "province": _province_name(source),
        "current_status": source["operational_status"],
        "homepage_url": source["official_landing_url"],
        "final_url": final_url,
        "http_status": status_code,
        "discovered_urls": discovered_urls[:10],
        "detected_mechanism": category,
        "evidence": evidence,
        "friction_level": friction,
        "recommended_next_action": _recommended_next_action(category),
        "monitor_candidate": monitor_candidate,
        "notes": _notes_for_source(source, response),
    }


def render_markdown_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Provincial Read-Only Batch Audit",
        "",
        f"Date: {payload['generated_at'][:10]}",
        "",
        f"Task: `{payload['task']}`",
        "",
        "## Scope",
        "",
        "- read-only landing-page audit;",
        "- one request per source;",
        "- no login, headless browser, anti-bot bypass, monitor additions, or registry writes;",
        "- outputs are planning evidence, not monitor validation.",
        "",
        "## Category Counts",
        "",
        "| Category | Count |",
        "| --- | ---: |",
    ]
    for category, count in payload["category_counts"].items():
        lines.append(f"| `{category}` | {count} |")

    lines.extend(
        [
            "",
            "## Recommended Candidates",
            "",
            "| Source | Category | Friction | Evidence |",
            "| --- | --- | --- | --- |",
        ]
    )
    for record in payload["recommended_candidates"]:
        lines.append(
            "| "
            f"`{record['source_id']}` | `{record['detected_mechanism']}` | "
            f"`{record['friction_level']}` | {record['evidence']} |"
        )

    lines.extend(
        [
            "",
            "## Defer Or Manual",
            "",
            "| Source | Category | Friction | Action |",
            "| --- | --- | --- | --- |",
        ]
    )
    for record in payload["records"]:
        if record["monitor_candidate"]:
            continue
        lines.append(
            "| "
            f"`{record['source_id']}` | `{record['detected_mechanism']}` | "
            f"`{record['friction_level']}` | {record['recommended_next_action']} |"
        )

    lines.extend(
        [
            "",
            "## Per-Source Results",
            "",
            "| Source | Province | Category | Friction | Candidate | URL |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for record in payload["records"]:
        candidate = "yes" if record["monitor_candidate"] else "no"
        lines.append(
            "| "
            f"`{record['source_id']}` | {record['province']} | "
            f"`{record['detected_mechanism']}` | `{record['friction_level']}` | "
            f"{candidate} | {record['homepage_url']} |"
        )

    lines.extend(
        [
            "",
            "## Validation Notes",
            "",
            "This audit classifies first-pass access-path evidence only. A recommended "
            "candidate still "
            "requires a separate metadata-only monitor PR with fixtures and preview validation.",
            "",
        ]
    )
    return "\n".join(lines)


def fetch_homepage(
    url: str,
    *,
    timeout_seconds: float = 5.0,
    max_bytes: int = 200_000,
) -> AuditHTTPResponse:
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "User-Agent": "official-sources-readonly-audit/0.1",
    }
    try:
        with httpx.Client(follow_redirects=True, timeout=timeout_seconds) as client:
            response = client.get(url, headers=headers)
            return AuditHTTPResponse(
                url=url,
                final_url=str(response.url),
                status_code=response.status_code,
                headers={key.lower(): value for key, value in response.headers.items()},
                body=response.content[:max_bytes],
                error=None,
            )
    except httpx.HTTPError as exc:
        return AuditHTTPResponse(
            url=url,
            final_url=url,
            status_code=None,
            headers={},
            body=b"",
            error=f"{type(exc).__name__}: {exc}",
        )


def write_outputs(payload: dict[str, Any], *, json_path: Path, report_path: Path) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    report_path.write_text(render_markdown_report(payload), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="provincial-readonly-audit")
    parser.add_argument(
        "--json-output",
        default="data/provincial_audit/provincial-readonly-batch-audit-2026-05-27.json",
    )
    parser.add_argument(
        "--report-output",
        default="docs/reports/provincial-readonly-batch-audit-2026-05-27.md",
    )
    parser.add_argument("--timeout-seconds", type=float, default=5.0)
    parser.add_argument("--max-bytes", type=int, default=200_000)
    args = parser.parse_args(argv)

    payload = audit_sources(
        list_auditable_provincial_sources(),
        timeout_seconds=args.timeout_seconds,
        max_bytes=args.max_bytes,
    )
    write_outputs(
        payload,
        json_path=Path(args.json_output),
        report_path=Path(args.report_output),
    )
    print(f"sources={payload['count']}")
    print(f"json={args.json_output}")
    print(f"report={args.report_output}")
    return 0


def _is_auditable_provincial_source(source: dict[str, Any]) -> bool:
    return (
        source["jurisdiction_level"] == "provincial"
        and source["operational_status"] == "inventory_only"
        and source["monitor_support"] == "none"
        and bool(str(source.get("official_landing_url", "")).strip())
    )


def _has_documented_blocker(source: dict[str, Any]) -> bool:
    evidence_text = " ".join(
        [
            str(source.get("notes", "")),
            *[str(limitation) for limitation in source.get("limitations", [])],
            *[str(method.get("notes", "")) for method in source.get("access_methods", [])],
        ]
    ).lower()
    return any(marker in evidence_text for marker in DOCUMENTED_BLOCKER_MARKERS)


def _discovered_urls(base_url: str, body_text: str) -> list[str]:
    urls = []
    seen = set()
    for match in LINK_RE.finditer(body_text):
        raw_url = (match.group(1) or match.group(2) or "").strip()
        if not raw_url or raw_url.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue
        url = urljoin(base_url, raw_url)
        if url in seen:
            continue
        seen.add(url)
        urls.append(url)
    return urls


def _recommended_candidates(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    priority = {source_code: index for index, source_code in enumerate(RECOMMENDATION_PRIORITY)}
    candidates = [record for record in records if record["monitor_candidate"]]
    return sorted(
        candidates,
        key=lambda record: (
            priority.get(record["source_id"], len(priority)),
            _category_rank(record["detected_mechanism"]),
            record["source_id"],
        ),
    )[:5]


def _category_rank(category: str) -> int:
    order = {
        "rss_or_api_detected": 0,
        "open_data_detected": 1,
        "static_html_viable": 2,
        "stable_form_or_endpoint": 3,
    }
    return order.get(category, 99)


def _recommended_next_action(category: str) -> str:
    if category in {"rss_or_api_detected", "open_data_detected"}:
        return "Review discovered feed/API/open-data path before a metadata-only monitor PR."
    if category == "static_html_viable":
        return "Take a one-source fixture and design a metadata-only HTML monitor pilot."
    if category == "stable_form_or_endpoint":
        return "Audit form or endpoint parameters before any monitor implementation."
    if category == "pdf_first":
        return "Defer monitor work until metadata can be captured without PDF download."
    if category == "js_or_headless_required":
        return "Defer to separate JS/headless or endpoint-specific audit."
    if category == "blocked_or_high_friction":
        return "Defer/manual; do not bypass access friction."
    return "Keep unknown/manual until a narrower source-specific check is approved."


def _notes_for_source(source: dict[str, Any], response: AuditHTTPResponse) -> str:
    source_notes = str(source.get("notes", "")).strip()
    if response.error:
        return f"{source_notes} Fetch error recorded; no retry attempted.".strip()
    return source_notes or "First-pass read-only landing-page audit."


def _province_name(source: dict[str, Any]) -> str:
    name = source["name"]
    prefix = "Boletin Oficial de "
    if name.startswith(prefix):
        return name[len(prefix) :]
    return name


def _has_any(text: str, markers: tuple[str, ...]) -> bool:
    return any(marker in text for marker in markers)


def _has_rss_or_api_signal(text: str, urls: list[str]) -> bool:
    return (
        "application/rss+xml" in text
        or "application/atom+xml" in text
        or any(_looks_like_feed_or_api_url(url) for url in urls)
    )


def _has_open_data_signal(text: str, urls: list[str]) -> bool:
    return _has_any(text, OPEN_DATA_MARKERS) or any(
        marker in url.lower() for url in urls for marker in ("/api/", ".json", ".csv")
    )


def _looks_like_feed_or_api_url(url: str) -> bool:
    lower = url.lower()
    return any(marker in lower for marker in ("/rss", "rss.", ".rss", "/feed", "atom", "/api/"))


def _looks_pdf_first(text: str, urls: list[str]) -> bool:
    pdf_url_count = sum(1 for url in urls if ".pdf" in url.lower())
    html_url_count = sum(1 for url in urls if ".html" in url.lower() or ".htm" in url.lower())
    return _has_any(text, PDF_MARKERS) and pdf_url_count >= max(1, html_url_count)


def _has_endpoint_url(urls: list[str]) -> bool:
    return any(
        marker in url.lower()
        for url in urls
        for marker in (".do", ".dll", "servlet", "consulta", "buscar", "buscador")
    )


if __name__ == "__main__":
    raise SystemExit(main())
