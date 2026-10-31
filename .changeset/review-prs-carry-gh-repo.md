---
"simonsteiner-skills": patch
---

address-review-findings now picks the repo before anything else: in a fork checkout with an `upstream` remote a new `pick-repo.sh` lists gh's default repo and origin's (resolving SSH aliases, and keeping an enterprise token off an unknown origin host), and it looks each PR up on both and uses the repo that has it (or the `GH_REPO` its caller passed) for every `gh` call, and checks the PR's URL before fixing. review-prs passes its `GH_REPO` on when it hands the fixes over, so the fix step no longer reads the upstream repo's PRs.
