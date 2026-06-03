---
name: littrail-research-intake
description: >
  Use when onboarding an AI-generated literature report or a list of paper
  candidates. Verifies stable identifiers against OpenAlex and keeps
  catalog.yaml as the authoritative record.
---

# littrail-research-intake

Handles AI-generated literature reports and existing paper candidates. Stable
identifiers must be verified before any paper is treated as evidence.

## Guardrails

- AI-generated reports live in `research/reports/` and are starting points only — not evidence.
- Do not treat a title or author list from a report as confirmed until `littrail verify` has run.
- Do not write `research/notes/<key>.md` until the paper is in `catalog.yaml` and verified.
- Do not edit `catalog.yaml` by hand. Use `littrail add-paper` and `littrail verify`.

## Workflow

1. Save the AI-generated report to `research/reports/`.
2. Extract candidate stable identifiers from the report (DOI, OpenAlex ID, arXiv ID).
3. For each candidate, add it to the catalog:
   ```bash
   littrail add-paper --doi <doi>
   # or
   littrail add-paper --openalex <openalex_id>
   ```
4. Verify all catalog entries against OpenAlex:
   ```bash
   littrail verify
   ```
5. Check repository consistency:
   ```bash
   littrail check
   ```
6. Papers that pass verification are ready for reading notes in `research/notes/`.

## Stable Identifiers

Prefer, in order: DOI → OpenAlex ID (`W<number>`) → arXiv ID.
If a report does not include a stable identifier, do not add the paper until one is found.

## Output

`research/catalog.yaml` is the only authoritative record. Nothing downstream
(notes, ideas, GitHub issues) should be created from unverified metadata.
