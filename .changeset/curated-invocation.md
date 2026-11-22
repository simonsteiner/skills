---
"simonsteiner-skills": patch
---

Each curated skill in `third-party/skills.json` now records its `invocation`, `"model"` or `"user"`. The third-party catalog groups by it again. The lint requires it and refuses a Skill tool call to a user-invoked curated skill, as it already did for owned ones. `scripts/sync-third-party.py --check` fails with an `invocation` line when an installed copy's `disable-model-invocation` disagrees with the entry, which is how an upstream flip shows up.
