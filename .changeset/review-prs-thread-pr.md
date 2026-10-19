---
"simonsteiner-skills": minor
---

review-prs, called in a thread that already has a linked PR or stack, reviews only that instead of every open PR that needs a review. It now renames the thread only when the title is generic, keeping one that already says what the thread is about.

It also reads CI before posting so a red job lands in the same review, sets `GH_REPO` in fork checkouts, waits for pending checks with `gh pr checks --watch` instead of `sleep`, relaunches sub-agents a harness restart cancelled, updates the PR's title and body when fixes change what they describe, and states the commit range each review covered.
