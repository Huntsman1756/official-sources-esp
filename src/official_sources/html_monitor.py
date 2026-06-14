from __future__ import annotations

import hashlib
import html
import json
import os
import re
import ssl
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlencode, urljoin

import httpx

from official_sources.source_registry import get_source

HTMLFetcher = Callable[[str], bytes | str]
HTML_RELAY_TARGETS = frozenset({"cuenca", "salamanca", "zaragoza"})
HTML_RELAY_BASE_URL_ENV = "OFFICIAL_SOURCES_HTML_RELAY_BASE_URL"
HTML_RELAY_SECRET_ENV = "OFFICIAL_SOURCES_HTML_RELAY_SECRET"

_HTML_MONITOR_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36 "
        "official-sources-html-monitor/0.1"
    ),
}

_HTML_EXTRA_CA_PEMS = (
    """
-----BEGIN CERTIFICATE-----
MIIEszCCA5ugAwIBAgIQCyWUIs7ZgSoVoE6ZUooO+jANBgkqhkiG9w0BAQsFADBh
MQswCQYDVQQGEwJVUzEVMBMGA1UEChMMRGlnaUNlcnQgSW5jMRkwFwYDVQQLExB3
d3cuZGlnaWNlcnQuY29tMSAwHgYDVQQDExdEaWdpQ2VydCBHbG9iYWwgUm9vdCBH
MjAeFw0xNzExMDIxMjI0MzNaFw0yNzExMDIxMjI0MzNaMGAxCzAJBgNVBAYTAlVT
MRUwEwYDVQQKEwxEaWdpQ2VydCBJbmMxGTAXBgNVBAsTEHd3dy5kaWdpY2VydC5j
b20xHzAdBgNVBAMTFlJhcGlkU1NMIFRMUyBSU0EgQ0EgRzEwggEiMA0GCSqGSIb3
DQEBAQUAA4IBDwAwggEKAoIBAQC/uVklRBI1FuJdUEkFCuDL/I3aJQiaZ6aibRHj
ap/ap9zy1aYNrphe7YcaNwMoPsZvXDR+hNJOo9gbgOYVTPq8gXc84I75YKOHiVA4
NrJJQZ6p2sJQyqx60HkEIjzIN+1LQLfXTlpuznToOa1hyTD0yyitFyOYwURM+/CI
8FNFMpBhw22hpeAQkOOLmsqT5QZJYeik7qlvn8gfD+XdDnk3kkuuu0eG+vuyrSGr
5uX5LRhFWlv1zFQDch/EKmd163m6z/ycx/qLa9zyvILc7cQpb+k7TLra9WE17YPS
n9ANjG+ECo9PDW3N9lwhKQCNvw1gGoguyCQu7HE7BnW8eSSFAgMBAAGjggFmMIIB
YjAdBgNVHQ4EFgQUDNtsgkkPSmcKuBTuesRIUojrVjgwHwYDVR0jBBgwFoAUTiJU
IBiV5uNu5g/6+rkS7QYXjzkwDgYDVR0PAQH/BAQDAgGGMB0GA1UdJQQWMBQGCCsG
AQUFBwMBBggrBgEFBQcDAjASBgNVHRMBAf8ECDAGAQH/AgEAMDQGCCsGAQUFBwEB
BCgwJjAkBggrBgEFBQcwAYYYaHR0cDovL29jc3AuZGlnaWNlcnQuY29tMEIGA1Ud
HwQ7MDkwN6A1oDOGMWh0dHA6Ly9jcmwzLmRpZ2ljZXJ0LmNvbS9EaWdpQ2VydEds
b2JhbFJvb3RHMi5jcmwwYwYDVR0gBFwwWjA3BglghkgBhv1sAQEwKjAoBggrBgEF
BQcCARYcaHR0cHM6Ly93d3cuZGlnaWNlcnQuY29tL0NQUzALBglghkgBhv1sAQIw
CAYGZ4EMAQIBMAgGBmeBDAECAjANBgkqhkiG9w0BAQsFAAOCAQEAGUSlOb4K3Wtm
SlbmE50UYBHXM0SKXPqHMzk6XQUpCheF/4qU8aOhajsyRQFDV1ih/uPIg7YHRtFi
CTq4G+zb43X1T77nJgSOI9pq/TqCwtukZ7u9VLL3JAq3Wdy2moKLvvC8tVmRzkAe
0xQCkRKIjbBG80MSyDX/R4uYgj6ZiNT/Zg6GI6RofgqgpDdssLc0XIRQEotxIZcK
zP3pGJ9FCbMHmMLLyuBd+uCWvVcF2ogYAawufChS/PT61D9rqzPRS5I2uqa3tmIT
44JhJgWhBnFMb7AGQkvNq9KNS9dd3GWc17H/dXa1enoxzWjE0hBdFjxPhUb0W3wi
8o34/m8Fxw==
-----END CERTIFICATE-----
""",
    """
-----BEGIN CERTIFICATE-----
MIIFjTCCA3WgAwIBAgIRAIN9TriekS/nLK07x2kt3CAwDQYJKoZIhvcNAQELBQAw
TDEgMB4GA1UECxMXR2xvYmFsU2lnbiBSb290IENBIC0gUjYxEzARBgNVBAoTCkds
b2JhbFNpZ24xEzARBgNVBAMTCkdsb2JhbFNpZ24wHhcNMjUwNTIxMDIzNjUyWhcN
MjcwNTIxMDAwMDAwWjBVMQswCQYDVQQGEwJCRTEZMBcGA1UEChMQR2xvYmFsU2ln
biBudi1zYTErMCkGA1UEAxMiR2xvYmFsU2lnbiBHQ0MgUjYgQWxwaGFTU0wgQ0Eg
MjAyNTCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBAJ/oiu0Bviq52UUE
ADbFWmgu3rC7KDSMoorLN1Wd03McG3Z1aP71DlPCE33838r72Dfuj5M9LXfiQLJp
Au6MwNExmKOzothw4x0zGf5oBYyrCMGm3fBpLPafwYQ3MchBOWMTbf83rKUPLH48
KCJ0MnU8GUl8oA/J81wIvbbKPuNrFf6hvJDccjzc4NyxLz3A89zjV2g5whCg5O0u
9YX4Zxk9JHuc/LvllOJO4waAYLjbWBJkz3rV3ts1SmSYnJqmyRTIjXwQgRvhEYqt
DbRskt0W7M6cPwCze3GTBN2UHNpHkMs3YmVxku68I0aOQn5+uz//fDROP3z1Z/7I
APteRtECAwEAAaOCAV8wggFbMA4GA1UdDwEB/wQEAwIBhjAdBgNVHSUEFjAUBggr
BgEFBQcDAQYIKwYBBQUHAwIwEgYDVR0TAQH/BAgwBgEB/wIBADAdBgNVHQ4EFgQU
xbSTj28r3B5Iv7cQMIXO0bK7SC0wHwYDVR0jBBgwFoAUrmwFo5MT4qLn4tcc1sfw
f8hnU6AwewYIKwYBBQUHAQEEbzBtMC4GCCsGAQUFBzABhiJodHRwOi8vb2NzcDIu
Z2xvYmFsc2lnbi5jb20vcm9vdHI2MDsGCCsGAQUFBzAChi9odHRwOi8vc2VjdXJl
Lmdsb2JhbHNpZ24uY29tL2NhY2VydC9yb290LXI2LmNydDA2BgNVHR8ELzAtMCug
KaAnhiVodHRwOi8vY3JsLmdsb2JhbHNpZ24uY29tL3Jvb3QtcjYuY3JsMCEGA1Ud
IAQaMBgwCAYGZ4EMAQIBMAwGCisGAQQBoDIKAQMwDQYJKoZIhvcNAQELBQADggIB
AB/uvBuZf4CiuSahwiXn4geF52roAH+6jxsEPTXTfb7bbeMDXsYgRRsOTNA70ruZ
Tnz5DfFMuBhNoFhIFb0qR1izdy6VkdKOqFPNF2dOFI1EcnY9l2ory9mrzHqVbrL4
vzUd17FLUVyjTVU7PAv4nxyhnO1GTeT83YlrdRF31NyR6bvZVTEERHmpbWSgeveJ
LRtaMzlGWiLZ8IwkH7o6GH3jp/KPtDW4Npu8w64HrRZdN2pqQhi7+YKwfHM7H+2U
dM1BGN0sjOWMVbMSB9MtCsleS2Mb7TRZEbOHxECJLLIluQypZr7Pol3+hAqrhyKI
k+6y+Da0NeDuWxW59Ku4NvClqW1UFX1SpfNGhzVfp/CH+vPM1tySomx2jE0EnYZu
GwVucXPBsp5nUWqUV9+143glVuS7GTg9hFPjNBInn17HbCoIIQIOzj5Vd9bK3A9U
GxXNpwenDHEalCsD/4eQYDHPhFE7sNe0D/OXu+FAM02VZkARx37Jp4bDdujvgL9P
vZPR3wThvDN1CTU8Bc3xea3yKFAraKcPZLkhReQUAm2VpR+HSJRPlUpYizlF9WkL
h3KcAVCBJWvnOkVwxyU5QJMcnwW95JlOtx+9100GL99jHE5rs3gXp7F4bg8H01QT
9jVOhBBmQ7nQoXuwI0tqal2QUqZz3eeu62CU7xBwtfYR
-----END CERTIFICATE-----
""",
    """
-----BEGIN CERTIFICATE-----
MIIG1jCCBL6gAwIBAgIQNMarBE42mRJRyCULbJTWwDANBgkqhkiG9w0BAQsFADA7
MQswCQYDVQQGEwJFUzERMA8GA1UECgwIRk5NVC1SQ00xGTAXBgNVBAsMEEFDIFJB
SVogRk5NVC1SQ00wHhcNMTMwNjI0MTA1MjU5WhcNMjgwNjI0MTA1MjU5WjBHMQsw
CQYDVQQGEwJFUzERMA8GA1UECgwIRk5NVC1SQ00xJTAjBgNVBAsMHEFDIENvbXBv
bmVudGVzIEluZm9ybcOhdGljb3MwggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEK
AoIBAQCXVx8rdbF7/xY44CaSqzzGo5BhvzA8knxC/3KJYVzTf+CkOvMxMUDub8b0
h38MDujm/RKZhBNOWbKhxF3U61ZVhcR9xOCciuS/soT80m3BByxAKcZsNka0jCA4
XRkglDaAFxCHEZ06MOnvXsSOZDfPYahbQ3VFCVycJuhlHdAwSpmceQwcRYkR6YgX
wTiyzCNGivMKAmRS3dItqDOmDW/nxiDFq/Jd8VWY7GFkwbbAeqYId8FjN8zfvafu
nsB9SLFkUjPPMeqfmC7Bdh7HMxLpaOXROwH201cmlebiPkn0xSFxXFqwhhr6yN8U
QYZ3O/+xdHLrS6DS9+CJUF6d09ijAgMBAAGjggLIMIICxDASBgNVHRMBAf8ECDAG
AQH/AgEAMA4GA1UdDwEB/wQEAwIBBjAdBgNVHQ4EFgQUGfhYLxTWpsybBJgIDUzX
qwCng2UwgZgGCCsGAQUFBwEBBIGLMIGIMEkGCCsGAQUFBzABhj1odHRwOi8vb2Nz
cGZubXRyY21jYS5jZXJ0LmZubXQuZXMvb2NzcGZubXRyY21jYS9PY3NwUmVzcG9u
ZGVyMDsGCCsGAQUFBzAChi9odHRwOi8vd3d3LmNlcnQuZm5tdC5lcy9jZXJ0cy9B
Q1JBSVpGTk1UUkNNLmNydDAfBgNVHSMEGDAWgBT3fcX9xOiaG3dkp/UdoMy/h2Ca
bTCB6wYDVR0gBIHjMIHgMIHdBgRVHSAAMIHUMCkGCCsGAQUFBwIBFh1odHRwOi8v
d3d3LmNlcnQuZm5tdC5lcy9kcGNzLzCBpgYIKwYBBQUHAgIwgZkMgZZTdWpldG8g
YSBsYXMgY29uZGljaW9uZXMgZGUgdXNvIGV4cHVlc3RhcyBlbiBsYSBEZWNsYXJh
Y2nDs24gZGUgUHLDoWN0aWNhcyBkZSBDZXJ0aWZpY2FjacOzbiBkZSBsYSBGTk1U
LVJDTSAoIEMvIEpvcmdlIEp1YW4sIDEwNi0yODAwOS1NYWRyaWQtRXNwYcOxYSkw
gdQGA1UdHwSBzDCByTCBxqCBw6CBwIaBkGxkYXA6Ly9sZGFwZm5tdC5jZXJ0LmZu
bXQuZXMvQ049Q1JMLE9VPUFDJTIwUkFJWiUyMEZOTVQtUkNNLE89Rk5NVC1SQ00s
Qz1FUz9hdXRob3JpdHlSZXZvY2F0aW9uTGlzdDtiaW5hcnk/YmFzZT9vYmplY3Rj
bGFzcz1jUkxEaXN0cmlidXRpb25Qb2ludIYraHR0cDovL3d3dy5jZXJ0LmZubXQu
ZXMvY3Jscy9BUkxGTk1UUkNNLmNybDANBgkqhkiG9w0BAQsFAAOCAgEAo2bsQ2xL
Dcyodieqjd+uy/lfxDw/MbrAq/ZaNFkIlcypUYamOM4vrm5rz8oLjPCoLkJ48P+n
P08Gkcl5Q6q6VFcZLia+U3gfHXrkyqToQlrtViGCGH3xA4u56XtMHGXSdk9vQ0yD
nW5f7bUEkp+uvcKewrOvNcpbIAgD4eU7gdOS0w7BagcFRBgTKBw2s3z73fRZtouJ
g/atmWYtXbBsfNjph+pCh+h5sbSyZUVzO5AemyjpYYYNMWDQrTXq+7O8zIPuPaNE
SjEexuzn+VjHG90RlUK1LygARi+Ir0opD2w6erb/hK8Eea7MFdKQ2ASqNBGJggNo
5vfPVvjHiL+Antmh7mQSKL+4YwFU64d4KK9k0C1mbJethDQFKcjTK1vMvnXFiups
IuyTqwKauo7u2zMKzY4r3VYOW9TpMyLPFIY8pII5GyNzXlL0F4nscOvduTEPEYqx
eNJfpDDPY/DO8WfxgdRTy2W3D/UoAulb+Y+nuzGGCtFQrsSMQX487R+aY0nWot/h
ajef6BcPuxhDfQrg5IafrISVmcJAplb3tXhh0sz7RbYz6jf1bke4eU5fnrTMtGlV
teUL2vjrfUPHW07kBJuaQ7sxORNV3bpHisOnHj+AriQzCn5vINpSHW6hTm7IfRkb
ltu/aQrsMuUhP7HE/v+uXe5CuboV5ubZhHU=
-----END CERTIFICATE-----
""",
    """
-----BEGIN CERTIFICATE-----
MIIETjCCAzagAwIBAgINAe5fIh38YjvUMzqFVzANBgkqhkiG9w0BAQsFADBMMSAw
HgYDVQQLExdHbG9iYWxTaWduIFJvb3QgQ0EgLSBSMzETMBEGA1UEChMKR2xvYmFs
U2lnbjETMBEGA1UEAxMKR2xvYmFsU2lnbjAeFw0xODExMjEwMDAwMDBaFw0yODEx
MjEwMDAwMDBaMFAxCzAJBgNVBAYTAkJFMRkwFwYDVQQKExBHbG9iYWxTaWduIG52
LXNhMSYwJAYDVQQDEx1HbG9iYWxTaWduIFJTQSBPViBTU0wgQ0EgMjAxODCCASIw
DQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBAKdaydUMGCEAI9WXD+uu3Vxoa2uP
UGATeoHLl+6OimGUSyZ59gSnKvuk2la77qCk8HuKf1UfR5NhDW5xUTolJAgvjOH3
idaSz6+zpz8w7bXfIa7+9UQX/dhj2S/TgVprX9NHsKzyqzskeU8fxy7quRU6fBhM
abO1IFkJXinDY+YuRluqlJBJDrnw9UqhCS98NE3QvADFBlV5Bs6i0BDxSEPouVq1
lVW9MdIbPYa+oewNEtssmSStR8JvA+Z6cLVwzM0nLKWMjsIYPJLJLnNvBhBWk0Cq
o8VS++XFBdZpaFwGue5RieGKDkFNm5KQConpFmvv73W+eka440eKHRwup08CAwEA
AaOCASkwggElMA4GA1UdDwEB/wQEAwIBhjASBgNVHRMBAf8ECDAGAQH/AgEAMB0G
A1UdDgQWBBT473/yzXhnqN5vjySNiPGHAwKz6zAfBgNVHSMEGDAWgBSP8Et/qC5F
JK5NUPpjmove4t0bvDA+BggrBgEFBQcBAQQyMDAwLgYIKwYBBQUHMAGGImh0dHA6
Ly9vY3NwMi5nbG9iYWxzaWduLmNvbS9yb290cjMwNgYDVR0fBC8wLTAroCmgJ4Yl
aHR0cDovL2NybC5nbG9iYWxzaWduLmNvbS9yb290LXIzLmNybDBHBgNVHSAEQDA+
MDwGBFUdIAAwNDAyBggrBgEFBQcCARYmaHR0cHM6Ly93d3cuZ2xvYmFsc2lnbi5j
b20vcmVwb3NpdG9yeS8wDQYJKoZIhvcNAQELBQADggEBAJmQyC1fQorUC2bbmANz
EdSIhlIoU4r7rd/9c446ZwTbw1MUcBQJfMPg+NccmBqixD7b6QDjynCy8SIwIVbb
0615XoFYC20UgDX1b10d65pHBf9ZjQCxQNqQmJYaumxtf4z1s4DfjGRzNpZ5eWl0
6r/4ngGPoJVpjemEuunl1Ig423g7mNA2eymw0lIYkN5SQwCuaifIFJ6GlazhgDEw
fpolu4usBCOmmQDo8dIm7A9+O4orkjgTHY+GzYZSR+Y0fFukAj6KYXwidlNalFMz
hriSqHKvoflShx8xpfywgVcvzfTO3PYkz6fiNJBonf6q8amaEsybwMbDqKWwIX7e
SPY=
-----END CERTIFICATE-----
""",
)


class HTMLMonitorError(ValueError):
    pass


@dataclass(frozen=True)
class HTMLParseResult:
    raw_page_hash: str
    records: list[dict[str, Any]]
    raw_page: bytes | None = None


@dataclass(frozen=True)
class BOPAcorunaAnnouncement:
    entry_id: str | None
    document_id: str | None
    title: str | None
    official_url: str | None


def validate_html_monitor_date(value: str) -> str:
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError as exc:
        raise HTMLMonitorError("--date must use YYYY-MM-DD format") from exc


def build_html_entry_hash(
    *,
    source_code: str,
    published_at: str | None,
    official_url: str | None,
    document_id: str | None,
    title: str | None,
) -> str:
    if official_url:
        hash_input = f"{source_code}{published_at or ''}{official_url}"
        return hashlib.sha256(hash_input.encode()).hexdigest()
    return hashlib.sha256(f"{source_code}{document_id or ''}{title or ''}".encode()).hexdigest()


def build_html_monitor_output_path(output_root: Path, source_code: str, target_date: str) -> Path:
    return output_root / source_code / target_date / "html_discovery.jsonl"


def build_bop_a_coruna_html_url(template_url: str, *, target_date: str) -> str:
    parsed_date = date.fromisoformat(validate_html_monitor_date(target_date))
    date_ddmmyyyy = quote(parsed_date.strftime("%d/%m/%Y"), safe="")
    return template_url.replace("{date_ddmmyyyy}", date_ddmmyyyy).replace(
        "{date}", parsed_date.isoformat()
    )


def build_bop_albacete_html_url(template_url: str, *, target_date: str) -> str:
    validate_html_monitor_date(target_date)
    return template_url.replace("{date}", target_date)


def build_bop_alicante_html_url(template_url: str, *, target_date: str) -> str:
    parsed_date = date.fromisoformat(validate_html_monitor_date(target_date))
    date_ddmmyyyy = parsed_date.strftime("%d/%m/%Y")
    param_xml = (
        "<raiz><entrada><registro>"
        f"<fechaPub>{date_ddmmyyyy}</fechaPub>"
        "<tipoorganismo></tipoorganismo>"
        "</registro></entrada></raiz>"
    )
    return f"{template_url}?{urlencode({'nemo': 'BOP_CON', 'param': param_xml, 'usuario': '-'})}"


def build_bop_almeria_html_url(template_url: str, *, target_date: str) -> str:
    validate_html_monitor_date(target_date)
    return template_url


def build_bop_araba_alava_html_url(template_url: str, *, target_date: str) -> str:
    parsed_date = date.fromisoformat(validate_html_monitor_date(target_date))
    date_ddmmyyyy = quote(parsed_date.strftime("%d/%m/%Y"), safe="")
    return template_url.replace("{date_ddmmyyyy}", date_ddmmyyyy).replace(
        "{date}", parsed_date.isoformat()
    )


def build_bop_avila_html_url(template_url: str, *, target_date: str) -> str:
    parsed_date = date.fromisoformat(validate_html_monitor_date(target_date))
    return (
        template_url.replace("{yyyy}", f"{parsed_date:%Y}")
        .replace("{dd_mm_yyyy}", parsed_date.strftime("%d-%m-%Y"))
        .replace("{date}", parsed_date.isoformat())
    )


def build_bop_barcelona_html_url(template_url: str, *, target_date: str) -> str:
    validate_html_monitor_date(target_date)
    return template_url


def build_bon_html_url(template_url: str, *, target_date: str) -> str:
    parsed_date = date.fromisoformat(validate_html_monitor_date(target_date))
    params = {
        "p_p_id": "es_navarra_bon_boletin_selectormes_portlet_BoletinSelectorMesPortlet",
        "p_p_lifecycle": "0",
        "p_p_state": "normal",
        "p_p_mode": "view",
        "_es_navarra_bon_boletin_selectormes_portlet_BoletinSelectorMesPortlet_anyo": str(
            parsed_date.year
        ),
        "_es_navarra_bon_boletin_selectormes_portlet_BoletinSelectorMesPortlet_mes": str(
            parsed_date.month
        ),
    }
    return f"{template_url}?{urlencode(params)}"


def build_bome_html_url(template_url: str, *, target_date: str) -> str:
    validate_html_monitor_date(target_date)
    return template_url


def build_bocce_html_url(template_url: str, *, target_date: str) -> str:
    validate_html_monitor_date(target_date)
    return template_url


def build_bop_bizkaia_html_url(template_url: str, *, target_date: str) -> str:
    validate_html_monitor_date(target_date)
    return template_url


def build_bop_burgos_html_url(template_url: str, *, target_date: str) -> str:
    validate_html_monitor_date(target_date)
    return template_url.replace("{date}", target_date)


def build_bop_cadiz_html_url(template_url: str, *, target_date: str) -> str:
    validate_html_monitor_date(target_date)
    return template_url


def build_bop_castellon_html_url(template_url: str, *, target_date: str) -> str:
    validate_html_monitor_date(target_date)
    return template_url


def build_bop_cordoba_html_url(template_url: str, *, target_date: str) -> str:
    parsed_date = date.fromisoformat(validate_html_monitor_date(target_date))
    return template_url.replace("{dd_mm_yyyy}", parsed_date.strftime("%d-%m-%Y")).replace(
        "{date}", parsed_date.isoformat()
    )


