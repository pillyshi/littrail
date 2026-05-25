from __future__ import annotations

from pathlib import Path

import pytest

from littrail.catalog import Catalog, PaperEntry, save_catalog
from tests.fixtures import MockFetcher


@pytest.fixture()
def mock_fetcher() -> MockFetcher:
    return MockFetcher()


@pytest.fixture()
def minimal_catalog_path(tmp_path: Path) -> Path:
    catalog = Catalog(
        catalog_version=1,
        project="test",
        verified_on=None,
        verification={"provider": "OpenAlex", "client": "pyalex"},
        source_reports=[],
        papers=[],
    )
    path = tmp_path / "research" / "catalog.yaml"
    save_catalog(catalog, path)
    return path


@pytest.fixture()
def catalog_with_paper(tmp_path: Path) -> tuple[Path, PaperEntry]:
    paper = PaperEntry(
        key="yin-2019",
        title="Benchmarking Zero-shot Text Classification: Datasets, Evaluation and Entailment Approach",
        authors=["Wenpeng Yin", "Jamaal Hay", "Dan Roth"],
        year=2019,
        publication_type="article",
        venue="EMNLP-IJCNLP 2019",
        identifiers={"doi": "10.18653/v1/D19-1404", "openalex": "W2970200208"},
    )
    catalog = Catalog(
        catalog_version=1,
        project="test",
        verified_on=None,
        verification={"provider": "OpenAlex", "client": "pyalex"},
        source_reports=[],
        papers=[paper],
    )
    path = tmp_path / "research" / "catalog.yaml"
    save_catalog(catalog, path)
    return path, paper
