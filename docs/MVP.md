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
6. Use SerpApi search-result data to extract snippet-based evidence from those sources.
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

The system should avoid producing unnecessary or unrelated atomic claims. The MVP default is a maximum of 5 atomic claims per user claim; this is a bounded configuration value.


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

The MVP default is a maximum of 2 queries per atomic claim. The research planner may select one or more appropriate SerpApi engines for an atomic claim.


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

The system should select one or more appropriate search sources instead of blindly calling every engine. SerpApi is a core required part of the research workflow, not an optional enhancement.


# 5. Search Result Collection

For every relevant search result, retain useful metadata.

At minimum:

title
url
canonical_url
domain
snippet
source_type
publication_date
retrieved_at
query_id
search_result_id

The system should normalize results from different search engines into a common internal format.

Search results should not automatically be treated as evidence.

The MVP considers at most 5 results per query by default. Use canonicalized source URLs where practical to deduplicate results, so repeated versions of the same source do not artificially increase the apparent amount of evidence. Source types such as `web/general`, `news`, and `academic` describe retrieval/classification only and are not credibility rankings.


# 6. Source Selection

The system should identify potentially relevant sources from SerpApi search results.

Consider:

- relevance to the atomic claim
- presence of substantive information
- source type
- publication date when relevant
- duplicate results

The MVP does not need a sophisticated source credibility scoring system.

Do not invent a numerical credibility score.

If relevance is retained internally, it is a research/ranking signal only. It must not be interpreted or displayed as a measure of truth, credibility, source reliability, or truth likelihood.


# 7. Evidence Extraction

For relevant SerpApi results, retain concise evidence related to the atomic claim.

Example:

Source:
Example Research Organization

Evidence:
Retrieved snippet: "The study reports lower routine maintenance expenditure
for electric vehicles during the observed ownership period."

For the MVP, SerpApi search-result data is the evidence acquisition layer. Use the structured data SerpApi returns, including title, URL/link, source/domain, publication/date metadata, snippet, and engine-specific metadata where available. Do not directly scrape or fetch source webpages, and never imply that TruthLens read the full article or page.

Evidence shown to users must be clearly represented as either a retrieved search-result snippet or a faithful paraphrase derived from that snippet. Each evidence item must remain linked to its original source URL so the user can inspect it directly.

Minimum evidence fields:

claim_id
atomic_claim_id
query_id
search_result_id
evidence_id
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

Each evidence item must be classified relative to its atomic claim.

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

An LLM may produce a Pydantic-validated structured classification, but it must not arbitrarily select the final overall assessment.


# 9. Evidence Gap Detection

After the initial search, the system should determine whether the collected evidence is sufficient.

Potential gaps include:

- important part of the claim has not been researched
- evidence only comes from one perspective
- sources disagree
- search results are too weak
- evidence is outdated for a time-sensitive claim
- important assumptions are unclear

If a meaningful gap is identified, TruthLens may generate a targeted follow-up search. A follow-up is permitted only for an unresolved contradiction, important evidence gap, ambiguous atomic claim, or need for a more targeted query.


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

The exact limit can be configured in application settings. The MVP default is 1 follow-up research round.

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

The final label is calculated deterministically from unique evidence classifications across atomic claims, rather than selected freely by the LLM. For an atomic claim, both direct support and contradiction yields `MIXED`; support only yields `SUPPORTED`; contradiction only yields `CONTRADICTED`; neither yields `INSUFFICIENT_EVIDENCE`. For the original claim, any insufficiently addressed atomic claim yields `INSUFFICIENT_EVIDENCE`; otherwise any mixed atomic assessment or combination of supported and contradicted atomic assessments yields `MIXED`; all supported yields `SUPPORTED`; and all contradicted yields `CONTRADICTED`. `CONTEXTUALIZES` and `DOES_NOT_ADDRESS` inform the explanation but are not direct support or contradiction.


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
INSUFFICIENT_EVIDENCE

## Summary

Provide a concise explanation of the overall evidence.

## Supporting Evidence

List relevant evidence that supports the claim.

Each item should show:

- source title
- source domain
- retrieved snippet or clearly identified faithful snippet paraphrase
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

ATOMIC CLAIM ASSESSMENT
SUPPORTED

        ↓

FINAL ASSESSMENT
MIXED

The exact UI implementation can evolve, but the underlying traceability must remain. Stable identifiers should be retained where appropriate: `claim_id`, `atomic_claim_id`, `query_id`, `search_result_id`, `evidence_id`, and `evidence_trail_id`.


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

"INSUFFICIENT_EVIDENCE

The available sources did not provide enough evidence
to evaluate this claim reliably."

### SerpApi failure

Display a useful error rather than crashing the application. Return `502` from the API; do not fabricate evidence or a conclusion.

### LLM failure

Display a useful error and do not fabricate a research result. Return `502` from the API.


# 18. MVP API

The backend should initially expose:

GET /api/v1/health
POST /api/v1/research

Example request:

{
  "claim": "Electric vehicles are cheaper to own than petrol cars."
}

`POST /api/v1/research` is synchronous: it performs the bounded research workflow and returns the completed structured research report. Do not add WebSockets, background queues, polling/status endpoints, or distributed task systems to the MVP.

The API uses `400` for invalid requests or validation errors, `502` for required SerpApi or configured LLM-provider failures, and `500` for unexpected internal errors. `200` is returned for a successful report, including a valid `INSUFFICIENT_EVIDENCE` outcome.

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

The UI should prioritize readability and traceability. While the synchronous research request runs, it may show a spinner or progress messages.


# 20. MVP Technical Requirements

The implementation should use:

Python
FastAPI
Streamlit
SerpApi
Pydantic
provider-agnostic LLM layer through an abstraction
pytest

Use environment variables for API credentials.

Configure the LLM provider and model through environment variables; do not hard-code a vendor. LLM outputs that affect application state must be validated with Pydantic structured schemas.

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
- direct source-page fetching or scraping
- WebSockets, background queues, polling/status endpoints, or distributed task systems

These may be considered after the core workflow is stable.


# 23. Performance and Cost Boundaries

The MVP should avoid unnecessary API calls.

Use:

- a maximum of 5 atomic claims per user claim
- a maximum of 2 search queries per atomic claim
- a maximum of 5 results considered per query
- a maximum of 1 follow-up research round
- targeted queries
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
- better evidence ranking
- persistent research history
- visual evidence graphs
- multilingual research
- additional search providers
- more sophisticated research planning
- source credibility metadata
- saved investigations

These are future considerations, not MVP requirements.
