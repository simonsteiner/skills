# Own frontend-craft instead of curating two design skills

## Context

Nothing in this repo or the curated list covered frontend design. Two upstream skills were candidates:

- `frontend-design` (anthropics/skills; the same `SKILL.md` ships as a plugin in anthropics/claude-code) — one ~80-line, prompt-only, model-invoked skill: ground the design in the subject, plan a compact token system, review the plan against five named "AI-generated" looks, build with restraint, critique your own render, write the copy plainly. Strong on process and voice; it stops at building, and its advice is tuned for landing pages — a dashboard or a docs page gets the same push for a bold hero.
- `impeccable` (pbakaus/impeccable) — started from frontend-design and grew into a toolkit: one skill with 24 commands, ~45 reference files, a self-contained engine binary with 59 detector rules, hooks that run the detector on every edit, four sub-agents, a live browser mode, and a `PRODUCT.md`/`DESIGN.md` setup flow. Its best ideas are portable prose: visitor modes (Persuade, Operate, Read, Experience) that change what good looks like per surface, "refinement preserves; redesign replaces", a concrete quality floor, bounded verification passes, and critique and audit rubrics.

Curating either has a cost. Both are model-invoked with overlapping triggers, so curating both means two skills competing for every UI request. Impeccable through skills.sh arrives as the skill alone — no hooks, no sub-agents — yet its first setup step downloads and runs an unpinned native engine, and it writes product and design files into whatever project it touches. Curating only frontend-design leaves out the modes and the review half.

## Decision

**Own a `frontend-craft` skill adapted from both, and archive both upstreams in `skills.json` without ever curating them.**

- `frontend-craft` is model-invoked, in `engineering/`. `SKILL.md` keeps frontend-design's process and voice, adds impeccable's mode choice, brief-wins and refine-vs-redesign rules, colour strategies, and bounded verification, and covers refinement requests (bolder, quieter, simpler, polish, copy) as short guidance rather than commands.
- Three references load on demand: `MODES.md` (what each mode lets the visual world do), `FLOOR.md` (checks and refusals, read before any UI edit), `REVIEW.md` (critique and audit rubrics and report format).
- Dropped from impeccable: the engine and detector, hooks, live mode, sub-agents, the command dispatcher, the setup flow and its project files, the concept-seed roll, the comp-led image pipeline, and native iOS/Android references. The skill reads a project's `DESIGN.md` when one exists but never creates it.
- Both upstreams are Apache-2.0. `CREDITS.md` carries the license, the copyright lines, and what changed, as section 4 requires. The repo itself stays MIT; the adapted files are under Apache-2.0 per the credits.

## Consequences

- **No upstream sync.** Impeccable moves fast (v4.5.2 as of this decision) and frontend-design was rewritten recently; neither change lands here on its own. Re-read both when revising the skill.
- **No deterministic detector.** The checks impeccable's engine runs mechanically are judgment calls here, verified against the render. For a project that wants the detector and live mode, install impeccable's own plugin into that project — `--check` will report it as `archived` if it lands in the global store.
- **The bar from ADR 0004 holds:** owning was justified because the wanted shape — one skill, both halves, no binary — couldn't be reached by calling either upstream, only by changing them.
