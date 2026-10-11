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
- **Let the skill rename the thread.** When the harness offers a rename tool (T3 Code's `t3_thread_update`), review-prs titles the thread after the set it settled on, e.g. `Review #32: gate push on checks` or `Review stack #24–#31: eval runner`. Harnesses without one skip the step.
