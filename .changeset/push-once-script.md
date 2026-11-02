---
"simonsteiner-skills": patch
---

address-review-findings pushes a fix round through a bundled `scripts/push-once.sh` instead of an inline shell chain. Before pushing anything, the script refuses a bare repo, uncommitted changes, an unfinished merge, a start commit that isn't an ancestor of HEAD, or a commit count that's off. It names untracked files the round may have forgotten to add. A rejected push and any other push failure get different exit codes, so a failed login or hook no longer sends the agent into a merge.
