# C1 · Take the 19 s suite off pre-commit

[← Report](README.md)

🔧 infra · 🟢 **Strong** · ↔ `two-way` · fix: `direct` · builds on: none

`lefthook.yml:18-21` · `.github/workflows/lint.yml:28-30` · `skills/engineering/setup-lefthook/SKILL.md:40`

The `tests` job runs all 356 tests (18.8 s, serial) on every commit that stages a `.py` or `skills/**` file; setup-lefthook, this repo's own skill, puts a suite over ~10 s on pre-push, and there is no pre-push hook.

**Now:** pre-commit runs `unittest discover` whole beside six sub-second jobs (`lint-skills.py` 0.11 s, ruff 0.16 s warm), so the hook's wall time is the suite's, ~19 s. CI runs the same suite on every push and PR (median 29 s for the whole Lint job, 0 reruns in 164 runs). The time is subprocess spawning in `tests/skill_scripts/` (~18 s across 18 modules; `test_post_review` 3.0 s, `test_test_history` 2.9 s); `tests/tooling/` is ~0.5 s.

**Change:** the Design phase picks one: move the `tests` job to a new `pre-push` section (setup-lefthook's rule, no dependency), or keep it on pre-commit but fan the modules out in parallel (the slowest module is 3.0 s; `xargs -P` over `unittest tests.<module>` needs no dependency, `pytest-xdist` would add one to `uv.lock`). Update `docs/setup.md`'s hook section and the job's comment to match.

**Measure:** pre-commit wall time with a staged `.py` file, now ~19 s, from `time npx lefthook run pre-commit` after staging a touched `scripts/tooling/catalog.py`; target under 3 s. Suite wall time stays 18.8 s unless the parallel option is chosen.

| Problem | Fix | Wins |
|---|---|---|
| Every commit, including every commit an agent makes in a `tdd` loop, waits ~19 s for a suite CI runs again anyway. | Run the suite once per push, or in parallel, as setup-lefthook prescribes. | −16 s per commit<br>repo follows its own hook rule |

**After:** the `tests` job moved unchanged to a new `pre-push` section (`349b523`); pre-commit with a touched `scripts/tooling/catalog.py` staged takes 0.41 s, down from 19.07 s (the tests job was 18.85 s of it; target under 3 s). `npx lefthook run pre-push` on a docs-only range skips the suite ("no matching push files") and on a range with a `.py` file runs it in 18.84 s. The suite is unchanged at 356 tests, 18.5 s. S1 (`skills` added to CI's ruff paths and `AGENTS.md`, `a5b01d5`), S2 (single-test command in `AGENTS.md`, `a5b01d5`) and S3 (`skipUnless(uv)` and the `shutil` import dropped, `5fa459f`) rode along. No tests added; the one skip is gone. Found while building, not fixed: lefthook 2.2.1 takes pre-push files from `git diff HEAD @{push}` (fallback `origin/main...HEAD`), not the pushed refs; a push touching only `lefthook.yml` skips the suite because the glob (moved unchanged) doesn't list it; existing clones need `npx lefthook install` once (or `npm install`, whose `prepare` runs it) to get the pre-push hook.

<details>
<summary>Decisions</summary>

<!-- one line each -->

- Q1: move the `tests` job to a new `pre-push` section or fan it out in parallel on pre-commit → move it to `pre-push` unchanged (same `run`, same glob), because setup-lefthook's own rule (`SKILL.md:40`, "a test suite over ~10 seconds runs in `pre-push`") applies at 18.8 s serial, and a parallel fan-out is floored by `test_post_review` at 3.0 s plus `uv` start-up, so it could not meet the under-3 s target and would split the suite's one interface (`unittest discover`) into a per-module list to keep current.
- Q2: does the `lint-skills` job stay on pre-commit → yes, unchanged, because it runs `build-catalog.py` and `lint-skills.py` only (no `unittest`; 0.29 s for both, measured), and it must stage the catalogs it rewrites, which only a pre-commit job can do.
- Q3: should pre-push run the suite only when the pushed range touches relevant files → yes, by keeping the job's `glob` and no `files`/`{push_files}` in `run`, because lefthook 2.2.1 (`package.json`) filters a pre-push job's glob against the pushed files and skips it when none match, so a docs-only push (like this card's) skips the 19 s; the Build phase confirms the skip with `npx lefthook run pre-push` on a docs-only range.
- Q4: how the hook seam gets installed → no step beyond the existing `prepare` script, because lefthook re-installs hooks when `.git/info/lefthook.checksum` no longer matches `lefthook.yml`; Build checks `.git/hooks/pre-push` exists after its first commit and runs `npx lefthook install` if not.
- Q5: what loses coverage → nothing CI gates on, because the Lint workflow already runs the same `unittest discover` on every push and PR (`lint.yml:28-30`, 0 failures in 164 runs); the hooks stay the early warning, now once per push.
- Q6: docs → rewrite the `tests` job's comment ("Same as CI, once per push: the suite is ~19 s, over setup-lefthook's ~10 s pre-commit budget") and `docs/setup.md:54` to say pre-commit runs the per-file checks and pre-push runs the suite when the pushed range touches Python, `tests/`, `skills/` or the lockfiles; the commands table is unchanged.
- Q7: Measure → pre-commit wall time from `time npx lefthook run pre-commit` with a touched `scripts/tooling/catalog.py` staged, now ~19 s, target under 3 s (remaining jobs: lint-skills 0.29 s, ruff 0.16 s warm, file-tokens and dashes sub-second, sonar skipped here as not logged in); plus `time npx lefthook run pre-push` on a range with a `.py` file at ~19 s and on a docs-only range skipped. Suite time stays 18.8 s.
- Q8: S1 → add `skills` to CI's Ruff step (`uvx --no-build ruff@0.17.0 check scripts tests skills`) and to the matching ruff command in `AGENTS.md:14` and `docs/setup.md`'s table, because `uvx ruff@0.17.0 check scripts tests skills` passes today ("All checks passed!"), so no code change rides along.
- Q9: S2 → add to AGENTS.md's Commands, after the one-module line, `uv run --locked --no-build python3 -m unittest tests.skill_scripts.test_post_review.PostReviewTest.test_summary_without_comments_posts  # run one test`, because that dotted name exists (`test_post_review.py:51,137`) and runs in 0.21 s, measured.
- Q10: S3 → drop `@unittest.skipUnless(shutil.which("uv"), …)` at `test_lint_skills.py:17` and the then-unused `import shutil` (line 7, its only other use), because every documented and CI run goes through `uv run`, so the skip can never fire and ruff would flag the orphaned import.
- Q11: door → stays two-way, because the change touches `lefthook.yml`, the Lint workflow's Ruff paths, one decorator and docs; no branch protection, required check name or fixture changes (the Lint job and its step names keep their names).
- Q12: this batch's own commits → this Decisions commit still pays nothing (a `.md`-only change matches neither glob), Build's commit that edits `lefthook.yml` runs under the new config because lefthook reads the working tree's `lefthook.yml`, and every later commit in C2 and C3 runs pre-commit under 3 s with the suite once per push.

</details>
