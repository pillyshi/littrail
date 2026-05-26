from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from littrail.openalex import FetchError, PyAlexFetcher

_STUB_WORK = {
    "id": "https://openalex.org/W123",
    "title": "Test Paper",
    "publication_year": 2024,
    "type": "article",
    "doi": "https://doi.org/10.1234/test",
    "authorships": [],
    "primary_location": None,
}


def _make_mock_works(return_value: dict) -> MagicMock:
    mock_works = MagicMock()
    mock_works.return_value.__getitem__ = MagicMock(return_value=return_value)
    return mock_works


def test_fetch_by_doi_calls_works() -> None:
    mock_works = _make_mock_works(_STUB_WORK)
    with patch("littrail.openalex.pyalex.Works", mock_works):
        result = PyAlexFetcher().fetch_by_doi("10.1234/test")
    mock_works.return_value.__getitem__.assert_called_once_with("https://doi.org/10.1234/test")
    assert result["title"] == "Test Paper"


def test_fetch_by_openalex_id_calls_works() -> None:
    mock_works = _make_mock_works(_STUB_WORK)
    with patch("littrail.openalex.pyalex.Works", mock_works):
        result = PyAlexFetcher().fetch_by_openalex_id("https://openalex.org/W123")
    mock_works.return_value.__getitem__.assert_called_once_with("https://openalex.org/W123")
    assert result["id"] == "https://openalex.org/W123"


def test_fetch_by_openalex_id_short_form() -> None:
    mock_works = _make_mock_works(_STUB_WORK)
    with patch("littrail.openalex.pyalex.Works", mock_works):
        PyAlexFetcher().fetch_by_openalex_id("W123")
    mock_works.return_value.__getitem__.assert_called_once_with("https://openalex.org/W123")


def test_fetch_404_raises_fetch_error() -> None:
    mock_works = MagicMock()
    mock_works.return_value.__getitem__ = MagicMock(side_effect=Exception("404 Not Found"))
    with patch("littrail.openalex.pyalex.Works", mock_works):
        with pytest.raises(FetchError, match="not found"):
            PyAlexFetcher().fetch_by_doi("10.1234/missing")


def test_fetch_network_error_raises_fetch_error() -> None:
    mock_works = MagicMock()
    mock_works.return_value.__getitem__ = MagicMock(side_effect=Exception("Connection timeout"))
    with patch("littrail.openalex.pyalex.Works", mock_works):
        with pytest.raises(FetchError, match="Failed to fetch"):
            PyAlexFetcher().fetch_by_doi("10.1234/test")
