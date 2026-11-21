---
"simonsteiner-skills": patch
---

`scripts/lint-skills.py` parses `SKILL.md` frontmatter with `ruamel.yaml` instead of hand-rolled regexes. It reads YAML 1.2, rejects duplicate keys, and is locked in `pyproject.toml`/`uv.lock`; run outside the repo, it re-runs itself through the repo's uv project. It enforces an allowlist of spec fields plus `disable-model-invocation`, with strict scalar types, and disallows `metadata` in owned skills: credits go in `CREDITS.md`, the version in `plugin.json`. It checks that bundled Python scripts stay stdlib-only unless they declare PEP 723 dependencies, flags vague description filler and boilerplate routing labels, and counts an `npx -- tool` call as unpinned again.
