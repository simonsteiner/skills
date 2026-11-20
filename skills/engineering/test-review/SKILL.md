---
name: test-review
description: Reviews a project's test setup for blind spots, wasted effort, and how the tests run; saves a ranked Markdown report with a status table to docs/test-review/, then fixes the batch you confirm — tdd for blind spots, prune-tests for waste — one stacked PR per candidate, loose ends audited.
disable-model-invocation: true
---

# Test Review

Find where the tests miss behaviour that keeps changing, and where they cost time without guarding anything. Write it down in the repo as a backlog, then work the backlog: one candidate, one branch, one PR, until the batch is done and audited.

**Evidence, not taste.** Every finding carries `path:line`, a count, a timing, or a commit. "Coverage is low" isn't a finding; "`billing/invoice.py` changed in 14 commits, 3 of them fixes, and no test calls `issue()`" is.

**One checkpoint, then hands-off.** The user confirms the batch once (Step 5), and that confirmation also agrees the seams each blind-spot card names, which `tdd` requires before it writes a test. After that every question is answered with the recommended option and written down; nothing else waits for the user except a one-way door. The report is the state: any session picks up from its status table.

**Budget.** A run is long, and its cost is turns × context. So:

- **Tier the models.** Judgement (this session, and a Design sub-agent when one runs) uses the strongest model. Scanner, Build and Ship sub-agents, and anything they spawn, use the mid-tier model (`model: "sonnet"` in Claude Code). Say so in every brief, including that nested sub-agents inherit the rule.
- **Keep contexts small.** Every brief carries the [context rules](#context-rules). Test files are the longest files in most repos; nobody reads one whole.
- **One run at a time**, and not beside an `/arch-review` run on the same repo: both stack PRs on the same code.

Call the Skill tool with "codebase-design" before anything else, and use its vocabulary (module, interface, seam, adapter, depth, locality) everywhere; `tdd` speaks it too. For waste, use prune-tests' own words: a test guards a behaviour, or it depends on the past, on nothing, or on the implementation.

**Pick the entry from what was asked:**

- `/test-review [direction]` — new review (Step 1) through the loose-ends audit (Step 8).
- `/test-review next` — resume: Step 4's reconcile on the newest report with open rows, then Step 5 — or straight to Step 6 when the status table already holds a confirmed batch (an `in-progress` row): the user confirmed it and its seams once, so don't ask again.
- `/test-review report` — Steps 1–4 only.

---

## Step 1 — Measure how the tests run

These numbers go in the report's **Vitals** and feed the infrastructure lens. Record the command behind each one.

- **Where tests run.** CI (`.github/workflows/`, or the project's CI config), git hooks (`lefthook dump` shows the merged config; else `.husky/`, `.pre-commit-config.yaml`), and the documented local command (`package.json` scripts, `pyproject.toml`, `Makefile`, `justfile`).
- **The suite, once, timed**, with per-test times sorted slowest first: `pytest --durations=25` prints them; elsewhere take them from the runner's JSON (`vitest --reporter=json`, `jest --json`, `go test -json`) and sort. Note the test count and the wall time. A suite that won't run locally (needs a service, a secret, a manual step) is the first infrastructure finding; record why and keep going on static evidence.
- **One test file, timed** — the `tdd` loop runs this dozens of times per slice. Over ~5 seconds for a unit-level file is a finding.
- **CI history** (GitHub): `gh run list --limit 200 --json workflowName,conclusion,attempt,startedAt,updatedAt` gives the test workflow's median duration, runs per week, and reruns (`attempt > 1`), each rerun a flakiness suspect.
- **Coverage, only if the project already produces it** (a coverage config, `coverage.xml`, `lcov.info`, `coverage-final.json`, a JaCoCo report) or a SonarQube project is configured (`sonar-project.properties`, `.sonarlint/connectedMode.json`). For the uncovered lines in the hot files: a sonar-coverage skill when one is available (the SonarQube plugin's, `sonarqube:sonar-coverage` in Claude Code; this repo doesn't ship it); else the SonarQube MCP tools when they're connected (file coverage details); else the project's own report. None of those readable → skip coverage and say so in Vitals. Don't add coverage tooling for the review. Coverage locates; it never ranks (see Rules of thumb).
- **Disabled tests**: `git grep -nE` over the test paths only, for the stack's skip, focus and retry markers (`\.skip\(|\bxit\(|\.only\(|@pytest\.mark\.(skip|xfail|flaky)|@flaky|t\.Skip\(|@Disabled|@Ignore|retryTimes\(`), plus a `retries`/`retry:` setting in the runner's config. `git blame` dates each one.

---

## Step 2 — Scope, then scan

- A direction from the user wins. Otherwise churn decides: scope to the top rows of the `drift` run below, which ranks the most-changed source files over six months. Tests pay off where change keeps landing; a cold module with no tests is not a blind spot worth a PR.
- Read the glossary (`GLOSSARY.md`), the ADRs under `docs/adr/`, and earlier reports in `docs/test-review/`. Don't re-suggest what an ADR or a `dropped` row settled unless the evidence is new; then say which and why.
- Gather the history evidence with [scripts/test-history.py](scripts/test-history.py) — run `--help` first; it explains every column and how it tells tests from source:

  ```bash
  <skill-dir>/scripts/test-history.py drift [<scope>…]      # hot source files, and how often their tests moved with them
  <skill-dir>/scripts/test-history.py fixes [<scope>…]      # fix commits that changed no test
  <skill-dir>/scripts/test-history.py refactors [<scope>…]  # test files that refactor commits had to change
  ```

  A repo with its own test layout passes `--test-pattern <regex>`; check a few pairings before citing them.
- Spawn three mid-tier sub-agents, one per lens in [LENSES.md](LENSES.md) — blind spots, waste, infrastructure — or one per lens per hot area in a large repo. Give each the scope, the vocabulary, its lens, the Step 1 numbers and the script output it needs, and the [context rules](#context-rules); ask for evidence behind every claim and a findings list under 800 words, not file contents.
- **Verify every claim yourself** before it becomes a candidate. A blind spot: grep the tests for the interface's names and callers, so a test reaching the behaviour through another interface isn't missed. Waste: name the `prune-tests` category it falls in and the test that still guards the behaviour, or "nothing — it guards none".
- **Tests that mock internals: the seam decides.** When the module has a seam the behaviour can be tested at, they're waste tied to the implementation: a `waste` candidate that rewrites them at that seam. When it has none (the only way in is mocking internals or reading private state), that's an architecture problem, not a test one: the module goes in the report's **Hand-offs**, for the user to run `/arch-review <direction>` on, and its tests stay, since they're the only guard until the seam exists. This skill doesn't redesign modules.

---

## Step 3 — Write the report

The report is a folder, `docs/test-review/YYYY-MM-DD-<slug>/`, so no file in it outgrows what an agent reads whole. Copy [assets/report-template.md](assets/report-template.md) to its `README.md` and [assets/card-template.md](assets/card-template.md) to one `C<n>-<card-slug>.md` per candidate, and fill them in following [REPORT.md](REPORT.md). Keep every file under the project's token budget (its lefthook `file-tokens` job's `--max-tokens`, else 5,000 tokens; bytes / 4). Add the report to the top of `docs/test-review/README.md` (create the index if it's missing).

Every candidate (`C1…`) has a **kind**, and the kind decides how it's fixed:

| Kind | Fixed by | The card names |
|---|---|---|
| `blind spot` | the Skill tool with "tdd" | each seam to test at, with what it catches and misses; the behaviours to pin there, each with `path:line` and its evidence |
| `waste` | the Skill tool with "prune-tests" | each test (`path:line`), its prune-tests category, what still guards its behaviour, and its cost (seconds, edits) |
| `infra` | a direct change; hooks through the Skill tool with "setup-lefthook", workflows through the Skill tool with "secure-github-actions" | what runs now, the change, and the measurement it should move |

Size each candidate for one PR: one seam's behaviours, one module's tests, one infrastructure change. Each gets strength (`Strong` / `Worth exploring` / `Speculative`), door (`one-way` when it deletes a recorded fixture or golden file that can't be regenerated, changes branch protection or required checks, or removes a test a contract or compliance doc names; else `two-way`), and `live defect` when the scan reproduced a bug. **Smaller findings** (`S1…`) are single-test or single-line fixes, two sentences each.

Rank: strength, then live defect, then cost (churn × fixes for a blind spot; CI seconds and refactor edits for waste), then dependency order: an `infra` row that makes the suite runnable or isolated goes before the rows that need it. Plan each row's branch now: `test/<slug>` for blind spots and waste, `ci/<slug>` for infra.

---

## Step 4 — Land the report as the backlog

- **New report:** cut `docs/test-review-<slug>` from the fresh default branch (`git fetch origin && git switch --no-track -c docs/test-review-<slug> origin/<default>`), call the Skill tool with "conventional-commit" to commit the report and index, push, and open a PR. It's the base of the stack.
- **Resume:** reconcile the status table against reality first — `gh pr list --state all --head <branch>` for each open row, and `git branch -a` — and fix rows that lag. The next base is the tip of the highest open branch in the stack, or the default branch if everything merged.

`/test-review report` stops here and reports the PR.

---

## Step 5 — Confirm the batch and the seams

Propose the batch and **wait for the user's answer** — the run's one checkpoint:

- **Default: every `Strong` row still `todo`**, in rank order, as `ID — title — kind — door — planned branch`. Under each blind spot, list its seams with their one-line catches/misses, and say that confirming the batch agrees them for `tdd`. Say up front that a `one-way` row stops for the user before its change lands.
- Name what's left out (`Worth exploring`, `Speculative`), and the hand-offs to `/arch-review`.
- Smaller findings ride with the candidate touching the same test file, or go in final PRs of at most five `S` rows each.

The user can accept, add or drop rows, reorder, or move a seam. Write the confirmed batch and any changed seam into the report, every confirmed row `in-progress`, so a `next` after a stop at a candidate boundary still sees the batch as confirmed. Then go.

---

## Step 6 — Implement the batch

Per candidate, fresh sub-agents in sequence, each briefed with pointers, not copies: the report path, the candidate ID, the branch and its base, its steps below, the [context rules](#context-rules), and the model rule.

| Phase | Model | When | Does | Hands back |
|---|---|---|---|---|
| **Design** | strongest | `infra` rows only | Decides the change from the card, `Q<n> — question → answer, because <fact>` in the card's Decisions; a one-way door marks the row `blocked` | Decisions committed on the branch |
| **Build** | mid-tier | every row | Step 7 | Branch committed, checks green, or what failed |
| **Ship** | mid-tier | every row | Step 8.1–3 | PR number, base, row updated and pushed |

Blind spots and waste skip Design: the seams and the tests to prune were decided at scan time and confirmed in Step 5. A batch of smaller findings is one candidate without a Design phase, on `test/smaller-findings-<n>`; its Build sub-agent cuts the branch. A card that proves wrong in Build becomes a **Departure**, not a redesign. Between phases, check the hand-back; a gap goes back to a fresh sub-agent of the same phase with the gap named. Candidates run in sequence, each branch stacked on the previous one. Without sub-agents, do it inline, one candidate completely before the next.

### Context rules

Put these in every brief:

- Read the report's `README.md` and your candidate's card, nothing else in the report.
- Read files in ranges (`grep -n`, then `sed -n` or `Read` with offset/limit); never a whole test file or a whole module.
- Run the narrowest test command that answers the question (one file, one test), and the full suite once at the end. Trim output: `… 2>&1 | tail -40`; `git diff --stat` before any full diff.
- Keep notes in the card or the commit, not in the conversation.

---

## Step 7 — Build

Branch the planned name off the base (or check out the Design phase's branch). A `one-way` row stops before the change that crosses the door: mark it `blocked` with the question in Notes and move on to the next candidate. Then by kind:

- **Blind spot.** Call the Skill tool with "tdd". The seams are the card's, already confirmed in Step 5; don't ask again. Pin one behaviour per cycle, through the seam's public interface, mocking only at system boundaries. Existing code usually passes a new test at once, so **prove each test can fail**: make the smallest change to the code under test that breaks the behaviour, watch the test go red, revert, and name that mutation in the commit body. A test that's red against the unchanged code found a live defect: keep it, fix the code in this PR, mark the row 🔴, and call the Skill tool with "diagnosing-bugs" when the cause isn't plain from the failure.
- **Waste.** Time the affected tests first. Call the Skill tool with "prune-tests", limited to the card's Prune rows: it prunes every test in whatever path it's given, and only those rows were confirmed in Step 5. A test it would also cut that the card doesn't list becomes a new `S` row, not part of this PR. Before each deletion, the card says what still guards the behaviour; a test that's the only guard of a behaviour something relies on is rewritten against that behaviour, not deleted. Time them again.
- **Infra.** Implement the Decisions. Re-measure what the card said it should move (suite time, single-file time, reruns, an order-shuffled run passing).

Then run what the repo runs — typecheck, lint, the full suite — and call the Skill tool with "conventional-commit" to commit.

---

## Step 8 — Ship, audit, report

**Ship** (8.1–3):

1. Check the diff against the approval bar in [LENSES.md](LENSES.md). Then call the Skill tool with "review-prs" in local mode: fixed point = the base branch, spec = the candidate's card. Rerun the checks.
2. Update the candidate's status row (`pr-open`, PR number) and its numbers (tests added or removed, seconds saved), and write any Departure, in the same branch.
3. Call the Skill tool with "conventional-commit" to commit, push, `gh pr create --base <base>`, and call the Skill tool with "pr-body" for the body, linking the card and showing each mutation that turned a new test red, or the before/after timings. Never merge.

**Loose ends.** Don't report until this comes back empty, or every gap is fixed or a new row:

- Every batch row is `pr-open`, `merged`, `dropped` or `blocked`, the last two with a reason.
- Every behaviour a blind-spot card listed has a test that was seen red, its mutation recorded. Every test a waste card listed is gone, rewritten, or explained in a Departure, and no test the card didn't list was deleted.
- No test added in the batch mocks a module the project owns, reads private state, or is skipped; no `TODO` without a row.
- Waste and infra rows carry before/after numbers.
- CI is green on every PR (`gh pr checks`), and each PR's base is the branch below it.
- The status table matches `gh` and is committed on the top branch.

Running low on budget? Stop at a candidate boundary, commit the table, and say where `/test-review next` resumes.

**Report:** one line per row (ID, kind, status, PR link), the vitals that moved (suite time, single-file time, tests added and removed, fix commits without a test), the blocked questions with a recommendation, the hand-offs as `/arch-review <direction>` lines for the user to run, and what `next` would pick.

---

## Rules of thumb

- A test earns its place by failing on a regression, and only on one. Everything here serves that sentence.
- Coverage locates; it never ranks. A covered line no assertion checks is still a blind spot, and 100% isn't a goal. Churn and fix history decide what's worth pinning.
- Waste is measured in seconds and edits: CI minutes per week, and how many refactor commits had to change the test.
- A test that needs internals mocked is telling you about the module, not the test: rewrite it at the seam when there is one, hand the module to `/arch-review` when there isn't (Step 2).
- Pin behaviour at the cheapest level that catches its regression; a second level asserting the same thing is waste.
- One candidate, one PR. The report is a dated record: after the scan only the status table, Decisions and Departures change.
