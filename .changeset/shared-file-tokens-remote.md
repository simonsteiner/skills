---
"simonsteiner-skills": minor
---

`setup-lefthook` no longer copies `check-file-tokens.py` into each project. A project's `lefthook.yml` now loads it from this repo as a lefthook `remotes:` entry pinned to a `filetokens.v*` tag, and keeps the `file-tokens` job (with its `--max-tokens`) in its own file, so the check fails closed when the remote can't be fetched. The skill explains how to migrate a repo that still has a copy, and the over-budget sweep runs `lefthook run pre-commit --job file-tokens --all-files`. `arch-review` finds the budget from that job and runs the check through lefthook, falling back to an old copy for repos not yet migrated.
