---
"simonsteiner-skills": minor
---

`arch-review` now works with the per-file token budget from `setup-lefthook`. It runs the project's `check-file-tokens.py` as its size lens, and gives every file over the budget a row that plans the split along the module's seams. New reports are a folder, an overview `README.md` plus one file per candidate card, so no report file goes over the budget. Older single-file reports are left as they are, and any over the budget are marked `linguist-generated`.
