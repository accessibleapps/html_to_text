"""Tests for block-level elements (p, div, blockquote, center)."""

import pytest

from tests.conftest import convert


@pytest.mark.parametrize("tag", ["p", "div", "blockquote", "center"])
class TestSingleBlockElement:
    """Test single block elements."""

    def test_single_block_with_text(self, tag):
        html = f"<{tag}>text</{tag}>"
        assert convert(html) == "text"

    def test_empty_block(self, tag):
        html = f"<{tag}></{tag}>"
        assert convert(html) == ""

    def test_block_with_whitespace_only(self, tag):
        html = f"<{tag}>   </{tag}>"
        assert convert(html) == ""


@pytest.mark.parametrize("tag", ["p", "div", "blockquote", "center"])
class TestConsecutiveBlocks:
    """Test multiple block elements in sequence."""

    def test_two_consecutive_blocks(self, tag):
        html = f"<{tag}>first</{tag}><{tag}>second</{tag}>"
        assert convert(html) == "first\n\nsecond"

    def test_three_consecutive_blocks(self, tag):
        html = f"<{tag}>a</{tag}><{tag}>b</{tag}><{tag}>c</{tag}>"
        assert convert(html) == "a\n\nb\n\nc"

    def test_consecutive_blocks_with_whitespace_between(self, tag):
        html = f"<{tag}>first</{tag}>  <{tag}>second</{tag}>"
        # Whitespace between blocks should be ignored
        assert convert(html) == "first\n\nsecond"


class TestMixedBlockTypes:
    """Test different block element types together."""

    def test_p_then_div(self):
        assert convert("<p>para</p><div>div</div>") == "para\n\ndiv"

    def test_div_then_blockquote(self):
        assert convert("<div>div</div><blockquote>quote</blockquote>") == "div\n\nquote"

    def test_all_block_types_together(self):
        html = "<p>p</p><div>div</div><blockquote>quote</blockquote><center>center</center>"
        assert convert(html) == "p\n\ndiv\n\nquote\n\ncenter"


class TestNestedBlocks:
    """Test nested block elements."""

    def test_div_inside_div(self):
        assert convert("<div><div>inner</div></div>") == "inner"

    def test_p_inside_div(self):
        assert convert("<div><p>para</p></div>") == "para"

    def test_deeply_nested_blocks(self):
        assert convert("<div><div><div>deep</div></div></div>") == "deep"

    def test_multiple_nested_blocks(self):
        html = "<div><p>first</p><p>second</p></div>"
        assert convert(html) == "first\n\nsecond"

    def test_sibling_blocks_inside_parent(self):
        html = "<div><p>a</p><p>b</p><p>c</p></div>"
        assert convert(html) == "a\n\nb\n\nc"


class TestBlocksWithInlineContent:
    """Test blocks containing inline elements."""

    def test_block_with_span(self):
        assert convert("<p>text <span>span</span> more</p>") == "text span more"

    def test_block_with_multiple_inline_elements(self):
        html = "<p><span>a</span> <em>b</em> <strong>c</strong></p>"
        assert convert(html) == "a b c"

    def test_nested_inline_in_block(self):
        html = "<div><span>outer <em>inner</em></span></div>"
        assert convert(html) == "outer inner"


class TestBlocksWithMixedContent:
    """Test blocks with text and inline elements mixed."""

    def test_text_before_block(self):
        assert convert("prefix<p>block</p>") == "prefix\n\nblock"

    def test_text_after_block(self):
        assert convert("<p>block</p>suffix") == "block\n\nsuffix"

    def test_text_before_and_after_block(self):
        assert convert("before<p>block</p>after") == "before\n\nblock\n\nafter"

    def test_inline_element_before_block(self):
        assert convert("<span>inline</span><p>block</p>") == "inline\n\nblock"

    def test_inline_element_after_block(self):
        assert convert("<p>block</p><span>inline</span>") == "block\n\ninline"