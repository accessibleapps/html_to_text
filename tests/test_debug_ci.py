"""Debug test to understand CI behavior."""
import sys
from lxml import html, etree

def test_debug_title_parsing():
    """Debug how lxml parses the title tag."""
    html_str = 'before<title>ignored</title>after'
    tree = html.fromstring(html_str)

    print("\n=== Debug Info ===")
    print(f"Python version: {sys.version}")
    print(f"Tree structure: {etree.tostring(tree, encoding='unicode')}")
    print(f"Root tag: {tree.tag}")
    print(f"Root text: {repr(tree.text)}")
    print(f"Root tail: {repr(tree.tail)}")
    print(f"Children: {len(tree)}")
    for i, child in enumerate(tree):
        print(f"  Child {i}: tag={child.tag}, text={repr(child.text)}, tail={repr(child.tail)}")

    # Now test actual conversion
    from html_to_text import html_to_text
    result = html_to_text(html_str)
    print(f"Result: {repr(result)}")
    print(f"Result bytes: {result.encode('utf-8')}")

    assert result == "before\n\nafter", f"Expected 'before\\n\\nafter', got {repr(result)}"
