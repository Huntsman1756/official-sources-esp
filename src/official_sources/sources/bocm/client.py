from __future__ import annotations

import re
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from urllib.parse import urlencode

import httpx

from official_sources.sources.boe.http_policy import BOERequestAudit, BOERequestPolicy

BOCM_BASE_URL = "https://www.bocm.es"
BOCM_SEARCH_DAY_PATH = "/search-day-month"


def validate_bocm_date(value: str) -> date:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError(f"Invalid BOCM date: {value}. Expected YYYY-MM-DD.")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"Invalid BOCM date: {value}. Expected YYYY-MM-DD.") from exc
    return parsed


def build_bocm_search_day_url(target_date: str, *, base_url: str = BOCM_BASE_URL) -> str:
    parsed = validate_bocm_date(target_date)
    query = urlencode({"field_date[date]": parsed.strftime("%d/%m/%Y")})
    return f"{base_url}{BOCM_SEARCH_DAY_PATH}?{query}"


def build_bocm_issue_url(
    target_date: str,
    issue_number: str | int,
    *,
    base_url: str = BOCM_BASE_URL,
) -> str:
    parsed = validate_bocm_date(target_date)
    return f"{base_url}/boletin/bocm-{parsed.strftime('%Y%m%d')}-{issue_number}"


def build_bocm_issue_summary_xml_url(
    target_date: str,
    issue_number: str | int,
    *,
    base_url: str = BOCM_BASE_URL,
) -> str:
    parsed = validate_bocm_date(target_date)
    yyyymmdd = parsed.strftime("%Y%m%d")
    return (
        f"{base_url}/boletin/CM_Boletin_BOCM/{parsed:%Y}/{parsed:%m}/{parsed:%d}/"
        f"BOCM-{yyyymmdd}{issue_number}.xml"
    )


def build_bocm_document_html_url(
    official_identifier: str,
    *,
    base_url: str = BOCM_BASE_URL,
) -> str:
    return f"{base_url}/{official_identifier.lower()}"


def build_bocm_document_xml_url(
    official_identifier: str,
    *,
    base_url: str = BOCM_BASE_URL,
) -> str:
    yyyy, mm, dd, _document_number = _split_bocm_identifier(official_identifier)
    return f"{base_url}/boletin/CM_Orden_BOCM/{yyyy}/{mm}/{dd}/{official_identifier.upper()}.xml"


def build_bocm_document_json_url(
    official_identifier: str,
    *,
    base_url: str = BOCM_BASE_URL,
) -> str:
    yyyy, mm, dd, _document_number = _split_bocm_identifier(official_identifier)
    return f"{base_url}/boletin/CM_Orden_BOCM/{yyyy}/{mm}/{dd}/{official_identifier.upper()}.json"


def build_bocm_document_pdf_url(
    official_identifier: str,
    *,
    base_url: str = BOCM_BASE_URL,
) -> str:
    yyyy, mm, dd, _document_number = _split_bocm_identifier(official_identifier)
    return f"{base_url}/boletin/CM_Orden_BOCM/{yyyy}/{mm}/{dd}/{official_identifier.upper()}.PDF"


def _split_bocm_identifier(official_identifier: str) -> tuple[str, str, str, str]:
    parts = official_identifier.upper().split("-")
    if len(parts) != 3 or parts[0] != "BOCM" or len(parts[1]) != 8 or not parts[2].isdigit():
        raise ValueError(f"Invalid BOCM official identifier: {official_identifier}")
    return parts[1][0:4], parts[1][4:6], parts[1][6:8], parts[2]


@dataclass(frozen=True)
class BOCMHTTPResponse:
    content: bytes
    final_url: str
    audit: BOERequestAudit


class BOCMClient:
    def __init__(
        self,
        *,
        base_url: str = BOCM_BASE_URL,
        request_policy: BOERequestPolicy | None = None,
        sleeper: Callable[[float], None] | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._policy = request_policy or BOERequestPolicy.from_env()
        self._sleeper = sleeper
        self.last_request_audit = BOERequestAudit()

    def fetch_search_day(self, target_date: str) -> BOCMHTTPResponse:
        url = build_bocm_search_day_url(target_date, base_url=self.base_url)
        result = self._get(url)
        self.last_request_audit = result.audit
        result.raise_for_status()
        return BOCMHTTPResponse(
            content=result.content,
            final_url=str(result.request.url),
            audit=result.audit,
        )

    def fetch_issue_page(self, issue_url: str) -> BOCMHTTPResponse:
        result = self._get(issue_url)
        self.last_request_audit = result.audit
        result.raise_for_status()
        return BOCMHTTPResponse(
            content=result.content,
            final_url=str(result.request.url),
            audit=result.audit,
        )

    def _get(self, url: str):
        with httpx.Client(timeout=30.0, follow_redirects=True) as client:
            return self._policy.get(
                url,
                headers={"Accept": "text/html,application/xhtml+xml"},
                client=client,
                sleeper=self._sleeper or time.sleep,
            )
