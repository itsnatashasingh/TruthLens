# TruthLens — System Architecture

## 1. Overview

TruthLens is an AI-powered evidence verification agent that researches factual claims using live web search.

The system accepts a user claim, decomposes it into researchable atomic claims, generates targeted search queries, retrieves structured search-result data through SerpApi, classifies snippet-based evidence, identifies conflicts or gaps, and produces an auditable research report.

For the MVP, SerpApi search-result data is the evidence acquisition layer. TruthLens does not fetch or scrape source webpages; it must not imply that it has read a full page.

The architecture is designed around one core principle:

> Every conclusion should be traceable back to the evidence that produced it.

---

## 2. High-Level Architecture

```text
                         ┌──────────────────────┐
                         │       User           │
                         │   Enter a claim      │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │     Streamlit        │
                         │      Frontend        │
                         └──────────┬───────────┘
                                    │
                                    │ HTTP
                                    ▼
                         ┌──────────────────────┐
                         │       FastAPI        │
                         │       Backend        │
                         └──────────┬───────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │       Research Orchestrator   │
                    └───────────────┬───────────────┘
                                    │
                 ┌──────────────────┼──────────────────┐
                 │                  │                  │
                 ▼                  ▼                  ▼
        ┌────────────────┐ ┌────────────────┐ ┌────────────────┐
        │ Claim Analyzer │ │ Search Planner │ │ LLM Provider   │
        └───────┬────────┘ └───────┬────────┘ └────────────────┘
                │                  │
                │                  ▼
                │        ┌────────────────────┐
                │        │      SerpApi       │
                │        └─────────┬──────────┘
                │                  │
                │       ┌──────────┼──────────┐
                │       ▼          ▼          ▼
                │   Google       News      Scholar
                │   Search
                │
                └──────────────────┬──────────────────┘
                                   ▼
                         ┌──────────────────────┐
                         │  Result Normalizer   │
                         └──────────┬───────────┘
                                    ▼
                         ┌──────────────────────┐
                         │ Evidence Extractor   │
                         └──────────┬───────────┘
                                    ▼
                         ┌──────────────────────┐
                         │ Stance Classifier    │
                         └──────────┬───────────┘
                                    ▼
                         ┌──────────────────────┐
                         │ Conflict / Gap       │
                         │ Detector             │
                         └──────────┬───────────┘
                                    │
                         More evidence needed?
                              │           │
                            YES           NO
                              │           │
                              └─────┐     │
                                    ▼     ▼
                              Additional  Evidence
                                Search    Synthesis
                                           │
                                           ▼
                                  ┌──────────────────┐
                                  │  Report Builder  │
                                  └────────┬─────────┘
                                           ▼
                                  ┌──────────────────┐
                                  │    Streamlit     │
                                  │     Report       │
                                  └──────────────────┘
```
## 3. Architectural Components

### 3.1 Streamlit Frontend

The frontend provides the user interface for TruthLens.

Responsibilities:

- Accept a factual claim.
- Start a research request.
- Display a spinner or progress messages while the synchronous research request runs.
- Display the final assessment.
- Display supporting evidence.
- Display contradicting evidence.
- Display contextual evidence.
- Display the Evidence Trail.
- Provide links to original sources.

The frontend should not contain research logic. It does not need WebSockets, polling/status endpoints, or background-job integration for the MVP.

It should communicate with the FastAPI backend through the defined API.

### 3.2 FastAPI Backend

FastAPI provides the application API.

Responsibilities:

- Validate incoming requests.
- Start research workflows.
- Return structured research reports.
- Handle API-level errors.
- Expose health information.

Initial endpoints:

```Bash
GET  /api/v1/health
POST /api/v1/research
```

Example research request:
```JSON
{
  "claim": "Electric vehicles are cheaper to own than petrol cars."
}
```

`POST /api/v1/research` is synchronous: it completes the bounded research workflow before returning a structured `ResearchReport`, rather than returning a job identifier.

MVP response policy is `200` for a successful report (including `INSUFFICIENT_EVIDENCE`), `400` for invalid requests or validation errors, `502` for a required SerpApi or configured LLM-provider failure, and `500` for unexpected internal errors. An external dependency failure must never be replaced with fabricated evidence or a fabricated conclusion.

