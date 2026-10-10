---
"simonsteiner-skills": patch
---

`scripts/lint-skills.py` now checks every listing rule in CLAUDE.md. It fails when the top-level README, a bucket README or `.claude-plugin/plugin.json` is missing a skill or lists one too many, when an entry sits under the wrong User-invoked or Model-invoked heading, when the README links an unpublished skill anywhere, and when a source, curated or archived skill in `third-party/skills.json` gives no reason. A link inside an HTML comment no longer counts as an entry, and `disable-model-invocation: true # comment` is read as `true`.
