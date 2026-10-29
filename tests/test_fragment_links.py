"""Resolve archive-local links using the complete current document URI."""

from pathlib import Path

import pytest

from tests.conftest import convert


def test_rust_fragment_link_matches_current_document_id(simple_callback):
    # Verbatim anchor and target from the existing Rust sample/all.html.
    raw = (Path(__file__).parent / "fixtures" / "rust-fragment-link.html").read_text(
        encoding="utf-8"
    )
    callback, nodes = simple_callback
    text = convert(raw, callback, file="docs/all.html")

    link = next(node for node in nodes if node["type"] == "link")
    target = next(node for node in nodes if node["type"] == "id")
    assert link["href"] == "docs/all.html#primitives"
    assert link["href"] == target["name"]
    assert text[link["start"]:link["end"]] == "Primitive Types"


@pytest.mark.parametrize(
    "reference, expected",
    [
        ("#part%201", "docs/chapter 1.html#part 1"),
        ("?view=plain#part", "docs/chapter 1.html?view=plain#part"),
        ("", "docs/chapter 1.html"),
        ("next%20chapter.html?view=plain#part", "docs/next chapter.html?view=plain#part"),
        ("../chapter%202.html#part", "chapter 2.html#part"),
        ("/root%20chapter.html#part", "/root chapter.html#part"),
    ],
)
def test_relative_uri_components_keep_their_meaning(reference, expected, simple_callback):
    callback, nodes = simple_callback
    convert('<a href="{}">target</a>'.format(reference), callback, file="docs/chapter 1.html")
    link = next(node for node in nodes if node["type"] == "link")
    assert link["href"] == expected


def test_fragment_retains_current_document_query(simple_callback):
    callback, nodes = simple_callback
    convert('<a href="#part">target</a>', callback, file="docs/chapter.html?view=plain")
    link = next(node for node in nodes if node["type"] == "link")
    assert link["href"] == "docs/chapter.html?view=plain#part"
