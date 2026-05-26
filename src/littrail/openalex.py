from __future__ import annotations

import os
from typing import Any, Protocol

import pyalex

from littrail.catalog import PaperEntry


class FetchError(Exception):
    pass


class WorkFetcher(Protocol):
    def fetch_by_doi(self, doi: str) -> dict[str, Any]: ...
    def fetch_by_openalex_id(self, openalex_id: str) -> dict[str, Any]: ...


class PyAlexFetcher:
    def __init__(self) -> None:
        api_key = os.environ.get("OPENALEX_API_KEY")
        if api_key:
            pyalex.config.api_key = api_key

    def fetch_by_doi(self, doi: str) -> dict[str, Any]:
        return self._fetch(f"https://doi.org/{doi}")

    def fetch_by_openalex_id(self, openalex_id: str) -> dict[str, Any]:
        # Accept both "W2970200208" and "https://openalex.org/W2970200208"
        if not openalex_id.startswith("https://"):
            openalex_id = f"https://openalex.org/{openalex_id}"
        return self._fetch(openalex_id)

    def _fetch(self, identifier: str) -> dict[str, Any]:
        try:
            work = pyalex.Works()[identifier]  # type: ignore[index]
            return dict(work)  # type: ignore[arg-type]
        except Exception as exc:
            msg = str(exc)
            if "404" in msg or "not found" in msg.lower():
                raise FetchError(
                    f"Paper not found: {identifier}\n"
                    "Check that the identifier is correct."
                ) from exc
            if "401" in msg or "403" in msg or "auth" in msg.lower():
                raise FetchError(
                    f"OpenAlex authentication error: {exc}\n"
                    "Set the OPENALEX_API_KEY environment variable and retry."
                ) from exc
            raise FetchError(
                f"Failed to fetch from OpenAlex: {exc}\n"
                "Check your network connection or set OPENALEX_API_KEY."
            ) from exc


def normalize_work(raw: dict[str, Any]) -> PaperEntry:
    title = str(raw.get("title") or "")
    authors = extract_authors(raw)
    year = int(raw.get("publication_year") or 0)
    publication_type = str(raw.get("type") or "")
    venue = extract_venue(raw)
    doi = extract_doi(raw)
    openalex_id = extract_openalex_id(raw)
    identifiers: dict[str, str] = {}
    if doi:
        identifiers["doi"] = doi
    if openalex_id:
        identifiers["openalex"] = openalex_id
    return PaperEntry(
        key="",  # caller sets key via generate_key
        title=title,
        authors=authors,
        year=year,
        publication_type=publication_type,
        venue=venue,
        identifiers=identifiers,
    )


def extract_authors(raw: dict[str, Any]) -> list[str]:
    authorships = raw.get("authorships") or []
    names: list[str] = []
    for a in authorships:
        author = a.get("author") or {}
        name = author.get("display_name") or ""
        if name:
            names.append(name)
    return names


def extract_venue(raw: dict[str, Any]) -> str:
    loc = raw.get("primary_location") or {}
    source = loc.get("source") or {}
    return str(source.get("display_name") or "")


def extract_doi(raw: dict[str, Any]) -> str:
    doi = raw.get("doi") or ""
    # Strip "https://doi.org/" prefix if present
    doi = str(doi)
    if doi.startswith("https://doi.org/"):
        doi = doi[len("https://doi.org/"):]
    return doi


def extract_openalex_id(raw: dict[str, Any]) -> str:
    url = str(raw.get("id") or "")
    # Strip "https://openalex.org/" prefix
    if url.startswith("https://openalex.org/"):
        return url[len("https://openalex.org/"):]
    return url
