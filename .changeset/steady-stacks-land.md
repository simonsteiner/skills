---
"simonsteiner-skills": minor
---

Add `land-prs`, a model-invoked skill that merges one PR, several, or a stack bottom-up. It checks every PR is ready (no open threads, green checks) before merging any, retargets each next PR before its base branch is deleted — the step whose absence closed a PR mid-stack — and merges the default branch into the next PR after a squash merge. It matches the repo's merge method, then fast-forwards the default branch, removes merged branches and worktrees, and deploys only when asked and only via the repo's documented path. `address-review-findings` now hands merges to it.
