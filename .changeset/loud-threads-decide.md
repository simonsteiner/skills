---
"simonsteiner-skills": minor
---

`address-review-findings` handles several PRs or a stack, bottom-up, merging each fix into the PRs stacked above it. The report now spells out every thread that needs a decision — the question, the options, and a recommendation — instead of only saying one is waiting. A PR with no review at all is called out rather than counted as clean (Copilot skips PRs based on another branch), and a merge the user asks for retargets the next PR in a stack before deleting its base.
