# TruthLens — MVP Specification

## 1. MVP Goal

The TruthLens MVP is an AI-powered evidence verification agent that accepts a factual claim, researches it using live web search through SerpApi, analyzes the retrieved evidence, and produces an auditable research report.

The MVP should demonstrate the complete workflow:

User Claim
    ↓
Claim Decomposition
    ↓
Search Planning
    ↓
SerpApi Search
    ↓
Evidence Collection
    ↓
Evidence Classification
    ↓
Conflict / Gap Detection
    ↓
Additional Search if Needed
    ↓
Evidence Synthesis
    ↓
Auditable Report

The MVP is successful when this workflow works reliably from beginning to end.


## 2. Core User Story

A user should be able to enter a factual claim such as:

"Electric vehicles are cheaper to own than petrol cars."

TruthLens should then:

1. Understand the claim.
2. Break it into smaller researchable claims.
3. Generate relevant search queries.
4. Search the live web using SerpApi.
5. Collect relevant sources.
6. Extract evidence from those sources.
7. Determine whether each piece of evidence supports, contradicts, or contextualizes the claim.
8. Detect conflicts or missing evidence.
9. Perform additional targeted searches when necessary.
10. Produce a final assessment.
11. Show the evidence and the path used to reach the assessment.


# 3. MVP Features

## 3.1 Claim Input

The frontend must provide a simple interface where the user can enter a factual claim.

Example:

"Are electric vehicles cheaper to own than petrol cars?"

Requirements:

- Text input
- Submit / Verify button
- Basic validation
- Clear error message for an empty claim

Do not require user accounts.


## 3.2 Claim Decomposition

The system should analyze the submitted claim and identify its researchable components.

Example:

Original claim:
"Electric vehicles are cheaper to own than petrol cars."

Atomic claims:

1. EV maintenance costs are lower.
2. EV operating costs are lower.
3. EV total ownership costs are lower.
4. The result depends on assumptions such as location,
   energy prices, vehicle type, incentives, and ownership period.

The exact decomposition should be generated dynamically.

The system should avoid producing unnecessary or unrelated atomic claims.


## 3.3 Search Query Generation

For each relevant atomic claim, TruthLens should generate targeted search queries.

Example:

Atomic claim:
EV maintenance costs are lower.

Queries:

"electric vehicle maintenance costs compared with petrol cars"

"EV maintenance cost study"

"electric vehicle total cost ownership maintenance"

Queries should be designed to find evidence rather than simply repeat the original claim.


# 4. SerpApi Integration

SerpApi is a core component of the MVP.

TruthLens should use SerpApi to perform live web research.

Initial engines:

### Google Search

Used for broad research.

### Google News

Used for claims involving recent or changing information.

### Google Scholar

Used for academic, scientific, or research-oriented claims.

The system should select appropriate search sources instead of blindly calling every engine.


# 5. Search Result Collection

For every relevant search result, retain useful metadata.

At minimum:

title
url
domain
snippet
source_type
publication_date
retrieved_at

The system should normalize results from different search engines into a common internal format.

Search results should not automatically be treated as evidence.


# 6. Source Selection

The system should identify potentially relevant sources from search results.

Consider:

- relevance to the atomic claim
- presence of substantive information
- source type
- publication date when relevant
- duplicate results

The MVP does not need a sophisticated source credibility scoring system.

Do not invent a numerical credibility score.


# 7. Evidence Extraction

For relevant sources, extract concise evidence related to the claim.

Example:

Source:
Example Research Organization

Evidence:
"The study reports lower routine maintenance expenditure
for electric vehicles during the observed ownership period."

Each evidence item must remain linked to its source.

Minimum evidence fields:

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


# 8. Evidence Classification

Each evidence item must be classified relative to the claim.

Allowed classifications:

SUPPORTS
CONTRADICTS
CONTEXTUALIZES
DOES_NOT_ADDRESS

Example:

Claim:
EVs are cheaper to own than petrol cars.

Evidence:
"EVs require less routine maintenance."

Classification:
SUPPORTS

Another example:

Evidence:
"EV purchase prices remain higher in the studied market."

Classification:
CONTEXTUALIZES

Another:

