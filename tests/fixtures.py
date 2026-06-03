from __future__ import annotations

from typing import Any

SAMPLE_RAW_WORK: dict[str, Any] = {
    "id": "https://openalex.org/W2970200208",
    "title": "Benchmarking Zero-shot Text Classification: Datasets, Evaluation and Entailment Approach",
    "publication_year": 2019,
    "type": "article",
    "doi": "https://doi.org/10.18653/v1/D19-1404",
    "authorships": [
        {"author": {"display_name": "Wenpeng Yin"}},
        {"author": {"display_name": "Jamaal Hay"}},
        {"author": {"display_name": "Dan Roth"}},
    ],
    "primary_location": {
        "source": {"display_name": "EMNLP-IJCNLP 2019"},
    },
}

SAMPLE_RAW_WORK_ALT: dict[str, Any] = {
    "id": "https://openalex.org/W9999999999",
    "title": "Another Paper About NLP",
    "publication_year": 2019,
    "type": "article",
    "doi": "https://doi.org/10.18653/v1/D19-9999",
    "authorships": [
        {"author": {"display_name": "Wenpeng Yin"}},
    ],
    "primary_location": {
        "source": {"display_name": "EMNLP 2019"},
    },
}


class MockFetcher:
    def __init__(
        self,
        by_doi: dict[str, Any] | None = None,
        by_oa: dict[str, Any] | None = None,
        error: Exception | None = None,
    ) -> None:
        self._by_doi = by_doi if by_doi is not None else SAMPLE_RAW_WORK
        self._by_oa = by_oa if by_oa is not None else SAMPLE_RAW_WORK
        self._error = error

    def fetch_by_doi(self, doi: str) -> dict[str, Any]:
        if self._error:
            raise self._error
        return self._by_doi

    def fetch_by_openalex_id(self, openalex_id: str) -> dict[str, Any]:
        if self._error:
            raise self._error
        return self._by_oa

    def search_works(self, query: str, limit: int) -> list[dict[str, Any]]:
        raise NotImplementedError