def build_bop_ciudad_real_html_url(template_url: str, *, target_date: str) -> str:
    parsed_date = date.fromisoformat(validate_html_monitor_date(target_date))
    return (
        template_url.replace("{yyyy}", f"{parsed_date:%Y}")
        .replace("{mm}", f"{parsed_date:%m}")
        .replace("{dd}", f"{parsed_date:%d}")
        .replace("{date}", parsed_date.isoformat())
    )


def build_bop_cuenca_html_url(template_url: str, *, target_date: str) -> str:
    parsed_date = date.fromisoformat(validate_html_monitor_date(target_date))
    date_ddmmyyyy = quote(parsed_date.strftime("%d/%m/%Y"), safe="")
    return template_url.replace("{date_ddmmyyyy}", date_ddmmyyyy).replace(
        "{date}", parsed_date.isoformat()
    )


def build_bop_girona_html_url(template_url: str, *, target_date: str) -> str:
    validate_html_monitor_date(target_date)
    return template_url.replace("{date}", target_date)


def build_bop_gipuzkoa_html_url(template_url: str, *, target_date: str) -> str:
    parsed_date = date.fromisoformat(validate_html_monitor_date(target_date))
    return (
        template_url.replace("{yyyy}", f"{parsed_date:%Y}")
        .replace("{yy}", f"{parsed_date:%y}")
        .replace("{mm}", f"{parsed_date:%m}")
        .replace("{dd}", f"{parsed_date:%d}")
        .replace("{yymmdd}", f"{parsed_date:%y%m%d}")
        .replace("{date}", parsed_date.isoformat())
    )


def build_bop_granada_html_url(template_url: str, *, target_date: str) -> str:
    parsed_date = date.fromisoformat(validate_html_monitor_date(target_date))
    return template_url.replace("{dd_mm_yyyy}", parsed_date.strftime("%d-%m-%Y")).replace(
        "{date}", parsed_date.isoformat()
    )


def build_bop_huesca_html_url(template_url: str, *, target_date: str) -> str:
    validate_html_monitor_date(target_date)
    return template_url.replace("{date}", target_date)


def build_bop_jaen_html_url(template_url: str, *, target_date: str) -> str:
    parsed_date = date.fromisoformat(validate_html_monitor_date(target_date))
    return template_url.replace("{dd_mm_yyyy}", parsed_date.strftime("%d-%m-%Y")).replace(
        "{date}", parsed_date.isoformat()
    )


def build_bop_las_palmas_html_url(template_url: str, *, target_date: str) -> str:
    validate_html_monitor_date(target_date)
    return template_url.replace("{date}", target_date)


def build_bop_leon_html_url(template_url: str, *, target_date: str) -> str:
    parsed_date = date.fromisoformat(validate_html_monitor_date(target_date))
    return template_url.replace("{dd_mm_yyyy}", parsed_date.strftime("%d-%m-%Y")).replace(
        "{date}", parsed_date.isoformat()
    )


def build_bop_lleida_html_url(template_url: str, *, target_date: str) -> str:
    validate_html_monitor_date(target_date)
    return template_url


def build_bop_malaga_html_url(template_url: str, *, target_date: str) -> str:
    validate_html_monitor_date(target_date)
    return template_url


def build_bop_pontevedra_html_url(template_url: str, *, target_date: str) -> str:
    parsed_date = date.fromisoformat(validate_html_monitor_date(target_date))
    return (
        template_url.replace("{yyyy}", f"{parsed_date:%Y}")
        .replace("{mm}", f"{parsed_date:%m}")
        .replace("{dd}", f"{parsed_date:%d}")
        .replace("{date}", parsed_date.isoformat())
    )


def build_bop_salamanca_html_url(template_url: str, *, target_date: str) -> str:
    validate_html_monitor_date(target_date)
    return template_url.replace("{date}", target_date)


def build_bop_palencia_html_url(template_url: str, *, target_date: str) -> str:
    validate_html_monitor_date(target_date)
    return template_url


def build_bop_santa_cruz_tenerife_html_url(template_url: str, *, target_date: str) -> str:
    validate_html_monitor_date(target_date)
    return template_url.replace("{date}", target_date)


def build_bop_segovia_html_url(template_url: str, *, target_date: str) -> str:
    validate_html_monitor_date(target_date)
    return template_url


def build_bop_sevilla_html_url(template_url: str, *, target_date: str) -> str:
    validate_html_monitor_date(target_date)
    return template_url


def build_bop_soria_html_url(template_url: str, *, target_date: str) -> str:
    parsed_date = date.fromisoformat(validate_html_monitor_date(target_date))
    return template_url.replace("{dd_mm_yyyy}", parsed_date.strftime("%d-%m-%Y")).replace(
        "{date}", parsed_date.isoformat()
    )


def build_bop_tarragona_html_url(template_url: str, *, target_date: str) -> str:
    validate_html_monitor_date(target_date)
    return template_url.replace("{date}", target_date)


def build_bop_teruel_html_url(template_url: str, *, target_date: str) -> str:
    parsed_date = date.fromisoformat(validate_html_monitor_date(target_date))
    return template_url.replace("{yyyymmdd}", parsed_date.strftime("%Y%m%d")).replace(
        "{date}", parsed_date.isoformat()
    )


def build_bop_toledo_html_url(template_url: str, *, target_date: str) -> str:
    parsed_date = date.fromisoformat(validate_html_monitor_date(target_date))
    date_ddmmyyyy = quote(parsed_date.strftime("%d/%m/%Y"), safe="")
    return template_url.replace("{date_ddmmyyyy}", date_ddmmyyyy).replace(
        "{date}", parsed_date.isoformat()
    )


def build_bop_valencia_html_url(template_url: str, *, target_date: str) -> str:
    validate_html_monitor_date(target_date)
    return template_url


def build_bop_valladolid_html_url(template_url: str, *, target_date: str) -> str:
    validate_html_monitor_date(target_date)
    return template_url.replace("{date}", target_date)


def build_bop_zaragoza_html_url(template_url: str, *, target_date: str) -> str:
    validate_html_monitor_date(target_date)
    return template_url.replace("{date}", target_date)


def build_bop_zamora_html_url(template_url: str, *, target_date: str) -> str:
    validate_html_monitor_date(target_date)
    return template_url


def build_bopa_html_url(template_url: str, *, target_date: str) -> str:
    parsed_date = date.fromisoformat(validate_html_monitor_date(target_date))
    summary_date = parsed_date.strftime("%d/%m/%Y")
    params = {"p_r_p_summaryDate": summary_date, "p_r_p_summaryIsSearch": "false"}
    return f"{template_url}?{urlencode(params)}"


def build_docm_html_url(template_url: str, *, target_date: str) -> str:
    parsed_date = date.fromisoformat(validate_html_monitor_date(target_date))
    return template_url.replace("{yyyymmdd}", f"{parsed_date:%Y%m%d}").replace(
        "{date}", parsed_date.isoformat()
    )


def select_html_access_method(source: dict[str, Any]) -> dict[str, Any]:
    for access_method in source.get("access_methods", []):
        if (
            access_method.get("type") == "html"
            and access_method.get("status") == "validated"
            and str(access_method.get("url", "")).strip()
        ):
            return access_method
    raise HTMLMonitorError(
        f"{source.get('source_code', 'source')} does not have a validated html access method"
    )


def monitor_html_source(
    source: dict[str, Any],
    *,
    fetcher: HTMLFetcher | None = None,
    target_date: str,
    limit: int | None = None,
) -> HTMLParseResult:
    target_date = validate_html_monitor_date(target_date)
    if limit is not None and limit < 1:
        raise HTMLMonitorError("--limit must be greater than zero")

    source_code = source["source_code"]
    access_method = select_html_access_method(source)
    page_url = _build_html_monitor_url(source_code, access_method["url"], target_date=target_date)
    fetch = fetcher or fetch_html
    relay_key = str(access_method.get("relay_key", "")).strip()
    if relay_key and fetcher is None:
        raw_page = fetch_html_via_relay(relay_key, target_date=target_date)
    elif source_code == "BOP_BIZKAIA":
        landing_page = _coerce_page_bytes(fetch(page_url))
        detail_url = _extract_bop_bizkaia_latest_detail_url(
            landing_page.decode("utf-8", errors="replace"),
            page_url,
        )
        raw_page = _coerce_page_bytes(fetch(detail_url))
        page_url = detail_url
    elif source_code == "BOP_SEVILLA":
        landing_page = _coerce_page_bytes(fetch(page_url))
        detail_url = _extract_bop_sevilla_latest_detail_url(
            landing_page.decode("utf-8", errors="replace"),
            page_url,
        )
        raw_page = _coerce_page_bytes(fetch(detail_url))
        page_url = detail_url
    elif source_code == "BOP_SORIA":
        landing_page = _coerce_page_bytes(fetch(page_url))
        detail_url = _extract_bop_soria_detail_url(
            landing_page.decode("utf-8", errors="replace"),
            page_url,
        )
        raw_page = _coerce_page_bytes(fetch(detail_url))
        page_url = detail_url
    elif source_code == "BON":
        landing_page = _coerce_page_bytes(fetch(page_url))
        detail_url = _extract_bon_issue_url(
            landing_page.decode("utf-8", errors="replace"),
            page_url,
            target_date,
        )
        raw_page = _coerce_page_bytes(fetch(detail_url))
        page_url = detail_url
    elif source_code == "BOME":
        landing_page = _coerce_page_bytes(fetch(page_url))
        detail_url = _extract_bome_issue_url(
            landing_page.decode("utf-8", errors="replace"),
            page_url,
            target_date,
        )
        raw_page = _coerce_page_bytes(fetch(detail_url))
        page_url = detail_url
    elif source_code == "BOP_ZAMORA":
        landing_page = _coerce_page_bytes(fetch(page_url))
        detail_url = _extract_bop_zamora_detail_url(
            landing_page.decode("utf-8", errors="replace"),
            page_url,
            target_date,
        )
        raw_page = _coerce_page_bytes(fetch(detail_url))
        page_url = detail_url
    elif source_code == "BOP_BURGOS":
        landing_page = _coerce_page_bytes(fetch(page_url))
        detail_url = _extract_bop_burgos_detail_url(
            landing_page.decode("utf-8", errors="replace"),
            page_url,
        )
        raw_page = _coerce_page_bytes(fetch(detail_url))
        page_url = detail_url
    elif source_code == "BOP_CADIZ":
        landing_page = _coerce_page_bytes(fetch(page_url))
        landing_text = landing_page.decode("utf-8", errors="replace")
        detail_url = _extract_bop_cadiz_latest_detail_url(landing_text, page_url)
        if detail_url:
            raw_page = _coerce_page_bytes(fetch(detail_url))
            page_url = detail_url
        else:
            raw_page = landing_page
    elif source_code == "BOP_ALMERIA" and fetcher is None:
        raw_page = fetch_bop_almeria_zkau_response(page_url)
    else:
        raw_page = _coerce_page_bytes(fetch(page_url))
    raw_page_hash = hashlib.sha256(raw_page).hexdigest()
    monitor_run_id = hashlib.sha256(
        f"{source_code}{page_url}{target_date}{raw_page_hash}".encode()
    ).hexdigest()[:16]
    result = _parse_html_monitor_response(
        raw_page,
        source_code=source_code,
        page_url=page_url,
        target_date=target_date,
        discovered_at=f"{target_date}T00:00:00Z",
        monitor_run_id=monitor_run_id,
    )
    if limit is None:
        return HTMLParseResult(
            raw_page_hash=result.raw_page_hash,
            records=result.records,
            raw_page=raw_page,
        )
    return HTMLParseResult(
        raw_page_hash=result.raw_page_hash,
        records=result.records[:limit],
        raw_page=raw_page,
    )


def monitor_html_source_code(
    source_code: str,
    *,
    fetcher: HTMLFetcher | None = None,
    target_date: str,
    limit: int | None = None,
) -> HTMLParseResult:
    return monitor_html_source(
        get_source(source_code),
        fetcher=fetcher,
        target_date=target_date,
        limit=limit,
    )


def parse_bop_a_coruna_html(
    raw_page: bytes | str,
    *,
    source_code: str,
    page_url: str,
    published_at: str,
    discovered_at: str,
    monitor_run_id: str,
) -> HTMLParseResult:
    raw_bytes = _coerce_page_bytes(raw_page)
    raw_page_hash = hashlib.sha256(raw_bytes).hexdigest()
    parser = _BOPAcorunaSummaryParser(page_url)
    parser.feed(raw_bytes.decode("utf-8", errors="replace"))
    records = [
        _build_bop_a_coruna_record(
            announcement=announcement,
            source_code=source_code,
            page_url=page_url,
            raw_page_hash=raw_page_hash,
            published_at=published_at,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
        )
        for announcement in parser.announcements
        if announcement.document_id or announcement.title
    ]
    return HTMLParseResult(raw_page_hash=raw_page_hash, records=records)


def parse_bop_albacete_html(
    raw_page: bytes | str,
    *,
    source_code: str,
    page_url: str,
    requested_date: str,
    discovered_at: str,
    monitor_run_id: str,
) -> HTMLParseResult:
    raw_bytes = _coerce_page_bytes(raw_page)
    raw_page_hash = hashlib.sha256(raw_bytes).hexdigest()
    text = raw_bytes.decode("utf-8", errors="replace")
    published_at = _extract_bop_albacete_publication_date(text) or requested_date
    records = [
        _build_html_record(
            source_code=source_code,
            page_url=page_url,
            page_format="html",
            entry_id=document_id,
            document_id=document_id,
            title=title,
            published_at=published_at,
            official_url=urljoin(page_url, href),
            summary=None,
            raw_page_hash=raw_page_hash,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
            warnings=["pdf_endpoint_not_downloaded"],
        )
        for title, href, document_id in _iter_bop_albacete_announcements(text)
    ]
    return HTMLParseResult(raw_page_hash=raw_page_hash, records=records)


def parse_bop_alicante_response(
    raw_page: bytes | str,
    *,
    source_code: str,
    page_url: str,
    requested_date: str,
    discovered_at: str,
    monitor_run_id: str,
) -> HTMLParseResult:
    raw_bytes = _coerce_page_bytes(raw_page)
    raw_page_hash = hashlib.sha256(raw_bytes).hexdigest()
    try:
        payload = json.loads(raw_bytes.decode("utf-8", errors="replace"))
    except json.JSONDecodeError as exc:
        raise HTMLMonitorError("BOP_ALICANTE response is not valid JSON") from exc

    records = []
    for item in _bop_alicante_items(payload):
        document_id = _first_json_value(item, "edicto")
        title = _first_json_value(item, "extracto")
        official_url = _first_json_value(item, "ubicacion")
        n_bop = _first_json_value(item, "nBop")
        published_at = _ddmmyyyy_to_iso(_first_json_value(item, "fechaPublica")) or requested_date
        summary = (
            " - ".join(
                value
                for value in [
                    _first_json_value(item, "gndenom"),
                    _first_json_value(item, "ampliacion"),
                ]
                if value
            )
            or None
        )
        entry_id = "-".join(value for value in [n_bop, document_id] if value) or None
        records.append(
            _build_html_record(
                source_code=source_code,
                page_url=page_url,
                page_format="json-backed-html",
                entry_id=entry_id,
                document_id=document_id,
                title=title,
                published_at=published_at,
                official_url=official_url,
                summary=summary,
                raw_page_hash=raw_page_hash,
                discovered_at=discovered_at,
                monitor_run_id=monitor_run_id,
                warnings=["pdf_endpoint_not_downloaded"] if official_url else [],
            )
        )
    return HTMLParseResult(raw_page_hash=raw_page_hash, records=records)


def parse_bop_almeria_zkau_response(
    raw_page: bytes | str,
    *,
    source_code: str,
    page_url: str,
    requested_date: str,
    discovered_at: str,
    monitor_run_id: str,
) -> HTMLParseResult:
    raw_bytes = _coerce_page_bytes(raw_page)
    raw_page_hash = hashlib.sha256(raw_bytes).hexdigest()
    text = raw_bytes.decode("utf-8", errors="replace")
    records = []
    for item in _iter_bop_almeria_announcements(text):
        published_at = _ddmmyyyy_to_iso(item["published_date"])
        if published_at != requested_date:
            continue
        record = _build_html_record(
            source_code=source_code,
            page_url=page_url,
            page_format="zkau",
            entry_id=item["edict_number"],
            document_id=item["edict_number"],
            title=item["title"],
            published_at=published_at,
            official_url=None,
            summary=item["summary"],
            raw_page_hash=raw_page_hash,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
            warnings=["zkau_xhr_metadata_only", "pdf_endpoint_not_downloaded"],
        )
        if item["issue_number"]:
            record["issue_number"] = item["issue_number"]
        records.append(record)
    return HTMLParseResult(raw_page_hash=raw_page_hash, records=records)


def parse_bop_araba_alava_html(
    raw_page: bytes | str,
    *,
    source_code: str,
    page_url: str,
    requested_date: str,
    discovered_at: str,
    monitor_run_id: str,
) -> HTMLParseResult:
    raw_bytes = _coerce_page_bytes(raw_page)
    raw_page_hash = hashlib.sha256(raw_bytes).hexdigest()
    text = raw_bytes.decode("iso-8859-1", errors="replace")
    issue_number = _extract_bop_araba_issue_number(text)
    records = [
        _build_html_record(
            source_code=source_code,
            page_url=page_url,
            page_format="html",
            entry_id=entry_id,
            document_id=document_id,
            title=title,
            published_at=requested_date,
            official_url=urljoin(page_url, href),
            summary=summary,
            raw_page_hash=raw_page_hash,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
            warnings=[],
        )
        for title, href, entry_id, document_id, summary in _iter_bop_araba_announcements(text)
    ]
    for record in records:
        if issue_number:
            record["issue_number"] = issue_number
    return HTMLParseResult(raw_page_hash=raw_page_hash, records=records)


def parse_bop_avila_html(
    raw_page: bytes | str,
    *,
    source_code: str,
    page_url: str,
    requested_date: str,
    discovered_at: str,
    monitor_run_id: str,
) -> HTMLParseResult:
    raw_bytes = _coerce_page_bytes(raw_page)
    raw_page_hash = hashlib.sha256(raw_bytes).hexdigest()
    text = raw_bytes.decode("utf-8", errors="replace")
    published_at = _extract_bop_avila_publication_date(text) or requested_date
    records = [
        _build_html_record(
            source_code=source_code,
            page_url=page_url,
            page_format="html",
            entry_id=document_id,
            document_id=document_id,
            title=title,
            published_at=published_at,
            official_url=urljoin(page_url, href),
            summary=None,
            raw_page_hash=raw_page_hash,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
            warnings=["pdf_endpoint_not_downloaded"],
        )
        for title, href, document_id in _iter_bop_avila_announcements(text)
    ]
    return HTMLParseResult(raw_page_hash=raw_page_hash, records=records)


def parse_bop_barcelona_html(
    raw_page: bytes | str,
    *,
    source_code: str,
    page_url: str,
    requested_date: str,
    discovered_at: str,
    monitor_run_id: str,
) -> HTMLParseResult:
    raw_bytes = _coerce_page_bytes(raw_page)
    raw_page_hash = hashlib.sha256(raw_bytes).hexdigest()
    text = raw_bytes.decode("utf-8", errors="replace")
    records = [
        _build_html_record(
            source_code=source_code,
            page_url=page_url,
            page_format="html",
            entry_id=document_id,
            document_id=document_id,
            title=title,
            published_at=published_at or requested_date,
            official_url=urljoin(page_url, href),
            summary=None,
            raw_page_hash=raw_page_hash,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
            warnings=[],
        )
        for title, href, document_id, published_at in _iter_bop_barcelona_announcements(text)
    ]
    return HTMLParseResult(raw_page_hash=raw_page_hash, records=records)


def parse_bon_html(
    raw_page: bytes | str,
    *,
    source_code: str,
    page_url: str,
    requested_date: str,
    discovered_at: str,
    monitor_run_id: str,
) -> HTMLParseResult:
    raw_bytes = _coerce_page_bytes(raw_page)
    raw_page_hash = hashlib.sha256(raw_bytes).hexdigest()
    text = raw_bytes.decode("utf-8", errors="replace")
    published_at = _extract_bon_publication_date(text) or requested_date
    issue_number = _extract_bon_issue_number(text, page_url)
    records = []
    for item in _iter_bon_announcements(text, page_url):
        record = _build_html_record(
            source_code=source_code,
            page_url=page_url,
            page_format="html",
            entry_id=item["document_id"],
            document_id=item["document_id"],
            title=item["title"],
            published_at=published_at,
            official_url=item["official_url"],
            summary=item["summary"],
            raw_page_hash=raw_page_hash,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
            warnings=[],
        )
        if issue_number:
            record["issue_number"] = issue_number
        records.append(record)
    return HTMLParseResult(raw_page_hash=raw_page_hash, records=records)


def parse_bome_html(
    raw_page: bytes | str,
    *,
    source_code: str,
    page_url: str,
    requested_date: str,
    discovered_at: str,
    monitor_run_id: str,
) -> HTMLParseResult:
    raw_bytes = _coerce_page_bytes(raw_page)
    raw_page_hash = hashlib.sha256(raw_bytes).hexdigest()
    text = raw_bytes.decode("utf-8", errors="replace")
    published_at = _extract_bome_publication_date(text) or requested_date
    if published_at != requested_date:
        return HTMLParseResult(raw_page_hash=raw_page_hash, records=[])
    records = [
        _build_html_record(
            source_code=source_code,
            page_url=page_url,
            page_format="html",
            entry_id=document_id,
            document_id=document_id,
            title=_join_title_parts(section, title),
            published_at=published_at,
            official_url=official_url,
            summary=summary,
            raw_page_hash=raw_page_hash,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
            warnings=[],
        )
        for section, summary, title, document_id, official_url in _iter_bome_announcements(
            text, page_url
        )
    ]
    return HTMLParseResult(raw_page_hash=raw_page_hash, records=records)


def parse_bocce_html(
    raw_page: bytes | str,
    *,
    source_code: str,
    page_url: str,
    requested_date: str,
    discovered_at: str,
    monitor_run_id: str,
) -> HTMLParseResult:
    raw_bytes = _coerce_page_bytes(raw_page)
    raw_page_hash = hashlib.sha256(raw_bytes).hexdigest()
    text = raw_bytes.decode("utf-8", errors="replace")
    records = [
        _build_html_record(
            source_code=source_code,
            page_url=page_url,
            page_format="html",
            entry_id=issue_number,
            document_id=document_id,
            title=f"BOCCE {issue_number}",
            published_at=published_at,
            official_url=official_url,
            summary=None,
            raw_page_hash=raw_page_hash,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
            warnings=["pdf_endpoint_not_downloaded"],
        )
        for issue_number, document_id, published_at, official_url in _iter_bocce_issues(
            text, page_url, requested_date
        )
    ]
    return HTMLParseResult(raw_page_hash=raw_page_hash, records=records)


