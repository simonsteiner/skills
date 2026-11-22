---
"simonsteiner-skills": patch
---

`scripts/lint-skills.py` now fails when a skill calls a user-invoked skill through the Skill tool, which can't reach it, and when a test file sits under `skills/` or `scripts/` instead of `tests/`. `scripts/eval-skill.py prepare` lines now name the `timing` file for the coordinator to fill from the sub-agent's completion, instead of asking the sub-agent for a token count it can't know.
