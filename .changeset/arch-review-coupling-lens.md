---
"simonsteiner-skills": minor
---

arch-review gains a third lens, coupling, adapted from caldoai's untangle-codebase. It asks whether pieces that change together live together, and sorts what it finds into hidden links, needless links and surplus. Lens 1 now covers depth only (shallow modules, the deletion test) and Lens 3 the links between modules, so a leak across a seam is raised once; a candidate can come from any lens. A bundled `scripts/co-change.py` lists the file pairs that keep landing in the same commit, and `--churn` ranks the most-changed files over six months for the hot-spot pass. Both leave out lockfiles, changelogs and `linguist-generated` paths, and take `--exclude <glob>`.

Special cases now count as symptoms of a missing design: each candidate card lists the ones its fix removes, and the loose-ends audit checks they're gone. Comments that only restate the code become smaller findings. The Build step calls prune-tests on the tests of the internals a candidate replaces, never a whole file it only touched. `/arch-review next` goes straight to building when the batch is already confirmed. The skill warns against running it beside a test-review on the same repo.

prune-tests from caldoai/skills is now curated: it deletes or rewrites tests that guard no behavior. untangle-codebase is archived in the manifest as adapted into arch-review.
