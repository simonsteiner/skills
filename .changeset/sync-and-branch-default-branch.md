---
"simonsteiner-skills": patch
---

`sync-and-branch` finds the default branch with a bundled `scripts/default-branch.sh` instead of an inline shell sequence. It asks the remote only when the local `origin/HEAD` is missing or names a branch the remote no longer has, which also fixes a renamed default branch being reported under its old name. Syncing a fork always asks upstream (`--refresh`), so an upstream that switched its default branch is followed even when the old branch still exists.
