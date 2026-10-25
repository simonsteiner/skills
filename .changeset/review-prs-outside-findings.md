---
"simonsteiner-skills": minor
---

review-prs now fixes what other tools already flagged on a PR, along with its own findings: the annotations its check runs carry (linters, type checkers, CodeQL), collected by a new `outside-findings.sh` script, and its open SonarQube issues. Each one is verified first, and only ones the PR introduced are posted and fixed. Review sub-agents now get a model chosen per PR: the session's model by default, a mid-tier model for small, low-risk PRs, and never the smallest tier.
