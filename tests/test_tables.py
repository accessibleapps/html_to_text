"""Tests for table structure tracking."""

import pytest

from tests.conftest import convert


class TestTablesWithoutCallbacks:
    """Test table rendering without callbacks."""

    def test_simple_table(self):
        html = "<table><tr><td>cell</td></tr></table>"
        assert convert(html) == "cell"

    def test_table_with_headers(self):
        html = "<table><thead><tr><th>Header</th></tr></thead><tbody><tr><td>Data</td></tr></tbody></table>"
        result = convert(html)
        assert "Header" in result
        assert "Data" in result

    def test_multiple_cells(self):
        html = "<table><tr><td>A</td><td>B</td></tr></table>"
        result = convert(html)
        assert "A" in result
        assert "B" in result


class TestTableCallbacks:
    """Test table structure tracking with callbacks."""

    def test_table_tracked(self, simple_callback):
        callback, nodes = simple_callback
        html = "<table><tr><td>cell</td></tr></table>"
        convert(html, callback)

        tables = [n for n in nodes if n["type"] == "table"]
        assert len(tables) == 1

    def test_table_with_no_callback_not_tracked(self):
        html = "<table><tr><td>cell</td></tr></table>"
        # Should not crash without callback
        result = convert(html)
        assert result == "cell"

    def test_all_table_tags_tracked(self, simple_callback):
        callback, nodes = simple_callback
        html = "<table><thead><tr><th>H</th></tr></thead><tbody><tr><td>D</td></tr></tbody><tfoot><tr><td>F</td></tr></tfoot></table>"
        convert(html, callback)

        table_nodes = [n for n in nodes if n["type"] in ["table", "thead", "tbody", "tfoot", "tr", "th", "td"]]

        # Should have: table, thead, tr, th, tbody, tr, td, tfoot, tr, td
        types = [n["type"] for n in table_nodes]
        assert "table" in types
        assert "thead" in types
        assert "tbody" in types
        assert "tfoot" in types
        assert "tr" in types
        assert "th" in types
        assert "td" in types


class TestTableHierarchy:
    """Test parent/child relationships in tables."""

    def test_table_is_root(self, simple_callback):
        callback, nodes = simple_callback
        html = "<table><tr><td>cell</td></tr></table>"
        convert(html, callback)

        tables = [n for n in nodes if n["type"] == "table"]
        assert tables[0]["parent"] is None

    def test_tr_parent_is_table(self, simple_callback):
        callback, nodes = simple_callback
        html = "<table><tr><td>cell</td></tr></table>"
        convert(html, callback)

        table = [n for n in nodes if n["type"] == "table"][0]
        tr = [n for n in nodes if n["type"] == "tr"][0]

        assert tr["parent"] == table["id"]

    def test_td_parent_is_tr(self, simple_callback):
        callback, nodes = simple_callback
        html = "<table><tr><td>cell</td></tr></table>"
        convert(html, callback)

        tr = [n for n in nodes if n["type"] == "tr"][0]
        td = [n for n in nodes if n["type"] == "td"][0]

        assert td["parent"] == tr["id"]

    def test_tbody_parent_is_table(self, simple_callback):
        callback, nodes = simple_callback
        html = "<table><tbody><tr><td>cell</td></tr></tbody></table>"
        convert(html, callback)

        table = [n for n in nodes if n["type"] == "table"][0]
        tbody = [n for n in nodes if n["type"] == "tbody"][0]

        assert tbody["parent"] == table["id"]

    def test_nested_table_hierarchy(self, simple_callback):
        callback, nodes = simple_callback
        html = "<table><tr><td><table><tr><td>inner</td></tr></table></td></tr></table>"
        convert(html, callback)

        tables = [n for n in nodes if n["type"] == "table"]
        assert len(tables) == 2

        # Outer table has no parent
        outer_table = tables[0]
        assert outer_table["parent"] is None

        # Inner table's parent is outer TD
        inner_table = tables[1]
        tds = [n for n in nodes if n["type"] == "td"]
        outer_td = tds[0]

        assert inner_table["parent"] == outer_td["id"]


