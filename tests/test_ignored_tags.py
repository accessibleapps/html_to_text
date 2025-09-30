"""Tests for ignored tag content (script, style, title)."""

import pytest

from tests.conftest import convert


@pytest.mark.parametrize("tag", ["script", "style", "title"])
class TestBasicIgnoredTags:
    """Test basic ignored tag behavior."""

    def test_content_omitted(self, tag):
        html = f"<{tag}>content</{tag}>"
        assert convert(html) == ""

    def test_empty_tag(self, tag):
        html = f"<{tag}></{tag}>"
        assert convert(html) == ""

    def test_whitespace_ignored(self, tag):
        html = f"<{tag}>   </{tag}>"
        assert convert(html) == ""

    def test_newlines_ignored(self, tag):
        html = f"<{tag}>\n\n\n</{tag}>"
        assert convert(html) == ""


@pytest.mark.parametrize("tag", ["script", "style", "title"])
class TestIgnoredTagsWithText:
    """Test ignored tags with surrounding text."""

    def test_text_before_ignored(self, tag):
        html = f"before<{tag}>ignored</{tag}>"
        assert convert(html) == "before"

    def test_text_after_ignored(self, tag):
        html = f"<{tag}>ignored</{tag}>after"
        assert convert(html) == "after"

    def test_text_before_and_after_ignored(self, tag):
        html = f"before<{tag}>ignored</{tag}>after"
        # Title tag adds block spacing, others don't
        if tag == "title":
            assert convert(html) == "before\n\nafter"
        else:
            assert convert(html) == "beforeafter"


@pytest.mark.parametrize("tag", ["script", "style", "title"])
class TestConsecutiveIgnoredTags:
    """Test multiple ignored tags in sequence."""

    def test_two_consecutive_ignored(self, tag):
        html = f"<{tag}>first</{tag}><{tag}>second</{tag}>"
        assert convert(html) == ""

    def test_three_consecutive_ignored(self, tag):
        html = f"<{tag}>a</{tag}><{tag}>b</{tag}><{tag}>c</{tag}>"
        assert convert(html) == ""


class TestMixedIgnoredTags:
    """Test different ignored tag types together."""

    def test_script_then_style(self):
        assert convert("<script>js</script><style>css</style>") == ""

    def test_all_ignored_types(self):
        html = "<script>js</script><style>css</style><title>Title</title>"
        assert convert(html) == ""

    def test_text_between_ignored_tags(self):
        html = "<script>js</script>text<style>css</style>"
        assert convert(html) == "text"


class TestIgnoredTagsInBlocks:
    """Test ignored tags inside block elements."""

    def test_script_inside_paragraph(self):
        assert convert("<p><script>ignored</script></p>") == ""

    def test_style_inside_div(self):
        assert convert("<div><style>ignored</style></div>") == ""

    def test_text_and_script_in_paragraph(self):
        html = "<p>text<script>ignored</script></p>"
        assert convert(html) == "text"

    def test_script_between_paragraphs(self):
        html = "<p>first</p><script>ignored</script><p>second</p>"
        assert convert(html) == "first\n\nsecond"


class TestNestedIgnoredTags:
    """Test nested ignored tags."""

    def test_div_inside_script(self):
        # Everything inside script is ignored, even nested tags
        assert convert("<script><div>content</div></script>") == ""

    def test_span_inside_style(self):
        assert convert("<style><span>content</span></style>") == ""

    def test_paragraph_inside_script(self):
        assert convert("<script><p>content</p></script>") == ""


class TestIgnoredTagsWithComplexContent:
    """Test ignored tags with various content."""

    def test_script_with_javascript(self):
        js = "function foo() { return 'bar'; }"
        assert convert(f"<script>{js}</script>") == ""

    def test_style_with_css(self):
        css = ".foo { color: red; }"
        assert convert(f"<style>{css}</style>") == ""

    def test_script_with_special_characters(self):
        js = "var x = '<div>'; alert('hi');"
        assert convert(f"<script>{js}</script>") == ""


class TestIgnoredTagsWithHeadings:
    """Test ignored tags with heading elements."""

    def test_script_between_headings(self):
        html = "<h1>Title</h1><script>ignored</script><h2>Subtitle</h2>"
        assert convert(html) == "Title\n\nSubtitle"

    def test_script_inside_heading(self):
        # Script inside heading should be ignored
        html = "<h1>Title<script>ignored</script></h1>"
        assert convert(html) == "Title"


class TestIgnoredTagsWithPreformatted:
    """Test interaction between ignored tags and pre tags."""

    def test_script_inside_pre(self):
        # Script is ignored, pre becomes empty, document boundary trimmed
        assert convert("<pre><script>ignored</script></pre>") == ""

    def test_pre_inside_script(self):
        # Everything inside script is ignored
        assert convert("<script><pre>ignored</pre></script>") == ""

    def test_script_between_pre_tags(self):
        html = "<pre>first</pre><script>ignored</script><pre>second</pre>"
        assert convert(html) == "\nfirst\nsecond"


class TestPagenumClassIgnored:
    """Test that elements with class='pagenum' are also ignored."""

    def test_span_with_pagenum_class(self):
        # Pagenum elements are ignored (treated specially in callbacks)
        html = '<span class="pagenum">123</span>'
        # Without callback, pagenum content is ignored
        assert convert(html) == ""

    def test_div_with_pagenum_class(self):
        html = '<div class="pagenum">456</div>'
        assert convert(html) == ""

    def test_text_before_and_after_pagenum(self):
        html = 'before<span class="pagenum">123</span>after'
        assert convert(html) == "beforeafter"

    def test_pagenum_between_paragraphs(self):
        html = '<p>first</p><span class="pagenum">123</span><p>second</p>'
        assert convert(html) == "first\n\nsecond"