---
"simonsteiner-skills": patch
---

`review-prs` and `address-review-findings` no longer switch the main checkout between PRs. `review-prs` reads each PR from a detached worktree it creates and removes, parallel reviewers get worktrees made for them, and `address-review-findings` fixes each PR in its own branch worktree (via `gh pr checkout` inside it) and carries stack fixes up there. Both now say to delete only paths they created, never a glob like `/tmp/tmp.*`.
