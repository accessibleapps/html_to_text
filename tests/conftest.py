"""Shared fixtures and helpers for html_to_text tests."""

from typing import Any, Callable, Union

import pytest

from html_to_text import html_to_text


@pytest.fixture
def simple_callback():
    """Create a mock callback that collects all node events.

    Returns a tuple of (callback_function, collected_nodes_list).
    """
    nodes = []
    counter = {"id": 0}

    def callback(
        parent: Union[str, int, None],
        node_type: str,
        name: Union[str, int, None],
        **kwargs: Any
    ) -> dict[str, Union[str, int]]:
        counter["id"] += 1
        node = {
            "id": counter["id"],
            "parent": parent,
            "type": node_type,
            "name": name,
            **kwargs
        }
        nodes.append(node)
        return node

    return callback, nodes


@pytest.fixture
def assert_positions():
    """Helper to verify start/end positions match actual content."""
    def _assert_positions(text: str, nodes: list[dict[str, Any]]) -> None:
        """Verify all nodes with start/end have valid positions."""
        for node in nodes:
            if "start" in node:
                assert node["start"] >= 0, f"Node {node} has negative start position"
                assert node["start"] <= len(text), f"Node {node} start beyond text length"
            if "end" in node:
                assert node["end"] >= 0, f"Node {node} has negative end position"
                assert node["end"] <= len(text), f"Node {node} end beyond text length"
            if "start" in node and "end" in node:
                assert node["start"] <= node["end"], f"Node {node} start > end"

    return _assert_positions


def convert(html: str, callback: Callable[..., dict[str, Union[str, int]]] | None = None) -> str:
    """Helper to convert HTML to text with optional callback."""
    return html_to_text(html, node_parsed_callback=callback)