---
"simonsteiner-skills": patch
---

address-review-findings and review-prs now push each PR once per fix round. Commits wait for the last one, and a stack layer's carried-up merge goes out in the same push as that layer's own fixes, so CodeRabbit and other bot reviewers start one review per round instead of one per push.
