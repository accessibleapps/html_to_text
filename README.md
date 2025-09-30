# html_to_text

Converts HTML to plain text. Preserves structure, handles tables, and can track document elements.

## Installation

```bash
pip install git+https://github.com/accessibleapps/html_to_text.git
```

Or with uv:

```bash
uv pip install git+https://github.com/accessibleapps/html_to_text.git
```

## Basic Usage

```python
from html_to_text import html_to_text

html = """
<h1>Title</h1>
<p>First paragraph with <strong>bold</strong> text.</p>
<p>Second paragraph.</p>
"""

text = html_to_text(html)
print(text)
```

Output:
```
Title

First paragraph with bold text.

Second paragraph.
```

## Features

- **Structure preservation**: Block elements (`<p>`, `<div>`, `<h1-h6>`) get appropriate spacing
- **Table handling**: Tables are parsed and tracked if callbacks are provided
- **Link extraction**: Internal and external links can be captured
- **Pre-formatted text**: `<pre>` and `<code>` blocks preserve whitespace
- **Heading hierarchy**: Tracks document structure through heading levels
- **Element tracking**: Optional callbacks for building document indexes

## API

### `html_to_text(item, node_parsed_callback=None, startpos=0, file="")`

**Parameters:**
- `item` (str|lxml.etree.Element): HTML string or parsed lxml element
- `node_parsed_callback` (callable, optional): Function called when elements are parsed. Receives `(parent, tag_type, content, **kwargs)`
- `startpos` (int, optional): Starting position offset for tracking
- `file` (str, optional): File path for resolving relative links

**Returns:** Plain text string

## Advanced: Callbacks

Track document structure by providing a callback function:

```python
def track_elements(parent, tag_type, content, **kwargs):
    """
    Called for each tracked element.

    Args:
        parent: Parent element ID (for hierarchical structures)
        tag_type: 'heading', 'link', 'table', 'tr', 'td', 'th', 'id', 'page'
        content: Element content (text for links, None for structural elements)
        **kwargs: Element-specific data (start, end, level, href, etc.)

    Returns:
        Dictionary with 'id' key (used as parent for child elements)
    """
    print(f"{tag_type}: {content}")
    return {'id': f"{tag_type}_{kwargs.get('start', 0)}"}

html = """
<h1>Main Title</h1>
<h2>Subsection</h2>
<p>Text with <a href="/page">link</a>.</p>
<table>
    <tr><td>Cell</td></tr>
</table>
"""

text = html_to_text(html, node_parsed_callback=track_elements)
```

**Callback parameters by element type:**

| Type | parent | content | kwargs |
|------|--------|---------|--------|
| `heading` | Parent heading ID | None | `start`, `end`, `tag`, `level` |
| `link` | None | Link text | `start`, `end`, `href` |
| `table` | Parent table ID | None | `start`, `attrs` |
| `tr`, `td`, `th` | Parent table element ID | None | `start`, `attrs` |
| `id` | None | Element ID | `start` |
| `page` | None | Page identifier | `start`, `pagenum` |

## Ignored Elements

- `<script>`
- `<style>`
- `<title>`
- Elements with `class="pagenum"`

## Special Handling

**Headings (`<h1>` - `<h6>`)**: Surrounded by double newlines. Hierarchy tracked in callbacks.

**Blocks (`<p>`, `<div>`, `<blockquote>`, `<center>`)**: Double newlines before and after.

**Line breaks (`<br>`)**: Converted to single newline.

**Horizontal rule (`<hr>`)**: Becomes 80-character dash line.

**Pre-formatted (`<pre>`, `<code>`)**: Whitespace preserved exactly.

**Links**: Text extracted; URLs captured via callbacks if provided.

**Tables**: Structure tracked via callbacks; text extracted in reading order.

## Requirements

- Python ≥ 3.8
- lxml

## Example: Building a Document Index

```python
from html_to_text import html_to_text

doc_structure = []

def index_callback(parent, tag_type, content, **kwargs):
    entry = {
        'id': len(doc_structure),
        'type': tag_type,
        'parent': parent,
        'start': kwargs.get('start'),
        'end': kwargs.get('end')
    }

    if tag_type == 'heading':
        entry['level'] = kwargs['level']
    elif tag_type == 'link':
        entry['text'] = content
        entry['href'] = kwargs['href']

    doc_structure.append(entry)
    return entry

html = open('document.html').read()
text = html_to_text(html, node_parsed_callback=index_callback, file='document.html')

# Now doc_structure contains full document index with positions
for item in doc_structure:
    if item['type'] == 'heading':
        indent = '  ' * int(item['level'])
        heading_text = text[item['start']:item['end']]
        print(f"{indent}{heading_text}")
```

## License

See LICENSE file.