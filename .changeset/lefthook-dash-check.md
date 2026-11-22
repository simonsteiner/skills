---
"simonsteiner-skills": minor
---

setup-lefthook adds a second shared check to every project: a pre-commit job that blocks em and en dashes in staged files, with the token budget's exemptions, and prints how to rewrite each one. Both scripts now ship from one `hooks.v*` tag through `lefthook/hooks.yml`; a project on a `filetokens.v*` ref bumps `ref:` and adds the `dashes` job.
