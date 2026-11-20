---
"simonsteiner-skills": patch
---

arch-review and test-review give each phase sub-agent its own brief file (`phases/design.md`, `phases/build.md`, `phases/ship.md`) instead of the whole `SKILL.md`, so a Build or Ship sub-agent loads a few hundred tokens of instructions rather than several thousand. The per-PR approval bar moves from `LENSES.md` into the Ship brief, arch-review's token-budget recipe lives once in `REPORT.md`, and restated rules are trimmed. The workflow and its rules are unchanged.