class TestTablePositions:
    """Test table position tracking."""

    def test_table_positions(self, simple_callback, assert_positions):
        callback, nodes = simple_callback
        text = convert("<table><tr><td>cell</td></tr></table>", callback)

        table_nodes = [n for n in nodes if n["type"] in ["table", "tr", "td"]]
        assert_positions(text, table_nodes)

    def test_table_start_before_content(self, simple_callback):
        callback, nodes = simple_callback
        text = convert("<table><tr><td>cell</td></tr></table>", callback)

        table = [n for n in nodes if n["type"] == "table"][0]
        td = [n for n in nodes if n["type"] == "td"][0]

        # Table should start at or before TD
        assert table["start"] <= td["start"]

    def test_table_end_after_content(self, simple_callback):
        callback, nodes = simple_callback
        text = convert("<table><tr><td>cell</td></tr></table>", callback)

        table = [n for n in nodes if n["type"] == "table"][0]
        td = [n for n in nodes if n["type"] == "td"][0]

        # Table should end at or after TD
        assert table["end"] >= td["end"]


class TestTableAttributes:
    """Test table attribute preservation."""

    def test_table_with_attributes(self, simple_callback):
        callback, nodes = simple_callback
        html = '<table border="1" class="data"><tr><td>cell</td></tr></table>'
        convert(html, callback)

        table = [n for n in nodes if n["type"] == "table"][0]

        # Attributes should be stored
        assert "attrs" in table
        assert table["attrs"]["border"] == "1"
        assert table["attrs"]["class"] == "data"

    def test_td_with_attributes(self, simple_callback):
        callback, nodes = simple_callback
        html = '<table><tr><td colspan="2">cell</td></tr></table>'
        convert(html, callback)

        td = [n for n in nodes if n["type"] == "td"][0]

        assert "attrs" in td
        assert td["attrs"]["colspan"] == "2"


class TestComplexTables:
    """Test complex table structures."""

    def test_table_with_multiple_rows(self, simple_callback):
        callback, nodes = simple_callback
        html = """
        <table>
            <tr><td>A1</td><td>A2</td></tr>
            <tr><td>B1</td><td>B2</td></tr>
        </table>
        """
        convert(html, callback)

        trs = [n for n in nodes if n["type"] == "tr"]
        tds = [n for n in nodes if n["type"] == "td"]

        assert len(trs) == 2
        assert len(tds) == 4

    def test_table_with_sections(self, simple_callback):
        callback, nodes = simple_callback
        html = """
        <table>
            <thead><tr><th>Header</th></tr></thead>
            <tbody><tr><td>Body</td></tr></tbody>
            <tfoot><tr><td>Footer</td></tr></tfoot>
        </table>
        """
        convert(html, callback)

        thead = [n for n in nodes if n["type"] == "thead"]
        tbody = [n for n in nodes if n["type"] == "tbody"]
        tfoot = [n for n in nodes if n["type"] == "tfoot"]

        assert len(thead) == 1
        assert len(tbody) == 1
        assert len(tfoot) == 1

    def test_table_without_tbody(self, simple_callback):
        callback, nodes = simple_callback
        html = "<table><tr><td>cell</td></tr></table>"
        convert(html, callback)

        # Should work without explicit tbody
        trs = [n for n in nodes if n["type"] == "tr"]
        assert len(trs) == 1


class TestTablesInContext:
    """Test tables in various contexts."""

    def test_table_in_paragraph(self, simple_callback):
        callback, nodes = simple_callback
        html = "<p><table><tr><td>cell</td></tr></table></p>"
        convert(html, callback)

        tables = [n for n in nodes if n["type"] == "table"]
        assert len(tables) == 1

    def test_table_between_paragraphs(self, simple_callback):
        callback, nodes = simple_callback
        html = "<p>before</p><table><tr><td>cell</td></tr></table><p>after</p>"
        text = convert(html, callback)

        assert "before" in text
        assert "cell" in text
        assert "after" in text

    def test_table_with_links(self, simple_callback):
        callback, nodes = simple_callback
        html = '<table><tr><td><a href="url">link</a></td></tr></table>'
        convert(html, callback)

        tables = [n for n in nodes if n["type"] == "table"]
        links = [n for n in nodes if n["type"] == "link"]

        assert len(tables) == 1
        assert len(links) == 1