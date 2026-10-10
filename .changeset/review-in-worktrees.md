---
"simonsteiner-skills": patch
---

`review-prs` and `address-review-findings` no longer switch the main checkout between PRs. `review-prs` reads each PR from a detached worktree it creates and removes, and creates the worktrees for parallel reviewers. `address-review-findings` fixes a PR in place when the checkout is already on its branch, otherwise in a detached worktree pushed with `git push origin HEAD:<branch>`, which works even when another session has the branch checked out; stack fixes are carried up by merging the pushed lower layer. Both now warn against `git stash` (shared by every worktree), pattern-based deletes, symlinking gitignored inputs into a worktree, and piping `git`/`gh` into `| tail`.
