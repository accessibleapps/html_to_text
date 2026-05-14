"""Property-based tests for parser invariants."""

from __future__ import annotations

from html import escape
from typing import Any

from hypothesis import given, settings
from hypothesis import strategies as st

from html_to_text import html_to_text


INLINE_TAGS = ("span", "em", "strong", "b", "i", "u", "a")
BLOCK_TAGS = ("p", "div", "blockquote", "center", "h1", "h2", "h3")
IGNORED_TAGS = ("script", "style", "title")


def escaped_text() -> st.SearchStrategy[str]:
    """Text safe to embed in generated HTML."""
    return st.text(
        alphabet=st.characters(
            blacklist_categories=("Cc", "Cs"),
            blacklist_characters="<>&",
        ),
        max_size=20,
    ).map(escape)


@st.composite
def html_fragments(draw: st.DrawFn, max_depth: int = 3) -> str:
    """Generate small, parseable HTML fragments."""
    if max_depth <= 0:
        return draw(escaped_text())

    choice = draw(st.integers(min_value=0, max_value=5))
    if choice == 0:
        return draw(escaped_text())

    if choice == 1:
        tag = draw(st.sampled_from(INLINE_TAGS))
        content = draw(html_fragments(max_depth=max_depth - 1))
        if tag == "a":
            href = draw(
                st.sampled_from(
                    ("chapter.html", "./next.html", "../up.html", "#section")
                )
            )
            return f'<a href="{href}">{content}</a>'
        return f"<{tag}>{content}</{tag}>"

    if choice == 2:
        tag = draw(st.sampled_from(BLOCK_TAGS))
        content = draw(html_fragments(max_depth=max_depth - 1))
        return f"<{tag}>{content}</{tag}>"

    if choice == 3:
        before = draw(html_fragments(max_depth=max_depth - 1))
        after = draw(html_fragments(max_depth=max_depth - 1))
        return f"{before}<br>{after}"

    if choice == 4:
        tag = draw(st.sampled_from(IGNORED_TAGS))
        ignored = draw(escaped_text())
        visible = draw(html_fragments(max_depth=max_depth - 1))
        return f"<{tag}>{ignored}</{tag}>{visible}"

    cells = draw(st.lists(escaped_text(), min_size=1, max_size=3))
    row = "".join(f"<td>{cell}</td>" for cell in cells)
    return f"<table><tr>{row}</tr></table>"


@settings(max_examples=200, deadline=None)
@given(html_fragments())
def test_conversion_is_deterministic(fragment: str) -> None:
    assert html_to_text(fragment) == html_to_text(fragment)


@settings(max_examples=200, deadline=None)
@given(html_fragments())
def test_callback_positions_are_in_output_bounds(fragment: str) -> None:
    nodes: list[dict[str, Any]] = []
    counter = {"id": 0}

    def callback(parent: object, node_type: str, content: object, **kwargs: Any) -> dict[str, Any]:
        counter["id"] += 1
        node = {
            "id": counter["id"],
            "parent": parent,
            "type": node_type,
            "content": content,
            **kwargs,
        }
        nodes.append(node)
        return node

    text = html_to_text(fragment, node_parsed_callback=callback, file="chapter.html")
    for node in nodes:
        start = node.get("start")
        end = node.get("end")
        if start is not None:
            assert 0 <= start <= len(text), node
        if end is not None:
            assert 0 <= end <= len(text), node
        if start is not None and end is not None:
            assert start <= end, node


@settings(max_examples=100, deadline=None)
@given(
    before=escaped_text(),
    after=escaped_text(),
    tag=st.sampled_from(IGNORED_TAGS),
)
def test_ignored_tag_content_does_not_leak(before: str, after: str, tag: str) -> None:
    marker = "UNIQUE_IGNORED_MARKER"
    html = f"{before}<{tag}>{marker}</{tag}>{after}"

    assert marker not in html_to_text(html)


@settings(max_examples=100, deadline=None)
@given(text=st.text(alphabet=st.sampled_from(["a", "b", " ", "\t", "\n"]), min_size=1))
def test_normal_text_never_contains_tabs(text: str) -> None:
    assert "\t" not in html_to_text(f"<p>{escape(text)}</p>")


@settings(max_examples=100, deadline=None)
@given(text=st.text(alphabet=st.sampled_from(["a", "b", " ", "\t", "\n"]), min_size=1))
def test_pre_text_preserves_tabs(text: str) -> None:
    assume_has_tab = "\t" in text
    rendered = html_to_text(f"<pre>{escape(text)}</pre>")
    if assume_has_tab:
        assert "\t" in rendered
