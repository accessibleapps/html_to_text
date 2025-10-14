"""Tests for semantic HTML tag style extraction."""
import pytest
from html_to_text import html_to_text
from lxml import etree


def test_bold_tag_creates_style():
    """Test that <b> tag creates font-weight style."""
    html = '<html><body><p>This is <b>bold</b> text</p></body></html>'

    styles_found = []

    def style_callback(element, start, end):
        style = element.get('style')
        styles_found.append({
            'tag': element.tag,
            'style': style,
            'start': start,
            'end': end
        })

    text = html_to_text(html, style_callback=style_callback)

    # Should find one style node for <b>
    assert len(styles_found) == 1
    assert 'font-weight: bold' in styles_found[0]['style']
    assert styles_found[0]['tag'] == 'b'


def test_italic_tag_creates_style():
    """Test that <i> tag creates font-style."""
    html = '<html><body><p>This is <i>italic</i> text</p></body></html>'

    styles_found = []

    def style_callback(element, start, end):
        style = element.get('style')
        styles_found.append({
            'tag': element.tag,
            'style': style,
            'start': start,
            'end': end
        })

    text = html_to_text(html, style_callback=style_callback)

    assert len(styles_found) == 1
    assert 'font-style: italic' in styles_found[0]['style']


def test_em_tag_creates_style():
    """Test that <em> tag creates font-style."""
    html = '<html><body><p><em>Emphasis</em> text</p></body></html>'

    styles_found = []

    def style_callback(element, start, end):
        styles_found.append({'style': element.get('style')})

    text = html_to_text(html, style_callback=style_callback)

    assert len(styles_found) == 1
    assert 'font-style: italic' in styles_found[0]['style']


def test_strong_tag_creates_style():
    """Test that <strong> tag creates font-weight."""
    html = '<html><body><p><strong>Strong</strong> text</p></body></html>'

    styles_found = []

    def style_callback(element, start, end):
        styles_found.append({'style': element.get('style')})

    text = html_to_text(html, style_callback=style_callback)

    assert len(styles_found) == 1
    assert 'font-weight: bold' in styles_found[0]['style']


def test_underline_tag_creates_style():
    """Test that <u> tag creates text-decoration."""
    html = '<html><body><p><u>Underlined</u> text</p></body></html>'

    styles_found = []

    def style_callback(element, start, end):
        styles_found.append({'style': element.get('style')})

    text = html_to_text(html, style_callback=style_callback)

    assert len(styles_found) == 1
    assert 'text-decoration: underline' in styles_found[0]['style']


def test_nested_semantic_tags():
    """Test that nested semantic tags create multiple overlapping styles."""
    html = '<html><body><p>Text with <b>bold and <i>bold italic</i></b></p></body></html>'

    styles_found = []

    def style_callback(element, start, end):
        styles_found.append({
            'tag': element.tag,
            'style': element.get('style'),
            'start': start,
            'end': end,
            'text_range': (start, end)
        })

    text = html_to_text(html, style_callback=style_callback)

    # Should have 2 style nodes: one for <b>, one for <i>
    assert len(styles_found) == 2

    # Find bold and italic styles
    bold_styles = [s for s in styles_found if 'font-weight: bold' in s['style']]
    italic_styles = [s for s in styles_found if 'font-style: italic' in s['style']]

    assert len(bold_styles) == 1
    assert len(italic_styles) == 1

    # The italic range should be contained within the bold range
    bold_start, bold_end = bold_styles[0]['start'], bold_styles[0]['end']
    italic_start, italic_end = italic_styles[0]['start'], italic_styles[0]['end']

    assert italic_start >= bold_start
    assert italic_end <= bold_end


def test_multiple_separate_semantic_tags():
    """Test multiple separate semantic tags in same paragraph."""
    html = '<html><body><p><b>Bold</b> and <i>italic</i> and <u>underline</u></p></body></html>'

    styles_found = []

    def style_callback(element, start, end):
        styles_found.append({
            'tag': element.tag,
            'style': element.get('style')
        })

    text = html_to_text(html, style_callback=style_callback)

    # Should have 3 separate style nodes
    assert len(styles_found) == 3

    tags = [s['tag'] for s in styles_found]
    assert 'b' in tags
    assert 'i' in tags
    assert 'u' in tags


def test_semantic_tag_with_existing_style_attribute():
    """Test that semantic tags work alongside existing style attributes."""
    html = '<html><body><p><b style="color: red">Bold red</b></p></body></html>'

    styles_found = []

    def style_callback(element, start, end):
        styles_found.append({
            'tag': element.tag,
            'style': element.get('style')
        })

    text = html_to_text(html, style_callback=style_callback)

    # Should have TWO style callbacks:
    # 1. One from the original <b style="color: red"> (line 388-394)
    # 2. One from our semantic tag tracking (new code)
    assert len(styles_found) == 2

    # One should have color: red, one should have font-weight: bold
    styles_str = ' '.join([s['style'] for s in styles_found])
    assert 'color: red' in styles_str
    assert 'font-weight: bold' in styles_str


def test_empty_semantic_tag():
    """Test that empty semantic tags don't create style nodes."""
    html = '<html><body><p><b></b>text</p></body></html>'

    styles_found = []

    def style_callback(element, start, end):
        styles_found.append({'tag': element.tag})

    text = html_to_text(html, style_callback=style_callback)

    # Empty tag should not create a style node (start == end check)
    assert len(styles_found) == 0


def test_semantic_tags_positions():
    """Test that style positions match text positions correctly."""
    html = '<html><body><p>Start <b>bold</b> end</p></body></html>'

    styles_found = []

    def style_callback(element, start, end):
        styles_found.append({
            'start': start,
            'end': end
        })

    text = html_to_text(html, style_callback=style_callback)

    # Text should be "Start bold end"
    assert text.strip() == "Start bold end"

    # The style should cover "bold" which starts at position 6 (after "Start ")
    assert len(styles_found) == 1
    styled_text = text[styles_found[0]['start']:styles_found[0]['end']]
    assert styled_text == "bold"


def test_no_style_callback_no_processing():
    """Test that semantic tags don't cause errors when no callback provided."""
    html = '<html><body><p><b>Bold</b> text</p></body></html>'

    # Should not raise any errors
    text = html_to_text(html)
    assert text.strip() == "Bold text"


def test_strikethrough_tags():
    """Test strikethrough tags (<s>, <strike>, <del>)."""
    html = '<html><body><p><s>Strike</s> <del>Deleted</del></p></body></html>'

    styles_found = []

    def style_callback(element, start, end):
        styles_found.append({
            'tag': element.tag,
            'style': element.get('style')
        })

    text = html_to_text(html, style_callback=style_callback)

    assert len(styles_found) == 2
    for style_info in styles_found:
        assert 'text-decoration: line-through' in style_info['style']


def test_semantic_tags_with_callback():
    """Integration test: semantic tags with style callback."""
    html = '''
    <html>
    <body>
        <h1>Test</h1>
        <p>This is a <b>test</b></p>
        <p><em>Emphasis</em> <i>italic</i></p>
        <p><span style="font-weight: bold">Bold using styles</span></p>
    </body>
    </html>
    '''

    nodes = []

    def callback(element, start, end):
        style = element.get('style', '')
        if 'bold' in style or 'italic' in style:
            nodes.append({
                'start': start,
                'end': end,
                'style': style
            })

    text = html_to_text(html, style_callback=callback)

    # Should find at least 4 style nodes: <b>, <em>, <i>, and <span>
    assert len(nodes) >= 4
