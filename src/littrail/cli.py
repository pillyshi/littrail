from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Annotated

import typer

from littrail.catalog import CatalogError, generate_key, load_catalog, save_catalog
from littrail.checks import run_checks
from littrail.openalex import FetchError, PyAlexFetcher, normalize_work

_OPENALEX_MAX_PER_PAGE = 200

app = typer.Typer(
    name="littrail",
    help="Verified literature trail for software projects.",
    no_args_is_help=True,
)

_TEMPLATES_DIR = Path(__file__).parent / "templates"
_DEFAULT_CATALOG = Path("research/catalog.yaml")


# ---------------------------------------------------------------------------
# init
# ---------------------------------------------------------------------------


@app.command()
def init(
    force: Annotated[
        bool,
        typer.Option("--force", help="Overwrite littrail-managed template files."),
    ] = False,
) -> None:
    """Initialise the research/ workflow in the current directory."""
    base = Path("research")
    subdirs = ["reports", "notes", "ideas", "pdfs"]
    for sub in subdirs:
        (base / sub).mkdir(parents=True, exist_ok=True)
        if sub != "pdfs":
            gitkeep = base / sub / ".gitkeep"
            if not gitkeep.exists():
                gitkeep.touch()

    _install_template("research_README.md", base / "README.md", force)
    _install_template("catalog.yaml", base / "catalog.yaml", force)
    _ensure_research_gitignore(base)
    typer.echo("research/ workflow initialised.")


def _install_template(template_name: str, dest: Path, force: bool) -> None:
    src = _TEMPLATES_DIR / template_name
    if dest.exists() and not force:
        typer.echo(f"Skipped (already exists): {dest}  (use --force to overwrite)")
        return
    dest.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    typer.echo(f"Created: {dest}")


def _ensure_research_gitignore(base: Path) -> None:
    gitignore = base / ".gitignore"
    entry = "pdfs/"
    if gitignore.exists():
        lines = gitignore.read_text(encoding="utf-8").splitlines()
        if any(line.strip() == entry for line in lines):
            return
        text = gitignore.read_text(encoding="utf-8")
        if not text.endswith("\n"):
            text += "\n"
        gitignore.write_text(text + entry + "\n", encoding="utf-8")
    else:
        gitignore.write_text(entry + "\n", encoding="utf-8")
    typer.echo(f"Created: {gitignore}")


# ---------------------------------------------------------------------------
# add-paper
# ---------------------------------------------------------------------------


@app.command(name="add-paper")
def add_paper(
    doi: Annotated[str | None, typer.Option(help="DOI of the paper.")] = None,
    openalex: Annotated[
        str | None, typer.Option(help="OpenAlex work ID (e.g. W2970200208).")
    ] = None,
    catalog: Annotated[
        Path,
        typer.Option(help="Path to catalog.yaml."),
    ] = _DEFAULT_CATALOG,
) -> None:
    """Fetch paper metadata from OpenAlex and add it to the catalog."""
    if not doi and not openalex:
        typer.echo("Error: provide --doi or --openalex", err=True)
        raise typer.Exit(1)
    if doi and openalex:
        typer.echo("Error: provide only one of --doi or --openalex", err=True)
        raise typer.Exit(1)

    try:
        cat = load_catalog(catalog)
    except CatalogError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1)

    fetcher = PyAlexFetcher()
    try:
        if doi:
            raw = fetcher.fetch_by_doi(doi)
        else:
            assert openalex is not None
            raw = fetcher.fetch_by_openalex_id(openalex)
    except FetchError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1)

    entry = normalize_work(raw)

    # Duplicate check
    existing_dois = {
        p.identifiers.get("doi") for p in cat.papers if p.identifiers.get("doi")
    }
    existing_oas = {
        p.identifiers.get("openalex")
        for p in cat.papers
        if p.identifiers.get("openalex")
    }
    entry_doi = entry.identifiers.get("doi")
    entry_oa = entry.identifiers.get("openalex")

    if (entry_doi and entry_doi in existing_dois) or (
        entry_oa and entry_oa in existing_oas
    ):
        typer.echo(
            f"Already in catalog: '{entry.title}' — no changes made.", err=False
        )
        raise typer.Exit(0)

    existing_keys = {p.key for p in cat.papers}
    entry.key = generate_key(entry.authors, entry.year, existing_keys)
    cat.papers.append(entry)
    save_catalog(cat, catalog)
    typer.echo(f"Added [{entry.key}]: {entry.title}")


# ---------------------------------------------------------------------------
# verify
# ---------------------------------------------------------------------------


