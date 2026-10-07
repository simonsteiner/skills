---
"simonsteiner-skills": patch
---

`review-prs` posts through a bundled `scripts/post-review.sh`. It checks the payload and every comment's line against the diff before sending anything, and deletes the empty draft a failed post leaves behind; a hand-built `jq | gh api` pipe had left one on a PR. Reviews now run the repo's checks rather than regenerating artifacts, and don't route a refused command through a script. Files are read from a pinned ref, not a checkout another session may switch. A stack's fixes go one layer at a time.
