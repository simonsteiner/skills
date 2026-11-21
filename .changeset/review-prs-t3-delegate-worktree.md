---
"simonsteiner-skills": patch
---

`review-prs` now uses T3 Code's `delegate_task` with `isolation: "worktree"` for review sub-agents instead of creating an out-of-workspace `mktemp` worktree for a native sub-agent (which hits permission-prompt timeouts under Antigravity).
