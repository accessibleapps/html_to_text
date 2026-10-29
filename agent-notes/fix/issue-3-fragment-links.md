# Goal
Resolve issue3: retain the current document filename for fragment-only archive links, using the existing href/ID contract.

# State
Independent branch fix/issue-3-fragment-links from freshly fetched origin/master. Raw anchor and target retained from Rust sample/all.html. Focused regression before source fix:5 failed,3 passed; after completed fix:8 passed. Source now resolves URI references against the complete document filename and retains archive percent decoding. Package0.15 and matching root lock metadata; existing CI runner pinned to Ubuntu24.04 with unchanged Python3.8-3.12 matrix. Root publishes; Q reviews and merges.

# Decisions and why
The existing resolver joins the complete href to dirname(file), losing the filename for empty-path references and treating query/fragment text as path content. Standard urljoin with the full file as base supplies the needed behavior; unquote retains current archive percent decoding. Removed now-unused posixpath import. No new resolver layer and no dependency on other open PRs. External-scheme classification itself remains unchanged; URL resolution inherently recognizes schemes but this branch does not claim issue1's external percent-encoding preservation.

# Surprises
The original sample is minified, but lxml confirms the exact source anchor href #primitives and target h3 id primitives. No copyrighted prose is included beyond these labels.

# Next step
Implementation and focused tests are committed locally. Root inspects and publishes the independent PR, then follows CI. No push, PR, review, merge or release performed by this worker.

# TDD evidence
Own isolated Python3.12 environment initialized with uv sync --frozen --all-groups. Command .venv/Scripts/python.exe -B -m pytest tests/test_fragment_links.py -q: before source edits5 failed/3 passed; after source edits8 passed. Real anchor href becomes docs/all.html#primitives and equals the emitted target ID. Focused controls cover decoded archive filenames/fragments, empty href, query-only references, base-query inheritance and existing relative/absolute archive paths. No complete CI suite, static checks or build was run locally.

# PR draft
Title: Resolve fragment links against their current document

Body: Resolve archive-relative URI references against the complete document filename instead of its directory. Fragment-only links now match emitted ID names, and empty-path query references retain the current document. Archive percent decoding remains. Library version0.15 and matching lock metadata; CI retains its complete matrix on a supported Ubuntu24.04 runner.

Closes #3.

TDD: tests/test_fragment_links.py initially failed5/passed3 and now passes all8 cases, including the retained actual Rust documentation anchor and target. Full suite awaits PR CI. Independent branch from master; no inherited open PR commits. Downstream parser-version integration remains root-owned after library integration.
