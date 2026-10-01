---
"simonsteiner-skills": patch
---

Link curated skills into every agent the skills.sh CLI treats as "universal" — Codex, GitHub Copilot, Gemini CLI and Antigravity — not just Codex. A global install never writes those agents' own directories, so Copilot and both Gemini agents kept loading frozen July copies of the Cloudflare skills that no sync could refresh, and `--check` told you to re-sync, which couldn't help. `--check` now verifies each link and names a stale copy as one to move aside.
