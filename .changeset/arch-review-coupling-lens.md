---
"simonsteiner-skills": minor
---

arch-review gains a third lens, coupling, adapted from caldoai's untangle-codebase: it asks whether pieces that change together live together, and sorts what it finds into hidden links, needless links and surplus. A bundled `scripts/co-change.py` lists the file pairs that keep landing in the same commit, as evidence for it. Special cases now count as symptoms of a missing design: each candidate card lists the ones its fix removes, and the loose-ends audit checks they're gone. Comments that only restate the code become smaller findings, and the Build step calls prune-tests on the test files a candidate touched.

prune-tests from caldoai/skills is now curated: it deletes or rewrites tests that guard no behavior. untangle-codebase is archived in the manifest as adapted into arch-review.
