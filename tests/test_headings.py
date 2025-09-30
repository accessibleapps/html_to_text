"""Tests for heading elements and hierarchy tracking."""

import pytest

from tests.conftest import convert


@pytest.mark.parametrize("tag", ["h1", "h2", "h3", "h4", "h5", "h6"])
class TestBasicHeadings:
    """Test basic heading behavior."""

    def test_single_heading(self, tag):
        html = f"<{tag}>Title</{tag}>"
        assert convert(html) == "Title"

    def test_empty_heading(self, tag):
        html = f"<{tag}></{tag}>"
        assert convert(html) == ""

    def test_heading_with_whitespace(self, tag):
        html = f"<{tag}>  Title  </{tag}>"
        assert convert(html) == "Title"


@pytest.mark.parametrize("tag", ["h1", "h2", "h3", "h4", "h5", "h6"])
class TestConsecutiveHeadings:
    """Test multiple headings in sequence."""

    def test_two_consecutive_same_level(self, tag):
        html = f"<{tag}>First</{tag}><{tag}>Second</{tag}>"
        assert convert(html) == "First\n\nSecond"

    def test_three_consecutive_same_level(self, tag):
        html = f"<{tag}>A</{tag}><{tag}>B</{tag}><{tag}>C</{tag}>"
        assert convert(html) == "A\n\nB\n\nC"


class TestHeadingLevels:
    """Test different heading levels."""

    def test_all_heading_levels(self):
        html = "<h1>H1</h1><h2>H2</h2><h3>H3</h3><h4>H4</h4><h5>H5</h5><h6>H6</h6>"
        assert convert(html) == "H1\n\nH2\n\nH3\n\nH4\n\nH5\n\nH6"

    def test_descending_hierarchy(self):
        html = "<h1>Title</h1><h2>Subtitle</h2><h3>Subsubtitle</h3>"
        assert convert(html) == "Title\n\nSubtitle\n\nSubsubtitle"

    def test_ascending_hierarchy(self):
        html = "<h3>H3</h3><h2>H2</h2><h1>H1</h1>"
        assert convert(html) == "H3\n\nH2\n\nH1"


class TestHeadingsWithContent:
    """Test headings with various content."""

    def test_heading_with_inline_elements(self):
        html = "<h1>Title <em>emphasized</em></h1>"
        assert convert(html) == "Title emphasized"

    def test_heading_with_multiple_inline_elements(self):
        html = "<h2><span>Part 1</span> <strong>Part 2</strong></h2>"
        assert convert(html) == "Part 1 Part 2"

    def test_heading_with_nested_inline(self):
        html = "<h1>Title <span>with <em>nested</em></span></h1>"
        assert convert(html) == "Title with nested"


class TestHeadingsWithBlocks:
    """Test headings mixed with block elements."""

    def test_heading_then_paragraph(self):
        html = "<h1>Title</h1><p>Content</p>"
        assert convert(html) == "Title\n\nContent"

    def test_paragraph_then_heading(self):
        html = "<p>Content</p><h1>Title</h1>"
        assert convert(html) == "Content\n\nTitle"

    def test_heading_between_paragraphs(self):
        html = "<p>Intro</p><h2>Section</h2><p>Content</p>"
        assert convert(html) == "Intro\n\nSection\n\nContent"


