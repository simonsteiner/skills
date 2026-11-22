---
"simonsteiner-skills": patch
---

The skill catalog in `README.md`, `skills/engineering/README.md` and `.claude-plugin/plugin.json` is now generated from the skills by `scripts/build-catalog.py`, so it can no longer drift from them. Each entry is the skill's own `description`: whole for a user-invoked skill, and up to its "Use when…" sentence for a model-invoked one. The pre-commit hook rebuilds and stages it, and `scripts/lint-skills.py` fails on a stale catalog or a model-invoked description with no summary before its "Use" sentence. The README's development notes moved to `docs/setup.md`.
