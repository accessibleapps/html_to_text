"""Tests for edge cases, empty documents, and malformed HTML."""

import pytest

from tests.conftest import convert


class TestEmptyAndMinimal:
    """Test empty and minimal documents."""

    def test_empty_string(self):
        # lxml raises ParserError on empty documents
        from lxml.etree import ParserError
        with pytest.raises(ParserError):
            convert("")

    def test_whitespace_only(self):
        # lxml raises ParserError on whitespace-only documents
        from lxml.etree import ParserError
        with pytest.raises(ParserError):
            convert("   ")

    def test_newlines_only(self):
        # lxml raises ParserError on newline-only documents
        from lxml.etree import ParserError
        with pytest.raises(ParserError):
            convert("\n\n\n")

    def test_single_character(self):
        assert convert("a") == "a"

    def test_single_word(self):
        assert convert("word") == "word"

    def test_empty_paragraph(self):
        assert convert("<p></p>") == ""

    def test_empty_div(self):
        assert convert("<div></div>") == ""

    def test_empty_heading(self):
        assert convert("<h1></h1>") == ""

    def test_only_whitespace_in_paragraph(self):
        assert convert("<p>   </p>") == ""


class TestMalformedHTML:
    """Test handling of malformed HTML (lxml fixes these)."""

    def test_unclosed_tag(self):
        # lxml will close the tag
        html = "<p>text"
        result = convert(html)
        assert "text" in result

    def test_mismatched_tags(self):
        # lxml will fix nesting
        html = "<p><div>text</div></p>"
        result = convert(html)
        assert "text" in result

    def test_overlapping_tags(self):
        html = "<p>start<b>bold</p>end</b>"
        result = convert(html)
        assert "start" in result
        assert "bold" in result

    def test_invalid_tag_name(self):
        # Unknown tags are ignored
        html = "<invalid>text</invalid>"
        assert convert(html) == "text"

    def test_tag_without_closing(self):
        html = "<p>paragraph<p>another"
        result = convert(html)
        assert "paragraph" in result
        assert "another" in result


class TestDeepNesting:
    """Test deeply nested structures."""

    def test_deeply_nested_divs(self):
        html = "<div>" * 20 + "text" + "</div>" * 20
        assert convert(html) == "text"

    def test_deeply_nested_spans(self):
        html = "<span>" * 20 + "text" + "</span>" * 20
        assert convert(html) == "text"

    def test_mixed_deep_nesting(self):
        html = "<div><p><span><em>text</em></span></p></div>" * 5
        result = convert(html)
        assert result.count("text") == 5


class TestTailText:
    """Test tail text handling on various elements."""

    def test_tail_after_inline(self):
        html = "<span>span</span>tail"
        assert convert(html) == "spantail"

    def test_tail_after_block(self):
        html = "<p>para</p>tail"
        assert convert(html) == "para\n\ntail"

    def test_tail_after_heading(self):
        html = "<h1>heading</h1>tail"
        assert convert(html) == "heading\n\ntail"

    def test_tail_after_pre(self):
        html = "<pre>pre</pre>tail"
        assert convert(html) == "\npretail"

    def test_tail_after_ignored(self):
        html = "<script>ignored</script>tail"
        assert convert(html) == "tail"

    def test_multiple_tails(self):
        html = "<span>a</span>t1<span>b</span>t2<span>c</span>t3"
        assert convert(html) == "at1bt2ct3"


class TestSpecialCharacters:
    """Test special character handling."""

    def test_ampersand_entity(self):
        html = "<p>A &amp; B</p>"
        assert convert(html) == "A & B"

    def test_lt_gt_entities(self):
        html = "<p>&lt;tag&gt;</p>"
        assert convert(html) == "<tag>"

    def test_nbsp_entity(self):
        html = "<p>A&nbsp;B</p>"
        # nbsp is normalized to regular space
        assert convert(html) == "A B"

    def test_unicode_characters(self):
        html = "<p>Café naïve</p>"
        assert convert(html) == "Café naïve"

    def test_emoji(self):
        html = "<p>Hello 👋 World</p>"
        assert convert(html) == "Hello 👋 World"


class TestComments:
    """Test HTML comment handling."""

    def test_comment_ignored(self):
        html = "<!-- comment -->text"
        assert convert(html) == "text"

    def test_comment_between_elements(self):
        html = "<p>before</p><!-- comment --><p>after</p>"
        result = convert(html)
        assert "before" in result
        assert "after" in result
        assert "comment" not in result

    def test_comment_inside_element(self):
        html = "<p>text<!-- comment -->more</p>"
        result = convert(html)
        assert "text" in result
        assert "more" in result
        assert "comment" not in result


class TestAttributeEdgeCases:
    """Test edge cases with attributes."""

    def test_attribute_without_value(self):
        html = '<input disabled>'
        # Input tags may not have text content
        result = convert(html)
        assert result == ""

    def test_attribute_with_quotes(self):
        html = '<a href="url with spaces">text</a>'
        assert convert(html) == "text"

    def test_multiple_classes(self):
        html = '<div class="class1 class2">text</div>'
        assert convert(html) == "text"

    def test_data_attributes(self):
        html = '<div data-foo="bar">text</div>'
        assert convert(html) == "text"


class TestMixedContent:
    """Test elements with mixed text and element content."""

    def test_text_element_text(self):
        html = "<p>before<span>middle</span>after</p>"
        assert convert(html) == "beforemiddleafter"

    def test_multiple_mixed_elements(self):
        html = "<p>a<em>b</em>c<strong>d</strong>e</p>"
        assert convert(html) == "abcde"

    def test_nested_mixed_content(self):
        html = "<p>a<span>b<em>c</em>d</span>e</p>"
        assert convert(html) == "abcde"


class TestSelfClosingTags:
    """Test self-closing tags."""

    def test_br_self_closing(self):
        html = "line1<br/>line2"
        assert convert(html) == "line1\nline2"

    def test_hr_self_closing(self):
        html = "text<hr/>more"
        result = convert(html)
        assert "text" in result
        assert "more" in result

    def test_img_tag(self):
        # IMG tags have no text content
        html = '<img src="image.jpg">text'
        result = convert(html)
        assert "text" in result


class TestDocumentBoundaryTrimming:
    """Test trimming at document boundaries."""

    def test_leading_newlines_trimmed(self):
        html = "<p>text</p>"
        # Paragraph adds \n\n before but document start trimmed
        assert convert(html) == "text"

    def test_trailing_newlines_trimmed(self):
        html = "<p>text</p>"
        # Paragraph adds \n\n after but document end trimmed
        assert convert(html) == "text"

    def test_both_boundaries_trimmed(self):
        html = "<div><p>text</p></div>"
        assert convert(html) == "text"

    def test_internal_newlines_preserved(self):
        html = "<p>a</p><p>b</p>"
        assert convert(html) == "a\n\nb"