### 3.3 Research Orchestrator

The Research Orchestrator coordinates the complete verification workflow.

It is responsible for controlling the sequence:
```text
Claim
  ↓
Claim Analysis
  ↓
Atomic Claims
  ↓
Search Planning
  ↓
Search
  ↓
Result Normalization
  ↓
Evidence Extraction
  ↓
Evidence Classification
  ↓
Atomic Claim Assessment
  ↓
Conflict / Gap Detection
  ↓
Additional Search if required
  ↓
Evidence Synthesis
  ↓
Final Report
```

The orchestrator should coordinate services rather than contain every implementation detail itself.

## 4. Claim Analyzer

The Claim Analyzer converts the user's natural-language claim into researchable components.

Example:

```Text
User Claim:

"Electric vehicles are cheaper to own than petrol cars."
```

Possible decomposition:

```Text
Atomic Claim 1:
Electric vehicles have lower maintenance costs.

Atomic Claim 2:
Electric vehicles have lower operating costs.

Atomic Claim 3:
The total cost of ownership of electric vehicles is lower.

Atomic Claim 4:
The comparison depends on vehicle type, location, energy prices,
purchase price, incentives, and ownership period.
```

The decomposition should preserve the meaning of the original claim. The original claim remains visible in the final report, and every atomic claim has a stable `atomic_claim_id` linked to its parent `claim_id`.

The system should avoid creating unnecessary atomic claims and must produce no more than 5 atomic claims per user claim by default. This is a bounded configuration value.

## 5. Search Planner

The Search Planner converts atomic claims into targeted search queries.

Example:

```Text
Atomic Claim:
Electric vehicles have lower maintenance costs.

Generated queries:

"electric vehicle maintenance costs compared with petrol cars"

"EV maintenance cost study petrol vehicles"

"electric vehicle total cost ownership maintenance research"
```
The planner should generate searches designed to find evidence rather than simply repeat the user's wording. It may choose one or more appropriate engines for an atomic claim, but must generate no more than 2 queries per atomic claim by default. Each query receives a stable `query_id` and links to its `atomic_claim_id`.

## 6. Search Engine Layer

SerpApi is the external search layer.

The initial system supports three search categories:

**Google Search**

Used for broad factual research.
```Text
engine = google
```

**Google News**

Used when the claim involves recent events, current developments, announcements, or changing information.
```Text
engine = google_news
```

**Google Scholar**

Used for scientific, academic, and research-oriented claims.
```Text
engine = google_scholar
```

The Search Planner should determine which search category or categories are appropriate.

The system should not blindly execute all three search types for every claim.

## 7. SerpApi Service

All SerpApi communication should be isolated behind a dedicated service.

Conceptually:
```Text
SearchService
    │
    ├── Google Search
    ├── Google News
    └── Google Scholar
```

The rest of the application should not need to know the details of SerpApi HTTP requests.

This abstraction makes the application easier to test and maintain.

It also ensures that SerpApi remains a meaningful part of the research pipeline.

SerpApi is a required core dependency, not an optional enhancement. The MVP uses its structured result data—title, URL/link, source/domain, publication/date metadata, snippet, and engine-specific metadata where available—as its evidence acquisition layer. No separate webpage-fetching or web-scraping service belongs in the MVP architecture.

## 8. Result Normalizer

Different search engines can return different result structures.

The Result Normalizer converts them into a common internal representation.

Conceptual model:
```Python
SearchResult:
    search_result_id
    query_id
    title
    url
    canonical_url
    domain
    snippet
    source_type
    publication_date
    retrieved_at
```
Example:
```JSON
{
  "title": "Study of Electric Vehicle Ownership Costs",
  "url": "https://example.org/study",
  "domain": "example.org",
  "snippet": "The study compares...",
  "source_type": "academic",
  "publication_date": "2026-04-12",
  "retrieved_at": "2026-09-19T..."
}
```
This allows downstream components to work with a consistent data structure. Results receive stable `search_result_id` values and should be deduplicated by canonicalized source URL where practical. Deduplication prevents repeated versions of the same source from being counted as independent evidence.

