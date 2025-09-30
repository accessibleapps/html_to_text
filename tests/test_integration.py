"""Integration tests with complex multi-feature documents."""

import pytest

from tests.conftest import convert


class TestBlogPost:
    """Test a typical blog post structure."""

    def test_blog_post_structure(self):
        html = """
        <article>
            <h1>Blog Post Title</h1>
            <p>Introduction paragraph with <a href="link.html">a link</a>.</p>
            <h2>Section 1</h2>
            <p>Content with <em>emphasis</em> and <strong>strong</strong> text.</p>
            <pre>code example
with multiple lines</pre>
            <h2>Section 2</h2>
            <p>More content.</p>
        </article>
        """
        result = convert(html)

        assert "Blog Post Title" in result
        assert "Introduction paragraph" in result
        assert "a link" in result
        assert "Section 1" in result
        assert "emphasis" in result
        assert "strong" in result
        assert "code example" in result
        assert "with multiple lines" in result
        assert "Section 2" in result

    def test_blog_post_with_callbacks(self, simple_callback):
        callback, nodes = simple_callback
        html = """
        <article>
            <h1>Title</h1>
            <p>Intro with <a href="link.html">link</a>.</p>
            <h2>Section</h2>
            <p>Content.</p>
        </article>
        """
        convert(html, callback)

        headings = [n for n in nodes if n["type"] == "heading"]
        links = [n for n in nodes if n["type"] == "link"]

        assert len(headings) == 2  # h1 and h2
        assert len(links) == 1
        # h2 should have h1 as parent
        assert headings[1]["parent"] == headings[0]["id"]


class TestDocumentationPage:
    """Test a documentation page with code, lists, and links."""

    def test_documentation_structure(self):
        html = """
        <div>
            <h1>API Documentation</h1>
            <p>The <code>function()</code> method does something.</p>
            <h2>Example</h2>
            <pre>result = function(arg1, arg2)
print(result)</pre>
            <h2>Parameters</h2>
            <dl>
                <dt>arg1</dt>
                <dd>The first argument</dd>
                <dt>arg2</dt>
                <dd>The second argument</dd>
            </dl>
        </div>
        """
        result = convert(html)

        assert "API Documentation" in result
        assert "function()" in result
        assert "Example" in result
        assert "result = function(arg1, arg2)" in result
        assert "Parameters" in result
        assert "arg1" in result
        assert "The first argument" in result


class TestTableHeavyDocument:
    """Test documents with multiple tables."""

    def test_multiple_tables(self, simple_callback):
        callback, nodes = simple_callback
        html = """
        <div>
            <h1>Data Tables</h1>
            <table>
                <thead><tr><th>Name</th><th>Value</th></tr></thead>
                <tbody>
                    <tr><td>A</td><td>1</td></tr>
                    <tr><td>B</td><td>2</td></tr>
                </tbody>
            </table>
            <p>Description</p>
            <table>
                <tr><td>C</td><td>3</td></tr>
                <tr><td>D</td><td>4</td></tr>
            </table>
        </div>
        """
        result = convert(html, callback)

        tables = [n for n in nodes if n["type"] == "table"]
        assert len(tables) == 2

        # Check that text content is extracted
        assert "Name" in result
        assert "Value" in result
        assert "A" in result
        assert "1" in result


class TestMixedContent:
    """Test complex documents with all feature types."""

    def test_all_features_together(self, simple_callback):
        callback, nodes = simple_callback
        html = """
        <html>
            <head><title>Page Title</title></head>
            <body>
                <h1 id="top">Main Title</h1>
                <p>Intro with <a href="page.html">link</a> and <em>emphasis</em>.</p>
                <hr>
                <h2>Code Section</h2>
                <pre>def foo():
    return 42</pre>
                <script>alert('ignored');</script>
                <h2>Table Section</h2>
                <table>
                    <tr><td>Data</td></tr>
                </table>
                <div><blockquote>A quote</blockquote></div>
            </body>
        </html>
        """
        result = convert(html, callback)

        # Check text output
        assert "Main Title" in result
        assert "link" in result
        assert "Code Section" in result
        assert "def foo():" in result
        assert "return 42" in result
        assert "alert" not in result  # Script ignored
        assert "Table Section" in result
        assert "Data" in result
        assert "A quote" in result

        # Check callbacks
        headings = [n for n in nodes if n["type"] == "heading"]
        links = [n for n in nodes if n["type"] == "link"]
        tables = [n for n in nodes if n["type"] == "table"]
        ids = [n for n in nodes if n["type"] == "id"]

        assert len(headings) == 3  # h1, h2, h2
        assert len(links) == 1
        assert len(tables) == 1
        assert len(ids) == 1
        assert ids[0]["name"] == "#top"


