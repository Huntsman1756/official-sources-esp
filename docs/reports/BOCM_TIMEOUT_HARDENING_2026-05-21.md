# BOCM Timeout Hardening

Date: 2026-05-21

## Summary

`TASK-AUTO-BOCM-003B` hardened BOCM metadata ingestion against transient read timeouts.

The previous controlled backfill stopped safely on `2026-04-22` after two read timeouts. The
failure was not a parser problem and was not a no-publication condition.

## Observed Failure

Previous run:

```text
2026-04-21: success, 60 documents
2026-04-22: failed, read timeout
2026-04-22 retry: failed, read timeout
```

The ingestion run preserved:

```text
status=failed
last_http_status=200
error_message=The read operation timed out
```

The likely cause was a slow or stalled BOCM response while reading official metadata. The adapter
already reused the BOE request policy for HTTP status retries, but `httpx` read timeouts were
raised as exceptions and were not retried by the BOCM ingestion path.

## Retry and Timeout Strategy

The BOCM metadata path now uses:

```text
connect timeout: 10 seconds
read timeout: 90 seconds
write timeout: 30 seconds
pool timeout: 10 seconds
timeout retries: 3
backoff: 1s, 2s, 4s, capped at 10s
```

Timeout retries are finite and conservative. A repeated timeout remains:

```text
status=failed
```

It is not classified as:

```text
no_publication
```

The ingestion run records `retry_count`, `throttle_triggered`, `last_http_status` when available,
and a clear timeout error message.

## CLI Diagnostics

`ingest-bocm-date` output now includes `error_message` for failed BOCM runs, while preserving the
existing fields:

```text
status
issue_identifier
documents_fetched
documents_new
documents_updated
retry_count
throttle_triggered
last_http_status
source_snapshot_hash
error_message
```

## Tests Added

Added coverage for:

- transient read timeout followed by success;
- repeated read timeout recorded as failed;
- timeout not classified as no-publication;
- retry count recorded;
- successful retry stores documents once;
- no PDF document files created;
- no source candidates created;
- CLI timeout diagnostics.

## Live Smoke

Controlled live smoke:

```text
date=2026-04-22
environment=local
```

Result:

```text
status=success
issue_identifier=bocm-20260422-94
documents_fetched=82
documents_new=82
retry_count=0
last_http_status=200
pdf_document_files=0
source_candidates=0
artifact_download_attempts=0
```

No PDFs were downloaded. No candidates were created. No downstream project was touched.

## Backfill Resume Decision

The 30-day BOCM backfill can resume only after this code is deployed on the VPS and a scoped VPS
smoke for `2026-04-22` passes.

Recommended next task:

```text
TASK-AUTO-BOCM-003C — Resume BOCM 30-day metadata backfill from 2026-04-22
```

First step of that task should be a VPS smoke for:

```text
2026-04-22
```

If that smoke fails again, stop and document the endpoint/network blocker. Do not move to BOCM
candidate dry-run until the metadata window is closed.
