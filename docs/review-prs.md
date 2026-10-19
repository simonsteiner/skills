# Running review-prs

Notes on getting the most out of [review-prs](../skills/engineering/review-prs/SKILL.md) that belong to how you call it, not to the skill itself.

## Same thread or a new one

Start the review in a **new thread**, even when only one PR is open.

- **Author bias.** With one PR, review-prs reviews it in the calling thread's own context; only several PRs fan out to sub-agents, each starting empty. If that thread wrote the PR, the reviewer already knows what the code was *meant* to do and reads that intent into the diff — exactly the gaps a fresh reader would catch.
- **Context budget.** An implementation thread plus a full review (whole files, checks, then address-review-findings) fills the window fast. Once older turns are summarized, details the review depends on get lost.

Staying in the same thread is fine for a quick re-review after you fixed something, or for a follow-up question about a finding just posted. For a PR's first real review, open a new thread.

## Thread titles

A thread started with just the skill call (`$review-prs`, "review open PRs") gets a generic title from its first message, so every review thread ends up called "Review Open Pull Requests". Two things help:

- **Name the PRs when you call it** — `/review-prs #32` gives the title generator something to work with.
- **Let the skill rename a generic title.** When the harness offers a rename tool (T3 Code's `t3_thread_update`) and the title names no PR or topic, review-prs titles the thread after the set it settled on, e.g. `Review #32: gate push on checks`. A thread that already has a meaningful title — say, the one that built the PR — keeps it.

## A thread that already has a PR

Called in a thread with open linked PRs (T3 Code's `list_thread_pull_requests`), review-prs reviews those PRs — or that stack — only, instead of every open PR that needs a review. Merged or closed links don't count. With nothing linked, the thread's own branch counts: if it isn't the default branch and has an open PR, review-prs reviews that PR alone (not the rest of a stack it's in), links it to the thread, and says so at the top of the report along with the other PRs that need a review. A thread opened on a checkout that happens to be on a feature branch narrows the same way, so ask for "all open PRs" there. Name other PRs in the call to override it.
