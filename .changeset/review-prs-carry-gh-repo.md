---
"simonsteiner-skills": patch
---

address-review-findings now picks the repo before anything else: in a fork checkout with an `upstream` remote it uses origin's repo (or the `GH_REPO` its caller passed) for every `gh` call, and checks the PR's URL before fixing. review-prs passes its `GH_REPO` on when it hands the fixes over, so the fix step no longer reads the upstream repo's PRs.
