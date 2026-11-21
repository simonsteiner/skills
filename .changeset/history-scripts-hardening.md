---
"simonsteiner-skills": patch
---

arch-review's `co-change.py` and test-review's `test-history.py` keep files whose names hold a `"`, `\`, tab or newline, which they used to drop. `--top`, `--min` and `--max-files` reject negative numbers with a usage error, and `test-history.py fixes` and `refactors` print their `# 0 of 0` summary in a repo with no commits yet.