class TestEbookChapter:
    """Test e-book chapter structure (the library's intended use case)."""

    def test_chapter_with_pagenums(self, simple_callback):
        callback, nodes = simple_callback
        html = """
        <div>
            <h1>Chapter 1: The Beginning</h1>
            <p>First paragraph of the chapter.</p>
            <span class="pagenum" id="page1">1</span>
            <p>This paragraph starts on page 1.</p>
            <h2>Section 1.1</h2>
            <p>Section content here.</p>
            <span class="pagenum" id="page2">2</span>
            <p>This paragraph starts on page 2.</p>
            <h2>Section 1.2</h2>
            <p>More content.</p>
        </div>
        """
        result = convert(html, callback)

        # Pagenum content should be omitted
        assert "textmore" not in result  # pagenum "1" omitted
        assert "This paragraph starts on page 1" in result

        # Check callbacks
        pages = [n for n in nodes if n["type"] == "page"]
        headings = [n for n in nodes if n["type"] == "heading"]

        assert len(pages) == 2
        assert pages[0]["pagenum"] == "1"
        assert pages[1]["pagenum"] == "2"

        # First page should have end position set
        assert "end" in pages[0]
        assert pages[0]["end"] > pages[0]["start"]

        # Verify heading hierarchy
        assert len(headings) == 3  # h1, h2, h2
        assert headings[1]["parent"] == headings[0]["id"]  # Section 1.1 under Chapter 1
        assert headings[2]["parent"] == headings[0]["id"]  # Section 1.2 under Chapter 1


class TestWikipediaStyle:
    """Test Wikipedia-style article structure."""

    def test_wikipedia_article(self):
        html = """
        <article>
            <h1>Article Title</h1>
            <p>Lead paragraph with <a href="#cite1">[1]</a> citation.</p>
            <div id="toc">
                <h2>Contents</h2>
            </div>
            <h2>History</h2>
            <p>Historical content.</p>
            <h3>Early period</h3>
            <p>Details about early period.</p>
            <h3>Modern era</h3>
            <p>Details about modern times.</p>
            <h2>See also</h2>
            <ul>
                <li><a href="related1.html">Related Article 1</a></li>
                <li><a href="related2.html">Related Article 2</a></li>
            </ul>
        </article>
        """
        result = convert(html)

        assert "Article Title" in result
        assert "Lead paragraph" in result
        assert "Contents" in result
        assert "History" in result
        assert "Early period" in result
        assert "Modern era" in result
        assert "See also" in result
        assert "Related Article 1" in result


class TestRealWorldQuirks:
    """Test real-world HTML quirks and edge cases."""

    def test_nested_formatting(self):
        # Real HTML sometimes has weird nesting
        html = "<p><strong><em>Bold and italic</em></strong> text.</p>"
        assert convert(html) == "Bold and italic text."

    def test_mixed_blocks_and_inline(self):
        html = "text<div>block</div>more<span>inline</span>end"
        result = convert(html)
        assert "text" in result
        assert "block" in result
        assert "more" in result
        assert "inline" in result
        assert "end" in result

    def test_whitespace_preservation_in_pre(self):
        # Ensure pre whitespace is truly preserved
        html = """<pre>    indented
        more indent
no indent</pre>"""
        result = convert(html)
        # Should preserve all the indentation
        assert "    indented" in result
        assert "        more indent" in result
        assert "no indent" in result

    def test_consecutive_inline_with_blocks(self):
        html = "<span>a</span><span>b</span><p>para</p><span>c</span><span>d</span>"
        result = convert(html)
        assert "ab" in result
        assert "para" in result
        assert "cd" in result