class TestHeadingHierarchy:
    """Test heading hierarchy tracking with callbacks."""

    def test_flat_h1_structure_no_parents(self, simple_callback):
        callback, nodes = simple_callback
        html = "<h1>First</h1><h1>Second</h1>"
        convert(html, callback)

        headings = [n for n in nodes if n["type"] == "heading"]
        assert len(headings) == 2
        assert headings[0]["parent"] is None
        assert headings[1]["parent"] is None

    def test_h1_h2_parent_child(self, simple_callback):
        callback, nodes = simple_callback
        html = "<h1>Parent</h1><h2>Child</h2>"
        convert(html, callback)

        headings = [n for n in nodes if n["type"] == "heading"]
        assert len(headings) == 2
        assert headings[0]["parent"] is None
        assert headings[1]["parent"] == headings[0]["id"]

    def test_h1_h2_h3_hierarchy(self, simple_callback):
        callback, nodes = simple_callback
        html = "<h1>H1</h1><h2>H2</h2><h3>H3</h3>"
        convert(html, callback)

        headings = [n for n in nodes if n["type"] == "heading"]
        assert len(headings) == 3
        assert headings[0]["parent"] is None  # H1 has no parent
        assert headings[1]["parent"] == headings[0]["id"]  # H2 parent is H1
        assert headings[2]["parent"] == headings[1]["id"]  # H3 parent is H2

    def test_siblings_share_parent(self, simple_callback):
        callback, nodes = simple_callback
        html = "<h1>Parent</h1><h2>Child1</h2><h2>Child2</h2>"
        convert(html, callback)

        headings = [n for n in nodes if n["type"] == "heading"]
        assert len(headings) == 3
        assert headings[1]["parent"] == headings[0]["id"]
        assert headings[2]["parent"] == headings[0]["id"]  # Same parent

    def test_jump_levels_h1_h3(self, simple_callback):
        callback, nodes = simple_callback
        html = "<h1>H1</h1><h3>H3</h3>"
        convert(html, callback)

        headings = [n for n in nodes if n["type"] == "heading"]
        assert len(headings) == 2
        # H3 parent should still be H1 (skipped H2)
        assert headings[1]["parent"] == headings[0]["id"]

    def test_reverse_hierarchy_stack_pops(self, simple_callback):
        callback, nodes = simple_callback
        html = "<h3>H3</h3><h2>H2</h2><h1>H1</h1>"
        convert(html, callback)

        headings = [n for n in nodes if n["type"] == "heading"]
        assert len(headings) == 3
        # All should have no parent (each pops previous from stack)
        assert headings[0]["parent"] is None
        assert headings[1]["parent"] is None
        assert headings[2]["parent"] is None

    def test_complex_nested_structure(self, simple_callback):
        callback, nodes = simple_callback
        html = """
        <h1>Chapter 1</h1>
        <h2>Section 1.1</h2>
        <h3>Subsection 1.1.1</h3>
        <h3>Subsection 1.1.2</h3>
        <h2>Section 1.2</h2>
        <h1>Chapter 2</h1>
        """
        convert(html, callback)

        headings = [n for n in nodes if n["type"] == "heading"]
        assert len(headings) == 6

        # Chapter 1 has no parent
        assert headings[0]["parent"] is None
        # Section 1.1 parent is Chapter 1
        assert headings[1]["parent"] == headings[0]["id"]
        # Subsection 1.1.1 parent is Section 1.1
        assert headings[2]["parent"] == headings[1]["id"]
        # Subsection 1.1.2 parent is Section 1.1 (sibling)
        assert headings[3]["parent"] == headings[1]["id"]
        # Section 1.2 parent is Chapter 1
        assert headings[4]["parent"] == headings[0]["id"]
        # Chapter 2 has no parent
        assert headings[5]["parent"] is None


class TestHeadingPositions:
    """Test heading position tracking."""

    def test_heading_start_end_positions(self, simple_callback, assert_positions):
        callback, nodes = simple_callback
        text = convert("<h1>Title</h1>", callback)

        headings = [n for n in nodes if n["type"] == "heading"]
        assert len(headings) == 1

        heading = headings[0]
        assert "start" in heading
        assert "end" in heading
        assert_positions(text, [heading])

    def test_multiple_headings_positions(self, simple_callback, assert_positions):
        callback, nodes = simple_callback
        text = convert("<h1>First</h1><h2>Second</h2>", callback)

        headings = [n for n in nodes if n["type"] == "heading"]
        assert len(headings) == 2
        assert_positions(text, headings)

        # Positions should be in order
        assert headings[0]["start"] < headings[0]["end"]
        assert headings[0]["end"] <= headings[1]["start"]


class TestHeadingMetadata:
    """Test heading metadata (level, tag)."""

    def test_heading_has_level_metadata(self, simple_callback):
        callback, nodes = simple_callback
        convert("<h2>Title</h2>", callback)

        headings = [n for n in nodes if n["type"] == "heading"]
        assert headings[0]["level"] == "2"

    def test_heading_has_tag_metadata(self, simple_callback):
        callback, nodes = simple_callback
        convert("<h3>Title</h3>", callback)

        headings = [n for n in nodes if n["type"] == "heading"]
        assert headings[0]["tag"] == "h3"

    @pytest.mark.parametrize("level", ["1", "2", "3", "4", "5", "6"])
    def test_all_heading_levels_metadata(self, simple_callback, level):
        callback, nodes = simple_callback
        convert(f"<h{level}>Title</h{level}>", callback)

        headings = [n for n in nodes if n["type"] == "heading"]
        assert headings[0]["level"] == level
        assert headings[0]["tag"] == f"h{level}"