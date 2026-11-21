---
"simonsteiner-skills": patch
---

docs-refactor checks design docs for four kinds of drift: missing behaviour, incomplete models, hardcoded shortcuts and divergent design. It links docs to the source it had to search for, and lists components no doc covers. Drift in an ADR goes in the report on its own line, with a superseding ADR proposed but not written. The cold read of `AGENTS.md` starts with a paraphrase of the project, and `docs/adr/` is linked from `AGENTS.md` only when it exists. With no sub-agent tool it falls back to a self-review. Adapted from Google's Elephant-Goldfish Model.
