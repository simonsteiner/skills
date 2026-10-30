---
"simonsteiner-skills": minor
---

review-prs treats bot reviews such as CodeRabbit and Copilot as input rather than a review: a PR only bots have looked at still gets reviewed, their findings are verified and fixed in their own threads instead of being posted twice, and a PR you name is always reviewed. A run now reviews at most 10 PRs found by listing, keeping stacks whole, and offers to continue with the rest; a listing that hits its 100-PR ceiling says so. The workflow is now forge-neutral, with the GitHub commands in `forges/github.md` and a new `forges/azure-devops.md` that runs the same review through the `az` CLI.
