---
"simonsteiner-skills": patch
---

`sync-and-branch` finds the default branch with a bundled `scripts/default-branch.sh` instead of an inline shell sequence. It asks the remote only when the local `origin/HEAD` (or `upstream/HEAD`) is missing or names a branch the remote no longer has, which also fixes a renamed default branch being reported under its old name.
