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


def test_cli_stdin_defaults_to_stdout(capsys, monkeypatch) -> None:
    monkeypatch.setattr(sys, "argv", ["html-to-text", "-"])
    monkeypatch.setattr(sys, "stdin", StringIO("<p>implicit stdout</p>"))

    assert main() == 0

    assert capsys.readouterr().out == "implicit stdout"


def test_cli_default_output_for_non_html_input(tmp_path: Path, monkeypatch) -> None:
    input_path = tmp_path / "input.xhtml"
    input_path.write_text("<p>xhtml</p>", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["html-to-text", str(input_path), "--quiet"])

    assert main() == 0

    assert (tmp_path / "input.xhtml.txt").read_text(encoding="utf-8") == "xhtml"


def test_cli_uses_detected_encoding_when_confident(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    input_path = tmp_path / "input.html"
    input_path.write_bytes(b"<p>\x93quote\x94</p>")
    monkeypatch.setattr(
        html_module.chardet,
        "detect",
        lambda data: {"encoding": "windows-1252", "confidence": 0.99},
    )
    monkeypatch.setattr(sys, "argv", ["html-to-text", str(input_path), "-o", "-"])

    assert main() == 0

    captured = capsys.readouterr()
    assert captured.out == "“quote”"
    assert "windows-1252" in captured.err


def test_cli_reports_read_errors(tmp_path: Path, capsys, monkeypatch) -> None:
    input_path = tmp_path / "input.html"
    input_path.write_text("<p>unreadable</p>", encoding="utf-8")

    def raise_os_error(self: Path, encoding: str = "utf-8") -> str:
        raise OSError("read failed")

    monkeypatch.setattr(Path, "read_text", raise_os_error)
    monkeypatch.setattr(sys, "argv", ["html-to-text", str(input_path), "-o", "-"])

    assert main() == 1

    assert "Error reading input" in capsys.readouterr().err


def test_cli_reports_conversion_errors(capsys, monkeypatch) -> None:
    monkeypatch.setattr(sys, "argv", ["html-to-text", "-", "-o", "-"])
    monkeypatch.setattr(sys, "stdin", StringIO("<p>broken</p>"))
    monkeypatch.setattr(
        html_module,
        "html_to_text",
        lambda html: (_ for _ in ()).throw(ValueError("convert failed")),
    )

    assert main() == 1

    assert "Error converting HTML" in capsys.readouterr().err


def test_cli_reports_write_errors(tmp_path: Path, capsys, monkeypatch) -> None:
    input_path = tmp_path / "input.html"
    output_path = tmp_path / "output.txt"
    input_path.write_text("<p>unwritable</p>", encoding="utf-8")

    def raise_os_error(self: Path, data: str, encoding: str = "utf-8") -> int:
        raise OSError("write failed")

    monkeypatch.setattr(Path, "write_text", raise_os_error)
    monkeypatch.setattr(
        sys,
        "argv",
        ["html-to-text", str(input_path), "-o", str(output_path)],
    )

    assert main() == 1

    assert "Error writing output" in capsys.readouterr().err
