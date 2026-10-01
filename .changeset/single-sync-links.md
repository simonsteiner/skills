---
"simonsteiner-skills": patch
---

`scripts/link-skills.sh` now prunes links left behind by removed or deprecated skills, and `--check` reports owned skills that aren't linked. A new `scripts/sync-skills.sh` runs it and `sync-third-party.sh` in one go on the dev machine, so a new owned skill no longer stays invisible until someone remembers to re-link.
