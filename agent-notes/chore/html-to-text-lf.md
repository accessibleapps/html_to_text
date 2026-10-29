# Goal
Q asked to review, fix and merge the open PRs: #6 (issue 1 URI schemes), #7 (issue 2 style ranges), #8 (issue 3 fragment links). This branch is the line-ending normalization Q chose so #8 can be integrated with a small diff.

# State
#6 merged, #7 merged (merge commits). This branch normalizes html_to_text.py to LF only; `git diff --ignore-cr-at-eol` against master is empty. #8 waits for this PR, then its add_link conflict with #6 is redone on the LF file.
html-4/html-5 worktrees (fix/issue-4-inline-code, fix/issue-5-list-boundaries) have no PRs; not touched.

# Decisions and why
html_to_text.py had mixed endings (631 of ~1008 lines CRLF on master). The Edit tool rewrites a mixed-ending file entirely to LF (one-line Edit took CR bytes 627 -> 0), so any edit through it produced whole-file churn; #8's first conflict resolution pushed ~1245 changed lines that way. Q chose (2026-10-29) a separate PR normalizing only html_to_text.py to LF. Six test files are uniformly CRLF; the Edit tool handles uniform files, so they stay as they are.
Reviews (ledgers in ~/.claude/reviews/accessibleapps-html_to_text-{6,7}.md), with real data from the untracked sample/ corpus (533 files):
- #6: no new errors, text unchanged, 53 hrefs changed, all mailto:/javascript: losing a bogus "doc/" prefix. urlsplit raises ValueError on malformed bracketed netlocs, but no such href exists in the corpus.
- #7: element_stack[-1] is the element being opened (parse_tag pushes before handle_starttag). Nonempty style ranges starting on whitespace: 1,119,873 -> 77,253; 0 reversed.
- #8: links matching emitted ids 18,987 -> 158,161, 0 lost. With file="" (document_parsers html.py, mobi.py, bookshare.py), urljoin leaves "./x.html" unnormalized; QRead interaction_handlers.py:45-53 matches hrefs against ids, else webbrowser.open, so no observable change.

# Surprises
Git Bash sed/grep/cat -A hide CR on this machine; count CRs with `tr -cd '\r' | wc -c` or Python bytes.

# Next step
Merge this PR after CI. Then in #8's worktree merge master, resolve html_to_text.py to master's LF file plus #8's three changes combined with #6 (import `unquote, urljoin, urlsplit`; drop posixpath; `if not reference.scheme and not reference.netloc: href = unquote(urljoin(self.file, href))`), push, CI, write #8 ledger, gate, merge. Then remove worktrees/branches for merged PRs.
