---
"simonsteiner-skills": patch
---

The repo's tooling now decides what an owned skill is in one place, `scripts/skill_inventory.py`. Two skills with the same name in different buckets, a skill in an unknown bucket, or an owned skill sharing a name with a curated one now fail `scripts/lint-skills.py` and stop `scripts/link-skills.sh` and `scripts/sync-third-party.sh` before they touch the skill store; a duplicate used to pass lint silently. `scripts/list-skills.sh`, which nothing called, is gone.
