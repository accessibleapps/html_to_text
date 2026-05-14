"""Tests for the command-line interface."""

from __future__ import annotations

import sys
from pathlib import Path

from html_to_text import main


def test_cli_writes_stdout_from_file(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    input_path = tmp_path / "input.html"
    input_path.write_text("<h1>Title</h1><p>Body</p>", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["html-to-text", str(input_path), "-o", "-"])

    assert main() == 0

    captured = capsys.readouterr()
    assert captured.out == "Title\n\nBody"
    assert captured.err == ""


def test_cli_refuses_to_overwrite_without_force(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    input_path = tmp_path / "input.html"
    output_path = tmp_path / "output.txt"
    input_path.write_text("<p>new</p>", encoding="utf-8")
    output_path.write_text("old", encoding="utf-8")
    monkeypatch.setattr(
        sys,
        "argv",
        ["html-to-text", str(input_path), "-o", str(output_path)],
    )

    assert main() == 1

    captured = capsys.readouterr()
    assert "already exists" in captured.err
    assert output_path.read_text(encoding="utf-8") == "old"


def test_cli_overwrites_with_force(tmp_path: Path, monkeypatch) -> None:
    input_path = tmp_path / "input.html"
    output_path = tmp_path / "output.txt"
    input_path.write_text("<p>new</p>", encoding="utf-8")
    output_path.write_text("old", encoding="utf-8")
    monkeypatch.setattr(
        sys,
        "argv",
        ["html-to-text", str(input_path), "-o", str(output_path), "--force", "--quiet"],
    )

    assert main() == 0
    assert output_path.read_text(encoding="utf-8") == "new"
