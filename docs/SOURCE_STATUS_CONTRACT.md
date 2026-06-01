# Source Status Contract

This contract defines the downstream-facing meaning of official-source registry, monitor,
discovery, candidate, and evidence states.

It is a control-plane contract. It does not change runtime behavior, source registry entries,
monitors, parsers, candidate creation, evidence generation, artifact download, downstream writes,
Hermes, systemd, VPS state, or production data.

Current baseline for this contract:

```text
registered sources: 65
metadata_adapter_validated: 9
monitor_validated: 50
inventory_only: 6
RSS/Atom discovery sources: 12
API discovery monitor sources: 5
HTML discovery monitor sources: 37
blocked_vps=true: BOP_CUENCA, BOP_SALAMANCA, BOP_ZARAGOZA
pending_relay=true: BOP_CUENCA, BOP_SALAMANCA, BOP_ZARAGOZA
candidate_creation_allowed=false: 65
evidence_grade_allowed=false: 65
data/rss_monitor present: false
data/html_monitor present: false
BOP_ALICANTE runtime health: degraded/manual-review
writes: disabled unless a future explicit write task authorizes them
```

## Contract Boundaries

The executable registry is:

```text
config/sources.yaml
```

The registry answers whether an official source is known, which public access paths are declared,
and which control-plane capabilities are currently allowed. It is not a product-readiness list.

Discovery monitors are metadata-only unless a separate source-specific evidence adapter and task
contract say otherwise. Monitor output, when explicitly written, is discovery data, not candidate
data and not evidence-grade data.

Downstream consumers must treat `official-sources` as a read-only upstream. A future write contract
must explicitly name the target repository, target data model, source scope, write command, review
gate, rollback path, and acceptance criteria before any downstream write is allowed.

## State Definitions

### Registered Source

A source is registered when it has a `source_code` entry in `config/sources.yaml`.

Downstream consumers MAY infer:

- the project tracks the source as an official-source inventory item;
- the source has declared metadata such as jurisdiction, landing URL, access methods, limitations,
  and safety flags;
- the source can be queried through read-only registry and coverage tools.

Downstream consumers MUST NOT infer:

- the source is monitorable;
- the source is runtime-healthy;
- the source has semantic extraction;
- the source can create candidates;
- the source is evidence-grade;
- the source is product-ready.

### Source Registered vs Source Product-Ready

`source registered` means the source exists in the official registry. `source product-ready` would
mean a downstream product has separately approved source semantics, staging behavior, review gates,
candidate rules, evidence rules, and publication constraints.

No current registry state by itself means product-ready.

For this baseline, no source is product-ready merely because it is one of the 65 registered sources.
Product use requires explicit product-side review.

### Registry Status vs Runtime Health

Registry fields describe declared control-plane capability. Runtime health describes whether a
specific monitor or operational check is currently passing.

These are separate axes.

For example, `BOP_ALICANTE` remains registered and monitor-capable in the registry, but its current
runtime health is `degraded/manual-review` due resolver-dependent DNS instability. It must not be
counted in an all-green source claim until normal DNS/live preview recovers and a later task records
that recovery.

### `healthy`

`healthy` is a runtime-health label, not a registry `operational_status` value.

A source or source set may be called healthy only when the specific runtime check being cited passed
under the stated scope, date, and command constraints. A healthy monitor result means that monitor
path was reachable and returned expected metadata for that check.

Downstream consumers MUST NOT infer from `healthy`:

- candidate creation permission;
- evidence-grade permission;
- full semantic extraction;
- downstream automation permission;
- product readiness;
- all-source success unless every registered source in the claim's scope passed.

Downstream consumers must never claim "all sources green" while any registered source in that claim's
scope is `degraded/manual-review`.

### `degraded/manual-review`

`degraded/manual-review` is a runtime-health overlay for a source that remains known but should not
be treated as operationally green.

Downstream consumers MAY infer:

- the project is tracking a specific source-level issue;
- the source may still be useful for registry awareness, upstream metadata, or manual inspection;
- automated downstream behavior should treat the source as needing review.

Downstream consumers MUST NOT infer:

- the project is broken;
- the source should be removed from the registry;
- the source should be reverted to `inventory_only`;
- product automation is allowed;
- a later source expansion may ignore the degraded state.

Current degraded/manual-review source:

```text
BOP_ALICANTE
reason: resolver-dependent DNS instability for sede.diputacionalicante.es
```

### `inventory_only`

`inventory_only` is a registry `operational_status`.

It means the source is known and retained as official-source inventory, but no operational discovery
monitor is validated for it in the current registry contract.

Downstream consumers MAY infer:

- the source exists in the official registry;
- the source may be useful for upstream metadata, source planning, or manual inspection;
- the source may become a future monitor candidate only after a separate source-specific task.

Downstream consumers MUST NOT infer:

- an operational monitor exists;
- runtime health has been checked;
- metadata discovery is available;
- semantic extraction is safe;
- candidates or evidence-grade records may be created.

### `monitor_validated`

`monitor_validated` is a registry `operational_status`.

It means the source has a validated metadata-only discovery path in the project control plane. The
path may be RSS/Atom, API, or HTML depending on the source. It does not imply candidate creation,
evidence-grade output, semantic classification, artifact download, or product automation.

Downstream consumers MAY infer:

