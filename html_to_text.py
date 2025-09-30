from io import StringIO
from logging import getLogger
import argparse
from enum import Enum
from pathlib import Path
import posixpath
import re
import sys
from typing import Callable, Optional, Union

from urllib.parse import unquote

import chardet
import lxml
import lxml.etree
import lxml.html
from lxml.etree import _Attrib, _Element

logger = getLogger("html_to_text")


class ContentState(Enum):
    """Represents the current content processing state.

    The state is determined by three boolean flags:
    - ignoring: whether we're inside ignored tags (script/style/title/pagenum)
    - in_pre: whether we're inside preformatted tags (pre/code)
    - starting: whether we've written any content yet (for boundary trimming)

    Note: ignoring takes precedence over in_pre when both are true.
    """
    STARTING_NORMAL = "starting_normal"      # Initial state, no content, normal mode
    STARTING_PRE = "starting_pre"            # No content yet, in pre/code tag
    STARTING_IGNORING = "starting_ignoring"  # No content yet, ignoring content
    WRITING_NORMAL = "writing_normal"        # Writing normal content
    WRITING_PRE = "writing_pre"              # Writing preformatted content
    WRITING_IGNORING = "writing_ignoring"    # Ignoring content after having written something

_collect_string_content = lxml.etree.XPath("string()")
HR_TEXT = "\n" + ("-" * 80)


class LXMLParser(object):
    def __init__(self, item: _Element) -> None:
        self.parse_tag(item)

    def parse_tag(self, item: _Element) -> None:
        if item.tag != lxml.etree.Comment and item.tag != lxml.etree.PI:
            self.handle_starttag(str(item.tag), item.attrib)
            if item.text is not None:
                self.handle_data(item.text, str(item.tag))
            for tag in item:
                self.parse_tag(tag)
            self.handle_endtag(str(item.tag), item)
        if item.tail:
            self.handle_data(item.tail, None)

    def handle_starttag(self, tag: str, attrs: _Attrib) -> None:  # type: ignore[misc]
        raise NotImplementedError

    def handle_data(self, data: str, start_tag: Optional[str]) -> None:  # type: ignore[misc]
        raise NotImplementedError

    def handle_endtag(self, tag: str, item: _Element) -> None:  # type: ignore[misc]
        raise NotImplementedError


