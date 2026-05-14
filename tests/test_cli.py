"""Tests for the command-line interface."""

from __future__ import annotations

from io import StringIO
import sys
from pathlib import Path

import html_to_text as html_module
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


def test_cli_reads_stdin_and_writes_stdout(capsys, monkeypatch) -> None:
    monkeypatch.setattr(sys, "argv", ["html-to-text", "-", "-o", "-"])
    monkeypatch.setattr(sys, "stdin", StringIO("<p>stdin</p>"))

    assert main() == 0

    captured = capsys.readouterr()
    assert captured.out == "stdin"
    assert captured.err == ""


def test_cli_missing_input_file_reports_error(tmp_path: Path, capsys, monkeypatch) -> None:
    missing_path = tmp_path / "missing.html"
    monkeypatch.setattr(sys, "argv", ["html-to-text", str(missing_path)])

    assert main() == 1

    captured = capsys.readouterr()
    assert "Input file not found" in captured.err


def test_cli_default_output_uses_current_directory(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    input_path = tmp_path / "input.html"
    input_path.write_text("<p>default</p>", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["html-to-text", str(input_path)])

    assert main() == 0

    output_path = tmp_path / "input.txt"
    assert output_path.read_text(encoding="utf-8") == "default"
    assert "Converted" in capsys.readouterr().out


def test_cli_falls_back_to_latin_1_when_encoding_detection_is_uncertain(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    input_path = tmp_path / "input.html"
    input_path.write_bytes(b"<p>\xff</p>")
    monkeypatch.setattr(
        html_module.chardet,
        "detect",
        lambda data: {"encoding": None, "confidence": 0.0},
    )
    monkeypatch.setattr(sys, "argv", ["html-to-text", str(input_path), "-o", "-"])

    assert main() == 0

    captured = capsys.readouterr()
    assert captured.out == "ÿ"
    assert "latin-1 fallback" in captured.err
