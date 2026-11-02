---
"simonsteiner-skills": patch
---

address-review-findings pushes a fix round through a bundled `scripts/push-once.sh` instead of an inline shell chain. The script refuses, before pushing anything, a bare repo, uncommitted changes, a start commit that isn't an ancestor of HEAD, or a commit count that's off. When a push is rejected, it says what to do next.