class HTMLParser(LXMLParser):
    _heading_tags = "h1 h2 h3 h4 h5 h6".split(" ")
    _pre_tags = ("pre", "code")
    _table_tags = ("table", "tr", "td", "th", "thead", "tbody", "tfoot")
    _ignored = ["script", "style", "title"]
    whitespace_re = re.compile(r"\s+")
    _block = ("p", "div", "center", "blockquote")
    heading_levels = {"h1": 1, "h2": 2, "h3": 3, "h4": 4, "h5": 5, "h6": 6}

    def __init__(
        self,
        item: _Element,
        node_parsed_callback: Optional[
            Callable[..., dict[str, Union[str, int]]]
        ] = None,
        startpos: int = 0,
        file: str = "",
    ) -> None:
        self.node_parsed_callback = node_parsed_callback
        self.startpos = startpos
        self.file = file
        self.output = StringIO()
        self.add = ""
        self.initial_space = False
        self.ignoring = False
        self.in_pre = False
        self.last_data = ""
        self.out: list[str] = [""]
        self.starting = True  # Haven't written anything yet
        self.final_space = False
        self.heading_stack: list[tuple[int, int, Union[str, int, None]]] = []
        self.last_page: Optional[dict[str, Union[str, int]]] = None
        self.table_stack: list[dict[str, Union[str, int]]] = []
        self.last_newline = False
        self.last_start = ""
        self.link_start = 0
        LXMLParser.__init__(self, item)

    @property
    def state(self) -> ContentState:
        """Compute current state from boolean flags.

        Note: ignoring takes precedence over in_pre when both are true.
        """
        if self.ignoring:
            return ContentState.STARTING_IGNORING if self.starting else ContentState.WRITING_IGNORING
        elif self.in_pre:
            return ContentState.STARTING_PRE if self.starting else ContentState.WRITING_PRE
        else:
            return ContentState.STARTING_NORMAL if self.starting else ContentState.WRITING_NORMAL

    def _enter_pre_mode(self) -> None:
        """Transition to preformatted mode (pre/code tags)."""
        old_state = self.state
        self.in_pre = True
        new_state = self.state
        logger.debug(f"State transition: {old_state} -> {new_state} (enter_pre_mode)")

    def _exit_pre_mode(self) -> None:
        """Exit preformatted mode."""
        old_state = self.state
        self.in_pre = False
        new_state = self.state
        logger.debug(f"State transition: {old_state} -> {new_state} (exit_pre_mode)")

    def _enter_ignoring_mode(self) -> None:
        """Transition to ignoring mode (script/style/title/pagenum tags)."""
        old_state = self.state
        self.ignoring = True
        new_state = self.state
        logger.debug(f"State transition: {old_state} -> {new_state} (enter_ignoring_mode)")

    def _exit_ignoring_mode(self) -> None:
        """Exit ignoring mode."""
        old_state = self.state
        self.ignoring = False
        new_state = self.state
        logger.debug(f"State transition: {old_state} -> {new_state} (exit_ignoring_mode)")

    def _mark_writing(self) -> None:
        """Mark that we've started writing content (no longer in starting state)."""
        old_state = self.state
        self.starting = False
        new_state = self.state
        logger.debug(f"State transition: {old_state} -> {new_state} (mark_writing)")

    def handle_starttag(self, tag: str, attrs: _Attrib) -> None:  # type: ignore[override]
        if self.ignoring:
            return
        if tag in self._ignored or attrs.get("class", None) == "pagenum":
            self._enter_ignoring_mode()
            return
        elif tag in self._block:
            self.add = "\n\n"
            self.final_space = False
        elif tag in self._heading_tags:
            self.add = "\n\n"
            self.final_space = False
            level = self.heading_levels[tag]
            start = (
                self.output.tell()
                + self.startpos
                + (len(self.add) if not self.starting else 0)
                + (1 if self.final_space else 0)
            )
            if self.node_parsed_callback:
                self.heading_stack.append((level, start, None))
        if tag in self._pre_tags:
            self.add = "\n"
            self._enter_pre_mode()
        if tag == "a" and "href" in attrs:
            self.link_start = (
                self.output.tell()
                + self.startpos
                + (len(self.add) if not self.starting else 0)
                + (1 if self.final_space else 0)
            )
        if tag in ("dd", "dt"):
            self.add = "\n"
        if "id" in attrs and self.node_parsed_callback:
            self.node_parsed_callback(
                None,
                "id",
                self.file + "#" + attrs["id"],
                start=self.output.tell() + self.startpos + len(self.add),
            )
        if tag in self._table_tags and self.node_parsed_callback:
            if self.table_stack:
                parent = self.table_stack[-1]["id"]
            else:
                parent = None
            node = self.node_parsed_callback(
                parent,
                tag,
                None,
                start=self.output.tell() + self.startpos + len(self.add),
                attrs=dict(attrs),
            )
            self.table_stack.append(node)

    def handle_endtag(self, tag: str, item: _Element) -> None:  # type: ignore[override]
        if "class" in item.attrib and item.attrib["class"] == "pagenum":
            if self.last_page is not None:
                self.last_page["end"] = self.output.tell() + self.startpos
            if self.node_parsed_callback:
                self.last_page = self.node_parsed_callback(
                    None,
                    "page",
                    item.attrib["id"],
                    start=self.output.tell() + self.startpos,
                    pagenum=parse_pagenum(item.attrib["id"]),
                )
        if tag in self._ignored or item.attrib.get("class", None) == "pagenum":
            self._exit_ignoring_mode()
            return
        if tag in self._block:
            self.add = "\n\n"
        elif tag == "br":
            self.write_data("\n")
        elif tag in self._heading_tags:
            self.add = "\n\n"
            if self.node_parsed_callback:
                self.add_heading_node(tag)
        elif tag in self._pre_tags:
            self._exit_pre_mode()
        elif tag == "a" and "href" in item.attrib and self.node_parsed_callback:
            self.add_link(item)
        elif tag == "hr":
            self.output.write(HR_TEXT)
        elif tag in self._table_tags and self.node_parsed_callback:
            self.table_stack[-1]["end"] = self.output.tell() + self.startpos
            self.table_stack.pop()
        self.last_start = tag

    def handle_data(self, data: str, start_tag: Optional[str]) -> None:  # type: ignore[override]
        if self.ignoring:
            return
        if self.in_pre:
            if self.add:
                self.write_data(self.add)
                self.add = ""
            self.write_data(data)
            return
        data = self.whitespace_re.sub(" ", data)
        # The newline after <br> will turn into space above. Also,
        # <span>a</span> <span>b</span> will return a space after a. We want to keep it
        if data[0] == " ":
            self.initial_space = True
            data = data[1:]
        if not data:
            return
        if not self.add and self.final_space:
            self.write_data(" ")
            self.final_space = False
        if data and data[-1] == " ":
            self.final_space = True
            data = data[:-1]
        if self.starting:
            self.initial_space = False
            self.add = ""
        if self.add:
            self.write_data(self.add)
            self.add = ""
        if self.initial_space and not self.last_newline:
            self.write_data(" ")
        self.write_data(data)
        self.add = ""
        self.initial_space = False

    def write_data(self, data: str) -> None:
        self.output.write(data)
        self.last_newline = data[-1] == "\n"
        self.last_data = data
        self._mark_writing()

    def add_heading_node(self, item: str) -> None:
        """Adds a heading to the list of nodes.
        We can't have an end heading without a start heading."""
        (level, start, node_id) = self.heading_stack.pop()
        end = self.output.tell() + self.startpos
        while self.need_heading_pop(level):
            self.heading_stack.pop()
        # The last element of the stack is our parent. If it's empty, we have no parent.
        parent = None
        if len(self.heading_stack):
            parent = self.heading_stack[-1][2]
        # parent should be set, create the heading. We need to put it back on the stack for the next heading to grab
        # its parent if needed.
        name = None  # self.output.getvalue()[start:end+1]
        if self.node_parsed_callback is not None:
            id = self.node_parsed_callback(
                parent, "heading", name, start=start, end=end, tag=item, level=item[-1]
            )["id"]
            self.heading_stack.append((level, start, id))

    def need_heading_pop(self, level: int) -> bool:
        if len(self.heading_stack) == 0:
            return False  # nothing to pop
        prev_level = self.heading_stack[-1][0]
        if level <= prev_level:
            return True
        return False

    def add_link(self, item: _Element) -> None:
        text = _collect_string_content(item)
        # Is this an internal link?
        href = item.attrib["href"]
        if "://" not in href:
            href = unquote(item.attrib["href"])
            href = posixpath.normpath(
                posixpath.join(posixpath.dirname(self.file), href)
            )
        if self.node_parsed_callback is not None:
            self.node_parsed_callback(
                None,
                "link",
                text,
                start=self.link_start,
                end=self.output.tell() + self.startpos,
                href=href,
            )


