---
"simonsteiner-skills": patch
---

review-prs: `post-review.sh` now works on PRs too big for `gh pr diff` (over 300 files or 20,000 lines), which GitHub refused with HTTP 406. It reads the hunks from GitHub's PR files API instead. A comment on a file GitHub shows no diff for, such as a large generated file, is now reported as outside the diff before posting. Before, GitHub rejected the whole review with 422 "Line could not be resolved".
