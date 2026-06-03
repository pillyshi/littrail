---
name: littrail-agent-research
description: >
  Use when deriving search queries from project context and discovering
  paper candidates with littrail search. Focuses on query strategy,
  multi-search deduplication, and relevance ranking before handing
  candidates to the verification workflow.
---

# littrail-agent-research

Guides autonomous literature discovery: reading project context to derive
queries, running multiple searches, deduplicating and ranking candidates, and
handing selected works to the verification workflow. Search results are
unverified candidates until stable identifiers and primary sources are checked.

## Guardrails

- `littrail search` results are candidates only — not verified papers.
- Do not add a candidate to the catalog without a stable identifier (OpenAlex ID or DOI). Skip candidates where neither can be found.
- Do not add every search result. Select intentionally based on project relevance.
- Do not treat titles, abstracts, or AI-generated summaries alone as evidence.
- Do not create GitHub issues directly from search results or candidate lists.
- Make uncertainty explicit when ranking candidates.

## Workflow

### 1. Read project context

Read the following files to understand the project's goals and existing work:

- `README.md`
- `CLAUDE.md` (if present)
- `research/README.md` (if present)
- `research/reports/` (AI-generated surveys, if any)
- `research/catalog.yaml` (to avoid re-adding already tracked papers)

### 2. Derive search queries

Based on project context, derive multiple queries that cover the problem space
from different angles. Vary terminology and phrasing across queries to widen
coverage. For example, if the project involves retrieval-augmented generation,
candidate queries might include "retrieval augmented generation", "dense
retrieval for question answering", and "knowledge grounding language models".

Aim for 3–6 queries. Write them down before running any searches.

### 3. Run searches

Run each query with the JSON flag for machine-readable output:

```bash
littrail search "<query>" --json --limit 20
```

Collect all results before proceeding. Each result includes `openalex_id`,
`doi`, `title`, `authors`, `year`, and `venue`.

### 4. Deduplicate and rank

Deduplicate across all search results using `openalex_id` as the key.
A paper that appears in multiple query results is a stronger signal of
relevance — note how many queries surfaced it.

Rank the deduplicated candidates by likely relevance to the project:

- How directly does the topic match the project's core problem?
- How recently was it published relative to the project's timeline?
- How many of your queries returned it?

Keep uncertainty explicit: a high-ranking candidate is still unverified.

### 5. Hand off to verification

For each candidate worth tracking, add it to the catalog:

```bash
littrail add-paper --openalex <openalex_id>
# or
littrail add-paper --doi <doi>
```

Then verify and check:

```bash
littrail verify
littrail check
```

Pass verified papers to `littrail-literature-work` for reading notes.

## Relationship to other skills

| Skill | Focus |
|---|---|
| `littrail-agent-research` | Query derivation, multi-search, deduplication, ranking |
| `littrail-literature-work` | Reading verified papers, writing `research/notes/<key>.md` |
| `littrail-research-intake` | Ingesting AI-generated reports from `research/reports/` |
| `littrail-issue-candidates` | Turning notes into `research/ideas/` candidates |

## Output

| Artifact | When to create |
|---|---|
| `research/catalog.yaml` | After `littrail add-paper` + `littrail verify` for selected candidates |
| Candidate ranking (in agent response) | After deduplication — for the human or next skill to review |
