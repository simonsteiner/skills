# Report and ledger

Every scan writes two files side by side in `docs/arch-review/`:

| File | What it is | Changes after the scan? |
|---|---|---|
| `YYYY-MM-DD-<slug>.html` | **The report.** A visual, self-contained page: ranked overview, friction map, one card per candidate with before/after diagrams, smaller findings, recommendation. | No — it's the dated record of what the scan found. |
| `YYYY-MM-DD-<slug>.md` | **The ledger.** Status table, decisions, departures — the state every later session reads and updates. | Yes, on every candidate. |

The report is for reading; the ledger is for working. Agents edit Markdown tables cleanly and git diffs them readably, so nothing that changes lives in the HTML. The index `docs/arch-review/README.md` lists scans newest first: date, headline linked to the report, ledger link, open row count.

## The report

Start from [report-template.html](report-template.html): copy it, keep `<head>`, the legend, and the class names, and fill the sections in order. Tailwind and Mermaid come from CDNs; there are no other scripts. Open it for the user when it's written (`wslview` on WSL, `xdg-open` on Linux, `open` on macOS) and give the absolute path. GitHub shows HTML as source, so the report is read locally or from a checkout; the ledger is what renders on GitHub.

### Sections

1. **Header** — repo, date, SHA and branch, scope, glossary file, link to the ledger, the legend, and a jump bar to each candidate. No introduction paragraph.
2. **Candidates, ranked** — one row per candidate: strength and live-defect badges, lens, planned branch, and which candidate it builds on. This is the backlog at a glance, and the order Step 4 proposes.
3. **Where it hurts** — one diagram of the scanned area with the hot modules marked, and one line of evidence for why they're hot (churn counts, defect count).
4. **Since the last review** — the previous ledger's open rows and what became of them. Omit on a first review.
5. **Candidate cards** — the centrepiece; see below.
6. **Smaller findings** — compact cards: title, `path:line`, two sentences, and whether it rides with a candidate PR.
7. **Top recommendation** — the candidate to take first, why in one sentence, and the proposed batch (every Strong, in order).

### Candidate card

The diagrams carry the weight. If a diagram needs a paragraph to be understood, redraw the diagram.

- **Title** — short, names the deepening ("Collapse the order intake pipeline").
- **Badges** — strength (`Strong` emerald, `Worth exploring` amber, `Speculative` slate), `live defect` in red when you reproduced a bug, and the dependency category (`in-process`, `local-substitutable`, `ports & adapters`, `mock`).
- **Files** — monospaced, with line ranges.
- **Before / After** — side by side, ~220–320px tall. Under *Before*, one line of evidence: the reproduced failure in red for a live defect, otherwise the count that shows the friction.
- **Problem / Solution / Wins** — one sentence, one sentence, bullets of ≤ 6 words. No interface design here; that happens per candidate in Step 6.
- **ADR callout** — one amber line, only when an ADR bears on it.

### Diagram patterns

Mix them. Every diagram looking the same is a sign of not thinking about what each candidate needs to show.

- **Mermaid flowchart** — the workhorse for "X calls Y calls Z, and look at the mess". `classDef` red for leaks; sequence diagrams for "before: six round-trips, after: one".
- **Hand-built deep module** — a thick dark `.deep` box with the small interface in a dashed `.seam` box on top and the absorbed modules `.faded` inside. Mermaid can't give an *after* the right weight; this can. The template's *After* panel is this pattern.
- **Cross-section** — stacked horizontal bands (`h-12 border-l-4`) for the layers a call passes through. Before: six thin bands doing nothing. After: one thick band named for the responsibility.
- **Mass diagram** — two rectangles per module, interface height against implementation height. Shallow: nearly equal. Deep: short interface, tall implementation.
- **Call-graph collapse** — before: nested boxes of calls. After: the same tree as one box, the now-internal calls faded inside it.

Style: editorial, not dashboard. Generous whitespace, serif headings, one accent (emerald) plus red for leaks and defects and amber for warnings. Module labels in diagrams use `.lbl` so they read as schematic, not UI.

### Tone

Plain and concise, with the nouns and verbs from codebase-design.

- **Use exactly:** module, interface, implementation, depth, deep, shallow, seam, adapter, leverage, locality.
- **Never substitute:** component, service, unit (for module) · API, signature (for interface) · boundary (for seam) · layer, wrapper (for module).
- Fits: "Order intake is shallow: its interface nearly matches its implementation." "Pricing leaks across the seam." "Two adapters justify the seam: HTTP in prod, in-memory in tests."
- **Wins** name the gain in those terms — "locality: pricing bugs live in one module", "interface shrinks; implementation absorbs the wrappers" — never "easier to maintain" or "cleaner code".
- No hedging, no throat-clearing. If a sentence could be a bullet, make it one; if a bullet could be cut, cut it.

## The ledger

Plain Markdown, so it renders on GitHub and diffs line by line.

```markdown
# YYYY-MM-DD — <same headline as the report>

Report: [YYYY-MM-DD-<slug>.html](YYYY-MM-DD-<slug>.html) · reviewed at `<sha>`

## Status

| ID | Candidate | Strength | Status | Branch | PR | Breaking | Notes |
|---|---|---|---|---|---|---|---|
| C1 | <names the deepening> | Strong, live defect | todo | refactor/<slug> | | | |
| S1 | <smaller finding> | — | todo | (rides with C1) | | | |

Status is one of `todo`, `in-progress`, `pr-open`, `merged`, `blocked`, `dropped`. `blocked` and `dropped` always carry a reason.

## Decisions

### C1

Q1 — <question> → <answer>, because <fact>.

## Departures

<where an implementation deliberately differs from the report, and why>
```