`source_type` may be `web/general`, `news`, or `academic`, describing how a result was retrieved or classified. It is not a credibility ranking.

## 9. Evidence Extractor

The Evidence Extractor determines whether a SerpApi search result contains information relevant to the atomic claim.

It should retain a concise retrieved snippet or create a faithful paraphrase derived only from that snippet. It must label the representation accordingly and must not claim to have read the full source page.

Example:
```Text
Source:
Example Automotive Study

Relevant evidence:
"The study reports lower routine maintenance expenditure
for electric vehicles over the observed ownership period."
```
The evidence must remain connected to the original source.

Every evidence object must retain:

- source title
- source URL
- source domain
- source type
- publication date when available
- retrieval timestamp
- extracted evidence
- related claim
- relevance

Evidence receives a stable `evidence_id` and links to its `claim_id`, `atomic_claim_id`, `query_id`, and `search_result_id`. Relevance, if retained, is only a research/ranking signal—not a truth, credibility, source-reliability, or truth-likelihood score.

The system must never invent evidence that does not appear in the retrieved source data.

## 10. Evidence Classifier

Each extracted evidence item is classified relative to a specific atomic claim.

Possible classifications:
```Text
SUPPORTS
CONTRADICTS
CONTEXTUALIZES
DOES_NOT_ADDRESS
```
Example:
```Text
Claim:
EVs are cheaper to own than petrol cars.

Evidence A:
"EVs require less routine maintenance."

Classification:
SUPPORTS
```
```Text
Evidence B:
"EV purchase prices remain higher in the studied market."

Classification:
CONTEXTUALIZES
```
```Text
Evidence C:
"Under the examined assumptions, the petrol vehicle had
lower total ownership cost."

Classification:
CONTRADICTS
```
Classification must always be relative to the specific claim being evaluated.

A source mentioning the same topic does not automatically constitute evidence.

An LLM may provide Pydantic-validated structured classifications, but it does not choose the overall verdict. `CONTEXTUALIZES` and `DOES_NOT_ADDRESS` explain evidence coverage but do not directly support or contradict an atomic claim.

## 11. Conflict and Gap Detector

The Conflict and Gap Detector examines the collected evidence.

It looks for:

- contradictory findings
- conflicting measurements
- different study assumptions
- different geographic conditions
- different time periods
- missing evidence
- weak evidence coverage
- claims that have not been directly addressed

Example:
```Text
Supporting evidence:       4
Contradicting evidence:    2
Contextual evidence:       3
Unaddressed evidence:      1
```
The detector can trigger one additional, targeted research round when it identifies an unresolved contradiction, important evidence gap, ambiguous atomic claim, or need for a more targeted query. The MVP permits at most 1 follow-up round by default; this is a bounded configuration value.

## 12. Iterative Search Loop

A key part of the TruthLens architecture is iterative research.

The workflow is not necessarily:
```Text
Search once → summarize
```
Instead:
```Text
Initial Search
      ↓
Evaluate Evidence
      ↓
Is important evidence missing?
      │
   ┌──┴──┐
  YES    NO
   │      │
   ▼      ▼
Generate  Synthesize
targeted
query
   │
   ▼
SerpApi
   │
   ▼
New Evidence
   │
   └──────────→ Evaluate Again
```
The system should stop when:

- sufficient evidence has been collected,
- additional searches are unlikely to materially improve coverage,
- or the configured research limit has been reached.

The MVP uses explicit, configurable defaults to prevent uncontrolled search loops: 5 atomic claims per original claim, 2 queries per atomic claim, 5 results considered per query, and 1 follow-up round.

## 13. Evidence Model

The core internal object is an Evidence object.

Conceptually:
```Python
Evidence:
    evidence_id
    claim_id
    atomic_claim_id
    query_id
    search_result_id
    source_title
    source_url
    source_domain
    source_type
    publication_date
    retrieved_at
    excerpt  # retrieved snippet or faithful snippet paraphrase
    stance
    relevance
```
Example:
```JSON
{
  "claim_id": "claim_001",
  "source_title": "Example Study",
  "source_url": "https://example.org/study",
  "source_domain": "example.org",
  "source_type": "academic",
  "publication_date": "2026-04-12",
  "retrieved_at": "2026-09-19T10:30:00Z",
  "excerpt": "The study found...",
  "stance": "SUPPORTS",
  "relevance": 0.91
}
```
The exact implementation may evolve, but source traceability must remain. Full-page source content is not an MVP input.

