# Goal
Resolve issue2: explicit style callback ranges start at their emitted content rather than preceding separators.

# State
Independent branch fix/issue-2-style-ranges from fetched origin/master. Raw fixture and focused tests reproduce block and inline offset errors. Existing handler now records pending-adjusted starts after start-tag processing; empty ranges clamp to their emitted end. Package0.15 and matching root lock version; runner pinned to24.04 without changing the Python matrix. Root publishes and Q reviews/merges.

# Decisions and why
Smallest change: record the current element's pending-output-adjusted start after its start tag updates block/preformatted state, approximately3-5 source lines in the existing handler. Keep extraction text and semantic style machinery unchanged. Focused cases retain actual Inline Styles Test input, use nonzero startpos, and check nested/inline positions. Avoid copying CSS extraction helpers or other URI/list/code fixes.
The three-line position update can predict a separator for an empty element; the existing callback now clamps that empty range to end, matching the existing heading-range convention. One additional source line. Exact extracted text is asserted unchanged.

# Surprises
The existing stack starts tracking before the element's start handler has set its pending separator. Merely replacing output.tell() before that handler would miss newly established block boundaries.

# Next step
Finish focused test, inspect and commit only this issue's files, then return to root without publishing.

# TDD evidence
Own Python3.12 worktree environment, created using uv sync --frozen --all-groups. `uv run --no-sync pytest tests/test_explicit_style_positions.py -q` initially failed4 cases: actual block positions25/50 instead27/52 and inline Beta start5 instead6, each with startpos0/41. The three-line start update passed all4. Added the empty-style case, which failed with reversed range7/5; callback clamp fixes it. Final focused result after source edits completed:5 passed in0.52s. No full CI suite, linter or build was run locally.

# CI setup
Root traced PR6's setup failure to ubuntu-latest26.04 lacking setup-python3.9. The official binary manifest supports all existing Python3.8-3.12 entries on24.04. This independent branch carries the same one-line existing-runner pin; no stack or inherited PR6 commit, matrix unchanged.

# PR draft
Title: Align explicit CSS ranges with emitted element content
Body: Record explicit style starts after pending separators are established, excluding preceding block separators and spaces from style ranges. Empty styled elements keep empty nonreversed ranges. Preserve extracted text. Closes #2. Retains the actual Inline Styles Test input; focused TDD4 failures before fix, then final5 cases. Library0.15 with matching root lock metadata. Existing Python3.8-3.12 CI matrix uses supported Ubuntu24.04. Full CI awaits root publication. Downstream parser output-version integration follows once this library is integrated.
