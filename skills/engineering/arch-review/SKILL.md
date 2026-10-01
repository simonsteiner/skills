---
name: arch-review
description: Scan the codebase for deepening and maintainability candidates, save a visual HTML report and a status ledger to docs/arch-review/, then implement the batch you confirm — one stacked PR per candidate, decisions recorded, loose ends audited.
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

**One checkpoint, then hands-off.** The user confirms the batch once (Step 4). After that every design question is decided with the recommended answer and written down; nothing else waits for the user except a one-way door (Step 5). The ledger is the state — any session, any agent, picks up from its status table.

Call the Skill tool with "codebase-design" before anything else. Use its vocabulary exactly — module, interface, implementation, depth, seam, adapter, leverage, locality — in the report, the ledger, commits, and PR bodies.

**Pick the entry from what was asked:**

- `/arch-review [direction]` — new scan (Step 1) through implementation (Step 6).
- `/arch-review next` — resume: Step 3's reconcile on the newest ledger with open rows, then Step 4.
- `/arch-review report` — Steps 1–3 only.

---

## Step 1 — Scope, then scan

- A direction from the user wins. Otherwise find the hot spots: `git log --since=3.months --name-only --format= | sort | uniq -c | sort -rn | head -40`. Deepening pays off only where change keeps landing — weight those paths first; widen only if churn is scattered.
- Read the domain glossary (`GLOSSARY.md` or `CONTEXT.md`, whichever exists), the ADRs under `docs/adr/`, and the previous ledgers in `docs/arch-review/`. Don't re-suggest what an ADR or an earlier `dropped` row already settled, unless the friction is real enough to reopen it — then say which ADR and why.
- Spawn sub-agents to walk the scoped code with both lenses in [LENSES.md](LENSES.md) — one per lens, or one per hot area in a large repo. Give each the scope, the vocabulary, and its lens; ask for evidence (file:line, counts, a failing input) behind every claim.
- Apply the deletion test to every suspected shallow module. Verify each sub-agent claim yourself before it becomes a candidate.

---

## Step 2 — Write the report and the ledger

Follow [REPORT.md](REPORT.md). Two files, same stem, in `docs/arch-review/`:

- **`YYYY-MM-DD-<slug>.html`** — the report, built from [report-template.html](report-template.html): ranked overview, friction map, one card per candidate with before/after diagrams, smaller findings, top recommendation. Open it for the user and give the path.
- **`YYYY-MM-DD-<slug>.md`** — the ledger: the status table, then empty **Decisions** and **Departures** sections that the implementation fills.

