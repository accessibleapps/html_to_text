"""Tests for <img> alt text extraction.

Images with alt text emit the alt as inline text. Empty or missing alt
emits nothing (decorative image convention). Drives Bookshare math
accessibility: equations are rendered as PNGs with MathSpeak-style alt
text like "f colon upper X right arrow upper Y" — that text must survive
HTML-to-text conversion.
"""

from tests.conftest import convert


class TestIMGAlt:
    def test_img_with_alt_emits_alt(self):
        assert convert('<img alt="picture of a cat" />') == "picture of a cat"

    def test_img_without_alt_emits_nothing(self):
        assert convert("<img src='cat.png' />") == ""

    def test_img_with_empty_alt_emits_nothing(self):
        assert convert('<img alt="" src="decorative.png" />') == ""

    def test_img_alt_inline_in_paragraph(self):
        html = '<p>Let <img alt="f colon upper X right arrow upper Y" /> be a map.</p>'
        assert convert(html) == "Let f colon upper X right arrow upper Y be a map."

    def test_bookshare_math_alt_survives(self):
        html = (
            '<p>For all <img alt="x comma y element of double struck upper R" />, '
            'we have <img alt="x less than or equals y" />.</p>'
        )
        assert convert(html) == (
            "For all x comma y element of double struck upper R, "
            "we have x less than or equals y."
        )

    def test_multiple_imgs_in_sequence(self):
        html = '<p><img alt="alpha" /> <img alt="beta" /> <img alt="gamma" /></p>'
        assert convert(html) == "alpha beta gamma"

    def test_img_in_heading(self):
        html = '<h1>Chapter <img alt="upper I upper I" /></h1>'
        assert convert(html) == "Chapter upper I upper I"

    def test_img_inside_ignored_tag_is_dropped(self):
        html = '<script><img alt="should not appear" /></script>after'
        assert convert(html) == "after"
