# Report format

## Contents

- [Layout](#layout)
- [What changes after the scan](#what-changes-after-the-scan)
- [Overview sections](#overview-sections-in-order)
- [Candidate card](#candidate-card)
- [Diagram](#diagram)
- [Tone](#tone)

## Layout

One folder per review: `docs/test-review/YYYY-MM-DD-<slug>/`, holding `README.md` (the overview, from `assets/report-template.md`) and one `C<n>-<card-slug>.md` per candidate (from `assets/card-template.md`). A folder, not one file, so every file stays under the project's token budget: an agent reads the overview and the one card it works on. It renders on GitHub, so it's read where the code is and git diffs it line by line.

The index `docs/test-review/README.md` lists reviews newest first: date, headline linked to the review's `README.md`, open row count.

Every file stays under the project's token budget: what its lefthook `file-tokens` job enforces (5,000 tokens unless the job passes `--max-tokens`), else 5,000 tokens, measured as bytes / 4. An overview that runs over moves **Smaller findings** to `smaller-findings.md` beside it and points the Status rows' `S` links there.

## What changes after the scan

Only the **Status** table and **Departures** in the overview, each card's **Decisions**, and the numbers a Ship phase fills in (the card's **After**, the Status row's PR). Everything else is the dated record of what the scan found. A new review is a new folder.

## Overview sections, in order

1. **Header** — repo and headline, then one meta line: date, SHA and branch, scope, glossary, ADRs read. A jump line to the sections and the cards. No introduction paragraph.
2. **Status** — the backlog in rank order, each ID linking to its card: kind, strength, door, fix route, status, planned branch, PR, notes.
3. **Vitals** — a two-column table from Step 1 and the history script, each value with the command that produced it: suite time and test count, the five slowest tests, single-file time, CI median duration and runs per week, reruns, fix commits without a test (n of m), refactor commits that changed a test (n of m), disabled tests, coverage when it exists. The next review compares against these.
4. **Where it hurts** — one diagram of the hot modules, each marked by how well its behaviour is guarded ([Diagram](#diagram)), with one line of evidence.
5. **Hand-offs** — behaviour with no seam to test at, one line each with `path:line` and the `/arch-review <direction>` to run. Omit when empty.
6. **Since the last review** — the previous review's open rows and what became of them, and which vitals moved. Omit on a first review.
7. **Smaller findings** — `S1…`: title, `path:line`, which PR it rides with, two sentences.
8. **Recommendation** — an `[!IMPORTANT]` callout: the candidate to take first, why in one sentence, the proposed batch (every Strong, in order).
9. **Departures** — empty at scan time.

## Candidate card

One file per candidate, `C<n>-<card-slug>.md`. The template carries all three kinds; keep the block for the card's kind and delete the other two.

- **Heading** — `# C1 · <title>`, a short title naming the fix ("Pin invoice rounding at `issue()`", "Drop the mocked-repository tests in orders", "Move the browser suite to pre-push"), with a `[← Report](README.md)` back link.
- **Badge line** — kind (🕳️ blind spot · 🗑️ waste · 🔧 infra), strength (🟢 Strong · 🟡 Worth exploring · ⚪ Speculative), 🔴 live defect when the scan reproduced a bug, the door (↔ `two-way` · 🚪 `one-way`), the fix route (`tdd` · `prune-tests` · `direct`), and what it builds on.
- **Files** — code-font paths with line ranges, on one line.
- **Evidence** — one plain line with the count or timing that makes the case, or a `[!CAUTION]` callout with the reproduced failure for a live defect.
- **The kind's block:**
  - *Blind spot* — a **Seams** table (seam · catches · misses), then a **Pin** table (behaviour · `path:line` · evidence: a fix commit, a churn count, an uncovered branch). Step 5 confirms the seams; Step 8 checks every Pin row has a test seen red.
  - *Waste* — a **Prune** table (test `path:line` · prune-tests category or other waste · still guarded by · cost). "Still guarded by" names a test or says "nothing — guards none"; a test that's the only guard of a relied-on behaviour is marked *rewrite*, not *delete*.
  - *Infra* — **Now**, **Change**, and **Measure** (the number it should move, with its current value and the command).
- **Problem / Fix / Wins** — a one-row table: one sentence, one sentence, ≤ 6-word wins separated by `<br>`.
- **After** — filled at Ship: tests added or removed, mutations that turned new tests red, the Measure's new value.
- **Decisions** — a collapsed `<details>`, filled by an infra card's Design phase, or by a Build phase recording a choice.

## Diagram

One diagram per overview, in **Where it hurts**: the hot modules as nodes, labelled with name and churn, each with the class for how well its behaviour is guarded, and test files as small nodes with an edge to the modules they reach through an interface. A dashed edge marks a test that mocks the module's internals.

| Class | Means |
|---|---|
| `guarded` | its changing behaviour has tests at a seam |
| `thin` | some tests, but the history or coverage shows behaviour moving without them |
| `blind` | hot, and no test reaches it through its interface |
| `waste` | test file that costs more than it guards |

Quote every label, and never put `{{ }}` in a diagram (Mermaid's hexagon shape breaks the render). Cards carry tables, not diagrams: a seam or a list of tests reads better as rows.

## Tone

Plain and concise, with codebase-design's nouns and the numbers up front.

- **Use exactly:** module, interface, seam, adapter, behaviour, regression. A test "guards" a behaviour, "pins" it, "reaches" a module through an interface.
- **Never substitute:** unit (for module), API (for interface), boundary (for seam, except "system boundary" in the mocking sense).
- **Wins** name the gain: "regression in rounding fails CI", "−41 s per CI run", "refactors stop touching `test_orders.py`" — never "better coverage" or "cleaner tests".
- No hedging. If a sentence could be a bullet, make it one; if a bullet could be cut, cut it.
