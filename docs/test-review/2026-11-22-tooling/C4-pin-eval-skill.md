# C4 · Pin `eval-skill.py`'s command

[← Report](README.md)

🕳️ blind spot · 🟡 **Worth exploring** · ↔ `two-way` · fix: `tdd` · builds on: none

`scripts/eval-skill.py:44-103` · `tests/tooling/test_evals.py`

6 commits in 6 months and no test runs the command (`grep -rn eval-skill tests` is empty); fix `4ad71e5` added the `"timing"` key to `prepare`'s JSON lines (`eval-skill.py:99-100`) with no test. `tests/tooling/test_evals.py` (8 tests) reaches `evals.prepare` and `evals.benchmark` as functions.

**Seams** (confirmed at Step 5):

| Seam | Catches | Misses |
|---|---|---|
| `scripts/eval-skill.py <subcommand> …` run as a command | usage and exit codes, the unknown-skill error, `benchmark`'s printed JSON | `prepare`'s JSON line for a real skill: it writes into the repo's `.eval-workspace/` (`REPO` is fixed, `scripts/tooling/skill_inventory.py:20`), so the `"timing"` key stays unpinned without a seam for the workspace root |

**Pin:**

| Behaviour | Where | Evidence |
|---|---|---|
| no arguments prints usage to stderr and exits 2; `-h` prints the docstring and exits 0 | `scripts/eval-skill.py:45-47` | never driven |
| an invalid call (`prepare a b`, `triggers --also`, two `--baseline`) prints usage and exits 2 | `scripts/eval-skill.py:53-55`, `:61-79` | never driven |
| `prepare <unknown skill>` exits 1, lists the known skills, and writes nothing | `scripts/eval-skill.py:94-96` | never driven |
| `benchmark <dir>` prints the benchmark as JSON and exits 0; a `ValueError` from it exits 1 | `scripts/eval-skill.py:49-52`, `:65-68` | never driven through the command |

| Problem | Fix | Wins |
|---|---|---|
| The eval command's parsing and error paths change with nothing to catch a regression. | Pin them at the command; leave `prepare`'s line until the workspace root has a seam. | bad-usage regression fails CI |

**After:** <!-- filled at Ship -->

<details>
<summary>Decisions</summary>

<!-- one line each -->

</details>