def parse_bop_bizkaia_detail_html(
    raw_page: bytes | str,
    *,
    source_code: str,
    page_url: str,
    requested_date: str,
    discovered_at: str,
    monitor_run_id: str,
) -> HTMLParseResult:
    raw_bytes = _coerce_page_bytes(raw_page)
    raw_page_hash = hashlib.sha256(raw_bytes).hexdigest()
    text = raw_bytes.decode("utf-8", errors="replace")
    published_at = _extract_bop_bizkaia_publication_date(page_url) or requested_date
    records = [
        _build_html_record(
            source_code=source_code,
            page_url=page_url,
            page_format="html",
            entry_id=document_id,
            document_id=document_id,
            title=title,
            published_at=published_at,
            official_url=urljoin(page_url, href),
            summary=None,
            raw_page_hash=raw_page_hash,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
            warnings=["pdf_endpoint_not_downloaded"],
        )
        for title, href, document_id in _iter_bop_bizkaia_announcements(text)
    ]
    return HTMLParseResult(raw_page_hash=raw_page_hash, records=records)


def parse_bop_burgos_html(
    raw_page: bytes | str,
    *,
    source_code: str,
    page_url: str,
    requested_date: str,
    discovered_at: str,
    monitor_run_id: str,
) -> HTMLParseResult:
    raw_bytes = _coerce_page_bytes(raw_page)
    raw_page_hash = hashlib.sha256(raw_bytes).hexdigest()
    text = raw_bytes.decode("utf-8", errors="replace")
    published_at = _extract_bop_burgos_publication_date(text) or requested_date
    if published_at != requested_date:
        return HTMLParseResult(raw_page_hash=raw_page_hash, records=[])
    issue_number = _extract_bop_burgos_issue_number(text)
    records = []
    for title, href, entry_id, document_id in _iter_bop_burgos_announcements(text):
        record = _build_html_record(
            source_code=source_code,
            page_url=page_url,
            page_format="html",
            entry_id=entry_id,
            document_id=document_id,
            title=title,
            published_at=published_at,
            official_url=urljoin(page_url, href),
            summary=None,
            raw_page_hash=raw_page_hash,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
            warnings=["pdf_endpoint_not_downloaded"],
        )
        if issue_number:
            record["issue_number"] = issue_number
        records.append(record)
    return HTMLParseResult(raw_page_hash=raw_page_hash, records=records)


def parse_bop_cadiz_html(
    raw_page: bytes | str,
    *,
    source_code: str,
    page_url: str,
    requested_date: str,
    discovered_at: str,
    monitor_run_id: str,
) -> HTMLParseResult:
    raw_bytes = _coerce_page_bytes(raw_page)
    raw_page_hash = hashlib.sha256(raw_bytes).hexdigest()
    text = raw_bytes.decode("utf-8", errors="replace")
    published_at = _extract_bop_cadiz_publication_date(text) or requested_date
    if published_at != requested_date:
        return HTMLParseResult(raw_page_hash=raw_page_hash, records=[])
    issue_number = _extract_bop_cadiz_issue_number(text)
    records = []
    for title, href, document_id, summary in _iter_bop_cadiz_announcements(text):
        record = _build_html_record(
            source_code=source_code,
            page_url=page_url,
            page_format="html",
            entry_id=document_id,
            document_id=document_id,
            title=title,
            published_at=published_at,
            official_url=urljoin(page_url, href),
            summary=summary,
            raw_page_hash=raw_page_hash,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
            warnings=["pdf_endpoint_not_downloaded"],
        )
        if issue_number:
            record["issue_number"] = issue_number
        records.append(record)
    return HTMLParseResult(raw_page_hash=raw_page_hash, records=records)


def parse_bop_castellon_html(
    raw_page: bytes | str,
    *,
    source_code: str,
    page_url: str,
    requested_date: str,
    discovered_at: str,
    monitor_run_id: str,
) -> HTMLParseResult:
    raw_bytes = _coerce_page_bytes(raw_page)
    raw_page_hash = hashlib.sha256(raw_bytes).hexdigest()
    text = raw_bytes.decode("utf-8", errors="replace")
    published_at = _extract_bop_castellon_publication_date(text) or requested_date
    records = [
        _build_html_record(
            source_code=source_code,
            page_url=page_url,
            page_format="html",
            entry_id=document_id,
            document_id=document_id,
            title=title,
            published_at=published_at,
            official_url=urljoin(page_url, href),
            summary=section,
            raw_page_hash=raw_page_hash,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
            warnings=["pdf_endpoint_not_downloaded"],
        )
        for title, href, document_id, section in _iter_bop_castellon_announcements(text)
    ]
    return HTMLParseResult(raw_page_hash=raw_page_hash, records=records)


def parse_bop_cordoba_html(
    raw_page: bytes | str,
    *,
    source_code: str,
    page_url: str,
    requested_date: str,
    discovered_at: str,
    monitor_run_id: str,
) -> HTMLParseResult:
    raw_bytes = _coerce_page_bytes(raw_page)
    raw_page_hash = hashlib.sha256(raw_bytes).hexdigest()
    text = raw_bytes.decode("utf-8", errors="replace")
    published_at = _extract_bop_cordoba_publication_date(page_url) or requested_date
    records = [
        _build_html_record(
            source_code=source_code,
            page_url=page_url,
            page_format="nextjs-rsc-html",
            entry_id=entry_id,
            document_id=document_id,
            title=title,
            published_at=published_at,
            official_url=urljoin(page_url, href),
            summary=issuer,
            raw_page_hash=raw_page_hash,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
            warnings=["pdf_endpoint_not_downloaded"],
        )
        for entry_id, title, href, document_id, issuer in _iter_bop_cordoba_announcements(text)
    ]
    return HTMLParseResult(raw_page_hash=raw_page_hash, records=records)


def parse_bop_ciudad_real_html(
    raw_page: bytes | str,
    *,
    source_code: str,
    page_url: str,
    requested_date: str,
    discovered_at: str,
    monitor_run_id: str,
) -> HTMLParseResult:
    raw_bytes = _coerce_page_bytes(raw_page)
    raw_page_hash = hashlib.sha256(raw_bytes).hexdigest()
    text = raw_bytes.decode("iso-8859-1", errors="replace")
    published_at = _extract_bop_ciudad_real_publication_date(text) or requested_date
    if published_at != requested_date:
        return HTMLParseResult(raw_page_hash=raw_page_hash, records=[])
    issue_number = _extract_bop_ciudad_real_issue_number(text)
    records = []
    for title, href, entry_id, document_id, summary in _iter_bop_ciudad_real_announcements(text):
        record = _build_html_record(
            source_code=source_code,
            page_url=page_url,
            page_format="html",
            entry_id=entry_id,
            document_id=document_id,
            title=title,
            published_at=published_at,
            official_url=urljoin(page_url, href),
            summary=summary,
            raw_page_hash=raw_page_hash,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
            warnings=["pdf_endpoint_not_downloaded"],
        )
        if issue_number:
            record["issue_number"] = issue_number
        records.append(record)
    return HTMLParseResult(raw_page_hash=raw_page_hash, records=records)


def parse_bop_cuenca_html(
    raw_page: bytes | str,
    *,
    source_code: str,
    page_url: str,
    requested_date: str,
    discovered_at: str,
    monitor_run_id: str,
) -> HTMLParseResult:
    raw_bytes = _coerce_page_bytes(raw_page)
    raw_page_hash = hashlib.sha256(raw_bytes).hexdigest()
    text = raw_bytes.decode("utf-8", errors="replace")
    records = []
    for title, href, document_id, published_at, issue_number in _iter_bop_cuenca_bulletins(
        text, requested_date
    ):
        record = _build_html_record(
            source_code=source_code,
            page_url=page_url,
            page_format="html",
            entry_id=document_id,
            document_id=document_id,
            title=title,
            published_at=published_at,
            official_url=urljoin(page_url, href),
            summary=None,
            raw_page_hash=raw_page_hash,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
            warnings=["bulletin_level_only"],
        )
        if issue_number:
            record["issue_number"] = issue_number
        records.append(record)
    return HTMLParseResult(raw_page_hash=raw_page_hash, records=records)


def parse_bop_gipuzkoa_html(
    raw_page: bytes | str,
    *,
    source_code: str,
    page_url: str,
    requested_date: str,
    discovered_at: str,
    monitor_run_id: str,
) -> HTMLParseResult:
    raw_bytes = _coerce_page_bytes(raw_page)
    raw_page_hash = hashlib.sha256(raw_bytes).hexdigest()
    text = raw_bytes.decode("iso-8859-15", errors="replace")
    published_at = _extract_bop_gipuzkoa_publication_date(text) or requested_date
    if published_at != requested_date:
        return HTMLParseResult(raw_page_hash=raw_page_hash, records=[])
    issue_number = _extract_bop_gipuzkoa_issue_number(text)
    records = []
    for title, href, document_id, summary in _iter_bop_gipuzkoa_announcements(text):
        record = _build_html_record(
            source_code=source_code,
            page_url=page_url,
            page_format="html",
            entry_id=document_id,
            document_id=document_id,
            title=title,
            published_at=published_at,
            official_url=urljoin(page_url, href),
            summary=summary,
            raw_page_hash=raw_page_hash,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
            warnings=[],
        )
        if issue_number:
            record["issue_number"] = issue_number
        records.append(record)
    return HTMLParseResult(raw_page_hash=raw_page_hash, records=records)


def parse_bop_girona_html(
    raw_page: bytes | str,
    *,
    source_code: str,
    page_url: str,
    requested_date: str,
    discovered_at: str,
    monitor_run_id: str,
) -> HTMLParseResult:
    raw_bytes = _coerce_page_bytes(raw_page)
    raw_page_hash = hashlib.sha256(raw_bytes).hexdigest()
    text = raw_bytes.decode("utf-8", errors="replace")
    published_at = _extract_bop_girona_publication_date(text)
    if published_at != requested_date:
        return HTMLParseResult(raw_page_hash=raw_page_hash, records=[])
    issue_number = _extract_bop_girona_issue_number(text)
    records = []
    for title, href, document_id, summary in _iter_bop_girona_announcements(text):
        record = _build_html_record(
            source_code=source_code,
            page_url=page_url,
            page_format="html",
            entry_id=document_id,
            document_id=document_id,
            title=title,
            published_at=published_at,
            official_url=urljoin(page_url, href),
            summary=summary,
            raw_page_hash=raw_page_hash,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
            warnings=["pdf_endpoint_not_downloaded"],
        )
        if issue_number:
            record["issue_number"] = issue_number
        records.append(record)
    return HTMLParseResult(raw_page_hash=raw_page_hash, records=records)


def parse_bop_huesca_html(
    raw_page: bytes | str,
    *,
    source_code: str,
    page_url: str,
    requested_date: str,
    discovered_at: str,
    monitor_run_id: str,
) -> HTMLParseResult:
    raw_bytes = _coerce_page_bytes(raw_page)
    raw_page_hash = hashlib.sha256(raw_bytes).hexdigest()
    text = raw_bytes.decode("iso-8859-1", errors="replace")
    published_at = _extract_bop_huesca_publication_date(text)
    if published_at != requested_date:
        return HTMLParseResult(raw_page_hash=raw_page_hash, records=[])
    issue_number = _extract_bop_huesca_issue_number(text)
    records = []
    for title, href, document_id, summary in _iter_bop_huesca_announcements(text):
        record = _build_html_record(
            source_code=source_code,
            page_url=page_url,
            page_format="html",
            entry_id=document_id,
            document_id=document_id,
            title=title,
            published_at=published_at,
            official_url=urljoin(page_url, href),
            summary=summary,
            raw_page_hash=raw_page_hash,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
            warnings=["pdf_endpoint_not_downloaded"],
        )
        if issue_number:
            record["issue_number"] = issue_number
        records.append(record)
    return HTMLParseResult(raw_page_hash=raw_page_hash, records=records)


def parse_bop_tarragona_html(
    raw_page: bytes | str,
    *,
    source_code: str,
    page_url: str,
    requested_date: str,
    discovered_at: str,
    monitor_run_id: str,
) -> HTMLParseResult:
    raw_bytes = _coerce_page_bytes(raw_page)
    raw_page_hash = hashlib.sha256(raw_bytes).hexdigest()
    text = raw_bytes.decode("utf-8", errors="replace")
    published_at = _first_datetime_value(text)
    if published_at != requested_date:
        return HTMLParseResult(raw_page_hash=raw_page_hash, records=[])
    records = []
    for title, href, document_id, summary in _iter_bop_tarragona_announcements(text):
        records.append(
            _build_html_record(
                source_code=source_code,
                page_url=page_url,
                page_format="html",
                entry_id=document_id,
                document_id=document_id,
                title=title,
                published_at=published_at,
                official_url=urljoin(page_url, href),
                summary=summary,
                raw_page_hash=raw_page_hash,
                discovered_at=discovered_at,
                monitor_run_id=monitor_run_id,
                warnings=[],
            )
        )
    return HTMLParseResult(raw_page_hash=raw_page_hash, records=records)


def parse_bop_las_palmas_html(
    raw_page: bytes | str,
    *,
    source_code: str,
    page_url: str,
    requested_date: str,
    discovered_at: str,
    monitor_run_id: str,
) -> HTMLParseResult:
    return _parse_legacy_island_bop_html(
        raw_page,
        source_code=source_code,
        page_url=page_url,
        requested_date=requested_date,
        discovered_at=discovered_at,
        monitor_run_id=monitor_run_id,
    )


def parse_bop_salamanca_html(
    raw_page: bytes | str,
    *,
    source_code: str,
    page_url: str,
    requested_date: str,
    discovered_at: str,
    monitor_run_id: str,
) -> HTMLParseResult:
    raw_bytes = _coerce_page_bytes(raw_page)
    raw_page_hash = hashlib.sha256(raw_bytes).hexdigest()
    text = raw_bytes.decode("utf-8", errors="replace")
    published_at = _extract_bop_salamanca_publication_date(text)
    if published_at != requested_date:
        return HTMLParseResult(raw_page_hash=raw_page_hash, records=[])
    pdf_url = _extract_bop_salamanca_bulletin_pdf_url(text, page_url, published_at)
    document_id = _document_id_from_filename(pdf_url) if pdf_url else None
    issue_number = _regex_value(r"BOP-SA-\d{8}-(\d+)", pdf_url or "")
    title = _extract_bop_salamanca_title(text) or (
        f"Boletin del dia {date.fromisoformat(published_at):%d/%m/%Y}"
    )
    record = _build_html_record(
        source_code=source_code,
        page_url=page_url,
        page_format="html",
        entry_id=document_id,
        document_id=document_id,
        title=title,
        published_at=published_at,
        official_url=pdf_url,
        summary="SUMARIO" if "SUMARIO" in _strip_tags(text).upper() else None,
        raw_page_hash=raw_page_hash,
        discovered_at=discovered_at,
        monitor_run_id=monitor_run_id,
        warnings=["pdf_endpoint_not_downloaded"] if pdf_url else [],
    )
    if issue_number:
        record["issue_number"] = issue_number
    return HTMLParseResult(raw_page_hash=raw_page_hash, records=[record])


def parse_bop_santa_cruz_tenerife_html(
    raw_page: bytes | str,
    *,
    source_code: str,
    page_url: str,
    requested_date: str,
    discovered_at: str,
    monitor_run_id: str,
) -> HTMLParseResult:
    return _parse_legacy_island_bop_html(
        raw_page,
        source_code=source_code,
        page_url=page_url,
        requested_date=requested_date,
        discovered_at=discovered_at,
        monitor_run_id=monitor_run_id,
    )


def parse_bop_teruel_html(
    raw_page: bytes | str,
    *,
    source_code: str,
    page_url: str,
    requested_date: str,
    discovered_at: str,
    monitor_run_id: str,
) -> HTMLParseResult:
    raw_bytes = _coerce_page_bytes(raw_page)
    raw_page_hash = hashlib.sha256(raw_bytes).hexdigest()
    text = raw_bytes.decode("utf-8", errors="replace")
    published_at = _extract_bop_teruel_publication_date(text)
    if published_at != requested_date:
        return HTMLParseResult(raw_page_hash=raw_page_hash, records=[])
    issue_number = _extract_bop_teruel_issue_number(text)
    official_url = _extract_bop_teruel_official_url(text, page_url)
    document_id = _regex_value(r"\bdia=(\d{8})\b", official_url or "")
    title = f"BOP del dia {_extract_bop_teruel_publication_label(text) or requested_date}"
    record = _build_html_record(
        source_code=source_code,
        page_url=page_url,
        page_format="html",
        entry_id=document_id,
        document_id=document_id,
        title=title,
        published_at=published_at,
        official_url=official_url,
        summary="BOP del dia",
        raw_page_hash=raw_page_hash,
        discovered_at=discovered_at,
        monitor_run_id=monitor_run_id,
        warnings=["pdf_endpoint_not_downloaded"] if official_url else [],
    )
    if issue_number:
        record["issue_number"] = issue_number
    return HTMLParseResult(raw_page_hash=raw_page_hash, records=[record])


def parse_bop_jaen_html(
    raw_page: bytes | str,
    *,
    source_code: str,
    page_url: str,
    requested_date: str,
    discovered_at: str,
    monitor_run_id: str,
) -> HTMLParseResult:
    raw_bytes = _coerce_page_bytes(raw_page)
    raw_page_hash = hashlib.sha256(raw_bytes).hexdigest()
    text = raw_bytes.decode("iso-8859-1", errors="replace")
    published_at = _extract_bop_jaen_publication_date(text, page_url) or requested_date
    issue_number = _extract_bop_jaen_issue_number(text)
    records = []
    for title, href, entry_id, document_id, summary in _iter_bop_jaen_announcements(text):
        record = _build_html_record(
            source_code=source_code,
            page_url=page_url,
            page_format="html",
            entry_id=entry_id,
            document_id=document_id,
            title=title,
            published_at=published_at,
            official_url=urljoin(page_url, href),
            summary=summary,
            raw_page_hash=raw_page_hash,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
            warnings=["pdf_endpoint_not_downloaded"],
        )
        if issue_number:
            record["issue_number"] = issue_number
        records.append(record)
    return HTMLParseResult(raw_page_hash=raw_page_hash, records=records)


def parse_bop_leon_html(
    raw_page: bytes | str,
    *,
    source_code: str,
    page_url: str,
    requested_date: str,
    discovered_at: str,
    monitor_run_id: str,
) -> HTMLParseResult:
    raw_bytes = _coerce_page_bytes(raw_page)
    raw_page_hash = hashlib.sha256(raw_bytes).hexdigest()
    text = raw_bytes.decode("utf-8", errors="replace")
    published_at = _ddmmyyyy_to_iso(_first_date_text(text)) or requested_date
    if published_at != requested_date:
        return HTMLParseResult(raw_page_hash=raw_page_hash, records=[])
    document_id = _first_bop_leon_document_id(text)
    title = _first_heading_text(text)
    if not document_id or not title:
        return HTMLParseResult(raw_page_hash=raw_page_hash, records=[])
    record = _build_html_record(
        source_code=source_code,
        page_url=page_url,
        page_format="html",
        entry_id=document_id,
        document_id=document_id,
        title=title,
        published_at=published_at,
        official_url=page_url,
        summary=None,
        raw_page_hash=raw_page_hash,
        discovered_at=discovered_at,
        monitor_run_id=monitor_run_id,
        warnings=["bulletin_level_only", "pdf_endpoint_not_downloaded"],
    )
    issue_number = _extract_bop_leon_issue_number(text)
    if issue_number:
        record["issue_number"] = issue_number
    return HTMLParseResult(raw_page_hash=raw_page_hash, records=[record])


def parse_bop_lleida_html(
    raw_page: bytes | str,
    *,
    source_code: str,
    page_url: str,
    requested_date: str,
    discovered_at: str,
    monitor_run_id: str,
) -> HTMLParseResult:
    raw_bytes = _coerce_page_bytes(raw_page)
    raw_page_hash = hashlib.sha256(raw_bytes).hexdigest()
    text = raw_bytes.decode("utf-8", errors="replace")
    published_at = _extract_bop_lleida_publication_date(text)
    if published_at != requested_date:
        return HTMLParseResult(raw_page_hash=raw_page_hash, records=[])
    issue_number = _extract_bop_lleida_issue_number(text)
    records = []
    for title, href, document_id, summary in _iter_bop_lleida_announcements(text):
        record = _build_html_record(
            source_code=source_code,
            page_url=page_url,
            page_format="html",
            entry_id=document_id,
            document_id=document_id,
            title=title,
            published_at=published_at,
            official_url=urljoin(page_url, href),
            summary=summary,
            raw_page_hash=raw_page_hash,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
            warnings=["pdf_endpoint_not_downloaded"],
        )
        if issue_number:
            record["issue_number"] = issue_number
        records.append(record)
    return HTMLParseResult(raw_page_hash=raw_page_hash, records=records)


def parse_bop_malaga_html(
    raw_page: bytes | str,
    *,
    source_code: str,
    page_url: str,
    requested_date: str,
    discovered_at: str,
    monitor_run_id: str,
) -> HTMLParseResult:
    raw_bytes = _coerce_page_bytes(raw_page)
    raw_page_hash = hashlib.sha256(raw_bytes).hexdigest()
    text = raw_bytes.decode("utf-8", errors="replace")
    published_at = _extract_bop_malaga_publication_date(text) or requested_date
    records = [
        _build_html_record(
            source_code=source_code,
            page_url=page_url,
            page_format="html",
            entry_id=document_id,
            document_id=document_id,
            title=title,
            published_at=published_at,
            official_url=urljoin(page_url, href),
            summary=None,
            raw_page_hash=raw_page_hash,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
            warnings=[],
        )
        for title, href, document_id in _iter_bop_malaga_announcements(text)
    ]
    return HTMLParseResult(raw_page_hash=raw_page_hash, records=records)


def parse_bop_pontevedra_html(
    raw_page: bytes | str,
    *,
    source_code: str,
    page_url: str,
    requested_date: str,
    discovered_at: str,
    monitor_run_id: str,
) -> HTMLParseResult:
    raw_bytes = _coerce_page_bytes(raw_page)
    raw_page_hash = hashlib.sha256(raw_bytes).hexdigest()
    text = raw_bytes.decode("utf-8", errors="replace")
    published_at = _extract_bop_pontevedra_publication_date(text) or requested_date
    records = [
        _build_html_record(
            source_code=source_code,
            page_url=page_url,
            page_format="html",
            entry_id=document_id,
            document_id=document_id,
            title=title,
            published_at=published_at,
            official_url=urljoin(page_url, href),
            summary=issuer,
            raw_page_hash=raw_page_hash,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
            warnings=["pdf_endpoint_not_downloaded"],
        )
        for title, href, document_id, issuer in _iter_bop_pontevedra_announcements(text)
    ]
    return HTMLParseResult(raw_page_hash=raw_page_hash, records=records)


def parse_bop_palencia_html(
    raw_page: bytes | str,
    *,
    source_code: str,
    page_url: str,
    requested_date: str,
    discovered_at: str,
    monitor_run_id: str,
) -> HTMLParseResult:
    raw_bytes = _coerce_page_bytes(raw_page)
    raw_page_hash = hashlib.sha256(raw_bytes).hexdigest()
    text = raw_bytes.decode("utf-8", errors="replace")
    records = []
    for title, detail_href, pdf_href, document_id in _iter_bop_palencia_bulletins(text):
        published_at = _bop_palencia_publication_date_from_id(document_id) or requested_date
        if published_at != requested_date:
            continue
        records.append(
            _build_html_record(
                source_code=source_code,
                page_url=page_url,
                page_format="html",
                entry_id=document_id,
                document_id=document_id,
                title=title,
                published_at=published_at,
                official_url=(
                    urljoin(page_url, detail_href) if detail_href else urljoin(page_url, pdf_href)
                ),
                summary=None,
                raw_page_hash=raw_page_hash,
                discovered_at=discovered_at,
                monitor_run_id=monitor_run_id,
                warnings=["pdf_endpoint_not_downloaded"] if pdf_href else [],
            )
        )
    return HTMLParseResult(raw_page_hash=raw_page_hash, records=records)


