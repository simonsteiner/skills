---
"simonsteiner-skills": patch
---

The curated list drops two third-party skills that were never used in Claude Code: `handoff` (mattpocock/skills) and `writing-guidelines` (vercel-labs/agent-skills). They move to their sources' archived lists, so `scripts/sync-third-party.py` stops installing them and `--check` reports any copy still installed.
