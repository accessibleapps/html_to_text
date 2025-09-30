"""Tests for state machine behavior."""

import pytest

from html_to_text import ContentState, HTMLParser
from lxml import html as lxml_html
from tests.conftest import convert


class TestStateProperty:
    """Test that state property correctly computes from flags."""

    def test_starting_normal_initial_state(self):
        """Test STARTING_NORMAL state with appropriate flags."""
        tree = lxml_html.fromstring("<p>text</p>")
        parser = HTMLParser(tree)
        # Set flags to simulate starting normal state
        parser.starting = True
        parser.ignoring = False
        parser.in_pre = False
        assert parser.state == ContentState.STARTING_NORMAL

    def test_starting_pre_state(self):
        """State when in pre tag before writing content."""
        tree = lxml_html.fromstring("<p>text</p>")
        parser = HTMLParser(tree)
        # Manually set flags to simulate entering pre tag before writing
        parser.starting = True
        parser.in_pre = True
        parser.ignoring = False
        assert parser.state == ContentState.STARTING_PRE

    def test_starting_ignoring_state(self):
        """State when ignoring before writing content."""
        tree = lxml_html.fromstring("<p>text</p>")
        parser = HTMLParser(tree)
        # Manually set flags to simulate entering ignored tag before writing
        parser.starting = True
        parser.ignoring = True
        parser.in_pre = False
        assert parser.state == ContentState.STARTING_IGNORING

    def test_writing_normal_state(self):
        """State when writing normal content."""
        tree = lxml_html.fromstring("<p>text</p>")
        parser = HTMLParser(tree)
        # Manually set flags to simulate writing normal content
        parser.starting = False
        parser.ignoring = False
        parser.in_pre = False
        assert parser.state == ContentState.WRITING_NORMAL

    def test_writing_pre_state(self):
        """State when writing preformatted content."""
        tree = lxml_html.fromstring("<p>text</p>")
        parser = HTMLParser(tree)
        # Manually set flags to simulate writing in pre tag
        parser.starting = False
        parser.in_pre = True
        parser.ignoring = False
        assert parser.state == ContentState.WRITING_PRE

    def test_writing_ignoring_state(self):
        """State when ignoring after having written content."""
        tree = lxml_html.fromstring("<p>text</p>")
        parser = HTMLParser(tree)
        # Manually set flags to simulate ignoring after writing
        parser.starting = False
        parser.ignoring = True
        parser.in_pre = False
        assert parser.state == ContentState.WRITING_IGNORING

    def test_ignoring_takes_precedence_over_pre(self):
        """When both ignoring and in_pre are true, ignoring takes precedence."""
        tree = lxml_html.fromstring("<p>text</p>")
        parser = HTMLParser(tree)
        # Both flags true - ignoring takes precedence
        parser.starting = False
        parser.ignoring = True
        parser.in_pre = True
        assert parser.state == ContentState.WRITING_IGNORING

        # Same with starting=True
        parser.starting = True
        assert parser.state == ContentState.STARTING_IGNORING


