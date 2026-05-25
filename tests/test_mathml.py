"""Tests for MathML extraction.

MathML should enter the reading stream as one accessible inline math run and
also produce a structural node for downstream consumers that want richer math
handling later.
"""

from html_to_text import html_to_text
from tests.conftest import convert


def test_mathml_alttext_is_preferred():
    html = (
        '<p>Let <math alttext="x squared plus y squared">'
        "<msup><mi>x</mi><mn>2</mn></msup><mo>+</mo>"
        "<msup><mi>y</mi><mn>2</mn></msup></math> be fixed.</p>"
    )

    assert convert(html) == "Let x squared plus y squared be fixed."


def test_mathml_annotation_is_used_before_presentation_fallback():
    html = (
        "<p><math><semantics><mrow><mi>x</mi><mo>+</mo><mi>y</mi></mrow>"
        '<annotation encoding="application/x-tex">x + y</annotation>'
        "</semantics></math></p>"
    )

    assert convert(html) == "x + y"


def test_mathml_presentation_fallback_keeps_operator_spacing():
    html = (
        "<p>Equation: <math><mrow><mi>a</mi><mo>+</mo><mi>b</mi>"
        "<mo>=</mo><mi>c</mi></mrow></math>.</p>"
    )

    assert convert(html) == "Equation: a + b = c."


def test_mathml_superscript_fallback_is_linearized():
    html = "<p><math><msup><mi>x</mi><mn>2</mn></msup></math></p>"

    assert convert(html) == "x^2"


def test_mathml_callback_gets_raw_mathml_and_text_span(simple_callback):
    callback, nodes = simple_callback
    html = '<p>Use <math display="block"><mi>x</mi><mo>+</mo><mi>1</mi></math>.</p>'

    text = html_to_text(html, node_parsed_callback=callback)

    assert text == "Use x + 1."
    math_nodes = [node for node in nodes if node["type"] == "math"]
    assert len(math_nodes) == 1
    math_node = math_nodes[0]
    assert math_node["name"] == "x + 1"
    assert text[math_node["start"] : math_node["end"]] == "x + 1"
    assert math_node["display"] == "block"
    assert "<math" in math_node["mathml"]
