---
"simonsteiner-skills": patch
---

review-prs renames the current thread after the PRs it reviews (e.g. `Review #32: gate push on checks`) when the harness offers a rename tool, such as T3 Code's `t3_thread_update`, so review threads no longer all share a generic title. New `docs/review-prs.md` explains why a review belongs in a new thread rather than the one that wrote the PR.