class TestStateTransitionsDuringParsing:
    """Test state transitions during actual HTML parsing."""

    def test_simple_text_transitions(self):
        """Test state transitions for simple text conversion."""
        states_seen = []

        class StateTrackingParser(HTMLParser):
            def write_data(self, data):
                states_seen.append(self.state)
                super().write_data(data)

        tree = lxml_html.fromstring("<p>text</p>")
        parser = StateTrackingParser(tree)

        # Should transition from STARTING_NORMAL to WRITING_NORMAL
        assert ContentState.STARTING_NORMAL in states_seen or ContentState.WRITING_NORMAL in states_seen

    def test_pre_tag_state(self):
        """Test state when processing pre tag."""
        states_seen = []

        class StateTrackingParser(HTMLParser):
            def handle_data(self, data, start_tag):
                states_seen.append((self.state, data[:20] if len(data) > 20 else data))
                super().handle_data(data, start_tag)

        tree = lxml_html.fromstring("<pre>preformatted</pre>")
        parser = StateTrackingParser(tree)

        # Should see PRE states
        pre_states = [s for s, _ in states_seen if s in (ContentState.STARTING_PRE, ContentState.WRITING_PRE)]
        assert len(pre_states) > 0

    def test_ignored_tag_state(self):
        """Test state when processing ignored tags."""
        states_seen = []

        class StateTrackingParser(HTMLParser):
            def handle_data(self, data, start_tag):
                states_seen.append(self.state)
                super().handle_data(data, start_tag)

        tree = lxml_html.fromstring("<p>before</p><script>ignored</script><p>after</p>")
        parser = StateTrackingParser(tree)

        # Should see NORMAL states (ignored content doesn't call handle_data)
        assert ContentState.WRITING_NORMAL in states_seen

    def test_pagenum_inside_pre_state(self):
        """Test state for pagenum (ignored) inside pre tag."""
        states_seen = []

        class StateTrackingParser(HTMLParser):
            def handle_starttag(self, tag, attrs):
                states_seen.append(("start", tag, self.state))
                super().handle_starttag(tag, attrs)

            def handle_endtag(self, tag, item):
                states_seen.append(("end", tag, self.state))
                super().handle_endtag(tag, item)

        tree = lxml_html.fromstring('<pre>before<span class="pagenum">1</span>after</pre>')
        parser = StateTrackingParser(tree)

        # Should see transitions: PRE -> IGNORING -> PRE
        state_sequence = [s for _, _, s in states_seen]
        assert ContentState.STARTING_PRE in state_sequence or ContentState.WRITING_PRE in state_sequence
        assert ContentState.WRITING_IGNORING in state_sequence or ContentState.STARTING_IGNORING in state_sequence


class TestStateFlagConsistency:
    """Test that state property stays consistent with flags."""

    def test_all_flag_combinations(self):
        """Test state for all valid flag combinations."""
        tree = lxml_html.fromstring("<p>text</p>")
        parser = HTMLParser(tree)

        # Test all 8 combinations of the 3 boolean flags
        test_cases = [
            # (starting, ignoring, in_pre, expected_state)
            (True, False, False, ContentState.STARTING_NORMAL),
            (True, False, True, ContentState.STARTING_PRE),
            (True, True, False, ContentState.STARTING_IGNORING),
            (True, True, True, ContentState.STARTING_IGNORING),  # ignoring takes precedence
            (False, False, False, ContentState.WRITING_NORMAL),
            (False, False, True, ContentState.WRITING_PRE),
            (False, True, False, ContentState.WRITING_IGNORING),
            (False, True, True, ContentState.WRITING_IGNORING),  # ignoring takes precedence
        ]

        for starting, ignoring, in_pre, expected_state in test_cases:
            parser.starting = starting
            parser.ignoring = ignoring
            parser.in_pre = in_pre
            assert parser.state == expected_state, (
                f"Expected {expected_state} for starting={starting}, "
                f"ignoring={ignoring}, in_pre={in_pre}, got {parser.state}"
            )


class TestStateInRealConversions:
    """Test state behavior during real HTML conversions."""

    def test_paragraph_conversion_state(self):
        """Verify state during paragraph conversion."""
        # This is more of an integration test - just ensure conversion works
        # with state property present
        result = convert("<p>text</p>")
        assert result == "text"

    def test_pre_conversion_state(self):
        """Verify state during pre tag conversion."""
        result = convert("<pre>preformatted</pre>")
        assert result == "\npreformatted"

    def test_ignored_conversion_state(self):
        """Verify state during ignored tag conversion."""
        result = convert("<p>before</p><script>ignored</script><p>after</p>")
        assert "before" in result
        assert "ignored" not in result
        assert "after" in result

    def test_complex_nesting_state(self):
        """Verify state during complex nested conversions."""
        html = '<div><p>normal</p><pre>pre</pre><script>ignored</script></div>'
        result = convert(html)
        assert "normal" in result
        assert "pre" in result
        assert "ignored" not in result