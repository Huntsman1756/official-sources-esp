from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from urllib.parse import urlencode

import httpx

from official_sources.sources.boe.http_policy import BOERequestAudit, BOERequestPolicy

BDNS_BASE_URL = "https://www.infosubvenciones.es/bdnstrans"
BDNS_API_BASE_URL = f"{BDNS_BASE_URL}/api"
BDNS_DEFAULT_TIMEOUT = httpx.Timeout(connect=10.0, read=60.0, write=30.0, pool=10.0)
BDNS_HARD_MAX_PAGES = 10
BDNS_DEFAULT_PAGE_SIZE = 10
BDNS_HARD_MAX_PAGE_SIZE = 100
BDNS_ALLOWED_CATALOGS = {
    "actividades": "actividades",
    "beneficiarios": "beneficiarios",
    "finalidades": "finalidades",
    "instrumentos": "instrumentos",
    "objetivos": "objetivos",
    "organos": "organos",
    "regiones": "regiones",
    "reglamentos": "reglamentos",
    "sectores": "sectores",
}
BDNS_CATALOGS_WITH_VPD = {
    "actividades",
    "beneficiarios",
    "finalidades",
    "instrumentos",
    "objetivos",
    "organos",
    "regiones",
    "reglamentos",
}
BDNS_ORGANOS_ID_ADMON_VALUES = {"A", "C", "L", "O"}
BDNS_REGLAMENTOS_AMBITO_VALUES = {"A", "C", "G", "M", "P", "S"}


@dataclass(frozen=True)
class BDNSHTTPResponse:
    content: bytes
    final_url: str
    status_code: int
    audit: BOERequestAudit


