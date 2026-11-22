# Build phase

You implement one candidate whose design is already decided. Your brief gives the report path, the candidate ID, the branch and its base, the context rules, and the model rule for anything you spawn. Follow them.

Work from the candidate's card and its Decisions; don't reopen the design. A Decision that proves wrong becomes a **Departure**, not a redesign: do what works, and say in the commit body what differs from the Decision and why, so the Ship phase can write it into the report.

1. Check out the candidate branch the Design phase committed. A batch of smaller findings has no Design phase: cut its planned branch off the base.
2. **Live defect** (🔴 on the card): pin it with a failing test first, then move code.
3. Implement the Decisions. Replace, don't layer: write tests at the new interface, delete the tests and shallow modules it makes redundant, update docs and code maps that name moved files. Then call the Skill tool with "prune-tests", limited to the tests of the internals this candidate replaces, so none of them survives the move. It prunes every test in whatever path it's given, so never hand it a whole test file or folder the candidate only touched; any other test it would cut becomes a new `S` row in the status table, not part of this PR.
4. Run what the repo runs: typecheck, lint, the full suite. Where the project has golden outputs, show they're byte-identical, or explain the intended difference. Call the Skill tool with "conventional-commit" to commit, naming things in codebase-design's terms (module, interface, seam, depth, locality).

**Delete complexity; don't move it.** A change that leaves the reader holding the same number of concepts isn't done. Things you notice that are out of scope become new `S` rows, not part of this PR.

**Hand back:** the branch committed with checks green, or what failed and the trimmed output that shows it.
