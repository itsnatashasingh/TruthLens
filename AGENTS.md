# TruthLens — Codex Development Instructions

## 1. Project Purpose

TruthLens is an AI-powered evidence verification agent.

The application accepts a factual claim, searches the live web using SerpApi, collects relevant sources, extracts evidence, identifies supporting and contradicting evidence, detects conflicts, and produces an auditable evidence trail.

TruthLens must help users understand the available evidence. It must not claim absolute truth or manufacture certainty.

---

## 2. Core Product Principles

Always preserve these principles:

1. MVP evidence must come from SerpApi search-result data returned for real retrieved sources.
2. Every evidence item must retain its source URL.
3. Search results are not automatically facts.
4. Never invent citations, sources, quotations, statistics, or evidence.
5. The LLM must not fabricate information that is not present in the retrieved source data.
6. Clearly distinguish supporting, contradicting, and contextual evidence.
7. Explicitly represent uncertainty and insufficient evidence.
8. Do not implement an arbitrary numerical "truth score".
9. Preserve an auditable evidence chain:
   
   Claim → Atomic Claim → Search Query → SerpApi Result → Source → Evidence → Evidence Classification → Atomic Claim Assessment → Overall Assessment

10. SerpApi must be a meaningful part of the research workflow, not a decorative API call.

---

## 3. MVP Assessment Labels

The system should use these overall assessment states:

- SUPPORTED
- CONTRADICTED
- MIXED
- INSUFFICIENT_EVIDENCE

Individual evidence items may use:

- SUPPORTS
- CONTRADICTS
- CONTEXTUALIZES
- DOES_NOT_ADDRESS

Do not introduce additional assessment labels without a clear architectural reason.

---

## 4. Architecture

The intended architecture is:

Frontend
    ↓
FastAPI Backend
    ↓
Claim Analysis
    ↓
Search Planning
    ↓
SerpApi
    ↓
Source Collection
    ↓
Evidence Extraction
    ↓
Evidence Classification
    ↓
Conflict / Gap Detection
    ↓
Evidence Synthesis
    ↓
Final Report
    ↓
Frontend

The initial technology stack is:

- Python
- FastAPI
- Streamlit
- SerpApi
- Pydantic
- An LLM provider through an abstraction layer

Keep external services behind service abstractions wherever practical.

---

## 5. SerpApi Usage

Use SerpApi as the primary web research layer.

Initial search sources:

- Google Search for broad factual research
- Google News for recent/current claims
- Google Scholar for academic/scientific claims

Do not automatically run every search source for every claim.

The search planner may select one or more appropriate search sources for a claim.

Preserve important search metadata such as:

- query
- engine
- result title
- result URL
- source/domain
- snippet when available
- publication date when available
- retrieval timestamp

For the MVP, SerpApi search-result data is the evidence acquisition layer. Use returned title, URL/link, domain/source, date metadata, snippet, and engine-specific metadata where available. Do not directly scrape, fetch, or imply that TruthLens read the full contents of source webpages.

Displayed evidence excerpts must be either retrieved search-result snippets or faithful paraphrases of those snippets. Users must receive the original source URL so they can inspect the source themselves.

---

## 6. Agentic Research Behavior

TruthLens should not behave as a single search followed by an LLM summary.

The research workflow should be capable of:

1. Decomposing a claim into atomic claims.
2. Generating targeted search queries.
3. Searching through SerpApi.
4. Collecting candidate sources.
5. Extracting relevant evidence.
6. Classifying evidence.
7. Detecting conflicts or missing evidence.
8. Generating additional targeted searches when necessary.
9. Re-evaluating the evidence.
10. Producing the final assessment.

If evidence is insufficient, the system should be able to say so.

Do not force a conclusion when the evidence does not support one.

MVP research is bounded by configurable defaults: at most 5 atomic claims, 2 search queries per atomic claim, 5 results considered per query, and 1 follow-up research round. These limits control cost, latency, and complexity.

---

## 7. Evidence Integrity

Every evidence object should retain enough information to trace it back to its source.

Conceptually:

```python
{
    "claim_id": "...",
    "atomic_claim_id": "...",
    "query_id": "...",
    "search_result_id": "...",
    "evidence_id": "...",
    "evidence_trail_id": "...",
    "source_title": "...",
    "source_url": "...",
    "source_domain": "...",
    "source_type": "...",
    "publication_date": "...",
    "retrieved_at": "...",
    "excerpt": "...",  # snippet or faithful snippet paraphrase
    "stance": "...",
    "relevance": 0.0
}
```
Do not create evidence from the model's general knowledge when that evidence is supposed to represent retrieved web research. Do not present a snippet or paraphrase as a quotation from a full source page unless SerpApi returned that exact text.

When an exact snippet quotation is unavailable, use a clearly identified faithful paraphrase rather than inventing quotation marks.

Deduplicate results using canonicalized source URLs where practical. Duplicate versions of the same source must not be treated as independent evidence or artificially increase the apparent amount of evidence. Source types such as `web/general`, `news`, and `academic` describe retrieval/classification only; they are not credibility rankings.

If relevance is retained internally, it is only a research/ranking signal. It is not a measure of truth, credibility, source reliability, or truth likelihood.

## 8. Uncertainty

TruthLens should explicitly communicate uncertainty.

Prefer statements such as:

- "The retrieved evidence supports this claim."
- "The available sources contain conflicting evidence."
- "The search produced insufficient evidence to determine the claim."
- "This source provides context but does not directly address the claim."

Avoid statements such as:

- "This is definitely true."
- "This is definitely false."
- "Truth score: 87%"

unless a future design explicitly establishes a defensible methodology for such a claim.

The overall assessment is determined by deterministic aggregation of unique evidence classifications across atomic claims, not by an LLM choosing a verdict. For each atomic claim, direct supporting and contradicting evidence is aggregated as follows: both produces `MIXED`; only supporting produces `SUPPORTED`; only contradicting produces `CONTRADICTED`; neither produces `INSUFFICIENT_EVIDENCE`. `CONTEXTUALIZES` and `DOES_NOT_ADDRESS` provide explanation but not direct support or contradiction. The original claim is `INSUFFICIENT_EVIDENCE` if any atomic claim is insufficiently addressed; otherwise it is `MIXED` if any atomic claim is mixed or atomic claims differ between supported and contradicted, `SUPPORTED` if all are supported, and `CONTRADICTED` if all are contradicted.

## 9. Code Quality

Use:

1. Python type hints
2. Pydantic models for structured data
3. Small, focused modules
4. Clear function and class names
5. Environment variables for secrets
6. Meaningful error handling
7. Tests for important logic

Avoid:

- Large monolithic files
- Hard-coded API keys
- Unnecessary dependencies
- Duplicate implementations
- Hidden global state
- Unexplained magic numbers

Do not add a dependency when the Python standard library or an existing project dependency is sufficient.

## 10. Secrets and Configuration

Never hard-code:

- SerpApi API keys
- LLM API keys
- passwords
- tokens
- credentials

Use environment variables.

The LLM provider and model must be configured through environment variables. Do not hard-code a vendor. Any LLM output that affects application state must use a Pydantic-validated structured schema.

.env files containing secrets must never be committed to Git.

Use .env.example to document required configuration variables without exposing actual credentials.

## 11. API Design

The backend should expose a clean API boundary.

The initial API should include:

- GET /api/v1/health
- POST /api/v1/research

`POST /api/v1/research` is synchronous: it runs the bounded research workflow and returns the completed structured research report. The frontend may show a spinner or progress messages while waiting; do not add WebSockets, polling/status endpoints, background job queues, or distributed task systems to the MVP.

The MVP error policy is: `400` for invalid requests or validation errors, `502` for required external dependency failures (including SerpApi or the configured LLM provider), and `500` for unexpected internal errors. A successful `200` response may validly contain `INSUFFICIENT_EVIDENCE`. Never fabricate evidence or a conclusion after an external dependency failure.

Keep API schemas separate from internal implementation details where practical.

## 12. Frontend

The MVP frontend should prioritize clarity over visual complexity.

The main user flow should be:

1. Enter a claim.
2. Start verification.
3. View assessment.
4. View supporting evidence.
5. View contradicting evidence.
6. View contextual evidence.
7. Inspect the evidence trail.
8. Open the original sources.

Do not add unnecessary UI features before the core research workflow works reliably.

## 13. Evidence Trail

The Evidence Trail is a core TruthLens feature.

The UI should allow a user to understand:

Claim
→ Atomic Claim
→ Search Query
→ SerpApi Result
→ Source
→ Extracted Evidence
→ Evidence Classification
→ Final Assessment

Do not hide the research process behind only a final LLM-generated answer.

## 14. Development Workflow

Before making substantial changes:

1. Inspect the existing repository.
2. Read relevant documentation.
3. Understand the current architecture.
4. Make the smallest coherent change.
5. Run relevant tests.
6. Check for errors.
7. Review the resulting diff.

Do not rewrite unrelated files.

Do not remove working functionality without a clear reason.

Do not make broad architectural changes unless explicitly requested.

## 15. Testing

Important components should have tests, especially:

- claim decomposition
- search query generation
- result normalization
- evidence classification
- assessment synthesis
- API validation

Tests should not depend on live API calls unless specifically written as integration tests.

Mock external services for normal unit tests.

## 16. Error Handling

External services can fail.

Handle:

- missing API keys
- API errors
- rate limits
- timeouts
- malformed responses
- empty search results
- insufficient evidence
- LLM failures

The application should fail gracefully and explain the problem to the user where appropriate.

Never silently replace failed evidence with fabricated content.

## 17. Scope Control

The MVP should remain focused.

Do not add:

- browser automation
- user accounts
- complex databases
- payment systems
- social features
- mobile applications
- unnecessary microservices

unless explicitly requested later.

The priority is a reliable end-to-end evidence verification workflow.

## 18. Documentation

Keep important architectural decisions documented in:

- docs/ARCHITECTURE.md
- docs/MVP.md

Update documentation when implementation decisions materially change the architecture or MVP scope.

## 19. Git Safety

Do not:

- force-push
- delete the repository
- rewrite Git history
- reset user work
- overwrite unrelated changes

without explicit user instruction.

Before committing, inspect:

```Bash
git status
git diff
```

Keep commits focused and descriptive.

## 20. Final Rule

When choosing between a more impressive implementation and a simpler reliable implementation, prefer the simpler implementation unless the additional complexity directly improves TruthLens's core evidence-verification capability.
