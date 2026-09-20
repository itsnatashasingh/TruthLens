# TruthLens — System Architecture

## 1. Overview

TruthLens is an AI-powered evidence verification agent that researches factual claims using live web search.

The system accepts a user claim, decomposes it into researchable components, generates targeted search queries, retrieves search results through SerpApi, extracts and classifies evidence, identifies conflicts or gaps, and produces an auditable research report.

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
- Display research progress.
- Display the final assessment.
- Display supporting evidence.
- Display contradicting evidence.
- Display contextual evidence.
- Display the Evidence Trail.
- Provide links to original sources.

The frontend should not contain research logic.

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

The response should contain structured information rather than only a plain text answer.

### 3.3 Research Orchestrator

The Research Orchestrator coordinates the complete verification workflow.

It is responsible for controlling the sequence:
```text
Claim
  ↓
Claim Analysis
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

The decomposition should preserve the meaning of the original claim.

The system should avoid creating unnecessary atomic claims.

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
The planner should generate searches designed to find evidence rather than simply repeat the user's wording.

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

The Search Planner should determine which search category is appropriate.

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

## 8. Result Normalizer

Different search engines can return different result structures.

The Result Normalizer converts them into a common internal representation.

Conceptual model:
```Python
SearchResult:
    title
    url
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
This allows downstream components to work with a consistent data structure.

## 9. Evidence Extractor

The Evidence Extractor determines whether a search result contains information relevant to the claim.

It should extract a concise evidence passage or paraphrase.

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

The system must never invent evidence that does not appear in the retrieved source data.

## 10. Evidence Classifier

Each extracted evidence item is classified relative to a specific claim.

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
The detector can trigger an additional search when an important evidence gap exists.

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

The MVP should use explicit limits to prevent uncontrolled search loops.

## 13. Evidence Model

The core internal object is an Evidence object.

Conceptually:
```Python
Evidence:
    claim_id
    source_title
    source_url
    source_domain
    source_type
    publication_date
    retrieved_at
    excerpt
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
The exact implementation may evolve, but source traceability must remain.

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
The LLM provider should be accessed through an abstraction so that the rest of the application is not tightly coupled to one provider.

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
INSUFFICIENT EVIDENCE
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
- source deduplication
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