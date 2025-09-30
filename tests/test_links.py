"""Tests for link handling and extraction."""

import pytest

from tests.conftest import convert


class TestLinksWithoutCallbacks:
    """Test link rendering without callbacks."""

    def test_simple_link(self):
        html = '<a href="http://example.com">text</a>'
        assert convert(html) == "text"

    def test_link_with_no_href(self):
        html = '<a>text</a>'
        assert convert(html) == "text"

    def test_link_in_paragraph(self):
        html = '<p>See <a href="http://example.com">here</a> for more</p>'
        assert convert(html) == "See here for more"

    def test_multiple_links(self):
        html = '<a href="url1">link1</a> <a href="url2">link2</a>'
        assert convert(html) == "link1 link2"

    def test_nested_inline_in_link(self):
        html = '<a href="url"><em>emphasized</em> text</a>'
        assert convert(html) == "emphasized text"


class TestLinkCallbacks:
    """Test link extraction with callbacks."""

    def test_link_tracked(self, simple_callback):
        callback, nodes = simple_callback
        html = '<a href="http://example.com">text</a>'
        convert(html, callback)

        links = [n for n in nodes if n["type"] == "link"]
        assert len(links) == 1
        assert links[0]["name"] == "text"
        assert links[0]["href"] == "http://example.com"

    def test_link_without_href_not_tracked(self, simple_callback):
        callback, nodes = simple_callback
        html = '<a>text</a>'
        convert(html, callback)

        links = [n for n in nodes if n["type"] == "link"]
        assert len(links) == 0

    def test_link_positions(self, simple_callback, assert_positions):
        callback, nodes = simple_callback
        text = convert('<a href="url">link text</a>', callback)

        links = [n for n in nodes if n["type"] == "link"]
        assert len(links) == 1
        assert_positions(text, links)

        # Link should span the text "link text"
        link = links[0]
        assert text[link["start"]:link["end"]] == "link text"

    def test_multiple_links_tracked(self, simple_callback):
        callback, nodes = simple_callback
        html = '<a href="url1">first</a> <a href="url2">second</a>'
        convert(html, callback)

        links = [n for n in nodes if n["type"] == "link"]
        assert len(links) == 2
        assert links[0]["href"] == "url1"
        assert links[1]["href"] == "url2"


class TestExternalLinks:
    """Test external link handling."""

    def test_http_link(self, simple_callback):
        callback, nodes = simple_callback
        html = '<a href="http://example.com">text</a>'
        convert(html, callback)

        links = [n for n in nodes if n["type"] == "link"]
        assert links[0]["href"] == "http://example.com"

    def test_https_link(self, simple_callback):
        callback, nodes = simple_callback
        html = '<a href="https://example.com">text</a>'
        convert(html, callback)

        links = [n for n in nodes if n["type"] == "link"]
        assert links[0]["href"] == "https://example.com"

    def test_ftp_link(self, simple_callback):
        callback, nodes = simple_callback
        html = '<a href="ftp://example.com">text</a>'
        convert(html, callback)

        links = [n for n in nodes if n["type"] == "link"]
        assert links[0]["href"] == "ftp://example.com"


class TestInternalLinks:
    """Test internal link normalization."""

    def test_relative_link_same_directory(self, simple_callback):
        callback, nodes = simple_callback
        html = '<a href="page.html">text</a>'
        convert(html, callback, file="dir/current.html")

        links = [n for n in nodes if n["type"] == "link"]
        # Should be normalized to dir/page.html
        assert links[0]["href"] == "dir/page.html"

    def test_relative_link_parent_directory(self, simple_callback):
        callback, nodes = simple_callback
        html = '<a href="../other.html">text</a>'
        convert(html, callback, file="dir/current.html")

        links = [n for n in nodes if n["type"] == "link"]
        assert links[0]["href"] == "other.html"

    def test_relative_link_subdirectory(self, simple_callback):
        callback, nodes = simple_callback
        html = '<a href="sub/page.html">text</a>'
        convert(html, callback, file="dir/current.html")

        links = [n for n in nodes if n["type"] == "link"]
        assert links[0]["href"] == "dir/sub/page.html"

    def test_fragment_link(self, simple_callback):
        callback, nodes = simple_callback
        html = '<a href="#anchor">text</a>'
        convert(html, callback, file="page.html")

        links = [n for n in nodes if n["type"] == "link"]
        # Fragment-only links become just the fragment
        assert links[0]["href"] == "#anchor"

    def test_url_encoded_link(self, simple_callback):
        callback, nodes = simple_callback
        html = '<a href="page%20name.html">text</a>'
        convert(html, callback)

        links = [n for n in nodes if n["type"] == "link"]
        # URL should be decoded
        assert links[0]["href"] == "page name.html"

    def test_complex_path_normalization(self, simple_callback):
        callback, nodes = simple_callback
        html = '<a href="./dir/../other.html">text</a>'
        convert(html, callback, file="current.html")

        links = [n for n in nodes if n["type"] == "link"]
        # Should normalize to other.html
        assert links[0]["href"] == "other.html"


class TestLinkTextExtraction:
    """Test link text content extraction."""

    def test_link_with_nested_elements(self, simple_callback):
        callback, nodes = simple_callback
        html = '<a href="url">text <em>emphasized</em> more</a>'
        convert(html, callback)

        links = [n for n in nodes if n["type"] == "link"]
        # Text should include content from nested elements
        assert links[0]["name"] == "text emphasized more"

    def test_link_with_whitespace(self, simple_callback):
        callback, nodes = simple_callback
        html = '<a href="url">  text  </a>'
        convert(html, callback)

        links = [n for n in nodes if n["type"] == "link"]
        # Whitespace preserved in link name (uses XPath string())
        assert links[0]["name"] == "  text  "

    def test_empty_link(self, simple_callback):
        callback, nodes = simple_callback
        html = '<a href="url"></a>'
        convert(html, callback)

        links = [n for n in nodes if n["type"] == "link"]
        assert links[0]["name"] == ""


class TestLinksInContext:
    """Test links in various contexts."""

    def test_links_in_paragraph(self, simple_callback):
        callback, nodes = simple_callback
        html = '<p>Text with <a href="url">link</a> inside</p>'
        convert(html, callback)

        links = [n for n in nodes if n["type"] == "link"]
        assert len(links) == 1

    def test_links_in_headings(self, simple_callback):
        callback, nodes = simple_callback
        html = '<h1><a href="url">Heading Link</a></h1>'
        convert(html, callback)

        links = [n for n in nodes if n["type"] == "link"]
        headings = [n for n in nodes if n["type"] == "heading"]
        assert len(links) == 1
        assert len(headings) == 1

    def test_links_in_list_items(self, simple_callback):
        callback, nodes = simple_callback
        html = '<ul><li><a href="url1">link1</a></li><li><a href="url2">link2</a></li></ul>'
        convert(html, callback)

        links = [n for n in nodes if n["type"] == "link"]
        assert len(links) == 2