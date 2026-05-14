"""Regression tests over local real-world HTML samples."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from html_to_text import html_to_text


CORPUS_LIMIT = int(os.environ.get("HTML_TO_TEXT_CORPUS_LIMIT", "20"))
CORPUS_DIR = Path(__file__).resolve().parents[1] / "sample"


def corpus_files() -> list[Path | None]:
    if not CORPUS_DIR.exists():
        return [None]
    files: list[Path | None] = []
    files.extend(sorted(CORPUS_DIR.glob("*.html"))[:CORPUS_LIMIT])
    return files


@pytest.mark.parametrize("path", corpus_files(), ids=lambda path: "missing" if path is None else path.name)
def test_local_html_corpus_converts_without_crashing(path: Path | None) -> None:
    if path is None:
        pytest.skip("local sample corpus is not present")

    html = path.read_text(encoding="utf-8", errors="replace")
    text = html_to_text(html, file=path.name)

    assert isinstance(text, str)