- the source can be monitored or previewed through the applicable source-specific discovery command;
- output records, when produced, are discovery metadata;
- monitor output should carry non-candidate and non-evidence status unless another explicit task
  changes that contract.

Downstream consumers MUST NOT infer:

- downstream product automation is allowed;
- candidates may be created;
- evidence-grade records may be created;
- all runtime checks are currently healthy;
- all official documents are semantically parsed.

### `metadata_adapter_validated`

`metadata_adapter_validated` is a registry `operational_status`.

It means a source has a source-specific metadata ingestion adapter validated for its current
contract. This is stronger than discovery inventory but still bounded by the adapter's documented
scope.

Downstream consumers MAY infer:

- the source can produce validated upstream metadata through its adapter path;
- the source may support read-only citation, integrity, or evidence-staging workflows when those
  workflows are separately documented for that source.

Downstream consumers MUST NOT infer:

- full semantic extraction is safe;
- candidate creation is allowed;
- evidence-grade use is allowed;
- downstream product publication is allowed;
- the source is product-ready without product-side review.

### `monitor_support=available`

`monitor_support=available` means monitor support is declared available for the source. It is a
capability flag, not a health verdict.

Downstream consumers MAY infer:

- a monitor-capable access route is declared for the source;
- registry and MCP tools may classify the source as monitorable.

Downstream consumers MUST NOT infer:

- the latest live preview passed;
- the source is healthy;
- candidate creation is allowed;
- evidence-grade use is allowed;
- downstream product automation is allowed.

### Discovery Monitor

A discovery monitor is a metadata-only reader for a source access path such as RSS/Atom, API, or
HTML. It is designed to discover publication metadata, not to make product decisions.

Discovery monitor records must be interpreted as:

```text
classification_status=unclassified
candidate_status=not_candidate
evidence_status=not_evidence
```

unless a future explicit contract changes those values for a named source and workflow.

Discovery monitor output paths are used only when writes are explicitly requested:

```text
data/rss_monitor/<source_code>/<YYYY-MM-DD>/rss_discovery.jsonl
data/api_monitor/<source_code>/<YYYY-MM-DD>/api_discovery.jsonl
data/html_monitor/<source_code>/<YYYY-MM-DD>/html_discovery.jsonl
```

For this baseline, `data/rss_monitor` and `data/html_monitor` are absent and no writes are enabled.

### `metadata-only`

`metadata-only` means the project may read or store index-level publication metadata such as title,
identifier, date, source URL, section, and discovery status.

Downstream consumers MAY infer:

- the source may be useful as upstream metadata;
- the source can support awareness, audit, or manual review workflows;
- the metadata may help decide whether a future source-specific adapter is worth building.

Downstream consumers MUST NOT infer:

- full semantic extraction is safe;
- official text has been parsed;
- artifact evidence has been downloaded;
- legal or eligibility meaning has been classified;
- candidate creation or evidence-grade use is allowed.

### `evidence_adapter`

`evidence_adapter` is an explicit boolean registry field. It must be treated independently from
monitor status.

`evidence_adapter=true` means code/docs include an evidence-oriented adapter path for that source
family. It still does not authorize downstream product automation by itself.

`evidence_adapter=false` means the source must not be used as evidence-grade input unless a future
task adds and validates an explicit evidence adapter.

### `candidate_creation_allowed`

`candidate_creation_allowed` is an explicit boolean registry field and permission gate.

`candidate_creation_allowed=false` means official-sources must not create source candidates from
that source through the source-coverage or discovery surface.

For this baseline:

```text
candidate_creation_allowed=false: 65/65
```

Downstream consumers MUST NOT infer candidate permission from registry presence, monitor health,
metadata-only discovery, `monitor_validated`, or `monitor_support=available`.

### `evidence_grade_allowed`

`evidence_grade_allowed` is an explicit boolean registry field and permission gate.

`evidence_grade_allowed=false` means the source must not be treated as evidence-grade through the
source-coverage or discovery surface.

For this baseline:

```text
evidence_grade_allowed=false: 65/65
```

Downstream consumers MUST NOT infer evidence-grade permission from registry presence, monitor
health, metadata-only discovery, `monitor_validated`, `monitor_support=available`, or
`evidence_adapter=true`.

## Consumer Guidance

Recommended downstream behavior:

- Treat `official-sources` as a read-only upstream.
- Require explicit product-side review before candidate creation.
- Require an explicit evidence adapter and evidence-grade permission before evidence-grade use.
- Treat `degraded/manual-review` as usable only for inventory awareness or manual inspection.
- Never claim "all sources green" while any registered source is `degraded/manual-review`.
- Preserve source code, official URL, citation metadata, integrity metadata, and safety flags.
- Keep downstream staging, review, approval, publication, notification, ranking, and product
  automation outside this repository.

## Explicit Non-Inferences

Downstream consumers MUST NOT infer:

- registered source means evidence-grade;
- healthy monitor means candidate creation is allowed;
- metadata-only means full semantic extraction is safe;
- `inventory_only` means operational monitor exists;
- `degraded/manual-review` means the project is broken;
- `monitor_validated` means downstream product automation is allowed;
- `monitor_support=available` means latest runtime health is green;
- source discovery records are product candidates;
- source discovery records are evidence-grade records;
- writes are allowed without a future explicit write contract.
