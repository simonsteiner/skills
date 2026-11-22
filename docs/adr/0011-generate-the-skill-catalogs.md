# The skill catalogs are generated from the skills and the curated manifest

## Context

Four files listed skills by hand: the top-level `README.md`, each bucket `README.md`, `.claude-plugin/plugin.json` and `third-party/README.md`. They worded each skill differently from each other and from its `description`. The lint checked that every skill had an entry under the right heading, but it couldn't check that an entry still said what the skill does, so the wording drifted.

## Decision

- **`scripts/build-catalog.py` renders every list** between `skill-catalog` markers (format in `scripts/tooling/catalog.py`). The pre-commit hook runs it and stages what it rewrote, and the lint fails on a stale catalog. Prose outside the markers stays hand-written.
- **An owned skill's entry is its `description`**: whole for a user-invoked skill, whose description is already a human summary, and up to the first sentence starting "Use" for a model-invoked one, so its trigger phrasing stays out. The lint requires that summary. A separate summary field was rejected: it would be a second blurb to drift, and owned skills carry no `metadata`.
- **A curated skill's entry comes from `skills.json`**: the first sentence of its `why`, under its source's `why` and its `invocation` group, with archived skills and their full reasons collapsed below.
- **`skills.json` records each curated skill's `invocation`** (`"model"` or `"user"`), since the installed copy isn't there in CI to read it from. The lint requires it and uses it to refuse a Skill tool call to a user-invoked curated skill, as it does for owned ones; `sync-third-party.py --check` fails with `invocation` when an installed copy's `disable-model-invocation` disagrees, which is how an upstream flip shows up.

## Consequences

- Adding, moving, renaming or re-describing a skill is one edit plus a rebuild. The old per-entry lint checks (link text, heading, duplicates) are gone, because the generator can't get those wrong.
- Catalog wording is now description wording: third person, and longer than the hand-written lines were.
- A `skills.json` reason should open with a sentence that works on its own as the skill's catalog line.
- `invocation` is one more field to keep true by hand; `--check` catches it drifting only on a machine where the skill is installed.