def parse_bop_segovia_html(
    raw_page: bytes | str,
    *,
    source_code: str,
    page_url: str,
    requested_date: str,
    discovered_at: str,
    monitor_run_id: str,
) -> HTMLParseResult:
    raw_bytes = _coerce_page_bytes(raw_page)
    raw_page_hash = hashlib.sha256(raw_bytes).hexdigest()
    text = raw_bytes.decode("utf-8", errors="replace")
    records = [
        _build_html_record(
            source_code=source_code,
            page_url=page_url,
            page_format="html",
            entry_id=document_id,
            document_id=document_id,
            title=title,
            published_at=published_at,
            official_url=urljoin(page_url, href),
            summary=None,
            raw_page_hash=raw_page_hash,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
            warnings=["bulletin_level_only"],
        )
        for title, href, document_id, published_at in _iter_bop_segovia_bulletins(
            text, requested_date
        )
    ]
    return HTMLParseResult(raw_page_hash=raw_page_hash, records=records)


def parse_bop_sevilla_html(
    raw_page: bytes | str,
    *,
    source_code: str,
    page_url: str,
    requested_date: str,
    discovered_at: str,
    monitor_run_id: str,
) -> HTMLParseResult:
    raw_bytes = _coerce_page_bytes(raw_page)
    raw_page_hash = hashlib.sha256(raw_bytes).hexdigest()
    text = raw_bytes.decode("utf-8", errors="replace")
    records = [
        _build_html_record(
            source_code=source_code,
            page_url=page_url,
            page_format="html",
            entry_id=document_id,
            document_id=document_id,
            title=title,
            published_at=published_at or requested_date,
            official_url=urljoin(page_url, href),
            summary=summary,
            raw_page_hash=raw_page_hash,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
            warnings=[],
        )
        for title, href, document_id, published_at, summary in _iter_bop_sevilla_announcements(text)
    ]
    return HTMLParseResult(raw_page_hash=raw_page_hash, records=records)


def parse_bop_soria_html(
    raw_page: bytes | str,
    *,
    source_code: str,
    page_url: str,
    requested_date: str,
    discovered_at: str,
    monitor_run_id: str,
) -> HTMLParseResult:
    raw_bytes = _coerce_page_bytes(raw_page)
    raw_page_hash = hashlib.sha256(raw_bytes).hexdigest()
    text = raw_bytes.decode("utf-8", errors="replace")
    published_at = _extract_bop_soria_publication_date(text) or requested_date
    records = [
        _build_html_record(
            source_code=source_code,
            page_url=page_url,
            page_format="html",
            entry_id=document_id,
            document_id=document_id,
            title=title,
            published_at=published_at,
            official_url=urljoin(page_url, href),
            summary=summary,
            raw_page_hash=raw_page_hash,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
            warnings=["pdf_endpoint_not_downloaded"],
        )
        for title, href, document_id, summary in _iter_bop_soria_announcements(text)
    ]
    return HTMLParseResult(raw_page_hash=raw_page_hash, records=records)


def parse_bop_toledo_html(
    raw_page: bytes | str,
    *,
    source_code: str,
    page_url: str,
    requested_date: str,
    discovered_at: str,
    monitor_run_id: str,
) -> HTMLParseResult:
    raw_bytes = _coerce_page_bytes(raw_page)
    raw_page_hash = hashlib.sha256(raw_bytes).hexdigest()
    text = raw_bytes.decode("utf-8", errors="replace")
    published_at = _extract_bop_toledo_publication_date(text) or requested_date
    if published_at != requested_date:
        return HTMLParseResult(raw_page_hash=raw_page_hash, records=[])
    issue_number = _extract_bop_toledo_issue_number(text)
    records = []
    for title, href, entry_id, document_id, summary in _iter_bop_toledo_announcements(text):
        record = _build_html_record(
            source_code=source_code,
            page_url=page_url,
            page_format="html",
            entry_id=entry_id,
            document_id=document_id,
            title=title,
            published_at=published_at,
            official_url=urljoin(page_url, href),
            summary=summary,
            raw_page_hash=raw_page_hash,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
            warnings=["pdf_endpoint_not_downloaded"],
        )
        if issue_number:
            record["issue_number"] = issue_number
        records.append(record)
    return HTMLParseResult(raw_page_hash=raw_page_hash, records=records)


def parse_bop_valencia_html(
    raw_page: bytes | str,
    *,
    source_code: str,
    page_url: str,
    requested_date: str,
    discovered_at: str,
    monitor_run_id: str,
) -> HTMLParseResult:
    raw_bytes = _coerce_page_bytes(raw_page)
    raw_page_hash = hashlib.sha256(raw_bytes).hexdigest()
    text = raw_bytes.decode("utf-8", errors="replace")
    records = [
        _build_html_record(
            source_code=source_code,
            page_url=page_url,
            page_format="html",
            entry_id=document_id,
            document_id=document_id,
            title=title,
            published_at=published_at or requested_date,
            official_url=None,
            summary=None,
            raw_page_hash=raw_page_hash,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
            warnings=[],
        )
        for title, document_id, published_at in _iter_bop_valencia_announcements(text)
    ]
    return HTMLParseResult(raw_page_hash=raw_page_hash, records=records)


def parse_bop_valladolid_html(
    raw_page: bytes | str,
    *,
    source_code: str,
    page_url: str,
    requested_date: str,
    discovered_at: str,
    monitor_run_id: str,
) -> HTMLParseResult:
    raw_bytes = _coerce_page_bytes(raw_page)
    raw_page_hash = hashlib.sha256(raw_bytes).hexdigest()
    text = raw_bytes.decode("utf-8", errors="replace")
    published_at = _extract_bop_valladolid_publication_date(text) or requested_date
    records = [
        _build_html_record(
            source_code=source_code,
            page_url=page_url,
            page_format="html",
            entry_id=document_id,
            document_id=document_id,
            title=title,
            published_at=published_at,
            official_url=urljoin(page_url, href),
            summary=issuer,
            raw_page_hash=raw_page_hash,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
            warnings=["pdf_endpoint_not_downloaded"],
        )
        for title, href, document_id, issuer in _iter_bop_valladolid_announcements(text)
    ]
    return HTMLParseResult(raw_page_hash=raw_page_hash, records=records)


def parse_bop_zaragoza_html(
    raw_page: bytes | str,
    *,
    source_code: str,
    page_url: str,
    requested_date: str,
    discovered_at: str,
    monitor_run_id: str,
) -> HTMLParseResult:
    raw_bytes = _coerce_page_bytes(raw_page)
    raw_page_hash = hashlib.sha256(raw_bytes).hexdigest()
    text = raw_bytes.decode("iso-8859-1", errors="replace")
    published_at = _ddmmyyyy_to_iso(_input_value(text, "fechaVista"))
    if published_at != requested_date:
        return HTMLParseResult(raw_page_hash=raw_page_hash, records=[])
    issue_number = _input_value(text, "numBop")
    fecha_pub = _input_value(text, "fechaPub")
    records = []
    for title, entry_id, summary in _iter_bop_zaragoza_announcements(text):
        record = _build_html_record(
            source_code=source_code,
            page_url=page_url,
            page_format="html",
            entry_id=entry_id,
            document_id=entry_id,
            title=title,
            published_at=published_at,
            official_url=_bop_zaragoza_detail_url(
                page_url,
                entry_id=entry_id,
                issue_number=issue_number,
                fecha_pub=fecha_pub,
            ),
            summary=summary,
            raw_page_hash=raw_page_hash,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
            warnings=[],
        )
        if issue_number:
            record["issue_number"] = issue_number
        records.append(record)
    return HTMLParseResult(raw_page_hash=raw_page_hash, records=records)


def parse_bop_zamora_html(
    raw_page: bytes | str,
    *,
    source_code: str,
    page_url: str,
    requested_date: str,
    discovered_at: str,
    monitor_run_id: str,
) -> HTMLParseResult:
    raw_bytes = _coerce_page_bytes(raw_page)
    raw_page_hash = hashlib.sha256(raw_bytes).hexdigest()
    text = raw_bytes.decode("utf-8", errors="replace")
    published_at = _extract_bop_zamora_publication_date(text) or requested_date
    if published_at != requested_date:
        return HTMLParseResult(raw_page_hash=raw_page_hash, records=[])
    issue_number = _extract_bop_zamora_issue_number(text)
    records = []
    for title, href, document_id, summary in _iter_bop_zamora_announcements(text):
        record = _build_html_record(
            source_code=source_code,
            page_url=page_url,
            page_format="html",
            entry_id=document_id,
            document_id=document_id,
            title=title,
            published_at=published_at,
            official_url=urljoin(page_url, href),
            summary=summary,
            raw_page_hash=raw_page_hash,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
            warnings=["pdf_endpoint_not_downloaded"],
        )
        if issue_number:
            record["issue_number"] = issue_number
        records.append(record)
    return HTMLParseResult(raw_page_hash=raw_page_hash, records=records)


def parse_bopa_html(
    raw_page: bytes | str,
    *,
    source_code: str,
    page_url: str,
    requested_date: str,
    discovered_at: str,
    monitor_run_id: str,
) -> HTMLParseResult:
    raw_bytes = _coerce_page_bytes(raw_page)
    raw_page_hash = hashlib.sha256(raw_bytes).hexdigest()
    text = raw_bytes.decode("utf-8", errors="replace")
    records = [
        _build_html_record(
            source_code=source_code,
            page_url=page_url,
            page_format="html",
            entry_id=document_id,
            document_id=document_id,
            title=title,
            published_at=requested_date,
            official_url=urljoin(page_url, href),
            summary=summary,
            raw_page_hash=raw_page_hash,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
            warnings=["pdf_endpoint_not_downloaded"] if has_pdf else [],
        )
        for title, href, document_id, summary, has_pdf in _iter_bopa_announcements(text)
    ]
    return HTMLParseResult(raw_page_hash=raw_page_hash, records=records)


def parse_docm_html(
    raw_page: bytes | str,
    *,
    source_code: str,
    page_url: str,
    requested_date: str,
    discovered_at: str,
    monitor_run_id: str,
) -> HTMLParseResult:
    raw_bytes = _coerce_page_bytes(raw_page)
    raw_page_hash = hashlib.sha256(raw_bytes).hexdigest()
    text = raw_bytes.decode("utf-8", errors="replace")
    published_at = _extract_docm_publication_date(text) or requested_date
    issue_number = _extract_docm_issue_number(text)
    records = []
    for item in _iter_docm_announcements(text):
        record = _build_html_record(
            source_code=source_code,
            page_url=page_url,
            page_format="html",
            entry_id=item["entry_id"],
            document_id=item["document_id"],
            title=item["title"],
            published_at=published_at,
            official_url=urljoin(page_url, item["href"]) if item["href"] else None,
            summary=item["summary"],
            raw_page_hash=raw_page_hash,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
            warnings=["pdf_endpoint_not_downloaded"] if item["has_pdf"] else [],
        )
        if issue_number:
            record["issue_number"] = issue_number
        if item["page"]:
            record["page"] = item["page"]
        records.append(record)
    return HTMLParseResult(raw_page_hash=raw_page_hash, records=records)


