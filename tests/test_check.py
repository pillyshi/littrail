from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from littrail.catalog import Catalog, PaperEntry, save_catalog
from littrail.checks import run_checks
from littrail.cli import app

runner = CliRunner()


def _make_catalog(tmp_path: Path, papers: list[PaperEntry] | None = None) -> Path:
    catalog = Catalog(
        catalog_version=1,
        project="test",
        verified_on=None,
        verification={"provider": "OpenAlex", "client": "pyalex"},
        source_reports=[],
        papers=papers or [],
    )
    path = tmp_path / "research" / "catalog.yaml"
    save_catalog(catalog, path)
    return path


def _make_root_gitignore(tmp_path: Path, include_pdfs: bool = True) -> None:
    content = "research/pdfs/\n" if include_pdfs else "__pycache__/\n"
    (tmp_path / ".gitignore").write_text(content, encoding="utf-8")


def _make_research_gitignore(tmp_path: Path, include_pdfs: bool = True) -> None:
    content = "pdfs/\n" if include_pdfs else "__pycache__/\n"
    research_dir = tmp_path / "research"
    research_dir.mkdir(parents=True, exist_ok=True)
    (research_dir / ".gitignore").write_text(content, encoding="utf-8")


# Alias kept for existing tests that pass root .gitignore (backward-compat path)
_make_gitignore = _make_root_gitignore


def test_check_minimal_catalog_passes(tmp_path: Path) -> None:
    path = _make_catalog(tmp_path)
    _make_gitignore(tmp_path)
    problems = run_checks(path)
    assert problems == []


def test_check_drafted_note_missing(tmp_path: Path) -> None:
    paper = PaperEntry(
        key="yin-2019",
        title="T",
        authors=["A"],
        year=2019,
        publication_type="article",
        venue="V",
        identifiers={"doi": "10.1/x"},
        note_status="drafted",
    )
    path = _make_catalog(tmp_path, [paper])
    _make_gitignore(tmp_path)
    problems = run_checks(path)
    assert any("notes/yin-2019.md" in p for p in problems)


def test_check_drafted_note_present_passes(tmp_path: Path) -> None:
    paper = PaperEntry(
        key="yin-2019",
        title="T",
        authors=["A"],
        year=2019,
        publication_type="article",
        venue="V",
        identifiers={"doi": "10.1/x"},
        note_status="drafted",
    )
    path = _make_catalog(tmp_path, [paper])
    _make_gitignore(tmp_path)
    notes_dir = tmp_path / "research" / "notes"
    notes_dir.mkdir(parents=True, exist_ok=True)
    (notes_dir / "yin-2019.md").write_text("note", encoding="utf-8")
    problems = run_checks(path)
    assert not any("yin-2019" in p for p in problems)


def test_check_cached_pdf_missing(tmp_path: Path) -> None:
    paper = PaperEntry(
        key="yin-2019",
        title="T",
        authors=["A"],
        year=2019,
        publication_type="article",
        venue="V",
        identifiers={"doi": "10.1/x"},
        pdf_status="cached",
        local_pdf="pdfs/yin-2019.pdf",
    )
    path = _make_catalog(tmp_path, [paper])
    _make_gitignore(tmp_path)
    problems = run_checks(path)
    assert any("yin-2019.pdf" in p for p in problems)


def test_check_local_pdf_outside_pdfs_rejected(tmp_path: Path) -> None:
    paper = PaperEntry(
        key="yin-2019",
        title="T",
        authors=["A"],
        year=2019,
        publication_type="article",
        venue="V",
        identifiers={"doi": "10.1/x"},
        pdf_status="cached",
        local_pdf="../secret.pdf",
    )
    path = _make_catalog(tmp_path, [paper])
    _make_gitignore(tmp_path)
    problems = run_checks(path)
    assert any("outside" in p for p in problems)


def test_check_research_gitignore_passes(tmp_path: Path) -> None:
    path = _make_catalog(tmp_path)
    _make_research_gitignore(tmp_path)
    problems = run_checks(path)
    assert not any("research/pdfs/" in p for p in problems)


def test_check_gitignore_entry_missing(tmp_path: Path) -> None:
    path = _make_catalog(tmp_path)
    _make_gitignore(tmp_path, include_pdfs=False)
    problems = run_checks(path)
    assert any("research/pdfs/" in p for p in problems)


def test_check_no_gitignore(tmp_path: Path) -> None:
    path = _make_catalog(tmp_path)
    # No .gitignore created
    problems = run_checks(path)
    assert any("research/pdfs/" in p for p in problems)


def test_check_cli_exits_zero_on_clean(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    path = _make_catalog(tmp_path)
    _make_gitignore(tmp_path)
    result = runner.invoke(
        app,
        ["check", "--catalog", str(path)],
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    assert "All checks passed" in result.output


def test_check_cli_exits_nonzero_on_problems(tmp_path: Path) -> None:
    paper = PaperEntry(
        key="yin-2019",
        title="T",
        authors=["A"],
        year=2019,
        publication_type="article",
        venue="V",
        identifiers={"doi": "10.1/x"},
        note_status="drafted",
    )
    path = _make_catalog(tmp_path, [paper])
    _make_gitignore(tmp_path)
    result = runner.invoke(
        app,
        ["check", "--catalog", str(path)],
    )
    assert result.exit_code != 0