def html_to_text(
    item: Union[str, _Element],
    node_parsed_callback: Optional[Callable[..., dict[str, Union[str, int]]]] = None,
    startpos: int = 0,
    file: str = "",
) -> str:
    if isinstance(item, str):
        item = tree_from_string(item)
    lxml.html.xhtml_to_html(item)  # type: ignore[arg-type]
    parser = HTMLParser(item, node_parsed_callback, startpos, file)
    text = parser.output.getvalue()
    if parser.last_page is not None:
        parser.last_page["end"] = parser.output.tell()
    return text


pagenum_re = re.compile(r"(\d+)$")


def parse_pagenum(num: str) -> Optional[str]:
    r = pagenum_re.search(num)
    if r:
        return str(int(r.group(1)))
    elif num.startswith("p"):
        return num[1:].lower()
    else:
        logger.warning("unable to parse page %r" % num)
        return None


def tree_from_string(html: str) -> _Element:
    try:
        return lxml.etree.fromstring(html)
    except lxml.etree.XMLSyntaxError:
        pass
    return lxml.html.fromstring(html)


def main() -> int:
    """Command-line interface for html_to_text."""
    parser = argparse.ArgumentParser(
        description="Convert HTML files to plain text",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s input.html                    # Output to input.txt
  %(prog)s input.html -o output.txt      # Specify output file
  %(prog)s page.htm -o -                 # Write to stdout
  %(prog)s - -o output.txt               # Read from stdin
        """,
    )
    parser.add_argument(
        "input",
        help="Input HTML file (use '-' for stdin)",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output text file (default: input filename with .txt extension, use '-' for stdout)",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Overwrite output file if it exists",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress status messages",
    )

    args = parser.parse_args()

    # Read input
    try:
        if args.input == "-":
            html_content = sys.stdin.read()
            input_path = None
        else:
            input_path = Path(args.input)
            if not input_path.exists():
                print(f"Error: Input file not found: {args.input}", file=sys.stderr)
                return 1
            # Try UTF-8 first, then use chardet for detection
            try:
                html_content = input_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                # Detect encoding with chardet
                raw_data = input_path.read_bytes()
                detected = chardet.detect(raw_data)
                encoding = detected.get("encoding", "utf-8")
                confidence = detected.get("confidence", 0.0)

                if encoding and confidence > 0.7:
                    html_content = raw_data.decode(encoding)
                    if not args.quiet:
                        print(
                            f"Note: File decoded using {encoding} encoding (confidence: {confidence:.1%})",
                            file=sys.stderr,
                        )
                else:
                    # Fall back to latin-1 which can decode any byte sequence
                    html_content = raw_data.decode("latin-1", errors="replace")
                    if not args.quiet:
                        print(
                            "Note: File decoded using latin-1 fallback encoding",
                            file=sys.stderr,
                        )
    except Exception as e:
        print(f"Error reading input: {e}", file=sys.stderr)
        return 1

    # Convert HTML to text
    try:
        text_content = html_to_text(html_content)
    except Exception as e:
        print(f"Error converting HTML: {e}", file=sys.stderr)
        return 1

    # Determine output path
    if args.output:
        output_path = args.output
    elif input_path:
        # Use just the filename (no directory) and replace extension with .txt
        filename = input_path.name
        if input_path.suffix.lower() in {".html", ".htm"}:
            output_filename = Path(filename).with_suffix(".txt")
            output_path = str(output_filename)
        else:
            output_path = filename + ".txt"
    else:
        # Reading from stdin, write to stdout
        output_path = "-"

    # Write output
    try:
        if output_path == "-":
            sys.stdout.write(text_content)
        else:
            output_file = Path(output_path)
            if output_file.exists() and not args.force:
                print(
                    f"Error: Output file already exists: {output_path}",
                    file=sys.stderr,
                )
                print("Use -f/--force to overwrite", file=sys.stderr)
                return 1

            output_file.write_text(text_content, encoding="utf-8")
            if not args.quiet:
                print(f"Converted {args.input} -> {output_path}")
    except Exception as e:
        print(f"Error writing output: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
