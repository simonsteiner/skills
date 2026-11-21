---
"simonsteiner-skills": patch
---

`scripts/lint-skills.py` now parses `SKILL.md` frontmatter with `ruamel.yaml` (YAML 1.2, duplicate keys rejected, locked in `pyproject.toml`/`uv.lock` via `uv`) instead of hand-rolled regexes, enforces an allowlist of spec fields plus `disable-model-invocation` with strict scalar types, checks bundled Python scripts stay stdlib-only unless they declare PEP 723 dependencies, and flags vague description filler and boilerplate routing-label prefixes.
