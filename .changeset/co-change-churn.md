---
"simonsteiner-skills": patch
---

arch-review finds its hot spots with `co-change.py --churn`, which ranks the most-changed files and leaves out lockfiles, changelogs and `linguist-generated` paths the way the co-change pairs do, instead of a raw `git log | uniq -c` count that let those files crowd the top.
