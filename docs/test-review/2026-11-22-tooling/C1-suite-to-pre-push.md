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

**After:** <!-- filled at Ship -->

<details>
<summary>Decisions</summary>

<!-- one line each -->

</details>
