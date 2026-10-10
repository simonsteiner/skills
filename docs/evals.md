# Running a skill's evals

A skill can carry `evals/evals.json`: realistic prompts, the setup each needs, and the behaviour that counts as success. The lint checks the file; [`scripts/eval-skill.py`](../scripts/eval-skill.py) runs the mechanical half of the [agentskills.io eval loop](https://agentskills.io/skill-creation/evaluating-skills). The runs and the grading are agent work, because each run needs a fresh context.

## One iteration

1. **Prepare.** `scripts/eval-skill.py prepare <skill> --baseline main` lays out `.eval-workspace/<skill>/iteration-<N>/` (gitignored) and prints one JSON line per run. Every eval runs twice: `with_skill` (the working tree) and `old_skill` (the skill as it was at the ref). Without `--baseline` the second run is `without_skill`.
2. **Run.** For every line, spawn a fresh sub-agent with its `task` file as the prompt. It builds the setup in a throwaway directory, does the task, and writes `outputs/reply.md` and `timing.json`. Record `total_tokens` and `duration_ms` from the sub-agent's completion as soon as it finishes; they aren't kept anywhere else.
3. **Grade.** For every line, spawn another fresh sub-agent with its `grade` file. It writes `grading.json` with PASS or FAIL and evidence per expected behaviour. Don't let the agent that ran a case grade it.
4. **Benchmark.** `scripts/eval-skill.py benchmark .eval-workspace/<skill>/iteration-<N>` writes `benchmark.json`: pass rate, time and tokens per configuration, and the delta the skill buys. It refuses while any run is ungraded.
5. **Read the runs, not just the numbers.** A behaviour that passes in both configurations tests nothing; one that fails in both is a broken case. Read the transcripts of the slow or failing runs, change the skill, and run the next iteration.

## Setups that need GitHub

The executor builds its setup locally and never touches a real GitHub repo. A setup that needs open PRs, reviews or threads (most of `review-prs`' evals) can't be built that way yet, so those runs grade as failures in both configurations. Read them as untested, not as regressions, until there's a sandbox repo to run them against.
