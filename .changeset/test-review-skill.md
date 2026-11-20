---
"simonsteiner-skills": minor
---

New user-invoked skill `test-review`: an arch-review for a project's tests. It measures how the tests run (suite and single-file time, CI reruns, disabled tests, coverage when the project has it), reads the git history with a bundled `scripts/test-history.py` for hot code whose tests never move, fix commits that added no regression test, and tests that refactor commits had to change, then scans three lenses: blind spots, waste, and test infrastructure. It saves a ranked report with a status table to `docs/test-review/`, and after you confirm the batch (which also agrees the seams `tdd` needs), it ships one stacked PR per candidate: blind spots through `tdd`, with every new test seen failing, and waste through `prune-tests`, with before/after timings. Behaviour with no seam to test at is handed off to `/arch-review`.
