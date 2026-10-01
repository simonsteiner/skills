# Report format

One Markdown file per scan: `docs/arch-review/YYYY-MM-DD-<slug>.md`, built from [report-template.md](report-template.md). It renders on GitHub — Mermaid diagrams, callouts, collapsible sections — so the report is read where the code is, and agents edit it and git diffs it line by line.

The look is borrowed from upstream's HTML report: diagrams carry the weight, prose is sparse, every candidate is a card with the same shape. The index `docs/arch-review/README.md` lists reports newest first: date, linked headline, open row count.

## What changes after the scan

Only three parts: the **Status** table, each candidate's **Decisions**, and **Departures**. Everything else is the dated record of what the scan found — never rewritten. A new scan is a new file.

## Sections, in order

1. **Header** — repo and headline, then one meta line: date, SHA and branch, scope, glossary file, ADRs read. A jump line to the sections and candidates. The legend sits in a collapsed `<details>`. No introduction paragraph.
2. **Status** — the backlog at a glance, in rank order: badges, lens, status, planned branch, PR, breaking, notes. Step 4 proposes the batch from it; every later session reads it first.
3. **Where it hurts** — one diagram of the scanned area with the hot modules marked, and one line of evidence for why they're hot.
4. **Since the last review** — the previous report's open rows and what became of them. Omit on a first scan.
5. **Candidate cards** — the centrepiece; see below. Separated by `---`.
6. **Smaller findings** — `S1…`: title, `path:line`, which PR it rides with, two sentences.
7. **Recommendation** — an `[!IMPORTANT]` callout: the candidate to take first, why in one sentence, the proposed batch (every Strong, in order).
8. **Departures** — empty at scan time.

## Candidate card

If a diagram needs a paragraph to be understood, redraw the diagram.

- **Heading** — `## C1 · <title>`, a short title naming the deepening ("Collapse the order intake pipeline").
- **Badge line** — strength (🟢 Strong · 🟡 Worth exploring · ⚪ Speculative), 🔴 live defect when a bug was reproduced, the dependency category in code font (`in-process`, `local-substitutable`, `ports & adapters`, `mock`), and what it builds on.
- **Files** — code-font paths with line ranges, on one line.
- **Before / After** — one Mermaid flowchart with two subgraphs side by side (`flowchart LR`, each subgraph `direction TB`, `before ~~~ after` to keep them apart). It's the only way GitHub puts two diagrams next to each other.
- **Evidence** — a `[!CAUTION]` callout with the reproduced failure for a live defect; otherwise one plain line with the count that shows the friction.
- **Problem / Solution / Wins** — a one-row table: one sentence, one sentence, ≤ 6-word wins separated by `<br>`. No interface design here; that's Step 6.
- **ADR** — a `[!NOTE]` callout, only when an ADR bears on it.
- **Decisions** — a collapsed `<details>`, empty until the candidate is implemented.

## Diagrams

Every diagram ends with the same `classDef` block from the template, so the visual language holds across reports: white `module`, dashed grey `shallow`, dark `deep`, `faded` internals inside a deep module, red `leak`. Quote every label, and never put `{{ }}` in a diagram — double braces are Mermaid's hexagon shape and break the render.

Pick the pattern that fits the candidate. Every diagram looking the same is a sign of not thinking about what each one needs to show.

- **Call flow** — `flowchart`, the workhorse for "X calls Y calls Z, and look at the mess". Mark leaking modules `:::leak` and label the edge `"leak"`.
- **Deep module** — the *after* as a dark `:::deep` node for the interface, joined by a dotted edge to a dark subgraph holding the absorbed modules as `:::faded` nodes. The template's card is this pattern.
- **Round-trips** — `sequenceDiagram` for "before: six round-trips; after: one".
- **Cross-section** — `flowchart TB` of thin `:::shallow` nodes for each pass-through a call crosses; after, one `:::deep` node named for the responsibility.
- **Collapse** — before: a nested call tree as subgraphs; after: the same tree inside one dark subgraph, its calls faded.

## Tone

Plain and concise, with the nouns and verbs from codebase-design.

- **Use exactly:** module, interface, implementation, depth, deep, shallow, seam, adapter, leverage, locality.
- **Never substitute:** component, service, unit (for module) · API, signature (for interface) · boundary (for seam) · layer, wrapper (for module).
- Fits: "Order intake is shallow: its interface nearly matches its implementation." "Pricing leaks across the seam." "Two adapters justify the seam: HTTP in prod, in-memory in tests."
- **Wins** name the gain in those terms — "locality: pricing bugs live in one module", "interface shrinks; implementation absorbs the wrappers" — never "easier to maintain" or "cleaner code".
- No hedging, no throat-clearing. If a sentence could be a bullet, make it one; if a bullet could be cut, cut it.
