# Goal
Resolve html_to_text issue1: preserve URI schemes and authority-bearing external references during archive-link extraction, with one independent TDD PR.

# State
Branch fix/issue-1-uri-schemes starts from fetched origin/master. Focused TDD is complete; six scoped files are committed locally for root publication. Only this issue's source, focused regression, raw fixture, package version, matching editable-package lock metadata and task note changed. No publication or merge authority; root publishes and Q reviews/merges.

# Decisions and why
Source change: import urlsplit, parse href, and normalize only references with neither scheme nor authority. Existing internal path normalization remains. Issue3's fragment-only resolution is excluded. The exact existing NVDA anchor is retained in tests/fixtures/nvda-mailto.html; it was read directly from the original sample/changes.html before copying. Standard scheme forms and archive-relative controls exercise the same public extraction contract. Version moves from0.14 to0.15 using the existing convention; uv.lock changes only its editable root package version, not dependency resolutions.

TDD command, from this worktree: `.venv/Scripts/python.exe -B -m pytest tests/test_uri_schemes.py -q`. Before the source fix:5 failed,4 passed. The NVDA anchor failed with actual href docs/mailto:info@nvaccess.org versus expected mailto:info@nvaccess.org; tel/urn and scheme-relative encoding cases also failed. After the source fix:9 passed. Cases include actual NVDA text ranges, mailto query encoding, tel,urn,https,authority references, and relative/parent/encoded archive paths. No full suite, linter or package build was run locally; PR CI remains root's responsibility.

# Surprises
PR6 CI failed before tests because ubuntu-latest moved to26.04 and setup-python could not install3.9 there. The official actions/python-versions manifest lists24.04 binaries for every existing3.8-3.12 matrix entry. Pin the existing runner to24.04, retaining the complete Python matrix and test command. No new guard or relaxed check.
uv sync --locked rejected the committed lock because the machine's global exclude-newer cutoff requests re-resolution. Use --frozen to consume the committed graph without unrelated dependency changes, in this worktree's own environment.

# Next step
Root inspects and publishes the independent PR, then follows its CI. No changes to downstream consumer repositories; their parser version integration remains root-owned and requires dependency integration, not a stacked PR.

# Draft PR
Title: Preserve URI schemes when extracting archive links

Body:
The URI classifier treated mailto, tel and urn references as relative archive paths because it required ://. Classify hrefs by scheme and authority so external references retain their original targets and percent encoding while relative archive links keep their existing resolution.

Retains the actual NVDA mailto anchor as a regression fixture. Focused TDD: tests/test_uri_schemes.py failed5/passed4 before the fix and passed9 after it. Library version is0.15; the lock's editable-package metadata matches. Full suite awaits PR CI. Refs #1. Downstream parser-version integration is handled separately after this library change integrates.
