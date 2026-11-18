# Own test-review as its own skill beside arch-review

## Context

The ask was a skill that reviews a project's test setup, finds blind spots and wasted effort, and works with `tdd` and `prune-tests`, both curated and model-invoked. `arch-review` ([ADR 0004](./0004-own-arch-review-instead-of-curating-two-review-skills.md)) already has the loop wanted: scan with lens sub-agents, a dated report folder whose status table is the backlog, one checkpoint, one stacked PR per candidate, a loose-ends audit. Its deepening lens even asks "what is untested, or hard to test through its current interface?".

Three ways to get a test review:

1. **A fourth lens in arch-review.** Reuses everything. But arch-review's candidates are structural fixes phrased as module changes, designed in a Design phase and built as refactors; a test candidate is fixed by writing tests through `tdd` or deleting them through `prune-tests`, and it needs evidence arch-review never gathers (suite timings, CI reruns, fix commits without a test). arch-review's `SKILL.md` is already 15.7 KB of a 20 KB body budget.
2. **A test-review skill that calls arch-review's pieces.** arch-review is user-invoked, so no skill can reach it through the Skill tool ([docs/invocation.md](../invocation.md)), and skills don't link into each other's folders. Its templates and `co-change.py` aren't reachable from another skill, and a user can install either skill alone.
3. **An owned test-review with its own copy of the shape.**

## Decision

**Option 3: own `test-review` in `skills/engineering/`, user-invoked, with the same workflow shape as arch-review and its own report, lenses, and script.**

- **User-invoked.** A run opens a stack of PRs and spends a usage window; the model shouldn't reach for it on "clean up the tests" (that's `prune-tests`' job). Being user-invoked, it may call the model-invoked `tdd`, `prune-tests`, `codebase-design`, `setup-lefthook`, `secure-github-actions`, `diagnosing-bugs`, `review-prs`, `conventional-commit` and `pr-body`.
- **Three lenses**, each mapped to a fix route: blind spots → `tdd`, waste → `prune-tests` (its categories are the lens's first bullet), infrastructure → a direct change. A blind spot with no seam to test at is a hand-off: the report tells the user to run `/arch-review`, since this skill can't call it and module design is that skill's job.
- **The checkpoint confirms seams too.** `tdd` refuses to write a test at a seam the user hasn't agreed. Each blind-spot card names its seams with what they catch and miss, and Step 5's batch confirmation is that agreement, so the run stays hands-off afterwards.
- **No Design phase for blind spots and waste.** The judgement (which seam, which tests to prune) is made at scan time by the strongest model and confirmed by the user; Build follows the card. Only `infra` rows, where the change itself is open, get a Design phase.
- **Prove each new test can fail.** `tdd` assumes red before green, but a test pinning existing behaviour passes at once. Build breaks the behaviour on purpose, sees red, reverts, and records the mutation; a test red against unchanged code is a live defect fixed in the same PR.
- **A new bundled script, `test-history.py`, not a test mode in `co-change.py`.** The questions differ (does a source file's own test move with it; which fix commits added no test; which tests do refactor commits touch), and option 2's reasons rule out sharing the file.
- **Coverage is evidence, never a target**, and used only when the project or its SonarQube project already produces it.

## Consequences

- **Two skills now carry the report-and-stack workflow.** A change to that shape in one (the status values, the reconcile step, the loose-ends audit) should be considered for the other. If a third skill wants it, extract the shape into a model-invoked skill both can call.
- **The scope line with arch-review is "is there a seam?"**: test-review writes and prunes tests where a seam exists, arch-review creates the seam. Running both on one repo at once stacks PRs on the same code; the skill says not to.
- **`test-history.py`'s test/source pairing is a name heuristic** (`test_x.py`, `x.test.ts`, `XTest.java`, `index` → folder name). Repos with other layouts pass `--test-pattern`; the skill tells the agent to check pairings before citing them.
