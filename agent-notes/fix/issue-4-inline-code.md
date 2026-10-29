# Goal
Resolve html_to_text issue4: keep inline code in its paragraph without automatic line breaks; retain genuine preformatted content.

# State
Independent branch fix/issue-4-inline-code from freshly fetched origin/master. Original untracked corpus is preserved. Actual NVDA paragraph retained as a fixture; focused regressions added before source changes. TDD complete:3failed/47passed before source fix,50passed afterward. One semantic source-line change removes code from pre classification; two explanatory docstrings match. Package0.15 with matching root lock metadata. Existing complete Python matrix uses Ubuntu24.04, independently pinned from the unsupported latest26.04 image. No publication or merge authority; root publishes and Q reviews/merges.

# Decisions and why
Smallest source change is to classify only pre as preformatted. Code is phrasing content and inherits preformatted context when inside pre. Existing tests wrongly expect standalone code to behave identically to pre; preserve every pre assertion and change each code expectation to normal whitespace handling rather than delete its coverage. Approximately one production line plus explanatory documentation, versions and focused tests.

# Surprises
Code currently both inserts a newline and exits its parent's pre state; the nested regression captures that second consequence of the same classification.

# Next step
Commit scoped files and return to root for source inspection/publication and PR CI. Do not push or publish. No full local suite, lint, build, review or CI steps were run.

# TDD evidence
Using this worktree's own Python3.12 environment, `.venv/Scripts/python.exe -B -m pytest tests/test_preformatted.py -q` first returned3failed/47passed. The real NVDA paragraph gained a newline before Windows+arrow and a double space afterward; inline whitespace remained preformatted; nested code inserted a newline and prematurely ended pre whitespace handling.
After removing code from the preformatted classification and correcting the old standalone-code expectations to inline semantics, the same actively authored file returned50passed. Every existing pre whitespace assertion is retained unchanged, and all existing code cases still assert their expected output. Added nested regression proves remaining preformatted text keeps multiple spaces/newlines after code closes.

# PR draft
Title: Keep inline code within normal paragraph flow

Body:
Treat code as inline phrasing content instead of entering preformatted block mode. Actual pre/code blocks inherit their pre context, including text after the inner code element closes. Preserve every preformatted assertion while updating standalone code cases to normal inline whitespace semantics. Retain the actual NVDA paragraph as the regression fixture. Library version0.15 and matching root lock metadata; the existing full Python3.8-3.12 CI matrix is independently pinned to supported Ubuntu24.04.

Closes #4.

TDD: tests/test_preformatted.py initially3failed/47passed, then50passed after the one-line behavioral fix. Full suite remains for PR CI. Independent branch from master with no other open PR's commits. Q handles review and merge; downstream parser output-version integration belongs to root after library integration.