## 14. Research Report Model

The final research result should be structured.

Conceptually:
```Text
ResearchReport
│
├── original_claim
│
├── assessment
│
├── summary
│
├── atomic_claims[]
│
├── atomic_claim_assessments[]
│
├── supporting_evidence[]
│
├── contradicting_evidence[]
│
├── contextual_evidence[]
│
├── evidence_gaps[]
│
└── evidence_trail[]
```
The final assessment must be one of:
```Text
SUPPORTED
CONTRADICTED
MIXED
INSUFFICIENT_EVIDENCE
```
TruthLens should not reduce the research result to an arbitrary percentage.

The report retains the original claim and its `claim_id`. Each evidence-trail entry receives an `evidence_trail_id` and represents the linked chain from claim through atomic claim, query, SerpApi result, source, evidence, classification, and assessment.

Overall assessment is deterministic aggregation of unique evidence classifications across atomic claims. For an atomic claim, both direct support and contradiction yields `MIXED`; direct support only yields `SUPPORTED`; direct contradiction only yields `CONTRADICTED`; neither yields `INSUFFICIENT_EVIDENCE`. For the original claim, any insufficiently addressed atomic claim yields `INSUFFICIENT_EVIDENCE`; otherwise any mixed atomic assessment or combination of supported and contradicted atomic assessments yields `MIXED`; all supported yields `SUPPORTED`; and all contradicted yields `CONTRADICTED`. Contextual and non-addressing evidence informs the explanation but does not directly determine support or contradiction.

## 15. Evidence Trail

The Evidence Trail is one of the primary differentiating features of TruthLens.

It should preserve the relationship:
```Text
Original Claim
      ↓
Atomic Claim
      ↓
Search Query
      ↓
SerpApi Result
      ↓
Source
      ↓
Extracted Evidence
      ↓
Evidence Classification
      ↓
Final Assessment
```
Example:
```Text
Claim:
"EVs are cheaper to own than petrol cars."

        ↓

Query:
"electric vehicle total cost ownership petrol comparison"

        ↓

Source:
Example Research Organization

        ↓

Evidence:
"EV maintenance costs were lower..."

        ↓

Classification:
SUPPORTS

        ↓

Assessment:
MIXED
```
A user should be able to inspect this chain rather than simply trusting the final summary.

## 16. LLM Layer

The LLM is used for reasoning and language tasks.

Potential responsibilities:

- claim decomposition
- search query generation
- evidence extraction
- evidence classification
- conflict interpretation
- evidence synthesis
- report generation

The LLM should not be treated as the source of factual evidence.

The factual evidence layer comes from retrieved sources.
```Text
Conceptually:

                 ┌─────────────────┐
                 │   LLM Provider  │
                 └────────┬────────┘
                          │
          ┌───────────────┼────────────────┐
          ▼               ▼                ▼
   Claim Analysis   Evidence Analysis   Synthesis
```
The LLM provider should be accessed through an abstraction so that the rest of the application is not tightly coupled to one provider. Provider and model are configured through environment variables; no vendor is hard-coded. Outputs that affect application state—including decomposition, planning, classification, gap analysis, and synthesis inputs—must be validated against Pydantic structured schemas.

## 17. Separation of Responsibilities

The architecture should maintain clear boundaries.
```Text
Frontend
    ↓
API
    ↓
Orchestration
    ↓
Domain Services
    ↓
External Services
```
For example:
```Text
Streamlit
    → FastAPI
        → Research Orchestrator
            → Claim Analyzer
            → Search Planner
            → SerpApi Service
            → Evidence Extractor
            → Evidence Classifier
            → Conflict Detector
            → Synthesizer
```
The frontend should not call SerpApi directly.

The LLM should not directly control the UI.

SerpApi-specific implementation should not be spread throughout the codebase.

