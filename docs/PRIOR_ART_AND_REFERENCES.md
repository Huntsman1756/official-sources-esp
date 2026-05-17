# Prior Art And References

This review is inspiration only. None of these repositories are canonical sources for `official-sources`.

## legalize-dev/legalize-es

Repository: <https://github.com/legalize-dev/legalize-es>

- What it does: Spanish legislation as a Git repository, with one law per Markdown file and reform history as commits.
- Relevance: strong inspiration for future Git/Markdown export and diffability.
- Reuse ideas: jurisdiction folders, frontmatter metadata, historical reform commits, one document per file.
- Do not reuse: source-of-truth role. BOE remains canonical.
- License: not clearly detected from the repository page during this review.
- Dependency concerns: should not become a runtime dependency.
- Security concerns: transformed text must not replace official raw artifacts.
- Suitability: architecture and methodology reference, not primary source.

## bukosabino/justicio

Repository: <https://github.com/bukosabino/justicio>

- What it does: BOE question-answering assistant using RAG, embeddings, vector database, daily ETL, traces, and LLM answers.
- Relevance: useful future RAG/search reference.
- Reuse ideas: chunking concepts, daily ETL, trace records, hybrid search considerations.
- Do not reuse: RAG as MVP architecture or tests as sufficient audit validation.
- License: MIT.
- Dependency concerns: LangChain, Qdrant, embeddings, and LLM dependencies are out of MVP scope.
- Security concerns: generated answers can overstate legal certainty.
- Suitability: RAG/search reference only.

## hpalacio/leyes

Repository: <https://github.com/hpalacio/leyes>

- What it does: Spanish Constitution represented as source code in Git.
- Relevance: conceptual inspiration for law as readable text and reviewable diffs.
- Reuse ideas: one sentence per line, commit dates aligned to BOE publication dates.
- Do not reuse: narrow scope as full architecture.
- License: CC-BY-SA-4.0.
- Dependency concerns: none for MVP.
- Security concerns: manual formatting cannot replace canonical ingestion.
- Suitability: methodology reference.

## arnabdeypolimi/your-ai-lawyer

Repository: <https://github.com/arnabdeypolimi/your-ai-lawyer>

- What it does: legal knowledge base using raw law submodules, Obsidian notes, ChromaDB indexes, citations, hashes, and slash commands.
- Relevance: future knowledge graph, linting, and incremental rebuild inspiration.
- Reuse ideas: citation links, hash-based incremental recompilation, broken-link linting, local-first processing.
- Do not reuse: LLM-generated summaries as canonical legal data.
- License: MIT.
- Dependency concerns: ChromaDB and agent command workflows are out of MVP.
- Security concerns: compiled notes must stay separate from official artifacts.
- Suitability: RAG/search and methodology reference.

## OpenHacienda/puntoBOE

Repository: <https://github.com/OpenHacienda/puntoBOE>

- What it does: local browser validator for AEAT fixed-format tax files.
- Relevance: methodology inspiration only.
- Reuse ideas: pure validators, fixtures, local-first processing, structured validation errors, privacy-preserving architecture.
- Do not reuse: as a BOE bulletin source.
- License: MIT.
- Dependency concerns: Rust/WASM stack is unrelated to this Python MVP.
- Security concerns: domain is AEAT file validation, not official bulletin ingestion.
- Suitability: methodology reference.

## AnCode666/boe-mcp

Repository: <https://github.com/AnCode666/boe-mcp>

- What it does: small Python MCP server for BOE API access.
- Relevance: minimal MCP reference.
- Reuse ideas: BOE summary and legislation tool categories.
- Do not reuse: limited architecture as sufficient for auditable storage.
- License: MIT.
- Dependency concerns: avoid adopting it as dependency.
- Security concerns: MVP requires structured output, ingestion audit, integrity checks, and read-only guarantees beyond this scope.
- Suitability: MCP reference.

## ComputingVictor/MCP-BOE

Repository: <https://github.com/ComputingVictor/MCP-BOE>

- What it does: Python MCP/REST access to BOE consolidated legislation, daily summaries, auxiliary tables, PDF reading, and diagnostics.
- Relevance: strongest MCP interface reference reviewed.
- Reuse ideas: tool taxonomy, Pydantic-style schemas, HTTP client timeouts/retries, separated tool modules, diagnostics.
- Do not reuse: PDF reading or broad analysis tools in MVP.
- License: MIT.
- Dependency concerns: should remain an interface reference, not a base implementation.
- Security concerns: broad PDF download and large raw text return are risky unless constrained.
- External reputation: GitHub page showed low issue count and modest stars; no independent security score was available in this review.
- Suitability: MCP reference and interface inspiration.

Tool concept classification:

- Daily summary lookup: safe read-only lookup.
- Document retrieval: safe only with structured output.
- Auxiliary tables: safe read-only lookup, future.
- PDF reading: risky because it fetches and returns large text.
- Analysis or comparison prompts: excluded from MVP.

## anamtb/boe-mcp

Repository: <https://github.com/anamtb/boe-mcp>

- What it does: TypeScript BOE and EUR-Lex MCP interface.
- Relevance: ES+EU interface reference for future phases.
- Reuse ideas: source namespacing, EU-law tool separation, article-level retrieval, cross-reference detection, limitations documentation.
- Do not reuse: EUR-Lex scraping or experimental access as canonical infrastructure.
- License: MIT.
- Dependency concerns: Node/TypeScript stack is not part of this Python MVP.
- Security concerns: README documents EUR-Lex anti-bot instability; such access is experimental and unsuitable as canonical source.
- Suitability: MCP reference and future EU interface inspiration.

EUR-Lex status in that repository appears experimental for portal access due to anti-bot protections. A future EUR-Lex adapter must use official APIs and have separate audit, citation, integrity, and tests.
