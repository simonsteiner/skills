# C3 · Pin `reply-resolve.sh` at its command

[← Report](README.md)

🕳️ blind spot · 🟢 **Strong** · ↔ `two-way` · fix: `tdd` · builds on: none

`skills/engineering/address-review-findings/scripts/reply-resolve.sh:17-52` · `tests/skill_scripts/test_gh_host.py:20`

The only one of 17 bundled scripts with no test module of its own (AGENTS.md: "Each bundled script is tested from `tests/skill_scripts/` against the fake `gh`"); 5 commits in 6 months, and the one test that runs it (`test_gh_host.py:20`) checks only which host its first `gh` call goes to.

**Seams** (confirmed at Step 5):

| Seam | Catches | Misses |
|---|---|---|
| `reply-resolve.sh <thread-id> [--resolve]` with the body on stdin, against the fake `gh` (`tests/skill_scripts/fake_gh.py`) | argument and body guards, which mutations are sent and in what order, the output, the failed-resolve error | whether GitHub's GraphQL accepts the mutations |

**Pin:**

| Behaviour | Where | Evidence |
|---|---|---|
| an empty or whitespace-only body exits 1 and sends nothing: a resolve without a reply is never allowed | `reply-resolve.sh:27-28` | the script's central rule, never driven |
| a thread id not starting `PRRT_` exits 1 and sends nothing | `reply-resolve.sh:24` | never driven |
| a second argument other than `--resolve` exits 1 and sends nothing | `reply-resolve.sh:25` | never driven |
| without `--resolve`: one reply mutation carrying the body, the reply URL printed, no resolve mutation | `reply-resolve.sh:41-46` | never asserted |
| with `--resolve`: the reply mutation first, then the resolve, and `resolved` printed | `reply-resolve.sh:48-52` | never asserted |
| a thread that comes back unresolved fails with "thread did not resolve" | `reply-resolve.sh:52` | never driven |

| Problem | Fix | Wins |
|---|---|---|
| The script that writes to reviewers' threads, and refuses a silent resolve, has none of its own rules under test. | A `test_reply_resolve.py` against the fake `gh`, like every other bundled script. | silent resolve fails CI<br>convention holds for all scripts |

**After:** 6 tests added in `tests/skill_scripts/test_reply_resolve.py` (0.15 s), one per Pin row, at the card's seam. All six went red under a named mutation (listed in `25eee59`): empty-body guard deleted, `PRRT_` check loosened, option check deleted, `--resolve` condition forced true, condition compared to `--nope`, `error(...)` replaced with `"resolved"`. No live defect; script untouched. Suite 369 -> 375 tests, 19.0 s. Departure: the unresolved-thread test asserts the failure, not the message (see the overview's Departures).

<details>
<summary>Decisions</summary>

<!-- one line each -->

</details>
