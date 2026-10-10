---
"simonsteiner-skills": patch
---

`review-prs` and `address-review-findings` now give their bundled scripts' full `<skill-dir>/scripts/…` path in every command, so a copied command no longer resolves inside the repo under review, and declare what they need (`git`, `gh`, plus `jq` for `review-prs`) in a `compatibility` field. `frontend-craft`'s CSS specificity tip no longer calls class selectors "type" and "element" selectors.
