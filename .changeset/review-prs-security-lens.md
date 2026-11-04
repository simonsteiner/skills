---
"simonsteiner-skills": patch
---

review-prs has a Security lens. A **Security** finding now names the lower-trust caller, what they control, the check that fails, the boundary it crosses and the concrete result for someone else, and carries a rating (`**Security** (high) — …`). A missing second layer behind a control that works is a **Smell**, and a finding that hinges on deployment config the repo doesn't hold goes in the summary with the fact to check. Adapted from Cloudflare's `security-audit` skill, which is now also curated for full codebase audits.
