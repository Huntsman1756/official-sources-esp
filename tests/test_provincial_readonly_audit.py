from __future__ import annotations

from official_sources.provincial_readonly_audit import (
    AuditHTTPResponse,
    audit_sources,
    classify_audit_response,
    list_auditable_provincial_sources,
    render_markdown_report,
)


def test_list_auditable_provincial_sources_excludes_monitored_and_documented_blocked():
    sources = list_auditable_provincial_sources()

    source_codes = {source["source_code"] for source in sources}
    assert len(sources) == 12
    assert "BOP_ALMERIA" not in source_codes
    assert {
        "BOP_A_CORUNA",
        "BOP_ALBACETE",
        "BOP_ALICANTE",
        "BOP_ARABA_ALAVA",
        "BOP_AVILA",
        "BOP_BARCELONA",
        "BOP_BIZKAIA",
        "BOP_BURGOS",
        "BOP_BADAJOZ",
        "BOP_CACERES",
        "BOP_CASTELLON",
        "BOP_CORDOBA",
        "BOP_GIPUZKOA",
        "BOP_GRANADA",
        "BOP_HUELVA",
        "BOP_JAEN",
        "BOP_LEON",
        "BOP_LLEIDA",
        "BOP_LUGO",
        "BOP_MALAGA",
        "BOP_PALENCIA",
        "BOP_PONTEVEDRA",
        "BOP_SEGOVIA",
        "BOP_SEVILLA",
        "BOP_SORIA",
        "BOP_TOLEDO",
        "BOP_VALENCIA",
        "BOP_VALLADOLID",
        "BOP_ZAMORA",
    }.isdisjoint(source_codes)
    assert all(source["jurisdiction_level"] == "provincial" for source in sources)
    assert all(source["operational_status"] == "inventory_only" for source in sources)


def test_classify_audit_response_detects_rss_or_api_candidate():
    response = AuditHTTPResponse(
        url="https://example.test/bop",
        final_url="https://example.test/bop",
        status_code=200,
        headers={"content-type": "text/html"},
        body=(
            b'<html><head><link rel="alternate" type="application/rss+xml" '
            b'href="/rss.xml"></head><body>Boletin provincial</body></html>'
        ),
        error=None,
    )

    result = classify_audit_response(_source("BOP_TEST"), response)

    assert result["detected_mechanism"] == "rss_or_api_detected"
    assert result["friction_level"] == "low"
    assert result["monitor_candidate"] is True
    assert result["discovered_urls"] == ["https://example.test/rss.xml"]


def test_classify_audit_response_detects_js_or_headless_required():
    response = AuditHTTPResponse(
        url="https://example.test/bop",
        final_url="https://example.test/bop",
        status_code=200,
        headers={"content-type": "text/html"},
        body=b"<html><body><script src='/zkau/web/js/zk.wpd'></script>publico.zul</body></html>",
        error=None,
    )

    result = classify_audit_response(_source("BOP_TEST"), response)

    assert result["detected_mechanism"] == "js_or_headless_required"
    assert result["friction_level"] == "high"
    assert result["monitor_candidate"] is False


def test_classify_audit_response_does_not_treat_generic_scripts_as_open_data():
    response = AuditHTTPResponse(
        url="https://example.test/bop",
        final_url="https://example.test/bop",
        status_code=200,
        headers={"content-type": "text/html"},
        body=(
            b"<html><script src='/analytics.js'></script>"
            b"<a href='/boletin-del-dia'>Boletin</a></html>"
        ),
        error=None,
    )

    result = classify_audit_response(_source("BOP_TEST"), response)

    assert result["detected_mechanism"] == "static_html_viable"
    assert result["friction_level"] == "low"
    assert result["monitor_candidate"] is True


def test_audit_sources_uses_one_read_only_fetch_per_source_and_renders_outputs():
    responses = {
        "https://barcelona.test": AuditHTTPResponse(
            url="https://barcelona.test",
            final_url="https://barcelona.test",
            status_code=200,
            headers={"content-type": "text/html"},
            body=b"<html><a href='/rss'>RSS</a><a href='/butlleti-del-dia'>Today</a></html>",
            error=None,
        ),
        "https://malaga.test": AuditHTTPResponse(
            url="https://malaga.test",
            final_url="https://malaga.test",
            status_code=200,
            headers={"content-type": "text/html"},
            body=b"<html><a href='/edicto/620-2026'>Ver edicto 620/2026</a></html>",
            error=None,
        ),
    }
    seen_urls: list[str] = []

    def fake_fetch(url: str, *, timeout_seconds: float, max_bytes: int) -> AuditHTTPResponse:
        assert timeout_seconds == 5.0
        assert max_bytes == 200_000
        seen_urls.append(url)
        return responses[url]

    payload = audit_sources(
        [
            _source("BOP_BARCELONA", url="https://barcelona.test"),
            _source("BOP_MALAGA", url="https://malaga.test"),
        ],
        fetcher=fake_fetch,
        generated_at="2026-05-27T00:00:00Z",
        timeout_seconds=5.0,
        max_bytes=200_000,
    )
    report = render_markdown_report(payload)

    assert seen_urls == ["https://barcelona.test", "https://malaga.test"]
    assert payload["count"] == 2
    assert payload["category_counts"] == {
        "rss_or_api_detected": 1,
        "static_html_viable": 1,
    }
    assert [item["source_id"] for item in payload["recommended_candidates"]] == [
        "BOP_BARCELONA",
        "BOP_MALAGA",
    ]
    assert "## Category Counts" in report
    assert "BOP_BARCELONA" in report


def test_recommended_candidates_prioritize_documented_waves_with_positive_evidence():
    responses = {
        "https://avila.test": AuditHTTPResponse(
            url="https://avila.test",
            final_url="https://avila.test",
            status_code=200,
            headers={"content-type": "text/html"},
            body=b"<html><a href='/rss'>RSS</a></html>",
            error=None,
        ),
        "https://barcelona.test": AuditHTTPResponse(
            url="https://barcelona.test",
            final_url="https://barcelona.test",
            status_code=200,
            headers={"content-type": "text/html"},
            body=b"<html><a href='/butlleti-del-dia'>Butlleti del dia</a></html>",
            error=None,
        ),
    }

    payload = audit_sources(
        [
            _source("BOP_AVILA", url="https://avila.test"),
            _source("BOP_BARCELONA", url="https://barcelona.test"),
        ],
        fetcher=lambda url, **_kwargs: responses[url],
        generated_at="2026-05-27T00:00:00Z",
    )

    assert [item["source_id"] for item in payload["recommended_candidates"]] == [
        "BOP_BARCELONA",
        "BOP_AVILA",
    ]


def _source(source_code: str, *, url: str = "https://example.test/bop") -> dict:
    return {
        "source_code": source_code,
        "name": f"{source_code} name",
        "jurisdiction": "ES-XX",
        "jurisdiction_level": "provincial",
        "official_landing_url": url,
        "access_methods": [
            {
                "type": "html",
                "url": url,
                "status": "inventory",
                "notes": "Official directory landing URL; not validated for monitoring.",
            }
        ],
        "operational_status": "inventory_only",
        "mcp_support": False,
        "monitor_support": "none",
        "backfill_support": "none",
        "evidence_adapter": False,
        "candidate_creation_allowed": False,
        "evidence_grade_allowed": False,
        "last_verified_at": "2026-05-27",
        "limitations": ["Provincial bulletin inventory only."],
        "notes": "Test source.",
    }
