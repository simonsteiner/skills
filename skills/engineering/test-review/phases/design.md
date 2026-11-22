# Design phase (infra rows only)

You decide one `infra` candidate's change alone and write it down; nobody answers questions mid-run. Blind spots and waste never come here: their seams and prune lists were settled at the batch checkpoint. Your brief gives the report path, the candidate ID, the branch and its base, the context rules, and the model rule for anything you spawn. Follow them.

Call the Skill tool with "codebase-design" before anything else, and use its vocabulary (module, interface, seam, adapter, depth, locality) in the Decisions and the commit.

1. Branch `ci/<slug>` (the planned name in the status table) off the base.
2. Start from the card's **Now**, **Change**, and **Measure**. List the open decisions: what changes, where it runs, what it costs, how the Measure will show it worked.
3. Work them in rounds. Each round, take every decision whose prerequisites are settled and **answer it yourself with the recommended option**, grounded in a fact (a timing, a count, a config line), never a guess.
4. Record every decision as `Q<n>: question → answer, because <fact>` in the card's **Decisions** block. Call the Skill tool with "conventional-commit" to commit them on the branch.
5. **A one-way door stops the candidate, not the run.** The card's door says what to expect, but a change that turns out to need one counts too: deleting a recorded fixture or golden file that can't be regenerated, changing branch protection or required checks, or removing a test a contract or compliance doc names. Mark the row `blocked` with the question in Notes, commit it, and hand back.

The report is a dated record: you change only the card's Decisions and, when the candidate stops, its status row.

**Hand back:** the Decisions committed on the branch, or the row `blocked` with its question.
