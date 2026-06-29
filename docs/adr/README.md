# Architecture Decision Records

This folder holds **ADRs** — short records of significant decisions made about this repo: how skills are structured, why a convention exists, what trade-off was accepted. An ADR captures a decision *and the reasoning behind it* so a future reader (human or agent) understands why things are the way they are, not just what they are.

## When to add one

Write an ADR when you make a decision that:

- is non-obvious or could reasonably have gone the other way,
- you'd otherwise have to re-explain later, or
- constrains how future skills or docs should be written.

Skip it for routine changes the diff already explains.

## Format

One file per decision, named `NNNN-short-title.md` (zero-padded, incrementing). Keep it short:

- **Title** — the decision, stated as a fact (e.g. "Skills depend on each other via prose invocation, not file cross-references").
- **Context** — what forced the decision; the constraints in play.
- **Decision** — what we chose.
- **Consequences** — what this makes easier, harder, or off-limits.

ADRs are a historical log. Once written, prefer superseding an old ADR with a new one over rewriting it.
