# Mining real sessions

Evals use invented prompts. Session transcripts show what really happens: which skills load, whether by slash command or by the model, how people actually word their requests, and what they push back on right after a skill has acted. Look at the history before writing synthetic evals or changing a description.

## What a run measures

- **Loads per skill:** split by slash command and model invocation. This is how we found that pr-body and conventional-commit are only ever loaded by the model, while review-prs is mostly `/review-prs`.
- **Corrections:** each load is paired with the next message from the human in that session. The message counts as a correction if it pushes back on, undoes or redirects what the agent just did under that skill. Corrections are grouped into themes per skill.

## Running it again

Spawn one subagent on `sonnet` (default effort) with the brief below. The 2026-11-22 run took about 117k tokens and 4 minutes. The transcripts are private: the extracted data stays in the subagent's scratchpad, and only the aggregate counts and paraphrased themes go into this repo, which is public.

```text
Goal: per skill, count loads and the corrections the user makes right after a load.
Read-only; everything you write goes in your scratchpad.

Skills: the repo's own under skills/ plus every entry in third-party/skills.json
(mark archived ones).

Sources: ~/.claude/projects/**/*.jsonl, skipping subagents/ dirs and eval-workspace
sessions (cwd or project contains eval-workspace, or the first message is a
"Read <path>/task.md and do exactly what it says" router or executor task); and
~/.codex/sessions/**/*.jsonl (inspect the format first).

1. Write a Python script in your scratchpad and run it with `python3 -I`:
   - loads: assistant Skill tool calls ("name":"Skill", input.skill, strip a
     plugin: prefix) and "Base directory for this skill: <path>/<name>" lines;
     a load preceded by a <command-name> message is a slash load. A "Base
     directory" line right after a "Launching skill:" tool result is a model
     load, however far back its Skill call was. Dedupe by session plus position.
   - pair each load with the next real human message, skipping tool results,
     system reminders, command output, hook output, compaction summaries, task
     notifications and agent-relayed messages. Keep ~400 chars of it.
   - write the pairs to JSONL.
2. Classify each next message as correction or not, then group the corrections
   by theme per skill.
3. Reply in under 60 lines: per skill, loads (slash/model), loads with a next
   message, clear and borderline corrections, and the top themes with 1-2 short
   quotes. Add the method caveats.
```

Compare the result with the previous run below. A theme that comes back after the change meant to fix it is the signal worth acting on.

## Caveats

- A long session often loads several skills before the human writes again, so one message counts toward each of them. Treat the rates as rough.
- The next message can come hours of agent work after the load. It shows how the human reacted to the whole turn, not only to the skill.
- The classifier only sees the human's text, never what the agent did, so some borderline corrections may just be questions.

## Run of 2026-11-22

The run covered 1,075 Claude Code sessions (about 2,160 subagent and eval paths skipped) and 40 Codex sessions. About 1,100 loads were followed by a human message, and about 14 of those messages were clear corrections. The table counts Claude Code loads only.

| Skill | Loads (slash / model) | With a next message | Clear | Borderline |
|---|---|---|---|---|
| conventional-commit | 473 (0 / 473) | 301 | 1 | 2 |
| address-review-findings | 428 (19 / 409) | 201 | 2 | 6 |
| review-prs | 424 (411 / 13) | 190 | 3 | 4 |
| pr-body | 292 (0 / 292) | 205 | 3 | 4 |
| domain-modeling (curated) | 27 (3 / 24) | 27 | 3 | 0 |
| sync-and-branch | 20 (0 / 20) | 16 | 0 | 0 |
| frontend-craft | 15 (6 / 9) | 12 | 2 | 0 |

Every other skill had no corrections. Codex added 103 loads, mostly codebase-design, conventional-commit and diagnosing-bugs, with no corrections; its user-invoked loads were sync-and-branch (4), address-review-findings (2) and one archived curated skill.

Themes, and what has happened to each since:

| Theme | Skill | Status |
|---|---|---|
| A review left a delegate's worktree behind | review-prs | Fixed 2026-11-22: review-prs removes delegate worktrees itself |
| PR opened against the default branch instead of the feature branch it belonged to | pr-body | Covered 2026-11-20: sync-and-branch takes "with target feat/x" and says the PR targets it. pr-body still doesn't pass `--base` itself |
| No changelog entry for a change in this repo | conventional-commit, pr-body | Covered by the changeset rule in AGENTS.md |
| The installed copy of a skill was older than the repo's | review-prs | A sync problem, not the skill's text |
| PR description went stale after other PRs merged into the feature branch | pr-body | A single case; the description already covers updating a body |
| A review missed one PR, or one commit of a PR | review-prs | Single cases, partly borderline |

There were no complaints about hard-wrapped commit bodies, draft PRs or wrong titles.

**Next run:** a few weeks after 2026-11-22. Check whether worktree leftovers and wrong PR targets come back.
