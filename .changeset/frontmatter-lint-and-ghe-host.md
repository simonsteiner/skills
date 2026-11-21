---
"simonsteiner-skills": patch
---

review-prs (`post-review.sh`, `outside-findings.sh`, `note-fixes.sh`) and address-review-findings (`reply-resolve.sh`) now take the GitHub Enterprise host from the checkout when `GH_REPO` isn't set, matching the thread scripts. Skill lint now disallows `metadata` in owned skills (credits belong in `CREDITS.md`, version in `plugin.json`) and rejects unquoted colons followed by whitespace or end-of-line in plain frontmatter values that YAML loaders fail to parse.
