# Own arch-review instead of curating two review skills

## Context

[ADR 0002](./0002-curate-third-party-skills-instead-of-vendoring.md) made curation the rule for other people's skills: list them, install them from upstream, own nothing. Two curated skills covered architecture review:

- `improve-codebase-architecture` (mattpocock/skills) scans for deepening opportunities, writes an HTML report to the OS temp dir, asks which candidate to explore, and grills the user through it. It never writes to the repo and never implements.
- `thermo-nuclear-code-quality-review` (cursor/plugins) is a harsh maintainability rubric for a branch's diff — spaghetti conditionals, one-off flags, casts hiding invariants, files past 1,000 lines — with an approval bar and no output beyond the review.

Chat history showed a different loop from either. About 49 requests read like "save the archreview to docs and implement the strongest candidates one by one"; grilling was asked to answer itself with its recommendations; "any loose ends from the arch review?" followed 8 times because the run stopped early; and a saved report doubled as a backlog across sessions and agents ("pick next archreview candidate"). The thermo review was used once, repo-wide rather than on a diff — and the reports written by hand already mixed its kind of finding with deepening candidates.

Neither skill can be bent into that loop from outside. Upstream's skill is user-invoked, so no other skill can call it; its report deliberately stays out of the repo; and the `grilling` skill it relies on is built to wait for the user's answers.

## Decision

**Own an `arch-review` skill, and archive both curated ones.**

- `arch-review` is user-invoked. It adapts improve-codebase-architecture's scan questions, scoping, candidate format, and strength scale, and folds thermo-nuclear's rubric in as a second lens and a per-PR approval bar — both rewritten into `codebase-design`'s vocabulary. Both upstreams are MIT; `CREDITS.md` carries the notices.
- What it adds: the report lives in the repo — upstream's visual HTML report, now in `docs/arch-review/` and built from a fixed scaffold, beside a Markdown ledger that holds the status table and decisions. It lands as its own PR, and the confirmed batch ships as one stacked PR per candidate, with decisions answered from the recommended option and recorded beside their evidence, and a loose-ends audit before reporting.
- The user confirms the batch once — every `Strong` candidate by default — and that is the run's only checkpoint short of a one-way door.
- It reaches `codebase-design`, `domain-modeling`, and `code-review` (still curated) and this repo's `conventional-commit` and `sync-and-branch` through the Skill tool. It doesn't call `grilling`; it runs the method inline without waiting.
- The two curated entries move to an `archived` list in `skills.json` rather than disappearing, so the reason survives. The sync skips them, and `--check` reports any copy still installed.

## Consequences

- **This repo now maintains the adapted parts.** Upstream improvements to improve-codebase-architecture's scan won't arrive by sync. Its recent history was mostly conventions; the one substantive change (scope to churn hot spots) is already in. Re-read upstream when re-syncing the rest of mattpocock/skills.
- **Two files per scan.** The HTML report is the dated record and isn't edited afterwards; everything that changes — status, decisions, departures — lives in the Markdown ledger, which agents edit and git diffs cleanly. GitHub shows HTML as source, so the report is read locally; the ledger is what renders on GitHub.
- **Curation stays the default.** This is the first skill taken from curated to owned, and the bar is the one this case met: the workflow needed couldn't be reached by calling the upstream skill, only by changing it.
