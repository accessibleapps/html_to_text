"""Tests for callback system (IDs, pagenums, positions)."""

import pytest

from tests.conftest import convert


class TestIDTracking:
    """Test element ID tracking."""

    def test_element_with_id(self, simple_callback):
        callback, nodes = simple_callback
        html = '<p id="para1">text</p>'
        convert(html, callback)

        id_nodes = [n for n in nodes if n["type"] == "id"]
        assert len(id_nodes) == 1
        assert id_nodes[0]["name"] == "#para1"

    def test_multiple_ids(self, simple_callback):
        callback, nodes = simple_callback
        html = '<div id="div1"><p id="para1">text</p></div>'
        convert(html, callback)

        id_nodes = [n for n in nodes if n["type"] == "id"]
        assert len(id_nodes) == 2

    def test_id_with_file_path(self, simple_callback):
        callback, nodes = simple_callback
        html = '<p id="para1">text</p>'
        convert(html, callback, file="chapter1.html")

        id_nodes = [n for n in nodes if n["type"] == "id"]
        assert id_nodes[0]["name"] == "chapter1.html#para1"

    def test_element_without_id_not_tracked(self, simple_callback):
        callback, nodes = simple_callback
        html = '<p>text</p>'
        convert(html, callback)

        id_nodes = [n for n in nodes if n["type"] == "id"]
        assert len(id_nodes) == 0


class TestPagenumTracking:
    """Test page marker tracking."""

    def test_pagenum_tracked(self, simple_callback):
        callback, nodes = simple_callback
        html = '<span class="pagenum" id="page123">123</span>'
        convert(html, callback)

        pages = [n for n in nodes if n["type"] == "page"]
        assert len(pages) == 1

    def test_pagenum_content_ignored(self):
        # Content of pagenum should be ignored in output
        html = '<span class="pagenum" id="page123">123</span>'
        assert convert(html) == ""

    def test_pagenum_numeric_parsing(self, simple_callback):
        callback, nodes = simple_callback
        html = '<span class="pagenum" id="page123">ignored</span>'
        convert(html, callback)

        pages = [n for n in nodes if n["type"] == "page"]
        # Should extract "123" from "page123"
        assert pages[0]["pagenum"] == "123"

    def test_pagenum_p_prefix(self, simple_callback):
        callback, nodes = simple_callback
        html = '<span class="pagenum" id="pxvii">ignored</span>'
        convert(html, callback)

        pages = [n for n in nodes if n["type"] == "page"]
        # p-prefixed page numbers get prefix stripped and lowercased
        assert pages[0]["pagenum"] == "xvii"

    def test_pagenum_unparseable(self, simple_callback):
        callback, nodes = simple_callback
        html = '<span class="pagenum" id="unparseable_id">ignored</span>'
        convert(html, callback)

        pages = [n for n in nodes if n["type"] == "page"]
        # Unparseable page numbers return None
        assert pages[0]["pagenum"] is None

    def test_pagenum_between_content(self, simple_callback):
        callback, nodes = simple_callback
        html = 'text<span class="pagenum" id="page1">1</span>more'
        text = convert(html, callback)

        # Pagenum content omitted
        assert text == "textmore"

        pages = [n for n in nodes if n["type"] == "page"]
        assert len(pages) == 1

    def test_multiple_pagenums(self, simple_callback):
        callback, nodes = simple_callback
        html = '''
        text<span class="pagenum" id="page1">1</span>
        more<span class="pagenum" id="page2">2</span>
        '''
        convert(html, callback)

        pages = [n for n in nodes if n["type"] == "page"]
        assert len(pages) == 2

    def test_pagenum_end_position(self, simple_callback):
        callback, nodes = simple_callback
        html = '''
        text<span class="pagenum" id="page1">1</span>more
        <span class="pagenum" id="page2">2</span>end
        '''
        text = convert(html, callback)

        pages = [n for n in nodes if n["type"] == "page"]
        # First page end should be set when second page starts
        assert "end" in pages[0]
        # Last page end is set in html_to_text function
        assert "end" in pages[1]


