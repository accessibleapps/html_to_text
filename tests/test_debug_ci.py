"""Debug test to understand CI behavior."""
import sys
from lxml import html, etree
import lxml

def test_debug_title_parsing():
    """Debug how lxml parses the title tag."""
    html_str = 'before<title>ignored</title>after'

    print("\n=== Parser Comparison ===")
    print(f"lxml version: {lxml.__version__}")

    # Test XML parser
    print("Testing etree.fromstring (XML parser):")
    try:
        xml_tree = etree.fromstring(html_str)
        print(f"  SUCCESS: {etree.tostring(xml_tree, encoding='unicode')}")
    except Exception as e:
        print(f"  FAILED: {e}")

    # Test HTML parser
    print("Testing html.fromstring (HTML parser):")
    tree = html.fromstring(html_str)
    print(f"  Tree structure: {etree.tostring(tree, encoding='unicode')}")
    print(f"  Root tag: {tree.tag}")
    print(f"  Root text: {repr(tree.text)}")
    print(f"  Root tail: {repr(tree.tail)}")
    print(f"  Children: {len(tree)}")
    for i, child in enumerate(tree):
        print(f"    Child {i}: tag={child.tag}, text={repr(child.text)}, tail={repr(child.tail)}")

    # Now test actual conversion
    print("\nTesting html_to_text conversion:")
    from html_to_text import html_to_text, tree_from_string

    # Show which parser tree_from_string uses
    parsed_tree = tree_from_string(html_str)
    print(f"  tree_from_string result: tag={parsed_tree.tag}, structure={etree.tostring(parsed_tree, encoding='unicode')}")

    result = html_to_text(html_str)
    print(f"  Result: {repr(result)}")

    assert result == "before\n\nafter", f"Expected 'before\\n\\nafter', got {repr(result)}"
