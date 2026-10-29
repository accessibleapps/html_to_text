from pathlib import Path

import pytest

from html_to_text import html_to_text, tree_from_string


@pytest.mark.parametrize("startpos", [0, 41])
def test_real_block_styles_exclude_preceding_separators(startpos):
    source = (Path(__file__).parent / "fixtures" / "inline-style-positions.html").read_bytes()
    ranges = []
    text = html_to_text(
        tree_from_string(source),
        startpos=startpos,
        style_callback=lambda element, start, end: ranges.append((start, end)),
    )
    expected = [
        "Header with Inline Styles",
        "Green italic paragraph.",
        "Arial paragraph at 12pt.",
    ]
    assert ranges == [
        (startpos + text.index(content), startpos + text.index(content) + len(content))
        for content in expected
    ]
    assert text == (
        "Header with Inline Styles\n\nGreen italic paragraph.\n\n"
        "Arial paragraph at 12pt.\n\nNormal paragraph without styles."
    )


@pytest.mark.parametrize("startpos", [0, 41])
def test_nested_inline_and_block_styles_share_exact_text_offsets(startpos):
    ranges = {}
    text = html_to_text(
        '<div style="color: red">Alpha <span style="font-weight: bold">Beta</span>'
        ' gamma</div><p style="color: blue">Delta</p>',
        startpos=startpos,
        style_callback=lambda element, start, end: ranges.update(
            {element.get("style"): (start, end)}
        ),
    )
    assert text == "Alpha Beta gamma\n\nDelta"
    expected = {
        "color: red": "Alpha Beta gamma",
        "font-weight: bold": "Beta",
        "color: blue": "Delta",
    }
    for style, content in expected.items():
        start = startpos + text.index(content)
        assert ranges[style] == (start, start + len(content))


def test_empty_styled_element_has_an_empty_range():
    ranges = []
    text = html_to_text(
        '<p>Alpha</p><p style="color: red"></p><p>Beta</p>',
        style_callback=lambda element, start, end: ranges.append((start, end)),
    )
    assert text == "Alpha\n\nBeta"
    assert ranges == [(5, 5)]
