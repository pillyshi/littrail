from __future__ import annotations

import os
from pathlib import Path

from typer.testing import CliRunner

from littrail.cli import app

runner = CliRunner()


def test_init_creates_research_structure(tmp_path: Path) -> None:
    os.chdir(tmp_path)
    result = runner.invoke(app, ["init"], catch_exceptions=False)
    assert result.exit_code == 0, result.output
    assert (tmp_path / "research" / "reports" / ".gitkeep").exists()
    assert (tmp_path / "research" / "notes" / ".gitkeep").exists()
    assert (tmp_path / "research" / "ideas" / ".gitkeep").exists()
    assert (tmp_path / "research" / "pdfs").is_dir()
    assert (tmp_path / "research" / "README.md").exists()
    assert (tmp_path / "research" / "catalog.yaml").exists()


def test_init_adds_gitignore_entry(tmp_path: Path) -> None:
    os.chdir(tmp_path)
    result = runner.invoke(app, ["init"], catch_exceptions=False)
    assert result.exit_code == 0
    gitignore = tmp_path / "research" / ".gitignore"
    assert gitignore.exists()
    lines = gitignore.read_text(encoding="utf-8").splitlines()
    assert "pdfs/" in lines


def test_init_does_not_touch_root_gitignore(tmp_path: Path) -> None:
    os.chdir(tmp_path)
    runner.invoke(app, ["init"], catch_exceptions=False)
    assert not (tmp_path / ".gitignore").exists()


def test_init_no_duplicate_gitignore_entry(tmp_path: Path) -> None:
    os.chdir(tmp_path)
    runner.invoke(app, ["init"], catch_exceptions=False)
    runner.invoke(app, ["init"], catch_exceptions=False)
    gitignore = tmp_path / "research" / ".gitignore"
    lines = gitignore.read_text(encoding="utf-8").splitlines()
    assert lines.count("pdfs/") == 1


def test_init_does_not_overwrite_existing_readme(tmp_path: Path) -> None:
    os.chdir(tmp_path)
    runner.invoke(app, ["init"], catch_exceptions=False)
    readme = tmp_path / "research" / "README.md"
    readme.write_text("custom content", encoding="utf-8")
    runner.invoke(app, ["init"], catch_exceptions=False)
    assert readme.read_text(encoding="utf-8") == "custom content"


def test_init_force_overwrites_readme(tmp_path: Path) -> None:
    os.chdir(tmp_path)
    runner.invoke(app, ["init"], catch_exceptions=False)
    readme = tmp_path / "research" / "README.md"
    readme.write_text("custom content", encoding="utf-8")
    runner.invoke(app, ["init", "--force"], catch_exceptions=False)
    assert readme.read_text(encoding="utf-8") != "custom content"
