---
"simonsteiner-skills": patch
---

`review-prs` and `address-review-findings` add the lessons of a real run on an 8-PR stack. After the first commit in a worktree they check that only that commit landed and the repo isn't bare, since a hook's tests can inherit `GIT_DIR`. They never skip hooks or rewrite pushed history unasked, and they resolve merge conflicts by editing, never with `git checkout <rev> --`. Sub-agents keep scratch files in their worktree. When a PR under review changes either skill, each runs its bundled scripts from a copy. The report reads CI from `gh pr checks` at report time, includes the per-thread lines, and confirms no worktree was left behind.
