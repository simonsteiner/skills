# A skill for merging PRs and stacks

Proposed as `land-prs` (closed PR #6): merge a stack bottom-up, retarget each next PR before deleting its base, carry squash merges up, then clean merged branches and deploy.

## Why this is out of scope

GitHub's own stacked-PR merge does this in one action, retargeting included, so a skill would re-implement a platform feature and drift from it. The one hazard worth remembering — deleting a base branch before the PR above it is retargeted closes that PR — stays as a single line in `address-review-findings`.

## Prior requests

- Chat history, Aug–Sep 2026: about 28 "merge stack in order" / "merge and deploy" / "clean merged branches" requests.
- PR #6.
