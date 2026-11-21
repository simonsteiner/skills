---
"simonsteiner-skills": minor
---

New user-invoked skill `test-review`, an arch-review for a project's tests. It measures how the tests run: suite and single-file time, CI reruns, disabled tests, and coverage from the sonar-coverage skill, the SonarQube MCP tools or the project's own report (Vitals says when there is none). A bundled `scripts/test-history.py` reads the git history for hot code whose tests never move, fix commits that added no regression test, and tests that refactor commits had to change. The skill then scans three lenses: blind spots, waste and test infrastructure. A test that mocks internals counts as waste to rewrite when a seam exists, and goes to `/arch-review` when it doesn't.

It saves a ranked report with a status table to `docs/test-review/`. Once you confirm the batch, which also agrees the seams `tdd` will need, it ships one stacked PR per candidate. Blind spots go through `tdd`, and every new test is seen failing. Waste goes through `prune-tests`, keeping only the deletions the card listed, with timings before and after. `/test-review next` goes straight to building when the batch is already confirmed.
