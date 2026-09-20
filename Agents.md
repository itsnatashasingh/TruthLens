# TruthLens — Codex Development Instructions

## 1. Project Purpose

TruthLens is an AI-powered evidence verification agent.

The application accepts a factual claim, searches the live web using SerpApi, collects relevant sources, extracts evidence, identifies supporting and contradicting evidence, detects conflicts, and produces an auditable evidence trail.

TruthLens must help users understand the available evidence. It must not claim absolute truth or manufacture certainty.

---

## 2. Core Product Principles

Always preserve these principles:

1. Evidence must come from real retrieved sources.
2. Every evidence item must retain its source URL.
3. Search results are not automatically facts.
4. Never invent citations, sources, quotations, statistics, or evidence.
5. The LLM must not fabricate information that is not present in the retrieved source data.
6. Clearly distinguish supporting, contradicting, and contextual evidence.
7. Explicitly represent uncertainty and insufficient evidence.
8. Do not implement an arbitrary numerical "truth score".
9. Preserve an auditable evidence chain:
   
   Claim → Search Query → Search Result → Source → Evidence → Assessment

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

The search planner should determine which search source is appropriate.

Preserve important search metadata such as:

- query
- engine
- result title
- result URL
- source/domain
- snippet when available
- publication date when available
- retrieval timestamp

Do not replace SerpApi with direct scraping in the MVP.

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

---

## 7. Evidence Integrity

Every evidence object should retain enough information to trace it back to its source.

Conceptually:

```python
{
    "claim_id": "...",
    "source_title": "...",
    "source_url": "...",
    "source_domain": "...",
    "source_type": "...",
    "publication_date": "...",
    "retrieved_at": "...",
    "excerpt": "...",
    "stance": "...",
    "relevance": 0.0
}
```
Do not create evidence from the model's general knowledge when that evidence is supposed to represent retrieved web research.

When an exact quotation is unavailable, use a clearly identified paraphrase rather than inventing quotation marks.

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

.env files containing secrets must never be committed to Git.

Use .env.example to document required configuration variables without exposing actual credentials.

## 11. API Design

The backend should expose a clean API boundary.

The initial API should include:

- GET /api/v1/health
- POST /api/v1/research

The research endpoint should accept a user claim and return a structured research report.

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
→ Search Query
→ Search Result
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