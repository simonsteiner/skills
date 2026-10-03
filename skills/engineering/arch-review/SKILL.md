---
name: arch-review
description: Scan the codebase for deepening and maintainability candidates, save a ranked Markdown report with diagrams and a status table to docs/arch-review/, then implement the batch you confirm — one stacked PR per candidate, decisions recorded, loose ends audited.
disable-model-invocation: true
metadata:
  credits:
    - skill: improve-codebase-architecture
      author: Matt Pocock
      url: "https://github.com/mattpocock/skills/tree/main/skills/engineering/improve-codebase-architecture"
    - skill: thermo-nuclear-code-quality-review
      author: Cursor
      url: "https://github.com/cursor/plugins/tree/main/cursor-team-kit/skills/thermo-nuclear-code-quality-review"
---

# Arch Review

Find where the code fights its maintainers, write it down in the repo as a backlog, then work the backlog: one candidate, one branch, one PR, until the batch is done and audited.

**One checkpoint, then hands-off.** The user confirms the batch once (Step 4). After that every design question is decided with the recommended answer and written down; nothing else waits for the user except a one-way door (Step 6). The report is the state — any session, any agent, picks up from its status table.

**Budget.** A run is long, and its cost is turns × context: every turn re-reads everything the agent has loaded. So:

- **Tier the models.** Judgement — this session and the Step 6 design agent — runs on the strongest model. Everything else — scanners, Build and Ship agents, and every nested sub-agent any of them spawns (code-review's reviewers, design-it-twice's designers) — runs on the mid-tier model (`model: "sonnet"` in Claude Code). Say so in every brief, including that nested sub-agents inherit the rule.
- **Keep contexts small.** Every brief carries the [context rules](#context-rules). Prefer a fresh agent over a long one.
- **One run at a time.** Two arch-reviews in parallel multiply the burn rate; queue the next repo instead.

Call the Skill tool with "codebase-design" before anything else. Use its vocabulary exactly — module, interface, implementation, depth, seam, adapter, leverage, locality — in the report, the decisions, commits, and PR bodies.

**Pick the entry from what was asked:**

- `/arch-review [direction]` — new scan (Step 1) through the loose-ends audit (Step 8).
- `/arch-review next` — resume: Step 3's reconcile on the newest report with open rows, then Step 4.
- `/arch-review report` — Steps 1–3 only.

---

## Step 1 — Scope, then scan

- A direction from the user wins. Otherwise find the hot spots: `git log --since=3.months --name-only --format= | sort | uniq -c | sort -rn | head -40`. Deepening pays off only where change keeps landing — weight those paths first; widen only if churn is scattered.
- Read the domain glossary (`GLOSSARY.md` or `CONTEXT.md`, whichever exists), the ADRs under `docs/adr/`, and the previous reports in `docs/arch-review/`. Don't re-suggest what an ADR or an earlier `dropped` row already settled, unless the friction is real enough to reopen it — then say which ADR and why.
- Spawn mid-tier sub-agents to walk the scoped code with both lenses in [LENSES.md](LENSES.md) — one per lens, or one per hot area in a large repo. Give each the scope, the vocabulary, its lens, and the [context rules](#context-rules); ask for evidence (file:line, counts, a failing input) behind every claim, and a findings list under 800 words — not file contents.
- Apply the deletion test to every suspected shallow module. Verify each sub-agent claim yourself before it becomes a candidate.

---

## Step 2 — Write the report

Copy [report-template.md](report-template.md) to `docs/arch-review/YYYY-MM-DD-<slug>.md` and fill it in following [REPORT.md](REPORT.md): status table, friction map, one card per candidate with a before/after diagram, smaller findings, recommendation. Add it to the top of `docs/arch-review/README.md` (create the index if it's missing).

- **Candidates** (`C1…`) are deepenings, each with Files, Problem, Solution, Wins, a before/after diagram, strength (`Strong` / `Worth exploring` / `Speculative`), dependency category, and `live defect` when it hides a bug you reproduced.
- **Smaller findings** (`S1…`) are local maintainability fixes from the second lens — two sentences each.
- Don't design interfaces here. That's Step 6.

Rank: strength, then live defect, then churn, then dependency order (a candidate another one builds on goes first). Plan the branch name for every row now — the status table carries it, so a later session can find the work.

---

## Step 3 — Land the report as the backlog

- **New report:** cut `docs/arch-review-<slug>` from the fresh default branch (`git fetch origin && git switch --no-track -c docs/arch-review-<slug> origin/<default>`), then call the Skill tool with "conventional-commit" to commit the report and index. Push and open a PR. This is the base of the stack — merging it puts the backlog on the default branch for every later session.
- **Resume:** reconcile the report's status table against reality first — `gh pr list --state all --head <branch>` for each open row, and `git branch -a`. Fix rows that lag (a merged PR still marked `pr-open`). The next base is the tip of the highest open branch in the stack, or the default branch if everything merged.

`/arch-review report` stops here and reports the PR.

---

## Step 4 — Confirm the batch

Propose the batch and **wait for the user's answer** — this is the run's one checkpoint:

- **Default: every `Strong` row still `todo`**, in rank order. List each as `ID — title — strength — planned branch`.
- Name what's left out (`Worth exploring`, `Speculative`) so the user can pull a row in.
- Say where the smaller findings go: with the candidate PR that touches the same module, or in final PRs of at most five `S` rows each, grouped by module.

The user can accept as is, add or drop rows, or reorder. Write the confirmed batch into the report's status table (`in-progress` for the first row), then go.

---

## Step 5 — Implement the batch

Per candidate, spawn **three sub-agents in sequence**, each with a fresh context — a single implementer's context grows past what the later phases need, and the review and PR turns then pay for all of it:

| Phase | Model | Does | Hands back |
|---|---|---|---|
| **Design** | strongest | Step 6 | Decisions committed to the report on the candidate branch, or the row `blocked` |
| **Build** | mid-tier | Step 7.1–4 | Branch committed with checks green, or what failed |
| **Ship** | mid-tier | Step 7.5–7 | PR number, base, row updated and pushed |

Brief each with pointers, not copies: the report path, the candidate ID, the branch and its base, its steps of this skill, the [context rules](#context-rules), and the model rule for anything it spawns. Build and Ship work from the candidate's card and Decisions — they don't reopen the design; a Decision that proves wrong becomes a **Departure**.

Run candidates in sequence; each branch stacks on the previous one. A batch of smaller findings is one candidate without a Design phase; its Build agent cuts the branch. When the harness has no sub-agents, do it inline and still finish one candidate completely before starting the next.

Between phases, check the hand-back — Decisions in the report, checks green, PR open against the right base, row updated. A gap goes back to a fresh agent of the same phase with the gap named; don't patch it from this session's context.

### Context rules

Put these in every brief:

- Read your candidate's card, not the report: `grep -n` its heading, then read that range.
- Read files in ranges (`grep -n`, then `sed -n` or `Read` with offset/limit); never a whole test file or a whole module you aren't rewriting.
- Trim command output: `… 2>&1 | tail -40` for tests, lint, and typecheck; `git diff --stat` before any full diff.
- Don't re-read what you already hold; keep notes in the report or the commit, not in the conversation.

---

## Step 6 — Decide the design (autonomous grilling)

Branch `refactor/<candidate-slug>` (the planned name) off the base. Map the candidate as a decision tree: the shape of the deepened module, what sits behind the seam, the dependency category (codebase-design's DEEPENING), which tests survive, which callers change.

- Work it in rounds. Each round, take every decision whose prerequisites are settled and **answer each one yourself with the recommended option**.
- Ground every answer in a fact from this tree — a measurement, a grep count, a reproduced failure — not an assertion. Look facts up; never guess them.
- When the interface shape is genuinely open, use codebase-design's design-it-twice pattern and take your own recommendation.
- Record every decision in the candidate's **Decisions** block in the report: `Q<n> — question → answer, because <fact>`. Call the Skill tool with "conventional-commit" to commit the Decisions on the candidate branch.
- **One-way doors stop the candidate, not the run:** data migrations, published wire or file formats, deletion of user data. Mark the row `blocked` with the question in Notes and move on to the next candidate.
- A new domain term, or a sharpened one: call the Skill tool with "domain-modeling" and update the glossary inline. Dropping a candidate for a load-bearing reason: record it as an ADR the same way, so the next review doesn't re-suggest it.

---

## Step 7 — Build, check, ship

**Build** (7.1–4):

1. Work on the candidate branch from Step 6.
2. **Live defect:** pin it with a failing test first, then move code.
3. Implement the decisions. Replace, don't layer: write tests at the new interface, delete the tests and shallow modules it makes redundant, update docs and code maps that name moved files.
4. Run what the repo runs — typecheck, lint, the full suite. Where the project has golden outputs, show they're byte-identical, or explain the intended difference. Call the Skill tool with "conventional-commit" to commit.

**Ship** (7.5–7):

5. Check the diff against the approval bar in [LENSES.md](LENSES.md). Then call the Skill tool with "code-review": fixed point = the base branch, spec = this candidate's card and decisions in the report. Fix what's real, and rerun the checks.
6. Update the candidate's status row (`pr-open`, PR number, Breaking) and write any **Departure** from the report, in the same branch.
7. Call the Skill tool with "conventional-commit" to commit, push, then `gh pr create --base <base>`. Call the Skill tool with "pr" for the body, and link the candidate's card in the report from it. Never merge.

---

## Step 8 — Loose ends, then report

Don't report until this audit comes back empty, or every gap it finds is fixed or has become a new row:

- Every batch row is `pr-open`, `merged`, `dropped`, or `blocked` — the last two with a reason in Notes.
- Every Solution bullet and every Decision is in a diff. Departures are written up.
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
- File size is a place to look, never a finding. A 1,200-line deep module is fine; a 300-line file of special cases isn't.
- One candidate, one PR. A PR that needs "and also" in its title is two.
- The report is a dated record: after the scan, only the status table, Decisions, and Departures change. Never rewrite a finding; a new scan is a new file.
- Decisions recorded with their facts are what make autonomy safe. A decision without a fact is a guess.