## 18. Proposed Repository Architecture
```Text
TruthLens/
│
├── AGENTS.md
├── README.md
├── .gitignore
├── .env.example
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   │
│   │   ├── api/
│   │   │   ├── routes.py
│   │   │   └── schemas.py
│   │   │
│   │   ├── models/
│   │   │   ├── claim.py
│   │   │   ├── evidence.py
│   │   │   ├── search.py
│   │   │   └── report.py
│   │   │
│   │   └── services/
│   │       ├── research_orchestrator.py
│   │       ├── claim_analyzer.py
│   │       ├── search_planner.py
│   │       ├── serpapi.py
│   │       ├── result_normalizer.py
│   │       ├── evidence_extractor.py
│   │       ├── evidence_classifier.py
│   │       ├── conflict_detector.py
│   │       ├── synthesizer.py
│   │       └── llm.py
│   │
│   └── tests/
│       ├── test_claim_analyzer.py
│       ├── test_search_planner.py
│       ├── test_evidence_classifier.py
│       └── test_api.py
│
├── frontend/
│   └── app.py
│
└── docs/
    ├── ARCHITECTURE.md
    └── MVP.md
```
This structure is a starting point rather than a requirement to create every file immediately.

Only create modules when they are actually needed by the implementation.

## 19. Data Flow

A complete research request should approximately follow this flow:
```Text
1. User submits claim
            ↓
2. FastAPI validates request
            ↓
3. Research Orchestrator starts
            ↓
4. Claim Analyzer creates atomic claims
            ↓
5. Search Planner creates queries
            ↓
6. SerpApi executes searches
            ↓
7. Results are normalized
            ↓
8. Relevant evidence is extracted
            ↓
9. Evidence is classified
            ↓
10. Conflicts and gaps are detected
            ↓
11. Additional searches may be performed
            ↓
12. Evidence is synthesized
            ↓
13. ResearchReport is created
            ↓
14. FastAPI returns structured report
            ↓
15. Streamlit renders report
```

## 20. Error Boundaries

Errors should be isolated by layer.

**Frontend errors**

Examples:

- invalid claim
- request timeout
- backend unavailable

**API errors**

Examples:

- invalid request schema
- service failure
- unexpected internal error

**SerpApi errors**

Examples:

- invalid API key
- rate limit
- timeout
- malformed response

**LLM errors**

Examples:

- provider unavailable
- invalid response
- malformed structured output

**Research errors**

Examples:

- no search results
- insufficient evidence
- conflicting evidence
- unable to evaluate claim

The system should distinguish between:
```Text
SYSTEM FAILURE
```
and
```Text
INSUFFICIENT_EVIDENCE
```
They are not the same condition.

## 21. MVP Architecture Constraints

The first version should remain intentionally simple.

Do not introduce:

- microservices
- message queues
- Kubernetes
- distributed databases
- browser automation
- direct webpage fetching or scraping
- WebSockets, polling/status endpoints, background job queues, or distributed task systems
- complex authentication
- real-time collaboration

unless the project requirements later justify them.

The MVP should be a single repository containing:
```Text
Streamlit Frontend
        +
FastAPI Backend
        +
Research Services
        +
SerpApi
        +
LLM Provider
```
This is sufficient to demonstrate the core TruthLens concept while keeping the system manageable for a solo developer.

## 22. Future Extension Points

The architecture should leave room for future capabilities without implementing them in the MVP.

Possible future extensions:

- research history
- persistent database
- source credibility metadata
- multilingual claims
- additional search engines
- citation graph visualization
- claim comparison
- saved investigations
- collaborative research
- browser-based source inspection
- user accounts

These should not be implemented merely because they are possible.

The MVP should first prove the core evidence-verification workflow.

## 23. Architectural Success Criteria

The architecture is successful when TruthLens can:

1. Accept a natural-language factual claim.
2. Break it into researchable components.
3. Generate targeted searches.
4. Use SerpApi to retrieve live evidence.
5. Preserve source traceability.
6. Identify supporting evidence.
7. Identify contradicting evidence.
8. Identify contextual evidence.
9. Detect important evidence gaps.
10. Perform additional targeted searches when necessary.
11. Produce an evidence-based assessment.
12. Show the user how the assessment was reached.

The final product should make the research process inspectable rather than presenting an unexplained AI conclusion.
