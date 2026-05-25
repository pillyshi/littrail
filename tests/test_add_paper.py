from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from littrail.catalog import load_catalog
from littrail.cli import app
from littrail.openalex import normalize_work
from tests.fixtures import SAMPLE_RAW_WORK, SAMPLE_RAW_WORK_ALT, MockFetcher

runner = CliRunner()


def _invoke_add_doi(catalog_path: Path, doi: str, fetcher: MockFetcher) -> object:
    with patch("littrail.cli.PyAlexFetcher", return_value=fetcher):
        return runner.invoke(
            app,
            ["add-paper", "--doi", doi, "--catalog", str(catalog_path)],
            catch_exceptions=False,
        )


def _invoke_add_oa(catalog_path: Path, oa_id: str, fetcher: MockFetcher) -> object:
    with patch("littrail.cli.PyAlexFetcher", return_value=fetcher):
        return runner.invoke(
            app,
            ["add-paper", "--openalex", oa_id, "--catalog", str(catalog_path)],
            catch_exceptions=False,
        )


def test_add_paper_by_doi(minimal_catalog_path: Path) -> None:
    fetcher = MockFetcher()
    result = _invoke_add_doi(minimal_catalog_path, "10.18653/v1/D19-1404", fetcher)
    assert result.exit_code == 0  # type: ignore[union-attr]
    cat = load_catalog(minimal_catalog_path)
    assert len(cat.papers) == 1
    paper = cat.papers[0]
    assert paper.key == "yin-2019"
    assert paper.title.startswith("Benchmarking Zero-shot")
    assert paper.identifiers["doi"] == "10.18653/v1/D19-1404"
    assert paper.identifiers["openalex"] == "W2970200208"
    assert paper.relevance == "to_classify"
    assert paper.note_status == "pending"


def test_add_paper_by_openalex_id(minimal_catalog_path: Path) -> None:
    fetcher = MockFetcher()
    result = _invoke_add_oa(minimal_catalog_path, "W2970200208", fetcher)
    assert result.exit_code == 0  # type: ignore[union-attr]
    cat = load_catalog(minimal_catalog_path)
    assert len(cat.papers) == 1


def test_add_paper_duplicate_doi_rejected(minimal_catalog_path: Path) -> None:
    fetcher = MockFetcher()
    _invoke_add_doi(minimal_catalog_path, "10.18653/v1/D19-1404", fetcher)
    result = _invoke_add_doi(minimal_catalog_path, "10.18653/v1/D19-1404", fetcher)
    assert result.exit_code == 0  # type: ignore[union-attr]  # reports and exits 0
    cat = load_catalog(minimal_catalog_path)
    assert len(cat.papers) == 1


def test_add_paper_duplicate_openalex_rejected(minimal_catalog_path: Path) -> None:
    fetcher = MockFetcher()
    _invoke_add_doi(minimal_catalog_path, "10.18653/v1/D19-1404", fetcher)
    # Add again via OpenAlex ID (same work)
    result = _invoke_add_oa(minimal_catalog_path, "W2970200208", fetcher)
    assert result.exit_code == 0  # type: ignore[union-attr]
    cat = load_catalog(minimal_catalog_path)
    assert len(cat.papers) == 1


def test_add_paper_key_collision_suffix(minimal_catalog_path: Path) -> None:
    # Both papers have same first author family name and year → suffix
    fetcher1 = MockFetcher(by_doi=SAMPLE_RAW_WORK)
    fetcher2 = MockFetcher(by_doi=SAMPLE_RAW_WORK_ALT)

    with patch("littrail.cli.PyAlexFetcher", return_value=fetcher1):
        runner.invoke(
            app,
            ["add-paper", "--doi", "10.18653/v1/D19-1404", "--catalog", str(minimal_catalog_path)],
            catch_exceptions=False,
        )
    with patch("littrail.cli.PyAlexFetcher", return_value=fetcher2):
        runner.invoke(
            app,
            ["add-paper", "--doi", "10.18653/v1/D19-9999", "--catalog", str(minimal_catalog_path)],
            catch_exceptions=False,
        )

    cat = load_catalog(minimal_catalog_path)
    keys = {p.key for p in cat.papers}
    assert "yin-2019" in keys
    assert "yin-2019-2" in keys


def test_normalize_work_extracts_fields() -> None:
    entry = normalize_work(SAMPLE_RAW_WORK)
    assert entry.title.startswith("Benchmarking")
    assert entry.authors == ["Wenpeng Yin", "Jamaal Hay", "Dan Roth"]
    assert entry.year == 2019
    assert entry.identifiers["doi"] == "10.18653/v1/D19-1404"
    assert entry.identifiers["openalex"] == "W2970200208"
    assert entry.venue == "EMNLP-IJCNLP 2019"
