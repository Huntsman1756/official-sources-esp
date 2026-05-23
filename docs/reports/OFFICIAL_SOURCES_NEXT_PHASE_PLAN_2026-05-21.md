# Official Sources Next Phase Plan - 2026-05-21

## Scope

This report records the next operational phase plan for `official-sources` after the BOE, BOJA,
DOGV, BOCYL, BOCM, BDNS, BOPV, provincial, and downstream planning work available on 2026-05-21.

This is a documentation and planning task only.

No code was implemented. No database was touched. No VPS connection was made. No candidates were
created. No artifacts were downloaded. No downstream project was touched.

## Current Source Status

| Source family | Current status | Evidence base | Next posture |
| --- | --- | --- | --- |
| BOE | Mature Tier 1 source. Daily ingestion, artifact handling, citation/integrity metadata, candidate review, and downstream evidence export are validated. | BOE 6-month pilot produced 75 candidates, 13 selected evidence reviews, 5 accepted downstream pilot candidates, and 0 downstream publications. | Keep as the reference source for downstream contract validation and controlled evidence exports. |
| BOJA | First validated autonomous/statutory source. Metadata ingestion, candidate creation, detail enrichment, scoped PDF download, evidence review, and pilot closure are complete. | 30-day pilot produced 1500 documents, 25 candidates, 10 PDFs, 4 accepted downstream pilot candidates, and 0 downstream writes. | Keep autonomous imports review-gated; do not import automatically downstream. |
| DOGV | Metadata adapter, 30-day backfill, candidate batch, evidence download/review, and downstream-ready export are complete. | 10 accepted DOGV evidence JSON files exported: 9 for EduAyudas and 1 for `la-ayuda`; schema review found them usable for preview/import after mapping review. | Continue staging/mapping work separately for EduAyudas and `la-ayuda`; no publication. |
| BOCYL | Metadata adapter and 30-day backfill are complete. Candidate profile was refined from broad `la-ayuda` overmatch to `bocyl-ayudas`. | 30-day window has 773 stored documents. Generic `la-ayuda` matched 34.28%; `bocyl-ayudas` reduced this to 21 matches / 2.72% in dry-run with 0 candidates created. | Run a small guarded candidate batch only after backup and supervisor approval. |
| BOCM | Metadata adapter exists, but the 30-day backfill is blocked by repeated VPS timeout on 2026-05-06. | Local smoke succeeded for the large XML path, but VPS retry still failed in `search_day`; BOCM has 982 stored documents and no PDF/candidate path should start. | Keep paused until a cooldown single-date retry succeeds or the blocker is explicitly accepted. |
| BDNS | Metadata-only grant-call adapter MVP and hardening are complete for `convocatorias`. BDNS is modeled as a primary grants registry, not a bulletin. | Latest/search/detail commands exist with bounded pagination, parser hardening, raw JSON hashes, no concessions, no candidates, no artifact downloads, and no downstream writes. | Run latest ingestion as the next operational source task; keep concessions deferred. |
| BOPV/EHAA | Audit-only P1 autonomous candidate with official REST/OpenAPI surface, stable administrative-act IDs, and direct artifact links. | Northern audit ranks BOPV/EHAA as the cleanest API-led northern source and a strong next MVP candidate after BOCYL. | Run BOPV-001 audit/fixture discovery first; proceed to metadata MVP only if fixtures confirm API semantics. |
| Provincials | Strategy-only audit completed. Provincial BOPs are heterogeneous and should not use one generic adapter first. | BOE seed list and sample deep checks identify Barcelona, A Coruna, Malaga, Bizkaia, and Valencia as higher-signal metadata monitor candidates. | Keep as a separate strategy stream; design metadata monitor before any adapter or candidate work. |

## Current Downstream Status

| Downstream | Current status | Operational boundary | Next posture |
| --- | --- | --- | --- |
| EduAyudas | Validated local/dev evidence consumer. BOE evidence path and DOGV export shape are usable for staging-oriented preview/import after mapping review. | Local/dev fallback is not a production pattern. Current product QA work belongs in the EduAyudas repo and should not be continued from this platform branch. | Continue only through explicit downstream tasks with preview/staging first, then candidate/draft review gates. |
| la-ayuda | BOE pilot validated non-public draft/internal review. DOGV has 1 staged export file and schema review says it is usable for a single preview import after mapping review. | `la-ayuda` still needs robust evidence/candidate staging foundation before broader imports. No public route or publication is authorized. | Continue DOGV/`la-ayuda` staging after foundation/mapping confirmation; keep publication out of scope. |
| subvenciones | BDNS is likely the primary source family for this product. BOE/BOJA/DOGV/BOCM can be supporting official context but should not replace a BDNS-first model. | Needs grant-specific staging, beneficiary/issuer model, call versus award distinction, and explicit publication/deadline checks. | Use BDNS latest/search metadata first; defer candidate creation until profiles and staging are reviewed. |
| oposiciones2.0 | Likely needs BOE, autonomous bulletins, and selected provincial/local bulletins. Candidate semantics differ from aid/subsidy projects. | Needs its own foundation because deadlines, territorial scope, call types, and review rules differ. | Wait for source metadata coverage and provincial monitor strategy; do not reuse aid profiles directly. |