Evidence:
"Under the study's assumptions, petrol vehicles had
lower total ownership cost."

Classification:
CONTRADICTS

The classification must consider the exact claim.


# 9. Evidence Gap Detection

After the initial search, the system should determine whether the collected evidence is sufficient.

Potential gaps include:

- important part of the claim has not been researched
- evidence only comes from one perspective
- sources disagree
- search results are too weak
- evidence is outdated for a time-sensitive claim
- important assumptions are unclear

If a meaningful gap is identified, TruthLens should generate a targeted follow-up search.


# 10. Iterative Research

The MVP should support limited iterative research.

Example:

Initial Search
      ↓
Evidence Analysis
      ↓
Important Gap?
   YES │ NO
      │   └────────→ Final Synthesis
      ↓
Targeted Search
      ↓
Additional Evidence
      ↓
Evidence Analysis
      ↓
Final Synthesis

The system must impose a maximum number of research iterations.

The exact limit can be configured in application settings.

The goal is controlled research, not unlimited autonomous searching.


# 11. Final Assessment

The final assessment must use one of four states:

SUPPORTED
CONTRADICTED
MIXED
INSUFFICIENT_EVIDENCE

### SUPPORTED

The retrieved evidence predominantly supports the claim and no major contradiction invalidates the conclusion.

### CONTRADICTED

Relevant evidence substantially contradicts the claim.

### MIXED

The retrieved evidence contains meaningful support and contradiction, or the conclusion depends substantially on differing conditions or assumptions.

### INSUFFICIENT_EVIDENCE

The available evidence does not adequately address the claim.

The assessment must be accompanied by an explanation.


# 12. No Arbitrary Truth Score

The MVP must not display a fabricated numerical truth score.

Do not implement:

Truth Score: 87%

or similar metrics without a defensible methodology.

Instead, display an evidence breakdown.

Example:

MIXED EVIDENCE

Supporting sources: 4
Contradicting sources: 2
Contextual sources: 3

Summary:
The evidence generally supports lower maintenance and operating
costs, but total ownership depends on purchase price, location,
energy costs, incentives, and ownership period.

Counts should reflect actual evidence collected.


# 13. Final Research Report

The report should contain the following sections.

## Claim

Display the original user claim.

## Assessment

Display:

SUPPORTED
CONTRADICTED
MIXED
INSUFFICIENT EVIDENCE

## Summary

Provide a concise explanation of the overall evidence.

## Supporting Evidence

List relevant evidence that supports the claim.

Each item should show:

- source title
- source domain
- evidence excerpt/paraphrase
- source link

## Contradicting Evidence

List relevant evidence that contradicts the claim.

Each item should show:

- source title
- source domain
- evidence excerpt/paraphrase
- source link

## Contextual Evidence

Show evidence that provides important conditions, assumptions, limitations, or surrounding context.

## Evidence Trail

Show how the final assessment was produced.


# 14. Evidence Trail UI

The Evidence Trail is a key MVP feature.

Users should be able to inspect something similar to:

CLAIM
"Electric vehicles are cheaper to own than petrol cars."

        ↓

ATOMIC CLAIM
"EV maintenance costs are lower."

        ↓

SEARCH QUERY
"electric vehicle maintenance costs compared with petrol cars"

        ↓

SEARCH ENGINE
Google Search via SerpApi

        ↓

SOURCE
Example Research Organization

        ↓

EVIDENCE
"EV maintenance expenditure was lower..."

        ↓

CLASSIFICATION
SUPPORTS

        ↓

FINAL ASSESSMENT
MIXED

The exact UI implementation can evolve, but the underlying traceability must remain.


# 15. Source Links

Every displayed evidence item should provide access to the original source.

The user should be able to open the source in a browser.

Do not display a citation that does not correspond to an actual retrieved source.

Never fabricate URLs.


# 16. Current Information

For claims involving current or rapidly changing information, the system should preserve retrieval timestamps.

Examples:

- current prices
- current regulations
- recent announcements
- ongoing events
- recent scientific developments

The report should make clear that web evidence was retrieved at a particular time.


# 17. Error States

The MVP must handle common failures gracefully.

### Empty claim

Display:

"Please enter a claim to verify."

### No search results

Display:

"No relevant search results were found."

