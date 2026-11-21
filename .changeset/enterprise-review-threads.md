---
"simonsteiner-skills": patch
---

On a GitHub Enterprise checkout, the review-prs scripts (`review-threads.sh`, `post-review.sh`, `outside-findings.sh`, `note-fixes.sh`) and the address-review-findings ones (`unresolved-threads.sh`, `reply-resolve.sh`) now query the checkout's own host instead of github.com. They take the host from a host-qualified `GH_REPO`, else from the checkout, and leave an explicit `GH_HOST` alone.