Add the pair to the top of `docs/arch-review/README.md` (create the index if it's missing).

- **Candidates** (`C1…`) are deepenings, each with Files, Problem, Solution, Wins, a before/after diagram, strength (`Strong` / `Worth exploring` / `Speculative`), dependency category, and `live defect` when it hides a bug you reproduced.
- **Smaller findings** (`S1…`) are local maintainability fixes from the second lens — two sentences each.
- Don't design interfaces here. That's Step 6.

Rank: strength, then live defect, then churn, then dependency order (a candidate another one builds on goes first). Plan the branch name for every row now — the ledger carries it, so a later session can find the work.

---

## Step 3 — Land the report as the backlog

- **New report:** call the Skill tool with "sync-and-branch" for `docs/arch-review-<slug>`, then call the Skill tool with "conventional-commit" to commit the report, ledger, and index. Push and open a PR. This is the base of the stack — merging it puts the backlog on the default branch for every later session.
- **Resume:** reconcile the ledger's status table against reality first — `gh pr list --state all --head <branch>` for each open row, and `git branch -a`. Fix rows that lag (a merged PR still marked `pr-open`). The next base is the tip of the highest open branch in the stack, or the default branch if everything merged.

`/arch-review report` stops here and reports the PR.

---

## Step 4 — Confirm the batch

Propose the batch and **wait for the user's answer** — this is the run's one checkpoint:

- **Default: every `Strong` row still `todo`**, in rank order. List each as `ID — title — strength — planned branch`.
- Name what's left out (`Worth exploring`, `Speculative`) so the user can pull a row in.
- Say where the smaller findings go: with the candidate PR that touches the same module, or together in one final PR.

The user can accept as is, add or drop rows, or reorder. Write the confirmed batch into the ledger's status table (`in-progress` for the first row), then go.

---

## Step 5 — Implement the batch

Per candidate, spawn **one implementer sub-agent** — fresh context per candidate is what keeps the run from stalling halfway. Brief it with pointers, not copies: the report and ledger paths, the candidate ID, the base branch, and Steps 6–7 of this skill. Run candidates in sequence; each branch stacks on the previous one. When the harness has no sub-agents, do it inline and still finish one candidate completely before starting the next.

After each sub-agent returns, verify its work — branch pushed, PR open against the right base, row updated — before starting the next.

---

## Step 6 — Decide the design (autonomous grilling)

Map the candidate as a decision tree: the shape of the deepened module, what sits behind the seam, the dependency category (codebase-design's DEEPENING), which tests survive, which callers change.

- Work it in rounds. Each round, take every decision whose prerequisites are settled and **answer each one yourself with the recommended option**.
- Ground every answer in a fact from this tree — a measurement, a grep count, a reproduced failure — not an assertion. Look facts up; never guess them.
- When the interface shape is genuinely open, use codebase-design's design-it-twice pattern and take your own recommendation.
- Record every decision under the candidate's heading in the ledger's **Decisions**: `Q<n> — question → answer, because <fact>`.
- **One-way doors stop the candidate, not the run:** data migrations, published wire or file formats, deletion of user data. Mark the row `blocked` with the question in Notes and move on to the next candidate.
- A new domain term, or a sharpened one: call the Skill tool with "domain-modeling" and update the glossary inline. Dropping a candidate for a load-bearing reason: record it as an ADR the same way, so the next review doesn't re-suggest it.

---

## Step 7 — Build, check, ship

1. Branch `refactor/<candidate-slug>` (the planned name) off the base.
2. **Live defect:** pin it with a failing test first, then move code.
3. Implement the decisions. Replace, don't layer: write tests at the new interface, delete the tests and shallow modules it makes redundant, update docs and code maps that name moved files.
4. Run what the repo runs — typecheck, lint, the full suite. Where the project has golden outputs, show they're byte-identical, or explain the intended difference.
5. Check the diff against the approval bar in [LENSES.md](LENSES.md). Then call the Skill tool with "code-review": fixed point = the base branch, spec = this candidate's card in the report plus its decisions in the ledger. Fix what's real.
6. Update the candidate's ledger row (`pr-open`, PR number, Breaking) and write any **Departure** from the report, in the same branch.
7. Call the Skill tool with "conventional-commit" to commit, push, then `gh pr create --base <base>`. Call the Skill tool with "pr" for the body, and link the candidate's decisions in the ledger from it. Never merge.

---

## Step 8 — Loose ends, then report

Don't report until this audit comes back empty, or every gap it finds is fixed or has become a new row:

- Every batch row is `pr-open`, `merged`, `dropped`, or `blocked` — the last two with a reason in Notes.
- Every Solution bullet and every Decision is in a diff. Departures are written up.
- No old shallow module, its tests, or its re-export survives beside the new one. `git grep` the old names and paths.
- No `TODO`, `FIXME`, or skipped test added in the batch's diffs without a row tracking it.
- CI is green on every PR (`gh pr checks`), and every PR's base is the branch below it.
- Things noticed during implementation but out of scope became `S` rows, not prose in a PR.
- The ledger's status table matches `gh` and is committed on the top branch of the stack.

Running low on budget? Stop at a candidate boundary, commit the table, and say exactly where `/arch-review next` resumes. Never stop silently mid-candidate.

**Report:** one line per row — ID, status, PR link, breaking — then the blocked questions spelled out with options and a recommendation, then what `next` would pick.

---

## Rules of thumb

- Delete complexity; don't move it. A refactor that leaves the reader holding the same number of concepts isn't a candidate.
- File size is a place to look, never a finding. A 1,200-line deep module is fine; a 300-line file of special cases isn't.
- One candidate, one PR. A PR that needs "and also" in its title is two.
- The report is a dated record: never edit it after the scan. Progress goes in the ledger; a new scan is a new pair of files.
- Decisions recorded with their facts are what make autonomy safe. A decision without a fact is a guess.
