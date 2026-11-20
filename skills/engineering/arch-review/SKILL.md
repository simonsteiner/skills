---
name: arch-review
description: Scans the codebase for deepening, coupling, and maintainability candidates, saves a ranked Markdown report with diagrams and a status table to docs/arch-review/, then implements the batch you confirm — one stacked PR per candidate, decisions recorded, loose ends audited.
disable-model-invocation: true
---

# Arch Review

Find where the code fights its maintainers, write it down in the repo as a backlog, then work the backlog: one candidate, one branch, one PR, until the batch is done and audited.

**One checkpoint, then hands-off.** The user confirms the batch once (Step 4). After that every design question is decided with the recommended answer and written down; nothing else waits for the user except a one-way door (Step 6). The report is the state — any session, any agent, picks up from its status table.

**Budget.** A run is long, and its cost is turns × context: every turn re-reads everything the agent has loaded. So:

- **Tier the models.** Judgement — this session and the Design sub-agent — runs on the strongest model. Everything else — scanner, Build, and Ship sub-agents, and every nested sub-agent any of them spawns (design-it-twice's designers) — runs on the mid-tier model (`model: "sonnet"` in Claude Code). Say so in every brief, including that nested sub-agents inherit the rule.
- **Keep contexts small.** Every brief carries the [context rules](#context-rules). Prefer a fresh sub-agent over a long one.
- **One run at a time**, and not beside a `/test-review` run on the same repo: both stack PRs on the same code. Two arch-reviews in parallel multiply the burn rate; queue the next repo instead.

Call the Skill tool with "codebase-design" before anything else. Use its vocabulary exactly — module, interface, implementation, depth, seam, adapter, leverage, locality — in the report, the decisions, commits, and PR bodies.

**Pick the entry from what was asked:**

- `/arch-review [direction]` — new scan (Step 1) through the loose-ends audit (Step 8).
- `/arch-review next` — resume: Step 3's reconcile on the newest report with open rows, then Step 4 — or straight to Step 5 when the status table already holds a confirmed batch (an `in-progress` row): the user confirmed it once, so don't ask again.
- `/arch-review report` — Steps 1–3 only.

---

## Step 1 — Scope, then scan

- A direction from the user wins. Otherwise find the hot spots over the last six months, the same window `co-change.py` uses by default: `git log --since=6.months --name-only --format= | sort | uniq -c | sort -rn | head -40`. Deepening pays off only where change keeps landing — weight those paths first; widen only if churn is scattered.
- Read the domain glossary (`GLOSSARY.md`; a repo still on `CONTEXT.md` should rename it — say so in the report), the ADRs under `docs/adr/`, and the previous reports in `docs/arch-review/` (a folder each; older reports are single files). Don't re-suggest what an ADR or an earlier `dropped` row already settled, unless the friction is real enough to reopen it — then say which ADR and why.
- Find the project's token budget and the files over it in the scope, as [REPORT.md](REPORT.md) says under "Token budget". Each file over it gets a row (LENSES.md, "Size as a pointer").
- Gather the coupling evidence: `<skill-dir>/scripts/co-change.py [<scope>…]` ([scripts/co-change.py](scripts/co-change.py)) lists the file pairs that keep changing in the same commit, with how often one never changes without the other; lockfiles, changelogs and generated files are left out, and `--exclude <glob>` drops more noise (run `--help` for the columns). Hand the list to whichever sub-agent runs the coupling lens (Lens 3).
- Spawn mid-tier sub-agents to walk the scoped code with the three lenses in [LENSES.md](LENSES.md) — one per lens, or one per hot area in a large repo. Give each the scope, the vocabulary, its lens, and the [context rules](#context-rules); ask for evidence (file:line, counts, a failing input) behind every claim, and a findings list under 800 words — not file contents.
- Apply the deletion test to every suspected shallow module. Verify each sub-agent claim yourself before it becomes a candidate.

---

## Step 2 — Write the report

The report is a folder, `docs/arch-review/YYYY-MM-DD-<slug>/`, so no file in it outgrows the token budget an agent can read whole. Copy [assets/report-template.md](assets/report-template.md) to its `README.md` (status table, friction map, smaller findings, recommendation) and [assets/card-template.md](assets/card-template.md) to one `C<n>-<card-slug>.md` per candidate, with its before/after diagram; fill them in following [REPORT.md](REPORT.md). Check every file against the budget (`wc -c`, bytes / 4) before committing. Add the report to the top of `docs/arch-review/README.md` (create the index if it's missing).

- **Candidates** (`C1…`) are structural fixes from the deepening or coupling lens, one card each, with the fields REPORT.md lists under "Candidate card".
- **Smaller findings** (`S1…`) are local maintainability fixes from the second lens — two sentences each.

Rank: strength, then live defect, then churn, then dependency order (a candidate another one builds on goes first). Plan the branch name for every row now — the status table carries it, so a later session can find the work.

---

## Step 3 — Land the report as the backlog

- **New report:** cut `docs/arch-review-<slug>` from the fresh default branch (`git fetch origin && git switch --no-track -c docs/arch-review-<slug> origin/<default>`), then call the Skill tool with "conventional-commit" to commit the report and index. Push and open a PR. This is the base of the stack — merging it puts the backlog on the default branch for every later session.
- **Resume:** reconcile the report's status table (its `README.md`; an older single-file report stays one file, as REPORT.md's "Token budget" says) against reality first — `gh pr list --state all --head <branch>` for each open row, and `git branch -a`. Fix rows that lag (a merged PR still marked `pr-open`). The next base is the tip of the highest open branch in the stack, or the default branch if everything merged.

`/arch-review report` stops here and reports the PR.

---

## Step 4 — Confirm the batch

Propose the batch and **wait for the user's answer** — this is the run's one checkpoint:

- **Default: every `Strong` row still `todo`**, in rank order. List each as `ID — title — strength — door — planned branch`, and say up front that a `one-way` row will stop at Step 6 for the user's answer.
- Name what's left out (`Worth exploring`, `Speculative`) so the user can pull a row in.
- Say where the smaller findings go: with the candidate PR that touches the same module, or in final PRs of at most five `S` rows each, grouped by module.

The user can accept as is, add or drop rows, or reorder. Write the confirmed batch into the report's status table (`in-progress` for the first row), then go.

---

## Step 5 — Implement the batch

Per candidate, spawn **three sub-agents in sequence**, each with a fresh context — a single implementer's context grows past what the later phases need, and the review and PR turns then pay for all of it:

| Phase | Model | Brief file | Hands back |
|---|---|---|---|
| **Design** | strongest | [phases/design.md](phases/design.md) | Decisions committed to the report on the candidate branch, or the row `blocked` |
| **Build** | mid-tier | [phases/build.md](phases/build.md) | Branch committed with checks green, or what failed |
| **Ship** | mid-tier | [phases/ship.md](phases/ship.md) | PR number, base, row updated and pushed |

Each phase file is self-contained: its steps and the rules that phase needs. Brief each sub-agent with pointers, not copies: the path to its phase file (`<skill-dir>/phases/<phase>.md`), the report path, the candidate ID, the branch and its base, the [context rules](#context-rules), and the model rule for anything it spawns.

Run candidates in sequence; each branch stacks on the previous one. A batch of smaller findings is one candidate without a Design phase; its Build sub-agent cuts the branch. When the harness has no sub-agents, read each phase file yourself and do it inline, still finishing one candidate completely before starting the next.

Between phases, check the hand-back — Decisions in the report, checks green, PR open against the right base, row updated. A gap goes back to a fresh sub-agent of the same phase with the gap named; don't patch it from this session's context.

### Context rules

Put these in every brief:

- Read the overview's `README.md` and your candidate's card file (a batch of smaller findings: their `S` entries, in the overview or `smaller-findings.md`), nothing else in the report (in an older single-file report: `grep -n` the Status table and your candidate's heading, then read those ranges).
- Read files in ranges (`grep -n`, then `sed -n` or `Read` with offset/limit); never a whole test file or a whole module you aren't rewriting.
- Trim command output: `… 2>&1 | tail -40` for tests, lint, and typecheck; `git diff --stat` before any full diff.
- Don't re-read what you already hold; keep notes in the report or the commit, not in the conversation.

---

## Step 6 — Decide the design

The Design phase, [phases/design.md](phases/design.md): every design question answered with the recommended option and a fact, recorded as Decisions on the card. A one-way door stops the candidate (row `blocked`, question in Notes), not the run.

---

## Step 7 — Build, check, ship

The Build phase, [phases/build.md](phases/build.md), implements the Decisions and gets the checks green; the Ship phase, [phases/ship.md](phases/ship.md), holds the diff to the approval bar, runs the local review, updates the row, and opens the PR. Never merge.

---

## Step 8 — Loose ends, then report

Don't report until this audit comes back empty, or every gap it finds is fixed or has become a new row:

- Every batch row is `pr-open`, `merged`, `dropped`, or `blocked` — the last two with a reason in Notes.
- Every Solution bullet and every Decision is in a diff, and every symptom a card listed is gone or explained in a Departure. Departures are written up.
- No old shallow module, its tests, or its re-export survives beside the new one. `git grep` the old names and paths.
- No `TODO`, `FIXME`, or skipped test added in the batch's diffs without a row tracking it.
- CI is green on every PR (`gh pr checks`), and every PR's base is the branch below it.
- Things noticed during implementation but out of scope became `S` rows, not prose in a PR.
- The status table matches `gh` and is committed on the top branch of the stack.

Running low on budget? Stop at a candidate boundary, commit the table, and say exactly where `/arch-review next` resumes. Never stop silently mid-candidate.

**Report:** one line per row — ID, status, PR link, breaking — then the blocked questions spelled out with options and a recommendation, then what `next` would pick.

---

## Rules of thumb

- Delete complexity; don't move it. A refactor that leaves the reader holding the same number of concepts isn't a candidate.
- Look for the one fix behind several problems. A candidate that removes one special case is a smaller finding; one that removes five is the point.
- One candidate, one PR. A PR that needs "and also" in its title is two.
