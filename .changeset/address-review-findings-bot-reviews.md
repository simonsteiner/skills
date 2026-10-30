---
"simonsteiner-skills": patch
---

address-review-findings no longer counts a bot's review (CodeRabbit, Copilot) as a real one: it still works through the bot's threads, but warns that only bots reviewed the PR and suggests running review-prs. Its PR listing now asks for up to 100 PRs instead of `gh`'s silent default of 30, and says so when it hits that ceiling.
