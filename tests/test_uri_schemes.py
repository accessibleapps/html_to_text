"""Preserve external URI references when extracting archived HTML links."""

from pathlib import Path

import pytest

from tests.conftest import convert


def test_nvda_mailto_link_keeps_scheme_and_text_range(simple_callback):
    # Verbatim anchor from NVDA's existing sample/changes.html.
    source = (Path(__file__).parent / "fixtures" / "nvda-mailto.html").read_text(
        encoding="utf-8"
    )
    callback, nodes = simple_callback

    text = convert(source, callback, file="docs/changes.html")

    link = next(node for node in nodes if node["type"] == "link")
    assert link["href"] == "mailto:info@nvaccess.org"
    assert text[link["start"]:link["end"]] == "info@nvaccess.org"


@pytest.mark.parametrize(
    "href",
    [
        "mailto:info@nvaccess.org?subject=Screen%20reader",
        "tel:+15551234567",
        "urn:isbn:9780140328721",
        "https://example.org/a%20page",
        "//example.org/a%20page",
    ],
)
def test_external_references_are_preserved(href, simple_callback):
    callback, nodes = simple_callback

    convert(f'<a href="{href}">target</a>', callback, file="docs/current.html")

    link = next(node for node in nodes if node["type"] == "link")
    assert link["href"] == href


@pytest.mark.parametrize(
    ("href", "expected"),
    [
        ("next.html", "docs/next.html"),
        ("../chapter%201.html", "chapter 1.html"),
        ("sub/chapter%202.html#section", "docs/sub/chapter 2.html#section"),
    ],
)
def test_relative_references_keep_archive_path_resolution(href, expected, simple_callback):
    callback, nodes = simple_callback

    convert(f'<a href="{href}">target</a>', callback, file="docs/current.html")

    link = next(node for node in nodes if node["type"] == "link")
    assert link["href"] == expected