class BDNSClient:
    def __init__(
        self,
        *,
        base_url: str = BDNS_API_BASE_URL,
        timeout: httpx.Timeout = BDNS_DEFAULT_TIMEOUT,
        request_policy: BOERequestPolicy | None = None,
        client_factory: Callable[[], httpx.Client] | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._request_policy = request_policy or BOERequestPolicy(max_retries=3)
        self._client_factory = client_factory
        self.last_audit = BOERequestAudit()

    def fetch_latest(self, *, limit: int) -> BDNSHTTPResponse:
        url = build_bdns_latest_url(page_size=limit, base_url=self.base_url)
        return self._get(url)

    def fetch_call_detail(self, num_conv: str) -> BDNSHTTPResponse:
        url = build_bdns_call_detail_api_url(num_conv, base_url=self.base_url)
        return self._get(url)

    def fetch_search(
        self,
        *,
        date_from: str | None,
        date_to: str | None,
        page: int,
        page_size: int,
    ) -> BDNSHTTPResponse:
        url = build_bdns_search_url(
            date_from=date_from,
            date_to=date_to,
            page=page,
            page_size=page_size,
            base_url=self.base_url,
        )
        return self._get(url)

    def fetch_catalog(
        self,
        catalog_name: str,
        *,
        vpd: str = "GE",
        id_admon: str | None = None,
        ambito: str | None = None,
    ) -> BDNSHTTPResponse:
        url = build_bdns_catalog_url(
            catalog_name,
            base_url=self.base_url,
            vpd=vpd,
            id_admon=id_admon,
            ambito=ambito,
        )
        return self._get(url)

    def fetch_concessions_search(
        self,
        *,
        num_conv: str,
        page: int,
        page_size: int,
        vpd: str = "GE",
    ) -> BDNSHTTPResponse:
        url = build_bdns_concessions_search_url(
            num_conv=num_conv,
            page=page,
            page_size=page_size,
            vpd=vpd,
            base_url=self.base_url,
        )
        return self._get(url)

    def _get(self, url: str) -> BDNSHTTPResponse:
        with self._build_client() as client:
            response = self._request_policy.get(
                url,
                headers={"Accept": "application/json", "User-Agent": "official-sources/BDNS"},
                client=client,
            )
            self.last_audit = response.audit
            response.raise_for_status()
            return BDNSHTTPResponse(
                content=response.content,
                final_url=str(response.request.url),
                status_code=response.status_code,
                audit=response.audit,
            )

    def _build_client(self) -> httpx.Client:
        if self._client_factory is not None:
            return self._client_factory()
        return httpx.Client(timeout=self._timeout, follow_redirects=True)


def validate_bdns_num_conv(value: str) -> str:
    cleaned = str(value).strip()
    if not re.fullmatch(r"\d{1,12}", cleaned):
        raise ValueError(f"Invalid BDNS numConv: {value}. Expected digits only.")
    return cleaned


def validate_bdns_catalog_name(value: str) -> str:
    cleaned = str(value).strip().lower()
    if cleaned not in BDNS_ALLOWED_CATALOGS:
        allowed = ", ".join(sorted(BDNS_ALLOWED_CATALOGS))
        raise ValueError(f"Invalid BDNS catalog: {value}. Allowed catalogs: {allowed}.")
    return cleaned


def validate_bdns_id_admon(value: str) -> str:
    cleaned = str(value).strip().upper()
    if cleaned not in BDNS_ORGANOS_ID_ADMON_VALUES:
        allowed = ", ".join(sorted(BDNS_ORGANOS_ID_ADMON_VALUES))
        raise ValueError(f"Invalid BDNS id-admon: {value}. Allowed values: {allowed}.")
    return cleaned


def validate_bdns_ambito(value: str) -> str:
    cleaned = str(value).strip().upper()
    if cleaned not in BDNS_REGLAMENTOS_AMBITO_VALUES:
        allowed = ", ".join(sorted(BDNS_REGLAMENTOS_AMBITO_VALUES))
        raise ValueError(f"Invalid BDNS ambito: {value}. Allowed values: {allowed}.")
    return cleaned


def parse_bdns_date_filter(value: str) -> str:
    if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", value):
        raise ValueError(f"Invalid BDNS date filter: {value}. Expected DD/MM/YYYY.")
    day, month, year = value.split("/")
    date(int(year), int(month), int(day))
    return value


def validate_bdns_limit(value: int, *, option_name: str = "limit") -> int:
    if value < 1:
        raise ValueError(f"{option_name} must be at least 1.")
    if value > BDNS_HARD_MAX_PAGE_SIZE:
        raise ValueError(f"{option_name} must be <= {BDNS_HARD_MAX_PAGE_SIZE}.")
    return value


def validate_bdns_max_pages(value: int) -> int:
    if value < 1:
        raise ValueError("max-pages must be at least 1.")
    if value > BDNS_HARD_MAX_PAGES:
        raise ValueError(f"max-pages must be <= {BDNS_HARD_MAX_PAGES}.")
    return value


def build_bdns_latest_url(
    *,
    page: int = 1,
    page_size: int = BDNS_DEFAULT_PAGE_SIZE,
    base_url: str = BDNS_API_BASE_URL,
) -> str:
    validate_bdns_limit(page_size, option_name="page-size")
    query = urlencode({"page": page, "pageSize": page_size})
    return f"{base_url.rstrip()}/convocatorias/ultimas?{query}"


def build_bdns_search_url(
    *,
    date_from: str | None = None,
    date_to: str | None = None,
    page: int = 1,
    page_size: int = BDNS_DEFAULT_PAGE_SIZE,
    base_url: str = BDNS_API_BASE_URL,
) -> str:
    validate_bdns_limit(page_size, option_name="page-size")
    params: dict[str, str | int] = {"page": page, "pageSize": page_size}
    if date_from:
        params["fechaDesde"] = parse_bdns_date_filter(date_from)
    if date_to:
        params["fechaHasta"] = parse_bdns_date_filter(date_to)
    return f"{base_url.rstrip()}/convocatorias/busqueda?{urlencode(params)}"


def build_bdns_concessions_search_url(
    *,
    num_conv: str,
    page: int = 1,
    page_size: int = BDNS_DEFAULT_PAGE_SIZE,
    vpd: str = "GE",
    base_url: str = BDNS_API_BASE_URL,
) -> str:
    if page < 1:
        raise ValueError("page must be at least 1.")
    validate_bdns_limit(page_size, option_name="page-size")
    params: dict[str, str | int] = {
        "page": page,
        "pageSize": page_size,
        "vpd": str(vpd).strip() or "GE",
        "numeroConvocatoria": validate_bdns_num_conv(num_conv),
    }
    return f"{base_url.rstrip()}/concesiones/busqueda?{urlencode(params)}"


def build_bdns_call_detail_api_url(
    num_conv: str,
    *,
    base_url: str = BDNS_API_BASE_URL,
) -> str:
    query = urlencode({"numConv": validate_bdns_num_conv(num_conv)})
    return f"{base_url.rstrip()}/convocatorias?{query}"


def build_bdns_catalog_url(
    catalog_name: str,
    *,
    base_url: str = BDNS_API_BASE_URL,
    vpd: str = "GE",
    id_admon: str | None = None,
    ambito: str | None = None,
) -> str:
    catalog_name = validate_bdns_catalog_name(catalog_name)
    path = BDNS_ALLOWED_CATALOGS[catalog_name]
    params: dict[str, str] = {}
    if catalog_name in BDNS_CATALOGS_WITH_VPD:
        params["vpd"] = str(vpd).strip() or "GE"
    if catalog_name == "organos":
        if id_admon is None:
            raise ValueError("id-admon is required for BDNS organos catalog.")
        params["idAdmon"] = validate_bdns_id_admon(id_admon)
    if catalog_name == "reglamentos" and ambito:
        params["ambito"] = validate_bdns_ambito(ambito)
    query = f"?{urlencode(params)}" if params else ""
    return f"{base_url.rstrip('/')}/{path}{query}"


def build_bdns_call_detail_url(
    num_conv: str,
    *,
    base_url: str = BDNS_BASE_URL,
) -> str:
    return f"{base_url.rstrip()}/GE/es/convocatoria/{validate_bdns_num_conv(num_conv)}"