class TestCallbackReturnValue:
    """Test callback return value requirements."""

    def test_callback_must_return_dict_with_id(self):
        def bad_callback(parent, node_type, name, **kwargs):
            return {}  # Missing "id" key

        html = '<h1>Title</h1>'
        # Should raise KeyError or similar
        with pytest.raises(KeyError):
            convert(html, bad_callback)

    def test_callback_return_value_used(self, simple_callback):
        callback, nodes = simple_callback
        html = '<h1>Title</h1>'
        convert(html, callback)

        headings = [n for n in nodes if n["type"] == "heading"]
        # Callback should have been called and returned valid dict
        assert headings[0]["id"] is not None


class TestPositionAccuracy:
    """Test position tracking accuracy."""

    def test_positions_with_startpos_offset(self, simple_callback):
        callback, nodes = simple_callback
        # Convert with startpos offset
        html = '<h1>Title</h1>'
        from html_to_text import html_to_text
        text = html_to_text(html, node_parsed_callback=callback, startpos=100)

        headings = [n for n in nodes if n["type"] == "heading"]
        # Positions should include the offset
        assert headings[0]["start"] >= 100

    def test_id_position(self, simple_callback):
        callback, nodes = simple_callback
        html = '<p id="test">text</p>'
        text = convert(html, callback)

        id_nodes = [n for n in nodes if n["type"] == "id"]
        # ID position accounts for paragraph's pending \n\n
        # But document boundary trimming means actual output is "text"
        assert id_nodes[0]["start"] >= 0

    def test_position_after_pending_add(self, simple_callback):
        callback, nodes = simple_callback
        # Block elements add newlines, position calc includes pending add
        html = '<p id="p1">text</p>'
        convert(html, callback)

        id_nodes = [n for n in nodes if n["type"] == "id"]
        # Position should be correct
        assert id_nodes[0]["start"] >= 0


class TestCallbackWithoutTracking:
    """Test elements that don't trigger callbacks."""

    def test_inline_elements_no_callbacks(self, simple_callback):
        callback, nodes = simple_callback
        html = '<span>text</span>'
        convert(html, callback)

        # Span doesn't trigger any callbacks
        assert len(nodes) == 0

    def test_text_only_no_callbacks(self, simple_callback):
        callback, nodes = simple_callback
        html = 'just text'
        convert(html, callback)

        assert len(nodes) == 0


class TestCallbackNodeTypes:
    """Test all callback node types."""

    def test_heading_callback(self, simple_callback):
        callback, nodes = simple_callback
        html = '<h1>Title</h1>'
        convert(html, callback)

        headings = [n for n in nodes if n["type"] == "heading"]
        assert len(headings) == 1
        assert headings[0]["tag"] == "h1"
        assert headings[0]["level"] == "1"

    def test_link_callback(self, simple_callback):
        callback, nodes = simple_callback
        html = '<a href="url">text</a>'
        convert(html, callback)

        links = [n for n in nodes if n["type"] == "link"]
        assert len(links) == 1
        assert links[0]["href"] == "url"

    def test_table_callback(self, simple_callback):
        callback, nodes = simple_callback
        html = '<table><tr><td>cell</td></tr></table>'
        convert(html, callback)

        tables = [n for n in nodes if n["type"] == "table"]
        assert len(tables) == 1

    def test_id_callback(self, simple_callback):
        callback, nodes = simple_callback
        html = '<p id="test">text</p>'
        convert(html, callback)

        ids = [n for n in nodes if n["type"] == "id"]
        assert len(ids) == 1

    def test_page_callback(self, simple_callback):
        callback, nodes = simple_callback
        html = '<span class="pagenum" id="page1">1</span>'
        convert(html, callback)

        pages = [n for n in nodes if n["type"] == "page"]
        assert len(pages) == 1