# Running review-prs

Notes on getting the most out of [review-prs](../skills/engineering/review-prs/SKILL.md) that belong to how you call it, not to the skill itself.

## Same thread or a new one

Start the review in a **new thread**, even when only one PR is open.

- **Author bias.** A thread that wrote the PR already knows what the code was *meant* to do and reads that intent into the diff — exactly the gaps a fresh reader would catch. Called partway through a thread, review-prs hands the review itself to a fresh sub-agent for that reason, but the calling thread still verifies and fixes the findings. A new thread keeps the bias out of those steps too.
- **Context budget.** An implementation thread plus a full review (whole files, checks, then address-review-findings) fills the window fast. Once older turns are summarized, details the review depends on get lost.

Staying in the same thread is fine for a quick re-review after you fixed something, or for a follow-up question about a finding just posted: the sub-agent does the reading. For a PR's first real review, open a new thread.

## Thread titles

A thread started with just the skill call (`$review-prs`, "review open PRs") gets a generic title from its first message, so every review thread ends up called "Review Open Pull Requests". Two things help:

- **Name the PRs when you call it** — `/review-prs #32` gives the title generator something to work with.
- **Let the skill rename a generic title.** When the harness offers a rename tool (T3 Code's `t3_thread_update`) and the title names no PR or topic, review-prs titles the thread after the set it settled on, e.g. `Review #32: gate push on checks`. A thread that already has a meaningful title — say, the one that built the PR — keeps it.

## A thread that already has a PR

Called in a thread with open linked PRs (T3 Code's `list_thread_pull_requests`), review-prs reviews those PRs — or that stack — only, instead of every open PR that needs a review. Merged or closed links don't count. With nothing linked, the thread's own branch counts: if it isn't the default branch and has an open PR, review-prs reviews that PR alone (not the rest of a stack it's in), links it to the thread, and says so at the top of the report along with the other PRs that need a review. A thread opened on a checkout that happens to be on a feature branch narrows the same way, so ask for "all open PRs" there. Name other PRs in the call to override it.

## Bot reviewers like CodeRabbit

CodeRabbit, Copilot and similar bots don't count as a review: a PR they alone have looked at still gets one. Their threads and nitpicks are input — review-prs reviews first, then checks each bot finding against the code, confirms or disputes it in its summary, and fixes the confirmed ones in the bot's own thread rather than posting them twice. Naming a PR (`/review-prs #32`) always reviews it, even right after a human review; with no new commits that review is short.

## Azure DevOps

review-prs picks the forge with its `scripts/forge.sh`, which reads `origin` only: a `GH_REPO` in your shell or a GitHub `upstream` remote can't turn an Azure DevOps checkout into a GitHub one. The workflow is the same on both; the commands live in one guide per forge, with the same sections in the same order. On Azure DevOps it uses the `az` CLI (`az extension add --name azure-devops`, then `az login` or `AZURE_DEVOPS_EXT_PAT`) and the commands in [forges/azure-devops.md](../skills/engineering/review-prs/forges/azure-devops.md). There are no bundled scripts for it yet, and address-review-findings is GitHub-only, so on Azure DevOps review-prs posts its threads and fixes the findings itself. That guide hasn't been run against a real organization yet, so review-prs stops on an `az` error rather than guess; expect the first runs to need a fix or two. Other forges get Local mode only.

## What a review records

Each review-prs summary ends with `Range: <base>..<head>`, the commits it covered, and once its findings are fixed, `Fixed: <sha> …`, the commits that answered it. The next run reads both: it starts from the reviewed head, and commits on the `Fixed:` line don't count toward "enough changed to review again". So a PR doesn't come back just because its own fixes landed, but when it does come back for new work, the fixes are reviewed with it.
