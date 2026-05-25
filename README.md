# littrail

**Verified literature trail for software projects.**

littrail solves the problem of using AI-generated research surveys as
unchecked evidence. It provides a CLI tool and workflow template that turns
an AI-generated survey into a verified literature trail — with metadata
confirmed against OpenAlex, reading notes, and GitHub issue candidates — all
stored in Git.

## Workflow

```
generated report -> verified catalog -> paper notes -> issue candidates -> GitHub issues
```

1. Save an AI-generated literature survey in `research/reports/`.
2. Add papers with verified metadata using `littrail add-paper`.
3. Confirm metadata against OpenAlex with `littrail verify`.
4. Write reading notes in `research/notes/<key>.md`.
5. Draft issue candidates in `research/ideas/`.
6. Promote to GitHub issues manually.

## Installation

```bash
# One-off use (no install required):
uvx littrail --help

# For CI or team-managed projects:
poetry add --group dev littrail
```

## Quickstart

```bash
littrail init
export OPENALEX_API_KEY=...
littrail add-paper --doi 10.18653/v1/D19-1404
littrail verify
littrail check
```

## Commands

| Command | Description |
|---------|-------------|
| `littrail init` | Initialise `research/` workflow in current directory |
| `littrail add-paper --doi <DOI>` | Add paper by DOI |
| `littrail add-paper --openalex <ID>` | Add paper by OpenAlex ID |
| `littrail verify` | Verify catalog metadata against OpenAlex (read-only) |
| `littrail check` | Check repository consistency offline |

## research/ Directory Policy

```
research/
  README.md          # Workflow documentation (Git tracked)
  catalog.yaml       # Verified metadata (Git tracked)
  reports/           # AI-generated surveys (Git tracked)
  notes/             # Per-paper reading notes (Git tracked)
  ideas/             # Issue candidates (Git tracked)
  pdfs/              # Local PDF cache (NOT tracked)
```

PDF binaries are stored in `research/pdfs/` and excluded from Git via
`.gitignore`. This keeps the repository lightweight while preserving the
human-readable record.

## API Key

`littrail add-paper` and `littrail verify` use the
[OpenAlex](https://openalex.org/) API via `pyalex`.

```bash
export OPENALEX_API_KEY=your_key_here
```

**Do not commit your API key.** It is never written to `catalog.yaml`,
logs, or any Git-tracked file.

## Design Decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| CLI framework | typer | Auto `--help`, type-annotation based |
| YAML library | ruamel.yaml | Preserves key order and formatting |
| Type checker | pyright | Strict mode, good typer compatibility |
| `verify` auto-update | No | Keeps human judgment in the loop |
| Key format | `<family>-<year>` | Human-readable, suffix on collision |

## MVP Non-Goals

The following are **not** included in this release:

- LLM API integration or automated report generation
- PDF auto-download
- PDF text extraction or citation scraping
- GitHub issue creation
- Automated note writing
- arXiv / ACL identifier input (DOI and OpenAlex ID only)
- Catalog auto-migration
- CI workflow template generation
- Plugin / MCP server packaging
