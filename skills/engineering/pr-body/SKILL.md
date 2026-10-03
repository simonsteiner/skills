---
name: pr-body
description: >
  Writes a pull request body shaped by the kind of change — a fix shows before → after, a feature shows it working, a refactor shows nothing changed, a chore stays a few lines. Use when writing or rewriting a PR body or description, before `gh pr create`, or when another workflow reaches its open-a-PR step.
---

# PR Body

The kind of change decides what the body proves. One skeleton, with the Evidence section swapped per kind, and no sections the change doesn't need.

Skip preambles beyond the context line, keep prose brief, and use the domain language from `GLOSSARY.md` when the repo has one.

---

## Pick the kind

From the PR's Conventional Commit type, or what dominates the diff when commits mix:

| Kind | Types | Evidence proves |
|---|---|---|
| **Fix** | `fix`, `perf` | the same input goes from wrong to right |
| **Feature** | `feat` | it works, on a real run |
| **Refactor** | `refactor` | nothing changed that shouldn't have |
| **Small** | `docs`, `chore`, `build`, `ci`, `style`, `test`, deps bumps | — |

A refactor that also fixes a bug is a refactor with a before → after for that bug. A feature that also fixes one is a feature with a before → after line for it.

---

## Small: no template

Two to five lines: what changed and why, a diff sketch if the change is a value (a version, a description, a config key), and the one check that applies. No headings, no Merge Danger.

````markdown
Aligns the PyPI summary with the GitHub description; takes effect with the next release.

```diff
-description = "Python implementation of XCTrack's task format"
+description = "Python library & CLI for XCTrack .xctsk competition tasks: …"
```

`tomllib` reads the new value on this branch.
````

---

## Fix, feature, refactor

```markdown
<Context line — only what applies: Implements [card](…) / closes #N. Stacked on #N; retarget to X once it merges.>
<Why, 1–2 sentences — only when no linked card or issue already says it.>

## Summary

<diagram, diff sketch, or tree; each decision's reason next to it>

## Evidence

<per kind, below>

**Checks:** <one line — suite count, lint, types, build>

## Merge Danger

<one line, or the two bullets below>

<optional sections, only when they apply>
```

### Summary

Pick the smallest view that makes the change clear, and put each decision's reason right next to it ("150 m: 99.9 % of flying fixes read above 89 m under the ground"). Thresholds, constants and rejected options are explained here, not in Evidence.

- **Call tree** for runtime control flow, **file tree** for a new module or a broad move, **component tree** for UI structure, **pseudocode** for an algorithm, **Mermaid** for interaction between parts.
- **`diff`** when the point is what changes and the surrounding shape already exists. Match the diff to the topic — a call tree, a file tree, a signature, a state machine — not just the source code.
- **A whole block** when most of it is new or the reader needs a copyable target shape.
- Keep only the calls, files, states and boundaries the reader needs. Usually one view, sometimes two; rarely more.

**Fix:** a bug with a story may use story headings in place of `## Summary` — the symptom as observed (`## Day 3, 19:12: a walk read as a 4 min flight`), then `## Fix: <the rule>`. Evidence and Merge Danger follow as usual.

**Feature:** after the view, the key decisions as bullets, each with its reason. Name the alternative not taken when a reviewer would ask about it ("a second backend rather than a flag, because …").

### Evidence

Screenshots for visual changes, when the environment can take them. Otherwise execution: commands, outputs, tests, measurements. Never a vague "tested locally".

**Fix — before → after**, the same input both times:

```markdown
- **Before** (on <base>): <exact input> → <wrong output, error, or failing test>
  **After:** <same input> → <right output>
- **Effect on real data:** <what else moved when re-run, with numbers; "nothing else changed" is evidence too>
- **New test:** `<name>` — fails on the base.
```

**Feature — shown working.** No "before": the feature didn't exist, and `invalid choice: 'fcw'` proves nothing.

```markdown
- **Run:** <a real end-to-end run — command, output trimmed to what matters, or a screenshot>
- **Measured:** <quality, speed, cost against the baseline or the alternative, as a table when there are several>
- **Tests:** what they cover, as a short list.
```

**Refactor — unchanged:**

```markdown
- **Unchanged:** <golden outputs / re-export / snapshot> byte-identical to the base (<how it was compared>).
- **Behaviour changes on purpose:** <none, or before → after per change>
```

**Checks** is one line under Evidence (`uv run pytest` 307 passed; ruff, mypy clean). Don't spread suite output across the section.

### Merge Danger

Trivial — one line:

```markdown
## Merge Danger

Reverts cleanly · blast radius: none — no export key or value changes.
```

Otherwise two bullets:

```markdown
## Merge Danger

- **Doesn't revert:** <what a revert leaves behind — a published release, synced calendar events, written data, a created job, a cache — or "nothing">
- **Blast radius:** <none | repo-internal | site users | library consumers | production data> — <what could break, and for whom>
```

Pick the blast radius from that fixed scale so it compares across PRs; the specifics go after the dash. For a feature, say what it now costs or depends on to run: an external service, VRAM, a scheduled job, a new secret.

### Optional sections

Add each only when it applies, after Merge Danger:

- **`## For consumers`** — a library's API or behaviour change, in the words the changelog will use.
- **`## After merge`** — deploy notes and exact commands, run from where.
- **`## Not done`** — what was dropped and why, follow-ups, and anything needed before the feature takes real work. New findings the work turned up go here, not in Evidence.

---

## Before handing it over

- The first screen tells a reviewer what changed and why, without scrolling.
- Every Evidence line is something that was actually run or measured.
- Nothing is left in angle brackets, and no section is there just because the template has it.

See [CREDITS.md](CREDITS.md) for the upstream skills this adapts.