### Insufficient evidence

Display:

"INSUFFICIENT EVIDENCE

The available sources did not provide enough evidence
to evaluate this claim reliably."

### SerpApi failure

Display a useful error rather than crashing the application.

### LLM failure

Display a useful error and do not fabricate a research result.


# 18. MVP API

The backend should initially expose:

GET /api/v1/health
POST /api/v1/research

Example request:

{
  "claim": "Electric vehicles are cheaper to own than petrol cars."
}

The response should contain a structured research report.

The exact schema should be defined using Pydantic models.


# 19. MVP Frontend

The frontend should be implemented using Streamlit.

Initial layout:

┌───────────────────────────────────────────┐
│                 TruthLens                 │
│                                           │
│   Enter a factual claim                  │
│   ┌───────────────────────────────────┐   │
│   │ Are EVs cheaper to own than       │   │
│   │ petrol cars?                      │   │
│   └───────────────────────────────────┘   │
│                                           │
│              [ Verify Claim ]             │
└───────────────────────────────────────────┘

After research:

┌───────────────────────────────────────────┐
│ Assessment                                │
│                                           │
│ MIXED                                     │
│                                           │
│ Summary                                   │
│ ...                                       │
│                                           │
│ Supporting Evidence                       │
│ ───────────────────────────────────────   │
│ Source A                                  │
│ Evidence...                               │
│                                           │
│ Contradicting Evidence                    │
│ ───────────────────────────────────────   │
│ Source B                                  │
│ Evidence...                               │
│                                           │
│ Context                                   │
│ ───────────────────────────────────────   │
│ ...                                       │
│                                           │
│ Evidence Trail                            │
│ ───────────────────────────────────────   │
│ Claim → Query → Source → Evidence         │
└───────────────────────────────────────────┘

The UI should prioritize readability and traceability.


# 20. MVP Technical Requirements

The implementation should use:

Python
FastAPI
Streamlit
SerpApi
Pydantic
LLM provider through an abstraction
pytest

Use environment variables for API credentials.

Required configuration should be documented in `.env.example`.


# 21. MVP Testing Requirements

The MVP should include automated tests for important deterministic logic.

At minimum:

- API request validation
- claim model validation
- search result normalization
- evidence model validation
- evidence classification
- assessment logic

External API calls should normally be mocked in unit tests.

Integration tests may use real services separately.


# 22. MVP Non-Goals

The following are explicitly outside the first MVP:

- user authentication
- user profiles
- payment systems
- subscriptions
- social sharing
- mobile application
- browser extensions
- browser automation
- complex database infrastructure
- distributed services
- real-time collaboration
- advanced source reputation scoring
- custom model training
- fine-tuning
- multilingual support
- unlimited autonomous research
- arbitrary truth percentages

These may be considered after the core workflow is stable.


# 23. Performance and Cost Boundaries

The MVP should avoid unnecessary API calls.

Use:

- limited search iterations
- targeted queries
- result limits
- clear stopping conditions

Do not repeatedly search the same query without a reason.

Do not send unnecessarily large amounts of search data to the LLM.

The implementation should aim to keep both SerpApi and LLM usage reasonable.


# 24. MVP Definition of Done

TruthLens MVP is considered complete when a user can:

1. Open the application.
2. Enter a factual claim.
3. Submit the claim.
4. See the claim being researched.
5. Observe that SerpApi is being used for live research.
6. Receive an evidence-based assessment.
7. See supporting evidence.
8. See contradicting evidence when present.
9. See contextual evidence when relevant.
10. Open the original sources.
11. Inspect the Evidence Trail.
12. Understand why the system reached its assessment.
13. Receive an explicit insufficient-evidence result when appropriate.
14. Run the application using documented setup instructions.

The MVP should demonstrate the complete TruthLens concept rather than maximizing the number of features.


# 25. Post-MVP Direction

Once the MVP is reliable, potential improvements can be evaluated based on their contribution to the core product.

Possible future areas:

- richer source analysis
- source deduplication
- better evidence ranking
- persistent research history
- visual evidence graphs
- multilingual research
- additional search providers
- more sophisticated research planning
- source credibility metadata
- saved investigations

These are future considerations, not MVP requirements.