from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

import httpx

from official_sources.source_registry import get_source

FeedFetcher = Callable[[str], bytes | str]

ATOM_NS = "{http://www.w3.org/2005/Atom}"
DC_NS = "{http://purl.org/dc/elements/1.1/}"


class RSSMonitorError(ValueError):
    pass


@dataclass(frozen=True)
class FeedParseResult:
    feed_format: str
    raw_feed_hash: str
    records: list[dict[str, Any]]


def validate_monitor_date(value: str) -> str:
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError as exc:
        raise RSSMonitorError("--date must use YYYY-MM-DD format") from exc


def build_entry_hash(
    *,
    source_code: str,
    published_at: str | None,
    official_url: str | None,
    entry_id: str | None,
    title: str | None,
) -> str:
    if official_url:
        hash_input = f"{source_code}{published_at or ''}{official_url}"
        return hashlib.sha256(hash_input.encode()).hexdigest()
    return hashlib.sha256(f"{source_code}{entry_id or ''}{title or ''}".encode()).hexdigest()


def build_rss_monitor_output_path(output_root: Path, source_code: str, target_date: str) -> Path:
    return output_root / source_code / target_date / "rss_discovery.jsonl"


def select_feed_access_method(source: dict[str, Any]) -> dict[str, Any]:
    for access_method in source.get("access_methods", []):
        is_feed = access_method.get("type") in {"rss", "atom"}
        if is_feed and access_method.get("status") == "validated":
            if not str(access_method.get("url", "")).strip():
                break
            return access_method
    raise RSSMonitorError(
        f"{source.get('source_code', 'source')} does not have a validated rss/atom access method"
    )


def monitor_source_feed(
    source: dict[str, Any],
    *,
    fetcher: FeedFetcher | None = None,
    target_date: str,
    limit: int | None = None,
) -> FeedParseResult:
    target_date = validate_monitor_date(target_date)
    if limit is not None and limit < 1:
        raise RSSMonitorError("--limit must be greater than zero")

    access_method = select_feed_access_method(source)
    source_code = source["source_code"]
    feed_url = access_method["url"]
    raw_feed = _coerce_feed_bytes((fetcher or fetch_feed)(feed_url))
    raw_feed_hash = hashlib.sha256(raw_feed).hexdigest()
    monitor_run_id = hashlib.sha256(
        f"{source_code}{feed_url}{target_date}{raw_feed_hash}".encode()
    ).hexdigest()[:16]
    result = parse_feed(
        raw_feed,
        source_code=source_code,
        feed_url=feed_url,
        discovered_at=f"{target_date}T00:00:00Z",
        monitor_run_id=monitor_run_id,
    )
    if limit is None:
        return result
    return FeedParseResult(
        feed_format=result.feed_format,
        raw_feed_hash=result.raw_feed_hash,
        records=result.records[:limit],
    )


def monitor_source_code(
    source_code: str,
    *,
    fetcher: FeedFetcher | None = None,
    target_date: str,
    limit: int | None = None,
) -> FeedParseResult:
    return monitor_source_feed(
        get_source(source_code),
        fetcher=fetcher,
        target_date=target_date,
        limit=limit,
    )


def parse_feed(
    raw_feed: bytes | str,
    *,
    source_code: str,
    feed_url: str,
    discovered_at: str,
    monitor_run_id: str,
) -> FeedParseResult:
    raw_bytes = _coerce_feed_bytes(raw_feed)
    raw_feed_hash = hashlib.sha256(raw_bytes).hexdigest()
    try:
        root = ElementTree.fromstring(raw_bytes)
    except ElementTree.ParseError as exc:
        raise RSSMonitorError(f"RSS/Atom feed parse failed: {exc}") from exc

    feed_format = _detect_feed_format(root)
    if feed_format == "rss":
        entries = _rss_entries(root)
    elif feed_format == "atom":
        entries = _atom_entries(root)
    else:
        entries = []

    records = [
        _build_record(
            source_code=source_code,
            feed_url=feed_url,
            feed_format=feed_format,
            raw_feed_hash=raw_feed_hash,
            discovered_at=discovered_at,
            monitor_run_id=monitor_run_id,
            entry=entry,
        )
        for entry in entries
    ]
    return FeedParseResult(feed_format=feed_format, raw_feed_hash=raw_feed_hash, records=records)


