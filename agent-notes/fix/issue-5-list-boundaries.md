# Goal
Resolve html_to_text issue5: preserve text boundaries between adjacent HTML list items.

# State
Independent branch fix/issue-5-list-boundaries from freshly fetched origin/master. Original unrelated corpus and worktrees preserved. Raw first UL retained verbatim from existing sample/all.html. Focused TDD5failed before the source change and5passed afterward. Added li to the existing block set; package0.15 and matching root lock metadata. Existing complete Python matrix retained on supported Ubuntu24.04. No publication; root publishes and Q reviews/merges.

# Decisions and why
The existing pending-output mechanism already separates block entries and avoids leading/trailing/duplicate separators. Smallest change is to recognize li in the existing block set, one production line, covering both start and end handlers. No bullet generation, list-node model or new traversal. Focused cases cover exact raw Rust output/link ranges, nested UL/OL, inline spans and empty items.

# Surprises
Minified markup exposes concatenation that indentation whitespace can mask. Existing list/link integration tests count nodes but do not assert boundaries.

# Next step
Commit scoped files and return to root for source verification, publication and PR CI. Do not push, review or merge.

# TDD evidence
Own isolated environment: uv sync --frozen --all-groups --python3.12. Command .venv/Scripts/python.exe -B -m pytest tests/test_list_boundaries.py -q produced5failed before source edits and5passed afterward. The original minified Rust list concatenated all ten labels; after the one-line fix labels are separated by the same two-newline boundary used for existing blocks. Exact link text ranges still match each label. Nested UL/OL, parent tail, inline spans, surrounding text and empty items preserve boundaries without extra pending separators. No full local suite, lint or build was run.

# PR draft
Title: Preserve text boundaries between HTML list items

Body: Treat li as an existing block boundary so minified adjacent entries no longer run together. Reuse pending separators for nested UL/OL, surrounding text and empty items; inline content remains intact. No new list nodes or bullet-generation machinery. Library version0.15 and matching root lock metadata; existing full Python3.8-3.12 matrix stays on supported Ubuntu24.04.

Closes #5.

TDD: retained the actual first UL from the Rust documentation sample; tests/test_list_boundaries.py produced5failures before the one-line source change and5passes afterward. Covers exact list output and link ranges, nested UL/OL, inline spans and empty entries. Full suite awaits PR CI. Independent branch from master; Q handles review and merge. Downstream parser-version integration remains root-owned after library integration.
