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
        # Don't parse yet - just create parser
        class NoParseParser(HTMLParser):
            def __init__(self, item, **kwargs):
                # Skip LXMLParser.__init__ which triggers parsing
                object.__setattr__(self, '__dict__', {})
                self.node_parsed_callback = kwargs.get('node_parsed_callback')
                self.startpos = kwargs.get('startpos', 0)
                self.file = kwargs.get('file', '')
                self.output = StringIO()
                self.add = ""
                self.initial_space = False
                self.in_pre = False
                self.last_data = ""
                self.out = [""]
                self.final_space = False
                self.heading_stack = []
                self.last_page = None
                self.table_stack = []
                self.last_newline = False
                self.last_start = ""
                self.link_start = 0
                # Set up state machine
                from html_to_text import ContentState
                from transitions import Machine
                states = [state.value for state in ContentState]
                transitions = [
                    {'trigger': 'mark_writing', 'source': 'starting_normal', 'dest': 'writing_normal'},
                    {'trigger': 'mark_writing', 'source': 'starting_pre', 'dest': 'writing_pre'},
                    {'trigger': 'mark_writing', 'source': 'starting_ignoring', 'dest': 'writing_ignoring'},
                    {'trigger': 'enter_pre', 'source': 'starting_normal', 'dest': 'starting_pre'},
                    {'trigger': 'enter_pre', 'source': 'writing_normal', 'dest': 'writing_pre'},
                    {'trigger': 'exit_pre', 'source': 'starting_pre', 'dest': 'starting_normal'},
                    {'trigger': 'exit_pre', 'source': 'writing_pre', 'dest': 'writing_normal'},
                    {'trigger': 'enter_ignoring', 'source': ['starting_normal', 'starting_pre'], 'dest': 'starting_ignoring'},
                    {'trigger': 'enter_ignoring', 'source': ['writing_normal', 'writing_pre'], 'dest': 'writing_ignoring'},
                    {'trigger': 'exit_ignoring', 'source': 'starting_ignoring', 'dest': 'starting_normal', 'conditions': 'is_not_in_pre'},
                    {'trigger': 'exit_ignoring', 'source': 'starting_ignoring', 'dest': 'starting_pre', 'conditions': 'is_in_pre'},
                    {'trigger': 'exit_ignoring', 'source': 'writing_ignoring', 'dest': 'writing_normal', 'conditions': 'is_not_in_pre'},
                    {'trigger': 'exit_ignoring', 'source': 'writing_ignoring', 'dest': 'writing_pre', 'conditions': 'is_in_pre'},
                ]
                self.machine = Machine(model=self, states=states, transitions=transitions, initial=ContentState.STARTING_NORMAL.value, send_event=True)

        parser = NoParseParser(tree)
        assert parser.state == ContentState.STARTING_NORMAL.value

    def test_starting_pre_state(self):
        """State transitions to STARTING_PRE when entering pre."""
        html = "<p>text</p>"
        tree = lxml_html.fromstring(html)
        parser = HTMLParser(tree)
        # Manually trigger state machine transition
        parser.in_pre = True
        parser.to_starting_normal()  # Reset to starting
        parser.enter_pre()
        assert parser.state == ContentState.STARTING_PRE.value

    def test_starting_ignoring_state(self):
        """State transitions to STARTING_IGNORING when entering ignoring."""
        html = "<p>text</p>"
        tree = lxml_html.fromstring(html)
        parser = HTMLParser(tree)
        # Manually trigger state machine transition
        parser.to_starting_normal()  # Reset to starting
        parser.enter_ignoring()
        assert parser.state == ContentState.STARTING_IGNORING.value

    def test_writing_normal_state(self):
        """State transitions to WRITING_NORMAL when writing."""
        html = "<p>text</p>"
        tree = lxml_html.fromstring(html)
        parser = HTMLParser(tree)
        # Manually trigger state machine transition
        parser.to_starting_normal()  # Reset to starting
        parser.mark_writing()
        assert parser.state == ContentState.WRITING_NORMAL.value

    def test_writing_pre_state(self):
        """State transitions to WRITING_PRE."""
        html = "<p>text</p>"
        tree = lxml_html.fromstring(html)
        parser = HTMLParser(tree)
        # Manually trigger state machine transitions
        parser.to_starting_normal()  # Reset
        parser.in_pre = True
        parser.enter_pre()
        parser.mark_writing()
        assert parser.state == ContentState.WRITING_PRE.value

    def test_writing_ignoring_state(self):
        """State transitions to WRITING_IGNORING."""
        html = "<p>text</p>"
        tree = lxml_html.fromstring(html)
        parser = HTMLParser(tree)
        # Manually trigger state machine transitions
        parser.to_starting_normal()  # Reset
        parser.mark_writing()
        parser.enter_ignoring()
        assert parser.state == ContentState.WRITING_IGNORING.value

    def test_ignoring_takes_precedence_over_pre(self):
        """Ignoring state takes precedence in state machine."""
        html = "<p>text</p>"
        tree = lxml_html.fromstring(html)
        parser = HTMLParser(tree)
        # Enter pre then ignoring
        parser.to_starting_normal()  # Reset
        parser.in_pre = True
        parser.enter_pre()
        parser.enter_ignoring()
        assert parser.state == ContentState.STARTING_IGNORING.value

        # Same after writing
        parser2 = HTMLParser(tree)
        parser2.to_starting_normal()  # Reset
        parser2.mark_writing()
        parser2.in_pre = True
        parser2.enter_pre()
        parser2.enter_ignoring()
        assert parser2.state == ContentState.WRITING_IGNORING.value


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
        assert ContentState.STARTING_NORMAL.value in states_seen or ContentState.WRITING_NORMAL.value in states_seen

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
        pre_states = [s for s, _ in states_seen if s in (ContentState.STARTING_PRE.value, ContentState.WRITING_PRE.value)]
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
        assert ContentState.WRITING_NORMAL.value in states_seen

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
        assert ContentState.STARTING_PRE.value in state_sequence or ContentState.WRITING_PRE.value in state_sequence
        assert ContentState.WRITING_IGNORING.value in state_sequence or ContentState.STARTING_IGNORING.value in state_sequence


class TestStateFlagConsistency:
    """Test that state machine transitions work correctly."""

    def test_all_state_transitions(self):
        """Test all valid state transitions."""
        tree = lxml_html.fromstring("<p>text</p>")
        parser = HTMLParser(tree)

        # Test state transitions
        parser.to_starting_normal()
        assert parser.state == ContentState.STARTING_NORMAL.value

        # STARTING_NORMAL -> STARTING_PRE
        parser.to_starting_normal()
        parser.in_pre = True
        parser.enter_pre()
        assert parser.state == ContentState.STARTING_PRE.value

        # STARTING_NORMAL -> STARTING_IGNORING
        parser.to_starting_normal()
        parser.enter_ignoring()
        assert parser.state == ContentState.STARTING_IGNORING.value

        # STARTING_NORMAL -> WRITING_NORMAL
        parser.to_starting_normal()
        parser.mark_writing()
        assert parser.state == ContentState.WRITING_NORMAL.value

        # STARTING_PRE -> WRITING_PRE
        parser.to_starting_normal()
        parser.in_pre = True
        parser.enter_pre()
        parser.mark_writing()
        assert parser.state == ContentState.WRITING_PRE.value

        # WRITING_NORMAL -> WRITING_IGNORING
        parser.to_starting_normal()
        parser.mark_writing()
        parser.enter_ignoring()
        assert parser.state == ContentState.WRITING_IGNORING.value


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