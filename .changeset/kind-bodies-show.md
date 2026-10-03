---
"simonsteiner-skills": minor
---

Add `pr-body`, which replaces the curated `pr` skill (archived with its reason in `skills.json`). Across 46 PRs in six repos, `pr`'s single template forced a before/after onto features, gave one-line chores three sections, and left nowhere for stack notes, deploy steps, consumer notes or what's not done, so agents kept adding those by hand. `pr-body` keeps `pr`'s diagram views but picks the evidence by kind of change — before → after for a fix, a real run for a feature, unchanged output for a refactor, no template for a chore — folds checks into one line, and asks "what doesn't revert?" with a fixed blast-radius scale instead of one-way/two-way doors. `arch-review` now writes its PR bodies with it.
