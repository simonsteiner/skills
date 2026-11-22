# Running a skill's evals

A skill can carry `evals/evals.json`: realistic prompts, the setup each needs, and the behaviour that counts as success. The lint checks the file; [`scripts/eval-skill.py`](../scripts/eval-skill.py) runs the mechanical half of the [agentskills.io eval loop](https://agentskills.io/skill-creation/evaluating-skills). The runs and the grading are agent work, because each run needs a fresh context.

## One iteration

1. **Prepare.** `scripts/eval-skill.py prepare <skill> --baseline main` lays out `.eval-workspace/<skill>/iteration-<N>/` (gitignored) and prints one JSON line per run. Every eval runs twice: `with_skill` (the working tree) and `old_skill` (the skill as it was at the ref). Without `--baseline` the second run is `without_skill`.
2. **Run.** For every line, spawn a fresh sub-agent with its `task` file as the prompt. It builds the setup in a throwaway directory, does the task, and writes `outputs/reply.md` and `timing.json`. Record `total_tokens` and `duration_ms` from the sub-agent's completion as soon as it finishes; they aren't kept anywhere else.
3. **Grade.** For every line, spawn another fresh sub-agent with its `grade` file. It writes `grading.json` with PASS or FAIL and evidence per expected behaviour. Don't let the agent that ran a case grade it.
4. **Benchmark.** `scripts/eval-skill.py benchmark .eval-workspace/<skill>/iteration-<N>` writes `benchmark.json`: pass rate, time and tokens per configuration, and the delta the skill buys. It refuses while any run is ungraded.
5. **Read the runs, not just the numbers.** A behaviour that passes in both configurations tests nothing; one that fails in both is a broken case. Read the transcripts of the slow or failing runs, change the skill, and run the next iteration.

## Trigger evals

`evals.json` tests what a skill does once it's loaded. Whether it loads at all is up to its `description`, which the harness shows the model beside every other skill's. A model-invoked skill can carry `evals/triggers.json` for that:

```json
{"skills": ["pr-body"], "triggers": [
  {"query": "open a PR", "should_trigger": true},
  {"query": "review PR 41", "should_trigger": false}
]}
```

Give it prompts that should load the skill, including ones that only imply it ("fix it and push" implies a commit), and near misses that shouldn't: a neighbour's prompts, or ones that share the skill's words but not its job. Copy a neighbour's prompt word for word and the two files share it; the run merges labels by prompt, so each copy is routed once. The lint requires both kinds and refuses the file on a user-invoked skill, whose description never reaches the model.

1. **Prepare.** `uv run --locked --no-build python3 scripts/eval-skill.py triggers --baseline <ref> --also ~/.claude/skills` lays out `.eval-workspace/_triggers/iteration-<N>/` from every skill's `triggers.json` and prints one JSON line per router task. `with_skill` routes against the descriptions in the working tree, `old_skill` against those at the ref. `--also` adds the installed skills that aren't owned here (curated ones, plugins) to both catalogues, so the neighbours a real session has compete too. The prompts are shuffled once and batched the same way for both configs, so the difference is the descriptions'.
2. **Route.** For every line, spawn a fresh sub-agent with its `task` file as the prompt. It sees the catalogue (names and descriptions only) and the batch's prompts, never the labels, and writes `answers.json`: the skills it would load for each prompt.
3. **Score.** `scripts/eval-skill.py triggers-score .eval-workspace/_triggers/iteration-<N>` writes `trigger-benchmark.json`: per config, the pass rate, each skill's should-trigger and should-not-trigger counts, and every miss with what loaded instead; then the delta. A skill missing from a config's catalogue (added since the ref, or user-invoked there) is listed under `absent`, so its misses read as such.

A router reads every description side by side at the start of a turn, with nothing else on its mind. That measures whether the descriptions tell skills apart. It doesn't measure how often a busy agent mid-task skips a skill it should have loaded, which takes running the real harness and watching its Skill tool calls.

## Cost

Subagents run on the session's model and effort unless told otherwise. Spawn each one on the `model` its task line names, and leave out `--baseline` when no description changed.

| Role | Model | Why |
|---|---|---|
| Router | `haiku` | it matched Opus on the trigger prompts, missing only ones Sonnet or Opus missed too |
| Executor | the session's model | it should behave like real sessions |
| Grader | not measured yet | |

## Setups that need GitHub

The executor builds its setup locally and never touches a real GitHub repo. A setup that needs open PRs, reviews or threads (most of `review-prs`' evals) can't be built that way yet, so those runs grade as failures in both configurations. Read them as untested, not as regressions, until there's a sandbox repo to run them against.
