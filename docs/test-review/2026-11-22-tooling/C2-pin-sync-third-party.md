# C2 · Pin `sync-third-party.py` and its GitHub adapter

[← Report](README.md)

🕳️ blind spot · 🟢 **Strong** · ↔ `two-way` · fix: `tdd` · builds on: none

`scripts/sync-third-party.py:53-127` · `scripts/tooling/third_party.py:334-391` · `tests/tooling/test_third_party.py`

8 commits in 6 months and no test runs the command (`grep -rn sync-third-party tests` is empty); 2 of them are fixes (`1682bb2` "name extra arguments", `bfe71f1` "use the gh login for --outdated") and neither added a test of what it fixed; `grep -rn 'GH_TOKEN\|github_folders' tests` is empty too.

**Seams** (confirmed at Step 5):

| Seam | Catches | Misses |
|---|---|---|
| `scripts/sync-third-party.py <args>` run as a command, `HOME` at a temp dir, the repo's real manifest | argument errors, the lock-file guards, `--list` output, exit codes `sync-skills.py:105,111` relies on | the install itself (`npx skills`, network); the no-agents refusal at `:76-80`, already pinned at lint (`tests/tooling/test_published_rules.py:141`) |
| `third_party.github_folders(repo)`, `urllib.request.urlopen` replaced at the network system boundary, the fake `gh` (`tests/skill_scripts/fake_gh.py`) first on `PATH` | which token is sent, the anonymous fallback, the incomplete-tree error | the real shape of GitHub's answer |

**Pin:**

| Behaviour | Where | Evidence |
|---|---|---|
| an unknown argument exits 2 and names it; two arguments exit 2 with "expected at most one argument" | `scripts/sync-third-party.py:58-61` | fix `1682bb2` changed the message, no test |
| `--check` with no skills.sh lock file exits 1 and says to run without `--check` | `scripts/sync-third-party.py:94-97` | never driven |
| `--outdated` with no lock file exits 1 | `scripts/sync-third-party.py:106-109` | never driven |
| `--list` exits 0 and prints one line per curated skill | `scripts/sync-third-party.py:81-83` | never driven through the command |
| the token is `GH_TOKEN`, else `GITHUB_TOKEN`, else the gh login, sent as `Authorization: Bearer` | `scripts/tooling/third_party.py:384-386` | fix `bfe71f1` added the gh-login fallback, no test |
| with `gh` missing or logged out, the call goes anonymous (no `Authorization` header) | `scripts/tooling/third_party.py:334-341` | never driven |
| a truncated tree, or an answer without `tree`, raises `ValueError` | `scripts/tooling/third_party.py:389-390` | never driven; `outdated` turns it into an `unknown` finding |

| Problem | Fix | Wins |
|---|---|---|
| The command `sync-skills.py` runs for every curated install, and the token logic behind `--outdated`, change with nothing to catch a regression. | Pin the command's guards with a temp `HOME`, and `github_folders` with the network faked. | broken `--check` exit fails CI<br>token regression fails CI |

**After:** 13 tests added in `tests/tooling/test_sync_third_party.py` (5 at the command, 8 at `github_folders`), 0.4 s, all green against unchanged code (no live defect). Each was proved red by a mutation, listed in `a111ecd`'s message; `test_returns_the_root_and_every_folder_sha` was mutated at Ship: dropping the `{"": data["sha"]}` root entry, and separately dropping the `type == "tree"` filter, each turned it red; both reverted, source diff empty. Suite 356 -> 369 tests. No Departures.

<details>
<summary>Decisions</summary>

<!-- one line each -->

</details>
