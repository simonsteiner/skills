# Owned skills grow past `conventional-commit`, and `mattpocock/skills` is tracked through curation

Supersedes the "pare down to a single skill" and "no sync" parts of [ADR 0001](./0001-fork-and-pare-down-to-conventional-commit.md).

## Context

ADR 0001 pared the fork down to one owned skill, `conventional-commit`, and cut every tie to `mattpocock/skills`: no `upstream` remote, nothing pulled. Both halves have since moved.

- Thirteen skills are owned now (`.claude-plugin/plugin.json`). Each came in either as a workflow nobody upstream ships (`address-review-findings`, `sync-and-branch`, `setup-lefthook`, …) or by taking over a curated skill that couldn't be bent to the workflow from outside ([ADR 0004](./0004-own-arch-review-instead-of-curating-two-review-skills.md), [0005](./0005-own-review-prs-instead-of-curating-code-review.md), [0007](./0007-own-frontend-craft-instead-of-curating-two-design-skills.md), [0008](./0008-own-test-review-beside-arch-review.md)).
- Seven `mattpocock/skills` skills are installed again (`codebase-design`, `diagnosing-bugs`, `domain-modeling`, `grilling`, `research`, `tdd`, `wizard`), from upstream at its latest, through `third-party/skills.json` ([ADR 0002](./0002-curate-third-party-skills-instead-of-vendoring.md)).

## Decision

- **Owned skills are added when curation can't reach the workflow**: a workflow no curated skill covers, or one that would need an upstream skill changed rather than called (ADR 0004's bar). There's no target size.
- **Upstream reaches this repo only through the curated manifest.** Still no `upstream` remote and no merges: an upstream skill worth having is curated and installed from its own repo, and an owned skill adapted from one credits it in `CREDITS.md` and is re-read by hand.

## Consequences

- ADR 0001's structure stays: the bucket taxonomy, the hard fork, the fresh changelog.
- Its consequence "upgrades from upstream are manual" now holds only for owned skills adapted from upstream. Curated skills upgrade on every sync, unpinned.
- An owned skill and a curated one must never share a name; `scripts/tooling/skill_inventory.py` fails the lint when they do.
