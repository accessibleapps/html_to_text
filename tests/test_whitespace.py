"""Tests for whitespace normalization - the most complex parsing behavior."""

import pytest

from tests.conftest import convert


class TestBasicNormalization:
    """Test basic whitespace collapsing."""

    def test_multiple_spaces_collapse_to_single(self):
        assert convert("<p>a    b</p>") == "a b"

    def test_multiple_newlines_collapse_to_single_space(self):
        assert convert("<p>a\n\n\nb</p>") == "a b"

    def test_tabs_collapse_to_single_space(self):
        assert convert("<p>a\t\tb</p>") == "a b"

    def test_mixed_whitespace_collapses(self):
        assert convert("<p>a \t\n  b</p>") == "a b"

    def test_nbsp_normalized_to_space(self):
        # Non-breaking space is normalized to regular space
        assert convert("<p>a\u00a0b</p>") == "a b"


class TestInlineElementSpacing:
    """Test whitespace between inline elements."""

    def test_consecutive_spans_preserve_single_space(self):
        # <span>a</span> <span>b</span> → "a b" not "a  b"
        assert convert("<span>a</span> <span>b</span>") == "a b"

    def test_span_with_trailing_space_then_span(self):
        assert convert("<span>a </span><span>b</span>") == "a b"

    def test_consecutive_spans_no_space(self):
        assert convert("<span>a</span><span>b</span>") == "ab"

    def test_em_and_strong_with_space(self):
        assert convert("<em>word</em> <strong>word</strong>") == "word word"

    def test_multiple_inline_elements_chain(self):
        assert convert("<span>a</span> <em>b</em> <strong>c</strong>") == "a b c"

    def test_nested_inline_elements(self):
        assert convert("<span>a <em>b</em> c</span>") == "a b c"

    def test_inline_with_internal_spaces(self):
        assert convert("<span>a  b</span> <span>c  d</span>") == "a b c d"


class TestLeadingTrailingWhitespace:
    """Test handling of leading and trailing whitespace."""

    def test_paragraph_leading_space_stripped(self):
        # Leading space at start of document is stripped
        assert convert("<p> leading</p>") == "leading"

    def test_paragraph_trailing_space_stripped(self):
        assert convert("<p>trailing </p>") == "trailing"

    def test_paragraph_both_leading_trailing_stripped(self):
        assert convert("<p> both </p>") == "both"

    def test_document_starting_space_stripped(self):
        assert convert(" text") == "text"

    def test_document_ending_space_stripped(self):
        assert convert("text ") == "text"

    def test_span_leading_space_preserved_mid_document(self):
        # Space before span is preserved when not at document start
        assert convert("text <span>more</span>") == "text more"

    def test_span_trailing_space_preserved(self):
        assert convert("<span>text</span> more") == "text more"


class TestWhitespaceAfterNewlines:
    """Test whitespace handling after newlines."""

    def test_consecutive_paragraphs_no_extra_space(self):
        # <p>text</p> <p>more</p> should not have space between blocks
        result = convert("<p>text</p> <p>more</p>")
        # Blocks separated by \n\n, document boundaries trimmed
        assert result == "text\n\nmore"

    def test_consecutive_divs_no_extra_space(self):
        result = convert("<div>a</div> <div>b</div>")
        assert result == "a\n\nb"

    def test_br_followed_by_space(self):
        # Space after <br> should be handled correctly
        assert convert("text<br> more") == "text\nmore"

    def test_br_followed_by_inline_element(self):
        assert convert("text<br><span>more</span>") == "text\nmore"


class TestEmptyAndWhitespaceOnly:
    """Test edge cases with empty or whitespace-only content."""

    def test_empty_text_nodes_between_tags(self):
        assert convert("<span></span><span>text</span>") == "text"

    def test_whitespace_only_between_inline_elements(self):
        assert convert("<span>a</span>   <span>b</span>") == "a b"

    def test_whitespace_only_paragraph(self):
        assert convert("<p>   </p>") == ""

    def test_multiple_whitespace_only_paragraphs(self):
        result = convert("<p>  </p><p>  </p>")
        assert result == ""

    def test_paragraph_with_only_newlines(self):
        assert convert("<p>\n\n\n</p>") == ""


class TestStartingState:
    """Test the 'starting' flag behavior."""

    def test_document_starts_without_leading_newline(self):
        # First text should not have leading whitespace
        assert convert("text") == "text"

    def test_document_starts_with_inline_element(self):
        assert convert("<span>text</span>") == "text"

    def test_document_starts_with_space_in_inline(self):
        # Leading space in first element stripped
        assert convert("<span> text</span>") == "text"

    def test_block_at_document_start(self):
        # Block elements at document boundaries have newlines trimmed
        assert convert("<p>text</p>") == "text"


class TestComplexWhitespaceScenarios:
    """Test complex real-world whitespace scenarios."""

    def test_inline_elements_in_paragraph(self):
        html = "<p>This is <em>emphasized</em> and <strong>strong</strong> text.</p>"
        assert convert(html) == "This is emphasized and strong text."

    def test_multiple_spaces_before_inline_element(self):
        assert convert("<p>text    <span>more</span></p>") == "text more"

    def test_nested_spans_with_spaces(self):
        html = "<span>outer <span>inner</span> outer</span>"
        assert convert(html) == "outer inner outer"

    def test_line_breaks_with_surrounding_text(self):
        html = "line1<br>line2<br>line3"
        assert convert(html) == "line1\nline2\nline3"

    def test_paragraph_with_line_break(self):
        html = "<p>first line<br>second line</p>"
        assert convert(html) == "first line\nsecond line"

    def test_whitespace_around_nested_blocks(self):
        html = "<div> <p>text</p> </div>"
        assert convert(html) == "text"