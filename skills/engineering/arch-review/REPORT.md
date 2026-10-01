# Report format

One Markdown file per scan: `docs/arch-review/YYYY-MM-DD-<slug>.md`. Mermaid renders on GitHub — use it for every before/after. Keep prose sparse; findings carry evidence (file:line, counts, a reproduced failure).

````markdown
# YYYY-MM-DD — <one-line headline>

Reviewed at `<sha>` (`<branch>`). Scope: <direction or hot spots, and how they were found>. Glossary: <file or none>. ADRs read: <list>.

## Status

| ID | Candidate | Strength | Status | Branch | PR | Breaking | Notes |
|---|---|---|---|---|---|---|---|
| C1 | <names the deepening> | Strong, live defect | todo | refactor/<slug> | | | |
| S1 | <smaller finding> | — | todo | (rides with C1) | | | |

Status is one of `todo`, `in-progress`, `pr-open`, `merged`, `blocked`, `dropped`. `blocked` and `dropped` always carry a reason.

## Since the last review

<the previous report's open rows and what happened to them — omit on a first review>

## Map

<one Mermaid diagram of where the friction sits>

## Candidates

### C1. <title> — **Strong**

**Files:** `path/a.ts`, `path/b.ts`
**Dependency category:** in-process | local-substitutable | ports & adapters | mock
**Problem:** one or two sentences, with the evidence.
**Solution:** one or two sentences. No interface design yet.
**Wins:** ≤ 6 words each, in glossary terms ("locality: pricing bugs live in one module").
**Before / after:** two Mermaid diagrams.

#### Decisions

Q1 — <question> → <answer>, because <fact>.

## Smaller findings

### S1. <title>

<what, where, the fix>

## Departures

<where an implementation deliberately differs from the report, and why>
````

The index `docs/arch-review/README.md` lists reports newest first, one line each: date, linked headline, and how many rows are still open.
