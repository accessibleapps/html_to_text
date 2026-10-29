from pathlib import Path

import pytest

from tests.conftest import convert


def test_real_minified_rust_list_keeps_entries_separate(simple_callback):
    # Verbatim first UL from the existing Rust sample/all.html.
    raw = (Path(__file__).parent / "fixtures" / "rust-navigation-list.html").read_text(
        encoding="utf-8"
    )
    callback, nodes = simple_callback
    text = convert(raw, callback)
    labels = [
        "Primitive Types", "Macros", "Structs", "Enums", "Constants", "Traits",
        "Functions", "Type Definitions", "Unions", "Trait Aliases",
    ]
    assert text == "\n\n".join(labels)
    links = [node for node in nodes if node["type"] == "link"]
    assert len(links) == len(labels)
    assert [text[node["start"]:node["end"]] for node in links] == labels


@pytest.mark.parametrize("tag", ["ul", "ol"])
def test_nested_lists_separate_children_parent_tail_and_next_item(tag):
    raw = (
        f"<{tag}><li>Parent<{tag}><li>Child one</li><li>Child two</li></{tag}>"
        f"Tail</li><li>Next</li></{tag}>"
    )
    assert convert(raw) == "Parent\n\nChild one\n\nChild two\n\nTail\n\nNext"


def test_list_boundaries_do_not_split_inline_content():
    raw = "Before<ul><li>First <span>inline</span></li><li>Second</li></ul>After"
    assert convert(raw) == "Before\n\nFirst inline\n\nSecond\n\nAfter"


def test_empty_items_do_not_duplicate_pending_separators():
    raw = "<ul><li>First</li><li></li><li>Second</li></ul>"
    assert convert(raw) == "First\n\nSecond"
