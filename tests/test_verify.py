from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from littrail.catalog import PaperEntry
from littrail.cli import app
from littrail.openalex import FetchError
from tests.fixtures import SAMPLE_RAW_WORK, MockFetcher

runner = CliRunner()


def _invoke_verify(catalog_path: Path, fetcher: MockFetcher) -> object:
    with patch("littrail.cli.PyAlexFetcher", return_value=fetcher):
        return runner.invoke(
            app,
            ["verify", "--catalog", str(catalog_path)],
            catch_exceptions=False,
        )


def test_verify_matching_metadata_exits_zero(catalog_with_paper: tuple[Path, PaperEntry]) -> None:
    path, _ = catalog_with_paper
    fetcher = MockFetcher(by_doi=SAMPLE_RAW_WORK)
    result = _invoke_verify(path, fetcher)
    assert result.exit_code == 0  # type: ignore[union-attr]
    assert "OK" in result.output  # type: ignore[union-attr]


def test_verify_title_mismatch_exits_nonzero(catalog_with_paper: tuple[Path, PaperEntry]) -> None:
    path, _ = catalog_with_paper
    modified = {**SAMPLE_RAW_WORK, "title": "A Completely Different Title"}
    fetcher = MockFetcher(by_doi=modified)
    result = _invoke_verify(path, fetcher)
    assert result.exit_code != 0  # type: ignore[union-attr]
    assert "title mismatch" in result.output  # type: ignore[union-attr]


def test_verify_year_mismatch_exits_nonzero(catalog_with_paper: tuple[Path, PaperEntry]) -> None:
    path, _ = catalog_with_paper
    modified = {**SAMPLE_RAW_WORK, "publication_year": 2020}
    fetcher = MockFetcher(by_doi=modified)
    result = _invoke_verify(path, fetcher)
    assert result.exit_code != 0  # type: ignore[union-attr]
    assert "year mismatch" in result.output  # type: ignore[union-attr]


def test_verify_author_mismatch_exits_nonzero(catalog_with_paper: tuple[Path, PaperEntry]) -> None:
    path, _ = catalog_with_paper
    modified = {
        **SAMPLE_RAW_WORK,
        "authorships": [{"author": {"display_name": "Someone Else"}}],
    }
    fetcher = MockFetcher(by_doi=modified)
    result = _invoke_verify(path, fetcher)
    assert result.exit_code != 0  # type: ignore[union-attr]
    assert "authors mismatch" in result.output  # type: ignore[union-attr]


def test_verify_fetch_error_exits_nonzero(catalog_with_paper: tuple[Path, PaperEntry]) -> None:
    path, _ = catalog_with_paper
    fetcher = MockFetcher(error=FetchError("Network error"))
    result = _invoke_verify(path, fetcher)
    assert result.exit_code != 0  # type: ignore[union-attr]
    assert "Fetch error" in result.output  # type: ignore[union-attr]
