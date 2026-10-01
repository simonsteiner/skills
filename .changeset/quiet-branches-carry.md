---
"simonsteiner-skills": minor
---

`sync-and-branch` gains a carry route: when the uncommitted work *is* the new branch's work ("commit this to a new branch"), it cuts the branch from the fresh default with `git switch --no-track -c`, which brings the changes along, and stacks on the current branch when they don't apply there. The worktree route stays for unrelated work. It also syncs a fork with its `upstream` remote — fast-forward and push when the fork carries nothing of its own, otherwise a merge on a `chore/sync-upstream-<date>` branch.
