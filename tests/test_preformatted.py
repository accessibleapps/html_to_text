"""Tests for preformatted content (pre and code tags)."""

import pytest

from tests.conftest import convert


@pytest.mark.parametrize("tag", ["pre", "code"])
class TestPreformattedBasics:
    """Test basic pre/code tag behavior."""

    def test_preserves_single_space(self, tag):
        html = f"<{tag}>a b</{tag}>"
        assert convert(html) == "\na b"

    def test_preserves_multiple_spaces(self, tag):
        html = f"<{tag}>a    b</{tag}>"
        assert convert(html) == "\na    b"

    def test_preserves_newlines(self, tag):
        html = f"<{tag}>a\nb</{tag}>"
        assert convert(html) == "\na\nb"

    def test_preserves_multiple_newlines(self, tag):
        html = f"<{tag}>a\n\n\nb</{tag}>"
        assert convert(html) == "\na\n\n\nb"

    def test_preserves_tabs(self, tag):
        html = f"<{tag}>a\tb</{tag}>"
        assert convert(html) == "\na\tb"

    def test_preserves_mixed_whitespace(self, tag):
        html = f"<{tag}>a  \t\n  b</{tag}>"
        assert convert(html) == "\na  \t\n  b"


@pytest.mark.parametrize("tag", ["pre", "code"])
class TestPreformattedLeadingTrailing:
    """Test leading and trailing whitespace in pre/code."""

    def test_preserves_leading_space(self, tag):
        html = f"<{tag}> leading</{tag}>"
        assert convert(html) == "\n leading"

    def test_preserves_trailing_space(self, tag):
        html = f"<{tag}>trailing </{tag}>"
        assert convert(html) == "\ntrailing "

    def test_preserves_leading_newline(self, tag):
        html = f"<{tag}>\ntext</{tag}>"
        assert convert(html) == "\n\ntext"

    def test_preserves_trailing_newline(self, tag):
        html = f"<{tag}>text\n</{tag}>"
        assert convert(html) == "\ntext\n"

    def test_preserves_leading_trailing_whitespace(self, tag):
        html = f"<{tag}>  text  </{tag}>"
        assert convert(html) == "\n  text  "


@pytest.mark.parametrize("tag", ["pre", "code"])
class TestPreformattedEmpty:
    """Test empty pre/code tags."""

    def test_empty_tag(self, tag):
        html = f"<{tag}></{tag}>"
        # Document boundary trimming removes the leading newline
        assert convert(html) == ""

    def test_whitespace_only(self, tag):
        html = f"<{tag}>   </{tag}>"
        assert convert(html) == "\n   "

    def test_newlines_only(self, tag):
        html = f"<{tag}>\n\n</{tag}>"
        assert convert(html) == "\n\n\n"


class TestPreformattedWithOtherElements:
    """Test pre/code with surrounding elements."""

    def test_text_before_pre(self):
        assert convert("text<pre>pre</pre>") == "text\npre"

    def test_text_after_pre(self):
        # Tail text follows immediately (no newline separator)
        assert convert("<pre>pre</pre>text") == "\npretext"

    def test_text_before_and_after_pre(self):
        # Tail text follows immediately
        assert convert("before<pre>pre</pre>after") == "before\npreafter"

    def test_paragraph_then_pre(self):
        assert convert("<p>para</p><pre>pre</pre>") == "para\npre"

    def test_pre_then_paragraph(self):
        # Paragraph adds \n\n before itself
        assert convert("<pre>pre</pre><p>para</p>") == "\npre\n\npara"

    def test_consecutive_pre_tags(self):
        assert convert("<pre>first</pre><pre>second</pre>") == "\nfirst\nsecond"


class TestNestedPreAndCode:
    """Test nested pre/code tags."""

    def test_code_inside_pre(self):
        html = "<pre><code>code</code></pre>"
        # Both are pre tags, whitespace preserved
        assert convert(html) == "\ncode"

    def test_pre_inside_code(self):
        html = "<code><pre>pre</pre></code>"
        # Nested pre tags don't double the leading newline
        assert convert(html) == "\npre"

    def test_span_inside_pre(self):
        # Inline elements inside pre should not affect whitespace
        html = "<pre>before<span>  span  </span>after</pre>"
        assert convert(html) == "\nbefore  span  after"


class TestPreformattedRealWorld:
    """Test realistic pre/code scenarios."""

    def test_code_block_indented(self):
        html = "<pre>def foo():\n    return 42</pre>"
        assert convert(html) == "\ndef foo():\n    return 42"

    def test_code_block_with_blank_lines(self):
        html = "<pre>line1\n\nline2</pre>"
        assert convert(html) == "\nline1\n\nline2"

    def test_ascii_art(self):
        art = "  /\\_/\\\n ( o.o )\n  > ^ <"
        html = f"<pre>{art}</pre>"
        assert convert(html) == f"\n{art}"

    def test_preformatted_table(self):
        table = "col1    col2\nval1    val2"
        html = f"<pre>{table}</pre>"
        assert convert(html) == f"\n{table}"


class TestPreformattedInBlocks:
    """Test pre/code inside block elements."""

    def test_pre_inside_div(self):
        html = "<div><pre>pre</pre></div>"
        assert convert(html) == "\npre"

    def test_pre_inside_paragraph(self):
        html = "<p><pre>pre</pre></p>"
        assert convert(html) == "\npre"

    def test_multiple_pre_in_div(self):
        html = "<div><pre>first</pre><pre>second</pre></div>"
        assert convert(html) == "\nfirst\nsecond"


class TestPreformattedStateManagement:
    """Test that pre mode is entered and exited correctly."""

    def test_pre_does_not_affect_following_text(self):
        html = "<pre>a  b</pre><p>c  d</p>"
        # Pre preserves spaces, but paragraph should normalize
        # Paragraph adds \n\n before itself
        assert convert(html) == "\na  b\n\nc d"

    def test_text_does_not_affect_pre(self):
        html = "<p>a  b</p><pre>c  d</pre>"
        # Paragraph normalizes, pre preserves
        assert convert(html) == "a b\nc  d"

    def test_multiple_pre_tags_independent(self):
        html = "<pre>a  b</pre>text<pre>c  d</pre>"
        # Each pre tag should work independently
        # Tail text follows immediately after closing tag
        assert convert(html) == "\na  btext\nc  d"