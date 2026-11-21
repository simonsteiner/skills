---
"simonsteiner-skills": patch
---

review-prs' `review-threads.sh` and address-review-findings' `unresolved-threads.sh` query a GitHub Enterprise checkout's own host when `GH_REPO` isn't set, instead of github.com.