@app.command()
def verify(
    catalog: Annotated[
        Path,
        typer.Option(help="Path to catalog.yaml."),
    ] = _DEFAULT_CATALOG,
) -> None:
    """Verify catalog metadata against OpenAlex (read-only)."""
    try:
        cat = load_catalog(catalog)
    except CatalogError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1)

    if not cat.papers:
        typer.echo("No papers in catalog.")
        return

    fetcher = PyAlexFetcher()
    mismatches: list[str] = []

    for paper in cat.papers:
        doi = paper.identifiers.get("doi")
        oa_id = paper.identifiers.get("openalex")
        if not doi and not oa_id:
            mismatches.append(
                f"[{paper.key}] No DOI or OpenAlex ID — cannot verify."
            )
            continue

        try:
            if doi:
                raw = fetcher.fetch_by_doi(doi)
            else:
                assert oa_id is not None
                raw = fetcher.fetch_by_openalex_id(oa_id)
        except FetchError as exc:
            mismatches.append(f"[{paper.key}] Fetch error: {exc}")
            continue

        from littrail.openalex import (
            extract_authors,
            extract_doi,
            extract_openalex_id,
        )

        live_title = str(raw.get("title") or "")
        live_authors = extract_authors(raw)
        live_year = int(raw.get("publication_year") or 0)
        live_doi = extract_doi(raw)
        live_oa = extract_openalex_id(raw)

        diffs = _compare(paper.key, {
            "title": (paper.title, live_title),
            "year": (str(paper.year), str(live_year)),
            "doi": (paper.identifiers.get("doi", ""), live_doi),
            "openalex": (paper.identifiers.get("openalex", ""), live_oa),
        })
        # authors: compare sorted sets
        catalog_authors_set = set(paper.authors)
        live_authors_set = set(live_authors)
        if catalog_authors_set != live_authors_set:
            diffs.append(
                f"  authors mismatch:\n"
                f"    catalog : {paper.authors}\n"
                f"    openalex: {live_authors}"
            )

        mismatches.extend(diffs)
        if not diffs:
            typer.echo(f"[{paper.key}] OK")

    if mismatches:
        typer.echo("\nVerification failed:")
        for m in mismatches:
            typer.echo(m)
        raise typer.Exit(1)


def _compare(key: str, fields: dict[str, tuple[str, str]]) -> list[str]:
    diffs: list[str] = []
    for field_name, (catalog_val, live_val) in fields.items():
        if catalog_val != live_val:
            diffs.append(
                f"[{key}] {field_name} mismatch:\n"
                f"  catalog : {catalog_val!r}\n"
                f"  openalex: {live_val!r}"
            )
    return diffs


# ---------------------------------------------------------------------------
# check
# ---------------------------------------------------------------------------


@app.command()
def check(
    catalog: Annotated[
        Path,
        typer.Option(help="Path to catalog.yaml."),
    ] = _DEFAULT_CATALOG,
) -> None:
    """Check repository workflow consistency (offline)."""
    problems = run_checks(catalog)
    if problems:
        typer.echo(f"Found {len(problems)} problem(s):", err=False)
        for p in problems:
            typer.echo(f"  - {p}")
        sys.exit(1)
    else:
        typer.echo("All checks passed.")


# ---------------------------------------------------------------------------
# search
# ---------------------------------------------------------------------------


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query."),
    limit: int = typer.Option(10, "--limit", help="Maximum number of results."),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON for agent pipelines."),
) -> None:
    """Search OpenAlex for papers matching a query (read-only)."""
    if limit < 1:
        typer.echo("Error: limit must be at least 1.", err=True)
        raise typer.Exit(1)
    if limit > _OPENALEX_MAX_PER_PAGE:
        typer.echo(
            f"Warning: limit capped at {_OPENALEX_MAX_PER_PAGE} (OpenAlex API maximum)",
            err=True,
        )
        limit = _OPENALEX_MAX_PER_PAGE

    fetcher = PyAlexFetcher()
    try:
        raw_works = fetcher.search_works(query, limit)
    except FetchError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1)

    if json_output:
        records = []
        for raw in raw_works:
            entry = normalize_work(raw)
            records.append({
                "openalex_id": entry.identifiers.get("openalex", ""),
                "doi": entry.identifiers.get("doi", ""),
                "title": entry.title,
                "authors": entry.authors,
                "year": entry.year if entry.year != 0 else None,
                "venue": entry.venue,
            })
        typer.echo(json.dumps(records, ensure_ascii=False))
        return

    # Table output
    rows: list[tuple[str, str, str, str]] = []
    seen_keys: set[str] = set()
    for raw in raw_works:
        entry = normalize_work(raw)
        key = generate_key(entry.authors, entry.year, seen_keys)
        seen_keys.add(key)
        authors_short = _format_authors_short(entry.authors)
        title_short = entry.title[:60] + "..." if len(entry.title) > 60 else entry.title
        year_display = "" if entry.year == 0 else str(entry.year)
        rows.append((key, year_display, authors_short, title_short))

    if not rows:
        return

    col_widths = (
        max(len("KEY"), max(len(r[0]) for r in rows)),
        max(len("YEAR"), max(len(r[1]) for r in rows)),
        max(len("AUTHORS"), max(len(r[2]) for r in rows)),
        max(len("TITLE"), max(len(r[3]) for r in rows)),
    )
    header = "  ".join(h.ljust(w) for h, w in zip(("KEY", "YEAR", "AUTHORS", "TITLE"), col_widths))
    typer.echo(header)
    for row in rows:
        typer.echo("  ".join(cell.ljust(w) for cell, w in zip(row, col_widths)))


def _format_authors_short(authors: list[str]) -> str:
    if not authors:
        return ""
    # OpenAlex display_name is "First Last" — take the last token as surname
    last = authors[0].split()[-1]
    if len(authors) > 1:
        return f"{last} et al."
    return last


if __name__ == "__main__":
    app()