def write_html_jsonl(records: list[dict[str, Any]], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = "".join(
        f"{json.dumps(record, ensure_ascii=False, sort_keys=True)}\n" for record in records
    )
    output_path.write_text(payload, encoding="utf-8")
    return output_path


def fetch_html(url: str) -> bytes:
    try:
        with httpx.Client(
            follow_redirects=True,
            timeout=30.0,
            verify=_html_ssl_context(),
        ) as client:
            response = client.get(
                url,
                headers=_HTML_MONITOR_HEADERS,
            )
            response.raise_for_status()
            return response.content
    except httpx.HTTPError as exc:
        raise HTMLMonitorError(f"html monitor fetch failed for {url}: {exc}") from exc


def fetch_html_via_relay(relay_key: str, *, target_date: str) -> bytes:
    target_date = validate_html_monitor_date(target_date)
    if relay_key not in HTML_RELAY_TARGETS:
        raise HTMLMonitorError(f"relay target is not allowed: {relay_key}")
    base_url = os.environ.get(HTML_RELAY_BASE_URL_ENV, "").strip()
    if not base_url:
        raise HTMLMonitorError(f"{HTML_RELAY_BASE_URL_ENV} is required for relay-backed sources")
    separator = "&" if "?" in base_url else "?"
    relay_params = urlencode({"target": relay_key, "date": target_date, "raw": "1"})
    relay_url = f"{base_url}{separator}{relay_params}"
    headers = {}
    relay_secret = os.environ.get(HTML_RELAY_SECRET_ENV, "").strip()
    if relay_secret:
        headers["X-Relay-Secret"] = relay_secret
    try:
        with httpx.Client(follow_redirects=True, timeout=60.0) as client:
            response = client.get(relay_url, headers=headers)
            response.raise_for_status()
            upstream_status = response.headers.get("X-Relay-Upstream-Status")
            if upstream_status and not upstream_status.startswith("2"):
                raise HTMLMonitorError(
                    f"relay upstream returned status {upstream_status} for {relay_key}"
                )
            return response.content
    except httpx.HTTPError as exc:
        raise HTMLMonitorError(f"html relay fetch failed for {relay_key}: {exc}") from exc


def fetch_bop_almeria_zkau_response(url: str) -> bytes:
    try:
        with httpx.Client(
            follow_redirects=True,
            timeout=30.0,
            verify=_html_ssl_context(),
            headers=_HTML_MONITOR_HEADERS,
        ) as client:
            initial_response = client.get(url)
            initial_response.raise_for_status()
            initial_text = initial_response.text
            dtid = _extract_bop_almeria_dtid(initial_text)
            uuid = _extract_bop_almeria_public_window_uuid(initial_text)
            response = client.post(
                "https://app.dipalme.org/bop/zkau",
                data={
                    "dtid": dtid,
                    "cmd_0": "echo",
                    "opt_0": "i",
                    "uuid_0": uuid,
                    "data_0": '{"":["onAfterComposeNinguna"]}',
                },
                headers={
                    "Accept": "*/*",
                    "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
                    "Origin": "https://app.dipalme.org",
                    "Referer": str(initial_response.url),
                    "User-Agent": _HTML_MONITOR_HEADERS["User-Agent"],
                },
            )
            response.raise_for_status()
            if response.headers.get("ZK-Error"):
                raise HTMLMonitorError(
                    f"BOP_ALMERIA ZK endpoint returned ZK-Error={response.headers['ZK-Error']}"
                )
            return response.content
    except httpx.HTTPError as exc:
        raise HTMLMonitorError(f"BOP_ALMERIA ZK fetch failed for {url}: {exc}") from exc


def _html_ssl_context() -> ssl.SSLContext:
    try:
        import truststore
    except ImportError:
        context = ssl.create_default_context()
    else:
        context = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.load_verify_locations(cadata="\n".join(_HTML_EXTRA_CA_PEMS))
    return context


def _build_bop_a_coruna_record(
    *,
    announcement: BOPAcorunaAnnouncement,
    source_code: str,
    page_url: str,
    raw_page_hash: str,
    published_at: str,
    discovered_at: str,
    monitor_run_id: str,
) -> dict[str, Any]:
    return _build_html_record(
        source_code=source_code,
        page_url=page_url,
        page_format="html",
        entry_id=announcement.entry_id,
        document_id=announcement.document_id,
        title=announcement.title,
        published_at=published_at,
        official_url=announcement.official_url,
        summary=None,
        raw_page_hash=raw_page_hash,
        discovered_at=discovered_at,
        monitor_run_id=monitor_run_id,
        warnings=[],
    )


def _build_html_monitor_url(source_code: str, template_url: str, *, target_date: str) -> str:
    if source_code == "BOP_A_CORUNA":
        return build_bop_a_coruna_html_url(template_url, target_date=target_date)
    if source_code == "BOP_ALBACETE":
        return build_bop_albacete_html_url(template_url, target_date=target_date)
    if source_code == "BOP_ALICANTE":
        return build_bop_alicante_html_url(template_url, target_date=target_date)
    if source_code == "BOP_ALMERIA":
        return build_bop_almeria_html_url(template_url, target_date=target_date)
    if source_code == "BOP_ARABA_ALAVA":
        return build_bop_araba_alava_html_url(template_url, target_date=target_date)
    if source_code == "BOP_AVILA":
        return build_bop_avila_html_url(template_url, target_date=target_date)
    if source_code == "BOP_BARCELONA":
        return build_bop_barcelona_html_url(template_url, target_date=target_date)
    if source_code == "BON":
        return build_bon_html_url(template_url, target_date=target_date)
    if source_code == "BOME":
        return build_bome_html_url(template_url, target_date=target_date)
    if source_code == "BOCCE":
        return build_bocce_html_url(template_url, target_date=target_date)
    if source_code == "BOP_BIZKAIA":
        return build_bop_bizkaia_html_url(template_url, target_date=target_date)
    if source_code == "BOP_BURGOS":
        return build_bop_burgos_html_url(template_url, target_date=target_date)
    if source_code == "BOP_CADIZ":
        return build_bop_cadiz_html_url(template_url, target_date=target_date)
    if source_code == "BOP_CASTELLON":
        return build_bop_castellon_html_url(template_url, target_date=target_date)
    if source_code == "BOP_CORDOBA":
        return build_bop_cordoba_html_url(template_url, target_date=target_date)
    if source_code == "BOP_CIUDAD_REAL":
        return build_bop_ciudad_real_html_url(template_url, target_date=target_date)
    if source_code == "BOP_CUENCA":
        return build_bop_cuenca_html_url(template_url, target_date=target_date)
    if source_code == "BOP_GIRONA":
        return build_bop_girona_html_url(template_url, target_date=target_date)
    if source_code == "BOP_GIPUZKOA":
        return build_bop_gipuzkoa_html_url(template_url, target_date=target_date)
    if source_code == "BOP_GRANADA":
        return build_bop_granada_html_url(template_url, target_date=target_date)
    if source_code == "BOP_HUESCA":
        return build_bop_huesca_html_url(template_url, target_date=target_date)
    if source_code == "BOP_JAEN":
        return build_bop_jaen_html_url(template_url, target_date=target_date)
    if source_code == "BOP_LAS_PALMAS":
        return build_bop_las_palmas_html_url(template_url, target_date=target_date)
    if source_code == "BOP_LEON":
        return build_bop_leon_html_url(template_url, target_date=target_date)
    if source_code == "BOP_LLEIDA":
        return build_bop_lleida_html_url(template_url, target_date=target_date)
    if source_code == "BOP_MALAGA":
        return build_bop_malaga_html_url(template_url, target_date=target_date)
    if source_code == "BOP_PONTEVEDRA":
        return build_bop_pontevedra_html_url(template_url, target_date=target_date)
    if source_code == "BOP_PALENCIA":
        return build_bop_palencia_html_url(template_url, target_date=target_date)
    if source_code == "BOP_SALAMANCA":
        return build_bop_salamanca_html_url(template_url, target_date=target_date)
    if source_code == "BOP_SEGOVIA":
        return build_bop_segovia_html_url(template_url, target_date=target_date)
    if source_code == "BOP_SEVILLA":
        return build_bop_sevilla_html_url(template_url, target_date=target_date)
    if source_code == "BOP_SANTA_CRUZ_TENERIFE":
        return build_bop_santa_cruz_tenerife_html_url(template_url, target_date=target_date)
    if source_code == "BOP_SORIA":
        return build_bop_soria_html_url(template_url, target_date=target_date)
    if source_code == "BOP_TARRAGONA":
        return build_bop_tarragona_html_url(template_url, target_date=target_date)
    if source_code == "BOP_TERUEL":
        return build_bop_teruel_html_url(template_url, target_date=target_date)
    if source_code == "BOP_TOLEDO":
        return build_bop_toledo_html_url(template_url, target_date=target_date)
    if source_code == "BOP_VALENCIA":
        return build_bop_valencia_html_url(template_url, target_date=target_date)
    if source_code == "BOP_VALLADOLID":
        return build_bop_valladolid_html_url(template_url, target_date=target_date)
    if source_code == "BOP_ZARAGOZA":
        return build_bop_zaragoza_html_url(template_url, target_date=target_date)
    if source_code == "BOP_ZAMORA":
        return build_bop_zamora_html_url(template_url, target_date=target_date)
    if source_code == "BOPA":
        return build_bopa_html_url(template_url, target_date=target_date)
    if source_code == "DOCM":
        return build_docm_html_url(template_url, target_date=target_date)
    raise HTMLMonitorError(
        "html monitor currently supports BOP_A_CORUNA, BOP_ALBACETE, BOP_ALICANTE, BOP_ALMERIA, "
        "BOP_ARABA_ALAVA, BOP_AVILA, BOP_BARCELONA, BON, BOME, BOCCE, BOP_BIZKAIA, "
        "BOP_BURGOS, BOP_CADIZ, BOP_CASTELLON, BOP_CIUDAD_REAL, BOP_CORDOBA, BOP_CUENCA, "
        "BOP_GIRONA, BOP_GIPUZKOA, BOP_GRANADA, BOP_HUESCA, BOP_JAEN, BOP_LAS_PALMAS, "
        "BOP_LEON, BOP_LLEIDA, BOP_MALAGA, BOP_PALENCIA, BOP_SALAMANCA, BOP_SEGOVIA, BOP_SEVILLA, "
        "BOP_SANTA_CRUZ_TENERIFE, BOP_SORIA, BOP_TARRAGONA, BOP_PONTEVEDRA, "
        "BOP_TERUEL, BOP_TOLEDO, "
        "BOP_VALENCIA, BOP_VALLADOLID, BOP_ZARAGOZA, BOP_ZAMORA, BOPA, and DOCM only"
    )


def _parse_html_monitor_response(
    raw_page: bytes,
    *,
    source_code: str,
    page_url: str,
    target_date: str,
    discovered_at: str,
    monitor_run_id: str,
) -> HTMLParseResult:
    if source_code == "BOP_A_CORUNA":
        return parse_bop_a_coruna_html(
            raw_page,
            source_code=source_code,
            page_url=page_url,
            published_at=target_date,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
        )
    if source_code == "BOP_ALBACETE":
        return parse_bop_albacete_html(
            raw_page,
            source_code=source_code,
            page_url=page_url,
            requested_date=target_date,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
        )
    if source_code == "BOP_ALICANTE":
        return parse_bop_alicante_response(
            raw_page,
            source_code=source_code,
            page_url=page_url,
            requested_date=target_date,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
        )
    if source_code == "BOP_ALMERIA":
        return parse_bop_almeria_zkau_response(
            raw_page,
            source_code=source_code,
            page_url=page_url,
            requested_date=target_date,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
        )
    if source_code == "BOP_ARABA_ALAVA":
        return parse_bop_araba_alava_html(
            raw_page,
            source_code=source_code,
            page_url=page_url,
            requested_date=target_date,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
        )
    if source_code == "BOP_AVILA":
        return parse_bop_avila_html(
            raw_page,
            source_code=source_code,
            page_url=page_url,
            requested_date=target_date,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
        )
    if source_code == "BOP_BARCELONA":
        return parse_bop_barcelona_html(
            raw_page,
            source_code=source_code,
            page_url=page_url,
            requested_date=target_date,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
        )
    if source_code == "BON":
        return parse_bon_html(
            raw_page,
            source_code=source_code,
            page_url=page_url,
            requested_date=target_date,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
        )
    if source_code == "BOME":
        return parse_bome_html(
            raw_page,
            source_code=source_code,
            page_url=page_url,
            requested_date=target_date,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
        )
    if source_code == "BOCCE":
        return parse_bocce_html(
            raw_page,
            source_code=source_code,
            page_url=page_url,
            requested_date=target_date,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
        )
    if source_code == "BOP_BIZKAIA":
        return parse_bop_bizkaia_detail_html(
            raw_page,
            source_code=source_code,
            page_url=page_url,
            requested_date=target_date,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
        )
    if source_code == "BOP_BURGOS":
        return parse_bop_burgos_html(
            raw_page,
            source_code=source_code,
            page_url=page_url,
            requested_date=target_date,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
        )
    if source_code == "BOP_CADIZ":
        return parse_bop_cadiz_html(
            raw_page,
            source_code=source_code,
            page_url=page_url,
            requested_date=target_date,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
        )
    if source_code == "BOP_CASTELLON":
        return parse_bop_castellon_html(
            raw_page,
            source_code=source_code,
            page_url=page_url,
            requested_date=target_date,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
        )
    if source_code == "BOP_CORDOBA":
        return parse_bop_cordoba_html(
            raw_page,
            source_code=source_code,
            page_url=page_url,
            requested_date=target_date,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
        )
    if source_code == "BOP_CIUDAD_REAL":
        return parse_bop_ciudad_real_html(
            raw_page,
            source_code=source_code,
            page_url=page_url,
            requested_date=target_date,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
        )
    if source_code == "BOP_CUENCA":
        return parse_bop_cuenca_html(
            raw_page,
            source_code=source_code,
            page_url=page_url,
            requested_date=target_date,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
        )
    if source_code == "BOP_GIPUZKOA":
        return parse_bop_gipuzkoa_html(
            raw_page,
            source_code=source_code,
            page_url=page_url,
            requested_date=target_date,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
        )
    if source_code == "BOP_GIRONA":
        return parse_bop_girona_html(
            raw_page,
            source_code=source_code,
            page_url=page_url,
            requested_date=target_date,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
        )
    if source_code == "BOP_GRANADA":
        return parse_bop_sevilla_html(
            raw_page,
            source_code=source_code,
            page_url=page_url,
            requested_date=target_date,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
        )
    if source_code == "BOP_HUESCA":
        return parse_bop_huesca_html(
            raw_page,
            source_code=source_code,
            page_url=page_url,
            requested_date=target_date,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
        )
    if source_code == "BOP_JAEN":
        return parse_bop_jaen_html(
            raw_page,
            source_code=source_code,
            page_url=page_url,
            requested_date=target_date,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
        )
    if source_code == "BOP_LAS_PALMAS":
        return parse_bop_las_palmas_html(
            raw_page,
            source_code=source_code,
            page_url=page_url,
            requested_date=target_date,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
        )
    if source_code == "BOP_LEON":
        return parse_bop_leon_html(
            raw_page,
            source_code=source_code,
            page_url=page_url,
            requested_date=target_date,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
        )
    if source_code == "BOP_LLEIDA":
        return parse_bop_lleida_html(
            raw_page,
            source_code=source_code,
            page_url=page_url,
            requested_date=target_date,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
        )
    if source_code == "BOP_MALAGA":
        return parse_bop_malaga_html(
            raw_page,
            source_code=source_code,
            page_url=page_url,
            requested_date=target_date,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
        )
    if source_code == "BOP_PONTEVEDRA":
        return parse_bop_pontevedra_html(
            raw_page,
            source_code=source_code,
            page_url=page_url,
            requested_date=target_date,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
        )
    if source_code == "BOP_PALENCIA":
        return parse_bop_palencia_html(
            raw_page,
            source_code=source_code,
            page_url=page_url,
            requested_date=target_date,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
        )
    if source_code == "BOP_SALAMANCA":
        return parse_bop_salamanca_html(
            raw_page,
            source_code=source_code,
            page_url=page_url,
            requested_date=target_date,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
        )
    if source_code == "BOP_SEGOVIA":
        return parse_bop_segovia_html(
            raw_page,
            source_code=source_code,
            page_url=page_url,
            requested_date=target_date,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
        )
    if source_code == "BOP_SEVILLA":
        return parse_bop_sevilla_html(
            raw_page,
            source_code=source_code,
            page_url=page_url,
            requested_date=target_date,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
        )
    if source_code == "BOP_SANTA_CRUZ_TENERIFE":
        return parse_bop_santa_cruz_tenerife_html(
            raw_page,
            source_code=source_code,
            page_url=page_url,
            requested_date=target_date,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
        )
    if source_code == "BOP_SORIA":
        return parse_bop_soria_html(
            raw_page,
            source_code=source_code,
            page_url=page_url,
            requested_date=target_date,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
        )
    if source_code == "BOP_TARRAGONA":
        return parse_bop_tarragona_html(
            raw_page,
            source_code=source_code,
            page_url=page_url,
            requested_date=target_date,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
        )
    if source_code == "BOP_TERUEL":
        return parse_bop_teruel_html(
            raw_page,
            source_code=source_code,
            page_url=page_url,
            requested_date=target_date,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
        )
    if source_code == "BOP_TOLEDO":
        return parse_bop_toledo_html(
            raw_page,
            source_code=source_code,
            page_url=page_url,
            requested_date=target_date,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
        )
    if source_code == "BOP_VALENCIA":
        return parse_bop_valencia_html(
            raw_page,
            source_code=source_code,
            page_url=page_url,
            requested_date=target_date,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
        )
    if source_code == "BOP_VALLADOLID":
        return parse_bop_valladolid_html(
            raw_page,
            source_code=source_code,
            page_url=page_url,
            requested_date=target_date,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
        )
    if source_code == "BOP_ZARAGOZA":
        return parse_bop_zaragoza_html(
            raw_page,
            source_code=source_code,
            page_url=page_url,
            requested_date=target_date,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
        )
    if source_code == "BOP_ZAMORA":
        return parse_bop_zamora_html(
            raw_page,
            source_code=source_code,
            page_url=page_url,
            requested_date=target_date,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
        )
    if source_code == "BOPA":
        return parse_bopa_html(
            raw_page,
            source_code=source_code,
            page_url=page_url,
            requested_date=target_date,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
        )
    if source_code == "DOCM":
        return parse_docm_html(
            raw_page,
            source_code=source_code,
            page_url=page_url,
            requested_date=target_date,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
        )
    raise HTMLMonitorError(f"Unsupported html monitor source: {source_code}")


def _build_html_record(
    *,
    source_code: str,
    page_url: str,
    page_format: str,
    entry_id: str | None,
    document_id: str | None,
    title: str | None,
    published_at: str | None,
    official_url: str | None,
    summary: str | None,
    raw_page_hash: str,
    discovered_at: str,
    monitor_run_id: str,
    warnings: list[str],
) -> dict[str, Any]:
    normalized_warnings = list(warnings)
    if not official_url:
        normalized_warnings.append("entry_hash_fallback_missing_official_url")
    return {
        "source_code": source_code,
        "page_url": page_url,
        "page_format": page_format,
        "entry_id": entry_id,
        "document_id": document_id,
        "title": title,
        "published_at": published_at,
        "official_url": official_url,
        "summary": summary,
        "raw_page_hash": raw_page_hash,
        "entry_hash": build_html_entry_hash(
            source_code=source_code,
            published_at=published_at,
            official_url=official_url,
            document_id=document_id,
            title=title,
        ),
        "discovered_at": discovered_at,
        "monitor_run_id": monitor_run_id,
        "classification_status": "unclassified",
        "evidence_status": "not_evidence",
        "candidate_status": "not_candidate",
        "warnings": normalized_warnings,
    }


class _BOPAcorunaSummaryParser(HTMLParser):
    def __init__(self, page_url: str) -> None:
        super().__init__(convert_charrefs=True)
        self._page_url = page_url
        self._in_block = False
        self._block_depth = 0
        self._current_id: str | None = None
        self._current_href: str | None = None
        self._links: list[tuple[str, str]] = []
        self.announcements: list[BOPAcorunaAnnouncement] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "div" and _has_class(attributes.get("class"), "bloqueAnuncio"):
            self._in_block = True
            self._block_depth = 1
            self._current_id = attributes.get("id")
            self._links = []
            return
        if self._in_block:
            if tag == "div":
                self._block_depth += 1
            if tag == "a":
                self._current_href = attributes.get("href")

    def handle_data(self, data: str) -> None:
        if not self._in_block or not self._current_href:
            return
        text = _normalize_text(data)
        if text:
            self._links.append((self._current_href, text))

    def handle_endtag(self, tag: str) -> None:
        if not self._in_block:
            return
        if tag == "a":
            self._current_href = None
        if tag == "div":
            self._block_depth -= 1
            if self._block_depth <= 0:
                self._append_current_announcement()
                self._in_block = False
                self._current_id = None
                self._links = []

    def _append_current_announcement(self) -> None:
        document_id = _first_document_id(text for _, text in self._links)
        title = _first_title(self._links, document_id)
        official_url = _first_html_url(self._links, self._page_url)
        self.announcements.append(
            BOPAcorunaAnnouncement(
                entry_id=self._current_id,
                document_id=document_id,
                title=title,
                official_url=official_url,
            )
        )


def _first_document_id(values: object) -> str | None:
    for value in values:
        match = re.search(r"\b\d{4}/\d+\b", str(value))
        if match:
            return match.group(0)
    return None


def _first_title(links: list[tuple[str, str]], document_id: str | None) -> str | None:
    for _, text in links:
        normalized = _normalize_text(text)
        if not normalized or normalized == document_id:
            continue
        if normalized.upper() == "PDF" or normalized.upper().startswith("HTML"):
            continue
        return normalized
    return None


def _first_html_url(links: list[tuple[str, str]], page_url: str) -> str | None:
    for href, _ in links:
        if href.lower().split("?", 1)[0].endswith(".html"):
            return urljoin(page_url, href)
    return None


def _extract_bop_albacete_publication_date(text: str) -> str | None:
    match = re.search(r"Bolet[ií]n\s+N[uú]mero\s+\d+\s+\((\d{2}/\d{2}/\d{4})\)", text, re.I)
    if not match:
        return None
    return _ddmmyyyy_to_iso(match.group(1))


def _iter_bop_albacete_announcements(text: str) -> list[tuple[str, str, str]]:
    pattern = re.compile(
        r'<div[^>]*class="[^"]*\bcol-12\b(?![^"]*\btext-end\b)[^"]*"[^>]*>'
        r"\s*(?P<title>[^<][^<]*?)\s*</div>\s*"
        r'<div[^>]*class="[^"]*\bcol-12\b[^"]*\btext-end\b[^"]*"[^>]*>\s*'
        r'<a[^>]+href="(?P<href>[^"]+)"[^>]*>.*?</a>',
        re.I | re.S,
    )
    announcements = []
    for match in pattern.finditer(text):
        title = _normalize_text(match.group("title"))
        href = html.unescape(match.group("href"))
        document_id = _url_last_number(href)
        if title and href and document_id:
            announcements.append((title, href, document_id))
    return announcements


def _iter_bop_barcelona_announcements(text: str) -> list[tuple[str, str, str, str | None]]:
    block_pattern = re.compile(
        r"<article\b[^>]*>(?P<article>.*?)</article>"
        r'|<div[^>]+class="[^"]*\bcard-body\b[^"]*"[^>]*>(?P<card>.*?)</div>\s*</div>',
        re.I | re.S,
    )
    announcements = []
    for block in block_pattern.finditer(text):
        body = block.group("article") or block.group("card") or ""
        link = re.search(
            r'<a[^>]+href="(?P<href>[^"]+)"[^>]*>(?P<title>.*?)</a>',
            body,
            re.I | re.S,
        )
        if not link:
            continue
        href = html.unescape(link.group("href"))
        title = _normalize_text(_strip_tags(link.group("title")))
        document_id = _first_value([_first_register_number(body), _url_last_number(href)])
        published_at = _first_value(
            [_first_datetime_value(body), _ddmmyyyy_to_iso(_first_date_text(body))]
        )
        if title and href and document_id:
            announcements.append((title, href, document_id, published_at))
    return announcements


def _extract_bon_issue_url(text: str, page_url: str, target_date: str) -> str:
    target_date = validate_html_monitor_date(target_date)
    match = re.search(r"var\s+boletines\s*=\s*(?P<payload>\{.*?\});", text, re.I | re.S)
    if match:
        try:
            payload = json.loads(match.group("payload"))
        except json.JSONDecodeError:
            payload = {}
        items = payload.get(target_date, [])
        if isinstance(items, list) and items:
            issue_number = None
            if isinstance(items[0], dict):
                issue_number = _string_number(items[0].get("numero"))
            if issue_number:
                return urljoin(
                    page_url,
                    f"/es/boletin/-/sumario/{target_date[:4]}/{issue_number}",
                )
    date_pattern = _bon_long_date_pattern(target_date)
    for link in re.finditer(
        r'<a[^>]+href="(?P<href>[^"]*/es/boletin/-/sumario/\d{4}/\d+)"[^>]*>',
        text,
        re.I,
    ):
        window = text[link.start() : min(len(text), link.end() + 400)]
        if date_pattern.search(_strip_tags(window)):
            return urljoin(page_url, html.unescape(link.group("href")))
    raise HTMLMonitorError("BON calendar page did not expose issue number for requested date")


def _extract_bon_publication_date(text: str) -> str | None:
    match = re.search(
        r"BOLET[IÍ]N\s+N[ºo]\s+\d+\s*-\s*(\d{1,2})\s+de\s+([a-záéíóú]+)\s+de\s+(\d{4})",
        _strip_tags(text),
        re.I,
    )
    if not match:
        return None
    month = _SPANISH_MONTHS.get(match.group(2).lower())
    if not month:
        return None
    return date(int(match.group(3)), month, int(match.group(1))).isoformat()


def _extract_bon_issue_number(text: str, page_url: str) -> str | None:
    url_match = re.search(r"/sumario/\d{4}/(\d+)", page_url)
    if url_match:
        return url_match.group(1)
    text_match = re.search(r"BOLET[IÍ]N\s+N[ºo]\s+(\d+)", _strip_tags(text), re.I)
    return text_match.group(1) if text_match else None


def _iter_bon_announcements(text: str, page_url: str) -> list[dict[str, str | None]]:
    paragraph_pattern = re.compile(r"<p\b(?P<attrs>[^>]*)>(?P<body>.*?)</p>", re.I | re.S)
    context: dict[str, str | None] = {
        "ambito": None,
        "seccion": None,
        "subseccion": None,
        "denominacion": None,
    }
    announcements: list[dict[str, str | None]] = []
    seen: set[str] = set()
    for paragraph in paragraph_pattern.finditer(text):
        attrs = paragraph.group("attrs")
        body = paragraph.group("body")
        class_match = re.search(r'class="(?P<class>[^"]*)"', attrs, re.I)
        classes = class_match.group("class") if class_match else ""
        paragraph_text = _normalize_text(_strip_tags(body))
        if _has_class(classes, "b-ambito"):
            context = {
                "ambito": paragraph_text,
                "seccion": None,
                "subseccion": None,
                "denominacion": None,
            }
            continue
        if _has_class(classes, "b-seccion"):
            context["seccion"] = paragraph_text
            context["subseccion"] = None
            context["denominacion"] = None
            continue
        if _has_class(classes, "b-subseccion"):
            context["subseccion"] = paragraph_text
            context["denominacion"] = None
            continue
        if _has_class(classes, "b-denominacion"):
            context["denominacion"] = paragraph_text
            continue
        link = re.search(
            r'<a[^>]+href="(?P<href>[^"]*/es/anuncio/-/texto/(?P<year>\d{4})/'
            r'(?P<issue>\d+)/(?P<ordinal>\d+))"(?P<attrs>[^>]*)>(?P<title>.*?)</a>',
            body,
            re.I | re.S,
        )
        if not link:
            continue
        href = html.unescape(link.group("href"))
        if href in seen:
            continue
        seen.add(href)
        title_attr = re.search(r'title="(?P<title>[^"]+)"', link.group("attrs"), re.I | re.S)
        title = _first_value(
            [
                _normalize_text(title_attr.group("title")) if title_attr else None,
                _normalize_text(_strip_tags(link.group("title"))),
            ]
        )
        document_id = f"{link.group('year')}.{link.group('issue')}.{link.group('ordinal')}"
        announcements.append(
            {
                "document_id": document_id,
                "title": title,
                "official_url": urljoin(page_url, href),
                "summary": _join_title_parts(
                    context["ambito"],
                    context["seccion"],
                    context["subseccion"],
                    context["denominacion"],
                ),
            }
        )
    return announcements


def _bon_long_date_pattern(target_date: str) -> re.Pattern[str]:
    parsed = date.fromisoformat(validate_html_monitor_date(target_date))
    month_names = [name for name, number in _SPANISH_MONTHS.items() if number == parsed.month]
    month_pattern = "|".join(re.escape(name) for name in month_names)
    return re.compile(rf"\b{parsed.day}\s+de\s+(?:{month_pattern})\s+de\s+{parsed.year}\b", re.I)


def _extract_bome_issue_url(text: str, page_url: str, target_date: str) -> str:
    date_pattern = _long_date_pattern(target_date)
    for link in re.finditer(
        r'<a[^>]+href=["\'](?P<href>[^"\']*/bome/BOME-B-\d{4}-\d+[^"\']*)["\'][^>]*>'
        r"(?P<label>.*?)</a>",
        text,
        re.I | re.S,
    ):
        label = _normalize_text(_strip_tags(link.group("label")))
        if date_pattern.search(label):
            return urljoin(page_url, html.unescape(link.group("href")))
    raise HTMLMonitorError("BOME landing page did not expose issue URL for requested date")


def _extract_bome_publication_date(text: str) -> str | None:
    plain = _strip_tags(text)
    match = re.search(
        r"BOME\s+N[Âºo]\s+\d+\s+del\s+(?:lunes|martes|mi[eÃ©]rcoles|jueves|viernes|s[aÃ¡]bado|domingo),?\s+"
        r"(?P<date>\d{1,2}\s+de\s+[A-Za-zÃÃ‰ÃÃ“ÃšÃ¡Ã©Ã­Ã³ÃºÃ±Ã‘]+\s+de\s+\d{4})",
        plain,
        re.I,
    )
    return _long_spanish_date_to_iso(match.group("date")) if match else None


def _iter_bome_announcements(
    text: str, page_url: str
) -> list[tuple[str | None, str | None, str, str, str]]:
    section_items = [
        (match.start(), _normalize_text(_strip_tags(match.group("heading"))))
        for match in re.finditer(
            r"<h[3-4]\b[^>]*>(?P<heading>.*?)</h[3-4]>",
            text,
            re.I | re.S,
        )
    ]
    block_pattern = re.compile(
        r'<li\b[^>]*>\s*<h5\b[^>]*>(?P<summary>.*?)</h5>(?P<body>.*?)</li>',
        re.I | re.S,
    )
    announcements: list[tuple[str | None, str | None, str, str, str]] = []
    for block in block_pattern.finditer(text):
        summary_text = _normalize_text(_strip_tags(block.group("summary")))
        cve_match = re.search(r"\b(BOME-[A-Z]-\d{4}-\d+)\b", summary_text, re.I)
        hrefs = [
            html.unescape(match.group("href"))
            for match in re.finditer(
                r'<a[^>]+href=["\'](?P<href>[^"\']*(?:/articulo/|BOME-[A-Z]-\d{4}-\d+)[^"\']*)["\']',
                block.group("body"),
                re.I | re.S,
            )
        ]
        title_match = re.search(
            r"<blockquote\b[^>]*>(?P<title>.*?)</blockquote>"
            r"|<p\b[^>]*>(?P<paragraph>.*?)</p>",
            block.group("body"),
            re.I | re.S,
        )
        document_id = cve_match.group(1).upper() if cve_match else None
        title = (
            _normalize_text(
                _strip_tags(title_match.group("title") or title_match.group("paragraph"))
            )
            if title_match
            else None
        )
        href = _first_value(
            [
                next((candidate for candidate in hrefs if "/articulo/" in candidate), None),
                next((candidate for candidate in hrefs if "/descargar/" not in candidate), None),
                hrefs[0] if hrefs else None,
            ]
        )
        if document_id and title and href:
            summary = re.sub(r"\s*\(CVE:\s*[^)]+\)", "", summary_text, flags=re.I).strip()
            section = _last_positioned_value(section_items, block.start())
            announcements.append((section, summary, title, document_id, urljoin(page_url, href)))
    return announcements


def _iter_bocce_issues(
    text: str, page_url: str, requested_date: str
) -> list[tuple[str, str, str, str]]:
    requested = date.fromisoformat(validate_html_monitor_date(requested_date))
    requested_token = requested.strftime("%d-%m-%Y")
    pattern = re.compile(
        r'<a[^>]+href=["\'](?P<href>[^"\']+)["\'][^>]*>\s*'
        r"(?P<label>BOCCE_(?!Extra)(?P<issue>\d+)_(?P<date>\d{2}-\d{2}-\d{4}))\s*</a>",
        re.I | re.S,
    )
    issues: list[tuple[str, str, str, str]] = []
    seen: set[str] = set()
    for match in pattern.finditer(text):
        if match.group("date") != requested_token:
            continue
        document_id = _normalize_text(match.group("label"))
        if document_id in seen:
            continue
        seen.add(document_id)
        published_at = _ddmmyyyy_to_iso(match.group("date").replace("-", "/"))
        if published_at:
            issues.append(
                (
                    match.group("issue"),
                    document_id,
                    published_at,
                    urljoin(page_url, html.unescape(match.group("href"))),
                )
            )
    return issues


def _string_number(value: object | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text if text.isdigit() else None


def _extract_bop_bizkaia_latest_detail_url(text: str, page_url: str) -> str:
    for tag in re.finditer(r"<a\b(?P<attrs>[^>]+)>", text, re.I | re.S):
        attrs = tag.group("attrs")
        if "last-boletin-detail" not in attrs and "_IYBIWBCC_bdate" not in attrs:
            continue
        href_match = re.search(r'href="(?P<href>[^"]+)"', attrs, re.I)
        if not href_match:
            continue
        href = html.unescape(href_match.group("href"))
        if "_IYBIWBCC_bdate" in href:
            return urljoin(page_url, href)
    raise HTMLMonitorError("BOP_BIZKAIA landing page did not expose latest bulletin detail URL")


def _iter_bop_bizkaia_announcements(text: str) -> list[tuple[str, str, str]]:
    row_pattern = re.compile(
        r'<li[^>]+class="[^"]*\brow\b[^"]*"[^>]*>(?P<body>.*?)</li>',
        re.I | re.S,
    )
    announcements = []
    for row in row_pattern.finditer(text):
        body = row.group("body")
        link = re.search(
            r'<a[^>]+href="(?P<href>[^"]+\.pdf)"[^>]*class="[^"]*\bbtn_bobresult\b[^"]*"',
            body,
            re.I | re.S,
        )
        if not link:
            continue
        href = html.unescape(link.group("href"))
        document_id = _bop_bizkaia_document_id_from_url(href)
        summary = _first_id_block_text(body, "emisorResumen")
        heading = _first_heading_text(body)
        title = _join_title_parts(heading, summary)
        if title and href and document_id:
            announcements.append((title, href, document_id))
    return announcements


def _extract_bop_castellon_publication_date(text: str) -> str | None:
    match = re.search(r"Sumario\s+BOP\s+N[ºo]\s+\d+.*?(\d{2}/\d{2}/\d{4})", text, re.I | re.S)
    if match:
        return _ddmmyyyy_to_iso(match.group(1))
    return None


def _iter_bop_castellon_announcements(text: str) -> list[tuple[str, str, str, str | None]]:
    pattern = re.compile(
        r'(?P<section><span[^>]+class="titulo2"[^>]*>.*?</span>)?'
        r"(?P<prefix>.*?)"
        r'<a[^>]+href="(?P<href>[^"]*descargarAnuncio\?idAnuncio=(?P<id>\d+)[^"]*)"[^>]*>'
        r".*?</a>.*?"
        r'<span[^>]+class="titulo4"[^>]*>(?P<title>.*?)</span>',
        re.I | re.S,
    )
    announcements = []
    last_section: str | None = None
    for match in pattern.finditer(text):
        section_text = _normalize_text(_strip_tags(match.group("section") or ""))
        if section_text:
            last_section = section_text
        href = html.unescape(match.group("href"))
        document_id = _normalize_text(match.group("id"))
        title = _normalize_text(_strip_tags(match.group("title")))
        if title and href and document_id:
            announcements.append((title, href, document_id, last_section))
    return announcements


def _extract_bop_bizkaia_publication_date(page_url: str) -> str | None:
    match = re.search(r"_IYBIWBCC_bdate=(\d{8})", page_url)
    if not match:
        return None
    return _yyyymmdd_to_iso(match.group(1))


def _extract_bop_burgos_detail_url(text: str, page_url: str) -> str:
    for match in re.finditer(r'href="(?P<href>/bopbur-\d{4}-\d+)"', text, re.I):
        return urljoin(page_url, html.unescape(match.group("href")))
    raise HTMLMonitorError("BOP_BURGOS date page did not expose an issue detail URL")


def _extract_bop_burgos_publication_date(text: str) -> str | None:
    title_date = _first_class_block_text(text, "title-date")
    return _long_spanish_date_to_iso(title_date or _strip_tags(text))


def _extract_bop_burgos_issue_number(text: str) -> str | None:
    title_number = _first_class_block_text(text, "title-number") or _strip_tags(text)
    match = re.search(r"\b(?:n[uú]m\.?|num\.?)\s*(\d+)\b", title_number, re.I)
    return match.group(1) if match else None


def _iter_bop_burgos_announcements(text: str) -> list[tuple[str, str, str, str]]:
    pattern = re.compile(
        r'<li[^>]+id="bopbur-anuncio-(?P<entry_id>\d+)"[^>]*'
        r'class="[^"]*\bbopbur-anuncio\b[^"]*"[^>]*>(?P<body>.*?)(?=<li[^>]+id="bopbur-anuncio-|</li>|</ul>)',
        re.I | re.S,
    )
    announcements = []
    for match in pattern.finditer(text):
        body = match.group("body")
        link = re.search(
            r'<a[^>]+href="(?P<href>[^"]+\.pdf)"[^>]*>(?P<link_text>.*?)</a>',
            body,
            re.I | re.S,
        )
        title_match = re.search(
            r"<p\b(?![^>]*bopbur-filefield-file)[^>]*>(?P<title>.*?)</p>",
            body,
            re.I | re.S,
        )
        document_id_match = re.search(r"\bBOPBUR-\d{4}-\d+\b", _strip_tags(body), re.I)
        title = _normalize_text(_strip_tags(title_match.group("title"))) if title_match else None
        if link and title and document_id_match:
            announcements.append(
                (
                    title,
                    html.unescape(link.group("href")),
                    match.group("entry_id"),
                    document_id_match.group(0).upper(),
                )
            )
    return announcements


def _extract_bop_cadiz_latest_detail_url(text: str, page_url: str) -> str:
    match = re.search(r'href="(?P<href>/boletin/Boletin-numero-\d+-del-ano-\d+)"', text, re.I)
    if match:
        return urljoin(page_url, html.unescape(match.group("href")))
    return ""


def _extract_bop_cadiz_publication_date(text: str) -> str | None:
    match = re.search(
        r"\b(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+([A-Z][a-z]{2})\s+(\d{1,2}).*?(\d{4})\b",
        _strip_tags(text),
        re.I,
    )
    if not match:
        return None
    month = {
        "jan": 1,
        "feb": 2,
        "mar": 3,
        "apr": 4,
        "may": 5,
        "jun": 6,
        "jul": 7,
        "aug": 8,
        "sep": 9,
        "oct": 10,
        "nov": 11,
        "dec": 12,
    }.get(match.group(1).lower())
    return date(int(match.group(3)), month, int(match.group(2))).isoformat() if month else None


def _extract_bop_cadiz_issue_number(text: str) -> str | None:
    match = re.search(r"Bolet[ií]n\s+n[uú]mero\s+(\d+)", _strip_tags(text), re.I)
    if not match:
        match = re.search(r"Boletin\s+numero\s+(\d+)", _strip_tags(text), re.I)
    return match.group(1) if match else None


def _iter_bop_cadiz_announcements(text: str) -> list[tuple[str, str, str, str | None]]:
    token_pattern = re.compile(
        r"<h3>(?P<section>.*?)</h3>|"
        r'<p>\s*<a[^>]+href="(?P<href>[^"]+\.pdf#page=\d+)"[^>]*>(?P<body>.*?)</a>\s*</p>',
        re.I | re.S,
    )
    section = None
    announcements = []
    for token in token_pattern.finditer(text):
        if token.group("section") is not None:
            section = _normalize_text(_strip_tags(token.group("section")))
            continue
        body = token.group("body") or ""
        strong = re.search(r"<strong>(?P<body>.*?)</strong>", body, re.I | re.S)
        if not strong:
            continue
        header = _normalize_text(_strip_tags(strong.group("body")))
        match = re.match(r"(?P<id>[\d.]+)\.-\s*(?P<issuer>.*)", header)
        if not match:
            continue
        title = _normalize_text(_strip_tags(body.replace(strong.group(0), "")))
        if title:
            announcements.append(
                (
                    title,
                    html.unescape(token.group("href")),
                    match.group("id"),
                    _join_title_parts(section, match.group("issuer")),
                )
            )
    return announcements


def _iter_bop_malaga_announcements(text: str) -> list[tuple[str, str, str]]:
    article_pattern = re.compile(r"<article\b[^>]*>(?P<body>.*?)</article>", re.I | re.S)
    announcements = []
    for article in article_pattern.finditer(text):
        body = article.group("body")
        link = re.search(
            r'<a[^>]+href="(?P<href>[^"]+)"[^>]*>\s*Ver\s+edicto\s+(?P<id>[^<]+)</a>',
            body,
            re.I | re.S,
        )
        if not link:
            continue
        title = _first_value(
            [
                _first_class_block_text(body, "vista_sumario"),
                _first_class_block_text(body, "vista_edicto"),
                _first_heading_text(body),
            ]
        )
        href = html.unescape(link.group("href"))
        document_id = _normalize_text(link.group("id"))
        if title and href and document_id:
            announcements.append((title, href, document_id))
    return announcements


def _extract_bop_sevilla_latest_detail_url(text: str, page_url: str) -> str:
    for tag in re.finditer(r"<a\b(?P<attrs>[^>]+)>", text, re.I | re.S):
        attrs = tag.group("attrs")
        href_match = re.search(r'href="(?P<href>[^"]+)"', attrs, re.I)
        if not href_match:
            continue
        href = html.unescape(href_match.group("href"))
        if "/publica/consulta-de-bops/buscador/BOP-" in href:
            return urljoin(page_url, href)
    raise HTMLMonitorError("BOP_SEVILLA landing page did not expose latest bulletin detail URL")


def _iter_bop_sevilla_announcements(
    text: str,
) -> list[tuple[str, str, str, str | None, str | None]]:
    item_pattern = re.compile(
        r'<li[^>]+class="[^"]*\belementoListado\b[^"]*"[^>]*>(?P<body>.*?)</li>',
        re.I | re.S,
    )
    announcements = []
    for item in item_pattern.finditer(text):
        body = item.group("body")
        link = re.search(
            r'<a[^>]+href="(?P<href>[^"]+)"[^>]*(?:title="(?P<title_attr>[^"]*)")?[^>]*>'
            r"\s*Ir\s+al\s+detalle\s*</a>",
            body,
            re.I | re.S,
        )
        if not link:
            continue
        title = _first_value(
            [
                _normalize_text(link.group("title_attr")),
                _first_heading_text(body),
            ]
        )
        href = html.unescape(link.group("href"))
        document_id = _first_bop_sevilla_document_id(body)
        published_at = _ddmmyyyy_to_iso(_first_date_text(body))
        summary = _first_class_block_text(body, "campo_1")
        if title and href and document_id:
            announcements.append((title, href, document_id, published_at, summary))
    return announcements


def _extract_bop_soria_detail_url(text: str, page_url: str) -> str:
    for tag in re.finditer(r"<a\b(?P<attrs>[^>]+)>", text, re.I | re.S):
        attrs = tag.group("attrs")
        href_match = re.search(r'href="(?P<href>[^"]+)"', attrs, re.I)
        if not href_match:
            continue
        href = html.unescape(href_match.group("href"))
        if "/mod.boloficial/mem.detalle/" in href:
            return urljoin(page_url, href)
    raise HTMLMonitorError("BOP_SORIA date page did not expose bulletin detail URL")


def _extract_bop_soria_publication_date(text: str) -> str | None:
    match = re.search(
        r"\b(\d{1,2})\s+de\s+([a-záéíóú]+)\s+de\s+(\d{4})\b",
        _strip_tags(text),
        re.I,
    )
    if not match:
        return None
    month = _SPANISH_MONTHS.get(match.group(2).lower())
    if not month:
        return None
    return date(int(match.group(3)), month, int(match.group(1))).isoformat()


def _iter_bop_soria_announcements(text: str) -> list[tuple[str, str, str, str | None]]:
    item_pattern = re.compile(r"<li>(?P<body>.*?)</li>", re.I | re.S)
    context: list[str | None] = [None, None, None]
    announcements = []
    summary_start = text.lower().find("<h3>sumario</h3>")
    for item in item_pattern.finditer(text):
        if summary_start < 0 or item.start() < summary_start:
            continue
        body = item.group("body")
        link = re.search(
            r'<a[^>]+href="(?P<href>[^"]+/mod\.documentos/mem\.descargar/[^"]+)"[^>]*>',
            body,
            re.I | re.S,
        )
        if not link:
            continue
        parts = [_normalize_soria_context(part) for part in _class_texts(body, "fec-f1")]
        non_empty_parts = [part for part in parts if part]
        if not non_empty_parts:
            continue
        for index, part in enumerate(parts[:3]):
            if part:
                context[index] = part
        title = non_empty_parts[-1]
        href = html.unescape(link.group("href"))
        document_id = _bop_soria_document_id_from_url(href)
        summary = _join_title_parts(*context)
        if title and href and document_id:
            announcements.append((title, href, document_id, summary))
    return announcements


def _normalize_soria_context(value: str | None) -> str | None:
    normalized = _normalize_text(value)
    if not normalized:
        return None
    return normalized.lstrip("- ").strip() or None


def _iter_bop_valencia_announcements(text: str) -> list[tuple[str, str, str | None]]:
    block_pattern = re.compile(
        r'<div[^>]+class="[^"]*\banuncio\b[^"]*"[^>]*>(?P<body>.*?)(?='
        r'<script[^>]+id="list:\d+:[^"]+_s"|<div[^>]+class="[^"]*\banuncio\b|</body>)',
        re.I | re.S,
    )
    announcements = []
    for block in block_pattern.finditer(text):
        body = block.group("body")
        title_match = re.search(
            r'<div[^>]+class="[^"]*\bsumario\b[^"]*"[^>]*>.*?'
            r"<a\b[^>]*>(?P<title>.*?)</a>",
            body,
            re.I | re.S,
        )
        title = _normalize_text(_strip_tags(title_match.group("title"))) if title_match else None
        document_id = _first_register_label_value(body, "registre")
        published_at = _ddmmyyyy_to_iso(_first_date_text(body))
        if title and document_id:
            announcements.append((title, document_id, published_at))
    return announcements


def _extract_bop_avila_publication_date(text: str) -> str | None:
    match = re.search(r"\[\s*(\d{2}/\d{2}/\d{4})\s*\]", _strip_tags(text))
    if not match:
        match = re.search(r"\b(\d{2}/\d{2}/\d{4})\b", _strip_tags(text))
    return _ddmmyyyy_to_iso(match.group(1)) if match else None


def _iter_bop_avila_announcements(text: str) -> list[tuple[str, str, str]]:
    link_pattern = re.compile(
        r'<a[^>]+href="(?P<href>[^"]*/bops/\d{4}/\d{2}-\d{2}-\d{4}/[^"]+\.pdf)"'
        r"[^>]*>(?P<title>.*?)</a>",
        re.I | re.S,
    )
    announcements = []
    for link in link_pattern.finditer(text):
        href = html.unescape(link.group("href"))
        document_id = _bop_avila_document_id_from_url(href)
        title = _normalize_text(_strip_tags(link.group("title")))
        if title and document_id:
            announcements.append((title, href, document_id))
    return announcements


def _extract_bop_cordoba_publication_date(page_url: str) -> str | None:
    match = re.search(r"/dia/(\d{2})-(\d{2})-(\d{4})(?:\b|$)", page_url)
    if not match:
        return None
    return date(int(match.group(3)), int(match.group(2)), int(match.group(1))).isoformat()


def _iter_bop_cordoba_announcements(text: str) -> list[tuple[str, str, str, str, str | None]]:
    pattern = re.compile(
        r'\\"li\\",\\"(?P<entry_id>\d+)\\",\{\\"className\\":\\"announcement[^"]*\\"'
        r'.*?\\"children\\":\[\\" \\",\\"(?P<title>.*?)\\"\]\}'
        r'.*?\\"href\\":\\"(?P<href>/visor-pdf/[^"]+?/(?P<document_id>BOP-A-\d{4}-\d+)\.pdf)\\"',
        re.I | re.S,
    )
    announcements = []
    for match in pattern.finditer(text):
        title = _decode_nextjs_text(match.group("title"))
        href = _decode_nextjs_text(match.group("href"))
        document_id = match.group("document_id")
        issuer = _last_bop_cordoba_issuer(text[: match.start()])
        if title and href and document_id:
            announcements.append((match.group("entry_id"), title, href, document_id, issuer))
    return announcements


def _extract_bop_jaen_publication_date(text: str, page_url: str) -> str | None:
    match = re.search(r"/bop/(\d{2})-(\d{2})-(\d{4})", page_url)
    if match:
        return date(int(match.group(3)), int(match.group(2)), int(match.group(1))).isoformat()
    return _long_spanish_date_to_iso(_strip_tags(text))


def _extract_bop_jaen_issue_number(text: str) -> str | None:
    match = re.search(r"Bolet[ií]n\s+N[ºo]\s+(\d+)", _strip_tags(text), re.I)
    return match.group(1) if match else None


def _iter_bop_jaen_announcements(text: str) -> list[tuple[str, str, str, str, str | None]]:
    section_pattern = re.compile(r"<section\b[^>]*>(?P<body>.*?)</section>", re.I | re.S)
    article_pattern = re.compile(r"<article\b[^>]*>(?P<body>.*?)</article>", re.I | re.S)
    announcements = []
    for section in section_pattern.finditer(text):
        section_body = section.group("body")
        section_label = _first_class_block_text(section_body, "seccion")
        subsection = None
        department = None
        for match in re.finditer(
            r"""<p[^>]+class=(?P<quote>["'])(?P<class>[^"']+)(?P=quote)[^>]*>(?P<body>.*?)</p>|"""
            r"<article\b[^>]*>(?P<article>.*?)</article>",
            section_body,
            re.I | re.S,
        ):
            class_name = match.group("class") or ""
            if "subseccion" in class_name:
                subsection = _normalize_text(_strip_tags(match.group("body") or ""))
                department = None
                continue
            if "departamento" in class_name:
                department = _normalize_text(_strip_tags(match.group("body") or ""))
                continue
            article = match.group("article")
            if article is None:
                continue
            title = _first_class_block_text(article, "edicto")
            link = re.search(
                r"""<a[^>]+href=(?P<quote>["'])(?P<href>(?:(?!\1).)*descargarws\.dip(?:(?!\1).)*numeroEdicto=(?P<id>\d+)(?:(?!\1).)*)(?P=quote)""",
                article,
                re.I | re.S,
            )
            if not (title and link):
                continue
            href = html.unescape(link.group("href"))
            entry_id = link.group("id")
            year = _query_param_value(href, "ejercicioBop") or _query_param_value(
                href, "anioExpedienteEdicto"
            )
            document_id = f"BOP-{year}-{entry_id}" if year else entry_id
            announcements.append(
                (
                    title,
                    href,
                    entry_id,
                    document_id,
                    _join_title_parts(section_label, subsection, department),
                )
            )
    if announcements:
        return announcements
    for article in article_pattern.finditer(text):
        title = _first_class_block_text(article.group("body"), "edicto")
        if title:
            continue
    return announcements


def _first_bop_leon_document_id(text: str) -> str | None:
    match = re.search(r"\bBOP-LE-\d{4}-\d+\b", _strip_tags(text), re.I)
    return match.group(0).upper() if match else None


def _extract_bop_leon_issue_number(text: str) -> str | None:
    match = re.search(r"\bBOP\s+n[uú]m\.?\s+(\d+)\b", _strip_tags(text), re.I)
    return match.group(1) if match else None


def _extract_bop_lleida_publication_date(text: str) -> str | None:
    match = re.search(r"Bop\s+n[úu]mero:\s*[\d/]+\s*-\s*(\d{2}/\d{2}/\d{4})", text, re.I)
    return _ddmmyyyy_to_iso(match.group(1)) if match else None


def _extract_bop_lleida_issue_number(text: str) -> str | None:
    match = re.search(r"Bop\s+n[úu]mero:\s*([\d/]+)\s*-", text, re.I)
    return match.group(1) if match else None


def _iter_bop_lleida_announcements(text: str) -> list[tuple[str, str, str, str | None]]:
    section_pattern = re.compile(
        r'<h2[^>]+class="[^"]*\bseccioTau\b[^"]*"[^>]*>(?P<section>.*?)</h2>'
        r"(?P<body>.*?)(?=<h2[^>]+class=\"[^\"]*\bseccioTau\b|</body>)",
        re.I | re.S,
    )
    announcements = []
    for section in section_pattern.finditer(text):
        summary = _normalize_text(_strip_tags(section.group("section")))
        for item in re.finditer(
            r'<li[^>]+class="[^"]*\bedicte\b[^"]*"[^>]*>.*?'
            r'<a[^>]+href="(?P<href>[^"]+\.pdf)"[^>]*>(?P<title>.*?)</a>',
            section.group("body"),
            re.I | re.S,
        ):
            href = html.unescape(item.group("href"))
            document_id = _bop_lleida_document_id_from_url(href)
            title = _normalize_text(_strip_tags(item.group("title")))
            if title and document_id:
                announcements.append((title, href, document_id, summary))
    return announcements


def _bop_lleida_document_id_from_url(value: str) -> str | None:
    match = re.search(r"/(\d+)\.pdf\b", value, re.I)
    return match.group(1) if match else None


def _last_bop_cordoba_issuer(text: str) -> str | None:
    pattern = re.compile(
        r'\\"className\\":\\"emisor\\".*?\\"h2\\",null,\{\\"children\\":\\"(?P<issuer>.*?)\\"\}',
        re.I | re.S,
    )
    matches = list(pattern.finditer(text))
    if not matches:
        return None
    return _decode_nextjs_text(matches[-1].group("issuer"))


def _decode_nextjs_text(value: str | None) -> str | None:
    if value is None:
        return None
    try:
        decoded = json.loads(f'"{value}"')
    except json.JSONDecodeError:
        decoded = value
    return _normalize_text(decoded)


def _extract_bop_araba_issue_number(text: str) -> str | None:
    plain = _strip_tags(text)
    match = re.search(r"Bolet[ií]n\s+N[ºo]?\s*(\d+)", plain, re.I)
    if match:
        return match.group(1)
    match = re.search(r"/Boletines/\d{4}/(\d{3})/", html.unescape(text), re.I)
    return str(int(match.group(1))) if match else None


def _iter_bop_araba_announcements(text: str) -> list[tuple[str, str, str, str, str | None]]:
    token_pattern = re.compile(
        r"""<div[^>]+class=(?P<q1>["'])titulo_bloque_resultados(?P=q1)[^>]*>"""
        r"(?P<section>.*?)</div>|"
        r"""<div[^>]+class=(?P<q2>["'])datos_anuncio(?P=q2)[^>]*>"""
        r"(?P<body>.*?)(?=<div[^>]+class=['\"]titulo_bloque_resultados|</literal>|$)",
        re.I | re.S,
    )
    context: list[str] = []
    announcements = []
    seen: set[str] = set()
    for token in token_pattern.finditer(text):
        section = token.group("section")
        if section is not None:
            section_text = _normalize_text(_strip_tags(section))
            if section_text:
                context.append(section_text)
                context = context[-2:]
            continue
        body = token.group("body") or ""
        link = re.search(
            r'<a[^>]+href="(?P<href>[^"]*Resultado\.aspx\?File=(?P<file>[^"&]+\.xml)[^"]*)"'
            r"[^>]*>(?P<title>.*?)</a>",
            body,
            re.I | re.S,
        )
        if not link:
            continue
        document_id = _document_id_from_filename(link.group("file"))
        if not document_id or document_id in seen:
            continue
        entry_id = _first_numeric_token(document_id.rsplit("_", 2)[-2])
        title = _normalize_text(_strip_tags(link.group("title")))
        if title and entry_id:
            seen.add(document_id)
            announcements.append(
                (
                    title,
                    html.unescape(link.group("href")),
                    entry_id,
                    document_id,
                    _join_title_parts(*context),
                )
            )
    return announcements


def _extract_bop_ciudad_real_publication_date(text: str) -> str | None:
    match = re.search(r"\b(\d{2})-(\d{2})-(\d{4})\b", _strip_tags(text))
    if not match:
        return None
    return date(int(match.group(3)), int(match.group(2)), int(match.group(1))).isoformat()


def _extract_bop_ciudad_real_issue_number(text: str) -> str | None:
    match = re.search(r"\bN[uú]mero\s+(\d+)\b", _strip_tags(text), re.I)
    return match.group(1) if match else None


def _iter_bop_ciudad_real_announcements(
    text: str,
) -> list[tuple[str, str, str, str, str | None]]:
    token_pattern = re.compile(
        r"""<h3[^>]+class=(?P<q1>["'])admons(?P=q1)[^>]*>(?P<section>.*?)</h3>|"""
        r"""<p[^>]+class=(?P<q2>["'])clasificaciones(?P=q2)[^>]*>(?P<issuer>.*?)</p>|"""
        r'<li[^>]+id="(?P<entry_id>\d+)"[^>]*>(?P<body>.*?)</li>',
        re.I | re.S,
    )
    section = None
    issuer = None
    announcements = []
    for token in token_pattern.finditer(text):
        if token.group("section") is not None:
            section = _normalize_text(_strip_tags(token.group("section")))
            issuer = None
            continue
        if token.group("issuer") is not None:
            issuer = _normalize_text(_strip_tags(token.group("issuer")))
            continue
        body = token.group("body") or ""
        link = re.search(
            r'<a[^>]+href="(?P<href>[^"]*getDocument\.do[^"]*)"[^>]*>(?P<title>.*?)</a>',
            body,
            re.I | re.S,
        )
        if not link:
            continue
        href = html.unescape(link.group("href"))
        document_id = _query_param_value(href, "doc")
        title = _normalize_text(_strip_tags(link.group("title")))
        if title and document_id:
            announcements.append(
                (
                    title,
                    href,
                    token.group("entry_id"),
                    document_id,
                    _join_title_parts(section, issuer),
                )
            )
    return announcements


def _iter_bop_cuenca_bulletins(
    text: str, requested_date: str
) -> list[tuple[str, str, str, str, str | None]]:
    target_date = validate_html_monitor_date(requested_date)
    pattern = re.compile(
        r'<a[^>]+href="(?P<href>[^"]+articleId=(?P<id>\d+)[^"]*)"[^>]+'
        r'title="Ir a (?P<title>[^"]+\d{4})"[^>]*>',
        re.I | re.S,
    )
    bulletins = []
    seen: set[str] = set()
    for match in pattern.finditer(text):
        document_id = match.group("id")
        if document_id in seen:
            continue
        title = _normalize_text(match.group("title"))
        published_at = _segovia_card_date_to_iso(title)
        if published_at != target_date:
            continue
        nearby = text[match.end() : match.end() + 1200]
        issue_match = re.search(
            r'<span[^>]+class="[^"]*\bcard-text\b[^"]*"[^>]*>\s*(\d+)\s*</span>',
            nearby,
            re.I | re.S,
        )
        seen.add(document_id)
        bulletins.append(
            (
                title,
                html.unescape(match.group("href")),
                document_id,
                published_at,
                issue_match.group(1) if issue_match else None,
            )
        )
    return bulletins


def _extract_bop_gipuzkoa_publication_date(text: str) -> str | None:
    match = re.search(r"\bFecha\s+(\d{2})-(\d{2})-(\d{4})\b", _strip_tags(text), re.I)
    if not match:
        match = re.search(r"\bBolet[ií]n\s+(\d{2})-(\d{2})-(\d{4})", _strip_tags(text), re.I)
    if not match:
        return None
    return date(int(match.group(3)), int(match.group(2)), int(match.group(1))).isoformat()


def _extract_bop_gipuzkoa_issue_number(text: str) -> str | None:
    match = re.search(r"\bN[uú]mero\s+(\d+)\b", _strip_tags(text), re.I)
    return match.group(1) if match else None


def _extract_bop_girona_publication_date(text: str) -> str | None:
    match = re.search(
        r"\bBop\s+n\S*mero:\s*(\d+)/\d+\s*-\s*(\d{2})/(\d{2})/(\d{4})\b",
        _strip_tags(text),
        re.I,
    )
    if not match:
        return None
    return date(int(match.group(4)), int(match.group(3)), int(match.group(2))).isoformat()


def _extract_bop_girona_issue_number(text: str) -> str | None:
    match = re.search(r"\bBop\s+n\S*mero:\s*(\d+)/\d+", _strip_tags(text), re.I)
    return match.group(1) if match else None


def _iter_bop_girona_announcements(text: str) -> list[tuple[str, str, str, str | None]]:
    sections = [
        (match.start(), _normalize_text(_strip_tags(match.group("body"))))
        for match in re.finditer(
            r'<h2[^>]+class="[^"]*\bseccioTau\b[^"]*"[^>]*>(?P<body>.*?)</h2>',
            text,
            re.I | re.S,
        )
    ]
    announcements = []
    seen: set[str] = set()
    for item in re.finditer(
        r'<li[^>]+class="[^"]*\bedicte\b[^"]*"[^>]*>(?P<body>.*?)</li>',
        text,
        re.I | re.S,
    ):
        body = item.group("body")
        link = re.search(
            r'<a[^>]+href="(?P<href>[^"]+)"[^>]*>(?P<body>.*?)</a>',
            body,
            re.I | re.S,
        )
        if not link:
            continue
        href = html.unescape(link.group("href"))
        document_id = _document_id_from_filename(href)
        if not document_id or document_id in seen:
            continue
        seen.add(document_id)
        _, issuer, title = _split_bop_girona_link_text(
            _normalize_text(_strip_tags(link.group("body")))
        )
        if title and href:
            announcements.append(
                (
                    title,
                    href,
                    document_id,
                    _join_title_parts(_last_positioned_value(sections, item.start()), issuer),
                )
            )
    return announcements


def _extract_bop_huesca_publication_date(text: str) -> str | None:
    match = re.search(r"\bFecha:\s*(\d{2})-(\d{2})-(\d{4})\b", _strip_tags(text), re.I)
    if not match:
        return None
    return date(int(match.group(3)), int(match.group(2)), int(match.group(1))).isoformat()


def _extract_bop_huesca_issue_number(text: str) -> str | None:
    match = re.search(r"\bN\S*mero:\s*(\d+)\b", _strip_tags(text), re.I)
    return match.group(1) if match else None


def _iter_bop_huesca_announcements(text: str) -> list[tuple[str, str, str, str | None]]:
    sections = [
        (match.start(), _normalize_text(_strip_tags(match.group("body"))))
        for match in re.finditer(
            r"<strong>\s*Secci\S*n:\s*(?P<body>.*?)</strong>",
            text,
            re.I | re.S,
        )
    ]
    subsections = [
        (match.start(), _normalize_text(_strip_tags(match.group("body"))))
        for match in re.finditer(
            r"<strong>\s*Subsecci\S*n:\s*(?P<body>.*?)</strong>",
            text,
            re.I | re.S,
        )
    ]
    announcements = []
    seen: set[str] = set()
    pattern = re.compile(
        r"<p[^>]*>\s*<strong>\s*\+(?:\s|&nbsp;)*\d{4}\s*/\s*\d+"
        r"(?:\s|&nbsp;)*-(?:\s|&nbsp;)*(?P<issuer>.*?)</strong>\s*</p>\s*"
        r"<p[^>]*>(?P<body>.*?)</p>",
        re.I | re.S,
    )
    for match in pattern.finditer(text):
        body = match.group("body")
        link = re.search(r'<a[^>]+href="(?P<href>[^"]*idbopanuncio\.(?P<id>\d+)[^"]*)"', body, re.I)
        title_match = re.search(r"<em>(?P<title>.*?)</em>", body, re.I | re.S)
        if not link or not title_match:
            continue
        document_id = link.group("id")
        if document_id in seen:
            continue
        seen.add(document_id)
        category = _bop_huesca_category(body)
        announcements.append(
            (
                _normalize_text(_strip_tags(title_match.group("title"))),
                html.unescape(link.group("href")),
                document_id,
                _join_title_parts(
                    _last_positioned_value(sections, match.start()),
                    _last_positioned_value(subsections, match.start()),
                    _normalize_text(_strip_tags(match.group("issuer"))),
                    category,
                ),
            )
        )
    return announcements


def _bop_huesca_category(body: str) -> str | None:
    before_title = body.split("<em", 1)[0]
    text = _normalize_text(_strip_tags(before_title))
    return text or None


def _split_bop_girona_link_text(value: str) -> tuple[str | None, str | None, str | None]:
    parts = [_normalize_text(part) for part in value.split(" - ") if _normalize_text(part)]
    if len(parts) >= 3:
        return parts[0], parts[1], " - ".join(parts[2:])
    if len(parts) == 2:
        return parts[0], None, parts[1]
    if len(parts) == 1:
        return None, None, parts[0]
    return None, None, None


def _iter_bop_tarragona_announcements(text: str) -> list[tuple[str, str, str, str | None]]:
    announcements = []
    seen: set[str] = set()
    for card in re.finditer(
        r'<div[^>]+class="[^"]*\bcard-body\b[^"]*"[^>]*>(?P<body>.*?)</div>',
        text,
        re.I | re.S,
    ):
        body = card.group("body")
        link = re.search(
            r'<a[^>]+href="(?P<href>[^"]*/bopt/web/anuncio/(?P<id>\d+)[^"]*)"[^>]*>'
            r"(?P<body>.*?)</a>",
            body,
            re.I | re.S,
        )
        if not link:
            continue
        document_id = link.group("id")
        if document_id in seen:
            continue
        seen.add(document_id)
        paragraph = re.search(r"<p\b[^>]*>(?P<body>.*?)</p>", body, re.I | re.S)
        title = _normalize_text(_strip_tags(paragraph.group("body"))) if paragraph else None
        href = html.unescape(link.group("href"))
        summary = _normalize_text(_strip_tags(link.group("body")))
        if title and href:
            announcements.append((title, href, document_id, summary))
    return announcements


def _iter_bop_gipuzkoa_announcements(text: str) -> list[tuple[str, str, str, str | None]]:
    sections = [
        (match.start(), _normalize_text(_strip_tags(match.group("body"))))
        for match in re.finditer(
            r'<li[^>]+class="[^"]*\bseccion\b[^"]*"[^>]*>\s*<p>(?P<body>.*?)</p>',
            text,
            re.I | re.S,
        )
    ]
    organisms = [
        (match.start(), _normalize_text(_strip_tags(match.group("body"))))
        for match in re.finditer(
            r'<li[^>]+class="[^"]*\borganismo\b[^"]*"[^>]*>\s*'
            r'<a[^>]+name="[^"]+"[^>]*>(?P<body>.*?)</a>',
            text,
            re.I | re.S,
        )
    ]
    announcements = []
    pattern = re.compile(
        r'<div[^>]+class="[^"]*\btitulo_anuncio\b[^"]*"[^>]*>(?P<title>.*?)</div>'
        r".*?"
        r'<a[^>]+class="[^"]*\bdescarga_html\b[^"]*"[^>]+href="(?P<href>[^"]+\.htm)"',
        re.I | re.S,
    )
    for match in pattern.finditer(text):
        title = _normalize_text(_strip_tags(match.group("title")))
        href = html.unescape(match.group("href"))
        document_id = _document_id_from_filename(href)
        if title and document_id:
            announcements.append(
                (
                    title,
                    href,
                    document_id,
                    _join_title_parts(
                        _last_positioned_value(sections, match.start()),
                        _last_positioned_value(organisms, match.start()),
                    ),
                )
            )
    return announcements


def _extract_bop_valladolid_publication_date(text: str) -> str | None:
    match = re.search(
        r'id="bop_sumario_tit_fecha"[^>]*>\s*(\d{1,2})\s+de\s+'
        r"([a-záéíóú]+)\s+de\s+(\d{4})",
        text,
        re.I,
    )
    if not match:
        match = re.search(
            r"\b(\d{1,2})\s+de\s+([a-záéíóú]+)\s+de\s+(\d{4})\b",
            _strip_tags(text),
            re.I,
        )
    if not match:
        return None
    month = _SPANISH_MONTHS.get(match.group(2).lower())
    if not month:
        return None
    return date(int(match.group(3)), month, int(match.group(1))).isoformat()


def _iter_bop_valladolid_announcements(text: str) -> list[tuple[str, str, str, str | None]]:
    item_pattern = re.compile(
        r'<li[^>]+class="[^"]*\bun_anuncio\b[^"]*"[^>]*>(?P<body>.*?)</li>',
        re.I | re.S,
    )
    announcements = []
    for item in item_pattern.finditer(text):
        body = item.group("body")
        link = re.search(
            r'<p[^>]+class="[^"]*\bbop_res_articulo\b[^"]*"[^>]*>.*?'
            r'<a[^>]+href="(?P<href>[^"]+\.pdf)"[^>]*(?:title="(?P<title_attr>[^"]*)")?'
            r"[^>]*>(?P<title>.*?)</a>",
            body,
            re.I | re.S,
        )
        if not link:
            continue
        href = html.unescape(link.group("href"))
        document_id = _bop_valladolid_document_id_from_url(href)
        title = _first_value(
            [
                _normalize_text(link.group("title_attr")),
                _normalize_text(_strip_tags(link.group("title"))),
            ]
        )
        issuer = _first_class_block_text(body, "bop_tit_articulo")
        if title and href and document_id:
            announcements.append((title, href, document_id, issuer))
    return announcements


def _iter_bop_zaragoza_announcements(text: str) -> list[tuple[str, str, str | None]]:
    token_pattern = re.compile(
        r"<h3>(?P<section>.*?)</h3>|"
        r'<p[^>]+class="[^"]*\bparrafo\b[^"]*"[^>]*style="[^"]*margin-bottom:0px[^"]*"'
        r'[^>]*>(?P<issuer>.*?)</p>|'
        r'<a[^>]+class="[^"]*\benlaceEdicto\b[^"]*"[^>]*'
        r'onclick="[^"]*abreVentanaDetalleEdicto\('
        r"'(?P<entry_id>\d+)'\)[^>]*>(?P<title>.*?)</a>",
        re.I | re.S,
    )
    section = None
    issuer = None
    announcements = []
    seen: set[str] = set()
    for token in token_pattern.finditer(text):
        if token.group("section") is not None:
            section = _normalize_text(_strip_tags(token.group("section")))
            issuer = None
            continue
        if token.group("issuer") is not None:
            issuer = _normalize_text(_strip_tags(token.group("issuer")))
            continue
        entry_id = token.group("entry_id")
        if not entry_id or entry_id in seen:
            continue
        title = _normalize_text(_strip_tags(token.group("title")))
        if title:
            seen.add(entry_id)
            announcements.append((title, entry_id, _join_title_parts(section, issuer)))
    return announcements


def _bop_zaragoza_detail_url(
    page_url: str,
    *,
    entry_id: str,
    issue_number: str | None,
    fecha_pub: str | None,
) -> str:
    params = {"idEdicto": entry_id}
    if issue_number:
        params["numBop"] = issue_number
    if fecha_pub:
        params["fechaPub"] = fecha_pub
    return urljoin(page_url, f"obtenerContenidoEdicto.do?{urlencode(params)}")


def _iter_bop_segovia_bulletins(
    text: str, requested_date: str
) -> list[tuple[str, str, str, str]]:
    target_date = validate_html_monitor_date(requested_date)
    pattern = re.compile(
        r'<a[^>]+href="(?P<href>[^"]+articleId=(?P<id>\d+)[^"]*)"[^>]+'
        r'title="Ir a (?P<title>[^"]+\d{4})"[^>]*>',
        re.I | re.S,
    )
    bulletins = []
    seen: set[str] = set()
    for match in pattern.finditer(text):
        document_id = match.group("id")
        if document_id in seen:
            continue
        title = _normalize_text(match.group("title"))
        published_at = _segovia_card_date_to_iso(title)
        if published_at != target_date:
            continue
        seen.add(document_id)
        bulletins.append((title, html.unescape(match.group("href")), document_id, published_at))
    return bulletins


def _segovia_card_date_to_iso(value: str) -> str | None:
    match = re.search(r"\b(\d{1,2})\s+de\s+([a-záéíóú]+)\s+(\d{4})\b", value, re.I)
    if not match:
        return None
    month = _SPANISH_MONTHS.get(match.group(2).lower())
    if not month:
        return None
    return date(int(match.group(3)), month, int(match.group(1))).isoformat()


def _extract_bop_toledo_publication_date(text: str) -> str | None:
    return _ddmmyyyy_to_iso(_first_date_text(text))


def _extract_bop_toledo_issue_number(text: str) -> str | None:
    plain = _strip_tags(text)
    match = re.search(r"\bBolet[ií]n\s+n[uú]mero\s+(\d+)\b", plain, re.I)
    if not match:
        match = re.search(r"\bBoletin\s+numero\s+(\d+)\b", plain, re.I)
    return match.group(1) if match else None


def _iter_bop_toledo_announcements(text: str) -> list[tuple[str, str, str, str, str | None]]:
    pattern = re.compile(
        r'<div[^>]+id="(?P<entry_id>\d+)>[^"]*"[^>]+class="announce"[^>]*>'
        r"(?P<body>.*?</ul>)\s*</div>",
        re.I | re.S,
    )
    announcements = []
    for match in pattern.finditer(text):
        body = match.group("body")
        plain = _strip_tags(body)
        link = re.search(r'<a[^>]+href="(?P<href>[^"]*DocGet[^"]*)"', body, re.I | re.S)
        insert_number = _toledo_label_value(plain, "Numero de insercion") or _toledo_label_value(
            plain, "Número de inserción"
        )
        insert_number = _first_numeric_token(insert_number)
        title = _toledo_label_value(plain, "Resumen/Asunto")
        announcement_type = _toledo_label_value(plain, "Tipo de anuncio")
        publisher = _last_bop_toledo_publisher(text[: match.start()])
        if title and link and insert_number:
            announcements.append(
                (
                    title,
                    html.unescape(link.group("href")),
                    match.group("entry_id"),
                    insert_number,
                    _join_title_parts(publisher, announcement_type),
                )
            )
    return announcements


def _last_bop_toledo_publisher(text: str) -> str | None:
    matches = list(
        re.finditer(
            r'<h3[^>]+class="[^"]*\bpublisherBlock\b[^"]*"[^>]*>(?P<body>.*?)</h3>',
            text,
            re.I | re.S,
        )
    )
    if not matches:
        return None
    publisher = _normalize_text(_strip_tags(matches[-1].group("body")))
    return re.sub(r"^Anunciante\s*:\s*", "", publisher, flags=re.I)


def _toledo_label_value(text: str, label: str) -> str | None:
    labels = [
        "Numero de insercion",
        "Número de inserción",
        "Tipo de anuncio",
        "Resumen/Asunto",
    ]
    next_labels = "|".join(re.escape(item) for item in labels if item != label)
    match = re.search(
        rf"{re.escape(label)}\s*:\s*(?P<value>.*?)(?=(?:{next_labels})\s*:|$)",
        text,
        re.I | re.S,
    )
    return _normalize_text(match.group("value")) if match else None


def _first_numeric_token(value: str | None) -> str | None:
    match = re.search(r"\d+", value or "")
    return match.group(0) if match else None


def _parse_legacy_island_bop_html(
    raw_page: bytes | str,
    *,
    source_code: str,
    page_url: str,
    requested_date: str,
    discovered_at: str,
    monitor_run_id: str,
) -> HTMLParseResult:
    raw_bytes = _coerce_page_bytes(raw_page)
    raw_page_hash = hashlib.sha256(raw_bytes).hexdigest()
    text = raw_bytes.decode("utf-8", errors="replace")
    issue_number, legacy_date = _extract_legacy_island_bop_issue_and_date(text)
    published_at = _legacy_short_date_to_iso(legacy_date)
    if published_at != requested_date:
        return HTMLParseResult(raw_page_hash=raw_page_hash, records=[])
    pdf_url = _first_pdf_url(text, page_url)
    record = _build_html_record(
        source_code=source_code,
        page_url=page_url,
        page_format="html",
        entry_id=legacy_date,
        document_id=legacy_date,
        title=f"Sumario del boletin {issue_number} de fecha {legacy_date}",
        published_at=published_at,
        official_url=pdf_url,
        summary="SUMARIO",
        raw_page_hash=raw_page_hash,
        discovered_at=discovered_at,
        monitor_run_id=monitor_run_id,
        warnings=["pdf_endpoint_not_downloaded"] if pdf_url else [],
    )
    if issue_number:
        record["issue_number"] = issue_number
    return HTMLParseResult(raw_page_hash=raw_page_hash, records=[record])


def _extract_legacy_island_bop_issue_and_date(text: str) -> tuple[str | None, str | None]:
    plain = _normalize_text(_strip_tags(text))
    match = re.search(
        r"SUMARIO\s+DEL\s+BOLET[IÍ]N\s+N[ºo]\s*(\d+).*?"
        r"DE\s+FECHA\s+(\d{1,2}-\d{1,2}-\d{2,4})",
        plain,
        re.I,
    )
    if not match:
        return None, None
    return match.group(1), match.group(2)


def _legacy_short_date_to_iso(value: str | None) -> str | None:
    if not value:
        return None
    try:
        day, month, year = value.split("-")
        parsed_year = int(year)
        if parsed_year < 100:
            parsed_year += 2000
        return date(parsed_year, int(month), int(day)).isoformat()
    except ValueError:
        return None


def _first_pdf_url(text: str, page_url: str) -> str | None:
    match = re.search(r'<a[^>]+href=["\'](?P<href>[^"\']+\.pdf)["\']', text, re.I | re.S)
    if not match:
        return None
    return urljoin(page_url, html.unescape(match.group("href")))


def _extract_bop_salamanca_publication_date(text: str) -> str | None:
    plain = _normalize_text(_strip_tags(text))
    match = re.search(r"Bolet[ií]n\s+del\s+d[ií]a\s+(\d{1,2})/(\d{1,2})/(\d{4})", plain, re.I)
    if not match:
        return None
    return date(int(match.group(3)), int(match.group(2)), int(match.group(1))).isoformat()


def _extract_bop_salamanca_title(text: str) -> str | None:
    for match in re.finditer(r"<h[1-6]\b[^>]*>(?P<title>.*?)</h[1-6]>", text, re.I | re.S):
        title = _normalize_text(_strip_tags(match.group("title")))
        if re.search(r"Bolet[ií]n\s+del\s+d[ií]a", title, re.I):
            return title
    return None


def _extract_bop_salamanca_bulletin_pdf_url(
    text: str, page_url: str, published_at: str
) -> str | None:
    yyyymmdd = date.fromisoformat(published_at).strftime("%Y%m%d")
    match = re.search(
        rf'<a[^>]+href=["\'](?P<href>[^"\']*BOP-SA-{yyyymmdd}-\d+\.pdf)["\']',
        text,
        re.I | re.S,
    )
    return urljoin(page_url, html.unescape(match.group("href"))) if match else None


def _extract_bop_teruel_publication_label(text: str) -> str | None:
    plain = _normalize_text(_strip_tags(text))
    match = re.search(
        r"\b(\d{1,2}\s+de\s+[A-Za-zÁÉÍÓÚáéíóúñÑ]+\s+de\s+\d{4})\b",
        plain,
        re.I,
    )
    return match.group(1) if match else None


def _extract_bop_teruel_publication_date(text: str) -> str | None:
    label = _extract_bop_teruel_publication_label(text)
    if not label:
        return None
    return _long_spanish_date_to_iso(label)


def _extract_bop_teruel_issue_number(text: str) -> str | None:
    plain = _normalize_text(_strip_tags(text))
    return _regex_value(r"BOP\s+n[uú]mero\s+(\d+)", plain)


def _extract_bop_teruel_official_url(text: str, page_url: str) -> str | None:
    match = re.search(
        r'<a[^>]+class=["\'][^"\']*\bver-boletin\b[^"\']*["\'][^>]+href=["\'](?P<href>[^"\']+)',
        text,
        re.I | re.S,
    )
    if not match:
        match = re.search(
            r'<a[^>]+href=["\'](?P<href>[^"\']*Redireccion[^"\']+)',
            text,
            re.I | re.S,
        )
    return urljoin(page_url, html.unescape(match.group("href"))) if match else None


def _regex_value(pattern: str, value: str) -> str | None:
    match = re.search(pattern, value, re.I)
    return match.group(1) if match else None


def _last_positioned_value(items: list[tuple[int, str | None]], position: int) -> str | None:
    value = None
    for item_position, item_value in items:
        if item_position > position:
            break
        if item_value:
            value = item_value
    return value


def _extract_bop_zamora_detail_url(text: str, page_url: str, target_date: str) -> str:
    date_pattern = _long_date_pattern(target_date)
    item_pattern = re.compile(
        r'<li[^>]+class="[^"]*\blist-entry\b[^"]*"[^>]*>(?P<body>.*?)</li>',
        re.I | re.S,
    )
    for item in item_pattern.finditer(text):
        body = item.group("body")
        if not date_pattern.search(_strip_tags(body)):
            continue
        link = re.search(
            r'<a[^>]+href="(?P<href>[^"]*/opencms/servicios/BOP/indice-bop/[^"]+)"',
            body,
            re.I | re.S,
        )
        if link:
            return urljoin(page_url, html.unescape(link.group("href")))
    raise HTMLMonitorError("BOP_ZAMORA landing page did not expose a detail URL for requested date")


def _extract_bop_zamora_publication_date(text: str) -> str | None:
    return _long_spanish_date_to_iso(_strip_tags(text))


def _extract_bop_zamora_issue_number(text: str) -> str | None:
    match = re.search(r"\bBOP\s+(\d+)\b", _strip_tags(text), re.I)
    return match.group(1) if match else None


def _iter_bop_zamora_announcements(text: str) -> list[tuple[str, str, str, str | None]]:
    block_pattern = re.compile(
        r'<div[^>]+id="anuncio"[^>]*>(?P<body>.*?)(?=<div[^>]+id="anuncio"|</body>)',
        re.I | re.S,
    )
    announcements = []
    for block in block_pattern.finditer(text):
        body = block.group("body")
        section = _first_class_block_text(body, "sub-header")
        procedencia = _label_value(body, "Procedencia")
        organismo = _label_value(body, "Organismo")
        title = _label_value(body, "Extracto")
        document_id = _bop_zamora_reference(body)
        link = re.search(r'<a[^>]+href="(?P<href>[^"]+\.pdf)"', body, re.I | re.S)
        if title and document_id and link:
            announcements.append(
                (
                    title,
                    html.unescape(link.group("href")),
                    document_id,
                    _join_title_parts(section, procedencia, organismo),
                )
            )
    return announcements


def _bop_zamora_reference(text: str) -> str | None:
    match = re.search(r"N[ºo]\s+de\s+referencia\s*:\s*(\d+)", _strip_tags(text), re.I)
    return match.group(1) if match else None


def _iter_bopa_announcements(text: str) -> list[tuple[str, str, str, str | None, bool]]:
    container = _first_id_container(text, "bopa-boletin") or text
    tokens = re.finditer(
        r"<h4\b[^>]*>(?P<h4>.*?)</h4>|<h5\b[^>]*>(?P<h5>.*?)</h5>|"
        r"<h6\b[^>]*>(?P<h6>.*?)</h6>|<dl\b[^>]*>(?P<dl>.*?)</dl>",
        container,
        re.I | re.S,
    )
    context: dict[str, str | None] = {"h4": None, "h5": None, "h6": None}
    announcements = []
    for token in tokens:
        if token.group("h4") is not None:
            context = {
                "h4": _normalize_text(_strip_tags(token.group("h4"))),
                "h5": None,
                "h6": None,
            }
            continue
        if token.group("h5") is not None:
            context["h5"] = _normalize_text(_strip_tags(token.group("h5")))
            context["h6"] = None
            continue
        if token.group("h6") is not None:
            context["h6"] = _normalize_text(_strip_tags(token.group("h6")))
            continue
        dl = token.group("dl") or ""
        dt_match = re.search(r"<dt\b[^>]*>(?P<title>.*?)</dt>", dl, re.I | re.S)
        link = re.search(
            r'<a[^>]+title="[^"]*Texto[^"]*"[^>]+href="(?P<href>[^"]+)"',
            dl,
            re.I | re.S,
        )
        code = re.search(r"\[\s*C[oó]d\.?\s*(?P<id>\d{4}-\d+)\s*\]", _strip_tags(dl), re.I)
        if not (dt_match and link and code):
            continue
        title = re.sub(
            r"\s*\[\s*C[oó]d\.?\s*\d{4}-\d+\s*\]\s*$",
            "",
            _normalize_text(_strip_tags(dt_match.group("title"))),
            flags=re.I,
        )
        announcements.append(
            (
                title,
                html.unescape(link.group("href")),
                code.group("id"),
                _join_title_parts(context["h4"], context["h5"], context["h6"]),
                ".pdf" in dl.lower(),
            )
        )
    return announcements


def _extract_bop_pontevedra_publication_date(text: str) -> str | None:
    match = re.search(
        r'<span[^>]+class="[^"]*\bfecha\b[^"]*"[^>]*>.*?'
        r"\b(\d{1,2})\s+de\s+([a-z]+)\s+de\s+(\d{4})\b",
        text,
        re.I | re.S,
    )
    if not match:
        match = re.search(
            r"\b(\d{1,2})\s+de\s+([a-z]+)\s+de\s+(\d{4})\b",
            _strip_tags(text),
            re.I,
        )
    if not match:
        return None
    month = _SPANISH_MONTHS.get(match.group(2).lower())
    if not month:
        return None
    return date(int(match.group(3)), month, int(match.group(1))).isoformat()


def _iter_bop_pontevedra_announcements(text: str) -> list[tuple[str, str, str, str | None]]:
    item_pattern = re.compile(r"<li\b[^>]*>(?P<body>.*?)</li>", re.I | re.S)
    announcements = []
    for item in item_pattern.finditer(text):
        body = item.group("body")
        link = re.search(
            r'<p[^>]+class="[^"]*\bsumario\b[^"]*"[^>]*>.*?'
            r'<a[^>]+href="(?P<href>[^"]+)"[^>]*>(?P<title>.*?)</a>',
            body,
            re.I | re.S,
        )
        if not link:
            continue
        href = html.unescape(link.group("href"))
        pdf_link = re.search(
            r'<a[^>]+class="[^"]*\bbotDescPDF\b[^"]*"[^>]+href="(?P<href>[^"]+)"',
            body,
            re.I | re.S,
        )
        document_id = _bop_pontevedra_document_id_from_url(href)
        if document_id is None and pdf_link:
            document_id = _bop_pontevedra_document_id_from_url(
                html.unescape(pdf_link.group("href"))
            )
        title = _normalize_text(_strip_tags(link.group("title")))
        issuer = _first_class_block_text(body, "pub")
        if title and href and document_id:
            announcements.append((title, href, document_id, issuer))
    return announcements


def _iter_bop_palencia_bulletins(text: str) -> list[tuple[str, str | None, str, str]]:
    row_pattern = re.compile(
        r'<div[^>]+class="[^"]*\bviews-row\b[^"]*"[^>]*>(?P<body>.*?)(?='
        r'<div[^>]+class="[^"]*\bviews-row\b|</body>)',
        re.I | re.S,
    )
    bulletins = []
    for row in row_pattern.finditer(text):
        body = row.group("body")
        pdf_match = re.search(r'<a[^>]+href="(?P<href>[^"]+\.pdf)"', body, re.I | re.S)
        if not pdf_match:
            continue
        detail_match = re.search(
            r'<a[^>]+href="(?P<href>[^"]*/servicios/boletin-oficial-provincia/[^"]+)"[^>]*>'
            r"(?P<title>.*?)</a>",
            body,
            re.I | re.S,
        )
        fallback_title = _first_heading_text(body) or _first_class_block_text(
            body, "views-field-title"
        )
        title = _first_value(
            [
                _normalize_text(_strip_tags(detail_match.group("title"))) if detail_match else None,
                fallback_title,
            ]
        )
        pdf_href = html.unescape(pdf_match.group("href"))
        detail_href = html.unescape(detail_match.group("href")) if detail_match else None
        document_id = _bop_palencia_document_id_from_url(pdf_href)
        if title and document_id:
            bulletins.append((title, detail_href, pdf_href, document_id))
    return bulletins


def _bop_palencia_document_id_from_url(value: str) -> str | None:
    match = re.search(r"/([^/]+)\.pdf\b", value, re.I)
    if not match:
        return None
    return match.group(1)


def _bop_palencia_publication_date_from_id(document_id: str | None) -> str | None:
    if not document_id:
        return None
    match = re.match(r"(\d{4})(\d{2})(\d{2})-", document_id)
    if not match:
        return None
    return date(int(match.group(1)), int(match.group(2)), int(match.group(3))).isoformat()


def _extract_docm_publication_date(text: str) -> str | None:
    date_text = _first_class_block_text(text, "fechaDiario")
    if not date_text:
        return None
    match = re.search(r"\b(\d{1,2})\s+de\s+([a-záéíóú]+)\s+de\s+(\d{4})\b", date_text, re.I)
    if not match:
        return None
    month = _SPANISH_MONTHS.get(match.group(2).lower())
    if not month:
        return None
    return date(int(match.group(3)), month, int(match.group(1))).isoformat()


def _extract_docm_issue_number(text: str) -> str | None:
    issue_text = _first_class_block_text(text, "numeroDiario")
    if not issue_text:
        return None
    match = re.search(r"\bN[úu]m\.?\s*(\d+)\b", issue_text, re.I)
    return match.group(1) if match else None


def _iter_docm_announcements(text: str) -> list[dict[str, Any]]:
    block_pattern = re.compile(
        r'<div\s+class\s*=\s*"disp_(?P<id>\d+)"[^>]*>(?P<body>.*?)(?='
        r'<div\s+class\s*=\s*"disp_|<div\s+class\s*=\s*"organismo|'
        r'<div\s+class\s*=\s*"categoriaDiario|</body>)',
        re.I | re.S,
    )
    announcements = []
    for block in block_pattern.finditer(text):
        body = block.group("body")
        title = _first_docm_sumario_text(body)
        nid = _first_docm_nid(body)
        href = _first_docm_html_href(body)
        page = _first_class_block_text(body, "paginaDisposicion")
        category = _last_docm_context_text(text[: block.start()], "cabeceraCategoria")
        organism = _last_docm_context_text(text[: block.start()], "tituloOrganismo")
        if title and (nid or href):
            announcements.append(
                {
                    "entry_id": f"DOCM:{nid}" if nid else f"DOCM:{block.group('id')}",
                    "document_id": nid,
                    "title": title,
                    "href": href,
                    "summary": _join_title_parts(category, organism),
                    "page": page,
                    "has_pdf": "descargarArchivo.do" in body,
                }
            )
    return announcements


def _first_docm_sumario_text(text: str) -> str | None:
    value = _first_class_block_text(text, "sumario")
    if not value:
        return None
    return re.sub(r"\s*\[NID\s+\d{4}/\d+\]\s*$", "", value).strip()


def _first_docm_nid(text: str) -> str | None:
    match = re.search(r"\[NID\s+(\d{4}/\d+)\]", _strip_tags(text), re.I)
    return match.group(1) if match else None


def _first_docm_html_href(text: str) -> str | None:
    match = re.search(
        r"abreVentanaHtml\('(?P<href>verArchivoHtml\.do\?ruta=[^']+?\.html&amp;tipo=rutaDocm)'\)",
        text,
        re.I | re.S,
    )
    if not match:
        return None
    return html.unescape(match.group("href"))


def _last_docm_context_text(text: str, class_name: str) -> str | None:
    pattern = re.compile(
        rf'<[^>]+class\s*=\s*"[^"]*\b{re.escape(class_name)}\b[^"]*"[^>]*>'
        r"(?P<body>.*?)</[^>]+>",
        re.I | re.S,
    )
    matches = list(pattern.finditer(text))
    if not matches:
        return None
    return _normalize_text(_strip_tags(matches[-1].group("body")))


def _extract_bop_malaga_publication_date(text: str) -> str | None:
    match = re.search(r"Bolet[ií]n\s+del\s+(\d{2}/\d{2}/\d{4})", text, re.I)
    if match:
        return _ddmmyyyy_to_iso(match.group(1))
    long_match = re.search(
        r"Bolet[ií]n\s+Oficial\s+de\s+la\s+Provincia\s+de\s+M[aá]laga"
        r".*?\b(\d{1,2})\s+de\s+([a-záéíóú]+)\s+de\s+(\d{4})\b",
        text,
        re.I | re.S,
    )
    if not long_match:
        return None
    month = _SPANISH_MONTHS.get(long_match.group(2).lower())
    if not month:
        return None
    return date(int(long_match.group(3)), month, int(long_match.group(1))).isoformat()


def _bop_alicante_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    if "error" in payload:
        return []
    try:
        items = payload["boletin"]["bop"][0]["registro"]
    except (KeyError, IndexError, TypeError):
        return []
    if not isinstance(items, list):
        return []
    return [item for item in items if isinstance(item, dict)]


def _extract_bop_almeria_dtid(text: str) -> str:
    match = re.search(r"dt:'(?P<dtid>[^']+)'", text)
    if not match:
        raise HTMLMonitorError("BOP_ALMERIA ZK bootstrap did not expose dtid")
    return match.group("dtid")


def _extract_bop_almeria_public_window_uuid(text: str) -> str:
    window_uuids = re.findall(r"\['zul\.wnd\.Window','(?P<uuid>[^']+)'", text)
    if len(window_uuids) < 2:
        raise HTMLMonitorError("BOP_ALMERIA ZK bootstrap did not expose public window uuid")
    return window_uuids[1]


def _iter_bop_almeria_announcements(text: str) -> list[dict[str, str | None]]:
    item_pattern = re.compile(
        r"\['zul\.sel\.Listitem','[^']+'.*?(?=\s*\['zul\.sel\.Listitem'|\s*\['zul\.mesh\.Paging'|$)",
        re.S,
    )
    announcements = []
    for block in item_pattern.finditer(text):
        item = block.group(0)
        values = [_decode_zk_string(value) for value in _zk_property_values(item, "value")]
        content_match = re.search(r"content:'(?P<content>(?:\\'|[^'])*)'", item, re.S)
        if len(values) < 3 or not content_match:
            continue
        content = _decode_zk_string(content_match.group("content"))
        title = _first_bop_almeria_class_text(content, "resumen")
        if not title:
            continue
        summary = _join_title_parts(
            _first_bop_almeria_class_text(content, "seccion"),
            _first_bop_almeria_class_text(content, "linea1"),
            _first_bop_almeria_class_text(content, "linea2"),
        )
        announcements.append(
            {
                "issue_number": values[0],
                "published_date": values[1],
                "edict_number": values[-1],
                "title": title,
                "summary": summary,
            }
        )
    return announcements


def _zk_property_values(text: str, property_name: str) -> list[str]:
    return re.findall(rf"{re.escape(property_name)}:'((?:\\'|[^'])*)'", text, re.S)


def _decode_zk_string(value: str) -> str:
    text = value.replace("\\/", "/").replace("\\'", "'")
    text = re.sub(r"\\x([0-9a-fA-F]{2})", lambda match: chr(int(match.group(1), 16)), text)
    return html.unescape(text)


def _first_bop_almeria_class_text(text: str, class_name: str) -> str | None:
    values = _class_texts(text, class_name)
    return values[0] if values else None


def _first_json_value(item: dict[str, Any], key: str) -> str | None:
    value = item.get(key)
    if isinstance(value, list) and value:
        return _normalize_text(str(value[0]))
    if isinstance(value, str):
        return _normalize_text(value)
    return None


def _query_param_value(url: str, key: str) -> str | None:
    match = re.search(rf"[?&]{re.escape(key)}=([^&#]+)", html.unescape(url))
    return html.unescape(match.group(1)) if match else None


def _input_value(text: str, name: str) -> str | None:
    match = re.search(
        rf'<input[^>]+name="{re.escape(name)}"[^>]+value="(?P<value>[^"]*)"',
        text,
        re.I,
    )
    return html.unescape(match.group("value")) if match else None


def _ddmmyyyy_to_iso(value: str | None) -> str | None:
    if not value:
        return None
    try:
        day, month, year = value.split("/")
        return date(int(year), int(month), int(day)).isoformat()
    except (TypeError, ValueError):
        return None


def _yyyymmdd_to_iso(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return date(int(value[:4]), int(value[4:6]), int(value[6:8])).isoformat()
    except (TypeError, ValueError):
        return None


def _url_last_number(value: str) -> str | None:
    match = re.search(r"(\d+)(?:\D*)$", value)
    if not match:
        return None
    return match.group(1)


def _document_id_from_filename(value: str) -> str | None:
    path = html.unescape(value).split("?", 1)[0].rstrip("/")
    match = re.search(r"/?([^/]+?)\.(?:xml|html?|pdf)\b", path, re.I)
    return match.group(1) if match else None


def _bop_bizkaia_document_id_from_url(value: str) -> str | None:
    match = re.search(r"/([^/]+?)_(?:cas|eus)\.pdf\b", value, re.I)
    if not match:
        return None
    return match.group(1)


def _bop_avila_document_id_from_url(value: str) -> str | None:
    match = re.search(r"/([^/]+)\.pdf\b", value, re.I)
    if not match:
        return None
    document_id = match.group(1)
    if re.fullmatch(r"\d{2}-\d{2}-\d{4}", document_id):
        return None
    return document_id


def _bop_valladolid_document_id_from_url(value: str) -> str | None:
    match = re.search(r"/(BOPVA-A-\d{4}-\d+)\.pdf\b", value, re.I)
    if not match:
        return None
    return match.group(1).upper()


def _bop_pontevedra_document_id_from_url(value: str) -> str | None:
    match = re.search(r"/(\d{8,})(?:/|$|\.pdf\b)", value, re.I)
    if not match:
        return None
    return match.group(1)


def _bop_soria_document_id_from_url(value: str) -> str | None:
    match = re.search(r"fichero\.documentos_(\d+)", value, re.I)
    if not match:
        return None
    return html.unescape(match.group(1))


def _first_register_number(text: str) -> str | None:
    match = re.search(r"\bRegistre\s*:?\s*(\d{6,})\b", _strip_tags(text), re.I)
    if match:
        return match.group(1)
    return None


def _first_register_label_value(text: str, label: str) -> str | None:
    plain_text = _strip_tags(text)
    match = re.search(rf"\bN[uú]m\.?\s+{re.escape(label)}:\s*([0-9]+/[0-9]+)", plain_text, re.I)
    if match:
        return match.group(1)
    return None


def _first_bop_sevilla_document_id(text: str) -> str | None:
    match = re.search(r"\bBOP-(?:SE|GRA)-\d{4}-\d+\b", _strip_tags(text), re.I)
    if match:
        return match.group(0)
    return None


def _first_datetime_value(text: str) -> str | None:
    match = re.search(r'datetime="(\d{4}-\d{2}-\d{2})"', text, re.I)
    if match:
        return match.group(1)
    return None


def _first_date_text(text: str) -> str | None:
    match = re.search(r"\b\d{2}/\d{2}/\d{4}\b", _strip_tags(text))
    if match:
        return match.group(0)
    return None


def _first_value(values: list[str | None]) -> str | None:
    for value in values:
        if value:
            return value
    return None


def _first_class_block_text(text: str, class_name: str) -> str | None:
    match = re.search(
        rf"""<[^>]+class\s*=\s*["'][^"']*\b{re.escape(class_name)}\b[^"']*["'][^>]*>"""
        r"(?P<body>.*?)(?:<span\b|</span>|</p>|</div>)",
        text,
        re.I | re.S,
    )
    if not match:
        return None
    return _normalize_text(_strip_tags(match.group("body")))


def _class_texts(text: str, class_name: str) -> list[str]:
    pattern = re.compile(
        rf"""<[^>]+class\s*=\s*["'][^"']*\b{re.escape(class_name)}\b[^"']*["'][^>]*>"""
        r"(?P<body>.*?)</[^>]+>",
        re.I | re.S,
    )
    return [_normalize_text(_strip_tags(match.group("body"))) for match in pattern.finditer(text)]


def _first_id_block_text(text: str, id_prefix: str) -> str | None:
    match = re.search(
        rf'<[^>]+id="{re.escape(id_prefix)}[^"]*"[^>]*>(?P<body>.*?)</[^>]+>',
        text,
        re.I | re.S,
    )
    if not match:
        return None
    return _normalize_text(_strip_tags(match.group("body")))


def _first_id_container(text: str, element_id: str) -> str | None:
    match = re.search(
        rf'<div[^>]+id="{re.escape(element_id)}"[^>]*>(?P<body>.*?)</body>',
        text,
        re.I | re.S,
    )
    if match:
        return match.group("body")
    match = re.search(
        rf'<div[^>]+id="{re.escape(element_id)}"[^>]*>(?P<body>.*)',
        text,
        re.I | re.S,
    )
    return match.group("body") if match else None


def _first_heading_text(text: str) -> str | None:
    match = re.search(r"<h[1-6]\b[^>]*>(?P<title>.*?)</h[1-6]>", text, re.I | re.S)
    if not match:
        return None
    return _normalize_text(_strip_tags(match.group("title")))


def _join_title_parts(*parts: str | None) -> str | None:
    normalized_parts = [_normalize_text(part) for part in parts if _normalize_text(part)]
    if not normalized_parts:
        return None
    return " - ".join(normalized_parts)


def _label_value(text: str, label: str) -> str | None:
    plain = _strip_tags(text)
    label_pattern = re.escape(label).replace("º", r"(?:º|o)")
    match = re.search(
        rf"{label_pattern}\s*:\s*(?P<value>.*?)(?=(?:Procedencia|Organismo|Extracto|N[ºo]\s+de\s+referencia)\s*:|$)",
        plain,
        re.I | re.S,
    )
    return _normalize_text(match.group("value")) if match else None


def _long_spanish_date_to_iso(text: str) -> str | None:
    match = re.search(
        r"\b(\d{1,2})\s+de\s+([a-záéíóú]+)\s+de\s+(\d{4})\b",
        text,
        re.I,
    )
    if not match:
        return None
    month = _SPANISH_MONTHS.get(match.group(2).lower())
    if not month:
        return None
    return date(int(match.group(3)), month, int(match.group(1))).isoformat()


def _long_date_pattern(target_date: str) -> re.Pattern[str]:
    parsed = date.fromisoformat(validate_html_monitor_date(target_date))
    month_names = [name for name, number in _SPANISH_MONTHS.items() if number == parsed.month]
    month_pattern = "|".join(re.escape(name) for name in month_names)
    return re.compile(rf"\b{parsed.day}\s+de\s+(?:{month_pattern})\s+de\s+{parsed.year}\b", re.I)


def _strip_tags(value: str) -> str:
    return re.sub(r"<[^>]+>", " ", html.unescape(value))


_SPANISH_MONTHS = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "maio": 5,
    "junio": 6,
    "xuno": 6,
    "xu\u00f1o": 6,
    "julio": 7,
    "xullo": 7,
    "agosto": 8,
    "septiembre": 9,
    "setiembre": 9,
    "setembro": 9,
    "octubre": 10,
    "outubro": 10,
    "noviembre": 11,
    "novembro": 11,
    "diciembre": 12,
    "decembro": 12,
    "xaneiro": 1,
    "febreiro": 2,
}


def _has_class(value: str | None, class_name: str) -> bool:
    return bool(value and class_name in value.split())


def _normalize_text(value: str | None) -> str:
    text = html.unescape(value or "")
    text = " ".join(text.split())
    return re.sub(r"\s+([.,;:])", r"\1", text)


def _coerce_page_bytes(raw_page: bytes | str) -> bytes:
    if isinstance(raw_page, bytes):
        return raw_page
    return raw_page.encode("utf-8")
