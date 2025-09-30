"""Tests for state machine behavior."""

from io import StringIO
import pytest

from html_to_text import ContentState, HTMLParser
from lxml import html as lxml_html
from tests.conftest import convert


class TestStateProperty:
    """Test state transitions using the state machine."""

    def test_starting_normal_initial_state(self):
        """Initial state should be STARTING_NORMAL."""
        html = "<p>text</p>"
        tree = lxml_html.fromstring(html)

        # Create parser that skips parsing to just test initial state
        class NoParseParser(HTMLParser):
            def parse_tag(self, item):
                # Override to prevent actual parsing, we just want to test initial state
                pass

        parser = NoParseParser(tree)
        assert parser.state == ContentState.STARTING_NORMAL

    def test_starting_pre_state(self):
        """State transitions to STARTING_PRE when entering pre."""
        html = "<p>text</p>"
        tree = lxml_html.fromstring(html)
        parser = HTMLParser(tree)
        # Manually trigger state machine transition
        parser._pre_context = True
        parser.machine.set_state(ContentState.STARTING_NORMAL)  # Reset to starting
        parser.enter_pre()
        assert parser.state == ContentState.STARTING_PRE

    def test_starting_ignoring_state(self):
        """State transitions to STARTING_IGNORING when entering ignoring."""
        html = "<p>text</p>"
        tree = lxml_html.fromstring(html)
        parser = HTMLParser(tree)
        # Manually trigger state machine transition
        parser.machine.set_state(ContentState.STARTING_NORMAL)  # Reset to starting
        parser.enter_ignoring()
        assert parser.state == ContentState.STARTING_IGNORING

    def test_writing_normal_state(self):
        """State transitions to WRITING_NORMAL when writing."""
        html = "<p>text</p>"
        tree = lxml_html.fromstring(html)
        parser = HTMLParser(tree)
        # Manually trigger state machine transition
        parser.machine.set_state(ContentState.STARTING_NORMAL)  # Reset to starting
        parser.mark_writing()
        assert parser.state == ContentState.WRITING_NORMAL

    def test_writing_pre_state(self):
        """State transitions to WRITING_PRE."""
        html = "<p>text</p>"
        tree = lxml_html.fromstring(html)
        parser = HTMLParser(tree)
        # Manually trigger state machine transitions
        parser.machine.set_state(ContentState.STARTING_NORMAL)  # Reset
        parser._pre_context = True
        parser.enter_pre()
        parser.mark_writing()
        assert parser.state == ContentState.WRITING_PRE

    def test_writing_ignoring_state(self):
        """State transitions to WRITING_IGNORING."""
        html = "<p>text</p>"
        tree = lxml_html.fromstring(html)
        parser = HTMLParser(tree)
        # Manually trigger state machine transitions
        parser.machine.set_state(ContentState.STARTING_NORMAL)  # Reset
        parser.mark_writing()
        parser.enter_ignoring()
        assert parser.state == ContentState.WRITING_IGNORING

    def test_ignoring_takes_precedence_over_pre(self):
        """Ignoring state takes precedence in state machine."""
        html = "<p>text</p>"
        tree = lxml_html.fromstring(html)
        parser = HTMLParser(tree)
        # Enter pre then ignoring
        parser.machine.set_state(ContentState.STARTING_NORMAL)  # Reset
        parser._pre_context = True
        parser.enter_pre()
        parser.enter_ignoring()
        assert parser.state == ContentState.STARTING_IGNORING

        # Same after writing
        parser2 = HTMLParser(tree)
        parser2.machine.set_state(ContentState.STARTING_NORMAL)  # Reset
        parser2.mark_writing()
        parser2._pre_context = True
        parser2.enter_pre()
        parser2.enter_ignoring()
        assert parser2.state == ContentState.WRITING_IGNORING


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
    """Test that state machine transitions work correctly."""

    def test_all_state_transitions(self):
        """Test all valid state transitions."""
        tree = lxml_html.fromstring("<p>text</p>")
        parser = HTMLParser(tree)

        # Test state transitions
        parser.machine.set_state(ContentState.STARTING_NORMAL)
        assert parser.state == ContentState.STARTING_NORMAL

        # STARTING_NORMAL -> STARTING_PRE
        parser.machine.set_state(ContentState.STARTING_NORMAL)
        parser._pre_context = True
        parser.enter_pre()
        assert parser.state == ContentState.STARTING_PRE

        # STARTING_NORMAL -> STARTING_IGNORING
        parser.machine.set_state(ContentState.STARTING_NORMAL)
        parser.enter_ignoring()
        assert parser.state == ContentState.STARTING_IGNORING

        # STARTING_NORMAL -> WRITING_NORMAL
        parser.machine.set_state(ContentState.STARTING_NORMAL)
        parser.mark_writing()
        assert parser.state == ContentState.WRITING_NORMAL

        # STARTING_PRE -> WRITING_PRE
        parser.machine.set_state(ContentState.STARTING_NORMAL)
        parser._pre_context = True
        parser.enter_pre()
        parser.mark_writing()
        assert parser.state == ContentState.WRITING_PRE

        # WRITING_NORMAL -> WRITING_IGNORING
        parser.machine.set_state(ContentState.STARTING_NORMAL)
        parser.mark_writing()
        parser.enter_ignoring()
        assert parser.state == ContentState.WRITING_IGNORING


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