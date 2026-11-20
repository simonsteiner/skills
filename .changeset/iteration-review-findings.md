---
"simonsteiner-skills": patch
---

`/arch-review next` and `/test-review next` go straight to building when the batch is already confirmed, instead of asking again. arch-review's prune-tests call is limited to the tests of the internals a candidate replaces, it now uses a six-month churn window like co-change.py, and it warns against running beside a test-review on the same repo. `co-change.py` leaves out lockfiles, changelogs and `linguist-generated` paths by default, takes `--exclude <glob>`, and explains its columns in `--help`.

test-review scopes from `test-history.py drift` instead of a hand-rolled churn pipeline, reads coverage from a sonar-coverage skill, the SonarQube MCP tools or the project's report (and says so in Vitals when none is there), and settles tests that mock internals by the seam: waste to rewrite when a seam exists, a hand-off to arch-review when it doesn't. Batches of smaller findings get a branch name, and the skill credits caldoai's prune-tests.

review-doc calls rejecting a finding "disagree", like address-review-findings, puts the full diff in its report and then deletes the baseline and saved pages from `.scratch/`, and gains an eval for a finding that comes back after it was settled.
