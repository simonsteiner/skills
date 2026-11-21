---
"simonsteiner-skills": patch
---

review-prs no longer claims T3 removes the worktree a `delegate_task` review creates. T3 leaves it, and the branch it made, on disk, so the skill now removes both once the review is posted and checks for them before reporting.
