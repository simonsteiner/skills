---
"simonsteiner-skills": patch
---

arch-review gives each phase sub-agent its own brief file (`phases/design.md`, `phases/build.md`, `phases/ship.md`) instead of the whole `SKILL.md`, so a Build or Ship sub-agent loads a few hundred tokens of instructions rather than several thousand. The per-PR approval bar moves from `LENSES.md` into the Ship brief, and the token-budget recipe lives once in `REPORT.md`. Three things change on purpose:

- Ship updates the status row in a second commit after `gh pr create`, since the PR number isn't known before.
- A Build sub-agent records a wrong Decision as a Departure in its commit body, for Ship to copy into the report, and can add `S` rows for out-of-scope findings.
- Design can hand a candidate back `dropped`, with an ADR, which skips its Build and Ship.
