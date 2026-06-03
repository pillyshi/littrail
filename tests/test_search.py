from __future__ import annotations

import json
from typing import Any
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from littrail.cli import app
from littrail.openalex import FetchError
from tests.fixtures import SAMPLE_RAW_WORK, SAMPLE_RAW_WORK_ALT, MockFetcher

runner = CliRunner()


class MockFetcherWithSearch(MockFetcher):
    def __init__(
        self,
        search_results: list[dict[str, Any]] | None = None,
        search_error: Exception | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._search_results = search_results if search_results is not None else [SAMPLE_RAW_WORK]
        self._search_error = search_error
        self.last_search_query: str | None = None
        self.last_search_limit: int | None = None

    def search_works(self, query: str, limit: int) -> list[dict[str, Any]]:
        self.last_search_query = query
        self.last_search_limit = limit
        if self._search_error:
            raise self._search_error
        return self._search_results


@pytest.fixture()
def mock_search_fetcher() -> MockFetcherWithSearch:
    return MockFetcherWithSearch()


def test_search_table_output() -> None:
    fetcher = MockFetcherWithSearch()
    with patch("littrail.cli.PyAlexFetcher", return_value=fetcher):
        result = runner.invoke(app, ["search", "zero-shot classification"])
    assert result.exit_code == 0
    assert "KEY" in result.output
    assert "YEAR" in result.output
    assert "AUTHORS" in result.output
    assert "TITLE" in result.output
    assert "2019" in result.output
    assert "Yin" in result.output


def test_search_json_output() -> None:
    fetcher = MockFetcherWithSearch()
    with patch("littrail.cli.PyAlexFetcher", return_value=fetcher):
        result = runner.invoke(app, ["search", "zero-shot", "--json"])
    assert result.exit_code == 0
    records = json.loads(result.output)
    assert isinstance(records, list)
    assert len(records) == 1
    assert records[0]["openalex_id"] == "W2970200208"
    assert records[0]["year"] == 2019
    assert "Wenpeng Yin" in records[0]["authors"]


def test_search_json_contains_doi() -> None:
    fetcher = MockFetcherWithSearch()
    with patch("littrail.cli.PyAlexFetcher", return_value=fetcher):
        result = runner.invoke(app, ["search", "zero-shot", "--json"])
    records = json.loads(result.output)
    assert records[0]["doi"] == "10.18653/v1/D19-1404"


def test_search_limit_passed_to_fetcher() -> None:
    fetcher = MockFetcherWithSearch()
    with patch("littrail.cli.PyAlexFetcher", return_value=fetcher):
        runner.invoke(app, ["search", "query", "--limit", "5"])
    assert fetcher.last_search_limit == 5


def test_search_default_limit() -> None:
    fetcher = MockFetcherWithSearch()
    with patch("littrail.cli.PyAlexFetcher", return_value=fetcher):
        runner.invoke(app, ["search", "query"])
    assert fetcher.last_search_limit == 10


def test_search_fetch_error_exits_1() -> None:
    fetcher = MockFetcherWithSearch(search_error=FetchError("network error"))
    with patch("littrail.cli.PyAlexFetcher", return_value=fetcher):
        result = runner.invoke(app, ["search", "query"])
    assert result.exit_code == 1
    assert "Error:" in result.output


def test_search_empty_results() -> None:
    fetcher = MockFetcherWithSearch(search_results=[])
    with patch("littrail.cli.PyAlexFetcher", return_value=fetcher):
        result = runner.invoke(app, ["search", "query"])
    assert result.exit_code == 0
    assert result.output.strip() == ""


def test_search_empty_results_json() -> None:
    fetcher = MockFetcherWithSearch(search_results=[])
    with patch("littrail.cli.PyAlexFetcher", return_value=fetcher):
        result = runner.invoke(app, ["search", "query", "--json"])
    assert result.exit_code == 0
    assert json.loads(result.output) == []


def test_search_multiple_results_table() -> None:
    fetcher = MockFetcherWithSearch(search_results=[SAMPLE_RAW_WORK, SAMPLE_RAW_WORK_ALT])
    with patch("littrail.cli.PyAlexFetcher", return_value=fetcher):
        result = runner.invoke(app, ["search", "NLP"])
    assert result.exit_code == 0
    lines = [l for l in result.output.splitlines() if l.strip()]
    # header + 2 data rows
    assert len(lines) == 3


def test_search_authors_short_single() -> None:
    single_author = {**SAMPLE_RAW_WORK, "authorships": [{"author": {"display_name": "Alice Smith"}}]}
    fetcher = MockFetcherWithSearch(search_results=[single_author])
    with patch("littrail.cli.PyAlexFetcher", return_value=fetcher):
        result = runner.invoke(app, ["search", "NLP"])
    assert "et al." not in result.output
    assert "Alice" in result.output or "Smith" in result.output


def test_search_authors_short_multiple() -> None:
    fetcher = MockFetcherWithSearch()
    with patch("littrail.cli.PyAlexFetcher", return_value=fetcher):
        result = runner.invoke(app, ["search", "NLP"])
    assert "et al." in result.output
