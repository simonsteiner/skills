---
"simonsteiner-skills": minor
---

review-prs treats bot reviews such as CodeRabbit and Copilot as input rather than a review: a PR that only bots have looked at still gets reviewed, and a PR you name always is. Each bot finding is verified: a confirmed one in an open thread is fixed there rather than posted twice, one found only in a review body or a resolved thread is posted as the skill's own comment, and a wrong one gets a reply and stays open. Thread replies no longer count as a review either. A run now reviews at most 10 PRs found by listing, keeping stacks whole, and offers to continue with the rest; a listing that hits its 100-PR ceiling says so. The workflow is now forge-neutral, with the GitHub commands in `forges/github.md` and a new `forges/azure-devops.md` that runs the same review through the `az` CLI.
