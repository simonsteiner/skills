---
"simonsteiner-skills": minor
---

`sync-and-branch` is rewritten at a third of its length around what agents actually got wrong. It carries uncommitted work onto a branch cut from the fresh default with `git switch --no-track -c` ("commit this to a new branch"), stacks on the current branch when the changes don't apply there, and syncs a fork with its `upstream` remote — fast-forward and push when the fork carries nothing of its own, otherwise a merge on a `chore/sync-upstream-<date>` branch. The worktree route and the long preflight are gone: the harness makes worktrees, and agents cut plain branches fine without a skill. Its description now triggers only on those requests, not on every new piece of work.