## Recommended Next Operational Tasks

| Priority | Task | Scope | Guardrails |
| --- | --- | --- | --- |
| 1 | `TASK-AUTO-BOCYL-005 - BOCYL guarded candidate batch` | Create a small explicit candidate batch from stored BOCYL metadata using `bocyl-ayudas`. | Backup first; supervisor required; small `--limit`; candidates stay `human_review_required`; no artifact downloads; no downstream writes. |
| 2 | `TASK-BDNS-003 - BDNS latest ingestion` | Run bounded latest `convocatorias` ingestion now that adapter hardening is complete. | Metadata only; no concessions; no candidates; no artifacts; no downstream writes; inspect diagnostics and hashes. |
| 3 | `TASK-AUTO-BOPV-001 - BOPV/EHAA audit and fixture discovery` | Pin API pagination/filter semantics, date/month behavior, language suffixes, artifact links, and raw JSON hash strategy. | Audit/fixtures first. If clean, plan a separate metadata-only MVP; do not skip straight to candidates. |
| 4 | `TASK-AUTO-DOGV-012 / downstream-specific continuation` | Continue DOGV export staging with EduAyudas and `la-ayuda` mapping review. | Each downstream separately; preview before write; no automatic publication; no raw PDF/XML/HTML leakage. |
| 5 | `TASK-AUTO-BOCM-003G - cooldown retry or pause decision` | Retry only the blocked 2026-05-06 search/ingest smoke after cooldown, or formally keep BOCM paused. | Single-date only; no backfill resume unless success; no candidate dry-run while metadata window is incomplete. |

## Risks And Constraints

| Risk | Why it matters | Required control |
| --- | --- | --- |
| VPS operations are single-agent only | Concurrent operators can mutate the same deployment, database, or evidence exports. | One supervisor/agent owns VPS operations at a time; docs/audits can run elsewhere. |
| Candidate creation requires backup | Candidate writes change review queues and can affect downstream export eligibility. | Take and verify backup before any `--write` candidate task; record before/after counts. |
| Downstream writes must stay separated | `official-sources` is evidence infrastructure, not a publisher or downstream CMS. | Export, preview import, staging write, candidate creation, draft creation, and publication remain separate tasks. |
| BDNS concesiones are deferred | Awards can include beneficiary/privacy/retention concerns and different semantics from calls. | Keep TASK-BDNS-003 to `convocatorias`; require a separate privacy/retention review before concessions. |
| Provincial strategy is separate | Provincial BOP systems are technically heterogeneous and easy to overgeneralize. | Build inventory and metadata monitor design before adapters, candidates, or oposiciones filters. |
| BOCM is externally blocked from VPS path | Repeated timeouts can create noisy failed ingestion rows and incomplete metadata windows. | Keep BOCM paused unless the single-date retry succeeds or the blocker is explicitly accepted. |

## Suggested Parallelization Model

| Workstream | Parallelization | Supervisor role |
| --- | --- | --- |
| Docs/audits | Can run in parallel across independent sources such as BOPV, BOR, provincial monitor design, and downstream mapping reviews. | Merge reports, resolve naming/status conflicts, and select the next serial operation. |
| Local docs/planning cleanup | Can run in parallel if each agent owns distinct files or report scopes. | Prevent duplicate roadmap/status documents and consolidate final recommendations. |
| VPS and DB operations | Must be serial. This includes ingestion, backfills, candidate writes, evidence review decisions, export generation, and backup/restore checks. | Assign one active operator, require pre/post counts, and pause other VPS tasks. |
| Downstream project writes | Must be serial per downstream and separated from platform source operations. | Confirm target branch, staging model, preview result, and publication gate before any write. |

## Phase Boundary

The next phase should favor controlled source operations over broad expansion:

1. Run BOCYL-005 only with backup and a small candidate cap.
2. Run BDNS-003 latest ingestion as metadata-only `convocatorias`.
3. Keep BOCM paused unless the single-date retry succeeds.
4. Continue DOGV downstream staging only through preview/mapping tasks.
5. Start BOPV as audit/fixture work, not candidate or backfill work.
6. Keep provincials as a separate monitor-design stream.

The invariant remains:

```text
official evidence import is not approval and must never publish
```
