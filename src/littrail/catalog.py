from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML


@dataclass
class PaperEntry:
    key: str
    title: str
    authors: list[str]
    year: int
    publication_type: str
    venue: str
    identifiers: dict[str, str]
    relevance: str = "to_classify"
    priority: str = "to_review"
    rationale: str = ""
    note_status: str = "pending"
    pdf_status: str = "missing"
    related_versions: list[str] = field(default_factory=list)
    cached_version: str | None = None
    local_pdf: str | None = None


@dataclass
class Catalog:
    catalog_version: int
    project: str
    verified_on: str | None
    verification: dict[str, str]
    source_reports: list[str]
    papers: list[PaperEntry]


class CatalogError(Exception):
    pass


def load_catalog(path: Path) -> Catalog:
    if not path.exists():
        raise CatalogError(f"Catalog not found: {path}\nRun 'littrail init' first.")
    yaml = YAML()
    try:
        raw = yaml.load(path)
    except Exception as exc:
        raise CatalogError(f"Failed to parse catalog YAML: {exc}") from exc
    if raw is None:
        raise CatalogError(f"Catalog is empty: {path}")
    _validate_schema(raw, path)
    papers = [_parse_paper(p) for p in (raw.get("papers") or [])]
    return Catalog(
        catalog_version=int(raw["catalog_version"]),
        project=str(raw.get("project") or ""),
        verified_on=raw.get("verified_on"),
        verification=dict(raw.get("verification") or {}),
        source_reports=list(raw.get("source_reports") or []),
        papers=papers,
    )


def save_catalog(catalog: Catalog, path: Path) -> None:
    yaml = YAML()
    yaml.default_flow_style = False
    yaml.width = 4096  # type: ignore[assignment]
    data: dict[str, Any] = {
        "catalog_version": catalog.catalog_version,
        "project": catalog.project,
        "verified_on": catalog.verified_on,
        "verification": catalog.verification,
        "source_reports": catalog.source_reports,
        "papers": [_entry_to_dict(p) for p in catalog.papers],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        yaml.dump(data, f)


def generate_key(authors: list[str], year: int, existing_keys: set[str]) -> str:
    family = _extract_family_name(authors[0]) if authors else "unknown"
    family = re.sub(r"[^a-z0-9]", "", family.lower())
    base = f"{family}-{year}"
    if base not in existing_keys:
        return base
    suffix = 2
    while f"{base}-{suffix}" in existing_keys:
        suffix += 1
    return f"{base}-{suffix}"


def _extract_family_name(full_name: str) -> str:
    parts = full_name.strip().split()
    return parts[-1] if parts else "unknown"


def _validate_schema(raw: Any, path: Path) -> None:
    required = ["catalog_version", "papers"]
    missing = [k for k in required if k not in raw]
    if missing:
        raise CatalogError(
            f"Catalog {path} is missing required fields: {', '.join(missing)}"
        )


def _parse_paper(raw: Any) -> PaperEntry:
    identifiers = dict(raw.get("identifiers") or {})
    return PaperEntry(
        key=str(raw.get("key") or ""),
        title=str(raw.get("title") or ""),
        authors=list(raw.get("authors") or []),
        year=int(raw.get("year") or 0),
        publication_type=str(raw.get("publication_type") or ""),
        venue=str(raw.get("venue") or ""),
        identifiers=identifiers,
        relevance=str(raw.get("relevance") or "to_classify"),
        priority=str(raw.get("priority") or "to_review"),
        rationale=str(raw.get("rationale") or ""),
        note_status=str(raw.get("note_status") or "pending"),
        pdf_status=str(raw.get("pdf_status") or "missing"),
        related_versions=list(raw.get("related_versions") or []),
        cached_version=raw.get("cached_version"),
        local_pdf=raw.get("local_pdf"),
    )


def _entry_to_dict(entry: PaperEntry) -> dict[str, Any]:
    d: dict[str, Any] = {
        "key": entry.key,
        "title": entry.title,
        "authors": entry.authors,
        "year": entry.year,
        "publication_type": entry.publication_type,
        "venue": entry.venue,
        "identifiers": entry.identifiers,
        "relevance": entry.relevance,
        "priority": entry.priority,
        "rationale": entry.rationale,
        "note_status": entry.note_status,
        "pdf_status": entry.pdf_status,
    }
    if entry.related_versions:
        d["related_versions"] = entry.related_versions
    if entry.cached_version is not None:
        d["cached_version"] = entry.cached_version
    if entry.local_pdf is not None:
        d["local_pdf"] = entry.local_pdf
    return d