def write_jsonl(records: list[dict[str, Any]], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = "".join(
        f"{json.dumps(record, ensure_ascii=False, sort_keys=True)}\n" for record in records
    )
    output_path.write_text(payload, encoding="utf-8")
    return output_path


def fetch_feed(url: str) -> bytes:
    with httpx.Client(follow_redirects=True, timeout=30.0) as client:
        response = client.get(
            url,
            headers={
                "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml"
            },
        )
        response.raise_for_status()
        return response.content


def _build_record(
    *,
    source_code: str,
    feed_url: str,
    feed_format: str,
    raw_feed_hash: str,
    discovered_at: str,
    monitor_run_id: str,
    entry: dict[str, str | None],
) -> dict[str, Any]:
    warnings = []
    if not entry.get("official_url"):
        warnings.append("entry_hash_fallback_missing_official_url")
    return {
        "source_code": source_code,
        "feed_url": feed_url,
        "feed_format": feed_format,
        "entry_id": entry.get("entry_id"),
        "title": entry.get("title"),
        "published_at": entry.get("published_at"),
        "updated_at": entry.get("updated_at"),
        "official_url": entry.get("official_url"),
        "summary": entry.get("summary"),
        "raw_feed_hash": raw_feed_hash,
        "entry_hash": build_entry_hash(
            source_code=source_code,
            published_at=entry.get("published_at"),
            official_url=entry.get("official_url"),
            entry_id=entry.get("entry_id"),
            title=entry.get("title"),
        ),
        "discovered_at": discovered_at,
        "monitor_run_id": monitor_run_id,
        "classification_status": "unclassified",
        "evidence_status": "not_evidence",
        "candidate_status": "not_candidate",
        "warnings": warnings,
    }


def _detect_feed_format(root: ElementTree.Element) -> str:
    tag = _strip_namespace(root.tag)
    if tag == "rss":
        return "rss"
    if tag == "feed" and root.tag.startswith(ATOM_NS):
        return "atom"
    return "unknown"


def _rss_entries(root: ElementTree.Element) -> list[dict[str, str | None]]:
    channel = root.find("channel")
    if channel is None:
        return []
    entries = []
    for item in channel.findall("item"):
        link = _text(item, "link")
        guid = _text(item, "guid")
        pub_date = _text(item, "pubDate") or _text(item, f"{DC_NS}date")
        entries.append(
            {
                "entry_id": guid or link,
                "title": _text(item, "title"),
                "published_at": pub_date,
                "updated_at": _text(item, f"{DC_NS}date") if not pub_date else None,
                "official_url": link,
                "summary": _text(item, "description"),
            }
        )
    return entries


def _atom_entries(root: ElementTree.Element) -> list[dict[str, str | None]]:
    entries = []
    for entry in root.findall(f"{ATOM_NS}entry"):
        link_element = entry.find(f"{ATOM_NS}link")
        link = link_element.get("href") if link_element is not None else None
        published = _text(entry, f"{ATOM_NS}published")
        updated = _text(entry, f"{ATOM_NS}updated") or _text(entry, f"{DC_NS}date")
        entries.append(
            {
                "entry_id": _text(entry, f"{ATOM_NS}id") or link,
                "title": _text(entry, f"{ATOM_NS}title"),
                "published_at": published or updated,
                "updated_at": updated if published else None,
                "official_url": link,
                "summary": _text(entry, f"{ATOM_NS}summary") or _text(entry, f"{ATOM_NS}content"),
            }
        )
    return entries


def _text(element: ElementTree.Element, path: str) -> str | None:
    found = element.find(path)
    if found is None or found.text is None:
        return None
    value = found.text.strip()
    return value or None


def _strip_namespace(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _coerce_feed_bytes(raw_feed: bytes | str) -> bytes:
    if isinstance(raw_feed, bytes):
        return raw_feed
    return raw_feed.encode("utf-8")
