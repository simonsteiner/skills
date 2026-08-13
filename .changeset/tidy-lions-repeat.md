---
"simonsteiner-skills": minor
---

Curate third-party skills instead of forking or vendoring them. `third-party/skills.json` lists the upstream skills worth having and why, and `scripts/sync-third-party.sh` installs and upgrades them from their own repos via the skills.sh CLI. Nothing is copied into `skills/`, so the published plugin still contains only the skills this repo owns.
