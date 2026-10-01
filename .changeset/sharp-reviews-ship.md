---
"simonsteiner-skills": minor
---

Add `arch-review`, a user-invoked skill that scans a codebase for deepening and maintainability candidates, saves a visual HTML report (adapted from upstream's, with a fixed scaffold) and a Markdown status ledger to `docs/arch-review/`, and — after you confirm the batch (every Strong candidate by default) — ships one stacked PR per candidate with its design decisions recorded and loose ends audited. It replaces the curated `improve-codebase-architecture` and `thermo-nuclear-code-quality-review`, which move to a new `archived` list in `third-party/skills.json`; the sync skips archived skills and `--check` flags any still installed. Skills now call each other with "Call the Skill tool with "name"" instead of `/skill` prose, following upstream (`docs/invocation.md`). See ADR 0004 for why arch-review is owned rather than curated.
