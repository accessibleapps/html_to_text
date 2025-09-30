"""Tests for special tags (BR, HR, DD, DT)."""

import pytest

from html_to_text import HR_TEXT
from tests.conftest import convert


class TestBRTag:
    """Test BR tag behavior."""

    def test_single_br(self):
        assert convert("text<br>more") == "text\nmore"

    def test_br_at_start(self):
        assert convert("<br>text") == "\ntext"

    def test_br_at_end(self):
        assert convert("text<br>") == "text\n"

    def test_multiple_consecutive_br(self):
        assert convert("a<br><br>b") == "a\n\nb"

    def test_three_consecutive_br(self):
        assert convert("a<br><br><br>b") == "a\n\n\nb"

    def test_br_in_paragraph(self):
        html = "<p>line1<br>line2</p>"
        assert convert(html) == "line1\nline2"

    def test_br_in_div(self):
        html = "<div>line1<br>line2</div>"
        assert convert(html) == "line1\nline2"

    def test_br_with_inline_elements(self):
        html = "<span>a</span><br><span>b</span>"
        assert convert(html) == "a\nb"

    def test_br_between_paragraphs(self):
        # BR between blocks - newlines may combine
        html = "<p>a</p><br><p>b</p>"
        assert convert(html) == "a\n\n\nb"


class TestHRTag:
    """Test HR tag behavior."""

    def test_single_hr(self):
        # HR produces 80 dashes with newlines
        assert convert("<hr>") == HR_TEXT

    def test_hr_format(self):
        # Verify HR_TEXT is exactly what we expect
        assert HR_TEXT == "\n" + ("-" * 80)

    def test_hr_with_text_before(self):
        result = convert("text<hr>")
        assert result == f"text{HR_TEXT}"

    def test_hr_with_text_after(self):
        result = convert("<hr>text")
        # Tail text follows immediately after HR
        assert result == f"{HR_TEXT}text"

    def test_hr_between_text(self):
        result = convert("before<hr>after")
        # HR adds its line, tail text follows
        assert result == f"before{HR_TEXT}after"

    def test_hr_in_paragraph(self):
        html = "<p>text<hr></p>"
        result = convert(html)
        assert HR_TEXT in result

    def test_multiple_hr(self):
        html = "<hr><hr>"
        result = convert(html)
        # Two HRs back to back
        assert result == f"{HR_TEXT}{HR_TEXT}"

    def test_hr_between_headings(self):
        html = "<h1>Title</h1><hr><h2>Subtitle</h2>"
        result = convert(html)
        assert "Title" in result
        assert HR_TEXT in result
        assert "Subtitle" in result


class TestDDDTTags:
    """Test DD and DT (definition list) tags."""

    def test_single_dt(self):
        # Document boundary trimming removes leading newline
        assert convert("<dt>term</dt>") == "term"

    def test_single_dd(self):
        assert convert("<dd>definition</dd>") == "definition"

    def test_dt_then_dd(self):
        html = "<dt>term</dt><dd>definition</dd>"
        # First newline trimmed at document boundary
        assert convert(html) == "term\ndefinition"

    def test_definition_list(self):
        html = "<dl><dt>Term</dt><dd>Definition</dd></dl>"
        assert convert(html) == "Term\nDefinition"

    def test_multiple_terms(self):
        html = "<dl><dt>Term1</dt><dd>Def1</dd><dt>Term2</dt><dd>Def2</dd></dl>"
        assert convert(html) == "Term1\nDef1\nTerm2\nDef2"

    def test_dd_with_inline_elements(self):
        html = "<dd><em>emphasized</em> definition</dd>"
        assert convert(html) == "emphasized definition"

    def test_dt_with_inline_elements(self):
        html = "<dt><strong>strong</strong> term</dt>"
        assert convert(html) == "strong term"

    def test_dd_dt_in_paragraph(self):
        # DT inside paragraph
        html = "<p><dt>term</dt></p>"
        assert convert(html) == "term"


class TestSpecialTagCombinations:
    """Test combinations of special tags."""

    def test_br_then_hr(self):
        html = "text<br><hr>"
        result = convert(html)
        assert result == f"text\n{HR_TEXT}"

    def test_hr_then_br(self):
        html = "<hr><br>text"
        result = convert(html)
        # HR ends with \n, BR adds \n
        assert result == f"{HR_TEXT}\ntext"

    def test_br_in_definition_list(self):
        html = "<dt>term<br>continued</dt>"
        # Document boundary trims leading newline
        assert convert(html) == "term\ncontinued"

    def test_definition_list_with_br_in_dd(self):
        html = "<dd>line1<br>line2</dd>"
        assert convert(html) == "line1\nline2"

    def test_hr_in_definition_list(self):
        html = "<dl><dt>Term</dt><hr><dd>Def</dd></dl>"
        result = convert(html)
        # Document boundary trimming
        assert "Term" in result
        assert HR_TEXT in result
        assert "Def" in result


class TestSpecialTagsWithBlocks:
    """Test special tags interaction with block elements."""

    def test_br_between_block_elements(self):
        html = "<p>para1</p><br><p>para2</p>"
        assert convert(html) == "para1\n\n\npara2"

    def test_definition_list_between_paragraphs(self):
        html = "<p>intro</p><dl><dt>Term</dt><dd>Def</dd></dl><p>outro</p>"
        result = convert(html)
        assert "intro" in result
        assert "Term" in result
        assert "Def" in result
        assert "outro" in result

    def test_hr_between_paragraphs(self):
        html = "<p>para1</p><hr><p>para2</p>"
        result = convert(html)
        assert "para1" in result
        assert HR_TEXT in result
        assert "para2" in result