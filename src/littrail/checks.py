from __future__ import annotations

import subprocess
from pathlib import Path

from littrail.catalog import Catalog, CatalogError, load_catalog


def run_checks(catalog_path: Path) -> list[str]:
    """Return a list of problem descriptions. Empty list means all checks passed."""
    problems: list[str] = []

    # 1. Parse catalog
    try:
        catalog = load_catalog(catalog_path)
    except CatalogError as exc:
        return [str(exc)]

    research_dir = catalog_path.parent

    # 2. note_status: drafted → notes/<key>.md must exist
    for paper in catalog.papers:
        if paper.note_status == "drafted":
            note_file = research_dir / "notes" / f"{paper.key}.md"
            if not note_file.exists():
                problems.append(
                    f"[{paper.key}] note_status is 'drafted' but "
                    f"notes/{paper.key}.md does not exist"
                )

    # 3. pdf_status: cached → local_pdf must exist and file must exist
    for paper in catalog.papers:
        if paper.pdf_status == "cached":
            if not paper.local_pdf:
                problems.append(
                    f"[{paper.key}] pdf_status is 'cached' but local_pdf is not set"
                )
            else:
                # 4. local_pdf must be under research/pdfs/
                pdf_path = research_dir / paper.local_pdf
                pdfs_dir = research_dir / "pdfs"
                try:
                    pdf_path.resolve().relative_to(pdfs_dir.resolve())
                except ValueError:
                    problems.append(
                        f"[{paper.key}] local_pdf '{paper.local_pdf}' is outside "
                        f"research/pdfs/"
                    )
                else:
                    if not pdf_path.exists():
                        problems.append(
                            f"[{paper.key}] pdf_status is 'cached' but "
                            f"{paper.local_pdf} does not exist"
                        )
        elif paper.pdf_status != "cached" and paper.local_pdf:
            # local_pdf set but pdf_status not cached — also validate path
            pdf_path = research_dir / paper.local_pdf
            pdfs_dir = research_dir / "pdfs"
            try:
                pdf_path.resolve().relative_to(pdfs_dir.resolve())
            except ValueError:
                problems.append(
                    f"[{paper.key}] local_pdf '{paper.local_pdf}' is outside "
                    f"research/pdfs/"
                )

    # 5. .gitignore must contain research/pdfs/
    gitignore_path = _find_gitignore(catalog_path)
    if gitignore_path is None:
        problems.append(
            ".gitignore not found. research/pdfs/ is not excluded from Git."
        )
    else:
        if not _gitignore_has_pdfs_entry(gitignore_path):
            problems.append(
                f"{gitignore_path} does not contain 'research/pdfs/'. "
                "PDF binaries may be accidentally committed."
            )

    # 6. No tracked PDFs in research/pdfs/
    tracked_pdf_problems = _check_tracked_pdfs(research_dir)
    problems.extend(tracked_pdf_problems)

    return problems


def _find_gitignore(catalog_path: Path) -> Path | None:
    # Walk up from catalog_path looking for .gitignore
    current = catalog_path.parent
    for _ in range(10):
        candidate = current / ".gitignore"
        if candidate.exists():
            return candidate
        parent = current.parent
        if parent == current:
            break
        current = parent
    return None


def _gitignore_has_pdfs_entry(gitignore_path: Path) -> bool:
    try:
        text = gitignore_path.read_text(encoding="utf-8")
    except OSError:
        return False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped in ("research/pdfs/", "research/pdfs", "/research/pdfs/"):
            return True
    return False


def _check_tracked_pdfs(research_dir: Path) -> list[str]:
    try:
        result = subprocess.run(
            ["git", "ls-files", str(research_dir / "pdfs")],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []
    if result.returncode != 0:
        return []
    tracked = [f.strip() for f in result.stdout.splitlines() if f.strip()]
    return [
        f"PDF is tracked by Git and should be removed: {f}" for f in tracked
    ]


def check_catalog_schema(catalog: Catalog) -> list[str]:
    """Additional schema checks beyond basic parsing."""
    problems: list[str] = []
    if catalog.catalog_version != 1:
        problems.append(
            f"Unsupported catalog_version: {catalog.catalog_version} (expected 1)"
        )
    return problems
